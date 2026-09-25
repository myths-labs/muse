#!/bin/bash
# MUSE Skills 定期自动更新
#
# 让 MUSE 自动保持 skills 与开源上游同步，无需人工提醒。
#
# 设计原则 — 分两层，这是本脚本最重要的部分：
#   Layer 1  git-backed skill clone  -> 自动 ff-only pull（幂等·可回滚）
#            + vendor 下的 git 仓库（skill 软链指向仓库子目录时，git 根在这里）
#            含 MANUAL skill 的仓库只 fetch 报告，绝不合并
#   Layer 1b Claude plugins marketplace -> 自动 pull（非 git 快照只报告）
#   Layer 2  非 git skill             -> 只检测，绝不改动 skill 文件
#
#   为什么 Layer 2 不自动改：这类 skill 常带本地定制（项目专属接线、
#   本地化语料、额外 scripts/templates、自定义 frontmatter 字段）。
#   实测中一次 `rsync --delete` 就会静默销毁它们，且难以察觉。
#   检测到上游更新只写进报告，由人来决定怎么合并。
#
#   Layer 2 怎么判断「上游有更新」：逐文件比内容，不看提交日期。
#   每个上游仓库只调一次 GitHub `git/trees/HEAD?recursive=1`（匿名额度 60 次/小时），
#   找到 skill 对应的上游目录，把每个文件的 blob SHA 和本地文件的 `git hash-object` 比。
#   仓库别处的提交不再误报。本地多出来的文件（本地定制）不算差异。
#   本地定制过的 skill 永远和上游不同，所以另记一份基线：上次确认时上游各文件的 SHA
#   （$MUSE_CONFIG_DIR/skills-upstream-baseline.json）。只有上游相对基线又变了才报。
#   本地与上游完全一致时自动记基线；人工合并或看过后用 --ack 记。
#
#   人工确认（与定时任务用同一组 MUSE_* 环境变量，报告里会给出完整命令）：
#     bash scripts/skills-autoupdate.sh --ack <skill> [<skill>...]
#
# 诚实报告原则：任何「查不出来」（网络失败/分支缺失/依赖缺失/未配置）
#   都必须在报告里显式标注，绝不折叠成「已最新/无更新」。假绿灯比没有报告更糟。
#
# 守卫：dirty 跳过 / detached HEAD 跳过 / 磁盘不足中止 / 只用 --ff-only
#
# 用法：
#   bash scripts/skills-autoupdate.sh
#
# 定时运行：每周一次即可（macOS 用 launchd StartCalendarInterval，Linux 用 cron）。
#
# 环境变量（均可选）：
#   MUSE_SKILL_ROOT   skills 目录。缺省时依次探测 $PWD/.agent/skills、$HOME/.agent/skills
#   MUSE_VENDOR_ROOT  vendor git 仓库目录，默认 $MUSE_SKILL_ROOT/../vendor（不存在则跳过）
#   MUSE_CONFIG_DIR   报告与映射表目录，默认 $HOME/.config/muse
#   MUSE_MAP_FILE     Layer 2 映射表路径，默认 $MUSE_CONFIG_DIR/skills-upstream-map.json
#   MUSE_MIN_DISK_MI  磁盘下限（MiB），默认 2048
#   MUSE_PLUGIN_MARKETPLACES  Claude plugins marketplace 目录，
#                     默认 $HOME/.claude/plugins/marketplaces
#   MUSE_GITHUB_API   GitHub API 根地址，默认 https://api.github.com（测试时指向本地假服务器）
#
# 映射表格式（自建·不随仓库分发，因为每人的 skill 集不同）：
#   { "skills": { "<skill-dir>": { "upstream": "owner/repo", "mode": "AUTO|MANUAL",
#                                  "path": "上游目录或文件（可选）" } } }
#   MANUAL = 本地有定制，检测到更新后必须人工 diff 合并，禁止直接覆盖。
#   path 缺省时找上游里同名、含 SKILL.md 的目录；有多个同名目录时取与本地一致
#   （或基线记下的、或最接近）的那个，报告会提示加 path 固定。path 可以是：
#   目录（如 .claude/skills/x）、"." = 整个仓库、单个文件（如 agents/x.md，与本地 SKILL.md 比）。
#   随 CLI release 分发的 skill（非 git）用 manifest 型，只比版本号、绝不下载/安装：
#   { "<skill-dir>": { "source": "manifest", "manifest": "<url 返回 {\"version\":..}>",
#                      "installed": "x.y.z", "binary": "~/path/to/cli（可选）", "mode": "MANUAL" } }

set -uo pipefail

CONFIG_DIR="${MUSE_CONFIG_DIR:-$HOME/.config/muse}"
MAP_FILE="${MUSE_MAP_FILE:-$CONFIG_DIR/skills-upstream-map.json}"
PLUGIN_MARKETPLACES="${MUSE_PLUGIN_MARKETPLACES:-$HOME/.claude/plugins/marketplaces}"
REPORT_FILE="$CONFIG_DIR/skills-update-report.md"
LOG_FILE="$CONFIG_DIR/skills-autoupdate.log"
STATE_FILE="$CONFIG_DIR/skills-upstream-baseline.json"
MIN_DISK_MI="${MUSE_MIN_DISK_MI:-2048}"
# 报告里给出可直接复制的 --ack 命令，需要本脚本的绝对路径（Layer 1 会 cd，先算好）
SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)/$(basename "${BASH_SOURCE[0]}")"

