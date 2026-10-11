# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / "progress.py"
TEMPLATE = Path(__file__).parents[2] / "assets" / "progress-template.html"


class CliCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.page = self.root / "docs" / "inprogress" / "run.html"
        self.page.parent.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=self.root, text=True, capture_output=True, input=stdin)

    def invoke(self, *args):
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def data(self):
        html = self.page.read_text()
        start = html.index("<script type=\"application/json\" id=\"progress-data\">")
        start = html.index("\n", start) + 1
        end = html.index("\n</script>", start)
        return json.loads(html[start:end])

    def input_file(self, payload):
        path = self.root / "input.json"
        path.write_text(json.dumps(payload))
        return path

    def set_schema(self, version):
        html = self.page.read_text()
        data = self.data()
        data["_progress"]["schemaVersion"] = version
        data.pop("tasks", None)
        data.pop("taskPlanRevision", None)
        start = html.index('>', html.index('<script type="application/json" id="progress-data">')) + 1
        end = html.index('</script>', start)
        self.page.write_text(html[:start] + "\n" + json.dumps(data).replace("<", "\\u003c") + "\n" + html[end:])

    def init(self, payload=None):
        args = ["init", self.page, "--checkpoint", "kickoff", "--observation-policy", "strict-observation-v1"]
        if payload is not None:
            args += ["--input", self.input_file(payload)]
        receipt = self.invoke(*args)
        # Existing tests are recovery fixtures for pages written before policy/schema metadata existed.
        html = self.page.read_text()
        data = self.data()
        data.pop("tasks", None)
        data.pop("taskPlanRevision", None)
        data["gates"].pop("observationPolicy", None)
        data["_progress"].pop("schemaVersion", None)
        start = html.index('>', html.index('<script type="application/json" id="progress-data">')) + 1
        end = html.index('</script>', start)
        self.page.write_text(html[:start] + "\n" + json.dumps(data).replace("<", "\\u003c") + "\n" + html[end:])
        return receipt

    @staticmethod
    def agent(agent_id, **updates):
        fields = dict(id=agent_id, name=agent_id, role="builder", area="api", status="working", tone="active",
                      reported="report", owned="files", result="done so far", next="continue", blocker="none",
                      model="model-x", observation="observed", stage="implementation", dependsOn=[])
        fields.update(updates)
        return fields


