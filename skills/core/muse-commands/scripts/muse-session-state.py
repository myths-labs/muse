#!/usr/bin/env python3
"""Deterministic MUSE session identity and handoff state helpers."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shlex
import sys
import tempfile
from pathlib import Path
from typing import Any


_config_spec = importlib.util.spec_from_file_location('muse_config', Path(__file__).with_name('muse-config.py'))
_config = importlib.util.module_from_spec(_config_spec)
_config_spec.loader.exec_module(_config)
CENTER, ROOTS = _config.load()
SKILL_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOTS[CENTER] / '.agent/workflows'

DYA_ROLES = {
    "strategy": "strategy",
    "build": "build",
    "growth": "growth",
    "qa": "qa",
    "ops": "ops",
    "research": "research",
    "fundraise": "fundraise",
    "crash": "strategy",
}
PROJECT_ROLES = {"build", "growth", "qa"}
LANE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,31}\Z")
HANDOFF_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}\Z")
TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
REQUIRED_SECTIONS = (
    "Objective",
    "Completed",
    "Decisions",
    "Open Issues",
    "Next Action",
    "Required Reads",
    "Artifact Manifest",
    "Verification",
)


class MuseStateError(ValueError):
    """A user-facing validation error."""


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def project_for_cwd(cwd: Path) -> str | None:
    resolved = cwd.resolve()
    matches = [
        (len(str(root)), project)
        for project, root in ROOTS.items()
        if path_is_within(resolved, root)
    ]
    return max(matches)[1] if matches else None


def normalize_lane(raw: str | None) -> str:
    if raw is None:
        return "default"
    if not LANE_RE.fullmatch(raw):
        raise MuseStateError(
            "Invalid lane. Use 1-32 ASCII letters, numbers, '_' or '-', with no path separators."
        )
    return raw


def split_lane(tokens: list[str]) -> tuple[list[str], str]:
    lane_positions = [i for i, token in enumerate(tokens) if token.lower() == "lane"]
    if not lane_positions:
        return tokens, "default"
    if len(lane_positions) != 1:
        raise MuseStateError("Invalid lane: specify Lane exactly once.")
    index = lane_positions[0]
    if index != len(tokens) - 2:
        raise MuseStateError("Invalid lane: use the suffix 'Lane <name>'.")
    return tokens[:index], normalize_lane(tokens[index + 1])


def parse_resume(command_line: str, cwd: str | None = None) -> dict[str, Any]:
    if any(ord(char) < 32 and char not in ("\t",) for char in command_line):
        raise MuseStateError("Invalid lane or command: control characters are not allowed.")
    try:
        tokens = shlex.split(command_line)
    except ValueError as exc:
        raise MuseStateError(f"Invalid resume command: {exc}") from exc
    if not tokens or tokens[0] not in ("/resume", "resume"):
        raise MuseStateError("Expected a /resume command.")

    body, lane = split_lane(tokens[1:])
    if not body:
        raise MuseStateError("/resume requires an explicit role or project.")

    secondary_roles: list[str] = []
    first = body[0].lower()
    if first in ROOTS and first != CENTER:
        project = first
        if len(body) == 1:
            role = "build"
        elif len(body) == 2:
            role = body[1].lower()
        else:
            raise MuseStateError("Unsupported resume target: too many project-role tokens.")
        if role == "strategy":
            suggestion = "/resume strategy"
            if lane != "default":
                suggestion += f" Lane {lane}"
            raise MuseStateError(
                f"Strategy is owned by {CENTER}. Use '{suggestion}' and record {project} as a subject project."
            )
        if role not in PROJECT_ROLES:
            raise MuseStateError(
                f"Unsupported resume target: {project} supports build, growth, or qa."
            )
        role_file_name = role
    else:
        project = CENTER
        role = first
        if role not in DYA_ROLES:
            raise MuseStateError(f"Unsupported resume target: {first}")
        role_file_name = DYA_ROLES[role]
        if len(body) > 1:
            if len(body) == 3 and body[1] == "+" and body[2].lower() in DYA_ROLES:
                secondary_roles.append(body[2].lower())
            else:
                raise MuseStateError("Unsupported resume target: unexpected role tokens.")

    root = ROOTS[project]
    cwd_path = Path(cwd or os.getcwd()).resolve()
    cwd_project = project_for_cwd(cwd_path)
    subject_projects = [cwd_project] if cwd_project and cwd_project != CENTER else []
    if project != CENTER and project not in subject_projects:
        subject_projects.append(project)

    lane_slug = lane.lower()
    checkpoint_path = root / "memory" / "lanes" / f"{role}-lane-{lane_slug}.md"
    if not path_is_within(checkpoint_path, root / "memory" / "lanes"):
        raise MuseStateError("Invalid lane: checkpoint path escapes the lane directory.")

    return {
        "schema_version": 1,
        "project": project,
        "role_home": project,
        "role": role,
        "secondary_roles": secondary_roles,
        "lane": lane,
        "subject_projects": subject_projects,
        "role_root": str(root),
        "role_file": str(root / ".muse" / f"{role_file_name}.md"),
        "memory_root": str(root / "memory"),
        "checkpoint_path": str(checkpoint_path),
        "convo_root": str(root),
        "workspace": str(cwd_path),
    }


def configured_lane_roots() -> list[Path]:
    return [root / "memory" / "lanes" for root in ROOTS.values()]


def require_path_in_roots(path: Path, roots: list[Path], label: str) -> Path:
    resolved = path.resolve()
    if not any(path_is_within(resolved, root) for root in roots):
        raise MuseStateError(f"{label} is outside configured lane roots: {resolved}")
    return resolved


def require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise MuseStateError(f"Missing or invalid required field: {key}")
    return value


def validate_checkpoint_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise MuseStateError("Checkpoint input must be a JSON object.")
    if payload.get("schema_version") != 1:
        raise MuseStateError("Invalid schema_version: expected 1.")
    role_home = require_text(payload, "role_home").lower()
    if role_home not in ROOTS:
        raise MuseStateError(f"Invalid role_home: {role_home}")
    role = require_text(payload, "role").lower()
    allowed_roles = set(DYA_ROLES) if role_home == CENTER else PROJECT_ROLES
    if role not in allowed_roles:
        raise MuseStateError(f"Invalid role '{role}' for role_home '{role_home}'.")
    lane = normalize_lane(require_text(payload, "lane"))
    platform = require_text(payload, "platform").lower()
    if platform not in {"claude", "codex"}:
        raise MuseStateError("Invalid platform: expected 'claude' or 'codex'.")
    require_text(payload, "session_id")
    handoff_id = require_text(payload, "handoff_id")
    if not HANDOFF_RE.fullmatch(handoff_id):
        raise MuseStateError("Invalid handoff_id format.")
    updated_at = require_text(payload, "updated_at")
    if not TIMESTAMP_RE.fullmatch(updated_at):
        raise MuseStateError("Invalid updated_at: expected ISO-8601 UTC seconds.")
    workspace = Path(require_text(payload, "workspace"))
    if not workspace.is_absolute():
        raise MuseStateError("Invalid workspace: expected an absolute path.")

    subject_projects = payload.get("subject_projects")
    if not isinstance(subject_projects, list) or any(
        item not in ROOTS or item == CENTER for item in subject_projects
    ):
        raise MuseStateError("Invalid subject_projects: expected configured subject project names.")
    if len(subject_projects) != len(set(subject_projects)):
        raise MuseStateError("Invalid subject_projects: duplicates are not allowed.")

    for nullable in ("branch", "head"):
        if payload.get(nullable) is not None and not isinstance(payload.get(nullable), str):
            raise MuseStateError(f"Invalid {nullable}: expected string or null.")

    sections = payload.get("sections")
    if not isinstance(sections, dict):
        raise MuseStateError("Missing required sections object.")
    for section in REQUIRED_SECTIONS:
        value = sections.get(section)
        if not isinstance(value, str) or not value.strip():
            raise MuseStateError(f"Missing required section: {section}")

    normalized = dict(payload)
    normalized.update(role_home=role_home, role=role, lane=lane, platform=platform)
    return normalized


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def render_checkpoint(payload: dict[str, Any]) -> str:
    lines = [
        "---",
        f"schema_version: {payload['schema_version']}",
        f"role_home: {payload['role_home']}",
        f"role: {payload['role']}",
        f"lane: {yaml_scalar(payload['lane'])}",
        "subject_projects:",
    ]
    lines.extend(f"  - {project}" for project in payload["subject_projects"])
    for key in ("platform", "session_id", "handoff_id", "updated_at", "workspace", "branch", "head"):
        lines.append(f"{key}: {yaml_scalar(payload.get(key))}")
    lines.extend(["---", ""])
    for section in REQUIRED_SECTIONS:
        lines.extend([f"## {section}", "", payload["sections"][section].rstrip(), ""])
    return "\n".join(lines).rstrip() + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


@contextmanager
def checkpoint_lock(path: Path):
    """Cooperative lock for native v1 and incremental writers on one lane."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name('.' + path.name + '.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def daily_enabled(path: Path) -> bool:
    folder = path.parent / '.daily'
    marker = folder / (path.stem + '.protocol')
    if folder.is_symlink() or marker.is_symlink() or (folder.exists() and not folder.is_dir()):
        raise MuseStateError('UNSAFE_PROTOCOL_PATH')
    if not marker.exists():
        return False
    if not marker.is_file() or marker.stat().st_size > 64 or marker.read_bytes() not in (b'muse-daily-v1\n',b'muse-daily-v1-legacy-workflow\n'):
        raise MuseStateError('UNKNOWN_PROTOCOL')
    return True


