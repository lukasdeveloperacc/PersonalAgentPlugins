import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_docs_sessions as sessions


class SessionPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        self.state = self.root / 'state'
        self.day = self.state / '2026-10-28'
        self.day.mkdir(parents=True)
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps({'vault': str(self.vault), 'state_root': str(self.state),
            'first_date': '2026-10-28', 'runtime_project': '/runtime',
            'claude_root': '/claude', 'codex_root': '/codex'}))
        self.prose = '## 10:00 · user · [claude-a]\n\n오류 조사\n\n^claude-a\n\n## 10:01 · assistant · [claude-b]\n\n실패 원인 미확인\n\n^claude-b\n'
        self.entry = self.entry_at('s1', self.prose)
        self.manifest = {'date': '2026-10-28', 'complete': True, 'errors': [],
                         'files': [], 'transcripts': [self.entry]}
        (self.day / 'manifest.json').write_text(json.dumps(self.manifest))

    def entry_at(self, name, text):
        p = self.day / (name + '.md')
        p.write_text(text)
        return {'id': name, 'path': str(p), 'summary_path': str(p),
                'session_id': name, 'project': '/work/project', 'provider': 'claude',
                'title': '오류 조사', 'source_ids': ['claude-a', 'claude-b'],
                'first_timestamp': '2026-10-28T01:00:00+00:00',
                'last_timestamp': '2026-10-28T01:01:00+00:00',
                'sha256': sessions.digest(text.encode())}

    def tearDown(self):
        self.tmp.cleanup()

    def response(self, source='claude-a'):
        return {'bullets': [{'text': '오류를 조사했으며 원인은 미확인이다.', 'sources': [source]}]}

    def test_failed_summary_keeps_original_and_readable_daily(self):
        with patch.object(sessions, 'model_json', side_effect=RuntimeError('model unavailable')):
            result = sessions.process_day(self.config, '2026-10-28')
        self.assertFalse(result['complete'])
        self.assertEqual((self.vault / 'Sources/2026-10-28/s1.md').read_text(), self.prose)
        daily = (self.vault / 'Daily/2026-10-28.md').read_text()
        self.assertIn('요약 대기', daily)
        self.assertNotIn('chunk-', daily)

    def test_success_cache_and_source_link(self):
        with patch.object(sessions, 'model_json', return_value=self.response()) as model:
            sessions.process_day(self.config, '2026-10-28', session_id='s1')
            sessions.process_day(self.config, '2026-10-28', session_id='s1')
        self.assertEqual(model.call_count, 1)
        self.assertIn('Sources/2026-10-28/s1#^claude-a',
                      (self.vault / 'Daily/2026-10-28.md').read_text())

    def test_unknown_source_is_not_published(self):
        with patch.object(sessions, 'model_json', return_value=self.response('made-up')):
            result = sessions.process_day(self.config, '2026-10-28', session_id='s1')
        self.assertFalse(result['complete'])
        self.assertNotIn('오류를 조사했으며', (self.vault / 'Daily/2026-10-28.md').read_text())

    def test_long_parts_preserve_all_bytes_and_partial_status(self):
        text = self.prose + ('긴 기록🙂\n' * 6000)
        parts = sessions.split_input(text)
        self.assertEqual(''.join(parts), text)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(p.encode()) <= sessions.PART_BYTES for p in parts))
        self.entry = self.entry_at('s1', text)
        self.manifest['transcripts'] = [self.entry]
        (self.day / 'manifest.json').write_text(json.dumps(self.manifest))
        with patch.object(sessions, 'model_json', side_effect=[self.response(), RuntimeError('bad')] * len(parts)):
            result = sessions.process_day(self.config, '2026-10-28', session_id='s1')
        self.assertFalse(result['complete'])
        self.assertIn('부분 요약', (self.vault / 'Daily/2026-10-28.md').read_text())

    def test_manual_text_preserved_and_generated_edits_refused(self):
        daily = self.vault / 'Daily/2026-10-28.md'
        daily.parent.mkdir()
        daily.write_text('# 2026-10-28 업무 로그\n\n수기 메모 보존\n')
        sessions.publish_day(self.config, '2026-10-28')
        self.assertIn('수기 메모 보존', daily.read_text())
        daily.write_text(daily.read_text().replace('요약 대기', '수기 변경'))
        with self.assertRaisesRegex(RuntimeError, 'modified'):
            sessions.publish_day(self.config, '2026-10-28')

    def test_legacy_migration_checks_receipts_and_preserves_backup(self):
        block = '<!-- daily-docs-status:2026-10-28:start -->\nold status\n<!-- daily-docs-status:2026-10-28:end -->'
        original = '# 2026-10-28 업무 로그\n\nmanual\n' + block + '\n'
        daily = self.vault / 'Daily/2026-10-28.md'
        daily.parent.mkdir()
        daily.write_text(original)
        (self.day / 'status-publication.json').write_text(json.dumps({'block_sha256': sessions.digest(block.encode())}))
        sessions.publish_day(self.config, '2026-10-28')
        self.assertNotIn('old status', daily.read_text())
        self.assertIn('manual', daily.read_text())
        backups = list((self.state / 'migration-backups').glob('*.md'))
        self.assertEqual(backups[0].read_text(), original)

    def test_remote_endpoint_rejected(self):
        with self.assertRaisesRegex(ValueError, 'local'):
            sessions.model_json({'ollama_url': 'https://remote.test'}, 'test', 'medium', sessions.SUMMARY_SCHEMA)

    def test_local_endpoint_cannot_select_cloud_model(self):
        with self.assertRaisesRegex(ValueError, 'local model'):
            sessions.model_json({'model': 'remote:cloud'}, 'test', 'medium', sessions.SUMMARY_SCHEMA)

    def test_model_text_cannot_inject_publication_markers_or_links(self):
        with self.assertRaisesRegex(ValueError, 'reserved'):
            sessions.validate_items({'bullets': [{'text': '<!-- session-log:daily:end -->',
                'sources': ['claude-a']}]}, 'bullets', {'claude-a'})
        text = sessions.safe_line('![image](https://remote.test) <img src="remote">')
        self.assertNotIn('![image]', text)
        self.assertNotIn('<img', text)

    def test_metadata_only_session_does_not_invoke_model(self):
        self.entry = self.entry_at('s1', '# 세션 기록\n\n프로젝트: metadata only\n')
        self.manifest['transcripts'] = [self.entry]
        (self.day / 'manifest.json').write_text(json.dumps(self.manifest))
        with patch.object(sessions, 'model_json') as model:
            sessions.process_day(self.config, '2026-10-28')
        model.assert_not_called()

    def test_long_session_consolidates_to_six_bullets_and_reuses_cache(self):
        text = self.prose + ('긴 기록🙂\n' * 2200)
        self.entry = self.entry_at('s1', text)
        self.manifest['transcripts'] = [self.entry]
        (self.day / 'manifest.json').write_text(json.dumps(self.manifest))
        def answer(cfg, prompt, effort, schema, response_path=None):
            return self.response('claude-b')
        with patch.object(sessions, 'model_json', side_effect=answer) as model:
            result = sessions.process_day(self.config, '2026-10-28', session_id='s1')
            calls = model.call_count
            self.assertGreater(calls, 1)
            sessions.process_day(self.config, '2026-10-28', session_id='s1')
            self.assertEqual(model.call_count, calls)
        self.assertTrue(result['complete'])
        daily = (self.vault / 'Daily/2026-10-28.md').read_text()
        self.assertEqual(daily.count('오류를 조사했으며'), 1)

    def test_memory_failure_keeps_pipeline_incomplete(self):
        def answer(cfg, prompt, effort, schema, response_path=None):
            if effort == 'xhigh':
                raise ValueError('memory failed')
            return self.response()
        with patch.object(sessions, 'model_json', side_effect=answer):
            result = sessions.process_day(self.config, '2026-10-28')
        self.assertTrue(result['summary_complete'])
        self.assertFalse(result['memory_complete'])
        self.assertFalse(result['complete'])

    def test_memory_candidates_retain_evidence_and_manual_text(self):
        memory = self.vault / 'Memory/2026-10-28.md'
        memory.parent.mkdir()
        memory.write_text('# 장기기억\n\n직접 적은 기억\n')
        def answer(cfg, prompt, effort, schema, response_path=None):
            if effort == 'xhigh':
                return {'memories': [{'category': '재사용할 교훈', 'text': '원인을 확인한 뒤 수정한다.',
                                      'sources': ['claude-a']}]}
            return self.response()
        with patch.object(sessions, 'model_json', side_effect=answer):
            result = sessions.process_day(self.config, '2026-10-28')
        self.assertTrue(result['complete'])
        self.assertIn('직접 적은 기억', memory.read_text())
        self.assertIn('Sources/2026-10-28/s1#^claude-a', memory.read_text())

    def test_topic_memory_preserves_manual_text_and_is_idempotent(self):
        topic = self.vault / 'Memory/재사용할 교훈.md'
        topic.parent.mkdir()
        topic.write_text('# 재사용할 교훈\n\n사용자가 직접 적은 교훈\n')
        def answer(cfg, prompt, effort, schema, response_path=None):
            if effort == 'xhigh':
                return {'memories': [{'category': '재사용할 교훈', 'text': '오류의 원인을 먼저 검증한다.',
                                     'sources': ['claude-a']}]}
            return self.response()
        with patch.object(sessions, 'model_json', side_effect=answer) as model:
            sessions.process_day(self.config, '2026-10-28')
            calls = model.call_count
            first = topic.read_text()
            sessions.process_day(self.config, '2026-10-28')
            self.assertEqual(calls, model.call_count)
        self.assertEqual(topic.read_text(), first)
        self.assertIn('사용자가 직접 적은 교훈', first)
        self.assertEqual(first.count('오류의 원인을 먼저 검증한다.'), 1)
        self.assertIn('2026-10-28', first)
        self.assertIn('Sources/2026-10-28/s1#^claude-a', first)

    def test_topic_memory_other_dates_preserved_and_edit_conflicts_refused(self):
        def answer(cfg, prompt, effort, schema, response_path=None):
            return ({'memories': [{'category': '결정', 'text': '이전 판단을 검증하고 선택한다.',
                                  'sources': ['claude-a']}]} if effort == 'xhigh' else self.response())
        with patch.object(sessions, 'model_json', side_effect=answer):
            sessions.process_day(self.config, '2026-10-28')
            next_day = self.state / '2026-10-29'
            next_day.mkdir()
            (next_day / 'manifest.json').write_text(json.dumps(dict(self.manifest, date='2026-10-29')))
            sessions.process_day(self.config, '2026-10-29')
            topic = self.vault / 'Memory/결정.md'
            text = topic.read_text()
            self.assertIn('## 2026-10-28', text)
            self.assertIn('## 2026-10-29', text)
            self.assertEqual(text.count('이전 판단을 검증하고 선택한다.'), 2)
            topic.write_text(text.replace('이전 판단을 검증하고 선택한다.', '직접 수정', 1))
            result = sessions.process_day(self.config, '2026-10-28')
        self.assertFalse(result['memory_complete'])
        self.assertIn('직접 수정', topic.read_text())

    def test_symlinked_sources_parent_is_refused(self):
        elsewhere = self.root / 'elsewhere'
        elsewhere.mkdir()
        (self.vault / 'Sources').symlink_to(elsewhere)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            sessions.publish_day(self.config, '2026-10-28')

    def test_prepare_reuses_complete_historical_session_manifests(self):
        yesterday = '2026-10-29'
        latest = self.state / yesterday
        latest.mkdir()
        (latest / 'manifest.json').write_text(json.dumps(dict(self.manifest, date=yesterday, transcripts=[])))
        def collect(date, *args, **kwargs):
            return self.state / date / 'manifest.json'
        with patch.object(sessions, 'collect', side_effect=collect) as collect_mock:
            sessions.prepare(self.config, now=dt.datetime(2026, 10, 30, tzinfo=sessions.KST))
        self.assertEqual([call.args[0] for call in collect_mock.call_args_list], [yesterday])

    def test_prepare_recollects_incomplete_historical_manifest(self):
        self.manifest['complete'] = False
        (self.day / 'manifest.json').write_text(json.dumps(self.manifest))
        latest = self.state / '2026-10-29'
        latest.mkdir()
        (latest / 'manifest.json').write_text(json.dumps(dict(self.manifest, date='2026-10-29', transcripts=[])))
        with patch.object(sessions, 'collect', side_effect=lambda date, *a, **kw:
                          self.state / date / 'manifest.json') as collect_mock:
            sessions.prepare(self.config, now=dt.datetime(2026, 10, 30, tzinfo=sessions.KST))
        self.assertEqual([call.args[0] for call in collect_mock.call_args_list], ['2026-10-28', '2026-10-29'])

    def test_prepare_conflict_does_not_block_next_day_collection(self):
        self.manifest['complete'] = False
        (self.day / 'manifest.json').write_text(json.dumps(self.manifest))
        latest = self.state / '2026-10-29'
        latest.mkdir()
        (latest / 'manifest.json').write_text(json.dumps(dict(self.manifest, date='2026-10-29', transcripts=[])))
        daily = self.vault / 'Daily/2026-10-28.md'
        daily.parent.mkdir()
        manual = '# 2026-10-28 업무 로그\n<!-- session-log:daily:start -->수기 편집<!-- session-log:daily:end -->'
        daily.write_text(manual)
        with patch.object(sessions, 'collect', side_effect=lambda date, *a, **kw:
                          self.state / date / 'manifest.json') as collect_mock:
            dates = sessions.prepare(self.config, now=dt.datetime(2026, 10, 30, tzinfo=sessions.KST))
        self.assertEqual(dates, ['2026-10-28', '2026-10-29'])
        self.assertEqual([call.args[0] for call in collect_mock.call_args_list], dates)
        self.assertEqual(daily.read_text(), manual)
        self.assertTrue((self.vault / 'Daily/2026-10-29.md').exists())
        self.assertFalse(json.loads((self.day / 'prepare-status.json').read_text())['complete'])

    def test_run_conflict_does_not_block_next_day_processing(self):
        calls = []
        def process(config, date, session_id=None):
            calls.append(date)
            if date == '2026-10-28':
                raise RuntimeError('human edited block')
            return {'date': date, 'complete': True}
        with patch.object(sys, 'argv', ['daily_docs_sessions.py', 'run', '--config', str(self.config)]), \
                patch.object(sessions, 'prepare', return_value=['2026-10-28', '2026-10-29']), \
                patch.object(sessions, 'process_day', side_effect=process):
            result = sessions.main()
        self.assertEqual(calls, ['2026-10-28', '2026-10-29'])
        self.assertEqual(result, 2)
        status = json.loads((self.state / 'pipeline_status.json').read_text())
        self.assertFalse(status['complete'])
        self.assertTrue(status['days'][1]['complete'])


if __name__ == '__main__':
    unittest.main()
