import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';

// ─── Activation ─────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext) {
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    if (!workspaceRoot) {
        return;
    }

    // Find MUSE root (could be workspace or parent)
    const museRoot = findMuseRoot(workspaceRoot);

    // Register tree data providers
    const rolesProvider = new RolesTreeProvider(workspaceRoot);
    const skillsProvider = new SkillsTreeProvider(museRoot || workspaceRoot);
    const memoryProvider = new MemoryTreeProvider(workspaceRoot);

    vscode.window.registerTreeDataProvider('muse-roles', rolesProvider);
    vscode.window.registerTreeDataProvider('muse-skills', skillsProvider);
    vscode.window.registerTreeDataProvider('muse-memory', memoryProvider);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('muse.showDashboard', () => showDashboard(context, workspaceRoot)),
        vscode.commands.registerCommand('muse.browseSkills', () => skillsProvider.refresh()),
        vscode.commands.registerCommand('muse.searchSkills', () => searchSkills(museRoot || workspaceRoot)),
        vscode.commands.registerCommand('muse.contextHealth', () => contextHealth(workspaceRoot)),
        vscode.commands.registerCommand('muse.showMemory', () => memoryProvider.refresh()),
        vscode.commands.registerCommand('muse.showRoles', () => rolesProvider.refresh()),
        vscode.commands.registerCommand('muse.openSkill', (skillPath: string) => openSkill(skillPath)),
        vscode.commands.registerCommand('muse.generateDashboard', () => generateDashboard(workspaceRoot, museRoot)),
    );

    // Status bar
    const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusItem.text = '$(symbol-misc) MUSE';
    statusItem.tooltip = 'MUSE Context OS';
    statusItem.command = 'muse.showDashboard';
    statusItem.show();
    context.subscriptions.push(statusItem);

    // Auto-detect MUSE project
    const claudeMd = path.join(workspaceRoot, 'CLAUDE.md');
    if (fs.existsSync(claudeMd)) {
        statusItem.text = '$(symbol-misc) MUSE ✓';
        statusItem.tooltip = 'MUSE project detected';
    }
}

export function deactivate() { }

// ─── Helpers ────────────────────────────────────────────────

function findMuseRoot(workspaceRoot: string): string | null {
    // Check if MUSE is cloned as subdir or is the workspace itself
    const museDir = path.join(workspaceRoot, 'skills');
    if (fs.existsSync(museDir)) {
        return workspaceRoot;
    }
    // Check if .agent/skills exists (MUSE installed into project)
    const agentDir = path.join(workspaceRoot, '.agent', 'skills');
    if (fs.existsSync(agentDir)) {
        return workspaceRoot;
    }
    return null;
}

function extractFrontmatter(filePath: string, field: string): string {
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        const match = content.match(/^---\n([\s\S]*?)\n---/);
        if (match) {
            const line = match[1].split('\n').find(l => l.startsWith(`${field}:`));
            if (line) {
                return line.replace(`${field}:`, '').trim().replace(/^"|"$/g, '');
            }
        }
    } catch { }
    return '';
}

function extractL0(filePath: string): string {
    try {
        const firstLine = fs.readFileSync(filePath, 'utf-8').split('\n')[0];
        return firstLine.replace('<!-- L0: ', '').replace(' -->', '').trim();
    } catch { }
    return '';
}

// ─── Roles Tree ─────────────────────────────────────────────

class RolesTreeProvider implements vscode.TreeDataProvider<RoleItem> {
    private _onDidChange = new vscode.EventEmitter<RoleItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChange.event;

    constructor(private workspaceRoot: string) { }

    refresh() { this._onDidChange.fire(undefined); }

    getTreeItem(element: RoleItem): vscode.TreeItem { return element; }