# skill root 解析：显式 > $PWD/.agent/skills > $HOME/.agent/skills
SKILLROOT_STATUS="ok"
if [ -n "${MUSE_SKILL_ROOT:-}" ]; then
  SKILL_ROOT="$MUSE_SKILL_ROOT"
  [ -d "$SKILL_ROOT" ] || SKILLROOT_STATUS="missing"
elif [ -d "$PWD/.agent/skills" ]; then
  SKILL_ROOT="$PWD/.agent/skills"
elif [ -d "$HOME/.agent/skills" ]; then
  SKILL_ROOT="$HOME/.agent/skills"
else
  SKILL_ROOT="(未找到)"
  SKILLROOT_STATUS="missing"
fi

# vendor root：skill 软链指向「仓库子目录」时（如 remotion-skills/skills/<name>），
# git 根不在 $SKILL_ROOT/*/ 下，只扫 skills 目录会让整个仓库永远不更新。
# 显式设置却不存在 = 配置错误（点亮）；缺省路径不存在 = 没用 vendor（正常）。
VENDOR_STATUS="ok"
if [ -n "${MUSE_VENDOR_ROOT:-}" ]; then
  VENDOR_ROOT=$(cd "$MUSE_VENDOR_ROOT" 2>/dev/null && pwd) || { VENDOR_ROOT="$MUSE_VENDOR_ROOT"; VENDOR_STATUS="missing"; }
elif [ "$SKILLROOT_STATUS" = "ok" ] && [ -d "$SKILL_ROOT/../vendor" ]; then
  VENDOR_ROOT=$(cd "$SKILL_ROOT/../vendor" && pwd)
else
  VENDOR_ROOT="(无)"; VENDOR_STATUS="absent"
fi

ts() { date "+%Y-%m-%d %H:%M:%S"; }
avail_mi() { echo $(( $(df -k "$HOME" | tail -1 | awk '{print $4}') / 1024 )); }
log() { echo "[$(ts)] $*" >> "$LOG_FILE"; }

# ── Layer 2 检测逻辑（python）────────────────────────────────
# l2_py check <map> <skill_root> <baseline>          -> stdout: 报告行 + 一行 "L2SUMMARY: ..."
# l2_py ack   <map> <skill_root> <baseline> <skill>… -> stdout: 每个 skill 一行结果；有失败则退出码非 0
# 失败统计走 stderr（L2PARTIAL/L2FATAL），让 bash 能区分「干净的无更新」和「查挂了」。
l2_py() {
  python3 - "$@" <<'PY'
import json,sys,os,urllib.request,urllib.error,time,re,subprocess,hashlib,tempfile
from collections import defaultdict
cmd,map_file,root,state_file=sys.argv[1:5]
ack_names=sys.argv[5:]
API=os.environ.get("MUSE_GITHUB_API","https://api.github.com").rstrip("/")
today=time.strftime("%Y-%m-%d")
try:
    mp=json.load(open(map_file,encoding="utf-8"))
except Exception as e:
    print(f"L2FATAL: 映射表无法解析： {e}", file=sys.stderr); sys.exit(3)
entries=mp.get("skills",{})

# 基线：每个 skill「上次确认时」上游各文件的 blob SHA。
# 读不了就绝不写（不覆盖一个也许还能救回的文件），本次按「无确认记录」处理。
state={"version":1,"skills":{}}; state_err=None
try:
    with open(state_file,encoding="utf-8") as f: state=json.load(f)
    if not isinstance(state.get("skills"),dict): raise ValueError("缺少 skills 字段")
except FileNotFoundError:
    pass
except Exception as e:
    state_err=f"{type(e).__name__}: {e}"; state={"version":1,"skills":{}}
bases=state["skills"]; state_dirty=False

def save_state():
    state["version"]=1
    fd,tmp=tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(state_file)),prefix=".baseline.",suffix=".tmp")
    with os.fdopen(fd,"w",encoding="utf-8") as f:
        json.dump(state,f,ensure_ascii=False,indent=1,sort_keys=True)
    os.replace(tmp,state_file)

