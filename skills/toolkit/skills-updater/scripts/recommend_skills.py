#!/usr/bin/env python3
"""
Skill Recommender - Fetches trending and recommended skills from marketplaces.

Usage:
    python recommend_skills.py [--source <source>] [--limit <n>] [--json]

Sources:
    - skills.sh: Community skills leaderboard
    - skillsmp.com: Curated marketplace (if accessible)
    - all: All sources (default)

Examples:
    python recommend_skills.py                     # Show trending from all sources
    python recommend_skills.py --source skills.sh  # Only skills.sh
    python recommend_skills.py --limit 10          # Show top 10
    python recommend_skills.py --json              # Output as JSON
"""

import json
import sys
import argparse
import re
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import urllib.request
from html.parser import HTMLParser

# Import i18n module
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
from i18n import get_i18n, t  # noqa: E402


@dataclass
class RecommendedSkill:
    name: str
    installs: Optional[int]
    source: str
    repo: Optional[str]
    description: Optional[str]
    install_command: str
    category: Optional[str] = None


class SkillsShParser(HTMLParser):
    """Parse skills.sh leaderboard page."""

    def __init__(self):
        super().__init__()
        self.skills = []
        self.current_skill = {}
        self.in_skill_item = False
        self.capture_text = False
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Look for skill entries in the leaderboard
        if tag == "div" and "class" in attrs_dict:
            classes = attrs_dict.get("class", "")
            if classes and ("skill" in classes.lower() or "item" in classes.lower()):
                self.in_skill_item = True
                self.current_skill = {}

        if self.in_skill_item:
            if tag == "a" and "href" in attrs_dict:
                href = attrs_dict.get("href", "")
                if href and ("github.com" in href or "/" in href):
                    self.current_skill["repo"] = href

            if tag in ["span", "p", "div", "h3", "h4"]:
                self.capture_text = True
                self.current_tag = tag

    def handle_endtag(self, tag):
        if tag == "div" and self.in_skill_item:
            if self.current_skill.get("name"):
                self.skills.append(self.current_skill)
            self.in_skill_item = False
            self.current_skill = {}

        self.capture_text = False
        self.current_tag = None

    def handle_data(self, data):
        if self.capture_text and self.in_skill_item:
            text = data.strip()
            if not text:
                return

            # Try to extract install count
            install_match = re.search(r"([\d,\.]+)\s*[kKmM]?\s*install", text, re.IGNORECASE)
            if install_match:
                count_str = install_match.group(1).replace(",", "")
                try:
                    count = float(count_str)
                    if "k" in text.lower():
                        count *= 1000
                    elif "m" in text.lower():
                        count *= 1000000
                    self.current_skill["installs"] = int(count)
                except Exception:
                    pass

            # Capture name (usually in h3/h4 or first significant text)
            if self.current_tag in ["h3", "h4"] or "name" not in self.current_skill:
                if len(text) > 2 and len(text) < 100 and not text.startswith("http"):
                    if "install" not in text.lower() and not re.match(r"^[\d,\.]+$", text):
                        self.current_skill["name"] = text


def fetch_skills_sh(limit: int = 20) -> List[RecommendedSkill]:
    """Fetch trending skills from skills.sh."""
    url = "https://skills.sh/"

    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) skills-updater/1.0"
        })
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print(f"Warning: Could not fetch skills.sh: {e}", file=sys.stderr)
        return get_hardcoded_skills_sh_top(limit)

    # Try to parse the page
    parser = SkillsShParser()
    try:
        parser.feed(html)
    except Exception:
        pass

    skills = []

    if parser.skills:
        for item in parser.skills[:limit]:
            if "name" in item:
                repo = item.get("repo", "")
                if repo.startswith("/"):
                    repo = repo.lstrip("/")

                skills.append(RecommendedSkill(
                    name=item["name"],
                    installs=item.get("installs"),
                    source="skills.sh",
                    repo=repo if repo else None,
                    description=None,
                    install_command=f"npx skills add {repo}" if repo else f"npx skills add <owner>/{item['name']}"
                ))
    else:
        # Fallback to hardcoded top skills if parsing fails
        skills = get_hardcoded_skills_sh_top(limit)

    return skills


