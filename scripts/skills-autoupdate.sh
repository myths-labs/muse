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
#   Layer 2  非 git skill             -> 只检测，绝不改动文件
#
#   为什么 Layer 2 不自动改：这类 skill 常带本地定制（项目专属接线、
#   本地化语料、额外 scripts/templates、自定义 frontmatter 字段）。
#   实测中一次 `rsync --delete` 就会静默销毁它们，且难以察觉。
#   检测到上游更新只写进报告，由人来决定怎么合并。
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
#
# 映射表格式（自建·不随仓库分发，因为每人的 skill 集不同）：
#   { "skills": { "<skill-dir>": { "upstream": "owner/repo", "mode": "AUTO|MANUAL" } } }
#   MANUAL = 本地有定制，检测到更新后必须人工 diff 合并，禁止直接覆盖。
#   随 CLI release 分发的 skill（非 git）用 manifest 型，只比版本号、绝不下载/安装：
#   { "<skill-dir>": { "source": "manifest", "manifest": "<url 返回 {\"version\":..}>",
#                      "installed": "x.y.z", "binary": "~/path/to/cli（可选）", "mode": "MANUAL" } }

set -uo pipefail

CONFIG_DIR="${MUSE_CONFIG_DIR:-$HOME/.config/muse}"
MAP_FILE="${MUSE_MAP_FILE:-$CONFIG_DIR/skills-upstream-map.json}"
PLUGIN_MARKETPLACES="${MUSE_PLUGIN_MARKETPLACES:-$HOME/.claude/plugins/marketplaces}"
REPORT_FILE="$CONFIG_DIR/skills-update-report.md"
LOG_FILE="$CONFIG_DIR/skills-autoupdate.log"
MIN_DISK_MI="${MUSE_MIN_DISK_MI:-2048}"

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

mkdir -p "$CONFIG_DIR"
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
# L2_STATUS: ok / no-map / no-python / error
L2_STATUS="ok"; L2_HINTS=""; L2_ERRNOTE=""
if [ ! -f "$MAP_FILE" ]; then
  L2_STATUS="no-map"
elif ! command -v python3 >/dev/null 2>&1; then
  L2_STATUS="no-python"
else
  L2_STDERR="$CONFIG_DIR/.l2-stderr.tmp"
  L2_HINTS=$(python3 - "$MAP_FILE" "$SKILL_ROOT" 2>"$L2_STDERR" <<'PY'
import json,sys,os,urllib.request,time,re,subprocess
from collections import defaultdict
try:
    mp=json.load(open(sys.argv[1],encoding="utf-8"))
except Exception as e:
    print(f"L2FATAL: 映射表无法解析： {e}", file=sys.stderr); sys.exit(3)
root=sys.argv[2]
by_repo=defaultdict(list); manifests=[]; bad_entries=0
for s,v in mp.get("skills",{}).items():
    try:
        if v.get("source")=="manifest":
            manifests.append((s,v["manifest"],v.get("installed",""),v.get("binary"),v.get("mode","MANUAL")))
        else:
            by_repo[v["upstream"]].append((s,v.get("mode","MANUAL")))
    except Exception:
        bad_entries+=1   # 单条坏数据只跳过该条，不拖垮整层
api_fail=0

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

for repo,skills in sorted(by_repo.items()):
    try:
        req=urllib.request.Request(f"https://api.github.com/repos/{repo}/commits?per_page=1",
                                   headers={"User-Agent":"muse-skills-autoupdate"})
        with urllib.request.urlopen(req,timeout=15) as r:
            pushed=json.loads(r.read())[0]["commit"]["committer"]["date"][:10]
    except Exception:
        api_fail+=1
        continue
    stale=[]
    for s,mode in skills:
        p=os.path.join(root,s,"SKILL.md")
        if not os.path.exists(p): continue
        if time.strftime("%Y-%m-%d",time.localtime(os.path.getmtime(p))) < pushed:
            stale.append(f"{s}({mode})")
    if stale:
        print(f"- `{repo}` 上游 {pushed} 有新提交 -> 本地更旧： {', '.join(stale)}")
    time.sleep(0.7)
# 失败统计走 stderr，让 bash 能区分「干净的无更新」和「查挂了」
if api_fail or bad_entries:
    print(f"L2PARTIAL: api_fail={api_fail} bad_entries={bad_entries}", file=sys.stderr)
PY
)
  L2_EXIT=$?
  L2_ERR=$(cat "$L2_STDERR" 2>/dev/null); rm -f "$L2_STDERR"
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
      else
        echo "- 无检测到上游更新"
      fi
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