calls=0
def gh(path):
    global calls
    calls+=1
    req=urllib.request.Request(API+path,headers={"User-Agent":"muse-skills-autoupdate"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read())
def why(e):
    if isinstance(e,urllib.error.HTTPError):
        if e.code in (403,429) and e.headers.get("X-RateLimit-Remaining")=="0": return "GitHub 限流"
        return f"HTTP {e.code}"
    return type(e).__name__

class Unresolved(Exception): pass   # 「查不出来」：必须进报告，绝不当成一致

class Repo:
    """一个上游仓库的文件清单：整仓一次 API 调用，所有 skill 共用。"""
    def __init__(self,name):
        self.name=name
        t=gh(f"/repos/{name}/git/trees/HEAD?recursive=1")
        self.truncated=bool(t.get("truncated"))
        self.items=[e for e in t.get("tree",[]) if isinstance(e,dict) and "path" in e]
        self.by_path={e["path"]:e for e in self.items}
        self.named=defaultdict(list)          # 目录名 -> 含 SKILL.md 的上游目录
        for e in self.items:
            if e.get("type")=="blob" and e["path"].endswith("/SKILL.md"):
                d=e["path"].rsplit("/",1)[0]
                self.named[d.rsplit("/",1)[-1]].append(d)
        self.subtrees={}
    def dir_files(self,d):                    # -> {相对路径： (sha, mode)}·子模块（commit）也列入，由 compare 判无法比较
        if not self.truncated:
            pre=d+"/" if d else ""
            return {e["path"][len(pre):]:(e["sha"],e.get("mode","")) for e in self.items
                    if e.get("type") in ("blob","commit") and e["path"].startswith(pre)}
        # 清单被截断（超大仓库）= 不完整：只能凭目录自己的 tree SHA 补查一次，查不到就如实报无法比较
        e=self.by_path.get(d) if d else None
        if not e or e.get("type")!="tree":
            raise Unresolved("上游目录树太大被 GitHub 截断，返回的部分里没有这个目录")
        if d not in self.subtrees:
            try:
                self.subtrees[d]=gh(f"/repos/{self.name}/git/trees/{e['sha']}?recursive=1")
            except Exception as x:
                raise Unresolved(f"上游目录树被截断，补查子目录失败（{why(x)}）")
        t=self.subtrees[d]
        if t.get("truncated"): raise Unresolved("上游目录树被截断，补查的子目录仍被截断")
        return {x["path"]:(x["sha"],x.get("mode","")) for x in t.get("tree",[]) if x.get("type") in ("blob","commit")}
    def candidates(self,s,path):              # -> [(上游路径， 文件清单)]
        if path is not None:
            p=str(path).strip().strip("/")
            if p in ("","."):
                if self.truncated: raise Unresolved("上游目录树被截断，无法比较整个仓库")
                return [(".",self.dir_files(""))]
            e=self.by_path.get(p)
            if e is None:
                raise Unresolved(("上游目录树被截断，" if self.truncated else "")+f"映射表 path `{p}` 在上游不存在")
            if e.get("type")=="blob":         # 单文件改写成的 skill（如 agents/x.md）-> 与本地 SKILL.md 比
                return [(p,{"SKILL.md":(e["sha"],e.get("mode",""))})]
            return [(p,self.dir_files(p))]
        ds=sorted(self.named.get(s,[]))
        if not ds:
            raise Unresolved("上游目录树被截断，返回的部分里没有同名目录（可在映射表加 \"path\"）" if self.truncated
                             else "上游找不到同名目录（可能改名或搬家；可在映射表加 \"path\" 指定）")
        return [(d,self.dir_files(d)) for d in ds]

def bsha(b): return hashlib.sha1(b"blob %d\0"%len(b)+b).hexdigest()   # == git hash-object
def compare(local,files):
    """只看上游有的文件；本地多出来的（本地定制）不算差异。
    -> (内容不同， 本地缺， 无法比较)。无法比较的绝不当成一致：上游是子模块、
    上游是软链而本地是普通文件（复制安装）、本地文件读不了。"""
    changed=[]; missing=[]; odd=[]
    for rel,(sha,mode) in files.items():
        lp=os.path.join(local,rel)
        try:
            if mode=="160000":
                odd.append(f"{rel}（子模块）"); continue
            if mode=="120000":
                if not os.path.islink(lp): odd.append(f"{rel}（上游是软链）"); continue
                got=bsha(os.fsencode(os.readlink(lp)))
            elif os.path.isfile(lp):
                with open(lp,"rb") as f: got=bsha(f.read())
            else:
                missing.append(rel); continue
        except OSError:
            odd.append(f"{rel}（本地读不了）"); continue
        if got!=sha: changed.append(rel)
    return sorted(changed),sorted(missing),sorted(odd)

def pick(repo,s,v,local):
    """-> ((上游路径， 文件清单， 内容不同， 本地缺， 无法比较), 基线， 候选数， 有歧义)
    基线记下的目录只要还在就一直用它，哪怕它已和本地不一致：否则一个滞后的镜像
    恰好等于本地，就会冒充「一致」、把真正在更新的目录永远藏起来。
    只有一个候选就用它。多个候选又没有基线 = 有歧义：取最接近的来展示
    （本地多出来的文件也算，再按目录层级最浅，主版本通常是 skills/x 而不是
    docs/<语言>/skills/x 这类翻译或各平台镜像），但绝不据此自动记基线。"""
    res=[(d,f)+compare(local,f) for d,f in repo.candidates(s,v.get("path"))]
    b=bases.get(s)
    base=b if isinstance(b,dict) and b.get("upstream")==repo.name and isinstance(b.get("files"),dict) else None
    chosen=next((r for r in res if base and r[0]==base.get("path")),None)
    amb=False
    if chosen is None and len(res)==1:
        chosen=res[0]
    elif chosen is None:
        mine={os.path.relpath(os.path.join(dp,f),local) for dp,_,fs in os.walk(local) for f in fs}
        def closeness(r): return (len(r[2])+len(r[3])+len(r[4])+len(mine-set(r[1])), r[0].count("/"), r[0])
        chosen=min(res,key=closeness); amb=True
    if not chosen[1]:
        raise Unresolved(f"上游 `{chosen[0]}` 里没有可比较的文件")
    if chosen[4]:
        raise Unresolved(f"`{chosen[0]}` 有文件无法逐字节比较：{names(chosen[4])}")
    return chosen,base,len(res),amb

def names(xs,n=3): return ", ".join(xs[:n])+(f" 等 {len(xs)} 个" if len(xs)>n else "")
def parts(groups): return " · ".join(f"{k} {names(v)}" for k,v in groups if v)

if cmd=="ack":
    if state_err:
        print(f"✗ 基线文件无法解析（{state_err}），拒绝写入以免覆盖。请先修复或移走：{state_file}"); sys.exit(3)
    rc=0; todo=defaultdict(list)
    for s in ack_names:
        v=entries.get(s)
        if not isinstance(v,dict) or v.get("source")=="manifest" or not v.get("upstream"):
            print(f"✗ {s}：映射表里没有这个 skill，或它不是按上游仓库比较的类型"); rc=1; continue
        local=os.path.join(root,s)
        if not os.path.isdir(local):
            print(f"✗ {s}：本地没有这个 skill 目录"); rc=1; continue
        todo[v["upstream"]].append((s,v,local))
    for name,items in sorted(todo.items()):
        try:
            repo=Repo(name)
        except Exception as e:
            for s,_,_ in items: print(f"✗ {s}：查询上游 {name} 失败（{why(e)}）")
            rc=1; continue
        for s,v,local in items:
            try:
                (d,files,changed,missing,_),base,ncand,amb=pick(repo,s,v,local)
            except Unresolved as e:
                print(f"✗ {s}：无法比较：{e}"); rc=1; continue
            except Exception as e:
                print(f"✗ {s}：比对出错（{type(e).__name__}: {e}）"); rc=1; continue
            up={r:x[0] for r,x in files.items()}
            # 报告最多是一周前的：把这次一并确认、报告里未必出现过的上游变化列出来
            if base and base.get("path")==d:
                bf=base["files"]
                took=parts([("修改",sorted(k for k in up if k in bf and bf[k]!=up[k])),
                            ("新增",sorted(k for k in up if k not in bf)),
                            ("删除",sorted(k for k in bf if k not in up))]) or "无（上游自上次确认后没变）"
                took="一并确认的上游变化："+took
            else:
                took="首次确认"
            left=len(changed)+len(missing)
            bases[s]={"upstream":name,"path":d,"files":up,"recorded":today,"via":"ack"}
            state_dirty=True
            print(f"✓ {s}：已记下（`{name}` · `{d}`）。{took}"
                  +(f"；本地仍有 {left} 个文件与上游不同，视为本地定制" if left else "；本地与上游一致")
                  +(f"；上游有 {ncand} 个同名目录，按最接近的记下，不对就在映射表加 \"path\"" if amb else ""))
    if state_dirty:
        try: save_state()
        except Exception as e: print(f"✗ 基线文件写入失败（{type(e).__name__}: {e}）"); rc=1
    sys.exit(rc)

by_repo=defaultdict(list); manifests=[]; bad_entries=0
for s,v in entries.items():
    try:
        if v.get("source")=="manifest":
            manifests.append((s,v["manifest"],v.get("installed",""),v.get("binary"),v.get("mode","MANUAL")))
        else:
            by_repo[v["upstream"]].append((s,v))
    except Exception:
        bad_entries+=1   # 单条坏数据只跳过该条，不拖垮整层
api_fail=0; failed_repos=[]

def vt(x):   # "v1.0.2" / "libtv 1.0.2" -> (1,0,2)；读不出版本号 -> None
    m=re.search(r"\d+(?:\.\d+)+",str(x or ""))
    return tuple(int(n) for n in m.group(0).split(".")) if m else None
def vs(t): return ".".join(map(str,t))

# release manifest 型（随某个 CLI 发布、非 git）：只比较版本号，绝不下载/安装。
# 映射条目：{"source":"manifest","manifest":<url>,"installed":<skill 文档对应版本>,"binary":<可选 CLI 路径>}
for s,url,inst,binary,mode in manifests:
    iv=vt(inst)
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"muse-skills-autoupdate"})
        with urllib.request.urlopen(req,timeout=15) as r:
            raw=json.loads(r.read()).get("version","")
    except Exception:
        api_fail+=1; raw=None
    if raw is not None:
        mv=vt(raw)
        if mv is None or iv is None:
            print(f"- `{s}` 🔴 版本号无法比较（上游 {str(raw)[:40]!r} / 已装 {str(inst)[:40]!r}）({mode})")
        elif mv>iv:
            print(f"- `{s}` 上游 release {vs(mv)} > 已装文档 {vs(iv)} ({mode})：需人工升级 CLI + 换同版本 skill 文档，再改映射表 installed")
    if binary:
        # 只取版本号，绝不把 CLI 原始输出写进报告
        try:
            out=subprocess.run([os.path.expanduser(binary),"--version"],capture_output=True,text=True,
                               timeout=20,stdin=subprocess.DEVNULL)
            bv=vt(out.stdout) or vt(out.stderr)
            if out.returncode!=0 or bv is None:
                print(f"- `{s}` 🔴 `{binary} --version` 失败或读不出版本（退出码 {out.returncode}）·实际 CLI 版本未知")
            elif iv is not None and bv!=iv:
                print(f"- `{s}` ⚠️ 文档与实际 CLI 版本不一致：CLI {vs(bv)} ≠ 已装文档 {vs(iv)} ({mode})")
        except FileNotFoundError:
            print(f"- `{s}` 🔴 CLI 不存在（`{binary}`）·实际 CLI 版本未知")
        except Exception as e:
            print(f"- `{s}` 🔴 `{binary} --version` 执行失败（{type(e).__name__}）·实际 CLI 版本未知")

