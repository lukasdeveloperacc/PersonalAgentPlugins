#!/usr/bin/env -S uv run --script
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
from string import Template
import sys
import tempfile
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_DIR / "assets" / "progress-template.html"
BRIEFS = SKILL_DIR / "assets" / "briefs"
ROLES = Path(__file__).resolve().parent / "roles.json"
DATA_TAG = re.compile(r'(<script type="application/json" id="progress-data">)(.*?)(</script>)', re.S)
TOP_FIELDS = {"goal", "summary", "stage", "updated", "path", "blockers", "flow", "plan", "reviewNotice", "reviews", "decisions", "agents", "gates"}
GATE_FIELDS = {"planApproved", "requiredReviewers", "reviewTarget", "verdicts", "models", "exceptions", "evidence"}
VERDICTS = {"PASS", "CHANGES_REQUIRED", "BLOCKED"}
MANDATORY_REVIEWERS = {"karpathy", "ponytail"}
UNOBSERVED = "미확인"
UNOBSERVED_FORMS = {UNOBSERVED, "unknown"}
ROLE_NAMES = ("planner", "executor", "reviewer")
COMPLIANCE_ROWS = (
    ("page", "HTML progress page, final save, link/absolute path/save time"),
    ("hook", "Hook arm/disarm and actual confirmation or manual checkpoints"),
    ("eli5", "eli5 kickoff, plan, progress/review/blocker, completion briefings"),
    ("models", "Per-call model/effort arguments, alias resolution evidence, requested/invocation/observed report"),
    ("planning", "Planner skill paths, ralplan Architect/Critic evidence or permitted fallback"),
    ("tasks", "Native task list/allocation record and stage handoff documents"),
    ("reviews", "All required independent reviews on the final revision"),
    ("validation", "Required validation/test outcomes and unmet criteria"),
    ("shutdown", "Teammate shutdown, unresponsive-agent recovery, inactive team-state verification"),
    ("cleanup", "Applicable browser/MCP cleanup and configuration boundary"),
)
DERIVED_ROWS = {"page", "models", "reviews"}
COMPLIANCE_STATUS = {"함", "부분", "안 함"}
BRIEF_FIELDS = ("task_id", "request", "project_instructions", "workdir", "area", "owned", "inputs", "deliverable", "validation", "contacts")
ROLE_TITLES = {"planner": "Planner", "executor": "Executor"}
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
    if "gates" in data:
        validate_gates(data["gates"])
    if "_progress" in data:
        meta = data["_progress"]
        if not isinstance(meta, dict) or not isinstance(meta.get("checkpoint"), str) or not isinstance(meta.get("revision"), int) or not isinstance(meta.get("saved_at"), str):
            fail("invalid _progress metadata")


def is_text_list(value):
    return isinstance(value, list) and all(isinstance(item, str) and item for item in value)


def validate_gates(gates):
    if not isinstance(gates, dict) or gates.keys() - GATE_FIELDS:
        fail(f"gates must be an object with only: {', '.join(sorted(GATE_FIELDS))}")
    for key in ("planApproved", "reviewTarget"):
        if key in gates and (not isinstance(gates[key], str) or not gates[key].strip()):
            fail(f"gates.{key} must be a nonempty string")
    if "requiredReviewers" in gates and not is_text_list(gates["requiredReviewers"]):
        fail("gates.requiredReviewers must be an array of nonempty strings")
    exceptions = gates.get("exceptions", {})
    if not isinstance(exceptions, dict) or any(not isinstance(k, str) or not isinstance(v, str) or not v.strip() for k, v in exceptions.items()):
        fail("gates.exceptions must be an object of agent-id -> nonempty reason")
    verdicts = gates.get("verdicts")
    if verdicts:
        if not isinstance(verdicts, dict):
            fail("gates.verdicts must be an object")
        # Verdicts are saved only as a complete set, so early independent verdicts never reach the page.
        if set(verdicts) != set(gates.get("requiredReviewers", [])):
            fail("gates.verdicts must contain exactly the requiredReviewers; save verdicts only after all required reviews arrive")
        for name, verdict in verdicts.items():
            if not isinstance(verdict, dict) or verdict.keys() != {"revision", "verdict"} or not isinstance(verdict["revision"], str) or not verdict["revision"].strip() or verdict["verdict"] not in VERDICTS:
                fail(f"gates.verdicts.{name} needs revision and verdict ({' | '.join(sorted(VERDICTS))})")
    models = gates.get("models", {})
    if not isinstance(models, dict):
        fail("gates.models must be an object")
    for agent_id, record in models.items():
        required = {"role", "requested", "invocation", "observed"}
        if not isinstance(record, dict) or required - record.keys() or record.keys() - required - {"observedEffort", "observationEvidence"} or any(not isinstance(v, str) or not v.strip() for v in record.values()):
            fail(f"gates.models.{agent_id} needs nonempty role, requested, invocation, and observed strings; optional observedEffort and observationEvidence must be nonempty strings")
        if record["role"] not in ROLE_NAMES:
            fail(f"gates.models.{agent_id}.role must be one of {', '.join(ROLE_NAMES)}")
        if record["requested"] not in requested_ids(record["role"]):
            fail(f"gates.models.{agent_id}.requested must be the spawn-args requested ID for {record['role']}: {', '.join(sorted(requested_ids(record['role'])))}")
    evidence = gates.get("evidence", {})
    if not isinstance(evidence, dict):
        fail("gates.evidence must be an object")
    for key, row in evidence.items():
        if key not in dict(COMPLIANCE_ROWS) or key in DERIVED_ROWS:
            fail(f"gates.evidence.{key} is not a leader-reported compliance row")
        if not isinstance(row, dict) or row.keys() != {"status", "evidence"} or row["status"] not in COMPLIANCE_STATUS or not isinstance(row["evidence"], str) or not row["evidence"].strip():
            fail(f"gates.evidence.{key} needs status (함 | 부분 | 안 함) and nonempty evidence")


