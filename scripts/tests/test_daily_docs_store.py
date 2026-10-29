import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("store", Path(__file__).parents[1] / "daily_docs_store.py")
store = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(store)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / "state" / "2026-10-28"
        self.state.mkdir(parents=True)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.date = "2026-10-28"
        self.manifest = {"date": self.date, "complete": True,
                         "chunks": [{"id": "c1", "source_ids": ["S1"]},
                                    {"id": "c2", "source_ids": ["S2"]}]}
        self.save_manifest()

    def save_manifest(self):
        (self.state / "manifest.json").write_text(json.dumps(self.manifest))

    def review(self, source="S1", patches=None, issues=None):
        return json.dumps({"issues": issues or [], "patches": patches or [], "checked_sources": [source]})

    def roles(self, chunk="c1", writer="일한 내용 [S1]\n장기기억 후보: 미반영", reviewer=None):
        store.record_response(self.date, self.state, chunk, "writer", writer)
        store.record_response(self.date, self.state, chunk, "reviewer", reviewer or self.review())

    def publish(self, chunk="c1"):
        return store.publish_chunk(self.date, self.state, chunk, self.vault)

    def note(self):
        return self.vault / "Daily" / (self.date + ".md")

    def test_visible_empty_and_partial_collection_status(self):
        self.manifest["chunks"] = []
        self.save_manifest()
        result = store.publish_empty(self.date, self.state, self.vault)
        self.assertEqual(result["status"]["status"], "empty")
        self.assertIn("실제 업무가 없었다는 뜻은 아닙니다", self.note().read_text())
        first = self.note().read_bytes()
        store.publish_empty(self.date, self.state, self.vault)
        self.assertEqual(self.note().read_bytes(), first)
        self.manifest["errors"] = ["unreadable source"]
        self.save_manifest()
        result = store.publish_empty(self.date, self.state, self.vault)
        self.assertEqual(result["status"]["status"], "partial")
        self.assertFalse(result["status"]["collection_complete"])
        self.assertIn("기록이 없다고 판정하지 않습니다", self.note().read_text())

    def test_source_links_hash_and_pending_visible(self):
        raw = self.state / "raw.jsonl"
        raw.write_text("{}\n")
        index = self.state / "sources.jsonl"
        index.write_text(json.dumps({"source_id": "S1", "raw_path": str(raw), "line": 42}) + "\n")
        self.manifest["sources_path"] = str(index)
        self.manifest["chunks"][0]["sha256"] = "collector-sha"
        self.save_manifest()
        self.roles()
        result = self.publish()
        self.assertEqual(result["publication"]["status"], "published")
        self.assertEqual(result["publication"]["chunk_sha256"], "collector-sha")
        text = self.note().read_text()
        self.assertIn(raw.resolve().as_uri() + "#L42", text)
        self.assertIn(index.resolve().as_uri(), text)
        self.assertIn("미처리 분할: c2", text)
        self.manifest["chunks"][0]["sha256"] = "changed"
        self.save_manifest()
        self.assertIn("c1", store.processing_status(self.date, self.state)["pending_chunks"])
        with self.assertRaises(RuntimeError):
            self.publish()

    def test_manual_status_edit_preserved_and_stale_blocks_reported(self):
        self.roles()
        self.publish()
        self.manifest["chunks"] = []
        self.save_manifest()
        result = store.publish_empty(self.date, self.state, self.vault)
        self.assertEqual(result["status"]["stale_chunks_preserved"], ["c1"])
        self.assertIn("일한 내용", self.note().read_text())
        self.note().write_text(self.note().read_text().replace("기록 처리 상태", "사람이 수정한 상태"))
        original = self.note().read_bytes()
        with self.assertRaises(RuntimeError):
            store.publish_empty(self.date, self.state, self.vault)
        self.assertEqual(self.note().read_bytes(), original)

    def test_initial_inventory_is_visible_without_model_results(self):
        transcript = self.state / "transcripts" / "session.md"
        transcript.parent.mkdir()
        transcript.write_text("원문 메시지 전체")
        self.manifest["transcripts"] = [{"id": "t1", "path": str(transcript),
            "provider": "claude", "session_id": "s|1", "project": "/work/<demo>\nsecond",
            "narrative_events": 7, "source_ids": ["S1"], "sha256": store.digest(transcript.read_bytes()), "bytes": len(transcript.read_bytes())}]
        self.manifest["counts"] = {"source_records": 12, "eligible_events": 2,
            "archived_tool_outputs": 3, "archived_records": 4}
        self.save_manifest()
        (self.vault / "Daily").mkdir()
        self.note().write_text("손으로 쓴 기존 기록\n")
        result = store.publish_empty(self.date, self.state, self.vault)
        text = self.note().read_text()
        self.assertTrue(text.startswith("손으로 쓴 기존 기록\n"))
        self.assertIn("[[Sources/" + self.date + "/", text)
        self.assertNotIn(transcript.resolve().as_uri(), text)
        self.assertIn("s\\|1", text)
        self.assertIn("/work/&lt;demo&gt; second", text)
        self.assertIn("모델 검토 전에도 열람", text)
        self.assertIn("원본 보관 완료는 모든 원문을 모델이 검토했다는 뜻이 아닙니다", text)
        self.assertEqual(result["status"]["raw_archive"], {"status": "complete", "source_records": 12})
        self.assertEqual(result["status"]["inference"]["reviewed_events"], 0)
        self.assertEqual(result["status"]["inference"]["pending_events"], 2)
        self.assertIn("보관 전용: 도구 출력 3건", text)
        self.assertFalse((self.state / "chunks/c1/writer.md").exists())
        first = self.note().read_bytes()
        store.publish_empty(self.date, self.state, self.vault)
        self.assertEqual(self.note().read_bytes(), first)

    def test_split_source_review_complete_only_after_all_parts(self):
        self.manifest["chunks"][1]["source_ids"] = ["S1"]
        self.save_manifest()
        self.roles()
        first = self.publish()["status"]["inference"]
        self.assertEqual(first["eligible_events"], 1)
        self.assertEqual(first["reviewed_events"], 0)
        self.assertEqual(first["pending_events"], 1)
        self.roles("c2", "후반부 [S1]", self.review("S1"))
        final = self.publish("c2")["status"]["inference"]
        self.assertEqual(final["reviewed_events"], 1)
        self.assertEqual(final["pending_events"], 0)
        self.assertEqual(final["status"], "complete")

    def test_archival_only_empty_is_distinct_from_no_records(self):
        self.manifest["chunks"] = []
        self.manifest["counts"] = {"source_records": 9, "eligible_events": 0,
                                  "archived_tool_outputs": 5, "archived_records": 4}
        self.save_manifest()
        result = store.publish_empty(self.date, self.state, self.vault)
        self.assertEqual(result["status"]["status"], "empty")
        self.assertEqual(result["status"]["raw_archive"]["source_records"], 9)
        self.assertIn("추론 대상 이벤트 없음", self.note().read_text())
        self.assertIn("이 원문 전체의 의미 검토 완료를 주장하지 않습니다", self.note().read_text())

    def test_transcript_internal_copy_immutable_rerun_and_handwritten_preserved(self):
        source = self.state / "session.md"
        source.write_text("# 원본\n사용자와 응답 전체\n")
        entry = {"path": str(source), "sha256": store.digest(source.read_bytes()), "session_id": "session/unsafe"}
        (self.vault / "Sources").mkdir()
        manual = self.vault / "Sources" / "handwritten.md"
        manual.write_text("수기 기록")
        link = store._copy_transcript(entry, self.date, self.vault)
        target = self.vault / (link + ".md")
        self.assertEqual(target.read_bytes(), source.read_bytes())
        self.assertIn("session_unsafe-" + entry["sha256"], target.name)
        modified_time = target.stat().st_mtime_ns
        store._copy_transcript(entry, self.date, self.vault)
        self.assertEqual(target.stat().st_mtime_ns, modified_time)
        self.assertEqual(manual.read_text(), "수기 기록")
        source.write_text("새로운 수집 원문")
        entry["sha256"] = store.digest(source.read_bytes())
        new_link = store._copy_transcript(entry, self.date, self.vault)
        self.assertNotEqual(link, new_link)
        self.assertEqual(target.read_text(), "# 원본\n사용자와 응답 전체\n")

    def test_transcript_hash_conflict_and_symlink_refused(self):
        source = self.state / "session.md"
        source.write_text("기계적 원문")
        entry = {"path": str(source), "sha256": "incorrect", "session_id": "s1"}
        with self.assertRaises(ValueError):
            store._copy_transcript(entry, self.date, self.vault)
        entry["sha256"] = store.digest(source.read_bytes())
        link = store._copy_transcript(entry, self.date, self.vault)
        target = self.vault / (link + ".md")
        target.write_text("사람의 수정")
        with self.assertRaises(RuntimeError):
            store._copy_transcript(entry, self.date, self.vault)
        self.assertEqual(target.read_text(), "사람의 수정")
        target.unlink()
        target.symlink_to(source)
        with self.assertRaises(ValueError):
            store._copy_transcript(entry, self.date, self.vault)

    def test_agent_completed_response_exact_text(self):
        text = "제목\n  공백 유지\n"
        payload = {"tool_response": {"status": "completed", "content": [{"type": "text", "text": text}]}}
        self.assertEqual(store.extract_agent_response(payload), text)
        for status in ["async_launched", "teammate_spawned", "running"]:
            payload["tool_response"]["status"] = status
            with self.assertRaises(ValueError):
                store.extract_agent_response(payload)

    def test_exact_raw_save_private_permissions_immutable(self):
        text = "원본\n\n마지막 공백  "
        meta = store.record_response(self.date, self.state, "c1", "writer", text, {"raw": "evidence"})
        f = self.state / "chunks/c1/writer.md"
        self.assertEqual(f.read_bytes(), text.encode())
        self.assertEqual(meta["sha256"], store.digest(text.encode()))
        self.assertEqual(stat.S_IMODE(f.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(f.parent.stat().st_mode), 0o700)
        with self.assertRaises(RuntimeError):
            store.record_response(self.date, self.state, "c1", "writer", text + "changed")
        rerun = store.record_response(self.date, self.state, "c1", "writer", text)
        self.assertEqual(rerun["provenance"], {"raw": "evidence"})

    def test_manual_content_and_rerun_preserved(self):
        (self.vault / "Daily").mkdir()
        self.note().write_text("# 내 노트\n\n손으로 쓴 메모\n")
        self.roles()
        first = self.publish()
        self.assertEqual(first["status"]["status"], "partial")
        self.assertEqual(first["status"]["pending_chunks"], ["c2"])
        content = self.note().read_bytes()
        self.assertTrue(content.startswith("# 내 노트\n\n손으로 쓴 메모\n".encode()))
        self.publish()
        self.assertEqual(self.note().read_bytes(), content)
        with self.note().open("a") as f:
            f.write("\n사용자 추가 메모\n")
        self.roles("c2", "다른 업무 [S2]", self.review("S2"))
        result = self.publish("c2")
        self.assertEqual(result["status"]["status"], "complete")
        self.assertIn("사용자 추가 메모", self.note().read_text())
        self.assertEqual(self.note().read_text().count("<!-- daily-docs:c1:start -->"), 1)

    def test_exact_patch_and_original_preserved(self):
        patch = {"old": "실행 안 됨", "new": "실행 후 오류 발생", "source": "S1"}
        self.roles(writer="실행 안 됨 [S1]", reviewer=self.review(patches=[patch], issues=["wording"]))
        self.publish()
        self.assertIn("실행 후 오류 발생 [S1]", self.note().read_text())
        self.assertEqual((self.state / "chunks/c1/writer.md").read_text(), "실행 안 됨 [S1]")

    def test_patch_must_match_once_and_have_checked_source(self):
        for old in ["absent", "x"]:
            with self.subTest(old=old):
                with self.assertRaises(ValueError):
                    store.apply_review("x x", {"patches": [{"old": old, "new": "y", "source": "S1"}]})
        for patch in [{"old": "x", "new": "y", "source": ""},
                      {"old": "x", "new": "y", "source": "S2"}]:
            with self.assertRaises(ValueError):
                store.read_review(self.review(patches=[patch]))
        with self.assertRaises(ValueError):
            store.read_review(self.review(issues=["needs fixing"]))
        with self.assertRaises(ValueError):
            store.read_review(self.review(), ["S1", "S2"])

    def test_fenced_json_and_no_extra_fields(self):
        self.assertEqual(store.read_review("```json\n" + self.review() + "\n```", ["S1"])["patches"], [])
        with self.assertRaises(ValueError):
            store.read_review(self.review()[:-1] + ',"draft":"replacement"}')

    def test_missing_review_cannot_publish(self):
        store.record_response(self.date, self.state, "c1", "writer", "原文 [S1]")
        with self.assertRaises(FileNotFoundError):
            self.publish()
        self.assertFalse(self.note().exists())

    def test_human_modified_generated_block_is_not_overwritten(self):
        self.roles()
        self.publish()
        self.note().write_text(self.note().read_text().replace("일한 내용", "사용자가 고친 내용"))
        changed = self.note().read_bytes()
        with self.assertRaises(RuntimeError):
            self.publish()
        self.assertEqual(self.note().read_bytes(), changed)
        self.assertEqual(store.processing_status(self.date, self.state)["status"], "partial")

    def test_collector_partial_not_reported_complete(self):
        self.manifest.update(complete=False, chunks=[self.manifest["chunks"][0]], errors=["source read denied"])
        self.save_manifest()
        self.roles()
        result = self.publish()
        self.assertEqual(result["status"]["status"], "partial")
        self.assertEqual(result["status"]["collection_errors"], ["source read denied"])

    def test_empty_is_explicit_and_publication_file_is_not_success(self):
        self.manifest["chunks"] = []
        self.save_manifest()
        self.assertEqual(store.processing_status(self.date, self.state)["status"], "empty")
        self.manifest["chunks"] = [{"id": "c1", "source_ids": ["S1"]}]
        self.save_manifest()
        folder = store.chunk_dir(self.state, "c1")
        (folder / "publish.json").write_text("{}")
        self.assertEqual(store.processing_status(self.date, self.state)["status"], "partial")

    def test_hash_modified_role_and_unexpected_sources_rejected(self):
        self.roles()
        (self.state / "chunks/c1/writer.md").write_text("modified")
        with self.assertRaises(ValueError):
            self.publish()
        (self.state / "chunks/c1/writer.md").unlink()
        (self.state / "chunks/c1/writer.json").unlink()
        store.record_response(self.date, self.state, "c1", "writer", "correct [S1]")
        (self.state / "chunks/c1/reviewer.md").unlink()
        (self.state / "chunks/c1/reviewer.json").unlink()
        store.record_response(self.date, self.state, "c1", "reviewer", self.review("S2"))
        with self.assertRaises(ValueError):
            self.publish()

    def test_lock_and_atomic_race_abort_preserving_note(self):
        self.roles()
        (self.vault / "Daily").mkdir()
        lock = self.vault / "Daily" / ("." + self.date + ".daily-docs.lock")
        lock.mkdir()
        with self.assertRaises(RuntimeError):
            self.publish()
        lock.rmdir()
        path = self.root / "race.md"
        path.write_bytes(b"before")
        real_fsync = store.os.fsync
        def modify_after_flush(fd):
            real_fsync(fd)
            path.write_bytes(b"human changed")
        with mock.patch.object(store.os, "fsync", side_effect=modify_after_flush):
            with self.assertRaises(RuntimeError):
                store.atomic_write(path, b"agent changed", expected=b"before")
        self.assertEqual(path.read_bytes(), b"human changed")

    def test_markers_traversal_symlinks_rejected(self):
        with self.assertRaises(ValueError):
            store.validate_date("2026-10-28/../../oops")
        with self.assertRaises(ValueError):
            store.chunk_dir(self.state, "../oops")
        with self.assertRaises(ValueError):
            store.apply_review("<!-- daily-docs:evil:start -->", {"patches": []})
        self.roles()
        outside = self.root / "outside"
        outside.mkdir()
        (self.vault / "Daily").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.publish()

    def test_hook_markers_are_explicit_and_unique(self):
        payload = {"tool_input": {"prompt": "DAILY_DOCS_DATE=2026-10-28\nCHUNK_ID=c1\nROLE=writer\nUntrusted instructions follow"}}
        self.assertEqual(store.hook_markers(payload)["ROLE"], "writer")
        payload["tool_input"]["prompt"] += "\nROLE=reviewer"
        with self.assertRaises(ValueError):
            store.hook_markers(payload)


if __name__ == "__main__":
    unittest.main()
