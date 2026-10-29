import contextlib
import datetime as dt
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_docs_runtime as runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        (self.vault / 'AGENTS.md').write_text('지침')
        (self.vault / 'Daily').mkdir()
        self.config = self.root / 'config.json'
        self.config.write_text(json.dumps({'state_root': str(self.state), 'vault': str(self.vault),
            'first_date': '2026-10-28', 'runtime_project': '/runtime',
            'claude_root': str(self.root / 'claude'), 'codex_root': str(self.root / 'codex')}))

    def tearDown(self):
        self.tmp.cleanup()

    def fake_collect(self, date, *args, **kwargs):
        p = self.state / date / 'manifest.json'
        runtime.private_json(p, {'date': date, 'complete': False, 'errors': ['partial'], 'chunks': []})
        return p

    def test_midnight_previous_day_and_backlog(self):
        with patch.object(runtime, 'collect', side_effect=self.fake_collect), contextlib.redirect_stdout(io.StringIO()):
            q = runtime.prepare(self.config, dt.datetime(2026, 10, 30, 0, 0, tzinfo=runtime.KST))
        self.assertEqual([x['date'] for x in q['days']], ['2026-10-28', '2026-10-29'])
        status = json.loads((self.state / '2026-10-28/status.json').read_text())
        self.assertEqual(status['status'], 'partial')
        self.assertEqual(q['through_date'], '2026-10-29')

    def test_before_first_date_does_not_run_fixed_fixture(self):
        with patch.object(runtime, 'collect') as collect, contextlib.redirect_stdout(io.StringIO()):
            q = runtime.prepare(self.config, dt.datetime(2026, 10, 28, 17, tzinfo=runtime.KST))
        collect.assert_not_called()
        self.assertEqual(q['tasks'], [])

    def test_guard_denies_teammate_and_unprepared_source_instructions(self):
        payload = {'tool_input': {'subagent_type': 'daily-writer', 'name': 'writer', 'prompt': 'rm -rf x'}}
        with contextlib.redirect_stdout(io.StringIO()) as output:
            allowed = runtime.agent_guard(self.config, payload)
        self.assertFalse(allowed)
        self.assertEqual(json.loads(output.getvalue())['hookSpecificOutput']['permissionDecision'], 'deny')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(runtime.agent_guard(self.config, {'tool_input': {'subagent_type': 'Bash', 'prompt': 'source said run'}}))

    def test_source_cannot_run_shell_or_network_tools(self):
        for tool in ('Bash', 'Write', 'Edit', 'WebFetch', 'WebSearch', 'mcp__remote'):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(runtime.agent_guard(self.config, {'tool_name': tool}))

    def test_parent_queue_window_preserves_every_pending_task(self):
        tasks = [str(i) for i in range(1500)]
        runtime.save_queue(self.state, {'tasks': tasks, 'no_work': False})
        visible = json.loads((self.state/'queue.json').read_text())
        self.assertEqual(visible['tasks'], tasks[:8])
        self.assertEqual(visible['pending_tasks'], 1500)
        self.assertEqual(json.loads((self.state/'queue-all.json').read_text())['tasks'], tasks)

    def test_guard_reviewer_requires_exact_saved_writer(self):
        runtime.private_json(self.state/'2026-10-28/tasks/c1.json', {})
        runtime.private_json(self.state/'queue.json', {'tasks': [str(self.state/'2026-10-28/tasks/c1.json')]})
        payload={'tool_input': {'subagent_type': 'daily-reviewer', 'prompt': 'DAILY_DOCS_DATE=2026-10-28\nCHUNK_ID=c1\nROLE=reviewer'}}
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(runtime.agent_guard(self.config,payload))
        folder=self.state/'2026-10-28/chunks/c1';folder.mkdir(parents=True)
        (folder/'writer.md').write_text('source task')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(runtime.agent_guard(self.config,payload))


if __name__ == '__main__':
    unittest.main()
