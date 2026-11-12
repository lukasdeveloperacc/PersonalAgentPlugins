import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'codex-agents.py'


class AgentInstallTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('codex_agents', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.home = self.root / 'codex'
        for role in self.module.ROLES:
            (self.source / f'basic-{role}.md').write_text(
                f'---\nname: basic-{role}\ndescription: "A {role}"\nmodel: inherit\n---\n\nKeep "quotes", 한글 and \\slashes.\n')

    def install(self):
        self.module.install(self.source, self.home)

    def test_roundtrip_repeat_update_and_remove(self):
        self.install()
        target = self.home / 'agents/basic_backend.toml'
        parsed = tomllib.loads(target.read_text())
        self.assertEqual(set(parsed), {'name', 'description', 'developer_instructions'})
        self.assertEqual(parsed['name'], 'basic_backend')
        self.assertEqual(parsed['developer_instructions'], 'Keep "quotes", 한글 and \\slashes.\n')
        self.install()
        source = self.source / 'basic-backend.md'
        source.write_text(source.read_text() + 'New rule.\n')
        self.install()
        self.assertIn('New rule.', target.read_text())
        other = self.home / 'agents/explorer.toml'
        other.write_text('user agent')
        self.module.remove(self.home)
        self.assertFalse(target.exists())
        self.assertEqual(other.read_text(), 'user agent')
        self.module.remove(self.home)

    def test_unmanaged_and_modified_files_preserved(self):
        target = self.home / 'agents/basic_backend.toml'
        target.parent.mkdir(parents=True)
        target.write_text('user agent')
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.install()
        self.assertEqual(target.read_text(), 'user agent')
        self.assertFalse((target.parent / 'basic_docs.toml').exists())
        target.unlink()
        self.install()
        target.write_text('customized')
        with self.assertRaisesRegex(ValueError, 'conflict'):
            self.install()
        self.module.remove(self.home)
        self.assertEqual(target.read_text(), 'customized')

    def test_symlink_and_corrupt_state_preserved(self):
        self.install()
        target = self.home / 'agents/basic_backend.toml'
        target.unlink()
        outside = self.root / 'outside'
        outside.write_text('keep')
        target.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.install()
        self.module.remove(self.home)
        self.assertTrue(target.is_symlink())
        self.assertEqual(outside.read_text(), 'keep')
        state = self.home / 'agents' / self.module.STATE
        state.write_text('{bad')
        with self.assertRaises(ValueError):
            self.install()
        with self.assertRaises(ValueError):
            self.module.remove(self.home)

    def test_directory_and_state_symlinks_are_not_followed(self):
        outside = self.root / 'outside'
        outside.mkdir()
        self.home.mkdir()
        (self.home / 'agents').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.install()
        self.assertEqual(list(outside.iterdir()), [])
        (self.home / 'agents').unlink()
        (self.home / 'agents').mkdir()
        record = outside / 'record'
        record.write_text('{}')
        (self.home / 'agents' / self.module.STATE).symlink_to(record)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.install()
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.module.remove(self.home)
        self.assertEqual(record.read_text(), '{}')

    def test_invalid_source_prevents_any_install(self):
        source = self.source / 'basic-reviewer.md'
        source.write_text(source.read_text().replace('model: inherit', 'model: other'))
        with self.assertRaises(ValueError):
            self.install()
        self.assertFalse((self.home / 'agents/basic_backend.toml').exists())

    def test_empty_codex_home_uses_user_home(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), 'install', '--source', str(self.source)],
            cwd=self.root, env={**os.environ, 'HOME': str(self.root), 'CODEX_HOME': ''},
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / '.codex/agents/basic_backend.toml').exists())
        self.assertFalse((self.root / 'agents').exists())


if __name__ == '__main__':
    unittest.main()
