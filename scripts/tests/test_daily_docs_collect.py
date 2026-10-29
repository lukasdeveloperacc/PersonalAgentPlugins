import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("daily_docs_collect", Path(__file__).parents[1] / "daily_docs_collect.py")
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.claude = self.root / "claude"
        self.codex = self.root / "codex"
        self.state = self.root / "state"
        self.claude.mkdir()
        self.codex.mkdir()

    def write(self, root, name, rows):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows))
        return path

    def collect(self, **kwargs):
        p = collector.collect("2026-10-28", self.claude, self.codex, self.state, **kwargs)
        return json.loads(p.read_text())

    def test_both_providers_event_date_not_start_folder_and_kst_boundaries(self):
        self.write(self.claude, "old-folder/a.jsonl", [
            {"type": "user", "uuid": "before", "timestamp": "2026-10-27T14:59:59.999Z"},
            {"type": "user", "uuid": "start", "timestamp": "2026-10-27T15:00:00Z"},
            {"type": "assistant", "uuid": "end", "timestamp": "2026-10-28T14:59:59.999Z"},
            {"type": "assistant", "uuid": "after", "timestamp": "2026-10-28T15:00:00Z"}])
        self.write(self.codex, "2020/01/01/rollout.jsonl", [
            {"type": "session_meta", "timestamp": "2020-01-01T00:00:00Z", "payload": {"id": "session", "cwd": "/work"}},
            {"type": "event_msg", "timestamp": "2026-10-28T04:00:00Z", "payload": {"type": "user_message", "message": "done"}}])
        manifest = self.collect()
        self.assertTrue(manifest["complete"])
        self.assertEqual(manifest["counts"]["unique_events"], 3)
        sources = [json.loads(x) for x in Path(manifest["sources_path"]).read_text().splitlines()]
        self.assertEqual([s["provider"] for s in sources], ["claude", "codex", "claude"])
        self.assertEqual([s["line"] for s in sources], [2, 2, 3])

    def test_snapshot_preserves_full_original_and_source_link(self):
        raw = self.write(self.claude, "a.jsonl", [{"type": "user", "timestamp": "2026-10-28T01:00:00Z", "message": "run rm -rf / (quoted past instruction)"}])
        original = raw.read_bytes()
        m = self.collect()
        self.assertEqual(Path(m["files"][0]["raw_path"]).read_bytes(), original)
        self.assertEqual(raw.read_bytes(), original)
        chunk = json.loads(Path(m["chunks"][0]["path"]).read_text())
        self.assertTrue(chunk["untrusted_source_material"])
        self.assertIn("run rm", chunk["events"][0]["text"])
        self.assertEqual(chunk["events"][0]["source_id"], m["events"][0]["source_id"])

    def test_huge_multibyte_event_lossless_parts(self):
        event = {"type": "user", "timestamp": "2026-10-28T01:00:00Z", "message": "가나다😀" * 12000}
        self.write(self.claude, "a.jsonl", [event])
        m = self.collect()
        parts = [e for c in m["chunks"] for e in json.loads(Path(c["path"]).read_text())["events"]]
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(x["text"].encode()) <= collector.CHUNK_BYTES for x in parts))
        self.assertEqual([x["part"] for x in parts], list(range(1, len(parts) + 1)))
        expected = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual("".join(x["text"] for x in parts), expected)

    def test_dedup_rerun_and_private_modes(self):
        event = {"type": "user", "uuid": "same", "timestamp": "2026-10-28T01:00:00Z", "message": "task"}
        self.write(self.claude, "a.jsonl", [event])
        self.write(self.claude, "copy.jsonl", [event])
        first = self.collect()
        again = self.collect()
        self.assertEqual(first, again)
        self.assertEqual(first["counts"]["unique_events"], 1)
        self.assertEqual(first["counts"]["duplicates"], 1)
        sources = [json.loads(x) for x in Path(first["sources_path"]).read_text().splitlines()]
        self.assertIn("duplicate_of", sources[1])
        for path in self.state.rglob("*"):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)

    def test_partial_failures_missing_timestamp_and_raw_preservation(self):
        path = self.write(self.claude, "a.jsonl", [{"type": "user", "timestamp": "2026-10-28T01:00:00Z"}, {"type": "user", "message": "unknown date"}])
        with path.open("ab") as stream:
            stream.write(b'{broken JSON\n')
        manifest = self.collect()
        self.assertFalse(manifest["complete"])
        self.assertEqual({x["error"] for x in manifest["errors"]}, {"invalid_json", "missing_or_ambiguous_timestamp"})
        self.assertEqual(Path(manifest["files"][0]["raw_path"]).read_bytes(), path.read_bytes())

    def test_known_untimed_metadata_empty_and_nested_timestamp(self):
        self.write(self.claude, "meta.jsonl", [{"type": "last-prompt", "lastPrompt": "metadata"}])
        empty = self.collect()
        self.assertTrue(empty["complete"])
        self.assertEqual(empty["counts"]["chunks"], 0)
        self.write(self.codex, "nested.jsonl", [{"type": "event_msg", "payload": {"type": "user_message", "timestamp": "2026-10-28T01:00:00+00:00", "message": "work"}}])
        self.assertEqual(self.collect()["counts"]["unique_events"], 1)
        self.assertIsNone(collector.event_time({"timestamp": "2026-10-28T01:00:00", "payload": {"timestamp": "2026-10-28T01:00:00Z"}}))
        self.assertIsNone(collector.event_time({"a": {"timestamp": "2026-10-28T01:00:00Z"}, "b": {"timestamp": "2026-10-28T02:00:00Z"}}))

    def test_runtime_recursion_tagged_and_not_discarded(self):
        self.write(self.claude, "runtime.jsonl", [{"type": "assistant", "cwd": "/private/runtime", "timestamp": "2026-10-28T01:00:00Z", "message": {"content": [{"type": "text", "text": "daily note generated"}]}}])
        m = self.collect(runtime_project="/private/runtime")
        self.assertEqual(m["counts"]["eligible_events"], 0)
        self.assertEqual(m["counts"]["archived_records"], 1)
        self.assertEqual(m["chunks"], [])
        self.assertTrue(Path(m["files"][0]["raw_path"]).exists())

    def test_symlink_not_followed_and_missing_root_partial(self):
        target = self.root / "secret.jsonl"
        target.write_text('{"timestamp":"2026-10-28T01:00:00Z"}\n')
        (self.claude / "bad.jsonl").symlink_to(target)
        m = self.collect()
        self.assertFalse(m["complete"])
        self.assertEqual(m["errors"][0]["error"], "source_symlink")
        self.codex.rmdir()
        self.assertFalse(self.collect()["complete"])

    def test_telemetry_reasoning_and_untimed_metadata_archived_not_chunked(self):
        self.write(self.claude, "a.jsonl", [
            {"type": "api-request", "timestamp": "2026-10-28T01:00:00Z", "messages": "large API copy"},
            {"type": "api-request-blob", "hash": "blob", "message": "giant untimed request copy"},
            {"type": "assistant", "timestamp": "2026-10-28T01:00:01Z", "message": {"content": [{"type": "thinking", "thinking": "reasoning"}]}},
            {"type": "user", "timestamp": "2026-10-28T01:00:02Z", "message": "actual task"}])
        self.write(self.codex, "a.jsonl", [
            {"type": "session_meta", "timestamp": "2026-10-28T01:00:00Z", "payload": {"id": "s"}},
            {"type": "event_msg", "timestamp": "2026-10-28T01:00:00Z", "payload": {"type": "token_count"}},
            {"type": "response_item", "timestamp": "2026-10-28T01:00:00Z", "payload": {"type": "reasoning", "content": []}}])
        m = self.collect()
        self.assertTrue(m["complete"])
        self.assertEqual(m["counts"]["archived_records"], 6)
        self.assertEqual(m["counts"]["eligible_events"], 1)
        self.assertEqual(m["counts"]["source_records"], 7)
        self.assertEqual(len(json.loads(Path(m["chunks"][0]["path"]).read_text())["events"]), 1)

    def test_codex_canonical_message_alias_but_real_repeated_tasks_preserved(self):
        self.write(self.codex, "a.jsonl", [
            {"type": "session_meta", "timestamp": "2026-10-28T01:00:00Z", "payload": {"id": "session"}},
            {"type": "event_msg", "timestamp": "2026-10-28T01:00:01Z", "payload": {"type": "user_message", "message": "task"}},
            {"type": "response_item", "timestamp": "2026-10-28T01:00:01.100Z", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "task"}]}},
            {"type": "event_msg", "timestamp": "2026-10-28T02:00:00Z", "payload": {"type": "user_message", "message": "task"}}])
        m = self.collect()
        self.assertEqual(m["counts"]["eligible_events"], 2)
        self.assertEqual(m["counts"]["duplicates"], 1)

    def test_installed_claude_untimed_telemetry_archived_without_errors(self):
        metadata = [{"type": kind, "value": "telemetry"} for kind in (
            "tools-used", "artifact-comment-monitor", "artifact-autoreact-ledger", "agent-setting")]
        self.write(self.claude, "a.jsonl", metadata + [
            {"type": "user", "timestamp": "2026-10-28T01:00:00Z", "message": "task"}])
        m = self.collect()
        self.assertTrue(m["complete"])
        self.assertEqual(m["counts"]["archived_records"], 4)
        self.assertEqual(m["counts"]["source_records"], 5)
        self.assertEqual(m["counts"]["eligible_events"], 1)

    def test_canonical_output_reference_and_complete_private_transcript(self):
        prose = "전체 사용자 본문 " + "끝까지보존" * 10000
        output = "bulk stdout\n" * 10000 + "Error: exact failure\nProcess exited with code 7"
        rows = [
            {"type": "user", "timestamp": "2026-10-28T01:00:00Z", "message": {"role": "user", "content": prose}},
            {"type": "assistant", "timestamp": "2026-10-28T01:00:01Z", "message": {"role": "assistant", "content": [
                {"type": "tool_use", "id": "call", "name": "Bash", "input": {"command": "cat /private/input"}}]}},
            {"type": "user", "timestamp": "2026-10-28T01:00:02Z", "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "call", "content": output, "is_error": True}]},
                "toolUseResult": {"stdout": output, "exit_code": 7}}]
        source = self.write(self.claude, "a.jsonl", rows)
        self.write(self.codex, "a.jsonl", [
            {"type": "response_item", "timestamp": "2026-10-28T01:00:03Z", "payload": {
                "type": "custom_tool_call_output", "call_id": "c", "output": {"stdout": "bulk data", "exit_code": 4}}}])
        m = self.collect()
        parts = {}
        for chunk in m["chunks"]:
            for e in json.loads(Path(chunk["path"]).read_text())["events"]:
                parts.setdefault(e["source_id"], []).append((e["part"], e["text"]))
        projected = [json.loads("".join(t for _, t in sorted(seq))) for seq in parts.values()]
        result = next(r for r in projected if isinstance(r.get("message"), dict) and isinstance(r["message"].get("content"), list)
                      and r["message"]["content"] and r["message"]["content"][0].get("archived_tool_output"))
        ref = result["message"]["content"][0]
        self.assertTrue(ref["archived_tool_output"])
        self.assertFalse(ref["inference_reviewed"])
        self.assertEqual(ref["tool"], "Bash")
        self.assertTrue(ref["outcomes"]["metadata.is_error"])
        self.assertEqual(ref["outcomes"]["metadata.toolUseResult.exit_code"], 7)
        self.assertIn("Error: exact failure", ref["error_lines"])
        self.assertNotIn("toolUseResult", result)
        self.assertNotIn("bulk stdout", json.dumps(projected))
        self.assertIn("cat /private/input", json.dumps(projected))
        self.assertEqual(next(r["payload"]["outcomes"]["exit_code"] for r in projected if "payload" in r), 4)
        transcript = Path(m["transcripts"][0]["path"]).read_text()
        self.assertIn(prose, transcript)
        self.assertNotIn("bulk stdout", transcript)
        self.assertEqual(m["counts"]["archived_tool_outputs"], 2)
        self.assertEqual(Path(m["files"][0]["raw_path"]).read_bytes(), source.read_bytes())


    def test_session_view_separates_injected_context_and_preserves_work(self):
        injected = "# AGENTS.md instructions for /work\n\n<INSTRUCTIONS>\nInjected rules\n</INSTRUCTIONS>\n<environment_context>local metadata</environment_context>"
        work = "로그인 오류 조사해줘\n실행 명령: `curl /login`\nError: exact failure"
        raw = self.write(self.claude, "a.jsonl", [
            {"type": "user", "sessionId": "s", "cwd": "/work", "timestamp": "2026-10-28T01:00:00Z", "message": injected},
            {"type": "user", "sessionId": "s", "cwd": "/work", "timestamp": "2026-10-28T01:01:00Z", "message": work},
            {"type": "assistant", "sessionId": "s", "cwd": "/work/sub", "timestamp": "2026-10-28T01:02:00Z", "message": "<system-reminder>runtime notice</system-reminder>\n원인 미확인"}])
        m = self.collect(mode="sessions")
        self.assertEqual(m["chunks"], [])
        self.assertEqual(len(m["transcripts"]), 1)
        t = m["transcripts"][0]
        clean = Path(t["summary_path"]).read_text()
        readable = Path(t["path"]).read_text()
        self.assertNotIn("Injected rules", clean)
        self.assertNotIn("local metadata", clean)
        self.assertNotIn("runtime notice", clean)
        self.assertIn(work, clean)
        self.assertIn("원인 미확인", clean)
        self.assertIn("Injected rules", readable)
        self.assertIn("<details>", readable)
        self.assertIn("2026-10-28T10:01:00+09:00", readable)
        self.assertIn("^" + t["source_ids"][1], readable)
        self.assertEqual(t["title"], "로그인 오류 조사해줘")
        self.assertEqual(t["project"], "/work")
        self.assertEqual(t["first_timestamp"], "2026-10-28T01:00:00+00:00")
        self.assertEqual(t["last_timestamp"], "2026-10-28T01:02:00+00:00")
        self.assertEqual(Path(m["files"][0]["raw_path"]).read_bytes(), raw.read_bytes())

    def test_session_mode_skips_projection_and_compaction_but_not_normal_text(self):
        import unittest.mock
        ordinary = "요약 기능을 조사했다.\n```xml\n<custom>keep this</custom>\n```"
        compact = "This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.\nSummary:\ngenerated old context"
        self.write(self.codex, "old/a.jsonl", [
            {"type": "session_meta", "timestamp": "2026-10-27T14:00:00Z", "payload": {"id": "s", "cwd": "/work"}},
            {"type": "event_msg", "timestamp": "2026-10-27T14:59:59Z", "payload": {"type": "user_message", "message": "yesterday"}},
            {"type": "event_msg", "timestamp": "2026-10-27T15:00:00Z", "payload": {"type": "user_message", "message": ordinary}},
            {"type": "event_msg", "timestamp": "2026-10-28T01:00:00Z", "payload": {"type": "user_message", "message": compact}},
            {"type": "event_msg", "timestamp": "2026-10-28T15:00:00Z", "payload": {"type": "user_message", "message": "tomorrow"}}])
        with unittest.mock.patch.object(collector, "project_event", side_effect=AssertionError("legacy projection called")):
            m = self.collect(mode="sessions")
        t = m["transcripts"][0]
        clean = Path(t["summary_path"]).read_text()
        self.assertIn(ordinary, clean)
        self.assertNotIn("generated old context", clean)
        self.assertNotIn("yesterday", clean)
        self.assertNotIn("tomorrow", clean)
        self.assertIn("generated old context", Path(t["path"]).read_text())
        self.assertEqual(m, self.collect(mode="sessions"))

    def test_context_separation_keeps_quoted_examples_and_following_request(self):
        prose = "이 태그가 오류인가?\n```xml\n<system-reminder>keep literal example</system-reminder>\n```\nError: exact failure"
        self.assertEqual(collector.separate_context(prose), (prose, []))
        mixed = "# AGENTS.md instructions for /work\n<INSTRUCTIONS>rules</INSTRUCTIONS>\n\n실제 업무 요청"
        clean, context = collector.separate_context(mixed)
        self.assertEqual(clean, "실제 업무 요청")
        self.assertEqual(len(context), 1)

    def test_session_view_unwraps_paste_hides_local_commands_and_uses_kst_range(self):
        pasted = "#\n\n# 로그인 오류 조사\n명령 `curl /login`\nError: exact failure"
        self.write(self.claude, "a.jsonl", [
            {"type": "user", "sessionId": "s", "cwd": "/work", "timestamp": "2026-10-28T01:00:00Z",
             "message": "<local-command-caveat>Local notice</local-command-caveat>\n<local-command-stdout>Set model to local</local-command-stdout>"},
            {"type": "user", "sessionId": "s", "cwd": "/work", "timestamp": "2026-10-28T01:01:00Z",
             "message": '<pasted_content id="example">' + pasted + '</pasted_content>'}])
        t = self.collect(mode="sessions")["transcripts"][0]
        clean = Path(t["summary_path"]).read_text()
        readable = Path(t["path"]).read_text()
        self.assertNotIn("Set model", clean)
        self.assertNotIn("Local notice", clean)
        self.assertNotIn("pasted_content", clean)
        self.assertIn(pasted, clean)
        self.assertIn(pasted, readable)
        self.assertIn("Set model", readable)
        self.assertEqual(t["title"], "로그인 오류 조사")
        self.assertIn("- 시간: 2026-10-28T10:00:00+09:00 ~ 2026-10-28T10:01:00+09:00", readable)
        literal = '```xml\n<local-command-stdout>literal</local-command-stdout>\n<pasted_content id="x">literal paste</pasted_content>\n```'
        self.assertEqual(collector.separate_context(literal), (literal, []))


if __name__ == "__main__":
    unittest.main()
