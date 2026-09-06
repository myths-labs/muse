#!/usr/bin/env python3
"""Independent public installer acceptance tests; all writes use temp projects.

These tests execute distribution entry points, not implementation internals.
Hook payload fixtures verify wiring only and are not native-client evidence.
Run: python3 -m unittest discover -s tests/continuity -p test_release_install.py -v
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SENTINEL = "User-owned policy: preserve my project rules.\n"
CLAUDE_SETTINGS = {
    "permissions": {"deny": ["Bash(disallowed-command)"]},
    "hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "command": "printf user-session"}]}],
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "printf user-prompt"}]}],
        "Stop": [{"hooks": [{"type": "command", "command": "printf user-stop"}]}],
    },
}


def tree_state(folder):
    """Record files and links without dereferencing symlinks or reading outside."""
    state = {}
    for parent, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            key = str(path.relative_to(folder))
            if path.is_symlink():
                state[key] = ("symlink", os.readlink(path))
            elif path.is_file():
                state[key] = ("file", hashlib.sha256(path.read_bytes()).hexdigest())
    return state


def within(path, root):
    return path == root or root in path.parents


class ReleaseInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = tempfile.TemporaryDirectory(prefix="muse independent distribution ")
        cls.distribution = Path(cls.archive.name).resolve() / "release source with spaces"
        shutil.copytree(REPO, cls.distribution, symlinks=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))

    @classmethod
    def tearDownClass(cls):
        cls.archive.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="muse independent install ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / "project with spaces"
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("MUSE_") and key not in
                    {"CODEX_THREAD_ID", "CLAUDE_SESSION_ID", "CLAUDE_ENV_FILE"}}
        self.env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + self.env.get("PATH", "")
        self.env["PYTHONDONTWRITEBYTECODE"] = "1"

    def put(self, relative, content):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def run_cli(self, arguments, ok=True, input_text=None, cwd=None, env=None):
        proc = subprocess.run(arguments, cwd=cwd or self.base, env=env or self.env,
                              text=True, input=input_text, capture_output=True, timeout=60)
        if ok:
            self.assertEqual(proc.returncode, 0, proc.stdout[-1500:] + proc.stderr[-1500:])
        else:
            self.assertNotEqual(proc.returncode, 0, "Expected refusal, got: " + proc.stdout[-1500:])
        return proc

    def install(self, tool="codex", ok=True, distribution=None):
        source = distribution or self.distribution
        return self.run_cli(["bash", str(source / "scripts/install.sh"), "--tool", tool,
                             "--target", str(self.project)], ok=ok)

    def receipt(self, proc):
        candidates = []
        decoder = json.JSONDecoder()
        for index, char in enumerate(proc.stdout):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(proc.stdout[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                candidates.append(value)
        for value in reversed(candidates):
            raw = value.get("receipt_path", value.get("receipt"))
            if isinstance(raw, str):
                path = Path(raw)
                self.assertTrue(path.is_file(), "Installer receipt must exist: " + raw)
                return path
        self.fail("Installer did not return a JSON receipt path: " + proc.stdout[-1500:])

    def rollback(self, receipt, ok=True):
        return self.run_cli([sys.executable, str(self.distribution / "scripts/install-continuity.py"),
                             "--rollback", str(receipt)], ok=ok)

    def native_entry(self, tool):
        return self.project / (".agents" if tool == "codex" else ".claude") / "skills/muse-commands"

    def commands(self):
        settings = json.loads((self.project / ".claude/settings.json").read_text())
        return [(event, item["command"]) for event, groups in settings.get("hooks", {}).items()
                for group in groups for item in group.get("hooks", [])
                if item.get("type") == "command"]

    def test_cold_codex_install_creates_project_and_portable_discovery(self):
        result = self.install()
        self.receipt(result)
        runtime = self.project / ".agent/skills/muse-commands"
        self.assertTrue((runtime / "SKILL.md").is_file())
        entry = self.native_entry("codex")
        self.assertTrue(entry.is_symlink())
        self.assertFalse(os.path.isabs(os.readlink(entry)))
        self.assertEqual(entry.resolve(), runtime.resolve())
        config = json.loads((self.project / ".muse/config.json").read_text())
        self.assertEqual(config["schema_version"], 1)
        self.assertEqual(config["projects"][config["role_home"]], ".")
        for name in ("save.md", "daily-resume.md", "daily-bye.md"):
            self.assertTrue((self.project / ".agent/workflows" / name).is_file(), name)

    def test_cold_claude_install_and_both_tools_share_runtime(self):
        self.install("claude")
        self.install("codex")
        self.assertEqual(self.native_entry("claude").resolve(), self.native_entry("codex").resolve())
        events = {event for event, cmd in self.commands() if "muse-" in cmd}
        self.assertTrue({"SessionStart", "UserPromptSubmit"}.issubset(events))

    def test_existing_policy_hooks_and_lane_records_survive_install(self):
        self.put("AGENTS.md", SENTINEL + "Codex unique instruction.\n")
        self.put("CLAUDE.md", SENTINEL + "Claude unique instruction.\n")
        self.put(".claude/settings.json", json.dumps(CLAUDE_SETTINGS))
        lane = self.put("memory/lanes/strategy-lane-b.md", "Closed or legacy state: NEVER overwrite.\n")
        opt_out = self.put("memory/lanes/.daily/strategy-lane-b.protocol", "legacy\n")
        self.install("claude")
        self.install("codex")
        self.assertTrue((self.project / "AGENTS.md").read_text().startswith(SENTINEL + "Codex unique instruction.\n"))
        self.assertTrue((self.project / "CLAUDE.md").read_text().startswith(SENTINEL + "Claude unique instruction.\n"))
        settings = json.loads((self.project / ".claude/settings.json").read_text())
        self.assertEqual(settings["permissions"], CLAUDE_SETTINGS["permissions"])
        for event, groups in CLAUDE_SETTINGS["hooks"].items():
            for group in groups:
                self.assertIn(group, settings["hooks"][event])
        self.assertEqual(lane.read_text(), "Closed or legacy state: NEVER overwrite.\n")
        self.assertEqual(opt_out.read_text(), "legacy\n")

    def test_reinstall_does_not_duplicate_blocks_or_hooks(self):
        self.install("claude")
        self.install("codex")
        original = {name: (self.project / name).read_bytes()
                    for name in ("AGENTS.md", "CLAUDE.md", ".claude/settings.json", ".muse/config.json")}
        for tool in ("claude", "codex", "claude"):
            self.install(tool)
        for name, content in original.items():
            self.assertEqual((self.project / name).read_bytes(), content, name)

    def test_existing_role_home_configuration_is_not_rewritten(self):
        original = '{"schema_version":1,"role_home":"control","projects":{"control":".","product":"../product"}}\n'
        self.put(".muse/config.json", original)
        (self.base / "product").mkdir()
        self.install("claude")
        self.install("codex")
        self.assertEqual((self.project / ".muse/config.json").read_text(), original)

    def test_invalid_claude_settings_refuses_before_mutation(self):
        self.put(".claude/settings.json", "{this is malformed JSON}\n")
        self.put("CLAUDE.md", SENTINEL)
        before = tree_state(self.project)
        self.install("claude", ok=False)
        self.assertEqual(tree_state(self.project), before)

    def test_invalid_project_config_refuses_before_mutation(self):
        self.put(".muse/config.json", '{"schema_version":1,"projects":')
        self.put("AGENTS.md", SENTINEL)
        before = tree_state(self.project)
        self.install(ok=False)
        self.assertEqual(tree_state(self.project), before)

    def test_unknown_workflow_conflict_is_preserved(self):
        self.put(".agent/workflows/save.md", "Private save flow; external writer controls it.\n")
        self.put("AGENTS.md", SENTINEL)
        before = tree_state(self.project)
        self.install(ok=False)
        self.assertEqual(tree_state(self.project), before)

    def test_unknown_runtime_conflict_is_preserved(self):
        self.put(".agent/skills/muse-commands/SKILL.md", "Private runtime: do not replace.\n")
        self.put(".agent/skills/muse-commands/private.py", "print('user data')\n")
        before = tree_state(self.project)
        self.install(ok=False)
        self.assertEqual(tree_state(self.project), before)

    def test_escape_symlink_in_runtime_parent_is_rejected(self):
        self.project.mkdir()
        outside = self.base / "external control center"
        outside.mkdir()
        (outside / "owner.txt").write_text(SENTINEL)
        (self.project / ".agent").symlink_to(outside, target_is_directory=True)
        before, external = tree_state(self.project), tree_state(outside)
        self.install(ok=False)
        self.assertEqual(tree_state(self.project), before)
        self.assertEqual(tree_state(outside), external)

    def test_escape_symlink_in_settings_is_rejected(self):
        external = self.base / "external settings.json"
        external.write_text(json.dumps(CLAUDE_SETTINGS))
        settings = self.project / ".claude/settings.json"
        settings.parent.mkdir(parents=True)
        settings.symlink_to(external)
        before = tree_state(self.project)
        self.install("claude", ok=False)
        self.assertEqual(tree_state(self.project), before)
        self.assertEqual(external.read_text(), json.dumps(CLAUDE_SETTINGS))

    def test_escape_symlink_in_agents_is_rejected(self):
        self.project.mkdir()
        external = self.base / "external policy.md"
        external.write_text(SENTINEL)
        (self.project / "AGENTS.md").symlink_to(external)
        before = tree_state(self.project)
        self.install(ok=False)
        self.assertEqual(tree_state(self.project), before)
        self.assertEqual(external.read_text(), SENTINEL)

    def test_rollback_restores_prior_bytes_and_keeps_unmanaged_new_file(self):
        self.put("AGENTS.md", SENTINEL)
        self.put(".claude/settings.json", json.dumps(CLAUDE_SETTINGS, indent=4) + "\n")
        before = tree_state(self.project)
        receipt = self.receipt(self.install("claude"))
        self.put("user-created-after-install.txt", "Keep this new user file.\n")
        self.rollback(receipt)
        after = tree_state(self.project)
        for path, value in before.items():
            self.assertEqual(after.get(path), value, path)
        self.assertEqual((self.project / "user-created-after-install.txt").read_text(), "Keep this new user file.\n")
        self.assertFalse(self.native_entry("claude").exists())
        self.assertFalse((self.project / ".muse/config.json").exists())

    def test_rollback_refuses_modified_managed_file_without_partial_restore(self):
        self.put("CLAUDE.md", SENTINEL)
        self.put(".claude/settings.json", json.dumps(CLAUDE_SETTINGS))
        receipt = self.receipt(self.install("claude"))
        policy = self.project / "CLAUDE.md"
        policy.write_text(policy.read_text() + "A user added this after installation.\n")
        before = tree_state(self.project)
        self.rollback(receipt, ok=False)
        self.assertEqual(tree_state(self.project), before)

    def test_second_provider_rollback_keeps_first_provider_functional(self):
        self.install("claude")
        initial = {path: item for path, item in tree_state(self.project).items()
                   if path.startswith((".agent/", ".claude/"))}
        receipt = self.receipt(self.install("codex"))
        self.rollback(receipt)
        current = tree_state(self.project)
        for path, item in initial.items():
            self.assertEqual(current.get(path), item, path)
        self.assertTrue((self.native_entry("claude") / "SKILL.md").is_file())
        self.assertFalse(self.native_entry("codex").exists())

    def test_installed_scripts_and_workflows_do_not_reference_distribution(self):
        self.install("claude")
        roots = (self.project / ".agent", self.project / ".claude", self.project / ".agents")
        for root in roots:
            if not root.exists():
                continue
            for parent, dirs, files in os.walk(root, followlinks=False):
                for name in dirs + files:
                    path = Path(parent) / name
                    if path.is_symlink():
                        self.assertFalse(os.path.isabs(os.readlink(path)), str(path))
                        self.assertTrue(within(path.resolve(), self.project.resolve()), str(path))
                    elif path.is_file() and path.suffix in {".py", ".sh", ".md", ".json"}:
                        content = path.read_text()
                        self.assertFalse(str(self.distribution) in content, "Distribution path dependency: " + str(path))
                        self.assertFalse(re.search(r"/Users/[^/\s]+/(?:Desktop|\.codex|\.cache)/", content),
                                         "Author-machine path in installed file: " + str(path))

    def test_unsupported_tool_refuses_without_creating_project(self):
        self.install("not-a-tool", ok=False)
        self.assertEqual(tree_state(self.project), {})

    def test_synthetic_session_hook_quotes_paths_and_exports_fixture_identity(self):
        """Synthetic hook wiring only; this does not count as native Claude QA."""
        self.install("claude")
        commands = [cmd for event, cmd in self.commands()
                    if event == "SessionStart" and "muse-" in cmd]
        self.assertEqual(len(commands), 1)
        env_file = self.base / "session fixture exports.sh"
        env = dict(self.env, CLAUDE_ENV_FILE=str(env_file), CLAUDE_PROJECT_DIR=str(self.project))
        payload = {"hook_event_name": "SessionStart", "session_id": "synthetic-install-session",
                   "cwd": str(self.project), "source": "startup"}
        self.run_cli(["bash", "-c", commands[0]], input_text=json.dumps(payload),
                     cwd=self.project, env=env)
        runtime = self.project / ".agent/skills/muse-commands/scripts/muse-runtime.py"
        command = ". " + shlex.quote(str(env_file)) + "; " + " ".join(map(shlex.quote, [sys.executable, str(runtime), "identity"]))
        proc = self.run_cli(["bash", "-c", command], cwd=self.project)
        value = json.loads(proc.stdout)
        self.assertEqual(value["platform"], "claude")
        self.assertEqual(value["session_id"], "synthetic-install-session")
        self.assertEqual(value["workspace"], str(self.project.resolve()))

    def test_installed_resume_survives_distribution_removal(self):
        source = self.base / "removable source with spaces"
        shutil.copytree(self.distribution, source, symlinks=True)
        self.install(distribution=source)
        source.rename(self.base / "source moved away")
        script = self.project / ".agent/skills/muse-commands/scripts/muse-daily.py"
        proc = self.run_cli([sys.executable, str(script), "prepare-resume", "--command",
                             "/resume strategy Lane INSTALL", "--workspace", str(self.project)],
                            cwd=self.project)
        value = json.loads(proc.stdout)
        self.assertTrue(within(Path(value["checkpoint_path"]), self.project.resolve()))
        self.assertIn("strategy-lane-install", value["checkpoint_path"])

    def test_known_v35_workflows_upgrade_and_rollback_restore_original_bytes(self):
        before = {}
        for name in ("resume.md", "bye.md"):
            fixture = self.distribution / "tests/continuity/fixtures/v3.5/workflows" / name
            self.assertTrue(fixture.is_file(), "Missing public upgrade fixture: " + name)
            target = self.project / ".agent/workflows" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(fixture.read_bytes())
            before[name] = target.read_bytes()
        receipt = self.receipt(self.install("claude"))
        for name, old in before.items():
            self.assertNotEqual(hashlib.sha256((self.project / ".agent/workflows" / name).read_bytes()).hexdigest(),
                                hashlib.sha256(old).hexdigest(), "Legacy workflow was not upgraded: " + name)
        self.rollback(receipt)
        for name, old in before.items():
            self.assertEqual(hashlib.sha256((self.project / ".agent/workflows" / name).read_bytes()).hexdigest(),
                             hashlib.sha256(old).hexdigest(), "Legacy workflow was not restored: " + name)

    def test_copied_rollback_receipt_outside_control_location_is_rejected(self):
        receipt = self.receipt(self.install())
        copied = self.base / "copied receipt.json"
        copied.write_bytes(receipt.read_bytes())
        before = tree_state(self.project)
        self.rollback(copied, ok=False)
        self.assertEqual(tree_state(self.project), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