if state_err:
    print(f"- 🔴 基线文件 `{state_file}` 无法解析（{state_err}）·本次全部按「还没有确认记录」处理，且未写入")
n_same=n_custom=n_todo=n_unres=n_fail=0
for name,skills in sorted(by_repo.items()):
    todo=[]
    for s,v in sorted(skills,key=lambda x:x[0]):
        mode=v.get("mode","MANUAL"); local=os.path.join(root,s)
        if not os.path.isdir(local):
            print(f"- `{s}` ({mode}) ⚪ 无法比较：本地没有这个 skill 目录（映射表可能过时）"); n_unres+=1; continue
        todo.append((s,v,mode,local))
    if not todo: continue
    try:
        repo=Repo(name)
    except Exception as e:
        api_fail+=1; failed_repos.append(f"{name}({why(e)})"); n_fail+=len(todo)
        time.sleep(0.7); continue
    for s,v,mode,local in todo:
        try:
            (d,files,changed,missing,_),base,ncand,amb=pick(repo,s,v,local)
        except Unresolved as e:
            print(f"- `{s}` ({mode}) ⚪ 无法比较（`{name}`）：{e}"); n_unres+=1; continue
        except Exception as e:                # 单个 skill 出错只影响它自己，不拖垮整层
            print(f"- `{s}` ({mode}) ⚪ 无法比较（`{name}`）：比对出错 {type(e).__name__}: {e}"); n_unres+=1; continue
        up={r:x[0] for r,x in files.items()}
        on_base=bool(base) and base.get("path")==d
        if not changed and not missing and amb:   # 与某个同名目录一致，但不知道该跟哪个：不自动记基线
            n_todo+=1
            print(f"- `{s}` ({mode}) ❓ 上游有 {ncand} 个同名目录，本地与其中 `{d}` 一致，但无法确定该跟哪个"
                  f"（`{name}`；在映射表加 \"path\" 或用 --ack 固定）")
            continue
        if not changed and not missing:       # 与上游一致：自动记基线
            n_same+=1
            if not on_base or base.get("files")!=up:
                bases[s]={"upstream":name,"path":d,"files":up,"recorded":today,"via":"identical"}; state_dirty=True
            continue
        if on_base and base["files"]==up:     # 上游自确认后没变，差异是本地定制
            n_custom+=1; continue
        n_todo+=1
        where=f"`{name}` · `{d}`"
        if amb:
            where+=f"；上游有 {ncand} 个同名目录，按最接近的比较，可在映射表加 \"path\" 或用 --ack 固定"
        if on_base:
            bf=base["files"]
            what=parts([("修改",sorted(k for k in up if k in bf and bf[k]!=up[k])),
                        ("新增",sorted(k for k in up if k not in bf)),
                        ("删除",sorted(k for k in bf if k not in up))])
            print(f"- `{s}` ({mode}) 🔄 上游自上次确认后改了：{what}（{where}）")
        else:
            what=parts([("内容不同",changed),("本地缺",missing)])
            print(f"- `{s}` ({mode}) ❓ 与上游不同·还没有确认记录（分不清是本地定制还是上游更新）：{what}（{where}）")
    time.sleep(0.7)