def requested_ids(role):
    entry = json.loads(ROLES.read_text(encoding="utf-8")).get(role)
    return {entry["claude"]["id"], entry["codex"]["model"]} if entry else set()


def requested_effort(record):
    entry = json.loads(ROLES.read_text(encoding="utf-8"))[record["role"]]
    return entry["claude"]["effort"] if record["requested"] == entry["claude"]["id"] else entry["codex"]["reasoning_effort"]


def observation_gaps(record):
    return [field for field in ("observed", "observedEffort", "observationEvidence")
            if record.get(field, UNOBSERVED).strip().lower() in UNOBSERVED_FORMS]


def model_problems(gates, need=("planner",), reviewers=()):
    models = gates.get("models", {})
    problems = [f"no {role} model record: save gates.models.<agent-id> with role {role}" for role in need
                if not any(record["role"] == role for record in models.values())]
    problems += [f"no model record for reviewer {name}: use the reviewer name as the agent id" for name in reviewers if name not in models]
    exceptions = gates.get("exceptions", {})
    for agent_id, record in models.items():
        for field, expected in (("observed", record["requested"]), ("observedEffort", requested_effort(record))):
            actual = record.get(field, UNOBSERVED)
            if actual.strip().lower() not in UNOBSERVED_FORMS and actual != expected:
                problems.append(f"{agent_id}: {field} {actual} != requested {expected}; BLOCKED, respawn with spawn-args and overwrite this record using the same agent id")
        gaps = observation_gaps(record)
        if gaps and agent_id not in exceptions:
            problems.append(f"{agent_id}: {', '.join(gaps)} {UNOBSERVED}; obtain actual host/pane model and effort evidence, or ask the user and add gates.exceptions.{agent_id} with the approval, or stop as BLOCKED")
    return problems


def review_problems(gates, stage):
    problems = []
    if not gates.get("reviewTarget"):
        problems.append("no frozen review target: set gates.reviewTarget")
    missing = MANDATORY_REVIEWERS - set(gates.get("requiredReviewers", []))
    if missing:
        problems.append(f"requiredReviewers is missing {', '.join(sorted(missing))}")
    if stage == "complete":
        verdicts = gates.get("verdicts")
        if not verdicts:
            problems.append("no verdicts saved")
        for name, verdict in (verdicts or {}).items():
            if verdict["verdict"] != "PASS":
                problems.append(f"{name}: {verdict['verdict']}")
            if verdict["revision"] != gates.get("reviewTarget"):
                problems.append(f"{name}: reviewed {verdict['revision']}, not the final target {gates.get('reviewTarget')}")
    return problems


def gate_problems(data, stage):
    gates = data.get("gates", {})
    problems = [] if gates.get("planApproved") else ["plan not approved: set gates.planApproved to the approved plan revision"]
    need = {"implementation": ("planner",), "review": ("planner", "executor"), "complete": ("planner", "executor")}[stage]
    problems += model_problems(gates, need, gates.get("requiredReviewers", []) if stage == "complete" else ())
    if stage != "implementation":
        problems += review_problems(gates, stage)
    return problems


