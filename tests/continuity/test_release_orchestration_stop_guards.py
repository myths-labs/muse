#!/usr/bin/env python3
"""Acceptance tests for the two opt-in Stop hooks shipped with muse-orchestration.

Every write goes to a temporary directory; no real settings file is read or changed (install runs get
a temporary HOME and working directory, and an explicit --settings path where one is used).
The transcripts below are minimal JSONL shaped like Claude Code transcripts; they check the hooks'
decisions and wiring, not native-client behaviour.
Run: python3 -m unittest discover -s tests/continuity -p test_release_orchestration_stop_guards.py -v
"""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "core" / "muse-orchestration" / "scripts"
NEGATIVE = SCRIPTS / "negative_claim_guard.py"
LICENCE = SCRIPTS / "licence_stop_guard.py"
GUARDS = (NEGATIVE, LICENCE)
BACKUPS = ".muse-hook-backups"
LICENCE_REASON = ("A licence is one line of fact, not by itself a reason to skip evaluating an open-source project, "
                  "model or paper. Record the licence in one line, keep evaluating side by side with your own inputs "
                  "where the licence permits evaluation, and raise licence limits for human review before any "
                  "production use.")
SETTINGS = {
    "permissions": {"allow": ["Bash(ls:*)"], "deny": ["Bash(disallowed-command)"]},
    "env": {"EXAMPLE_FLAG": "1"},
    "model": "example-model",
    "statusLine": {"type": "command", "command": "printf 'status ✓'"},
    "hooks": {
        "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "printf user-pre"}]}],
        "Stop": [{"hooks": [{"type": "command", "command": "printf user-stop", "timeout": 20}]}],
    },
}


def base_env(home=None):
    env = {k: v for k, v in os.environ.items() if k != "MUSE_LICENCE_GUARD_REASON"}
    if home:
        env["HOME"] = home
    return env


def run_script(script, args=(), stdin=b"", cwd=None, env=None):
    return subprocess.run([sys.executable, "-I", str(script)] + list(args), input=stdin,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                          env=env if env is not None else base_env(), timeout=120)