if state_dirty and not state_err:
    try: save_state()
    except Exception as e: print(f"- 🔴 基线文件写入失败（{type(e).__name__}: {e}）·下次仍会按旧基线比较")
print(f"L2SUMMARY: 逐文件比对：一致 {n_same} · 本地定制·上游未变 {n_custom} · 待处理 {n_todo} · 无法比较 {n_unres}"
      +(f" · 查询失败 {n_fail}" if n_fail else "")+f"（GitHub 请求 {calls} 次）")
if api_fail or bad_entries:
    print(f"L2PARTIAL: api_fail={api_fail} bad_entries={bad_entries}"+(f" failed={','.join(failed_repos)}" if failed_repos else ""),
          file=sys.stderr)
PY
}

mkdir -p "$CONFIG_DIR"

# ── --ack：人工合并或看过报告里的 skill 后，记下「已确认」──────
# 只写基线文件，不跑 Layer 1/1b、不改 skill 文件、不重写报告。
if [ "${1:-}" = "--ack" ]; then
  shift
  [ $# -gt 0 ] || { echo "用法：bash $SELF --ack <skill> [<skill>...]" >&2; exit 2; }
  [ "$SKILLROOT_STATUS" = "ok" ] || { echo "未找到 skills 目录（$SKILL_ROOT），请设置 MUSE_SKILL_ROOT" >&2; exit 2; }
  [ -f "$MAP_FILE" ] || { echo "映射表不存在：$MAP_FILE（请用与定时任务相同的 MUSE_* 环境变量）" >&2; exit 2; }
  command -v python3 >/dev/null 2>&1 || { echo "需要 python3" >&2; exit 2; }
  l2_py ack "$MAP_FILE" "$SKILL_ROOT" "$STATE_FILE" "$@"; rc=$?
  log "ack rc=$rc: $*"
  [ "$rc" = "0" ] && echo "（报告在下次运行时刷新）"
  exit "$rc"
fi

log "=== autoupdate start (root=$SKILL_ROOT) ==="

DISK_START=$(avail_mi)
if [ "$DISK_START" -lt "$MIN_DISK_MI" ]; then
  {
    echo "# MUSE Skills 自动更新报告"; echo
    echo "> 生成时间：$(ts)"
    echo "> 需要关注：是"; echo
    echo "## ABORTED — 磁盘不足"; echo
    echo "可用 ${DISK_START}Mi < 阈值 ${MIN_DISK_MI}Mi，本次未执行任何更新。"
  } > "$REPORT_FILE"
  log "ABORTED: disk ${DISK_START}Mi"
  exit 0
fi

PULLED=(); SKIPPED_DIRTY=(); SKIPPED_DETACHED=(); ALREADY=(); FAILED=()
HELD_MANUAL=(); DEDUPED=()
GITSKILL_COUNT=0
NL=$'\n'

# ── MANUAL 守卫 ─────────────────────────────────────────────
# 映射表里标 MANUAL（或没标 mode）的 skill 若实际落在某个 git 仓库里，
# 该仓库只 fetch + 报告落后多少，绝不合并。
# 映射表存在但读不了 = 无法判断谁是 MANUAL = 全部只报告（fail-closed）。
MANUAL_PATHS="$NL"; MANUAL_GUARD="ok"
if [ "$SKILLROOT_STATUS" = "ok" ] && [ -f "$MAP_FILE" ]; then
  if MANUAL_LIST=$(python3 -c '
import json,sys
for k,v in json.load(open(sys.argv[1],encoding="utf-8")).get("skills",{}).items():
    if not isinstance(v,dict) or v.get("mode","MANUAL")!="AUTO": print(k)
' "$MAP_FILE" 2>/dev/null); then
    while IFS= read -r s; do
      [ -n "$s" ] && [ -e "$SKILL_ROOT/$s" ] || continue
      rp=$(cd "$SKILL_ROOT/$s" 2>/dev/null && pwd -P) && MANUAL_PATHS+="$rp$NL"
    done <<< "$MANUAL_LIST"
  else
    MANUAL_GUARD="unknown"
  fi
fi

repo_has_manual() {  # $1 = 仓库物理路径
  local m
  while IFS= read -r m; do
    [ -n "$m" ] || continue
    case "$m" in "$1"|"$1"/*) return 0 ;; esac
  done <<< "$MANUAL_PATHS"
  return 1
}

# 单个 git 仓库的完整守卫链：去重 -> 磁盘 -> dirty -> detached -> fetch -> 可比较 -> MANUAL -> ff-only
# $1 = 报告里显示的名字  $2 = 仓库路径
# 返回 1 = 磁盘守卫触发，调用方必须停止整个 Layer 1
SEEN_REPOS="$NL"
update_repo() {
  local s="$1" p="$2" rp br behind old
  rp=$(cd "$p" 2>/dev/null && pwd -P) || { FAILED+=("$s (路径无法解析)"); return 0; }
  # 同一仓库可能既被 skill 软链指向又躺在 vendor 下（如 jianying-editor），只处理一次
  case "$SEEN_REPOS" in *"$NL$rp$NL"*) DEDUPED+=("$s"); return 0 ;; esac
  SEEN_REPOS+="$rp$NL"
  GITSKILL_COUNT=$((GITSKILL_COUNT+1))

  if [ "$(avail_mi)" -lt "$MIN_DISK_MI" ]; then
    FAILED+=("$s (磁盘守卫中止·后续未处理)"); return 1
  fi

  # dirty 守卫：有本地未提交改动就绝不碰
  if [ -n "$(git -C "$p" status --porcelain 2>/dev/null)" ]; then
    SKIPPED_DIRTY+=("$s"); return 0
  fi

  br=$(git -C "$p" rev-parse --abbrev-ref HEAD 2>/dev/null)
  [ -z "$br" ] && { FAILED+=("$s (无法解析分支)"); return 0; }
  # detached HEAD = 用户刻意钉在某个 commit，绝不替他移动
  [ "$br" = "HEAD" ] && { SKIPPED_DETACHED+=("$s"); return 0; }

  git -C "$p" fetch --quiet origin 2>/dev/null || { FAILED+=("$s (fetch 失败·网络或权限)"); return 0; }

  # 「查不出来」≠「已最新」：rev-list 失败（上游分支改名/删除）必须报 FAILED
  behind=$(git -C "$p" rev-list --count "HEAD..origin/$br" 2>/dev/null)
  if [ -z "$behind" ]; then
    FAILED+=("$s (无法比较·origin/$br 不存在？上游分支可能已改名)"); return 0
  fi
  [ "$behind" = "0" ] && { ALREADY+=("$s"); return 0; }

  if [ "$MANUAL_GUARD" = "unknown" ] || repo_has_manual "$rp"; then
    HELD_MANUAL+=("$s: 上游 +$behind commits 未合并"); return 0
  fi

  old=$(git -C "$p" rev-parse --short HEAD)
  if git -C "$p" merge --ff-only "origin/$br" >/dev/null 2>&1; then
    PULLED+=("$s: $old -> $(git -C "$p" rev-parse --short HEAD) (+$behind)")
  else
    FAILED+=("$s (ff-only 失败·本地已分叉)")
  fi
  return 0
}

# ── Layer 1：git-backed skill clone + vendor 仓库 ───────────
if [ "$SKILLROOT_STATUS" = "ok" ]; then
  cd "$SKILL_ROOT" || SKILLROOT_STATUS="missing"
fi
DISK_ABORT=0
if [ "$SKILLROOT_STATUS" = "ok" ]; then
  for d in */.git; do
    [ -d "$d" ] || continue
    update_repo "${d%/.git}" "$SKILL_ROOT/${d%/.git}" || { DISK_ABORT=1; break; }
  done
fi
if [ "$DISK_ABORT" = "0" ] && [ "$VENDOR_STATUS" = "ok" ]; then
  for d in "$VENDOR_ROOT"/*/.git; do
    [ -d "$d" ] || continue
    v="${d%/.git}"
    update_repo "vendor/${v##*/}" "$v" || break
  done
fi

# ── Layer 1b：Claude plugins marketplace ────────────────────
PLUGIN_RESULT=""
PLUGIN_UPDATED=0
PLUGIN_PROBLEMS=0
if [ -d "$PLUGIN_MARKETPLACES" ]; then
  for m in "$PLUGIN_MARKETPLACES"/*/; do
    [ -d "$m" ] || continue
    name=$(basename "$m")
    # 非 git ≠ 不存在：Claude Code 可能把 marketplace 重建成非 git 快照，由它自己更新。
    # 显式列出但不算问题，也绝不去动它。
    if [ ! -d "$m/.git" ]; then
      PLUGIN_RESULT+="- \`$name\` — ⚪ 存在但非 git（由 Claude Code 自行管理·本脚本不更新）"$'\n'; continue
    fi
    if [ -n "$(git -C "$m" status --porcelain 2>/dev/null)" ]; then
      PLUGIN_RESULT+="- \`$name\` — 有本地改动，已跳过"$'\n'; PLUGIN_PROBLEMS=$((PLUGIN_PROBLEMS+1)); continue
    fi
    br=$(git -C "$m" rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ -z "$br" ] || [ "$br" = "HEAD" ]; then
      PLUGIN_RESULT+="- \`$name\` — detached/异常分支，已跳过"$'\n'; PLUGIN_PROBLEMS=$((PLUGIN_PROBLEMS+1)); continue
    fi
    git -C "$m" fetch --quiet origin 2>/dev/null || { PLUGIN_RESULT+="- \`$name\` — fetch 失败"$'\n'; PLUGIN_PROBLEMS=$((PLUGIN_PROBLEMS+1)); continue; }
    behind=$(git -C "$m" rev-list --count "HEAD..origin/$br" 2>/dev/null)
    if [ -z "$behind" ]; then
      PLUGIN_RESULT+="- \`$name\` — 无法比较（origin/$br 不存在？）"$'\n'; PLUGIN_PROBLEMS=$((PLUGIN_PROBLEMS+1)); continue
    fi
    if [ "$behind" = "0" ]; then
      PLUGIN_RESULT+="- \`$name\` — 已最新"$'\n'
    elif git -C "$m" merge --ff-only "origin/$br" >/dev/null 2>&1; then
      PLUGIN_RESULT+="- \`$name\` — **已更新 +$behind commits**（需重启 Claude Code 生效）"$'\n'
      PLUGIN_UPDATED=$((PLUGIN_UPDATED+1))
    else
      PLUGIN_RESULT+="- \`$name\` — ff-only 失败"$'\n'; PLUGIN_PROBLEMS=$((PLUGIN_PROBLEMS+1))
    fi
  done
  [ -z "$PLUGIN_RESULT" ] && PLUGIN_RESULT="- 目录存在但为空（\`$PLUGIN_MARKETPLACES\`）"$'\n'
else
  PLUGIN_RESULT="- 未检测到 marketplace 目录（\`$PLUGIN_MARKETPLACES\` 不存在）"$'\n'
fi

# ── Layer 2：非 git skill 上游变化检测（只读·失败必须显式）──
# L2_STATUS: ok / partial / no-map / no-python / error
L2_STATUS="ok"; L2_HINTS=""; L2_ERRNOTE=""; L2_SUMMARY=""
if [ ! -f "$MAP_FILE" ]; then
  L2_STATUS="no-map"
elif ! command -v python3 >/dev/null 2>&1; then
  L2_STATUS="no-python"
else
  L2_STDERR="$CONFIG_DIR/.l2-stderr.tmp"
  L2_OUT=$(l2_py check "$MAP_FILE" "$SKILL_ROOT" "$STATE_FILE" 2>"$L2_STDERR")
  L2_EXIT=$?
  L2_ERR=$(cat "$L2_STDERR" 2>/dev/null); rm -f "$L2_STDERR"
  # 统计行不算「有更新」，单独拿出来，否则 NEED 永远是 1
  L2_SUMMARY=$(printf '%s\n' "$L2_OUT" | sed -n 's/^L2SUMMARY: //p')
  L2_HINTS=$(printf '%s\n' "$L2_OUT" | grep -v '^L2SUMMARY: ')
  if [ "$L2_EXIT" -ne 0 ]; then
    L2_STATUS="error"; L2_ERRNOTE="$L2_ERR"
  elif [ -n "$L2_ERR" ]; then
    L2_STATUS="partial"; L2_ERRNOTE="$L2_ERR"
  fi
fi

# ── 汇总 NEED（任何「有变化」或「有问题」都必须点亮）────────
NEED=0
[ ${#PULLED[@]} -gt 0 ] && NEED=1
[ ${#FAILED[@]} -gt 0 ] && NEED=1
[ ${#SKIPPED_DIRTY[@]} -gt 0 ] && NEED=1        # dirty 永远静默 = 永远不更新，必须浮出
[ ${#HELD_MANUAL[@]} -gt 0 ] && NEED=1          # MANUAL 有上游更新，等人 diff
[ "$MANUAL_GUARD" = "unknown" ] && NEED=1
[ "$VENDOR_STATUS" = "missing" ] && NEED=1
[ "$PLUGIN_UPDATED" -gt 0 ] && NEED=1
[ "$PLUGIN_PROBLEMS" -gt 0 ] && NEED=1
[ -n "$L2_HINTS" ] && NEED=1
[ "$L2_STATUS" = "error" ] || [ "$L2_STATUS" = "partial" ] && NEED=1
[ "$SKILLROOT_STATUS" = "missing" ] && NEED=1    # 配置错误比无更新更需要被看到

{
  echo "# MUSE Skills 自动更新报告"; echo
  echo "> 生成时间：$(ts) · 磁盘 ${DISK_START}Mi -> $(avail_mi)Mi"
  echo "> 需要关注：$([ "$NEED" = "1" ] && echo '是' || echo '否·全部最新')"; echo
  echo "## Layer 1 — git-backed skill（已自动更新）"; echo
  if [ "$SKILLROOT_STATUS" = "missing" ]; then
    echo "- 🔴 **未找到 skills 目录**（探测了 \$MUSE_SKILL_ROOT / \$PWD/.agent/skills / \$HOME/.agent/skills）"
    echo "  请设置 \`MUSE_SKILL_ROOT\` 指向实际 skills 目录。本层未执行。"
  elif [ "$GITSKILL_COUNT" = "0" ]; then
    echo "- 该目录下没有 git-backed skill（0 个内嵌 .git）。如 skills 均为复制安装则属正常。"
  else
    if [ ${#PULLED[@]} -gt 0 ]; then printf '%s\n' "${PULLED[@]}" | sed 's/^/- ✅ /'
    else echo "- 无更新"; fi
    echo; echo "已最新 ${#ALREADY[@]} / ${GITSKILL_COUNT} 个"
    if [ ${#SKIPPED_DETACHED[@]} -gt 0 ]; then
      echo; echo "**detached HEAD·刻意钉住，未动**："
      printf '%s\n' "${SKIPPED_DETACHED[@]}" | sed 's/^/- 📌 /'
    fi
    if [ ${#SKIPPED_DIRTY[@]} -gt 0 ]; then
      echo; echo "**因本地有未提交改动而跳过**（长期不处理 = 永远停更，需人工决策）："
      printf '%s\n' "${SKIPPED_DIRTY[@]}" | sed 's/^/- ⚠️ /'
    fi
    if [ ${#HELD_MANUAL[@]} -gt 0 ]; then
      echo; echo "**含 MANUAL skill·只 fetch 未合并**（需逐个 diff 后人工合并）："
      printf '%s\n' "${HELD_MANUAL[@]}" | sed 's/^/- ✋ /'
    fi
    if [ ${#FAILED[@]} -gt 0 ]; then
      echo; echo "**失败**（不是「已最新」，是查不了/合不了）："
      printf '%s\n' "${FAILED[@]}" | sed 's/^/- 🔴 /'
    fi
  fi
  case "$VENDOR_STATUS" in
    ok)      echo; echo "vendor 仓库目录：\`$VENDOR_ROOT\`（与 skill 同一套守卫）" ;;
    missing) echo; echo "- 🔴 **\`MUSE_VENDOR_ROOT\` 指向的目录不存在**（\`$VENDOR_ROOT\`），vendor 仓库本次未扫描" ;;
  esac
  if [ ${#DEDUPED[@]} -gt 0 ]; then
    echo "与 skill 软链是同一仓库、已去重：$(printf '%s ' "${DEDUPED[@]}")"
  fi
  if [ "$MANUAL_GUARD" = "unknown" ]; then
    echo; echo "- 🔴 **映射表无法解析·分不清谁是 MANUAL**，本次所有仓库只 fetch 不合并"
  fi
  echo; echo "## Layer 1b — Claude plugins marketplace"; echo
  echo "$PLUGIN_RESULT"
  echo "## Layer 2 — 非 git skill 上游变化（**仅检测·未改动任何文件**）"; echo
  case "$L2_STATUS" in
    no-map)
      echo "- ⚪ **未配置映射表·已跳过**（\`$MAP_FILE\` 不存在）"
      echo "  格式见脚本头注释；让 agent 审计一次本地 skills 来源即可生成。" ;;
    no-python)
      echo "- 🔴 **python3 缺失·已跳过**（Layer 2 需要 python3）" ;;
    error)
      echo "- 🔴 **检查失败**（本次结果不可信，不代表无更新）："
      echo '```'; echo "$L2_ERRNOTE"; echo '```' ;;
    partial|ok)
      if [ -n "$L2_HINTS" ]; then
        echo "$L2_HINTS"; echo
        echo "> \`(AUTO)\` = 本地无定制，可安全同步。"
        echo "> \`(MANUAL)\` = **本地有定制**，必须逐个 diff 后人工合并，禁止直接覆盖。"
        echo "> 🔄 上游自上次确认后又改了 · ❓ 与上游不同但从没确认过 · ⚪ 无法比较（≠ 已最新）"
        echo "> 合并完或看过后，记下「已确认」（本地改到与上游完全一致时会自动记下）："
        echo "> \`PATH='$PATH' MUSE_SKILL_ROOT='$SKILL_ROOT' MUSE_CONFIG_DIR='$CONFIG_DIR' MUSE_MAP_FILE='$MAP_FILE' bash '$SELF' --ack <skill>...\`"
      elif [ "$L2_STATUS" = "partial" ]; then
        echo "- ⚠️ 查到的部分没有发现上游更新，但有查询失败（见下），不代表全部已最新"
      else
        echo "- 无检测到上游更新"
      fi
      [ -n "$L2_SUMMARY" ] && { echo; echo "$L2_SUMMARY"; }
      if [ "$L2_STATUS" = "partial" ]; then
        echo
        echo "- ⚠️ **部分上游查询失败**（下列统计范围内的结论不完整）：\`$L2_ERRNOTE\`"
      fi ;;
  esac
  echo; echo "---"
  echo "*由 \`scripts/skills-autoupdate.sh\` 生成，\`/resume\` Boot 序列会自动读取。*"
} > "$REPORT_FILE"

log "done: pulled=${#PULLED[@]} already=${#ALREADY[@]} dirty=${#SKIPPED_DIRTY[@]} detached=${#SKIPPED_DETACHED[@]} failed=${#FAILED[@]} held_manual=${#HELD_MANUAL[@]} vendor=$VENDOR_STATUS plugin_upd=$PLUGIN_UPDATED l2=$L2_STATUS py=$(command -v python3 || echo none)"
exit 0