    getChildren(): RoleItem[] {
        const museDir = path.join(this.workspaceRoot, '.muse');
        if (!fs.existsSync(museDir)) {
            return [new RoleItem('No .muse/ directory found', '', '', vscode.TreeItemCollapsibleState.None)];
        }

        const items: RoleItem[] = [];
        const files = fs.readdirSync(museDir).filter(f => f.endsWith('.md')).sort();

        for (const file of files) {
            const fullPath = path.join(museDir, file);
            const name = file.replace('.md', '');
            const l0 = extractL0(fullPath);
            const stat = fs.statSync(fullPath);
            const lines = fs.readFileSync(fullPath, 'utf-8').split('\n').length;

            const item = new RoleItem(
                `${name}`,
                `${lines} lines · ${l0.substring(0, 60)}${l0.length > 60 ? '...' : ''}`,
                fullPath,
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon(getRoleIcon(name));
            item.command = {
                command: 'vscode.open',
                title: 'Open Role',
                arguments: [vscode.Uri.file(fullPath)]
            };
            items.push(item);
        }

        return items;
    }
}

class RoleItem extends vscode.TreeItem {
    constructor(
        label: string,
        public readonly description: string,
        public readonly filePath: string,
        collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = description;
    }
}

function getRoleIcon(role: string): string {
    const icons: Record<string, string> = {
        build: 'tools', qa: 'checklist', growth: 'graph',
        gm: 'organization', strategy: 'compass', ops: 'server',
        research: 'beaker', fundraise: 'credit-card'
    };
    return icons[role] || 'file';
}

// ─── Skills Tree ────────────────────────────────────────────

class SkillsTreeProvider implements vscode.TreeDataProvider<SkillItem> {
    private _onDidChange = new vscode.EventEmitter<SkillItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChange.event;

    constructor(private museRoot: string) { }

    refresh() { this._onDidChange.fire(undefined); }

    getTreeItem(element: SkillItem): vscode.TreeItem { return element; }

    getChildren(element?: SkillItem): SkillItem[] {
        if (!element) {
            // Root: show tiers
            const tiers = [
                { name: 'Core', icon: 'shield', dir: 'core' },
                { name: 'Toolkit', icon: 'wrench', dir: 'toolkit' },
                { name: 'Ecosystem', icon: 'globe', dir: 'ecosystem' },
            ];

            return tiers.map(t => {
                const tierPath = path.join(this.museRoot, 'skills', t.dir);
                const agentPath = path.join(this.museRoot, '.agent', 'skills');
                const exists = fs.existsSync(tierPath) || (t.dir === 'toolkit' && fs.existsSync(agentPath));
                const item = new SkillItem(
                    `${t.name}`,
                    exists ? tierPath : '',
                    vscode.TreeItemCollapsibleState.Collapsed
                );
                item.iconPath = new vscode.ThemeIcon(t.icon);
                return item;
            }).filter(t => t.dirPath);
        }

        // Children: skills in this tier
        const items: SkillItem[] = [];
        if (fs.existsSync(element.dirPath)) {
            const findSkills = (dir: string) => {
                if (!fs.existsSync(dir)) return;
                const entries = fs.readdirSync(dir, { withFileTypes: true });
                for (const entry of entries) {
                    if (entry.isDirectory()) {
                        const skillFile = path.join(dir, entry.name, 'SKILL.md');
                        if (fs.existsSync(skillFile)) {
                            const name = extractFrontmatter(skillFile, 'name') || entry.name;
                            const desc = extractFrontmatter(skillFile, 'description');
                            const item = new SkillItem(
                                name,
                                skillFile,
                                vscode.TreeItemCollapsibleState.None
                            );
                            item.description = desc.substring(0, 50) + (desc.length > 50 ? '...' : '');
                            item.tooltip = desc;
                            item.iconPath = new vscode.ThemeIcon('note');
                            item.command = {
                                command: 'vscode.open',
                                title: 'Open Skill',
                                arguments: [vscode.Uri.file(skillFile)]
                            };
                            items.push(item);
                        } else {
                            // Recurse for ecosystem packs
                            findSkills(path.join(dir, entry.name));
                        }
                    }
                }
            };
            findSkills(element.dirPath);
        }

        return items.sort((a, b) => a.label!.toString().localeCompare(b.label!.toString()));
    }
}

class SkillItem extends vscode.TreeItem {
    constructor(
        label: string,
        public readonly dirPath: string,
        collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
    }
}

// ─── Memory Tree ────────────────────────────────────────────

class MemoryTreeProvider implements vscode.TreeDataProvider<MemoryItem> {
    private _onDidChange = new vscode.EventEmitter<MemoryItem | undefined>();
    readonly onDidChangeTreeData = this._onDidChange.event;

