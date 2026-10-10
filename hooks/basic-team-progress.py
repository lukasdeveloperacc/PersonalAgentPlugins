#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Explicit, session-scoped basic-team hook reminders."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import secrets
import sys
import tempfile
import time
from pathlib import Path

MARKER = "basic_team_hook"
STATE_HOME = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "lukas-plugin/basic-team"
TTL = 3600


def _key(host: str, session: str) -> str:
    return hashlib.sha256((host + "\0" + session).encode()).hexdigest()


def _private_dir() -> Path:
    STATE_HOME.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(STATE_HOME, 0o700)
    return STATE_HOME


def _locked():
    directory = _private_dir()
    lock = open(directory / ".lock", "a", encoding="utf-8")
    os.chmod(directory / ".lock", 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX)
    return lock


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _write(path: Path, data: dict) -> None:
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def _receipt(action: str, host: str, session: str, request_id: str, run_id: str, page: str = "") -> None:
    print(json.dumps({MARKER: {"action": action, "host": host, "session_id": session,
                              "request_id": request_id, "run_id": run_id, "page": page}}))


def _identity(host: str, requested: str | None) -> str | None:
    if host == "codex":
        thread, session = os.getenv("CODEX_THREAD_ID", ""), os.getenv("CODEX_SESSION_ID", "")
        if not thread or thread != session or (requested and requested != thread):
            return None
        return thread
    session = requested or os.getenv("CLAUDE_SESSION_ID", "")
    env_session = os.getenv("CLAUDE_SESSION_ID", "")
    if not session or (env_session and env_session != session):
        return None
    return session


def _page(value: str) -> tuple[Path, Path] | None:
    try:
        root = Path.cwd().resolve(strict=True)
        page = Path(value)
        if not page.is_absolute():
            return None
        page = page.resolve(strict=True)
        allowed = (root / "docs" / "inprogress").resolve(strict=True)
        if not page.is_file() or not page.is_relative_to(allowed):
            return None
        return root, page
    except (OSError, RuntimeError):
        return None


def helper(args) -> int:
    session = _identity(args.host, args.session_id)
    if not session:
        print(json.dumps({"basic_team_hook": {"status": "unarmed", "reason": "Main session identity could not be verified."}}))
        return 0
    run_id = args.run_id or secrets.token_hex(16)
    if args.action == "arm":
        validated = _page(args.page)
        if not validated:
            print(json.dumps({"basic_team_hook": {"status": "unarmed", "reason": "PAGE must be an existing absolute file under this project's docs/inprogress."}}))
            return 0
        root, page = validated
    else:
        root, page = Path.cwd().resolve(), Path()
        if not args.run_id:
            return 2
    request_id = secrets.token_hex(24)
    directory = _private_dir()
    with _locked():
        record_path = directory / (_key(args.host, session) + ".json")
        record = _read(record_path) or {"host": args.host, "session_id": session, "generation": secrets.token_hex(16), "runs": []}
        # A pending request belongs to the current generation, so reset invalidates late receipts.
        data = {"action": args.action, "host": args.host, "session_id": session,
                "generation": record["generation"], "request_id": request_id, "run_id": run_id,
                "root": str(root), "page": str(page) if args.action == "arm" else "",
                "created": time.time()}
        if args.action == "arm":
            record["latest_arm_request_id"] = request_id
        _write(record_path, record)
        _write(directory / ("request-" + request_id + ".json"), data)
    _receipt(args.action, args.host, session, request_id, run_id, str(page) if args.action == "arm" else "")
    return 0


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _receipts(event: dict):
    values = [event.get("tool_response"), event.get("stdout"), event.get("output")]
    for value in values:
        for raw in _strings(value):
            try:
                parsed = json.loads(raw)
            except ValueError:
                continue
            if isinstance(parsed, dict) and isinstance(parsed.get(MARKER), dict):
                yield parsed[MARKER]
            # Common text content is itself JSON in the text field; nested strings cover it.
            if isinstance(parsed, dict):
                for nested in _strings(parsed):
                    try:
                        inner = json.loads(nested)
                    except ValueError:
                        continue
                    if isinstance(inner, dict) and isinstance(inner.get(MARKER), dict):
                        yield inner[MARKER]