class ProgressCliTests(CliCase):
    def test_record_times_saved_preserved_and_legacy_not_invented(self):
        record = {"title": "First", "body": "evidence"}
        receipt = self.init({"plan": [record], "agents": [self.agent("a")]})
        first = self.data()["plan"][0]
        self.assertEqual(first["recordedAt"], receipt["saved_at"])
        self.invoke("update", self.page, "--checkpoint", "next", "--input", self.input_file({
            "plan": [record, {"title": "Second", "body": "new"}], "agents": [{"id": "a", "status": "done"}]
        }))
        self.assertEqual(self.data()["plan"][0], first)
        self.assertEqual(self.data()["agents"][0]["recordedAt"], receipt["saved_at"])
        self.assertEqual(self.data()["plan"][1]["recordedAt"], self.data()["updated"])
        # Simulate an existing page whose record predates timestamp support.
        html = self.page.read_text()
        import re
        html = re.sub(r',?\s*"recordedAt": "[^"]+"', '', html)
        self.page.write_text(html)
        self.invoke("update", self.page, "--checkpoint", "legacy", "--input", self.input_file({"plan": [record]}))
        self.assertNotIn("recordedAt", self.data()["plan"][0])

    def test_all_record_types_get_time_and_handoff_retry_keeps_it(self):
        record = {"title": "entry", "body": "evidence"}
        handoff = HandoffTests.record()
        handoff.pop("recordedAt")
        task = PhaseTodoTests.task()
        task.pop("recordedAt")
        payload = {key: [dict(record)] for key in ("flow", "plan", "reviews", "decisions")}
        payload.update(tasks=[task], agents=[self.agent("a")], handoffs=[handoff])
        receipt = self.invoke("init", self.page, "--checkpoint", "start", "--input", self.input_file(payload))
        for key in payload:
            self.assertEqual(self.data()[key][0]["recordedAt"], receipt["saved_at"], key)
        original = self.data()["handoffs"]
        self.invoke("update", self.page, "--checkpoint", "retry", "--input", self.input_file({"handoffs": [handoff]}))
        self.assertEqual(self.data()["handoffs"], original)

    def test_invalid_record_times_rejected_atomically(self):
        self.init()
        before = self.page.read_bytes()
        for value in (None, 12, "yesterday", "2026-10-11T10:00:00"):
            result = self.run_cli("update", self.page, "--checkpoint", "bad-time", "--input", self.input_file({
                "reviews": [{"title": "Review", "body": "result", "recordedAt": value}]
            }))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(self.page.read_bytes(), before)

    def test_renderer_time_sort_is_stable_and_does_not_mutate_records(self):
        html = TEMPLATE.read_text()
        helpers = html[html.index("function recordTime("):html.index("function list(")]
        result = subprocess.run(["node", "-e", "const assert = require('node:assert/strict');\n" + helpers + """
const records = [
  {id:'unknown'}, {id:'late',recordedAt:'2026-10-11T01:00:01Z'},
  {id:'first',recordedAt:'2026-10-11T10:00:00+09:00'},
  {id:'tie',recordedAt:'2026-10-11T01:00:00Z'}, {id:'invalid',recordedAt:'bad'}
];
const before = JSON.stringify(records);
assert.deepEqual(chronological(records).map(x=>x.id), ['first','tie','late','unknown','invalid']);
assert.equal(JSON.stringify(records), before);
assert.equal(recordedTime(records[0]), '시간 미기록');
const node=(tag,text)=>({tag,text,children:[],append(...items){this.children.push(...items)}});
assert.equal(timestamp(records[0]).textContent, '시간 미기록');
assert.equal(timestamp(records[2]).children[1].dateTime, records[2].recordedAt);
"""], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_partial_agent_update_preserves_existing_fields_and_other_agents(self):
        self.init({"agents": [self.agent("a", model="model-a", dependsOn=["b"]), self.agent("b", name="Bee")]})
        self.invoke("update", self.page, "--checkpoint", "agent-a", "--input", self.input_file({"agents": [{"id": "a", "status": "done", "result": "finished"}]}))
        agents = self.data()["agents"]
        self.assertEqual(agents[0]["model"], "model-a")
        self.assertEqual(agents[0]["dependsOn"], ["b"])
        self.assertEqual(agents[0]["result"], "finished")
        self.assertEqual(agents[1]["name"], "Bee")
        self.assertIn("<script>", self.page.read_text())

    def test_legacy_agent_without_id_survives_unrelated_and_other_agent_updates(self):
        legacy = self.agent("discard-id")
        del legacy["id"]
        self.init({"agents": [legacy, self.agent("current")]})
        self.invoke("update", self.page, "--checkpoint", "partial", "--input", self.input_file({
            "summary": "updated summary", "agents": [{"id": "current", "status": "done"}]
        }))
        data = self.data()
        self.assertEqual(data["summary"], "updated summary")
        self.assertNotIn("id", data["agents"][0])
        self.assertEqual(data["agents"][0]["name"], "discard-id")
        self.assertEqual(data["agents"][1]["status"], "done")

    def test_managed_metadata_patches_are_rejected_without_mutation(self):
        self.init()
        before = self.page.read_bytes()
        for field, value in (("updated", "forged"), ("path", "/outside"), ("_progress", {"revision": 99})):
            result = self.run_cli("update", self.page, "--checkpoint", "managed", "--input", self.input_file({field: value}))
            self.assertNotEqual(result.returncode, 0, field)
            self.assertEqual(self.page.read_bytes(), before, field)

    def test_legacy_dangling_dependency_allows_status_and_unrelated_patch(self):
        self.init({"agents": [self.agent("old")]})
        data = self.data()
        data["agents"][0]["dependsOn"] = ["removed-agent"]
        html = self.page.read_text()
        start = html.index("<script type=\"application/json\" id=\"progress-data\">")
        start = html.index("\n", start) + 1
        end = html.index("\n</script>", start)
        self.page.write_text(html[:start] + json.dumps(data) + html[end:])
        self.assertEqual(self.invoke("status", self.page)["revision"], 1)
        self.invoke("update", self.page, "--checkpoint", "legacy", "--input", self.input_file({"summary": "still readable"}))
        self.assertEqual(self.data()["agents"][0]["dependsOn"], ["removed-agent"])

    def test_new_dangling_dependency_patch_is_rejected_intact(self):
        self.init({"agents": [self.agent("a")]})
        before = self.page.read_bytes()
        result = self.run_cli("update", self.page, "--checkpoint", "bad-edge", "--input", self.input_file({
            "agents": [{"id": "a", "dependsOn": ["missing"]}]
        }))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.page.read_bytes(), before)

    def test_less_than_is_escaped_without_changing_template_renderer(self):
        original = TEMPLATE.read_text()
        self.init({"summary": "literal </script><script>bad"})
        html = self.page.read_text()
        self.assertIn(r"\u003c/script>", html)
        self.assertNotIn("literal </script><script>bad", html)
        self.assertIn("function renderAgents(agents)", html)
        self.assertEqual(html[:html.index('<script type="application/json" id="progress-data">')], original[:original.index('<script type="application/json" id="progress-data">')])

    def test_invalid_graph_update_leaves_original_file_intact(self):
        self.init({"agents": [self.agent("a")]})
        before = self.page.read_bytes()
        result = self.run_cli("update", self.page, "--checkpoint", "bad", "--input", self.input_file({"agents": [{"id": "a", "dependsOn": ["missing"]}]}))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.page.read_bytes(), before)

    def test_init_collision_and_outside_path_are_rejected(self):
        self.init()
        before = self.page.read_bytes()
        result = self.run_cli("init", self.page, "--checkpoint", "again")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.page.read_bytes(), before)
        outside = self.root / "elsewhere.html"
        result = self.run_cli("init", outside, "--checkpoint", "outside")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(outside.exists())

    def test_status_returns_checkpoint_revision_and_absolute_path(self):
        self.init()
        self.invoke("update", self.page, "--checkpoint", "resume-2")
        receipt = self.invoke("status", self.page)
        self.assertEqual(receipt["path"], str(self.page.resolve()))
        self.assertEqual(receipt["checkpoint"], "resume-2")
        self.assertEqual(receipt["revision"], 2)
        self.assertTrue(receipt["saved_at"])

    def test_unlinked_implementation_agents_are_reported_and_linked_ones_are_not(self):
        plan = self.agent("critic", stage="planning", status="done", tone="good")
        receipt = self.invoke("init", self.page, "--checkpoint", "k", "--input", self.input_file({"agents": [plan, self.agent("backend")]}))
        self.assertEqual(len(receipt["graph_warnings"]), 2)
        self.assertIn("backend", receipt["graph_warnings"][0])
        receipt = self.invoke("update", self.page, "--checkpoint", "linked", "--input", self.input_file({"agents": [{"id": "backend", "dependsOn": ["critic"]}]}))
        self.assertIn("no review agents", receipt["graph_warnings"][0])
        queued = self.agent("karpathy", stage="review", status="대기", tone="neutral", dependsOn=["backend"])
        receipt = self.invoke("update", self.page, "--checkpoint", "reviewers", "--input", self.input_file({"agents": [queued]}))
        self.assertNotIn("graph_warnings", receipt)

    def test_transitive_links_pass_and_wrong_stage_links_warn(self):
        agents = [self.agent("critic", stage="planning", status="done", tone="good"),
                  self.agent("backend", dependsOn=["critic"]),
                  self.agent("backend-2", dependsOn=["backend"]),
                  self.agent("karpathy", stage="review", status="대기", tone="neutral", dependsOn=["backend-2"]),
                  self.agent("ponytail", stage="review", status="대기", tone="neutral", dependsOn=["critic"])]
        receipt = self.init({"agents": agents})
        self.assertEqual(len(receipt["graph_warnings"]), 1)
        self.assertIn("ponytail", receipt["graph_warnings"][0])

    def test_warnings_are_saved_for_the_page_and_cleared_when_fixed(self):
        self.init({"agents": [self.agent("critic", stage="planning", status="done", tone="good"), self.agent("backend")]})
        self.assertEqual(len(self.data()["_progress"]["graph_warnings"]), 2)
        fixes = [{"id": "backend", "dependsOn": ["critic"]}, self.agent("karpathy", stage="review", status="대기", tone="neutral", dependsOn=["backend"])]
        self.invoke("update", self.page, "--checkpoint", "fixed", "--input", self.input_file({"agents": fixes}))
        self.assertNotIn("graph_warnings", self.data()["_progress"])
        self.assertIn("data._progress?.graph_warnings", self.page.read_text())

    def test_legacy_agents_without_id_are_not_warned_about_but_missing_stage_is(self):
        legacy = dict(name="old", role="r", area="a", status="done")
        staged = self.agent("x")
        del staged["stage"]
        receipt = self.init({"agents": [legacy, staged]})
        self.assertEqual(len(receipt["graph_warnings"]), 1)
        self.assertIn("x: missing stage", receipt["graph_warnings"][0])

    def test_receipts_carry_the_briefing_line(self):
        receipt = self.init({"goal": "로그인 고치기"})
        self.assertEqual(receipt["briefing"], f"진행판: [로그인 고치기]({receipt['path']}) — {receipt['path']} · 마지막 저장: {receipt['saved_at']}")
        self.assertEqual(self.invoke("status", self.page)["briefing"], receipt["briefing"])


