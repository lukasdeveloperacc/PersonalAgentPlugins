#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Create and update a Basic Team progress page without changing its renderer."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from datetime import datetime

TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "progress-template.html"
DATA_TAG = re.compile(r'(<script type="application/json" id="progress-data">)(.*?)(</script>)', re.S)
TOP_FIELDS = {"goal", "summary", "stage", "updated", "path", "blockers", "flow", "plan", "reviewNotice", "reviews", "decisions", "agents"}
TEXT_FIELDS = ("name", "role", "area", "status", "tone", "reported", "owned", "result", "next", "blocker", "model", "observation")
REQUIRED_AGENT_FIELDS = {"name", "role", "area", "status"}
AGENT_FIELDS = set(TEXT_FIELDS) | {"id", "stage", "dependsOn"}
TONES = {"neutral", "active", "good", "warn", "bad"}
STAGES = {"planning", "implementation", "review", "other"}


def fail(message):
    raise ValueError(message)


def page_path(value):
    path = Path(value)
    if not path.is_absolute():
        fail("PAGE must be an absolute path")
    path = path.resolve()
    root = (Path.cwd() / "docs" / "inprogress").resolve()
    if not path.is_relative_to(root):
        fail("PAGE must be under the executing project's docs/inprogress")
    return path


def read_data(html):
    match = DATA_TAG.search(html)
    if not match:
        fail("missing progress-data script")
    try:
        data = json.loads(match.group(2))
    except json.JSONDecodeError as error:
        fail(f"corrupt progress-data JSON: {error}")
    if not isinstance(data, dict):
        fail("progress-data must be an object")
    return match, data


def validate(data, strict_dependency_ids=()):
    unknown = data.keys() - TOP_FIELDS - {"_progress"}
    if unknown:
        fail(f"unknown progress fields: {', '.join(sorted(unknown))}")
    for key in ("goal", "summary", "stage", "updated", "path", "reviewNotice"):
        if key in data and not isinstance(data[key], str):
            fail(f"{key} must be a string")
    blockers = data.get("blockers")
    if blockers is not None:
        if not isinstance(blockers, dict) or blockers.keys() - {"text", "tone"} or not isinstance(blockers.get("text"), str) or blockers.get("tone") not in TONES:
            fail("blockers must contain string text and a valid tone")
    for key in ("flow", "plan", "reviews", "decisions"):
        if key in data:
            if not isinstance(data[key], list):
                fail(f"{key} must be an array")
            required = ("title", "body")
            for item in data[key]:
                if not isinstance(item, dict) or item.keys() - {"title", "body", "meta"} or any(not isinstance(item.get(field), str) for field in required) or ("meta" in item and not isinstance(item["meta"], str)):
                    fail(f"{key} entries must contain string title and body, with optional string meta")
    if "agents" in data:
        if not isinstance(data["agents"], list):
            fail("agents must be an array")
        ids = set()
        id_agents = []
        for agent in data["agents"]:
            if not isinstance(agent, dict) or agent.keys() - AGENT_FIELDS:
                fail("agent has unknown fields or is not an object")
            if REQUIRED_AGENT_FIELDS - agent.keys() or any(not isinstance(agent.get(field), str) for field in TEXT_FIELDS if field in agent):
                fail("agent required fields must be strings")
            if agent.get("tone") is not None and agent["tone"] not in TONES:
                fail("agent tone is invalid")
            if agent.get("id") is not None:
                if not isinstance(agent["id"], str) or not agent["id"]:
                    fail("agent id must be a nonempty string")
                if agent["id"] in ids:
                    fail(f"duplicate agent id: {agent['id']}")
                ids.add(agent["id"])
                id_agents.append(agent)
            if "stage" in agent and agent["stage"] not in STAGES:
                fail("agent stage is invalid")
            if "dependsOn" in agent and (not isinstance(agent["dependsOn"], list) or any(not isinstance(dep, str) for dep in agent["dependsOn"])):
                fail("agent dependsOn must be an array of strings")
        for agent in id_agents:
            if agent["id"] in strict_dependency_ids and any(dep not in ids for dep in agent.get("dependsOn", [])):
                fail(f"agent {agent['id']} has a dangling dependency")
    if "_progress" in data:
        meta = data["_progress"]
        if not isinstance(meta, dict) or not isinstance(meta.get("checkpoint"), str) or not isinstance(meta.get("revision"), int) or not isinstance(meta.get("saved_at"), str):
            fail("invalid _progress metadata")


