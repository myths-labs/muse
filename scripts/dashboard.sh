#!/bin/bash
# MUSE Web Dashboard — Memory & Role Visualization
# Generates a self-contained HTML dashboard from your MUSE project data.
#
# Usage:
#   ./scripts/dashboard.sh [project-dir]    # Generate dashboard for a project
#   ./scripts/dashboard.sh --serve [port]   # Generate and serve locally
#   ./scripts/dashboard.sh --help
#
# Zero dependencies — pure HTML/CSS/JS, no framework needed.

set -euo pipefail

# ─── Colors ───
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BOLD=''; DIM=''; RESET=''
fi

info()  { printf "  ${GREEN}✓${RESET} %s\n" "$*"; }
warn()  { printf "  ${YELLOW}⚠${RESET} %s\n" "$*"; }
error() { printf "  ${RED}✗${RESET} %s\n" "$*" >&2; }

# ─── Args ───
PROJECT_DIR="${1:-.}"
SERVE_MODE=false
SERVE_PORT=8432

if [[ "${1:-}" == "--serve" ]]; then
  SERVE_MODE=true
  SERVE_PORT="${2:-8432}"
  PROJECT_DIR="."
elif [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo ""
  echo "🎭 MUSE Web Dashboard"
  echo "═══════════════════════"
  echo ""
  echo "Usage:"
  echo "  ./scripts/dashboard.sh [project-dir]    Generate dashboard"
  echo "  ./scripts/dashboard.sh --serve [port]   Generate and serve (default: 8432)"
  echo ""
  exit 0
fi

PROJECT_DIR="$(cd "$PROJECT_DIR" 2>/dev/null && pwd || echo "$PROJECT_DIR")"

echo ""
echo "🎭 MUSE Web Dashboard Generator"
echo "═════════════════════════════════"
echo ""

# ─── Collect Data ───

# Roles
ROLES_JSON="["
if [ -d "$PROJECT_DIR/.muse" ]; then
  first=true
  for role_file in "$PROJECT_DIR/.muse"/*.md; do
    [ ! -f "$role_file" ] && continue
    role_name=$(basename "$role_file" .md)
    # Extract L0 line (UTF-8 safe)
    l0_line=$(head -1 "$role_file" | LC_ALL=C sed 's/<!-- L0: //' | LC_ALL=C sed 's/ -->//' | cut -c1-200 || echo "")
    line_count=$(wc -l < "$role_file" | tr -d ' ')
    last_modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$role_file" 2>/dev/null || stat -c "%y" "$role_file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)

    $first || ROLES_JSON+=","
    first=false
    # Escape special chars for JSON
    l0_escaped=$(echo "$l0_line" | LC_ALL=C sed 's/"/\\"/g' | LC_ALL=C sed "s/'/\\\\'/g")
    ROLES_JSON+="{\"name\":\"$role_name\",\"l0\":\"$l0_escaped\",\"lines\":$line_count,\"modified\":\"$last_modified\"}"
  done
fi
ROLES_JSON+="]"

# Memory entries
MEMORY_JSON="["
if [ -d "$PROJECT_DIR/memory" ]; then
  first=true
  for mem_file in $(ls -r "$PROJECT_DIR/memory"/*.md 2>/dev/null | head -30); do
    [ ! -f "$mem_file" ] && continue
    mem_date=$(basename "$mem_file" .md)
    mem_lines=$(wc -l < "$mem_file" | tr -d ' ')
    mem_size=$(wc -c < "$mem_file" | tr -d ' ')
    # Extract first meaningful line as title
    mem_title=$(grep -m1 "^#\|^##\|^>" "$mem_file" 2>/dev/null | sed 's/^[# >]*//' | head -c 80 | sed 's/"/\\"/g')

    $first || MEMORY_JSON+=","
    first=false
    MEMORY_JSON+="{\"date\":\"$mem_date\",\"lines\":$mem_lines,\"size\":$mem_size,\"title\":\"$mem_title\"}"
  done
fi
MEMORY_JSON+="]"

# Skills count
SKILL_COUNT=0
if [ -d "$PROJECT_DIR/.agent/skills" ] || [ -d "$PROJECT_DIR/skills" ]; then
  SKILL_DIR="${PROJECT_DIR}/skills"
  [ ! -d "$SKILL_DIR" ] && SKILL_DIR="${PROJECT_DIR}/.agent/skills"
  [ -d "$SKILL_DIR" ] && SKILL_COUNT=$(find "$SKILL_DIR" -name "SKILL.md" -type f 2>/dev/null | wc -l | tr -d ' ')
fi

# MEMORIES.md info
MEMORIES_LINES=0
MEMORIES_WORDS=0
if [ -f "$PROJECT_DIR/MEMORIES.md" ]; then
  MEMORIES_LINES=$(wc -l < "$PROJECT_DIR/MEMORIES.md" | tr -d ' ')
  MEMORIES_WORDS=$(wc -w < "$PROJECT_DIR/MEMORIES.md" | tr -d ' ')
fi

# Git info
GIT_BRANCH=""
GIT_COMMITS=0
if [ -d "$PROJECT_DIR/.git" ]; then
  GIT_BRANCH=$(cd "$PROJECT_DIR" && git branch --show-current 2>/dev/null || echo "")
  GIT_COMMITS=$(cd "$PROJECT_DIR" && git rev-list --count HEAD 2>/dev/null || echo "0")
fi

# Project name
PROJECT_NAME=$(basename "$PROJECT_DIR")

info "Project: $PROJECT_NAME"
info "Roles: $(echo "$ROLES_JSON" | grep -o '"name"' | wc -l | tr -d ' ')"
info "Memory files: $(echo "$MEMORY_JSON" | grep -o '"date"' | wc -l | tr -d ' ')"
info "Skills: $SKILL_COUNT"

# ─── Generate HTML ───

OUTPUT_FILE="$PROJECT_DIR/.muse/dashboard.html"
mkdir -p "$(dirname "$OUTPUT_FILE")"

cat > "$OUTPUT_FILE" << 'DASHBOARD_HTML'
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🎭 MUSE Dashboard</title>
<style>
:root {
  --bg-primary: #0a0a0f;
  --bg-secondary: #12121a;
  --bg-card: #1a1a2e;
  --bg-card-hover: #1e1e35;
  --text-primary: #e8e8f0;
  --text-secondary: #8888aa;
  --text-muted: #555577;
  --accent: #6c5ce7;
  --accent-light: #a29bfe;
  --accent-glow: rgba(108, 92, 231, 0.3);
  --success: #00b894;
  --warning: #fdcb6e;
  --danger: #e17055;
  --info: #74b9ff;
  --border: #2a2a44;
  --border-light: #3a3a55;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 4px 24px rgba(0,0,0,0.3);
  --transition: 0.2s ease;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  line-height: 1.6;
}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ─── Layout ─── */
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.header {
  text-align: center;
  padding: 40px 0 32px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 32px;
}

.header h1 {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-light), var(--accent));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}

