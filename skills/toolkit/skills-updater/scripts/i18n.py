#!/usr/bin/env python3
"""
Internationalization (i18n) module for skills-updater.

Detects user locale from environment and provides translated strings.
Supports: English (en), Chinese (zh)
"""

import os
import locale
from typing import Dict, Optional


# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Check updates
        "checking_updates": "Checking for skill updates...",
        "installed_skills_status": "Installed Skills Status",
        "up_to_date": "Up-to-date",
        "updates_available": "Updates Available",
        "unknown_version": "Unknown Version",
        "errors": "Errors",
        "total": "Total",
        "skills": "skills",
        "updates_available_count": "updates available",
        "skill_not_found": "Skill '{skill}' not found.",
        "no_installed_skills": "No installed skills found.",
        "local": "Local",
        "remote": "Remote",

        # Update marketplace
        "updating_marketplace": "Updating marketplace: {marketplace}",
        "marketplace_up_to_date": "Marketplace is up to date",
        "marketplace_updated": "Marketplace updated successfully",
        "commits_behind": "Behind by {count} commit(s)",
        "update_content": "Update content",
        "affected_skills": "Affected skills",
        "reinstalling_skills": "Reinstalling affected skills...",
        "reinstalling_skill": "Reinstalling: {skill}",
        "skill_reinstalled": "Reinstalled: {skill}",
        "skill_reinstall_failed": "Failed to reinstall: {skill}",
        "all_skills_updated": "All affected skills have been updated",
        "no_affected_skills": "No installed skills affected by this update",
        "confirm_update": "Confirm update? Enter 'yes' to proceed",
        "update_cancelled": "Update cancelled",
        "fetching_remote": "Fetching remote updates...",
        "current_commit": "Current commit",
        "remote_commit": "Remote commit",
        "status": "Status",

        # Recommendations
        "fetching_recommendations": "Fetching skill recommendations...",
        "trending_skills": "Trending Skills",
        "from_skills_sh": "From skills.sh",
        "top_n": "Top {n}",
        "installs": "installs",
        "personalized_recommendations": "Personalized Recommendations",
        "based_on_installed": "Based on your installed skills:",
        "install_hint": "Install: claude /install <skill-name>@<marketplace>",
        "install_hint_npx": "    or: npx skills add <owner/repo>",
        "could_not_fetch": "Could not fetch trending skills.",

        # Common
        "yes": "yes",
        "no": "no",
        "error": "Error",
        "warning": "Warning",
        "success": "Success",
    },
    "zh": {
        # Check updates
        "checking_updates": "正在检查技能更新...",
        "installed_skills_status": "已安装技能状态",
        "up_to_date": "已是最新",
        "updates_available": "有可用更新",
        "unknown_version": "版本未知",
        "errors": "错误",
        "total": "总计",
        "skills": "个技能",
        "updates_available_count": "个可更新",
        "skill_not_found": "未找到技能 '{skill}'",
        "no_installed_skills": "未找到已安装的技能",
        "local": "本地",
        "remote": "远程",

        # Update marketplace
        "updating_marketplace": "正在更新市场: {marketplace}",
        "marketplace_up_to_date": "市场已是最新",
        "marketplace_updated": "市场更新成功",
        "commits_behind": "落后 {count} 个提交",
        "update_content": "更新内容",
        "affected_skills": "受影响的技能",
        "reinstalling_skills": "正在重新安装受影响的技能...",
        "reinstalling_skill": "正在安装: {skill}",
        "skill_reinstalled": "已安装: {skill}",
        "skill_reinstall_failed": "安装失败: {skill}",
        "all_skills_updated": "所有受影响的技能已更新",
        "no_affected_skills": "此更新不影响已安装的技能",
        "confirm_update": "确认更新？输入 '是' 继续",
        "update_cancelled": "更新已取消",
        "fetching_remote": "正在获取远程更新...",
        "current_commit": "当前提交",
        "remote_commit": "远程提交",
        "status": "状态",

        # Recommendations
        "fetching_recommendations": "正在获取技能推荐...",
        "trending_skills": "热门技能",
        "from_skills_sh": "来自 skills.sh",
        "top_n": "前 {n} 名",
        "installs": "次安装",
        "personalized_recommendations": "个性化推荐",
        "based_on_installed": "基于您已安装的技能:",
        "install_hint": "安装命令: claude /install <技能名>@<市场>",
        "install_hint_npx": "    或: npx skills add <owner/repo>",
        "could_not_fetch": "无法获取热门技能",

        # Common
        "yes": "是",
        "no": "否",
        "error": "错误",
        "warning": "警告",
        "success": "成功",
    }
}


def detect_locale() -> str:
    """
    Detect user's preferred language from environment.

    Checks in order:
    1. LANG environment variable
    2. LC_ALL environment variable
    3. LANGUAGE environment variable
    4. System locale

    Returns: 'zh' for Chinese, 'en' for others
    """
    # Check environment variables
    for env_var in ['LANG', 'LC_ALL', 'LANGUAGE', 'LC_MESSAGES']:
        lang = os.environ.get(env_var, '')
        if lang:
            lang_lower = lang.lower()
            if lang_lower.startswith('zh') or 'chinese' in lang_lower:
                return 'zh'
            elif lang_lower.startswith('en'):
                return 'en'

    # Try system locale
    try:
        system_locale = locale.getlocale()[0]
        if system_locale:
            if system_locale.lower().startswith('zh'):
                return 'zh'
    except Exception:
        pass

    # Default to English
    return 'en'


class I18n:
    """Internationalization helper class."""

    def __init__(self, lang: Optional[str] = None):
        """
        Initialize with specified language or auto-detect.

        Args:
            lang: Language code ('en', 'zh') or None for auto-detect
        """
        self.lang = lang or detect_locale()
        self.translations = TRANSLATIONS.get(self.lang, TRANSLATIONS['en'])

    def t(self, key: str, **kwargs) -> str:
        """
        Get translated string.

        Args:
            key: Translation key
            **kwargs: Format arguments

        Returns:
            Translated and formatted string
        """
        text = self.translations.get(key, TRANSLATIONS['en'].get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text

    def is_chinese(self) -> bool:
        """Check if current language is Chinese."""
        return self.lang == 'zh'


# Global instance for convenience
_i18n: Optional[I18n] = None


def get_i18n(lang: Optional[str] = None) -> I18n:
    """Get or create global I18n instance."""
    global _i18n
    if _i18n is None or (lang and _i18n.lang != lang):
        _i18n = I18n(lang)
    return _i18n


def t(key: str, **kwargs) -> str:
    """Convenience function for translation."""
    return get_i18n().t(key, **kwargs)


if __name__ == "__main__":
    import io
    import sys
    # Fix Windows console encoding for test
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # Test locale detection
    print(f"Detected locale: {detect_locale()}")

    i18n = get_i18n()
    print(f"Language: {i18n.lang}")
    print(f"Test translation: {t('checking_updates')}")
    print(f"With params: {t('updating_marketplace', marketplace='test-market')}")
