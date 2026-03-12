#!/usr/bin/env python3
"""
Marketplace Updater - Updates marketplace repos and reinstalls affected skills.

Usage:
    python update_marketplace.py <marketplace_name> [--auto-install] [--json]

Examples:
    python update_marketplace.py anthropic-agent-skills
    python update_marketplace.py anthropic-agent-skills --auto-install
    python update_marketplace.py claude-plugins-official --json
"""

import json
import sys
import argparse
import subprocess
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Import i18n module
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
from i18n import get_i18n, t  # noqa: E402


@dataclass
class UpdateResult:
    marketplace: str
    updated: bool
    local_commit: str
    remote_commit: str
    commits_behind: int
    commit_messages: List[str]
    affected_skills: List[str]
    reinstalled_skills: List[str]
    failed_skills: List[str]
    error: Optional[str] = None


def get_plugins_dir() -> Path:
    """Get the Claude Code plugins directory."""
    return Path.home() / ".claude" / "plugins"


def get_marketplace_dir(marketplace_name: str) -> Optional[Path]:
    """Get the marketplace directory path."""
    marketplace_dir = get_plugins_dir() / "marketplaces" / marketplace_name
    if marketplace_dir.exists():
        return marketplace_dir
    return None


def load_installed_plugins() -> Dict:
    """Load the installed_plugins.json file."""
    plugins_file = get_plugins_dir() / "installed_plugins.json"
    if not plugins_file.exists():
        return {"version": 2, "plugins": {}}

    with open(plugins_file, encoding='utf-8') as f:
        return json.load(f)


def load_known_marketplaces() -> Dict:
    """Load the known_marketplaces.json file."""
    marketplaces_file = get_plugins_dir() / "known_marketplaces.json"
    if not marketplaces_file.exists():
        return {}

    with open(marketplaces_file, encoding='utf-8') as f:
        return json.load(f)


def get_affected_skills(marketplace_name: str) -> List[str]:
    """Get list of installed skills from the specified marketplace."""
    installed = load_installed_plugins()
    affected = []

    for key in installed.get("plugins", {}).keys():
        if key.endswith(f"@{marketplace_name}"):
            skill_name = key.rsplit("@", 1)[0]
            affected.append(skill_name)

    return affected


def get_default_branch(repo_dir: Path) -> str:
    """
    Detect the default branch of a git repository.

    Tries multiple methods:
    1. Check symbolic-ref of origin/HEAD
    2. Check remote show origin
    3. Fall back to 'main', then 'master'

    Returns: branch name (e.g., 'main', 'master')
    """
    # Method 1: Try symbolic-ref
    result = subprocess.run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=repo_dir,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        # Output like: refs/remotes/origin/main
        ref = result.stdout.strip()
        if ref:
            return ref.split("/")[-1]

    # Method 2: Check if origin/main exists
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/main"],
        cwd=repo_dir,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return "main"

    # Method 3: Check if origin/master exists
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/master"],
        cwd=repo_dir,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return "master"

    # Default fallback
    return "main"


