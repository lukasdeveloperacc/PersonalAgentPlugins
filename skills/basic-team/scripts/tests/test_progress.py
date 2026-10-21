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

    def update(self, patch):
        return self.cli("update", str(self.page), "--input", "-", stdin=json.dumps(patch))

    def data(self):
        return progress.read(self.page)[2]

    def edit(self, change):
        """Change the stored data directly, as an older page or an earlier update would have left it."""
        html, match, data = progress.read(self.page)
        change(data)
        progress.write(self.page, html, match, data)

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

    def test_todos_merge_by_id_inside_their_task(self):
        self.cli("init", str(self.page))
        self.update({"tasks": [{"id": "FE", "todos": [{"id": "FE-1", "text": "조건 수정", "phase": "구현"},
                                                     {"id": "FE-2", "phase": "검증", "detail": "vitest"}]}]})
        result = self.update({"tasks": [{"id": "FE", "status": "진행중", "todos": [{"id": "FE-1", "done": True}]}]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.data()["tasks"][0]["todos"],
                         [{"id": "FE-1", "text": "조건 수정", "phase": "구현", "done": True},
                          {"id": "FE-2", "phase": "검증", "detail": "vitest", "text": "FE-2"}])

    def test_unfinished_todos_block_success_but_not_interruption(self):
        self.cli("init", str(self.page))
        self.update({"tasks": [{"id": "FE", "status": "진행중", "todos": [{"id": "FE-1", "done": True}, {"id": "FE-2"}]},
                               {"id": "OLD", "status": "중단", "todos": [{"id": "OLD-1", "done": False}]},
                               {"id": "DONE", "lane": "finish"}]})
        before = self.page.read_bytes()
        result = self.update({"tasks": [{"id": "FE", "status": "완료"}]})
        self.assertIn("task FE: unfinished TODOs: FE-2", result.stderr)
        result = self.update({"tasks": [{"id": "FE", "status": "완료", "todos": [{"id": "FE-2", "done": True}]},
                                        {"id": "DONE", "status": "완료"}]})  # an interrupted task's TODOs count too
        self.assertIn("run stage 완료 has unfinished TODOs: OLD: OLD-1; resolve them or interrupt the run", result.stderr)
        self.assertEqual(self.page.read_bytes(), before)
        result = self.update({"stage": "중단", "tasks": [{"id": "FE", "status": "완료", "todos": [{"id": "FE-2", "done": True}]}]})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bad_input_is_rejected_without_touching_the_page(self):
        self.cli("init", str(self.page))
        before = self.page.read_bytes()
        for patch in ({"tasks": [{"id": "A", "after": ["missing"]}]}, {"tasks": [{"id": "A", "status": "done"}]},
                      {"tasks": [{"id": "A", "lane": "구현"}]}, {"verdicts": {}}, {"reviews": [{"reviewer": "K"}]},
                      {"stage": "done"}, {"stage": "수정(1라운드)"}, {"stage": "완료", "tasks": [{"id": "A"}]},
                      {"reviews": [{"round": 1, "reviewer": "Karpathy"}]}, {"tasks": None},
                      {"tasks": [{"id": "A", "todos": {}}]}, {"tasks": [{"id": "A", "todos": [{"text": "no id"}]}]},
                      {"tasks": [{"id": "A", "todos": [{"id": "A-1", "done": "yes"}]}]},
                      {"tasks": [{"id": "A", "todos": [{"id": "A-1", "status": "완료"}]}]}):
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
        self.assertEqual(len(patches), 7)
        self.cli("init", str(self.page))
        for patch in patches:
            result = self.cli("update", str(self.page), "--input", "-", stdin=patch)
            self.assertEqual(result.returncode, 0, result.stderr)
            tasks = {task["id"]: task for task in self.data()["tasks"]}
            if self.data()["stage"] == "수정 (1라운드)":
                # Finished reviewers should idle while their approval gate stays open.
                self.assertEqual(tasks["R1-X"]["status"], "대기중")
                self.assertEqual([t["owner"] for t in tasks.values() if t["status"] == "진행중"],
                                 ["frontend-lead"])
                before = self.page.read_bytes()
                premature_finish = self.update({"stage": "완료", "tasks": [{"id": "FIX", "status": "완료"}]})
                self.assertEqual(premature_finish.returncode, 2)
                self.assertIn("R1-X", premature_finish.stderr)
                self.assertEqual(self.page.read_bytes(), before)
            for change in json.loads(patch).get("tasks", []):
                if change.get("status") == "진행중":
                    for prerequisite in tasks[change["id"]].get("after", []):
                        self.assertEqual(tasks[prerequisite]["status"], "완료",
                                         f"{change['id']} starts before {prerequisite} completes")
        self.assertEqual({t["status"] for t in self.data()["tasks"]}, {"완료"})
        self.assertEqual(self.data()["stage"], "완료")

    def test_team_summary_and_domain_review_preserve_history_on_resume(self):
        self.cli("init", str(self.page))
        patch = {
            "tasks": [
                {"id": "FE", "owner": "frontend-lead", "status": "완료", "note": "2/2 완료 · evidence/frontend.md"},
                {"id": "BE", "owner": "backend-lead", "status": "완료", "note": "1/1 완료 · evidence/backend.md"},
                {"id": "DOC", "owner": "docs-lead", "status": "완료", "after": ["BE"]},
                {"id": "DOMAIN", "owner": "backend-review-lead", "lane": "review", "status": "진행중",
                 "after": ["FE", "BE", "DOC"], "note": "r1 · BLOCKED · 권한 검사 대기"},
            ],
            "reviews": [{"round": 1, "reviewer": reviewer, "verdict": "PASS", "note": "r1"}
                        for reviewer in progress.REVIEWERS],
            "decisions": [{"title": "API-1", "body": "양측 확인 · BE 소유"}],
        }
        result = self.update(patch)
        self.assertEqual(result.returncode, 0, result.stderr)
        first = self.data()
        # Each CLI call reads the persisted page anew, like a resumed coordinator.
        result = self.cli("status", str(self.page))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["tasks"]["진행중"], ["DOMAIN"])
        result = self.update(patch)
        self.assertEqual(result.returncode, 0, result.stderr)
        replay = self.data()
        for key in ("tasks", "reviews", "decisions"):
            self.assertEqual(replay[key], first[key], key)
        result = self.update({
            "tasks": [{"id": "DOMAIN", "status": "완료", "note": "r2 · PASS · evidence/domain.md"}],
            "reviews": [{"round": 2, "reviewer": reviewer, "verdict": "PASS", "note": "r2"}
                        for reviewer in progress.REVIEWERS],
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        resumed = self.data()
        self.assertEqual(resumed["tasks"][:3], first["tasks"][:3])
        self.assertEqual(resumed["tasks"][3]["after"], ["FE", "BE", "DOC"])
        self.assertEqual(resumed["tasks"][3]["note"], "r2 · PASS · evidence/domain.md")
        self.assertEqual(len(resumed["reviews"]), 8)
        self.assertEqual(resumed["reviews"][:4], first["reviews"])
        self.assertEqual(resumed["decisions"], first["decisions"])

    def test_unsupported_team_fields_and_domain_review_rows_preserve_bytes(self):
        self.cli("init", str(self.page))
        self.update({"tasks": [{"id": "FE", "owner": "frontend-lead", "status": "완료"}]})
        before = self.page.read_bytes()
        for invalid in (
            {"team": "frontend"},
            {"parent": "root"},
            {"reviews": [{"round": 1, "reviewer": "frontend-lead", "verdict": "PASS"}]},
            {"reviews": [{"round": 1, "reviewer": "backend-review-lead", "verdict": "PASS"}]},
        ):
            with self.subTest(patch=invalid):
                # Even a valid change accompanying invalid input must not be persisted.
                result = self.update({"summary": "must not be saved", **invalid})
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.page.read_bytes(), before)

    def test_finish_rejects_open_team_or_domain_review_even_with_external_passes(self):
        for task in (
            {"id": "BE", "owner": "backend-lead", "lane": "build", "status": "진행중",
             "note": "1/2 완료 · 통합 검사 막힘"},
            {"id": "DOMAIN", "owner": "backend-review-lead", "lane": "review", "status": "진행중",
             "note": "r1 · BLOCKED · required evidence 없음"},
        ):
            with self.subTest(task=task["id"]):
                self.page = Path(self.temp.name) / f"{task['id']}.html"
                self.cli("init", str(self.page))
                result = self.update({
                    "tasks": [task, {"id": "DONE", "lane": "finish", "status": "진행중", "after": [task["id"]]}],
                    "reviews": [{"round": 1, "reviewer": reviewer, "verdict": "PASS"}
                                for reviewer in progress.REVIEWERS],
                })
                self.assertEqual(result.returncode, 0, result.stderr)
                before = self.page.read_bytes()
                result = self.update({"tasks": [{"id": "DONE", "status": "완료"}]})
                self.assertEqual(result.returncode, 2)
                self.assertIn(task["id"], result.stderr)
                self.assertEqual(self.page.read_bytes(), before)
                result = self.update({"tasks": [{"id": task["id"], "status": "완료"},
                                                {"id": "DONE", "status": "완료"}]})
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.data()["stage"], "완료")

    def test_todo_starts_as_none_and_is_reported(self):
        self.cli("init", str(self.page))
        self.assertEqual(self.data()["todo"], "없음")
        result = self.update({"todo": "커밋·push 여부 결정"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.data()["todo"], "커밋·push 여부 결정")
        self.assertEqual(json.loads(self.cli("status", str(self.page)).stdout)["todo"], "커밋·push 여부 결정")

    def test_task_times_are_stamped_when_the_status_changes(self):
        self.cli("init", str(self.page))
        self.update({"tasks": [{"id": "A"}]})
        self.assertFalse({"started", "finished"} & set(self.data()["tasks"][0]))
        self.update({"tasks": [{"id": "A", "status": "진행중"}]})
        data = self.data()
        self.assertEqual(data["tasks"][0]["started"], data["updated"])
        old = "2000-01-01T00:00:00+00:00"
        self.edit(lambda d: d["tasks"][0].update(started=old))
        self.update({"tasks": [{"id": "A", "status": "진행중", "note": "재시도"}]})
        self.assertEqual(self.data()["tasks"][0]["started"], old)  # resending 진행중 keeps the start
        self.update({"tasks": [{"id": "A", "status": "완료"}]})
        data = self.data()
        self.assertEqual((data["tasks"][0]["started"], data["tasks"][0]["finished"]), (old, data["updated"]))
        self.edit(lambda d: d["tasks"][0].update(finished=old))
        self.update({"tasks": [{"id": "A", "status": "중단"}]})
        self.assertEqual(self.data()["tasks"][0]["finished"], old)  # 완료 → 중단 keeps the first end time
        self.update({"tasks": [{"id": "A", "status": "진행중"}]})  # reopened by a fix
        task = self.data()["tasks"][0]
        self.assertNotEqual(task["started"], old)
        self.assertNotIn("finished", task)

    def test_stage_detail_and_auto_finish(self):
        self.cli("init", str(self.page))
        self.assertIn("수정 (2라운드)", self.update({"stage": "done"}).stderr)
        result = self.update({"stage": "수정 (1라운드)", "tasks": [{"id": "BE", "status": "완료"}, {"id": "DONE", "lane": "finish", "after": ["BE"]}]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.data()["stage"], "수정 (1라운드)")
        result = self.update({"stage": "완료"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("DONE", result.stderr)
        self.update({"tasks": [{"id": "DONE", "status": "완료"}]})
        self.assertEqual(self.data()["stage"], "완료")
        self.update({"stage": "수정 (3라운드)"})
        self.assertEqual(self.data()["stage"], "수정 (3라운드)")  # only the patch that closes the finish task ends the run

    def test_a_reopened_run_keeps_the_leaders_stage(self):
        self.cli("init", str(self.page))
        self.update({"tasks": [{"id": "BE", "status": "완료"}, {"id": "DONE", "lane": "finish", "status": "완료", "after": ["BE"]}]})
        self.assertEqual(self.data()["stage"], "완료")
        self.update({"stage": "수정 (2라운드)", "tasks": [{"id": "FIX-2", "lane": "fix", "status": "진행중"}]})
        self.update({"tasks": [{"id": "FIX-2", "status": "완료"}]})  # DONE is still 완료, but this patch did not close it
        self.assertEqual(self.data()["stage"], "수정 (2라운드)")

    def test_dropped_finish_task_or_abandoned_run_is_not_finished(self):
        self.cli("init", str(self.page))
        self.update({"stage": "마무리", "tasks": [{"id": "BE", "status": "완료"}, {"id": "DONE", "lane": "finish", "status": "진행중"}]})
        result = self.update({"tasks": [{"id": "DONE", "status": "중단"}]})
        self.assertEqual(json.loads(result.stdout)["tasks"]["중단"], ["DONE"])
        self.assertEqual(self.data()["stage"], "마무리")
        self.update({"stage": "중단", "tasks": [{"id": "DONE", "status": "완료"}]})
        self.assertEqual(self.data()["stage"], "중단")  # an abandoned run stays 중단 even when its finish task closes

    def test_closing_the_last_finish_task_needs_every_task_closed(self):
        self.cli("init", str(self.page))
        self.update({"stage": "마무리", "tasks": [{"id": "BE-9", "status": "대기중"}, {"id": "DONE", "lane": "finish", "status": "중단"},
                                                  {"id": "DONE-2", "lane": "finish", "status": "진행중"},
                                                  {"id": "DONE-3", "lane": "finish", "status": "진행중"}]})
        result = self.update({"tasks": [{"id": "DONE-3", "status": "완료"}]})
        self.assertEqual(result.returncode, 0, result.stderr)  # DONE-2 is still open, so the run simply goes on
        self.assertEqual(self.data()["stage"], "마무리")
        before = self.page.read_bytes()
        result = self.update({"tasks": [{"id": "DONE-2", "status": "완료"}]})
        self.assertEqual(result.returncode, 2)
        self.assertIn("BE-9", result.stderr)
        self.assertEqual(self.page.read_bytes(), before)
        result = self.update({"tasks": [{"id": "BE-9", "status": "완료"}, {"id": "DONE-2", "status": "완료"}]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.data()["stage"], "완료")  # DONE stays 중단; closing DONE-2 ends the run

    def test_dropping_the_last_finish_task_also_ends_the_run(self):
        self.cli("init", str(self.page))
        self.update({"stage": "마무리", "tasks": [{"id": "R1-E", "lane": "review", "status": "대기중"},
                                                  {"id": "CHECK", "lane": "finish", "status": "완료"},
                                                  {"id": "PR", "lane": "finish", "status": "진행중"}]})
        before = self.page.read_bytes()
        result = self.update({"tasks": [{"id": "PR", "status": "중단"}]})  # the user opens the PR; a forgotten card is still open
        self.assertEqual(result.returncode, 2)
        self.assertIn("R1-E", result.stderr)
        self.assertEqual(self.page.read_bytes(), before)
        result = self.update({"tasks": [{"id": "R1-E", "status": "중단"}, {"id": "PR", "status": "중단"}]})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.data()["stage"], "완료")  # CHECK finished the run's work even though PR was dropped

    def test_update_gives_an_older_page_the_current_template(self):
        self.cli("init", str(self.page))
        self.update({"summary": "이전 요약", "tasks": [{"id": "A"}]})
        box = '<div class="box"><b>사용자 할 일</b><span id="todo"></span></div>'
        html = self.page.read_text(encoding="utf-8")
        self.assertIn(box, html)
        self.page.write_text(html.replace(box, ""), encoding="utf-8")  # a page made before the box existed
        result = self.update({"blockers": "없음"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('id="todo"', self.page.read_text(encoding="utf-8"))
        data = self.data()
        self.assertEqual((data["summary"], [t["id"] for t in data["tasks"]]), ("이전 요약", ["A"]))

    def test_reviewer_names_are_checked_on_new_rows_only(self):
        self.cli("init", str(self.page))
        self.assertIn("Karpathy Agent, Ponytail Agent, Impeccable Agent, E2E Agent",
                      self.update({"reviews": [{"round": 1, "reviewer": "Karpathy"}]}).stderr)
        self.edit(lambda d: d.update(reviews=[{"round": 1, "reviewer": "Karpathy", "verdict": "PASS"}]))
        result = self.update({"reviews": [{"round": 2, "reviewer": "Karpathy Agent", "verdict": "PASS"}]})
        self.assertEqual(result.returncode, 0, result.stderr)  # an older page keeps working

    def test_runs_on_declared_python_floor_with_uv(self):
        result = subprocess.run(["uv", "run", "--no-project", "--python", "3.10", "python", str(SCRIPT), "init", str(self.page)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