def compliance_table(data):
    gates = data.get("gates", {})
    meta = data.get("_progress")
    derived = {"page": ("함", f"{data.get('path')} · 마지막 저장 {meta['saved_at']} · checkpoint {meta['checkpoint']}") if meta else ("안 함", "저장 기록 없음")}
    models = gates.get("models", {})
    problems = model_problems(gates, ("planner", "executor"), gates.get("requiredReviewers", []))
    excepted = [a for a, r in models.items() if observation_gaps(r) and a in gates.get("exceptions", {})]
    summary = "; ".join(f"{a}: requested {r['requested']} / effort {requested_effort(r)} / invocation {r['invocation']} / observed {r['observed']} / effort {r.get('observedEffort', UNOBSERVED)} / host/pane evidence {r.get('observationEvidence', UNOBSERVED)}" for a, r in models.items())
    if excepted:
        summary += "; 사용자 승인 예외: " + ", ".join(f"{a} ({gates['exceptions'][a]})" for a in excepted)
    derived["models"] = ("안 함", "기록 없음") if not models else (
        "부분" if problems or excepted else "함", summary + ("; " + "; ".join(problems) if problems else ""))
    verdicts = gates.get("verdicts")
    open_reviews = review_problems(gates, "complete")
    derived["reviews"] = ("안 함", "판정 기록 없음") if not verdicts else ("부분", "; ".join(open_reviews)) if open_reviews else (
        "함", f"revision {gates['reviewTarget']}: " + ", ".join(f"{n} {v['verdict']}" for n, v in verdicts.items()))
    lines = ["| Requirement | 함 / 부분 / 안 함 | Evidence, gap, or approved exception |", "| --- | --- | --- |"]
    for key, label in COMPLIANCE_ROWS:
        row = gates.get("evidence", {}).get(key)
        status, evidence = derived.get(key) or ((row["status"], row["evidence"]) if row else ("안 함", "증거 기록 없음"))
        lines.append(f"| {label} | {status} | {" ".join(evidence.replace("|", "/").split())} |")
    return "\n".join(lines)


def spawn_args(host, role):
    roles = json.loads(ROLES.read_text(encoding="utf-8"))
    if role not in roles or host not in roles[role]:
        fail(f"unknown role/host: {role}/{host}; roles are {', '.join(roles)}")
    settings = dict(roles[role][host])
    if host == "claude":
        requested = {"id": settings.pop("id"), "effort": settings["effort"]}
    else:
        requested = {"id": settings["model"], "effort": settings["reasoning_effort"]}
    return {"role": role, "host": host, "arguments": settings, "requested": requested}


def render_brief(role, fields):
    if role not in ("planner", "executor", "reviewer"):
        fail("brief --role must be planner, executor, or reviewer")
    required = BRIEF_FIELDS + (("revision", "reviewer") if role == "reviewer" else ())
    missing = [key for key in required if not isinstance(fields.get(key), str) or not fields[key].strip()]
    if not is_text_list(fields.get("skills")):
        missing.append("skills")
    if missing:
        fail(f"brief input is missing or empty: {', '.join(missing)}")
    values = {key: fields[key].strip() for key in required}
    values["skills"] = "\n".join(f"- {path}" for path in fields["skills"])
    values["role_title"] = fields["reviewer"].strip() if role == "reviewer" else ROLE_TITLES[role]
    text = (BRIEFS / "common.md").read_text(encoding="utf-8") + (BRIEFS / f"{role}.md").read_text(encoding="utf-8")
    return Template(text).substitute(values)


def briefing_line(data, path, saved_at):
    return f"진행판: [{data.get('goal') or path.stem}]({path}) — {path} · 마지막 저장: {saved_at}"