class GateAndBriefTests(CliCase):
    PLANNER = {"role": "planner", "requested": "claude-opus-5-5", "invocation": "model=opus, effort=medium", "observed": "claude-opus-5-5", "observedEffort": "medium", "observationEvidence": "host pane planner: model and effort settings"}
    EXECUTOR = {"role": "executor", "requested": "claude-haiku-5-5", "invocation": "model=haiku, effort=max", "observed": "claude-haiku-5-5", "observedEffort": "max", "observationEvidence": "host pane executor: model and effort settings"}
    REVIEWER = {"role": "reviewer", "requested": "claude-sonnet-5-5", "invocation": "model=sonnet, effort=high", "observed": "claude-sonnet-5-5", "observedEffort": "high", "observationEvidence": "host pane reviewer: model and effort settings"}
    MODEL_OK = EXECUTOR

    def all_models(self):
        return {"planner": self.PLANNER, "b1": self.EXECUTOR, "karpathy": self.REVIEWER, "ponytail": self.REVIEWER}

    def gate(self, stage):
        result = self.run_cli("gate", self.page, "--stage", stage)
        return result.returncode, json.loads(result.stdout)

    def patch(self, gates):
        return self.run_cli("update", self.page, "--checkpoint", "gates", "--input", self.input_file({"gates": gates}))

    def test_spawn_args_match_the_skill_model_table(self):
        skill = (Path(__file__).parents[2] / "SKILL.md").read_text()
        for role, row in (("planner", "Planner"), ("executor", "Executor"), ("reviewer", "Reviewer (each)")):
            cells = [c.strip(" `") for c in next(l for l in skill.splitlines() if l.startswith(f"| {row} ")).split("|")[2:6]]
            claude = self.invoke("spawn-args", "--host", "claude", "--role", role)
            codex = self.invoke("spawn-args", "--host", "codex", "--role", role)
            self.assertEqual([codex["arguments"]["model"], codex["arguments"]["reasoning_effort"], claude["requested"]["id"], claude["arguments"]["effort"]], cells)
            self.assertNotIn("id", claude["arguments"])
            self.assertIn(claude["arguments"]["model"], {"opus", "sonnet", "haiku", "fable"})

    def test_implementation_gate_needs_approved_plan_and_proven_models(self):
        self.init()
        code, result = self.gate("implementation")
        self.assertEqual(code, 1)
        self.assertEqual(len(result["problems"]), 2)
        self.assertEqual(self.patch({"planApproved": "plan-r2", "models": {"planner": dict(self.PLANNER, observed="claude-sonnet-5-5")}}).returncode, 0)
        self.assertIn("BLOCKED", self.gate("implementation")[1]["problems"][0])
        # A second record for a respawn overwrites by the same agent id, and unknown is normalized.
        self.patch({"models": {"planner": dict(self.PLANNER, observed="unknown")}})
        self.assertIn("exceptions.planner", self.gate("implementation")[1]["problems"][0])
        self.patch({"exceptions": {"planner2": "다른 에이전트 승인"}})
        self.assertEqual(self.gate("implementation")[0], 1)
        self.patch({"exceptions": {"planner": "사용자가 미확인 진행 승인"}})
        self.assertEqual(self.gate("implementation"), (0, {"gate": "implementation", "ok": True, "problems": []}))

    def test_model_record_must_use_the_role_requested_id_and_can_be_deleted(self):
        self.init({"gates": {"models": {"x": self.EXECUTOR}}})
        self.assertNotEqual(self.patch({"models": {"x": dict(self.EXECUTOR, requested="claude-sonnet-5-5")}}).returncode, 0)
        self.assertNotEqual(self.patch({"models": {"y": {k: v for k, v in self.EXECUTOR.items() if k != "role"}}}).returncode, 0)
        self.assertEqual(self.patch({"models": {"x": None}}).returncode, 0)
        self.assertEqual(self.data()["gates"]["models"], {})

    def test_missing_effort_or_host_evidence_blocks_but_legacy_records_still_load(self):
        self.init({"gates": {"planApproved": "p1"}})
        for fields in (("observedEffort",), ("observationEvidence",), ("observedEffort", "observationEvidence")):
            with self.subTest(fields=fields):
                record = {k: v for k, v in self.PLANNER.items() if k not in fields}
                self.patch({"models": {"planner": None}})
                self.assertEqual(self.patch({"models": {"planner": record}}).returncode, 0)
                code, result = self.gate("implementation")
                self.assertEqual(code, 1)
                for field in fields:
                    self.assertIn(field, result["problems"][0])
        for field in ("observedEffort", "observationEvidence"):
            self.assertNotEqual(self.patch({"models": {"planner": dict(self.PLANNER, **{field: " "})}}).returncode, 0)

    def test_unknown_effort_requires_same_agent_exception_and_compliance_stays_partial(self):
        models = self.all_models()
        models["planner"] = dict(self.PLANNER, observedEffort="미확인", observationEvidence="unknown")
        self.init({"gates": {"planApproved": "p1", "models": models}})
        self.assertEqual(self.gate("implementation")[0], 1)
        self.patch({"exceptions": {"other": "사용자 예외 승인"}})
        self.assertEqual(self.gate("implementation")[0], 1)
        self.patch({"exceptions": {"planner": "사용자가 추론 및 호스트 관찰 미확인 진행 승인"}})
        self.assertEqual(self.gate("implementation")[0], 0)
        output = self.run_cli("compliance", self.page).stdout
        row = next(line for line in output.splitlines() if "Per-call model/effort" in line)
        self.assertIn("| 부분 |", row)
        self.assertIn("effort 미확인", row)
        self.assertIn("사용자 승인 예외", row)

    def test_known_model_or_effort_mismatch_blocks_despite_exception(self):
        self.init({"gates": {"planApproved": "p1", "exceptions": {"planner": "미확인 진행 승인"}}})
        for field, actual, expected in (("observed", "claude-sonnet-5-5", "claude-opus-5-5"), ("observedEffort", "high", "medium")):
            with self.subTest(field=field):
                self.patch({"models": {"planner": dict(self.PLANNER, **{field: actual})}})
                code, result = self.gate("implementation")
                self.assertEqual(code, 1)
                self.assertIn(f"{field} {actual} != requested {expected}; BLOCKED", result["problems"][0])

    def test_confirmed_codex_model_and_effort_pass_and_report_host_evidence(self):
        settings = self.invoke("spawn-args", "--host", "codex", "--role", "planner")
        record = {"role": "planner", "requested": settings["requested"]["id"], "invocation": str(settings["arguments"]), "observed": settings["requested"]["id"], "observedEffort": settings["requested"]["effort"], "observationEvidence": "Codex pane /status settings capture"}
        self.init({"gates": {"planApproved": "p1", "models": dict(self.all_models(), planner=record)}})
        self.assertEqual(self.gate("implementation")[0], 0)
        row = next(line for line in self.run_cli("compliance", self.page).stdout.splitlines() if "Per-call model/effort" in line)
        self.assertIn("| 함 |", row)
        self.assertIn("Codex pane /status settings capture", row)
        self.assertIn(f"effort {settings['requested']['effort']}", row)
        self.assertNotIn("호스트가 노출하지 않아", row)

    def test_review_and_complete_gates_need_executor_and_reviewer_records(self):
        models = self.all_models()
        del models["ponytail"]
        self.init({"gates": {"planApproved": "p1", "models": models, "requiredReviewers": ["karpathy", "ponytail"], "reviewTarget": "r2"}})
        self.assertEqual(self.gate("review")[0], 0)
        problems = self.gate("complete")[1]["problems"]
        self.assertTrue(any("reviewer ponytail" in p for p in problems), problems)

    def test_partial_verdicts_are_rejected_and_complete_needs_all_pass_on_target(self):
        self.init({"gates": {"planApproved": "p1", "models": self.all_models(), "requiredReviewers": ["karpathy", "ponytail"], "reviewTarget": "r2"}})
        before = self.page.read_bytes()
        self.assertNotEqual(self.patch({"verdicts": {"karpathy": {"revision": "r2", "verdict": "PASS"}}}).returncode, 0)
        self.assertEqual(self.page.read_bytes(), before)
        self.patch({"verdicts": {"karpathy": {"revision": "r2", "verdict": "PASS"}, "ponytail": {"revision": "r1", "verdict": "PASS"}}})
        code, result = self.gate("complete")
        self.assertEqual((code, len(result["problems"])), (1, 1))
        self.assertIn("ponytail: reviewed r1", result["problems"][0])
        self.patch({"verdicts": {}, "reviewTarget": "r3"})  # new round clears saved verdicts
        self.assertEqual(self.data()["gates"]["verdicts"], {})
        self.patch({"verdicts": {"karpathy": {"revision": "r3", "verdict": "PASS"}, "ponytail": {"revision": "r3", "verdict": "PASS"}}})
        self.assertEqual(self.gate("complete")[0], 0)

    def test_compliance_derives_rows_and_marks_missing_evidence(self):
        self.init({"gates": {"planApproved": "p1", "models": self.all_models(), "requiredReviewers": ["karpathy", "ponytail"], "reviewTarget": "r2",
                             "verdicts": {"karpathy": {"revision": "r2", "verdict": "PASS"}, "ponytail": {"revision": "r2", "verdict": "CHANGES_REQUIRED"}},
                             "evidence": {"hook": {"status": "함", "evidence": "run_id x | confirmed\nline2"}}}})
        result = self.run_cli("compliance", self.page)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {line.split("|")[1].strip(): line.split("|")[2].strip() for line in result.stdout.splitlines()[2:]}
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows["HTML progress page, final save, link/absolute path/save time"], "함")
        self.assertEqual(rows["Hook arm/disarm and actual confirmation or manual checkpoints"], "함")
        self.assertEqual(rows["Per-call model/effort arguments, alias resolution evidence, requested/invocation/observed report"], "함")
        self.assertEqual(rows["All required independent reviews on the final revision"], "부분")
        self.assertEqual(rows["Teammate shutdown, unresponsive-agent recovery, inactive team-state verification"], "안 함")
        self.assertNotEqual(self.patch({"evidence": {"reviews": {"status": "함", "evidence": "trust me"}}}).returncode, 0)

    def test_tool_errors_exit_2_and_unmet_gates_exit_1(self):
        self.assertEqual(self.run_cli("gate", self.root / "docs/inprogress/missing.html", "--stage", "review").returncode, 2)
        self.init()
        self.assertEqual(self.run_cli("gate", self.page, "--stage", "review").returncode, 1)
        self.assertEqual(self.run_cli("spawn-args", "--host", "claude", "--role", "nobody").returncode, 2)

    def test_brief_rejects_missing_fields_and_renders_without_expected_model_id(self):
        fields = {key: f"{key} value" for key in ("task_id", "request", "project_instructions", "workdir", "area", "owned", "inputs", "deliverable", "validation", "contacts")}
        fields["skills"] = ["/skills/ralplan/SKILL.md"]
        result = self.run_cli("brief", "--role", "reviewer", "--input", self.input_file(fields))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("revision, reviewer", result.stderr)
        brief = self.run_cli("brief", "--role", "reviewer", "--input", self.input_file(dict(fields, revision="r2", reviewer="Karpathy Agent"))).stdout
        self.assertTrue(brief.startswith("ROLE: Karpathy Agent (task_id value)"))
        self.assertIn("without a separate identity-release handshake", brief)
        self.assertNotIn("MODEL: <the exact model ID", brief)
        self.assertIn("Reviewed revision: r2", brief)
        self.assertNotIn("claude-", brief)
        self.assertNotIn("$role", brief)
        dollar = self.run_cli("brief", "--role", "executor", "--input", self.input_file(dict(fields, request="costs $5 and ${HOME} $role_title")))
        self.assertEqual(dollar.returncode, 0, dollar.stderr)
        self.assertIn("costs $5 and ${HOME} $role_title", dollar.stdout)
        for role in ("planner", "executor"):
            out = self.run_cli("brief", "--role", role, "--input", self.input_file(fields))
            self.assertEqual(out.returncode, 0, out.stderr)