def load_recommendations_config() -> Dict:
    """Load recommendations from external config file."""
    config_file = script_dir / "recommendations.json"
    if config_file.exists():
        try:
            with open(config_file, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_hardcoded_skills_sh_top(limit: int = 20) -> List[RecommendedSkill]:
    """Return top skills from config file as fallback."""
    config = load_recommendations_config()
    fallback_trending = config.get("fallback_trending", [])

    skills = []
    for item in fallback_trending[:limit]:
        skills.append(RecommendedSkill(
            name=item.get("name", ""),
            installs=item.get("installs"),
            source="skills.sh",
            repo=item.get("repo"),
            description=None,
            install_command=f"npx skills add {item.get('repo', '')}"
        ))

    return skills


def get_installed_categories() -> Set[str]:
    """Get categories of installed skills for personalized recommendations."""
    plugins_file = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

    if not plugins_file.exists():
        return set()

    try:
        with open(plugins_file, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return set()

    # Extract keywords from skill names
    categories = set()

    for key in data.get("plugins", {}).keys():
        skill_name = key.split("@")[0]
        # Common category keywords
        if any(kw in skill_name.lower() for kw in ["github", "git", "code"]):
            categories.add("developer-tools")
        if any(kw in skill_name.lower() for kw in ["doc", "pdf", "ppt", "excel", "word"]):
            categories.add("document-tools")
        if any(kw in skill_name.lower() for kw in ["test", "qa", "playwright"]):
            categories.add("testing")
        if any(kw in skill_name.lower() for kw in ["front", "ui", "design", "css"]):
            categories.add("frontend")
        if any(kw in skill_name.lower() for kw in ["security", "safe"]):
            categories.add("security")
        if any(kw in skill_name.lower() for kw in ["learn", "study", "explain"]):
            categories.add("learning")

    return categories


def get_personalized_recommendations(installed_categories: Set[str], limit: int = 5) -> List[RecommendedSkill]:
    """Get personalized skill recommendations based on installed categories."""
    config = load_recommendations_config()
    recommendations_by_category = config.get("category_recommendations", {})
    default_recommendations = config.get("default_recommendations", [])

    recommendations = []
    seen_names = set()

    # Add category-specific recommendations
    for category in installed_categories:
        if category in recommendations_by_category:
            for item in recommendations_by_category[category]:
                name = item.get("name", "")
                if name and name not in seen_names:
                    recommendations.append(RecommendedSkill(
                        name=name,
                        installs=None,
                        source="personalized",
                        repo=item.get("repo"),
                        description=item.get("description"),
                        install_command=f"claude /install {name}",
                        category=category
                    ))
                    seen_names.add(name)

    # Fill with defaults if needed
    for item in default_recommendations:
        if len(recommendations) >= limit:
            break
        name = item.get("name", "")
        if name and name not in seen_names:
            recommendations.append(RecommendedSkill(
                name=name,
                installs=None,
                source="personalized",
                repo=item.get("repo"),
                description=item.get("description"),
                install_command=f"claude /install {name}"
            ))
            seen_names.add(name)

    return recommendations[:limit]


def format_installs(count: Optional[int]) -> str:
    """Format install count for display."""
    if count is None:
        return ""

    if count >= 1000000:
        return f"{count/1000000:.1f}M"
    elif count >= 1000:
        return f"{count/1000:.1f}K"
    else:
        return str(count)


def print_recommendations(trending: List[RecommendedSkill],
                          personalized: List[RecommendedSkill],
                          as_json: bool = False):
    """Print skill recommendations."""
    if as_json:
        output = {
            "trending": [],
            "personalized": []
        }

        for skill in trending:
            output["trending"].append({
                "name": skill.name,
                "installs": skill.installs,
                "source": skill.source,
                "repo": skill.repo,
                "install_command": skill.install_command
            })

        for skill in personalized:
            output["personalized"].append({
                "name": skill.name,
                "description": skill.description,
                "category": skill.category,
                "repo": skill.repo,
                "install_command": skill.install_command
            })

        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print(f"🔥 {t('trending_skills')}")
    print("━" * 18)
    print()

    if trending:
        print(f"{t('from_skills_sh')} ({t('top_n', n=len(trending))}):")
        for i, skill in enumerate(trending, 1):
            installs_str = format_installs(skill.installs)
            if installs_str:
                installs_str = f" ({installs_str} {t('installs')})"
            print(f"{i:2}. {skill.name}{installs_str}")
            print(f"    {skill.install_command}")
            print()
    else:
        print(t('could_not_fetch'))
        print()

    if personalized:
        print(f"💡 {t('personalized_recommendations')}")
        print("━" * 31)
        print()
        print(t('based_on_installed'))
        for skill in personalized:
            category_str = f" [{skill.category}]" if skill.category else ""
            print(f"• {skill.name}{category_str}")
            if skill.description:
                print(f"  {skill.description}")
            print(f"  → {skill.install_command}")
            print()

    print("━" * 40)
    print(t('install_hint'))
    print(t('install_hint_npx'))


def main():
    parser = argparse.ArgumentParser(description="Discover recommended skills")
    parser.add_argument("--source", choices=["skills.sh", "skillsmp.com", "all"],
                        default="all", help="Source for recommendations")
    parser.add_argument("--limit", type=int, default=10,
                        help="Number of trending skills to show")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    parser.add_argument("--lang", choices=["en", "zh"],
                        help="Language for output (auto-detected if not specified)")
    args = parser.parse_args()

    # Initialize i18n
    if args.lang:
        get_i18n(args.lang)

    if not args.json:
        print(f"🔍 {t('fetching_recommendations')}\n")

    trending = []
    personalized = []

    # Fetch trending skills
    if args.source in ["skills.sh", "all"]:
        trending = fetch_skills_sh(limit=args.limit)

    # Get personalized recommendations
    installed_categories = get_installed_categories()
    if installed_categories:
        personalized = get_personalized_recommendations(installed_categories)
    else:
        # Default recommendations for new users
        personalized = get_personalized_recommendations(set(), limit=5)

    print_recommendations(trending, personalized, as_json=args.json)


if __name__ == "__main__":
    main()