.header .subtitle {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.header .meta {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.header .meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.meta-item .value {
  color: var(--text-primary);
  font-weight: 600;
}

/* ─── Stats Grid ─── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  text-align: center;
  transition: var(--transition);
}

.stat-card:hover {
  border-color: var(--accent);
  box-shadow: 0 0 20px var(--accent-glow);
  transform: translateY(-2px);
}

.stat-card .stat-icon {
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.stat-card .stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--accent-light);
}

.stat-card .stat-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ─── Sections ─── */
.section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ─── Role Cards ─── */
.role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 16px;
}

.role-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  transition: var(--transition);
  cursor: default;
}

.role-card:hover {
  border-color: var(--accent);
  background: var(--bg-card-hover);
}

.role-card .role-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.role-card .role-name {
  font-size: 1.1rem;
  font-weight: 600;
  text-transform: capitalize;
}

.role-card .role-badge {
  font-size: 0.7rem;
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--accent-glow);
  color: var(--accent-light);
  border: 1px solid var(--accent);
}

.role-card .role-l0 {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.role-card .role-meta {
  display: flex;
  gap: 16px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ─── Memory Timeline ─── */
.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: linear-gradient(to bottom, var(--accent), var(--border));
}

.timeline-item {
  position: relative;
  margin-bottom: 16px;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: var(--transition);
}

.timeline-item:hover {
  border-color: var(--accent);
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: -20px;
  top: 22px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent);
  border: 2px solid var(--bg-primary);
}

.timeline-date {
  font-size: 0.8rem;
  color: var(--accent-light);
  font-weight: 600;
  margin-bottom: 4px;
}

