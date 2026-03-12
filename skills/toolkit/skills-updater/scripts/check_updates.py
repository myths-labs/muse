#!/usr/bin/env python3
"""
Skill Update Checker - Scans installed skills and checks for available updates.

Usage:
    python check_updates.py [--skill <name>] [--json]

Examples:
    python check_updates.py                    # Check all installed skills
    python check_updates.py --skill skill-creator  # Check specific skill
    python check_updates.py --json             # Output as JSON
"""

import json
import sys
import argparse
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import urllib.request
import urllib.error

# Import i18n module
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
from i18n import get_i18n, t  # noqa: E402


class UpdateStatus(Enum):
    UP_TO_DATE = "up_to_date"
    UPDATE_AVAILABLE = "update_available"
    UNKNOWN_VERSION = "unknown_version"
    ERROR = "error"


@dataclass
class SkillInfo:
    name: str
    marketplace: str
    local_version: str
    remote_version: Optional[str]
    status: UpdateStatus
    install_path: str
    git_commit_sha: Optional[str] = None
    remote_commit_sha: Optional[str] = None
    error_message: Optional[str] = None


def get_plugins_dir() -> Path:
    """Get the Claude Code plugins directory."""
    return Path.home() / ".claude" / "plugins"


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


def parse_plugin_key(key: str) -> Tuple[str, str]:
    """Parse plugin key into (skill_name, marketplace)."""
    parts = key.rsplit("@", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return key, "unknown"


def get_github_repo_from_marketplace(marketplace_name: str, marketplaces: Dict) -> Optional[str]:
    """Get the GitHub repo from marketplace info."""
    marketplace_info = marketplaces.get(marketplace_name, {})
    source = marketplace_info.get("source", {})

    if source.get("source") == "github":
        return source.get("repo")
    elif source.get("source") == "git":
        url = source.get("url", "")
        # Parse git URL to get owner/repo
        if "github.com" in url:
            # Handle formats: https://github.com/owner/repo.git or git@github.com:owner/repo.git
            url = url.replace(".git", "")
            if "github.com/" in url:
                return url.split("github.com/")[-1]
            elif "github.com:" in url:
                return url.split("github.com:")[-1]

    return None


def fetch_remote_marketplace_json(repo: str) -> Optional[Dict]:
    """Fetch marketplace.json from GitHub repo."""
    url = f"https://raw.githubusercontent.com/{repo}/main/.claude-plugin/marketplace.json"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "skills-updater/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Try HEAD branch instead of main
            url_head = url.replace("/main/", "/HEAD/")
            try:
                req = urllib.request.Request(url_head, headers={"User-Agent": "skills-updater/1.0"})
                with urllib.request.urlopen(req, timeout=10) as response:
                    return json.loads(response.read().decode())
            except Exception:
                pass
        return None
    except Exception:
        return None


def fetch_remote_commit_sha(repo: str) -> Optional[str]:
    """Fetch the latest commit SHA from GitHub."""
    url = f"https://api.github.com/repos/{repo}/commits/main"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "skills-updater/1.0",
            "Accept": "application/vnd.github.v3+json"
        })
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get("sha")
    except Exception:
        # Try HEAD branch
        url_head = url.replace("/main", "/HEAD")
        try:
            req = urllib.request.Request(url_head, headers={
                "User-Agent": "skills-updater/1.0",
                "Accept": "application/vnd.github.v3+json"
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data.get("sha")
        except Exception:
            return None


def get_skill_version_from_marketplace_json(marketplace_json: Dict, skill_name: str) -> Optional[str]:
    """Extract skill version from marketplace.json."""
    plugins = marketplace_json.get("plugins", [])
    for plugin in plugins:
        if plugin.get("name") == skill_name:
            return plugin.get("version")
    return None


def compare_versions(local: str, remote: str) -> bool:
    """Compare versions. Returns True if remote is newer."""
    if local == remote:
        return False

    # Handle unknown versions
    if local in ["unknown", "", None]:
        return True

    # Try semantic version comparison
    try:
        local_parts = [int(x) for x in local.split(".")]
        remote_parts = [int(x) for x in remote.split(".")]

        # Pad shorter version with zeros
        max_len = max(len(local_parts), len(remote_parts))
        local_parts.extend([0] * (max_len - len(local_parts)))
        remote_parts.extend([0] * (max_len - len(remote_parts)))

        return remote_parts > local_parts
    except Exception:
        # Fall back to string comparison
        return local != remote


def compare_commit_sha(local_sha: Optional[str], remote_sha: Optional[str]) -> bool:
    """Compare commit SHAs. Returns True if different."""
    if not local_sha or not remote_sha:
        return False

    # Handle short SHA comparison
    min_len = min(len(local_sha), len(remote_sha))
    return local_sha[:min_len] != remote_sha[:min_len]


def check_skill_update(skill_name: str, marketplace: str, plugin_info: Dict, marketplaces: Dict) -> SkillInfo:
    """Check if a skill has an available update."""
    local_version = plugin_info.get("version", "unknown")
    install_path = plugin_info.get("installPath", "")
    git_commit_sha = plugin_info.get("gitCommitSha")

    # Get GitHub repo
    repo = get_github_repo_from_marketplace(marketplace, marketplaces)

    if not repo:
        return SkillInfo(
            name=skill_name,
            marketplace=marketplace,
            local_version=local_version,
            remote_version=None,
            status=UpdateStatus.ERROR,
            install_path=install_path,
            git_commit_sha=git_commit_sha,
            error_message="Could not determine GitHub repo"
        )

    # Try to get remote version from marketplace.json
    remote_marketplace = fetch_remote_marketplace_json(repo)
    remote_version = None

    if remote_marketplace:
        remote_version = get_skill_version_from_marketplace_json(remote_marketplace, skill_name)

    # Fetch remote commit SHA as fallback
    remote_commit = fetch_remote_commit_sha(repo)

    # Determine update status
    if local_version in ["unknown", "", None]:
        # Unknown local version - check by commit
        if git_commit_sha and remote_commit:
            if compare_commit_sha(git_commit_sha, remote_commit):
                status = UpdateStatus.UPDATE_AVAILABLE
            else:
                status = UpdateStatus.UP_TO_DATE
        else:
            status = UpdateStatus.UNKNOWN_VERSION
    elif remote_version:
        # Have both versions - compare them
        if compare_versions(local_version, remote_version):
            status = UpdateStatus.UPDATE_AVAILABLE
        else:
            status = UpdateStatus.UP_TO_DATE
    elif remote_commit and git_commit_sha:
        # No version but have commits - compare commits
        if compare_commit_sha(git_commit_sha, remote_commit):
            status = UpdateStatus.UPDATE_AVAILABLE
        else:
            status = UpdateStatus.UP_TO_DATE
    else:
        status = UpdateStatus.UNKNOWN_VERSION

    return SkillInfo(
        name=skill_name,
        marketplace=marketplace,
        local_version=local_version,
        remote_version=remote_version,
        status=status,
        install_path=install_path,
        git_commit_sha=git_commit_sha,
        remote_commit_sha=remote_commit[:12] if remote_commit else None
    )


def check_all_updates(filter_skill: Optional[str] = None) -> List[SkillInfo]:
    """Check updates for all installed skills."""
    installed = load_installed_plugins()
    marketplaces = load_known_marketplaces()

    results = []

    for key, plugin_list in installed.get("plugins", {}).items():
        if not plugin_list:
            continue

        skill_name, marketplace = parse_plugin_key(key)

        if filter_skill and skill_name != filter_skill:
            continue

        # Use the first (usually only) plugin entry
        plugin_info = plugin_list[0]

        skill_info = check_skill_update(skill_name, marketplace, plugin_info, marketplaces)
        results.append(skill_info)

    return results


def print_results(results: List[SkillInfo], as_json: bool = False):
    """Print the update check results."""
    if as_json:
        output = []
        for r in results:
            output.append({
                "name": r.name,
                "marketplace": r.marketplace,
                "local_version": r.local_version,
                "remote_version": r.remote_version,
                "status": r.status.value,
                "install_path": r.install_path,
                "git_commit_sha": r.git_commit_sha,
                "remote_commit_sha": r.remote_commit_sha,
                "error_message": r.error_message
            })
        print(json.dumps(output, indent=2))
        return

    # Group by status
    up_to_date = [r for r in results if r.status == UpdateStatus.UP_TO_DATE]
    updates_available = [r for r in results if r.status == UpdateStatus.UPDATE_AVAILABLE]
    unknown = [r for r in results if r.status == UpdateStatus.UNKNOWN_VERSION]
    errors = [r for r in results if r.status == UpdateStatus.ERROR]

    print(f"📦 {t('installed_skills_status')}")
    print("━" * 26)
    print()

    if up_to_date:
        print(f"✅ {t('up_to_date')} ({len(up_to_date)}):")
        for r in up_to_date:
            version_str = r.local_version
            if r.git_commit_sha and r.local_version in ["unknown", ""]:
                version_str = r.git_commit_sha[:12]
            print(f"   • {r.name}@{r.marketplace} ({version_str})")
        print()

    if updates_available:
        print(f"⬆️  {t('updates_available')} ({len(updates_available)}):")
        for r in updates_available:
            local_str = r.local_version
            remote_str = r.remote_version or r.remote_commit_sha or "newer"
            if r.local_version in ["unknown", ""]:
                local_str = r.git_commit_sha[:12] if r.git_commit_sha else "unknown"
            print(f"   • {r.name}@{r.marketplace}")
            print(f"     {t('local')}: {local_str} → {t('remote')}: {remote_str}")
        print()

    if unknown:
        print(f"⚠️  {t('unknown_version')} ({len(unknown)}):")
        for r in unknown:
            print(f"   • {r.name}@{r.marketplace} ({r.local_version})")
        print()

    if errors:
        print(f"❌ {t('errors')} ({len(errors)}):")
        for r in errors:
            print(f"   • {r.name}@{r.marketplace}: {r.error_message}")
        print()

    # Summary
    print("━" * 26)
    print(f"{t('total')}: {len(results)} {t('skills')} | "
          f"{len(updates_available)} {t('updates_available_count')}")


def main():
    parser = argparse.ArgumentParser(description="Check for skill updates")
    parser.add_argument("--skill", help="Check specific skill only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--lang", choices=["en", "zh"],
                        help="Language for output (auto-detected if not specified)")
    args = parser.parse_args()

    # Initialize i18n
    if args.lang:
        get_i18n(args.lang)

    if not args.json:
        print(f"🔍 {t('checking_updates')}\n")

    results = check_all_updates(filter_skill=args.skill)

    if not results:
        if args.skill:
            print(t('skill_not_found', skill=args.skill))
        else:
            print(t('no_installed_skills'))
        sys.exit(1)

    print_results(results, as_json=args.json)

    # Exit with code 1 if updates available (useful for CI/CD)
    updates_available = any(r.status == UpdateStatus.UPDATE_AVAILABLE for r in results)
    sys.exit(0 if not updates_available else 1)


if __name__ == "__main__":
    main()
