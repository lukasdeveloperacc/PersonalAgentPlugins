"""All process boundaries are mocked: no model CLI is launched by these checks."""
import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from runner import run


class RunnerTests(unittest.TestCase):
    def trial(self, host='claude', code=0, timeout=False):
        with tempfile.TemporaryDirectory() as directory:
            proc = Mock(pid=99999, returncode=code)
            if timeout:
                proc.wait.side_effect = [subprocess.TimeoutExpired('fake', 1), None]
            completed = subprocess.CompletedProcess([], 0, stdout='mock-cli', stderr='')
            with patch.dict('os.environ', {'EVAL_HOST': host, 'EVAL_OUT': directory, 'TIMEOUT': '1', 'LEADER_EFFORT': 'max'}), patch('runner.subprocess.run', return_value=completed), patch('runner.subprocess.Popen', return_value=proc) as launch, patch('runner.os.killpg') as stop, contextlib.redirect_stdout(io.StringIO()):
                status = run('haiku' if host == 'claude' else 'gpt-6-luna', 'test')
            folder = next(Path(directory).iterdir())
            manifest = json.loads((folder / 'manifest.json').read_text())
            return status, manifest, launch.call_count, stop.call_count

    def test_codex_preflight_no_live_process(self):
        status, manifest, launches, stops = self.trial('codex')
        self.assertEqual(status, 2)
        self.assertEqual(manifest['stop_reason'], 'capability_blocked')
        self.assertEqual(launches, 0)
        self.assertIsNone(manifest['leader']['invocation'])

    def test_nonzero_exit_preserved(self):
        status, manifest, launches, stops = self.trial(code=7)
        self.assertEqual(status, 7)
        self.assertEqual(manifest['exit_status'], 7)
        self.assertEqual(launches, 1)
        self.assertIn('--effort', manifest['leader']['invocation'])
        self.assertTrue(manifest['source_hashes'])

    def test_timeout_recorded_and_scoped_stop(self):
        status, manifest, launches, stops = self.trial(code=-15, timeout=True)
        self.assertEqual(status, -15)
        self.assertEqual(manifest['stop_reason'], 'timed_out')
        self.assertEqual(stops, 1)


if __name__ == '__main__':
    unittest.main()
