import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import daily_docs_claude as harness


class ClaudeHarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        (self.vault / 'AGENTS.md').write_text('실제 Vault 규칙')
        self.skill = self.root / 'SKILL.md'
        self.skill.write_text('실제 스킬 지침')
        self.cfg = {'vault': str(self.vault), 'state_root': str(self.root / 'state'),
                    'skill_path': str(self.skill)}
        self.response = self.root / 'responses/final.json'
        self.value = {'bullets': [{'text': '원인을 확인했다.', 'sources': ['claude-one']}]}
        self.schema = {'type': 'object', 'required': ['bullets'], 'additionalProperties': False,
                       'properties': {'bullets': {'type': 'array', 'maxItems': 6, 'items': {
                           'type': 'object', 'required': ['text', 'sources'], 'additionalProperties': False,
                           'properties': {'text': {'type': 'string', 'maxLength': 1000},
                                          'sources': {'type': 'array', 'minItems': 1,
                                                      'items': {'type': 'string'}}}}}}}

    def tearDown(self):
        self.tmp.cleanup()

    def final(self, value=None, **changes):
        envelope = {'type': 'result', 'subtype': 'success', 'is_error': False,
                    'structured_output': self.value if value is None else value}
        envelope.update(changes)
        return subprocess.CompletedProcess(['claude'], 0, json.dumps(envelope), '')

    def call(self, **kwargs):
        return harness.model_json(self.cfg, '원문 데이터', kwargs.pop('effort', 'medium'),
                                  self.schema, kwargs.pop('response_path', self.response), **kwargs)

    def test_fresh_process_receives_live_skill_and_vault_without_resume(self):
        seen = []
        def execute(command, **kwargs):
            settings = json.loads(Path(command[command.index('--settings') + 1]).read_text())
            self.assertEqual(settings['hooks'], {})
            self.assertEqual(settings['enabledPlugins'], {})
            self.assertEqual(settings['env']['ANTHROPIC_BASE_URL'], 'http://127.0.0.1:11434')
            seen.append((command, kwargs))
            return self.final()
        with patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                patch.object(harness.subprocess, 'run', side_effect=execute):
            self.assertEqual(self.call(), self.value)
            self.skill.write_text('수정된 스킬 지침')
            (self.vault / 'AGENTS.md').write_text('수정된 Vault 규칙')
            self.call(effort='xhigh')
        first, second = seen[0][0], seen[1][0]
        self.assertIn('실제 스킬 지침', first[first.index('--system-prompt') + 1])
        self.assertIn('실제 Vault 규칙', first[first.index('--system-prompt') + 1])
        self.assertIn('수정된 스킬 지침', second[second.index('--system-prompt') + 1])
        self.assertIn('수정된 Vault 규칙', second[second.index('--system-prompt') + 1])
        for command, kwargs in seen:
            for required in ('--bare', '--strict-mcp-config', '--no-session-persistence'):
                self.assertIn(required, command)
            self.assertEqual(command[command.index('--tools') + 1], '')
            self.assertEqual(command[command.index('--setting-sources') + 1], '')
            self.assertNotIn('--resume', command)
            self.assertNotIn('--continue', command)
            self.assertNotIn('--fallback-model', command)
            self.assertNotIn('timeout', kwargs)
            self.assertNotIn('shell', kwargs)
        self.assertNotEqual(seen[0][1]['cwd'], seen[1][1]['cwd'])
        self.assertEqual(second[second.index('--effort') + 1], 'xhigh')
        record = json.loads(self.response.read_text())
        self.assertEqual(record['status'], 'completed')
        self.assertEqual(record['skill_sha256'], harness.digest(self.skill.read_bytes()))
        self.assertEqual(record['vault_rules_sha256'], harness.digest((self.vault / 'AGENTS.md').read_bytes()))
        self.assertEqual(self.response.stat().st_mode & 0o777, 0o600)

    def test_inherited_cloud_auth_proxies_and_provider_flags_are_removed(self):
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'private-cloud-key', 'ANTHROPIC_AUTH_TOKEN': 'private-token',
                'CLAUDE_CODE_USE_BEDROCK': '1', 'CLAUDE_CODE_USE_VERTEX': '1', 'HTTPS_PROXY': 'https://proxy',
                'ANTHROPIC_BASE_URL': 'https://cloud.test', 'CLAUDECODE': '1'}), \
                patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                patch.object(harness.subprocess, 'run', return_value=self.final()) as run:
            self.call()
        env = run.call_args.kwargs['env']
        self.assertEqual(env['ANTHROPIC_API_KEY'], 'ollama')
        self.assertEqual(env['ANTHROPIC_AUTH_TOKEN'], 'ollama')
        self.assertEqual(env['ANTHROPIC_BASE_URL'], 'http://127.0.0.1:11434')
        self.assertEqual(env['CLAUDE_CODE_MAX_OUTPUT_TOKENS'], '8192')
        for forbidden in ('CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'HTTPS_PROXY', 'CLAUDECODE'):
            self.assertNotIn(forbidden, env)
        self.assertNotIn('private-cloud-key', self.response.read_text())

    def test_prompt_uses_stdin_without_shell_interpolation(self):
        prompt = 'quoted `danger` $(danger)\n원문'
        with patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                patch.object(harness.subprocess, 'run', return_value=self.final()) as run:
            harness.model_json(self.cfg, prompt, 'medium', self.schema, self.response)
        self.assertEqual(run.call_args.kwargs['input'], prompt)
        self.assertNotIn(prompt, run.call_args.args[0])

    def test_instruction_snapshot_is_exact_private_and_refuses_tampering_or_symlink(self):
        with patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                patch.object(harness.subprocess, 'run', return_value=self.final()) as run:
            self.call()
            command = run.call_args.args[0]
            exact = command[command.index('--system-prompt') + 1].encode()
            record = json.loads(self.response.read_text())
            snapshot = Path(record['system_prompt_path'])
            self.assertEqual(snapshot.read_bytes(), exact)
            self.assertEqual(snapshot.stat().st_mode & 0o777, 0o600)
            self.assertEqual(record['system_prompt_sha256'], harness.digest(exact))
            self.skill.write_text('지침이 나중에 변경됨')
            self.call()
            self.assertEqual(snapshot.read_bytes(), exact)
            self.assertNotEqual(json.loads(self.response.read_text())['system_prompt_path'], str(snapshot))
            self.skill.write_text('실제 스킬 지침')
            for mode in ('modified', 'symlink'):
                with self.subTest(mode=mode):
                    snapshot.unlink()
                    if mode == 'modified':
                        snapshot.write_bytes(b'changed')
                    else:
                        snapshot.symlink_to(self.skill)
                    before = run.call_count
                    with self.assertRaisesRegex(ValueError, 'snapshot'):
                        self.call()
                    self.assertEqual(run.call_count, before)

    def test_result_json_string_is_accepted(self):
        envelope = {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': json.dumps(self.value)}
        with patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                patch.object(harness.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(envelope), '')):
            self.assertEqual(self.call(), self.value)

    def test_nonzero_exit_preserves_stdout_stderr_and_failure(self):
        with patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                patch.object(harness.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, 'partial output', 'connection failed')):
            with self.assertRaisesRegex(RuntimeError, 'code 1'):
                self.call()
        record = json.loads(self.response.read_text())
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['raw_stdout'], 'partial output')
        self.assertEqual(record['raw_stderr'], 'connection failed')

    def test_spawn_error_preserves_failure_receipt(self):
        with patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                patch.object(harness.subprocess, 'run', side_effect=OSError('spawn failed')):
            with self.assertRaisesRegex(OSError, 'spawn failed'):
                self.call()
        self.assertEqual(json.loads(self.response.read_text())['status'], 'failed')

    def test_incomplete_or_invalid_json_never_counts_as_success(self):
        results = [self.final(subtype='error_max_turns'), self.final(is_error=True),
                   self.final(value={'other': []}), self.final(value={'bullets': [{'text': 2, 'sources': []}]}),
                   subprocess.CompletedProcess([], 0, 'not JSON', '')]
        for result in results:
            with self.subTest(result=result.stdout), patch.object(harness.shutil, 'which', return_value='/bin/claude'), \
                    patch.object(harness.subprocess, 'run', return_value=result):
                with self.assertRaises(ValueError):
                    self.call()
                self.assertEqual(json.loads(self.response.read_text())['status'], 'failed')

    def test_remote_endpoint_and_model_rejected_before_files_or_process(self):
        for cfg in ({'ollama_url': 'https://remote.test'}, {'model': 'remote:cloud'},
                    {'ollama_url': 'http://127.0.0.1:11434/redirect'}, {'ollama_url': 'http://user@localhost:11434'}):
            with self.subTest(cfg=cfg), patch.object(harness.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    harness.model_json(cfg, 'test', 'medium', self.schema)
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