class InvocationPolicyTests(CliCase):
    PLANNER = GateAndBriefTests.PLANNER
    all_models = GateAndBriefTests.all_models
    EXECUTOR = GateAndBriefTests.EXECUTOR
    REVIEWER = GateAndBriefTests.REVIEWER
    gate = GateAndBriefTests.gate
    patch = GateAndBriefTests.patch
    def setUp(self):
        super().setUp()
        self.plan = self.root / "plan.md"
        self.plan.write_text("approved plan")
        self.architect = self.root / "architect.md"
        self.architect.write_text("architect review")
        self.critic = self.root / "critic.md"
        self.critic.write_text("critic review with architect input")

    def v2_gates(self):
        settings = self.invoke("spawn-args", "--host", "claude", "--role", "planner")
        record = dict(self.PLANNER, observed="미확인", observedEffort="미확인", observationEvidence="미확인",
                      invocationArguments=settings["arguments"], invocationAccepted=True, invocationEvidence="Agent call 1 accepted")
        return {"planApproved": "p1", "models": {name: dict(record, role=name) for name in ("planner", "architect", "critic")},
                "planReview": {"method": "ralplan", "revision": "p1", "artifact": str(self.plan), "sha256": hashlib.sha256(self.plan.read_bytes()).hexdigest(), "reviews": [
                    {"role": "architect", "revision": "p1", "artifact": str(self.architect), "sha256": hashlib.sha256(self.architect.read_bytes()).hexdigest(), "verdict": "APPROVE"},
                    {"role": "critic", "revision": "p1", "artifact": str(self.critic), "sha256": hashlib.sha256(self.critic.read_bytes()).hexdigest(), "verdict": "APPROVE"}]},
                "conditionalReviews": {"impeccable": {"required": False, "reason": "no UI"}, "e2e": {"required": False, "reason": "isolated helper"}},
                "requiredReviewers": ["karpathy", "ponytail"]}

    def init_v2(self, gates):
        receipt = self.invoke("init", self.page, "--checkpoint", "kickoff", "--input", self.input_file({"gates": gates}))
        self.set_schema(2)  # Recovery fixture: schema 2 retains its original gates.
        return receipt

    def test_new_run_policy_default_and_immutable(self):
        self.init_v2(self.v2_gates())
        self.assertEqual(self.data()["gates"]["observationPolicy"], "invocation-evidence-v2")
        before = self.page.read_bytes()
        self.assertNotEqual(self.patch({"observationPolicy": "strict-observation-v1"}).returncode, 0)
        self.assertEqual(self.page.read_bytes(), before)
        self.assertNotEqual(self.run_cli("status", self.page, "--observation-policy", "strict-observation-v1").returncode, 0)
        self.assertEqual(self.gate("implementation")[0], 0)
        self.assertIn("invocation-only", self.run_cli("compliance", self.page).stdout)

    def test_invocation_missing_rejected_wrong_and_known_mismatch_block(self):
        gates = self.v2_gates()
        self.init_v2(gates)
        for changes in ({"invocationArguments": {}}, {"invocationAccepted": False}, {"invocationEvidence": "unknown"},
                        {"invocationArguments": {"model": "opus", "effort": "high"}}, {"observed": "claude-sonnet-5-5"}):
            record = dict(gates["models"]["planner"], **changes)
            self.assertEqual(self.patch({"models": {"planner": record}, "exceptions": {"planner": "approved missing observation"}}).returncode, 0)
            self.assertEqual(self.gate("implementation")[0], 1, changes)

    def test_plan_revision_sequence_missing_artifacts_and_conditional_decisions_block(self):
        gates = self.v2_gates()
        self.init_v2(gates)
        for change in ({"revision": "p0"}, {"artifact": str(self.root / "missing")},
                       {"reviews": list(reversed(gates["planReview"]["reviews"]))}):
            self.patch({"planReview": dict(gates["planReview"], **change)})
            self.assertEqual(self.gate("implementation")[0], 1)
        self.patch({"planReview": gates["planReview"], "conditionalReviews": {}})
        self.assertEqual(self.gate("implementation")[0], 1)
        self.patch({"conditionalReviews": dict(gates["conditionalReviews"], impeccable={"required": True, "reason": "new UI"})})
        self.assertEqual(self.gate("implementation")[0], 1)

    def test_ready_does_not_require_shutdown_but_complete_does(self):
        gates = self.v2_gates()
        for name, record in self.all_models().items():
            settings = self.invoke("spawn-args", "--host", "claude", "--role", record["role"])
            gates["models"][name] = dict(record, invocationArguments=settings["arguments"], invocationAccepted=True, invocationEvidence=f"Agent {name} accepted")
        gates.update(reviewTarget="r1", verdicts={name: {"revision": "r1", "verdict": "PASS"} for name in ("karpathy", "ponytail")},
                     validation={"revision": "r1", "status": "PASS", "evidence": "uv run tests exit 0", "checks": [{"command": "uv run tests", "revision": "r1", "exitCode": 0, "evidence": "exit 0"}]})
        self.init_v2(gates)
        code, receipt = self.gate("ready")
        self.assertEqual(code, 0)
        self.assertTrue(Path(receipt["path"]).samefile(self.page))
        self.assertEqual(receipt["reviewTarget"], "r1")
        self.assertEqual(receipt["progressRevision"], self.data()["_progress"]["revision"])
        self.assertEqual(self.gate("complete")[0], 1)
        self.patch({"evidence": {"shutdown": {"status": "함", "evidence": "host confirms all run agents ended"},
                                 "cleanup": {"status": "안 함", "evidence": "해당 없음: no browser or hook identity"},
                                 "tasks": {"status": "함", "evidence": "task allocation reconciled; final handoff saved"}}})
        self.assertEqual(self.gate("complete")[0], 0)
        for row in (None, {"status": "부분", "evidence": "final handoff missing"}):
            self.patch({"evidence": {"tasks": row}})
            self.assertEqual(self.gate("ready")[0], 0)
            self.assertTrue(any("evidence.tasks" in p for p in self.gate("complete")[1]["problems"]))
        self.patch({"evidence": {"tasks": {"status": "함", "evidence": "allocation reconciled and final handoff saved"}}})
        self.patch({"validation": dict(gates["validation"], checks=[{"command": "uv run tests", "revision": "r1", "exitCode": 1, "evidence": "failed"}])})
        self.assertEqual(self.gate("ready")[0], 1)
        self.patch({"validation": gates["validation"], "models": {"karpathy": gates["models"]["b1"]}})
        self.assertTrue(any("INVOCATION_ROLE" in p for p in self.gate("ready")[1]["problems"]))
        self.patch({"models": {"karpathy": gates["models"]["karpathy"]}})
        self.patch({"validation": dict(gates["validation"], revision="r0")})
        self.assertEqual(self.gate("ready")[0], 1)

    def test_stale_artifact_and_new_strict_run_require_current_evidence(self):
        gates = self.v2_gates()
        self.invoke("init", self.page, "--checkpoint", "strict", "--observation-policy", "strict-observation-v1", "--input", self.input_file({"gates": gates}))
        self.set_schema(2)
        self.assertEqual(self.gate("implementation")[0], 1)
        self.patch({"models": {name: dict(record, observed=self.PLANNER["observed"], observedEffort="medium", observationEvidence="host /status") for name, record in gates["models"].items()}})
        self.assertEqual(self.gate("implementation")[0], 0)
        self.architect.write_text("modified after review")
        problems = self.gate("implementation")[1]["problems"]
        self.assertTrue(any("ARTIFACT_STALE" in p for p in problems))

    def test_helper_roles_share_planner_settings_and_use_own_briefs(self):
        fields = {key: f"{key} value" for key in ("task_id", "request", "project_instructions", "workdir", "area", "owned", "inputs", "deliverable", "validation", "contacts")}
        fields["skills"] = ["/skills/ralplan/SKILL.md"]
        for role in ("architect", "critic"):
            self.assertEqual(self.invoke("spawn-args", "--host", "codex", "--role", role)["arguments"],
                             self.invoke("spawn-args", "--host", "codex", "--role", "planner")["arguments"])
            result = self.run_cli("brief", "--role", role, "--input", self.input_file(fields))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"ROLE: {role.title()}", result.stdout)
            self.assertNotIn("ask the leader to dispatch", result.stdout)