    constructor(private workspaceRoot: string) { }

    refresh() { this._onDidChange.fire(undefined); }

    getTreeItem(element: MemoryItem): vscode.TreeItem { return element; }

    getChildren(): MemoryItem[] {
        const items: MemoryItem[] = [];

        // MEMORIES.md
        const memoriesPath = path.join(this.workspaceRoot, 'MEMORIES.md');
        if (fs.existsSync(memoriesPath)) {
            const stat = fs.statSync(memoriesPath);
            const lines = fs.readFileSync(memoriesPath, 'utf-8').split('\n').length;
            const item = new MemoryItem(
                '📚 MEMORIES.md (Long-term)',
                `${lines} lines`,
                memoriesPath,
                vscode.TreeItemCollapsibleState.None
            );
            item.iconPath = new vscode.ThemeIcon('book');
            item.command = {
                command: 'vscode.open',
                title: 'Open',
                arguments: [vscode.Uri.file(memoriesPath)]
            };
            items.push(item);
        }

        // memory/ files
        const memoryDir = path.join(this.workspaceRoot, 'memory');
        if (fs.existsSync(memoryDir)) {
            const files = fs.readdirSync(memoryDir)
                .filter(f => f.endsWith('.md'))
                .sort()
                .reverse();

            for (const file of files.slice(0, 20)) {
                const fullPath = path.join(memoryDir, file);
                const lines = fs.readFileSync(fullPath, 'utf-8').split('\n').length;
                const stat = fs.statSync(fullPath);
                const sizeKb = (stat.size / 1024).toFixed(1);

                const item = new MemoryItem(
                    file.replace('.md', ''),
                    `${lines} lines · ${sizeKb} KB`,
                    fullPath,
                    vscode.TreeItemCollapsibleState.None
                );
                item.iconPath = new vscode.ThemeIcon('calendar');
                item.command = {
                    command: 'vscode.open',
                    title: 'Open',
                    arguments: [vscode.Uri.file(fullPath)]
                };
                items.push(item);
            }
        }

        if (items.length === 0) {
            items.push(new MemoryItem('No memory files found', '', '', vscode.TreeItemCollapsibleState.None));
        }

        return items;
    }
}

class MemoryItem extends vscode.TreeItem {
    constructor(
        label: string,
        public readonly description: string,
        public readonly filePath: string,
        collapsibleState: vscode.TreeItemCollapsibleState
    ) {
        super(label, collapsibleState);
        this.tooltip = description;
    }
}

// ─── Commands ───────────────────────────────────────────────

function showDashboard(context: vscode.ExtensionContext, workspaceRoot: string) {
    const panel = vscode.window.createWebviewPanel(
        'museDashboard',
        'MUSE Dashboard',
        vscode.ViewColumn.One,
        { enableScripts: true }
    );

    // Collect data
    const roles = collectRoles(workspaceRoot);
    const memory = collectMemory(workspaceRoot);
    const skillCount = countSkills(workspaceRoot);

    panel.webview.html = getDashboardHtml(roles, memory, skillCount);
}

function searchSkills(museRoot: string) {
    vscode.window.showInputBox({
        prompt: 'Search MUSE skills by keyword',
        placeHolder: 'e.g. git, frontend, debug'
    }).then(query => {
        if (!query) return;

        const results: { name: string; desc: string; path: string }[] = [];
        const skillDirs = [
            path.join(museRoot, 'skills'),
            path.join(museRoot, '.agent', 'skills')
        ];

        for (const dir of skillDirs) {
            if (!fs.existsSync(dir)) continue;
            findSkillsRecursive(dir, query.toLowerCase(), results);
        }

        if (results.length === 0) {
            vscode.window.showInformationMessage(`No skills found matching "${query}"`);
            return;
        }

        const picks = results.map(r => ({
            label: r.name,
            description: r.desc,
            detail: r.path
        }));

        vscode.window.showQuickPick(picks, {
            placeHolder: `Found ${results.length} skill(s)`
        }).then(pick => {
            if (pick) {
                vscode.commands.executeCommand('vscode.open', vscode.Uri.file(pick.detail!));
            }
        });
    });
}

function findSkillsRecursive(dir: string, query: string, results: { name: string; desc: string; path: string }[]) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (entry.isDirectory()) {
            const skillFile = path.join(dir, entry.name, 'SKILL.md');
            if (fs.existsSync(skillFile)) {
                const name = extractFrontmatter(skillFile, 'name') || entry.name;
                const desc = extractFrontmatter(skillFile, 'description');
                if (name.toLowerCase().includes(query) || desc.toLowerCase().includes(query)) {
                    results.push({ name, desc, path: skillFile });
                }
            }
            findSkillsRecursive(path.join(dir, entry.name), query, results);
        }
    }
}