def daily_workflow_enabled(path: Path) -> bool:
    if daily_enabled(path):
        return (path.parent/'.daily'/(path.stem+'.protocol')).read_bytes()==b'muse-daily-v1\n'
    policy = SKILL_ROOT/'continuity.json'
    if policy.is_symlink(): raise MuseStateError('UNSAFE_CONTINUITY_POLICY')
    if not policy.exists(): return False
    if not policy.is_file() or policy.stat().st_size > 1024:
        raise MuseStateError('UNKNOWN_CONTINUITY_POLICY')
    try:
        def unique(items):
            result = {}
            for key,value in items:
                if key in result: raise ValueError('duplicate key')
                result[key] = value
            return result
        data = json.loads(policy.read_text(), object_pairs_hook=unique)
        expected = dict(schema_version=1,default_workflow='daily-v1',activation='on_resume')
        if data != expected or type(data.get('schema_version')) is not int: raise ValueError('policy')
    except (ValueError,AttributeError): raise MuseStateError('UNKNOWN_CONTINUITY_POLICY')
    return True


def require_daily_writer(payload):
    checkpoint = ROOTS[payload['role_home']]/'memory/lanes'/f"{payload['role']}-lane-{payload['lane'].lower()}.md"
    if (checkpoint.parent/'.daily'/(checkpoint.stem+'.adoption-pending')).exists():
        raise MuseStateError('ADOPTION_RECOVERY_REQUIRED')
    spec = importlib.util.spec_from_file_location('muse_runtime', Path(__file__).with_name('muse-runtime.py'))
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    try:
        return runtime.require_writer(payload)
    except ValueError as exc:
        raise MuseStateError(str(exc)) from exc