class HandoffTests(CliCase):
    def setUp(self):
        super().setUp()
        for name in ("plan", "architect", "critic"):
            path = self.root / f"{name}.md"
            path.write_text(f"{name} evidence")
            setattr(self, name, path)
    PLANNER = InvocationPolicyTests.PLANNER
    EXECUTOR = InvocationPolicyTests.EXECUTOR
    REVIEWER = InvocationPolicyTests.REVIEWER
    all_models = InvocationPolicyTests.all_models
    v2_gates = InvocationPolicyTests.v2_gates
    gate = InvocationPolicyTests.gate
    patch = InvocationPolicyTests.patch

    @staticmethod
    def record(record_id="plan-1", transition="planning-to-implementation", revision="p1", **changes):
        return dict(dict(id=record_id, transition=transition, round=1, revision=revision, outcome="ready",
                         recordedAt="2026-10-11T10:00:00+09:00", summary="다음 단계 인수", evidence=["tool call 1 completed"], next=["dispatch owner"], pending=[]), **changes)

    def init_current(self, handoffs=None):
        self.invoke("init", self.page, "--checkpoint", "kickoff", "--input", self.input_file({
            "gates": self.v2_gates(), "handoffs": handoffs or [],
            "taskPlanRevision": "p1", "tasks": [dict(id="build", phase="Implementation", title="Build", owner="executor", status="done", evidence="verified")]}))

    def append(self, records):
        return self.run_cli("update", self.page, "--checkpoint", "handoff", "--input", "-", stdin=json.dumps({"handoffs": records}))

    def test_append_retry_conflict_and_unrelated_update_preserve_history(self):
        first = self.record()
        self.init_current([first])
        self.assertEqual(self.data()["_progress"]["schemaVersion"], 3)
        second = dict(first, id="plan-2", round=2, summary="새 계획 회차")
        self.assertEqual(self.append([first, second]).returncode, 0)
        self.assertEqual(self.append([second]).returncode, 0)
        self.assertEqual(self.append([]).returncode, 0)
        self.assertEqual(self.data()["handoffs"], [first, second])
        self.invoke("update", self.page, "--checkpoint", "summary", "--input", self.input_file({"summary": "new"}))
        self.assertEqual(self.data()["handoffs"], [first, second])
        before = self.page.read_bytes()
        conflict = self.append([dict(first, summary="replace history")])
        self.assertEqual(conflict.returncode, 2)
        self.assertIn("immutable", conflict.stderr)
        self.assertEqual(self.page.read_bytes(), before)

    def test_malformed_handoffs_rejected_without_mutation(self):
        self.init_current()
        first = self.record()
        malformed = [None, {}, [dict(first, transition=[])], [dict(first, outcome={})], [dict(first, round=True)],
                     [dict(first, revision=" ")], [dict(first, evidence=[])], [dict(first, next=[3])],
                     [dict(first, pending="none")], [dict(first, extra="x")], [first, first]]
        before = self.page.read_bytes()
        for records in malformed:
            with self.subTest(records=records):
                self.assertEqual(self.append(records).returncode, 2)
                self.assertEqual(self.page.read_bytes(), before)

    def test_read_only_selection_has_receipt_and_missing_id_error(self):
        first = self.record(summary="인수 </script> 기록")
        self.init_current([first])
        before = self.page.read_bytes()
        all_records = self.invoke("handoffs", self.page)
        self.assertEqual(all_records["handoffs"], [first])
        self.assertEqual(all_records["revision"], 1)
        self.assertEqual(all_records["saved_at"], self.data()["_progress"]["saved_at"])
        self.assertTrue(Path(all_records["path"]).samefile(self.page))
        self.assertEqual(self.invoke("handoffs", self.page, "--id", "plan-1"), all_records)
        self.assertEqual(self.run_cli("handoffs", self.page, "--id", "missing").returncode, 2)
        self.assertEqual(self.run_cli("handoffs", self.page, "--input", "-").returncode, 2)
        self.assertEqual(self.page.read_bytes(), before)
        self.assertNotIn("인수 </script>", self.page.read_text())

    def test_stdin_init_update_and_brief_need_no_input_file(self):
        result = self.run_cli("init", self.page, "--checkpoint", "start", "--input", "-", stdin=json.dumps({"summary": "stdin"}))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.data()["summary"], "stdin")
        self.assertEqual(self.append([self.record()]).returncode, 0)
        fields = {key: key for key in ("task_id", "request", "project_instructions", "workdir", "area", "owned", "inputs", "deliverable", "validation", "contacts")}
        fields["skills"] = []
        brief = self.run_cli("brief", "--role", "executor", "--input", "-", stdin=json.dumps(fields))
        self.assertEqual(brief.returncode, 0, brief.stderr)
        self.assertIn("ROLE: Executor", brief.stdout)
        self.assertFalse((self.root / "input.json").exists())

    def test_latest_applicable_handoff_blocks_missing_stale_or_blocked(self):
        self.init_current()
        self.assertTrue(any("HANDOFF_MISSING" in p for p in self.gate("implementation")[1]["problems"]))
        self.assertEqual(self.append([self.record()]).returncode, 0)
        self.assertEqual(self.gate("implementation")[0], 0)
        self.append([dict(self.record(), id="plan-stale", revision="p0")])
        self.assertTrue(any("HANDOFF_STALE" in p for p in self.gate("implementation")[1]["problems"]))
        self.append([dict(self.record(), id="plan-blocked", outcome="BLOCKED")])
        self.assertTrue(any("HANDOFF_OUTCOME" in p for p in self.gate("implementation")[1]["problems"]))
        self.append([dict(self.record(), id="plan-cancelled", outcome="cancelled")])
        self.assertTrue(any("HANDOFF_OUTCOME" in p for p in self.gate("implementation")[1]["problems"]))
        self.append([dict(self.record(), id="plan-ready", round=2)])
        self.assertEqual(self.gate("implementation")[0], 0)

    def prepare_review(self):
        self.init_current([self.record()])
        models = {}
        for name, record in self.all_models().items():
            settings = self.invoke("spawn-args", "--host", "claude", "--role", record["role"])
            models[name] = dict(record, invocationArguments=settings["arguments"], invocationAccepted=True, invocationEvidence="accepted")
        self.patch({"models": models, "reviewTarget": "r1", "verdicts": {name: {"revision": "r1", "verdict": "PASS"} for name in ("karpathy", "ponytail")},
                    "validation": {"revision": "r1", "status": "PASS", "evidence": "no executable changes", "checks": [], "notApplicable": "documentation only"},
                    "evidence": {"tasks": {"status": "함", "evidence": "terminal tasks"}, "shutdown": {"status": "함", "evidence": "all stopped"}, "cleanup": {"status": "안 함", "evidence": "해당 없음: no browser"}}})

    def test_review_and_completion_handoffs_ready_order_and_pending(self):
        self.prepare_review()
        self.assertTrue(any("HANDOFF_TRANSITION" in p for p in self.gate("review")[1]["problems"]))
        self.assertTrue(any("HANDOFF_TRANSITION" in p for p in self.gate("ready")[1]["problems"]))
        self.append([self.record("build-1", "implementation-to-verification", "r1")])
        self.assertEqual(self.gate("review")[0], 0)
        self.append([dict(self.record("fix-1", "fixes-to-verification", "r1"), outcome="BLOCKED")])
        self.assertTrue(any("HANDOFF_OUTCOME" in p for p in self.gate("review")[1]["problems"]))
        self.append([dict(self.record("fix-2", "fixes-to-verification", "r1"), round=2)])
        self.assertEqual(self.gate("review")[0], 0)
        self.assertEqual(self.gate("ready")[0], 0)
        self.assertTrue(any("HANDOFF_TRANSITION" in p for p in self.gate("complete")[1]["problems"]))
        self.append([dict(self.record("done-pending", "completion", "r1"), pending=["unresolved task"])])
        self.assertTrue(any("HANDOFF_PENDING" in p for p in self.gate("complete")[1]["problems"]))
        self.append([dict(self.record("done", "completion", "r1"), next=[])])
        self.assertEqual(self.gate("complete")[0], 0)
        self.append([dict(self.record("done-stale", "completion", "r0"), next=[])])
        self.assertTrue(any("HANDOFF_STALE" in p for p in self.gate("complete")[1]["problems"]))
        self.append([dict(self.record("done-blocked", "completion", "r1"), outcome="BLOCKED")])
        self.assertTrue(any("HANDOFF_OUTCOME" in p for p in self.gate("complete")[1]["problems"]))

    def test_later_recovery_supersedes_review_entry_and_completion_on_same_revision(self):
        self.prepare_review()
        self.append([self.record("build", "implementation-to-verification", "r1"),
                     self.record("done", "completion", "r1")])
        self.assertEqual(self.gate("ready")[0], 0)
        self.assertEqual(self.gate("complete")[0], 0)
        self.append([self.record("recover", "verification-to-fixes", "r1", outcome="BLOCKED", pending=["await recovery"])])
        for stage in ("review", "ready", "complete"):
            self.assertTrue(any("HANDOFF_TRANSITION" in p for p in self.gate(stage)[1]["problems"]), stage)
        self.append([self.record("fix", "fixes-to-verification", "r1")])
        self.assertEqual(self.gate("ready")[0], 0)
        self.assertTrue(any("HANDOFF_TRANSITION" in p for p in self.gate("complete")[1]["problems"]))
        self.append([self.record("done-again", "completion", "r1")])
        self.assertEqual(self.gate("complete")[0], 0)
        self.append([self.record("replan", revision="p1")])
        self.assertEqual(self.gate("implementation")[0], 0)
        self.assertTrue(any("HANDOFF_TRANSITION" in p for p in self.gate("ready")[1]["problems"]))

    def test_old_schema_resume_preserves_version_without_new_gate(self):
        for version in (1, 2):
            with self.subTest(version=version):
                self.page.unlink(missing_ok=True)
                self.init_current()
                self.set_schema(version)
                self.assertEqual(self.gate("implementation")[0], 0)
                self.assertEqual(self.append([self.record()]).returncode, 0)
                self.assertEqual(self.data()["_progress"]["schemaVersion"], version)


