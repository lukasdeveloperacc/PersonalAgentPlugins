# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("progress.py")
TEMPLATE = Path(__file__).parents[1] / "assets" / "progress-template.html"


class ProgressCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.page = self.root / "docs" / "inprogress" / "run.html"
        self.page.parent.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=self.root, text=True, capture_output=True)

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

    def init(self, payload=None):
        args = ["init", self.page, "--checkpoint", "kickoff"]
        if payload is not None:
            args += ["--input", self.input_file(payload)]
        return self.invoke(*args)

    @staticmethod
    def agent(agent_id, **updates):
        fields = dict(id=agent_id, name=agent_id, role="builder", area="api", status="working", tone="active",
                      reported="report", owned="files", result="done so far", next="continue", blocker="none",
                      model="model-x", observation="observed", stage="implementation", dependsOn=[])
        fields.update(updates)
        return fields

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


if __name__ == "__main__":
    unittest.main()