function contextHealth(workspaceRoot: string) {
    const memoryDir = path.join(workspaceRoot, 'memory');
    const museDir = path.join(workspaceRoot, '.muse');

    let totalFiles = 0;
    let totalSize = 0;
    let oldestUnDistilled = '';

    if (fs.existsSync(memoryDir)) {
        const files = fs.readdirSync(memoryDir).filter(f => f.endsWith('.md'));
        totalFiles = files.length;
        for (const f of files) {
            totalSize += fs.statSync(path.join(memoryDir, f)).size;
        }
        if (files.length > 0) {
            oldestUnDistilled = files.sort()[0].replace('.md', '');
        }
    }

    const sizeKb = (totalSize / 1024).toFixed(1);
    const status = totalFiles >= 7 ? '🔴' : totalFiles >= 4 ? '🟡' : '🟢';

    vscode.window.showInformationMessage(
        `${status} MUSE Context Health: ${totalFiles} memory files (${sizeKb} KB)` +
        (totalFiles >= 7 ? ' — Consider running /distill' : '') +
        (oldestUnDistilled ? ` · Oldest: ${oldestUnDistilled}` : '')
    );
}

function openSkill(skillPath: string) {
    if (fs.existsSync(skillPath)) {
        vscode.commands.executeCommand('vscode.open', vscode.Uri.file(skillPath));
    }
}

function generateDashboard(workspaceRoot: string, museRoot: string | null) {
    const scriptPath = museRoot ? path.join(museRoot, 'scripts', 'dashboard.sh') : null;
    if (scriptPath && fs.existsSync(scriptPath)) {
        const terminal = vscode.window.createTerminal('MUSE Dashboard');
        terminal.sendText(`"${scriptPath}" "${workspaceRoot}" && open "${workspaceRoot}/.muse/dashboard.html"`);
        terminal.show();
    } else {
        vscode.window.showWarningMessage('MUSE dashboard.sh not found. Install MUSE first.');
    }
}

// ─── Data Collectors ────────────────────────────────────────

function collectRoles(root: string): { name: string; l0: string; lines: number }[] {
    const museDir = path.join(root, '.muse');
    if (!fs.existsSync(museDir)) return [];

    return fs.readdirSync(museDir)
        .filter(f => f.endsWith('.md'))
        .map(f => ({
            name: f.replace('.md', ''),
            l0: extractL0(path.join(museDir, f)),
            lines: fs.readFileSync(path.join(museDir, f), 'utf-8').split('\n').length
        }));
}