class PhaseTodoTests(CliCase):
    @staticmethod
    def task(**changes):
        return dict(dict(id="build", phase="Implementation", title="Build API", owner="backend", status="pending", evidence="", recordedAt="2026-10-11T10:00:00+09:00"), **changes)

    def patch_tasks(self, tasks, **fields):
        return self.run_cli("update", self.page, "--checkpoint", "todo", "--input", self.input_file(dict(tasks=tasks, **fields)))

    def test_snapshot_roundtrip_reopen_and_unrelated_update(self):
        self.init()
        tasks = [self.task(), self.task(id="cleanup", phase="Finish", owner="leader")]
        self.assertEqual(self.patch_tasks(tasks, taskPlanRevision="p1").returncode, 0)
        self.assertEqual(self.data()["tasks"], tasks)
        self.invoke("update", self.page, "--checkpoint", "summary", "--input", self.input_file({"summary": "unchanged checklist"}))
        self.assertEqual(self.data()["tasks"], tasks)
        tasks[0].update(status="done", evidence="API test passed")
        self.assertEqual(self.patch_tasks(tasks).returncode, 0)
        tasks[0].update(status="in_progress", evidence="regression found")
        self.assertEqual(self.patch_tasks(tasks).returncode, 0)
        self.assertEqual(self.data()["tasks"], tasks)
        self.assertEqual(self.data()["taskPlanRevision"], "p1")
        self.assertEqual(self.patch_tasks(tasks[:1]).returncode, 0)
        self.assertEqual(self.data()["tasks"], tasks[:1])

    def test_invalid_snapshots_leave_page_intact(self):
        self.init()
        before = self.page.read_bytes()
        invalid = [None, {}, [None], [self.task(extra="unexpected")], [self.task(title=" ")],
                   [self.task(owner=2)], [self.task(status="complete")], [self.task(status="done")],
                   [self.task(status="blocked", evidence=" ")], [self.task(), self.task(phase="Another phase")]]
        missing = self.task()
        del missing["evidence"]
        invalid.append([missing])
        for tasks in invalid:
            with self.subTest(tasks=tasks):
                self.assertNotEqual(self.patch_tasks(tasks).returncode, 0)
                self.assertEqual(self.page.read_bytes(), before)
        self.assertNotEqual(self.patch_tasks([self.task()], taskPlanRevision=12).returncode, 0)
        self.assertEqual(self.page.read_bytes(), before)
        self.assertEqual(self.patch_tasks([self.task(status="blocked", evidence="waiting for API contract")]).returncode, 0)

    def test_all_gates_require_checklist_and_matching_source_plan(self):
        self.init({"gates": {"planApproved": "p1"}})
        for fields, expected in (({}, "TASK_PLAN_REVISION"), ({"taskPlanRevision": "p0"}, "TASK_PLAN_REVISION"),
                                 ({"taskPlanRevision": ""}, "TASK_PLAN_REVISION")):
            self.assertEqual(self.patch_tasks([self.task()], **fields).returncode, 0)
            for stage in ("implementation", "review", "ready", "complete"):
                result = self.run_cli("gate", self.page, "--stage", stage)
                self.assertTrue(any(expected in p for p in json.loads(result.stdout)["problems"]), result.stdout)
        self.assertEqual(self.patch_tasks([], taskPlanRevision="p1").returncode, 0)
        for stage in ("implementation", "review", "ready", "complete"):
            result = self.run_cli("gate", self.page, "--stage", stage)
            self.assertTrue(any("TASKS_EMPTY" in p for p in json.loads(result.stdout)["problems"]))

    def test_legacy_without_tasks_adds_no_checklist_gate(self):
        self.init()
        self.assertNotIn("tasks", self.data())
        for stage in ("implementation", "review", "ready", "complete"):
            result = self.run_cli("gate", self.page, "--stage", stage)
            self.assertFalse(any(p.startswith("TASK") for p in json.loads(result.stdout)["problems"]))

    def test_ready_allows_final_cleanup_but_complete_requires_done(self):
        # Reuse the valid current-run fixture, keeping all other gates exercised.
        case = HandoffTests(methodName="test_review_and_completion_handoffs_ready_order_and_pending")
        case.setUp()
        try:
            case.prepare_review()
            case.append([case.record("build", "implementation-to-verification", "r1"), case.record("done", "completion", "r1")])
            for status in ("pending", "in_progress", "blocked"):
                task = self.task(id="cleanup", phase="Finish", owner="leader", status=status, evidence="cleanup pending")
                case.invoke("update", case.page, "--checkpoint", "cleanup", "--input", case.input_file({"tasks": [task]}))
                self.assertEqual(case.gate("ready")[0], 0)
                code, result = case.gate("complete")
                self.assertEqual(code, 1)
                self.assertTrue(any("TASKS_INCOMPLETE" in p for p in result["problems"]))
            case.invoke("update", case.page, "--checkpoint", "cleanup-done", "--input", case.input_file({"tasks": [dict(task, status="done", evidence="host stopped")]}))
            self.assertEqual(case.gate("complete")[0], 0)
        finally:
            case.tearDown()


if __name__ == "__main__":
    unittest.main()