def require_source_preserved(output, current, payload):
    source_file=Path(__file__).with_name('muse-sources.py')
    if not source_file.exists():
        if 'MUSE_SOURCE_LEDGER_V1:' in current['sections']['Artifact_Manifest']:
            raise MuseStateError('SOURCE_HELPER_MISSING')
        return
    spec=importlib.util.spec_from_file_location('muse_sources_guard',source_file)
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    old,manifest=source.current(output,current)
    source.verify_graph(output,manifest)
    after=dict(current,sections={k.replace(' ','_'):v for k,v in payload['sections'].items()})
    new,_=source.current(output,after)
    if old!=new:raise MuseStateError('SOURCE_POINTER_CHANGE_REQUIRES_SOURCE_UPDATE')


def write_checkpoint(input_path: Path, expected_sha256: str | None = None) -> Path:
    try:
        with input_path.open(encoding="utf-8") as handle:
            payload = validate_checkpoint_payload(json.load(handle))
    except (OSError, json.JSONDecodeError) as exc:
        raise MuseStateError(f"Cannot read checkpoint input: {exc}") from exc
    root = ROOTS[payload["role_home"]]
    output = root / "memory" / "lanes" / f"{payload['role']}-lane-{payload['lane'].lower()}.md"
    output = require_path_in_roots(output, configured_lane_roots(), "Checkpoint path")
    with checkpoint_lock(output):
        if (output.parent/'.daily'/(output.stem+'.adoption-pending')).exists():
            raise MuseStateError('ADOPTION_RECOVERY_REQUIRED')
        if daily_enabled(output):
            if not expected_sha256:
                raise MuseStateError('EXPECTED_SHA_REQUIRED: daily Lane full writes need a pinned version')
            if output.stat().st_size > 256 * 1024:
                raise MuseStateError('CHECKPOINT_TOO_LARGE')
            raw = output.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected_sha256:
                raise MuseStateError('STALE_VERSION')
            current = parse_checkpoint_content(raw.decode('utf-8'))
            source_payload = dict(current)
            source_payload['sections'] = {key: current['sections'][key.replace(' ', '_')] for key in REQUIRED_SECTIONS}
            if render_checkpoint(source_payload).encode('utf-8') != raw:
                raise MuseStateError('UNREPRESENTABLE_CHECKPOINT')
            require_daily_writer(current)
            require_source_preserved(output,current,payload)
            if any(payload.get(key) != current.get(key) for key in ('role_home', 'role', 'lane', 'platform', 'session_id', 'workspace')):
                raise MuseStateError('WRITER_IDENTITY_CHANGE_REQUIRES_CLAIM')
            reread = parse_checkpoint_content(render_checkpoint(payload))
            if len(reread['sections']) != len(REQUIRED_SECTIONS) or any(reread['sections'].get(key.replace(' ', '_')) != payload['sections'][key] for key in REQUIRED_SECTIONS):
                raise MuseStateError('UNREPRESENTABLE_CHECKPOINT_INPUT')
        atomic_write(output, render_checkpoint(payload))
    return output


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value.isdigit():
        return int(value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def read_checkpoint(path: Path) -> dict[str, Any]:
    resolved = require_path_in_roots(path, configured_lane_roots(), "Checkpoint path")
    try:
        content = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise MuseStateError(f"Cannot read checkpoint: {exc}") from exc
    return parse_checkpoint_content(content)


def parse_checkpoint_content(content: str) -> dict[str, Any]:
    """Parse bytes already selected by a caller without reopening a moving path."""
    lines = content.splitlines()
    if len(lines) < 3 or lines[0] != "---" or "---" not in lines[1:]:
        raise MuseStateError("Invalid checkpoint frontmatter.")
    end = lines.index("---", 1)
    metadata: dict[str, Any] = {}
    index = 1
    while index < end:
        line = lines[index]
        if line == "subject_projects:":
            projects: list[str] = []
            index += 1
            while index < end and lines[index].startswith("  - "):
                projects.append(lines[index][4:])
                index += 1
            metadata["subject_projects"] = projects
            continue
        if ":" not in line:
            raise MuseStateError(f"Invalid checkpoint metadata line: {line}")
        key, value = line.split(":", 1)
        metadata[key] = parse_scalar(value)
        index += 1

    sections: dict[str, str] = {}
    current: str | None = None
    section_lines: list[str] = []
    for line in lines[end + 1 :]:
        if line.startswith("## "):
            if current is not None:
                sections[current.replace(" ", "_")] = "\n".join(section_lines).strip()
            current = line[3:]
            section_lines = []
        elif current is not None:
            section_lines.append(line)
    if current is not None:
        sections[current.replace(" ", "_")] = "\n".join(section_lines).strip()
    metadata["sections"] = sections
    validation_payload = dict(metadata)
    validation_payload["sections"] = {
        section: sections.get(section.replace(" ", "_"), "") for section in REQUIRED_SECTIONS
    }
    validate_checkpoint_payload(validation_payload)
    return metadata


def verify_handoff(checkpoint: Path, evidence: list[Path]) -> dict[str, Any]:
    parsed = read_checkpoint(checkpoint)
    handoff_id = parsed["handoff_id"]
    files = [require_path_in_roots(checkpoint, configured_lane_roots(), "Checkpoint path")]
    configured_roots = list(ROOTS.values())
    for candidate in evidence:
        resolved = candidate.resolve()
        if not any(path_is_within(resolved, root) for root in configured_roots):
            raise MuseStateError(f"Evidence path is outside configured roots: {resolved}")
        files.append(resolved)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise MuseStateError(f"Cannot read handoff evidence {path}: {exc}") from exc
        count = text.count(handoff_id)
        if count == 0:
            raise MuseStateError(f"Evidence {path} is missing handoff_id {handoff_id}.")
        if count != 1:
            raise MuseStateError(f"handoff_id {handoff_id} appears {count} times in {path}.")
    return {"handoff_id": handoff_id, "files_verified": [str(path) for path in files]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    parse_parser = subparsers.add_parser("parse-resume")
    parse_parser.add_argument("command_line")
    parse_parser.add_argument("--cwd", default=os.getcwd())
    path_parser = subparsers.add_parser("checkpoint-path")
    path_parser.add_argument("command_line")
    path_parser.add_argument("--cwd", default=os.getcwd())
    write_parser = subparsers.add_parser("write-checkpoint")
    write_parser.add_argument("--input", type=Path, required=True)
    write_parser.add_argument("--expected-sha256")
    read_parser = subparsers.add_parser("read-checkpoint")
    read_parser.add_argument("--path", type=Path, required=True)
    verify_parser = subparsers.add_parser("verify-handoff")
    verify_parser.add_argument("--checkpoint", type=Path, required=True)
    verify_parser.add_argument("--evidence", type=Path, action="append", default=[])
    subparsers.add_parser("new-handoff-id")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.subcommand == "parse-resume":
            identity = parse_resume(args.command_line, args.cwd)
            print(json.dumps(identity, ensure_ascii=False, sort_keys=True))
        elif args.subcommand == "checkpoint-path":
            identity = parse_resume(args.command_line, args.cwd)
            print(identity["checkpoint_path"])
        elif args.subcommand == "write-checkpoint":
            print(write_checkpoint(args.input, args.expected_sha256))
        elif args.subcommand == "read-checkpoint":
            print(json.dumps(read_checkpoint(args.path), ensure_ascii=False, sort_keys=True))
        elif args.subcommand == "verify-handoff":
            result = verify_handoff(args.checkpoint, args.evidence)
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        elif args.subcommand == "new-handoff-id":
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            print(f"{timestamp}-{secrets.token_hex(12)}")
    except MuseStateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