def git_fetch_and_check(marketplace_dir: Path) -> Tuple[str, str, int, List[str]]:
    """
    Fetch remote and check for updates.

    Returns: (local_commit, remote_commit, commits_behind, commit_messages)
    """
    # Detect default branch
    default_branch = get_default_branch(marketplace_dir)

    # Get local commit
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=marketplace_dir,
        capture_output=True,
        text=True
    )
    local_commit = result.stdout.strip()[:12] if result.returncode == 0 else "unknown"

    # Fetch remote
    subprocess.run(
        ["git", "fetch", "origin", default_branch, "--quiet"],
        cwd=marketplace_dir,
        capture_output=True
    )

    # Get remote commit
    result = subprocess.run(
        ["git", "rev-parse", f"origin/{default_branch}"],
        cwd=marketplace_dir,
        capture_output=True,
        text=True
    )
    remote_commit = result.stdout.strip()[:12] if result.returncode == 0 else "unknown"

    # Count commits behind
    result = subprocess.run(
        ["git", "rev-list", f"HEAD..origin/{default_branch}", "--count"],
        cwd=marketplace_dir,
        capture_output=True,
        text=True
    )
    commits_behind = int(result.stdout.strip()) if result.returncode == 0 else 0

    # Get commit messages
    commit_messages = []
    if commits_behind > 0:
        result = subprocess.run(
            ["git", "log", f"HEAD..origin/{default_branch}", "--oneline"],
            cwd=marketplace_dir,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            commit_messages = result.stdout.strip().split("\n")[:10]  # Limit to 10

    return local_commit, remote_commit, commits_behind, commit_messages


def git_pull(marketplace_dir: Path) -> bool:
    """Pull latest changes from remote."""
    default_branch = get_default_branch(marketplace_dir)
    result = subprocess.run(
        ["git", "pull", "origin", default_branch],
        cwd=marketplace_dir,
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def reinstall_skill(skill_name: str, marketplace_name: str) -> bool:
    """
    Reinstall a skill using Claude Code's install mechanism.

    This generates an install command that should be executed by Claude Code.
    """
    # Generate the install command
    install_cmd = f"/install {skill_name}@{marketplace_name}"

    # Write command to a temporary file that can be read by Claude
    cmd_file = get_plugins_dir() / ".pending_installs"
    try:
        with open(cmd_file, "a", encoding='utf-8') as f:
            f.write(f"{install_cmd}\n")
        return True
    except Exception:
        return False


def update_marketplace(
    marketplace_name: str,
    auto_install: bool = False,
    interactive: bool = True
) -> UpdateResult:
    """
    Update a marketplace and optionally reinstall affected skills.

    Args:
        marketplace_name: Name of the marketplace to update
        auto_install: Whether to automatically reinstall affected skills
        interactive: Whether to show progress output

    Returns:
        UpdateResult with details of the update
    """
    i18n = get_i18n()

    # Get marketplace directory
    marketplace_dir = get_marketplace_dir(marketplace_name)
    if not marketplace_dir:
        return UpdateResult(
            marketplace=marketplace_name,
            updated=False,
            local_commit="",
            remote_commit="",
            commits_behind=0,
            commit_messages=[],
            affected_skills=[],
            reinstalled_skills=[],
            failed_skills=[],
            error=f"Marketplace '{marketplace_name}' not found"
        )

    if interactive:
        print(f"📡 {t('fetching_remote')}")

    # Check for updates
    local_commit, remote_commit, commits_behind, commit_messages = git_fetch_and_check(marketplace_dir)

    # Get affected skills
    affected_skills = get_affected_skills(marketplace_name)

    if commits_behind == 0:
        return UpdateResult(
            marketplace=marketplace_name,
            updated=False,
            local_commit=local_commit,
            remote_commit=remote_commit,
            commits_behind=0,
            commit_messages=[],
            affected_skills=affected_skills,
            reinstalled_skills=[],
            failed_skills=[]
        )

    if interactive:
        print(f"\n{t('current_commit')}: {local_commit}")
        print(f"{t('remote_commit')}: {remote_commit}")
        print(f"{t('status')}: {t('commits_behind', count=commits_behind)}")

        if commit_messages:
            print(f"\n📝 {t('update_content')}:")
            for msg in commit_messages[:5]:
                print(f"   • {msg}")
            if len(commit_messages) > 5:
                print(f"   ... +{len(commit_messages) - 5} more")

        if affected_skills:
            print(f"\n📦 {t('affected_skills')}: {', '.join(affected_skills)}")
        else:
            print(f"\n📦 {t('no_affected_skills')}")

    # Pull updates
    if interactive:
        print(f"\n📥 {t('updating_marketplace', marketplace=marketplace_name)}")

    if not git_pull(marketplace_dir):
        return UpdateResult(
            marketplace=marketplace_name,
            updated=False,
            local_commit=local_commit,
            remote_commit=remote_commit,
            commits_behind=commits_behind,
            commit_messages=commit_messages,
            affected_skills=affected_skills,
            reinstalled_skills=[],
            failed_skills=[],
            error="Git pull failed"
        )

    if interactive:
        print(f"✅ {t('marketplace_updated')}")

    # Reinstall affected skills if requested
    reinstalled = []
    failed = []

    if auto_install and affected_skills:
        if interactive:
            print(f"\n🔄 {t('reinstalling_skills')}")

        for skill in affected_skills:
            if interactive:
                print(f"   {t('reinstalling_skill', skill=skill)}")

            if reinstall_skill(skill, marketplace_name):
                reinstalled.append(skill)
                if interactive:
                    print(f"   ✅ {t('skill_reinstalled', skill=skill)}")
            else:
                failed.append(skill)
                if interactive:
                    print(f"   ❌ {t('skill_reinstall_failed', skill=skill)}")

        if interactive and reinstalled:
            print(f"\n✅ {t('all_skills_updated')}")

    return UpdateResult(
        marketplace=marketplace_name,
        updated=True,
        local_commit=local_commit,
        remote_commit=remote_commit,
        commits_behind=commits_behind,
        commit_messages=commit_messages,
        affected_skills=affected_skills,
        reinstalled_skills=reinstalled,
        failed_skills=failed
    )


def print_result_json(result: UpdateResult):
    """Print result as JSON."""
    output = {
        "marketplace": result.marketplace,
        "updated": result.updated,
        "local_commit": result.local_commit,
        "remote_commit": result.remote_commit,
        "commits_behind": result.commits_behind,
        "commit_messages": result.commit_messages,
        "affected_skills": result.affected_skills,
        "reinstalled_skills": result.reinstalled_skills,
        "failed_skills": result.failed_skills,
        "error": result.error
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def get_pending_installs() -> List[str]:
    """Get list of pending skill installs."""
    cmd_file = get_plugins_dir() / ".pending_installs"
    if not cmd_file.exists():
        return []

    with open(cmd_file, encoding='utf-8') as f:
        commands = [line.strip() for line in f if line.strip()]

    # Clear the file
    cmd_file.unlink()

    return commands


def main():
    parser = argparse.ArgumentParser(description="Update marketplace and reinstall skills")
    parser.add_argument("marketplace", help="Marketplace name to update")
    parser.add_argument("--auto-install", action="store_true",
                        help="Automatically reinstall affected skills")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--lang", choices=["en", "zh"],
                        help="Language for output (auto-detected if not specified)")
    args = parser.parse_args()

    # Initialize i18n
    if args.lang:
        get_i18n(args.lang)

    result = update_marketplace(
        args.marketplace,
        auto_install=args.auto_install,
        interactive=not args.json
    )

    if args.json:
        print_result_json(result)
    elif result.error:
        print(f"❌ {t('error')}: {result.error}")
        sys.exit(1)

    # Output pending installs for Claude to execute
    pending = get_pending_installs()
    if pending:
        print("\n" + "=" * 40)
        print("PENDING_SKILL_INSTALLS:")
        for cmd in pending:
            print(cmd)
        print("=" * 40)


if __name__ == "__main__":
    main()
