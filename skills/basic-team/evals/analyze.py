"""Conservative Claude transcript scoring; recorded claims alone are not execution proof."""
import json
import re
import subprocess
import sys
from pathlib import Path

EXPECTED = {"planner": ("opus", "medium"), "architect": ("opus", "medium"),
            "critic": ("opus", "medium"), "executor": ("haiku", "max"),
            "karpathy": ("sonnet", "high"), "ponytail": ("sonnet", "high"),
            "impeccable": ("sonnet", "high"), "e2e": ("sonnet", "high")}


def role(call):
    # Use structured assignment identifiers, never names mentioned inside a prompt.
    names = " ".join(str(call.get(k, "")) for k in ("name", "subagent_type", "description")).lower()
    tokens = re.split(r"[^a-z]+", names)
    matches = [r for r in EXPECTED if r in tokens]
    return matches[0] if len(matches) == 1 else None


def text_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def objects(text):
    for line in text.splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                yield value
        except json.JSONDecodeError:
            pass


def transcript(path):
    calls, results, terminal = {}, {}, None
    child_reports = {}
    malformed = 0
    for position, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(event, dict):
            continue
        if event.get("parent_tool_use_id"):
            if event.get("type") == "result":
                child_reports[event["parent_tool_use_id"]] = {**event, "_event_index": position}
            continue
        if event.get("type") in ("assistant", "user"):
            for block in event.get("message", {}).get("content", []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use" and block.get("id"):
                    calls[block["id"]] = {**block, "_event_index": position}
                elif block.get("type") == "tool_result" and block.get("tool_use_id"):
                    results[block["tool_use_id"]] = {**block, "_event_index": position}
        if event.get("type") == "result":
            terminal = event
    return calls, results, terminal, malformed, child_reports


def backend_oracle(work):
    # The harness owns expectations; agent-written tests are supplementary only.
    script = """import sys
sys.path.insert(0, sys.argv[1])
from util import add, slugify
assert add(1, 2) == 3
for value, expected in [('Hello World', 'hello-world'), ('  A__B!! C  ', 'a-b-c'), ('', ''), ('!!!', ''), ('Already-Slug', 'already-slug'), ('a\\tb\\nc', 'a-b-c'), ('123', '123')]:
    assert slugify(value) == expected, (value, slugify(value), expected)
"""
    try:
        result = subprocess.run([sys.executable, "-I", "-c", script, str(work.resolve())],
                                capture_output=True, text=True, timeout=10)
        return {"level": "runtime", "passed": result.returncode == 0,
                "exit_status": result.returncode, "detail": result.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        return {"level": "runtime", "passed": False, "detail": "oracle timed out"}


def ui_checks(work):
    page = (work / "index.html").read_text() if (work / "index.html").exists() else ""
    button = re.search(r"<button\b[^>]*>(.*?)</button>", page, re.I | re.S)
    return {"level": "source-only", "runtime_passed": None,
            "checks": {"button": bool(button),
                       "accessible_name": bool(button and (re.search(r'aria-label\s*=\s*[\"\'][^\"\']+', button[0], re.I) or re.sub(r'<[^>]+>', '', button[1]).strip())),
                       "focus_style": bool(re.search(r':focus(?:-visible)?\s*[{,]', page))},
            "detail": "Theme toggle behavior and visual design remain unchecked; browser prohibited by this case."}


def analyze(run):
    manifest = json.loads((run / "manifest.json").read_text()) if (run / "manifest.json").exists() else {}
    calls, results, terminal, malformed, child_reports = transcript(run / "stream.jsonl")
    spawns = [(key, call["input"], role(call["input"])) for key, call in calls.items()
              if call.get("name") in ("Agent", "Task") and isinstance(call.get("input"), dict)]
    def completion(key, data):
        if data.get("run_in_background"):
            event = child_reports.get(key, {})
            return event if event.get("subtype") == "success" and not event.get("is_error") else None
        return results.get(key) if key in results and not results[key].get("is_error") else None

    successful = [(key, data, assigned) for key, data, assigned in spawns if completion(key, data)]
    def report(key, data):
        event = completion(key, data) or {}
        return event.get("result", text_content(event.get("content")))

    implementation_results_verified = {"planner", "executor"} <= {assigned for _, _, assigned in successful}
    gate_receipts = []
    for key, call in calls.items():
        command = call.get("input", {}).get("command", "")
        if call.get("name") != "Bash" or key not in results or results[key].get("is_error"):
            continue
        if re.search(r'progress\.py[\"\']?\s+gate\b', command):
            gate_receipts.extend(objects(text_content(results[key].get("content"))))
    pages = list((run / "work/docs/inprogress").glob("*-progress.html"))
    review_records_verified = False
    plan_verified = False
    complete_gate = False
    observed_policies = set()
    required = {"karpathy", "ponytail"} | ({"impeccable"} if manifest.get("kind") == "ui" else set())
    for page in pages:
        match = re.search(r'<script type="application/json" id="progress-data">(.*?)</script>', page.read_text(), re.S)
        if not match:
            continue
        try:
            page_data = json.loads(match[1])
            gates = page_data.get("gates", {})
            observed_policies.add(gates.get("observationPolicy", "strict-observation-v1"))
        except json.JSONDecodeError:
            continue
        plan = gates.get("planReview", {})
        plan_revision = gates.get("planApproved")
        plan_valid = bool(plan_revision) and plan.get("revision") == plan_revision
        if plan.get("method") == "plan":
            plan_valid = plan_valid and isinstance(plan.get("fallbackEvidence"), str) and bool(plan["fallbackEvidence"].strip())
            plan_valid = plan_valid and any(all(completion(p, pd)["_event_index"] < calls[e]["_event_index"] for e, _, r in spawns if r == "executor") for p, pd, r in successful if r == "planner")
        elif plan.get("method") == "ralplan":
            planning = {}
            for assigned in ("architect", "critic"):
                planning[assigned] = [(key, data) for key, data, r in successful if r == assigned
                    and re.search(r"Verdict:\s*APPROVE\b", report(key, data))
                    and re.search(r"(?:Reviewed (?:plan )?revision|Plan revision):\s*" + re.escape(str(plan_revision)) + r"(?:\s|$)", report(key, data), re.I)]
            sequence = any(completion(a, ad)["_event_index"] < calls[c]["_event_index"]
                           and any(completion(p, pd)["_event_index"] < calls[a]["_event_index"] for p, pd, r in successful if r == "planner")
                           and all(completion(c, cd)["_event_index"] < calls[e]["_event_index"] for e, _, r in spawns if r == "executor")
                           for a, ad in planning["architect"] for c, cd in planning["critic"])
            saved_reviews = plan.get("reviews", [])
            plan_valid = plan_valid and sequence and [r.get("role") for r in saved_reviews] == ["architect", "critic"]
            plan_valid = plan_valid and all(r.get("revision") == plan_revision and r.get("verdict") == "APPROVE" for r in saved_reviews)
        else:
            plan_valid = False
        target = gates.get("reviewTarget")
        records = gates.get("verdicts", {})
        necessary = required | {role({"name": name}) for name in gates.get("requiredReviewers", [])}
        necessary |= {name for name, decision in gates.get("conditionalReviews", {}).items()
                      if isinstance(decision, dict) and decision.get("required") is True}
        required |= necessary
        recorded_roles = {role({"name": name}): record for name, record in records.items()}
        valid = bool(target) and None not in necessary and necessary <= set(recorded_roles)
        for assigned in necessary:
            record = recorded_roles.get(assigned, {})
            reports = [report(key, data) for key, data, r in successful if r == assigned]
            valid = valid and record.get("revision") == target and record.get("verdict") == "PASS"
            valid = valid and any(re.search(r"Verdict:\s*PASS\b", report) and
                                     re.search(r"Reviewed revision:\s*" + re.escape(str(target)) + r"(?:\s|$)", report)
                                     for report in reports)
        bound_gate = any(g.get("gate") == "complete" and g.get("ok") is True
                         and g.get("reviewTarget") == target and g.get("path") == str(page.resolve())
                         and g.get("progressRevision") == page_data.get("_progress", {}).get("revision")
                         and isinstance(g.get("progressRevision"), int)
                         for g in gate_receipts)
        review_records_verified = review_records_verified or (valid and bound_gate)
        complete_gate = complete_gate or bound_gate
        plan_verified = plan_verified or (plan_valid and bound_gate)
    final = terminal.get("result", "") if terminal else ""
    status = manifest.get("exit_status")
    stop = manifest.get("stop_reason")
    if stop in ("cancelled", "timed_out", "capability_blocked"):
        outcome = "workflow_blocked" if stop == "capability_blocked" else stop
    elif terminal and terminal.get("subtype") == "error_max_budget_usd":
        outcome = "budget_exhausted"
    elif status not in (None, 0) or (terminal and terminal.get("is_error")):
        outcome = "runtime_error"
    elif terminal and terminal.get("subtype") == "success" and status == 0:
        outcome = "completed" if complete_gate and review_records_verified and plan_verified and implementation_results_verified else "workflow_blocked"
    else:
        outcome = "unknown"
    kind = manifest.get("kind", "backend")
    settings = bool(spawns) and all(assigned and (data.get("model"), data.get("effort")) == EXPECTED[assigned]
                                  and data.get("subagent_type") != "fork" for _, data, assigned in spawns)
    checks = {"roles_match_explicit_call_settings": settings,
              "mandatory_review_calls_succeeded": required <= {assigned for _, _, assigned in successful},
              "complete_gate_succeeded": complete_gate,
              "planning_sequence_verified": plan_verified,
              "planner_executor_results_verified": implementation_results_verified,
              "same_revision_review_results_verified": review_records_verified,
              "leader_terminal_success": bool(terminal and terminal.get("subtype") == "success" and not terminal.get("is_error")),
              "process_exit_zero": status == 0,
              "transcript_well_formed": malformed == 0,
              "source_identity_recorded": bool(manifest.get("source_commit") and manifest.get("source_hashes")),
              "final_compliance_table_present": sum(1 for line in final.splitlines() if line.startswith("|") and re.search(r"\|\s*(함|부분|안 함)\s*\|", line)) >= 10}
    product = ui_checks(run / "work") if kind == "ui" else backend_oracle(run / "work")
    return {"run": run.name, "outcome": outcome, "checks": checks,
            "workflow_verified": outcome == "completed" and all(checks.values()),
            "validated_completion": outcome == "completed" and all(checks.values()) and product.get("passed") is True,
            "product": product, "spawns": [{"tool_call_id": key, "role": assigned,
                "invocation": {k: data.get(k) for k in ("model", "effort", "subagent_type")},
                "result_received": key in results, "succeeded": bool(completion(key, data))}
                for key, data, assigned in spawns],
            "leader_final": final, "gate_receipts": gate_receipts,
            "recorded_observation_policies": sorted(observed_policies),
            "settings_evidence": "invocation-only; actual child model/effort unverified"}


if __name__ == "__main__":
    print(json.dumps(analyze(Path(sys.argv[1])), ensure_ascii=False))