def _success(event: dict) -> bool:
    response = event.get("tool_response")
    if isinstance(response, str):
        try:
            response = json.loads(response)
        except ValueError:
            response = None
    for result in (event, response if isinstance(response, dict) else {}):
        code = result.get("exit_code", result.get("exitCode"))
        if code not in (None, 0) or result.get("isError") is True or result.get("interrupted") is True:
            return False
        if result is not event and result.get("session_id"):
            return False
    if any(event.get(key) == 0 for key in ("exit_code", "exitCode")):
        return True
    if isinstance(response, dict):
        if any(response.get(key) == 0 for key in ("exit_code", "exitCode")):
            return True
        return response.get("interrupted") is False and isinstance(response.get("stdout"), str)
    return False


def _detect_host(event: dict) -> str | None:
    session = event.get("session_id")
    if not isinstance(session, str) or not session:
        return None
    if event.get("turn_id"):
        return "codex" if os.getenv("CODEX_THREAD_ID") == session and os.getenv("CODEX_SESSION_ID") == session else None
    codex_marker = bool(os.getenv("PLUGIN_ROOT") or os.getenv("CODEX_THREAD_ID") or os.getenv("CODEX_SESSION_ID"))
    if codex_marker:
        return "codex" if os.getenv("CODEX_THREAD_ID") == session and os.getenv("CODEX_SESSION_ID") == session else None
    if os.getenv("CLAUDE_SESSION_ID") == session:
        return "claude"
    if os.getenv("CLAUDE_PLUGIN_ROOT") and "agent_id" not in event:
        return "claude"
    return None


def _main(host: str, event: dict) -> tuple[str | None, str | None]:
    session = event.get("session_id")
    if not isinstance(session, str) or not session:
        return None, None
    if host == "codex":
        turn = event.get("turn_id")
        if not isinstance(turn, str) or not turn or os.getenv("CODEX_THREAD_ID") != session or os.getenv("CODEX_SESSION_ID") != session:
            return None, None
        return session, turn
    if event.get("agent_id"):
        return None, None
    env_session = os.getenv("CLAUDE_SESSION_ID", "")
    if env_session and env_session != session:
        return None, None
    return session, None