.timeline-title {
  font-size: 0.9rem;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.timeline-meta {
  display: flex;
  gap: 16px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* ─── Nav Tabs ─── */
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.tab {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.85rem;
  transition: var(--transition);
  font-family: inherit;
}

.tab:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}

.tab-content { display: none; }
.tab-content.active { display: block; }

/* ─── Footer ─── */
.footer {
  text-align: center;
  padding: 32px 0;
  color: var(--text-muted);
  font-size: 0.8rem;
  border-top: 1px solid var(--border);
  margin-top: 40px;
}

/* ─── Responsive ─── */
@media (max-width: 768px) {
  .dashboard { padding: 16px; }
  .header h1 { font-size: 1.5rem; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .role-grid { grid-template-columns: 1fr; }
}

/* ─── Animations ─── */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.section { animation: fadeIn 0.5s ease forwards; }
.section:nth-child(2) { animation-delay: 0.1s; }
.section:nth-child(3) { animation-delay: 0.2s; }
.section:nth-child(4) { animation-delay: 0.3s; }
</style>
</head>
<body>
<div class="dashboard">

  <div class="header">
    <h1>🎭 MUSE Dashboard</h1>
    <p class="subtitle" id="project-name"></p>
    <div class="meta">
      <span class="meta-item">📅 Generated: <span class="value" id="gen-date"></span></span>
      <span class="meta-item" id="git-meta"></span>
    </div>
  </div>

  <div class="stats-grid" id="stats-grid"></div>

  <div class="tabs">
    <button class="tab active" data-tab="roles">🎭 Roles</button>
    <button class="tab" data-tab="memory">🧠 Memory</button>
  </div>

  <div class="tab-content active" id="tab-roles">
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">🎭 Active Roles</h2>
      </div>
      <div class="role-grid" id="role-grid"></div>
    </div>
  </div>

  <div class="tab-content" id="tab-memory">
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">🧠 Memory Timeline</h2>
      </div>
      <div class="timeline" id="timeline"></div>
    </div>
  </div>

  <div class="footer">
    🎭 MUSE — Memory-Unified Skills & Execution<br>
    <a href="https://github.com/myths-labs/muse" style="color: var(--accent-light)">github.com/myths-labs/muse</a>
  </div>

</div>

<script>
DASHBOARD_HTML

# Inject data into the HTML
cat >> "$OUTPUT_FILE" << INJECT_DATA
// ─── Injected Data ───
const DATA = {
  project: "$PROJECT_NAME",
  roles: $ROLES_JSON,
  memory: $MEMORY_JSON,
  skillCount: $SKILL_COUNT,
  memoriesLines: $MEMORIES_LINES,
  memoriesWords: $MEMORIES_WORDS,
  gitBranch: "$GIT_BRANCH",
  gitCommits: $GIT_COMMITS,
  generatedAt: "$(date '+%Y-%m-%d %H:%M')"
};
INJECT_DATA

cat >> "$OUTPUT_FILE" << 'DASHBOARD_JS'

// ─── Render ───
document.getElementById('project-name').textContent = DATA.project;
document.getElementById('gen-date').textContent = DATA.generatedAt;

if (DATA.gitBranch) {
  document.getElementById('git-meta').innerHTML =
    `🌿 <span class="value">${DATA.gitBranch}</span> · ${DATA.gitCommits} commits`;
}

// Stats
const stats = [
  { icon: '🎭', value: DATA.roles.length, label: 'Active Roles' },
  { icon: '🧠', value: DATA.memory.length, label: 'Memory Files' },
  { icon: '⚡', value: DATA.skillCount, label: 'Skills' },
  { icon: '📚', value: DATA.memoriesWords, label: 'Words (Long-term)' },
];

document.getElementById('stats-grid').innerHTML = stats.map(s => `
  <div class="stat-card">
    <div class="stat-icon">${s.icon}</div>
    <div class="stat-value">${s.value}</div>
    <div class="stat-label">${s.label}</div>
  </div>
`).join('');

// Roles
document.getElementById('role-grid').innerHTML = DATA.roles.map(r => `
  <div class="role-card">
    <div class="role-header">
      <span class="role-name">${r.name}</span>
      <span class="role-badge">${r.lines} lines</span>
    </div>
    <div class="role-l0">${r.l0 || 'No L0 summary'}</div>
    <div class="role-meta">
      <span>📅 ${r.modified}</span>
    </div>
  </div>
`).join('');

// Memory Timeline
document.getElementById('timeline').innerHTML = DATA.memory.map(m => `
  <div class="timeline-item">
    <div class="timeline-date">${m.date}</div>
    <div class="timeline-title">${m.title || 'Session notes'}</div>
    <div class="timeline-meta">
      <span>${m.lines} lines</span>
      <span>${(m.size / 1024).toFixed(1)} KB</span>
    </div>
  </div>
`).join('') || '<p style="color: var(--text-muted)">No memory files found</p>';

// Tabs
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
  });
});
DASHBOARD_JS

echo '</script></body></html>' >> "$OUTPUT_FILE"

# ─── Output ───
LINE_COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
info "Generated: $OUTPUT_FILE ($LINE_COUNT lines)"

if $SERVE_MODE; then
  echo ""
  echo "  🌐 Serving at: http://localhost:$SERVE_PORT"
  echo "  Press Ctrl+C to stop"
  echo ""
  cd "$(dirname "$OUTPUT_FILE")"
  python3 -m http.server "$SERVE_PORT" 2>/dev/null || python -m SimpleHTTPServer "$SERVE_PORT"
else
  echo ""
  echo "  ${DIM}Open in browser:${RESET}"
  echo "  ${DIM}  open $OUTPUT_FILE${RESET}"
  echo ""
  echo "  ${DIM}Or serve locally:${RESET}"
  echo "  ${DIM}  ./scripts/dashboard.sh --serve${RESET}"
  echo ""
fi