def graph_warnings(data):
    """Non-blocking hints for graphs that would render without the intended edges."""
    agents = [a for a in data.get("agents", []) if isinstance(a, dict)]
    by_stage = {}
    for agent in agents:
        by_stage.setdefault(agent.get("stage", "other"), []).append(agent)
    notes = []
    for agent in agents:
        if not agent.get("id") or agent.get("stage") not in STAGES - {"other"}:
            notes.append(f"{agent.get('name')}: missing id or stage; renders under 단계 미분류 with no edges")
    for stage, upstream in (("implementation", "planning"), ("review", "implementation")):
        if upstream in by_stage:
            notes += [f"{a.get('id')}: {stage} agent has no recorded predecessor; set dependsOn to the {upstream} agent(s) that actually gated it"
                      for a in by_stage.get(stage, []) if a.get("id") and not a.get("dependsOn")]
    return notes


def embedded(match, data):
    encoded = json.dumps(data, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    return match.group(1) + "\n" + encoded + "\n" + match.group(3)


def write_exclusive(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        fail(f"progress page already exists: {path}")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(contents)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def write_atomic(path, contents):
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            output.write(contents)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("init", "update", "status"))
    parser.add_argument("PAGE")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--checkpoint")
    args = parser.parse_args()
    try:
        path = page_path(args.PAGE)
        if args.command == "status":
            if args.input or args.checkpoint:
                fail("status does not accept --input or --checkpoint")
            _, data = read_data(path.read_text(encoding="utf-8"))
            validate(data)
            meta = data.get("_progress")
            if not meta:
                fail("progress page has no resume metadata")
            receipt = {"path": str(path), "saved_at": meta["saved_at"], "checkpoint": meta["checkpoint"], "revision": meta["revision"]}
            if graph_warnings(data):
                receipt["graph_warnings"] = graph_warnings(data)
        else:
            if not args.checkpoint or not args.checkpoint.strip():
                fail("init and update require a nonempty --checkpoint")
            incoming = json.loads(args.input.read_text(encoding="utf-8")) if args.input else {}
            if not isinstance(incoming, dict):
                fail("input JSON must be an object")
            managed = incoming.keys() & {"updated", "path", "_progress"}
            if managed:
                fail(f"managed fields cannot be supplied: {', '.join(sorted(managed))}")
            if args.command == "init":
                if path.exists():
                    fail(f"progress page already exists: {path}")
                html = TEMPLATE.read_text(encoding="utf-8")
                match, data = read_data(html)
                data.update(incoming)
                validate(data)
                revision = 1
                strict_dependency_ids = {agent["id"] for agent in data.get("agents", []) if isinstance(agent, dict) and isinstance(agent.get("id"), str)}
            else:
                html = path.read_text(encoding="utf-8")
                match, data = read_data(html)
                validate(data)
                if "agents" in incoming:
                    if not isinstance(incoming["agents"], list):
                        fail("agents must be an array")
                    changes = {}
                    strict_dependency_ids = set()
                    for agent in incoming["agents"]:
                        if not isinstance(agent, dict) or not isinstance(agent.get("id"), str) or not agent["id"]:
                            fail("agent updates require a nonempty id")
                        if agent["id"] in changes:
                            fail(f"duplicate agent id: {agent['id']}")
                        changes[agent["id"]] = agent
                        if "dependsOn" in agent:
                            strict_dependency_ids.add(agent["id"])
                    existing = data.get("agents", [])
                    merged, consumed = [], set()
                    for agent in existing:
                        change = changes.get(agent.get("id")) if agent.get("id") else None
                        if change:
                            merged.append({**agent, **change})
                            consumed.add(change["id"])
                        else:
                            merged.append(agent)
                    for key, change in changes.items():
                        if key not in consumed and REQUIRED_AGENT_FIELDS - change.keys():
                            fail(f"new agent {key} must contain all renderer fields")
                        if key not in consumed:
                            merged.append(change)
                            strict_dependency_ids.add(key)
                    incoming["agents"] = merged
                else:
                    strict_dependency_ids = set()
                data.update(incoming)
                revision = data.get("_progress", {}).get("revision", 0) + 1
            now = datetime.now().astimezone().isoformat(timespec="seconds")
            data["updated"] = now
            data["path"] = str(path)
            data["_progress"] = {"checkpoint": args.checkpoint, "revision": revision, "saved_at": now}
            validate(data, strict_dependency_ids)
            contents = html[:match.start()] + embedded(match, data) + html[match.end():]
            if args.command == "init":
                write_exclusive(path, contents)
            else:
                write_atomic(path, contents)
            receipt = {"path": str(path), "saved_at": now, "checkpoint": args.checkpoint, "revision": revision}
            if graph_warnings(data):
                receipt["graph_warnings"] = graph_warnings(data)
        print(json.dumps(receipt, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"progress.py: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