def write_transcript(folder, name, turns):
    """turns: [(prompt, steps)]; a step is ("text", str) or ("bash", command, is_error)."""
    rows, n = [], 0
    for prompt, steps in turns:
        rows.append({"type": "user", "isSidechain": False, "message": {"role": "user", "content": prompt}})
        for step in steps:
            if step[0] == "text":
                rows.append({"type": "assistant", "isSidechain": False,
                             "message": {"role": "assistant", "content": [{"type": "text", "text": step[1]}]}})
                continue
            n += 1
            tid = "toolu_%02d" % n
            rows.append({"type": "assistant", "isSidechain": False, "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": tid, "name": "Bash", "input": {"command": step[1]}}]}})
            rows.append({"type": "user", "isSidechain": False, "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tid, "content": "ok", "is_error": step[2]}]}})
    path = os.path.join(folder, name + ".jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def stop_payload(folder, transcript, **extra):
    data = {"session_id": "00000000-0000-4000-8000-000000000001", "transcript_path": transcript, "cwd": folder,
            "permission_mode": "default", "hook_event_name": "Stop", "stop_hook_active": False}
    data.update(extra)
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


class GuardSelftests(unittest.TestCase):
    def test_selftest_exits_zero(self):
        for script in GUARDS:
            with self.subTest(script=script.name):
                r = run_script(script, ["--selftest"])
                out = r.stdout.decode("utf-8")
                self.assertEqual(r.returncode, 0, out + r.stderr.decode("utf-8", "replace"))
                self.assertNotIn("FAIL", out)
                last = out.strip().splitlines()[-1]
                done, total = last.split()[0].split("/")
                self.assertEqual(done, total, last)


class HookDecisionBase(unittest.TestCase):
    script = None

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="muse-stop-guard-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def decide(self, stdin, env=None):
        r = run_script(self.script, stdin=stdin, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stderr, b"")
        out = r.stdout.decode("utf-8").strip()
        return json.loads(out) if out else None

    def assertFailsOpen(self):
        transcript_dir = os.path.join(self.tmp, "a-directory.jsonl")
        os.mkdir(transcript_dir)
        garbage = write_transcript(self.tmp, "garbage", [])
        with open(garbage, "wb") as f:
            f.write(b"\xff\xfe not json at all\n{\"type\": \"assistant\", broken\n")
        for stdin in (b"not json {", b"\xff\xfe\x00", b"[1, 2, 3]", b"",
                      stop_payload(self.tmp, os.path.join(self.tmp, "missing.jsonl")),
                      stop_payload(self.tmp, transcript_dir), stop_payload(self.tmp, garbage)):
            with self.subTest(stdin=stdin[:60]):
                self.assertIsNone(self.decide(stdin))


class NegativeClaimGuardDecisions(HookDecisionBase):
    script = NEGATIVE
    claim = "OtherModel 我的记录里没有出现过，不像是在用。"
    prompt = "我们用不用 OtherModel？"
    recall = "python3 -I /opt/tools/recall.py OtherModel 其它模型 2>&1 | tail -20"

    def test_negative_claim_without_recall_blocks(self):
        t = write_transcript(self.tmp, "a", [(self.prompt, [("text", self.claim)])])
        out = self.decide(stop_payload(self.tmp, t))
        self.assertEqual(out["decision"], "block")
        self.assertIn("OtherModel 我的记录里没有出现过", out["reason"])
        self.assertIn(str(SCRIPTS / "recall.py"), out["reason"])
        self.assertIn("a synonym in each language your notes use", out["reason"])
        self.assertIn("not the same as not there", out["reason"])

    def test_english_claim_blocks(self):
        t = write_transcript(self.tmp, "e", [(self.prompt, [("text", "There is nothing in my notes about OtherModel.")])])
        self.assertEqual(self.decide(stop_payload(self.tmp, t))["decision"], "block")

    def test_successful_recall_in_this_turn_lets_stop_through(self):
        t = write_transcript(self.tmp, "b", [(self.prompt, [("bash", self.recall, False), ("text", self.claim)])])
        self.assertIsNone(self.decide(stop_payload(self.tmp, t)))

    def test_failed_recall_or_recall_in_previous_turn_still_blocks(self):
        failed = write_transcript(self.tmp, "f1", [(self.prompt, [("bash", self.recall, True), ("text", self.claim)])])
        earlier = write_transcript(self.tmp, "f2", [(self.prompt, [("bash", self.recall, False), ("text", "查到了。")]),
                                                    ("再确认一下", [("text", self.claim)])])
        for t in (failed, earlier):
            with self.subTest(transcript=os.path.basename(t)):
                self.assertEqual(self.decide(stop_payload(self.tmp, t))["decision"], "block")

    def test_stop_hook_active_lets_stop_through(self):
        t = write_transcript(self.tmp, "c", [(self.prompt, [("text", self.claim)])])
        self.assertIsNone(self.decide(stop_payload(self.tmp, t, stop_hook_active=True)))

    def test_bad_input_fails_open(self):
        self.assertFailsOpen()


class LicenceStopGuardDecisions(HookDecisionBase):
    script = LICENCE
    prompt = "Can we use ExampleModel?"
    hit = "ExampleModel is non-commercial, so we skip it."

    def test_licence_plus_stop_word_blocks_with_default_reason(self):
        t = write_transcript(self.tmp, "a", [(self.prompt, [("text", self.hit)])])
        out = self.decide(stop_payload(self.tmp, t))
        self.assertEqual(out["decision"], "block")
        self.assertTrue(out["reason"].startswith(LICENCE_REASON), out["reason"])
        self.assertIn("ExampleModel is non-commercial, so we skip it", out["reason"])

    def test_licence_line_without_stop_word_lets_stop_through(self):
        t = write_transcript(self.tmp, "b", [(self.prompt, [
            ("text", "Licence: CC BY-NC 4.0 (one line). Next we compare it side by side with our own inputs.")])])
        self.assertIsNone(self.decide(stop_payload(self.tmp, t)))

    def test_only_the_latest_turn_counts(self):
        t = write_transcript(self.tmp, "p", [(self.prompt, [("text", self.hit)]),
                                             ("and now?", [("text", "Side-by-side results are in the table.")])])
        self.assertIsNone(self.decide(stop_payload(self.tmp, t)))

    def test_stop_hook_active_lets_stop_through(self):
        t = write_transcript(self.tmp, "c", [(self.prompt, [("text", self.hit)])])
        self.assertIsNone(self.decide(stop_payload(self.tmp, t, stop_hook_active=True)))

    def test_reason_can_be_replaced_by_environment(self):
        t = write_transcript(self.tmp, "r", [(self.prompt, [("text", self.hit)])])
        env = base_env()
        env["MUSE_LICENCE_GUARD_REASON"] = "Project policy: ask the maintainer before dropping a candidate."
        out = self.decide(stop_payload(self.tmp, t), env=env)
        self.assertTrue(out["reason"].startswith("Project policy: ask the maintainer"), out["reason"])

    def test_bad_input_fails_open(self):
        self.assertFailsOpen()


class InstallRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="muse-stop-guard-install-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)

    def run_install(self, script, *args, cwd=None):
        r = run_script(script, list(args), cwd=cwd or self.tmp, env=base_env(self.home))
        return r.returncode, r.stdout.decode("utf-8") + r.stderr.decode("utf-8", "replace")

    def write_settings(self, path, data=SETTINGS, indent=2):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        text = json.dumps(data, ensure_ascii=False, indent=indent) + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return text

    @staticmethod
    def read(path):
        with open(path, encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def backups(folder):
        return sorted(n for n in os.listdir(folder) if n.endswith(".json")) if os.path.isdir(folder) else []

    def assertOurEntry(self, group, script):
        hook = group["hooks"][0]
        exe, flag, path = shlex.split(hook["command"])
        self.assertTrue(os.path.isabs(exe) and os.path.exists(exe), exe)
        self.assertEqual((flag, path), ("-I", str(script)))
        self.assertEqual((hook["type"], hook["timeout"]), ("command", 3))

    def test_install_reinstall_uninstall_touch_only_this_entry(self):
        for script in GUARDS:
            with self.subTest(script=script.name):
                folder = os.path.join(self.tmp, script.stem)
                settings = os.path.join(folder, "settings.json")
                original = self.write_settings(settings)
                backup_dir = os.path.join(folder, BACKUPS)

                rc, out = self.run_install(script, "--install", "--settings", settings)
                self.assertEqual(rc, 0, out)
                after = json.loads(self.read(settings))
                self.assertEqual(after["hooks"]["Stop"][:-1], SETTINGS["hooks"]["Stop"])
                self.assertOurEntry(after["hooks"]["Stop"][-1], script)
                self.assertEqual({k: v for k, v in after.items() if k != "hooks"},
                                 {k: v for k, v in SETTINGS.items() if k != "hooks"})
                self.assertEqual(after["hooks"]["PreToolUse"], SETTINGS["hooks"]["PreToolUse"])
                first = self.backups(backup_dir)
                self.assertEqual(len(first), 1, out)
                self.assertEqual(self.read(os.path.join(backup_dir, first[0])), original)
                self.assertTrue(os.path.isfile(os.path.join(backup_dir, ".gitignore")))
                installed = self.read(settings)

                rc, out = self.run_install(script, "--install", "--settings", settings)
                self.assertEqual(rc, 0, out)
                self.assertIn("Already installed", out)
                self.assertEqual(self.read(settings), installed)
                self.assertEqual(len(self.backups(backup_dir)), 1)

                rc, out = self.run_install(script, "--uninstall", "--settings", settings)
                self.assertEqual(rc, 0, out)
                self.assertEqual(self.read(settings), original)
                second = [n for n in self.backups(backup_dir) if n not in first]
                self.assertEqual(len(second), 1)
                self.assertEqual(self.read(os.path.join(backup_dir, second[0])), installed)

                rc, out = self.run_install(script, "--uninstall", "--settings", settings)
                self.assertEqual(rc, 0, out)
                self.assertEqual(self.read(settings), original)
                self.assertEqual(len(self.backups(backup_dir)), 2)

    def test_default_target_is_the_project_settings_under_cwd(self):
        project = os.path.join(self.tmp, "project")
        settings = os.path.join(project, ".claude", "settings.json")
        original = self.write_settings(settings)
        rc, out = self.run_install(NEGATIVE, "--install", cwd=project)
        self.assertEqual(rc, 0, out)
        self.assertOurEntry(json.loads(self.read(settings))["hooks"]["Stop"][-1], NEGATIVE)
        self.assertEqual(len(self.backups(os.path.join(project, ".claude", BACKUPS))), 1)
        self.assertEqual(os.listdir(self.home), [])
        rc, out = self.run_install(NEGATIVE, "--uninstall", cwd=project)
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.read(settings), original)

    def test_missing_project_settings_is_created(self):
        project = os.path.join(self.tmp, "fresh")
        os.makedirs(project)
        rc, out = self.run_install(LICENCE, "--install", cwd=project)
        self.assertEqual(rc, 0, out)
        settings = os.path.join(project, ".claude", "settings.json")
        data = json.loads(self.read(settings))
        self.assertEqual(list(data), ["hooks"])
        self.assertEqual(len(data["hooks"]["Stop"]), 1)
        self.assertOurEntry(data["hooks"]["Stop"][0], LICENCE)
        rc, out = self.run_install(LICENCE, "--uninstall", cwd=project)
        self.assertEqual(rc, 0, out)
        self.assertEqual(json.loads(self.read(settings)), {"hooks": {"Stop": []}})

    def test_backup_dir_override_and_both_guards_side_by_side(self):
        folder = os.path.join(self.tmp, "both")
        settings = os.path.join(folder, "settings.json")
        original = self.write_settings(settings, indent=4)
        elsewhere = os.path.join(self.tmp, "kept-backups")
        for script in GUARDS:
            rc, out = self.run_install(script, "--install", "--settings", settings, "--backup-dir", elsewhere)
            self.assertEqual(rc, 0, out)
        stop = json.loads(self.read(settings))["hooks"]["Stop"]
        self.assertEqual(stop[0], SETTINGS["hooks"]["Stop"][0])
        self.assertOurEntry(stop[1], NEGATIVE)
        self.assertOurEntry(stop[2], LICENCE)
        self.assertIn('\n    "permissions"', self.read(settings))       # the file's own 4-space indent is kept
        rc, out = self.run_install(LICENCE, "--uninstall", "--settings", settings, "--backup-dir", elsewhere)
        self.assertEqual(rc, 0, out)
        stop = json.loads(self.read(settings))["hooks"]["Stop"]
        self.assertEqual(len(stop), 2)
        self.assertOurEntry(stop[1], NEGATIVE)
        rc, out = self.run_install(NEGATIVE, "--uninstall", "--settings", settings, "--backup-dir", elsewhere)
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.read(settings), original)
        self.assertEqual(len(self.backups(elsewhere)), 4)
        self.assertFalse(os.path.exists(os.path.join(folder, BACKUPS)))

    def test_invalid_settings_are_left_alone(self):
        folder = os.path.join(self.tmp, "bad")
        os.makedirs(folder)
        settings = os.path.join(folder, "settings.json")
        for text in ('{"hooks": ', '{"hooks": {"Stop": {"not": "a list"}}}\n'):
            with self.subTest(text=text):
                with open(settings, "w", encoding="utf-8") as f:
                    f.write(text)
                for script in GUARDS:
                    rc, out = self.run_install(script, "--install", "--settings", settings)
                    self.assertEqual(rc, 1, out)
                    self.assertEqual(self.read(settings), text)
                    self.assertFalse(os.path.exists(os.path.join(folder, BACKUPS)))


if __name__ == "__main__":
    unittest.main()