function collectMemory(root: string): { date: string; lines: number; size: number }[] {
    const memDir = path.join(root, 'memory');
    if (!fs.existsSync(memDir)) return [];

    return fs.readdirSync(memDir)
        .filter(f => f.endsWith('.md'))
        .sort().reverse()
        .slice(0, 20)
        .map(f => {
            const fp = path.join(memDir, f);
            return {
                date: f.replace('.md', ''),
                lines: fs.readFileSync(fp, 'utf-8').split('\n').length,
                size: fs.statSync(fp).size
            };
        });
}

function countSkills(root: string): number {
    let count = 0;
    const dirs = [path.join(root, 'skills'), path.join(root, '.agent', 'skills')];
    for (const dir of dirs) {
        if (fs.existsSync(dir)) {
            const countRecursive = (d: string) => {
                for (const e of fs.readdirSync(d, { withFileTypes: true })) {
                    if (e.isFile() && e.name === 'SKILL.md') count++;
                    if (e.isDirectory()) countRecursive(path.join(d, e.name));
                }
            };
            countRecursive(dir);
        }
    }
    return count;
}

// ─── Dashboard HTML ─────────────────────────────────────────

function getDashboardHtml(
    roles: { name: string; l0: string; lines: number }[],
    memory: { date: string; lines: number; size: number }[],
    skillCount: number
): string {
    const rolesHtml = roles.map(r => `
        <div class="card">
            <div class="card-header">
                <span class="card-title">${r.name}</span>
                <span class="badge">${r.lines} lines</span>
            </div>
            <div class="card-body">${escapeHtml(r.l0.substring(0, 100))}</div>
        </div>
    `).join('');

    const memoryHtml = memory.map(m => `
        <div class="timeline-item">
            <div class="timeline-date">${m.date}</div>
            <div class="timeline-meta">${m.lines} lines · ${(m.size / 1024).toFixed(1)} KB</div>
        </div>
    `).join('');

    return `<!DOCTYPE html>
    <html><head>
    <style>
        body { font-family: -apple-system, sans-serif; background: #1e1e2e; color: #cdd6f4; padding: 24px; }
        h1 { color: #cba6f7; text-align: center; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 24px 0; }
        .stat { background: #313244; border-radius: 12px; padding: 20px; text-align: center; }
        .stat-value { font-size: 2rem; font-weight: 700; color: #89b4fa; }
        .stat-label { font-size: 0.8rem; color: #6c7086; text-transform: uppercase; }
        .section { margin: 24px 0; }
        .section h2 { color: #a6adc8; border-bottom: 1px solid #45475a; padding-bottom: 8px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
        .card { background: #313244; border-radius: 12px; padding: 16px; border: 1px solid #45475a; }
        .card:hover { border-color: #cba6f7; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .card-title { font-weight: 600; text-transform: capitalize; }
        .badge { font-size: 0.7rem; background: rgba(203,166,247,0.2); color: #cba6f7; padding: 2px 8px; border-radius: 10px; }
        .card-body { font-size: 0.85rem; color: #6c7086; }
        .timeline-item { padding: 12px 16px; background: #313244; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #89b4fa; }
        .timeline-date { color: #89b4fa; font-weight: 600; font-size: 0.9rem; }
        .timeline-meta { color: #6c7086; font-size: 0.8rem; }
    </style>
    </head><body>
        <h1>🎭 MUSE Dashboard</h1>
        <div class="stats">
            <div class="stat"><div class="stat-value">${roles.length}</div><div class="stat-label">Active Roles</div></div>
            <div class="stat"><div class="stat-value">${memory.length}</div><div class="stat-label">Memory Files</div></div>
            <div class="stat"><div class="stat-value">${skillCount}</div><div class="stat-label">Skills</div></div>
        </div>
        <div class="section"><h2>🎭 Roles</h2><div class="grid">${rolesHtml}</div></div>
        <div class="section"><h2>🧠 Memory Timeline</h2>${memoryHtml}</div>
    </body></html>`;
}

function escapeHtml(str: string): string {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
