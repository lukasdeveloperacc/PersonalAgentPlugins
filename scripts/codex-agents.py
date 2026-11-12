#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Install this plugin's five Markdown roles as native Codex agents."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import tomllib

ROLES = ('planner', 'frontend', 'backend', 'docs', 'reviewer')
STATE = '.lukas-plugin-agents.json'
NAMES = {f'basic_{role}.toml' for role in ROLES}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def directory(home):
    path = home / 'agents'
    if path.is_symlink():
        raise ValueError(f'agent directory is a symlink: {path}')
    return path


def read_state(path):
    if path.is_symlink():
        raise ValueError(f'agent state is a symlink: {path}')
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    if not isinstance(data, dict) or any(
        name not in NAMES or not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{64}', value)
        for name, value in data.items()
    ):
        raise ValueError(f'invalid agent state: {path}')
    return data


def write(path, data):
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}.')
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def render(source, role):
    text = (source / f'basic-{role}.md').read_text()
    parts = text.split('---\n', 2)
    if len(parts) != 3 or parts[0]:
        raise ValueError(f'invalid frontmatter: basic-{role}.md')
    fields = {}
    for line in parts[1].splitlines():
        key, separator, value = line.partition(': ')
        if not separator or key in fields:
            raise ValueError(f'invalid metadata: basic-{role}.md')
        fields[key] = value
    if set(fields) != {'name', 'description', 'model'} or fields['name'] != f'basic-{role}' or fields['model'] != 'inherit':
        raise ValueError(f'unsupported metadata: basic-{role}.md')
    description = json.loads(fields['description'])
    body = parts[2].lstrip('\n')
    if not isinstance(description, str) or not description.strip() or not body.strip():
        raise ValueError(f'empty description or instructions: basic-{role}.md')
    data = {'name': f'basic_{role}', 'description': description, 'developer_instructions': body}
    output = ''.join(f'{key} = {json.dumps(value, ensure_ascii=False)}\n' for key, value in data.items())
    tomllib.loads(output)
    return output.encode()


def install(source, home):
    path = directory(home)
    old = read_state(path / STATE)
    outputs = {f'basic_{role}.toml': render(source, role) for role in ROLES}
    for name in outputs:
        target = path / name
        if target.is_symlink():
            raise ValueError(f'agent target is a symlink: {target}')
        if target.exists() and (name not in old or digest(target.read_bytes()) != old[name]):
            raise ValueError(f'agent conflict; preserving {target}')
    path.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        write(path / name, data)
        # Keep ownership evidence for each file before replacing the next one.
        old[name] = digest(data)
        write(path / STATE, (json.dumps(old, indent=2) + '\n').encode())


def remove(home):
    path = directory(home)
    old = read_state(path / STATE)
    for name, expected in old.items():
        target = path / name
        if target.is_symlink() or (target.exists() and digest(target.read_bytes()) != expected):
            print(f'Preserved modified agent: {target}', file=sys.stderr)
        elif target.exists():
            target.unlink()
    if old:
        (path / STATE).unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'remove'))
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[1] / 'agents')
    parser.add_argument('--home', type=Path, default=Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex'))
    args = parser.parse_args()
    try:
        if args.action == 'install':
            install(args.source, args.home)
        else:
            remove(args.home)
    except (OSError, ValueError) as error:
        parser.exit(1, f'codex-agents: {error}\n')


if __name__ == '__main__':
    main()
