# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "progress.py"
sys.path.insert(0, str(SCRIPT.parent))
import progress  # noqa: E402


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.page = Path(self.temp.name) / "docs" / "inprogress" / "run.html"

    def cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, text=True, capture_output=True)

    def data(self):
        return progress.read(self.page)[2]

    def test_init_update_merge_and_status(self):
        self.assertEqual(self.cli("init", str(self.page), "--title", "목록 API").returncode, 0)
        patch = {"tasks": [{"id": "PLAN", "title": "계획", "lane": "plan", "status": "완료"},
                           {"id": "BE-1", "title": "API", "owner": "backend-1", "after": ["PLAN"], "status": "진행중"}],
                 "decisions": [{"title": "E2E", "body": "생략"}]}
        self.assertEqual(self.cli("update", str(self.page), "--input", "-", stdin=json.dumps(patch)).returncode, 0)
        result = self.cli("update", str(self.page), "--input", "-", stdin=json.dumps(
            {"tasks": [{"id": "BE-1", "status": "완료"}], "decisions": [{"title": "Notion", "body": "제외"}],
             "reviews": [{"round": 1, "reviewer": "Karpathy Agent", "verdict": "PASS"}]}))
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.data()
        self.assertEqual([(t["id"], t["status"], t["lane"]) for t in data["tasks"]], [("PLAN", "완료", "plan"), ("BE-1", "완료", "build")])
        self.assertEqual(data["tasks"][1]["after"], ["PLAN"])  # partial task update keeps other fields
        self.assertEqual([d["title"] for d in data["decisions"]], ["E2E", "Notion"])  # earlier decisions are never dropped
        self.assertEqual(json.loads(result.stdout)["tasks"]["완료"], ["PLAN", "BE-1"])

    def test_bad_input_is_rejected_without_touching_the_page(self):
        self.cli("init", str(self.page))
        before = self.page.read_bytes()
        for patch in ({"tasks": [{"id": "A", "after": ["missing"]}]}, {"tasks": [{"id": "A", "status": "done"}]},
                      {"tasks": [{"id": "A", "lane": "구현"}]}, {"verdicts": {}}, {"reviews": [{"reviewer": "K"}]}):
            result = self.cli("update", str(self.page), "--input", "-", stdin=json.dumps(patch))
            self.assertEqual(result.returncode, 2, patch)
            self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.page.read_bytes(), before)
        self.assertEqual(self.cli("init", str(self.page)).returncode, 2)  # never overwrite a run

    def test_script_tag_in_text_cannot_break_the_page(self):
        self.cli("init", str(self.page))
        self.cli("update", str(self.page), "--input", "-", stdin=json.dumps({"summary": "</script><b>x</b>"}))
        self.assertEqual(self.data()["summary"], "</script><b>x</b>")
        self.assertEqual(self.page.read_text().count("</script>"), 2)

    def test_reference_example_patches_apply_in_order(self):
        example = (SCRIPT.parents[1] / "references" / "progress-example.md").read_text()
        patches = re.findall(r"```json\n(.*?)```", example, re.S)
        self.assertEqual(len(patches), 5)
        self.cli("init", str(self.page))
        for patch in patches:
            result = self.cli("update", str(self.page), "--input", "-", stdin=patch)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({t["status"] for t in self.data()["tasks"]}, {"완료"})

    def test_runs_on_declared_python_floor_with_uv(self):
        result = subprocess.run(["uv", "run", "--no-project", "--python", "3.10", "python", str(SCRIPT), "init", str(self.page)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