def graph_warnings(data):
    """Non-blocking hints for graphs that would render without the intended edges."""
    agents = [a for a in data.get("agents", []) if isinstance(a, dict)]
    by_stage = {}
    for agent in agents:
        by_stage.setdefault(agent.get("stage", "other"), []).append(agent)
    notes = []
    for agent in agents:
        # Legacy agents without an id cannot be patched, so only id'd agents are worth a warning.
        if agent.get("id") and "stage" not in agent:
            notes.append(f"{agent['id']}: missing stage; renders under 단계 미분류")
    by_id = {a["id"]: a for a in agents if a.get("id")}

    def reaches(agent, stage, seen=()):
        # Transitive, so a chain like backend-2 -> backend -> critic counts as linked to planning.
        return any(dep in by_id and dep not in seen and (by_id[dep].get("stage") == stage or reaches(by_id[dep], stage, seen + (dep,)))
                   for dep in agent.get("dependsOn", []))

    for stage, upstream in (("implementation", "planning"), ("review", "implementation")):
        if upstream in by_stage:
            notes += [f"{a.get('id')}: {stage} agent is not linked to any {upstream} agent; set dependsOn to the {upstream} agent(s) that actually gated it"
                      for a in by_stage.get(stage, []) if a.get("id") and not reaches(a, upstream)]
    if "implementation" in by_stage and "review" not in by_stage:
        notes.append("no review agents registered; add required reviewers as queued nodes (stage review, dependsOn the implementation agents)")
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
    parser.add_argument("command", choices=("init", "update", "status", "gate", "compliance", "spawn-args", "brief"))
    parser.add_argument("PAGE", nargs="?", help="absolute progress page; required except for spawn-args and brief")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--checkpoint")
    parser.add_argument("--stage", choices=("implementation", "review", "complete"), help="gate to check")
    parser.add_argument("--host", choices=("claude", "codex"))
    parser.add_argument("--role")
    args = parser.parse_args()
    try:
        if args.command == "spawn-args":
            if not args.host or not args.role:
                fail("spawn-args requires --host and --role")
            print(json.dumps(spawn_args(args.host, args.role), ensure_ascii=False))
            return 0
        if args.command == "brief":
            if not args.role or not args.input:
                fail("brief requires --role and --input")
            fields = json.loads(args.input.read_text(encoding="utf-8"))
            print(render_brief(args.role, fields if isinstance(fields, dict) else {}))
            return 0
        if not args.PAGE:
            fail(f"{args.command} requires PAGE")
        path = page_path(args.PAGE)
        if args.command in ("gate", "compliance"):
            _, data = read_data(path.read_text(encoding="utf-8"))
            validate(data)
            if args.command == "compliance":
                print(compliance_table(data))
                return 0
            if not args.stage:
                fail("gate requires --stage")
            problems = gate_problems(data, args.stage)
            print(json.dumps({"gate": args.stage, "ok": not problems, "problems": problems}, ensure_ascii=False))
            return 1 if problems else 0
        if args.command == "status":
            if args.input or args.checkpoint:
                fail("status does not accept --input or --checkpoint")
            _, data = read_data(path.read_text(encoding="utf-8"))
            validate(data)
            meta = data.get("_progress")
            if not meta:
                fail("progress page has no resume metadata")
            receipt = {"path": str(path), "saved_at": meta["saved_at"], "checkpoint": meta["checkpoint"], "revision": meta["revision"],
                       "briefing": briefing_line(data, path, meta["saved_at"])}
            warnings = graph_warnings(data)
            if warnings:
                receipt["graph_warnings"] = warnings
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
                if "gates" in incoming:
                    if not isinstance(incoming["gates"], dict):
                        fail("gates must be an object")
                    # Gate keys merge like agents; models/evidence merge per entry so records can arrive one at a time.
                    gates = dict(data.get("gates", {}))
                    for key, value in incoming["gates"].items():
                        gates[key] = {**gates.get(key, {}), **value} if key in ("models", "evidence", "exceptions") and isinstance(value, dict) else value
                    for key in ("models", "evidence", "exceptions"):
                        if isinstance(gates.get(key), dict):
                            gates[key] = {k: v for k, v in gates[key].items() if v is not None}  # null deletes a stale record
                    incoming["gates"] = gates
                data.update(incoming)
                revision = data.get("_progress", {}).get("revision", 0) + 1
            now = datetime.now().astimezone().isoformat(timespec="seconds")
            data["updated"] = now
            data["path"] = str(path)
            data["_progress"] = {"checkpoint": args.checkpoint, "revision": revision, "saved_at": now}
            warnings = graph_warnings(data)
            if warnings:
                data["_progress"]["graph_warnings"] = warnings
            validate(data, strict_dependency_ids)
            contents = html[:match.start()] + embedded(match, data) + html[match.end():]
            if args.command == "init":
                write_exclusive(path, contents)
            else:
                write_atomic(path, contents)
            receipt = {"path": str(path), "saved_at": now, "checkpoint": args.checkpoint, "revision": revision,
                       "briefing": briefing_line(data, path, now)}
            if warnings:
                receipt["graph_warnings"] = warnings
        print(json.dumps(receipt, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"progress.py: {error}", file=sys.stderr)
        return 2  # tool error; exit 1 is reserved for an unmet gate


if __name__ == "__main__":
    sys.exit(main())
