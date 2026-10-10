"""Score one run directory from its stream-json transcript with scripted assertions."""
import glob, json, subprocess, sys
from pathlib import Path

run = Path(sys.argv[1])
spawns, final, commands = [], "", []
for line in (run / "stream.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        continue
    if event.get("type") == "assistant":
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_use" and block.get("name") in ("Agent", "Task"):
                spawns.append(block.get("input", {}))
            if block.get("type") == "tool_use" and block.get("name") == "Bash":
                commands.append(str(block.get("input", {}).get("command", "")))
    if event.get("type") == "result":
        final = event.get("result", "")

def role(spawn):
    text = " ".join(str(spawn.get(k, "")) for k in ("name", "subagent_type", "description")).lower()
    for key, name in (("karpathy", "reviewer"), ("ponytail", "reviewer"), ("review", "reviewer"), ("plan", "planner"), ("architect", "planner"), ("critic", "planner"), ("exec", "executor")):
        if key in text:
            return name
    return "other"

expected = {"planner": ("opus", "medium"), "executor": ("haiku", "max"), "reviewer": ("sonnet", "high")}
names = " ".join(str(s.get("name", "")) + str(s.get("prompt", ""))[:400] for s in spawns).lower()
work = run / "work"
test = subprocess.run(["python3", "test_util.py"], cwd=work, capture_output=True, text=True)
util = (work / "util.py").read_text() if (work / "util.py").exists() else ""
checks = {
    "all_spawns_have_model_and_effort_no_fork": bool(spawns) and all(s.get("model") and s.get("effort") and s.get("subagent_type") != "fork" for s in spawns),
    "roles_match_table": bool(spawns) and all(role(s) == "other" or (s.get("model"), s.get("effort")) == expected[role(s)] for s in spawns),
    "both_mandatory_reviewers_spawned": "karpathy" in names and "ponytail" in names,
    "progress_page_exists": bool(glob.glob(str(work / "docs" / "inprogress" / "*-progress.html"))),
    "ran_gate_review_complete_and_compliance": all(any(f"progress.py" in c and word in c for c in commands) for word in (" gate ", " compliance ", "spawn-args", " brief ")),
    "final_has_compliance_table": "Requirement" in final and "함 / 부분 / 안 함" in final,
    "slugify_implemented_and_tests_pass": "def slugify" in util and test.returncode == 0,
}
print(json.dumps({"run": run.name, "spawns": len(spawns), "checks": checks, "passed": sum(checks.values()), "total": len(checks)}, ensure_ascii=False))