def hook(args) -> int:
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            return 0
        name = args.event
        if event.get("agent_id"):
            return 0
        host = args.host if args.host != "auto" else _detect_host(event)
        if host not in ("codex", "claude"):
            return 0
        args.host = host
        session = event.get("session_id")
        if name in ("UserPromptSubmit", "SessionStart"):
            if name == "SessionStart" and event.get("source") not in ("startup", "resume", "clear", "compact"):
                return 0
            if isinstance(session, str) and session and STATE_HOME.exists():
                with _locked():
                    path = STATE_HOME / (_key(host, session) + ".json")
                    record = _read(path)
                    if record:
                        record["generation"] = secrets.token_hex(16)
                        record["latest_arm_request_id"] = None
                        record["runs"] = []
                        _write(path, record)
                        for pending in STATE_HOME.glob("request-*.json"):
                            item = _read(pending)
                            if item and item.get("host") == host and item.get("session_id") == session:
                                pending.unlink(missing_ok=True)
            return 0
        if name == "SessionEnd":
            if isinstance(session, str) and session and STATE_HOME.exists():
                with _locked():
                    (STATE_HOME / (_key(host, session) + ".json")).unlink(missing_ok=True)
                    for pending in STATE_HOME.glob("request-*.json"):
                        item = _read(pending)
                        if item and item.get("host") == host and item.get("session_id") == session:
                            pending.unlink(missing_ok=True)
            return 0
        if name != "PostToolUse" or event.get("tool_name") not in ("Bash", "exec_command", "write_stdin"):
            return _progress(args, event)
        active_session, turn = _main(host, event)
        if not active_session or not _success(event):
            return 0
        receipts = list(_receipts(event))
        if receipts:
            if not STATE_HOME.exists():
                return 0
            with _locked():
                record_path = STATE_HOME / (_key(host, active_session) + ".json")
                record = _read(record_path)
                for receipt in receipts:
                    rid = receipt.get("request_id")
                    if not isinstance(rid, str) or not re.fullmatch(r"[0-9a-f]{48}", rid):
                        continue
                    request_path = STATE_HOME / ("request-" + rid + ".json")
                    request = _read(request_path)
                    if not request or request.get("host") != host or request.get("session_id") != active_session:
                        continue
                    if request.get("created", 0) + TTL < time.time():
                        request_path.unlink(missing_ok=True)
                        continue
                    valid = (request.get("host") == host and request.get("session_id") == active_session
                             and request.get("request_id") == rid and receipt.get("action") == request.get("action")
                             and receipt.get("run_id") == request.get("run_id") and record
                             and request.get("generation") == record.get("generation")
                             and (request.get("action") != "arm" or record.get("latest_arm_request_id") == rid))
                    if not valid:
                        if request.get("action") == "arm" and record and record.get("latest_arm_request_id") != rid:
                            request_path.unlink(missing_ok=True)
                        continue
                    request_path.unlink(missing_ok=True)
                    if request["action"] == "arm" and request.get("root") == str(Path.cwd().resolve()) and (host == "claude" or turn):
                        run = {"run_id": request["run_id"], "page": request["page"], "turn_id": turn}
                        record["runs"] = [run]
                        _write(record_path, record)
                        return _emit("basic-team reminders armed for this session and turn.")
                    if request["action"] == "disarm" and record:
                        before = len(record.get("runs", []))
                        record["runs"] = [r for r in record.get("runs", []) if r.get("run_id") != request.get("run_id")]
                        if len(record["runs"]) != before:
                            _write(record_path, record)
                            return _emit("basic-team reminders disarmed.")
            return 0
        return _progress(args, event, active_session, turn)
    except Exception:
        return 0


def _progress(args, event, session=None, turn=None) -> int:
    if args.event != "PostToolUse" or event.get("tool_name") not in ("Agent", "spawn_agent", "wait_agent", "wait"):
        return 0
    session, turn = _main(args.host, event)
    if not session:
        return 0
    if not STATE_HOME.exists():
        return 0
    with _locked():
        record = _read(STATE_HOME / (_key(args.host, session) + ".json"))
    if not record:
        return 0
    for run in record.get("runs", []):
        if args.host == "codex" and run.get("turn_id") != turn:
            continue
        return _emit(f"Basic-team run is active. Reconcile received progress and save verified new facts to {run['page']} before dependent dispatch or briefing. Reuse this page; no new facts means no rewrite.")
    return 0


def _emit(message: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": message}}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="mode", required=True)
    cmd = subs.add_parser("arm")
    cmd.add_argument("page")
    cmd.add_argument("--host", choices=("codex", "claude"), required=True)
    cmd.add_argument("--session-id")
    cmd.set_defaults(func=helper, action="arm", run_id=None)
    cmd = subs.add_parser("disarm")
    cmd.add_argument("--host", choices=("codex", "claude"), required=True)
    cmd.add_argument("--session-id")
    cmd.add_argument("--run-id", required=True)
    cmd.set_defaults(func=helper, action="disarm", page=None)
    cmd = subs.add_parser("hook")
    cmd.add_argument("event", choices=("UserPromptSubmit", "SessionStart", "SessionEnd", "PostToolUse"))
    cmd.add_argument("--host", choices=("codex", "claude", "auto"), default="auto")
    cmd.set_defaults(func=hook)
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception:
        return 0 if args.mode == "hook" else 2


if __name__ == "__main__":
    raise SystemExit(main())
