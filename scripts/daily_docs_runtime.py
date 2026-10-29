#!/usr/bin/env python3
"""Deterministic preparation and hook orchestration for the local daily pipeline."""
import argparse
import datetime as dt
import hashlib
import json
import os
import fcntl
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

from daily_docs_collect import collect
from daily_docs_store import (record_response, extract_agent_response, publish_chunk,
                              processing_status, validate_date, validate_chunk, publish_empty, read_review, apply_review)

KST = ZoneInfo('Asia/Seoul')


def private_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o600)


def config_at(path):
    cfg = json.loads(Path(path).read_text())
    root = Path(cfg['state_root']).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root.chmod(0o700)
    return cfg, root


def save_queue(root, queue):
    private_json(root / 'queue-all.json', queue)
    visible = dict(queue, tasks=queue['tasks'][:8], pending_tasks=len(queue['tasks']))
    private_json(root / 'queue.json', visible)


def prepare(config_path, now=None):
    cfg, root = config_at(config_path)
    today = (now or dt.datetime.now(KST)).astimezone(KST).date()
    end = today - dt.timedelta(days=1)
    day = dt.date.fromisoformat(cfg['first_date'])
    # This is run by the actual Claude SessionStart process, proving its Vault TCC path.
    probe = Path(cfg['vault']) / 'Daily' / ('.daily-docs-probe-' + str(os.getpid()))
    try:
        probe.parent.mkdir(exist_ok=True)
        probe.write_bytes(b'daily-docs TCC probe\n')
        if probe.read_bytes() != b'daily-docs TCC probe\n':
            raise OSError('Vault probe readback differs')
    finally:
        if probe.exists():
            probe.unlink()
    private_json(root / 'runtime-access.json', {'ok': True, 'temporary_removed': not probe.exists(),
                 'at': dt.datetime.now(KST).isoformat(), 'pid': os.getpid(), 'ppid': os.getppid()})
    tasks = []
    days = []
    while day <= end:
        date = day.isoformat()
        manifest_path = collect(date, Path(cfg['claude_root']).expanduser(),
                                Path(cfg['codex_root']).expanduser(), root,
                                runtime_project=cfg['runtime_project'])
        manifest = json.loads(manifest_path.read_text())
        # Keep a per-run copy of Vault rules beside private inputs; source is re-read each run.
        rules = Path(cfg['vault']) / 'AGENTS.md'
        copied_rules = root / date / 'vault-AGENTS.md'
        copied_rules.write_bytes(rules.read_bytes())
        copied_rules.chmod(0o600)
        days.append({'date': date, 'manifest': str(manifest_path),
                     'collection_complete': manifest['complete'], 'chunks': len(manifest['chunks'])})
        publish_empty(date, root / date, Path(cfg['vault']))
        verified_status = processing_status(date, root / date)
        for chunk in manifest['chunks']:
            cid = chunk['id']
            chunk_path = Path(chunk['path'])
            if not chunk_path.is_absolute():
                chunk_path = manifest_path.parent / chunk_path
            rendered = root / date / 'chunks' / cid / 'publish.json'
            # Publish validation is responsible for detecting human edits; task skip needs input identity.
            if rendered.exists():
                saved = json.loads(rendered.read_text())
                if (saved.get('chunk_sha256') == chunk['sha256']
                    and cid not in verified_status['pending_chunks']):
                    continue
            task = {'date': date, 'chunk_id': cid, 'input': str(chunk_path),
                    'sources': chunk['source_ids'], 'rules': str(copied_rules),
                    'writer_file': str(root / date / 'chunks' / cid / 'writer.md')}
            task_path = root / date / 'tasks' / (cid + '.json')
            private_json(task_path, task)
            tasks.append(str(task_path))
        day += dt.timedelta(days=1)
    queue = {'prepared_at': dt.datetime.now(KST).isoformat(), 'timezone': 'Asia/Seoul',
             'first_date': cfg['first_date'], 'through_date': end.isoformat(),
             'tasks': tasks, 'days': days, 'vault': cfg['vault'],
             'state_root': str(root), 'no_work': not tasks}
    save_queue(root, queue)
    print(json.dumps({'queue': str(root / 'queue.json'), 'tasks': len(tasks), 'days': days}, ensure_ascii=False))
    return queue


def markers(prompt):
    keys = ('DAILY_DOCS_DATE', 'CHUNK_ID', 'ROLE')
    lines = prompt.splitlines()
    if len(lines) < 3:
        return {}
    result = {}
    for key, line in zip(keys, lines[:3]):
        if not line.startswith(key + '='):
            return {}
        result[key] = line.split('=', 1)[1].strip()
    if any(line.startswith(key + '=') for line in lines[3:] for key in keys):
        return {}
    return result


def agent_guard(config_path, payload):
    cfg, root = config_at(config_path)
    tool = payload.get('tool_name', 'Agent')
    if tool in ('Read', 'Grep', 'Glob'):
        return True
    if tool != 'Agent':
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
              'permissionDecision': 'deny', 'permissionDecisionReason': 'Read-only local pipeline: only Read/Grep/Glob and guarded native Agent are allowed. Scripts own collection and storage.'}}))
        return False
    args = payload.get('tool_input', {})
    mark = markers(args.get('prompt', ''))
    reason = None
    role = args.get('subagent_type')
    if args.get('model') not in (None, 'inherit', 'datewiki-qwen3.8:27b-64k'):
        reason = 'Model overrides must retain the configured local alias.'
    elif args.get('effort') not in (None, 'medium' if role == 'daily-writer' else 'xhigh'):
        reason = 'Keep writer medium and reviewer xhigh.'
    elif role not in ('daily-writer', 'daily-reviewer'):
        reason = 'Only daily-writer and daily-reviewer custom native roles are allowed.'
    elif any(args.get(k) for k in ('name', 'team_name', 'run_in_background', 'isolation')):
        reason = 'Omit name, team_name, run_in_background and isolation; this pipeline requires local synchronous native Agent returns.'
    elif set(mark) != {'DAILY_DOCS_DATE', 'CHUNK_ID', 'ROLE'}:
        reason = 'Agent prompt must begin DAILY_DOCS_DATE=YYYY-MM-DD, CHUNK_ID=<queue id>, ROLE=writer|reviewer on separate lines.'
    elif mark['ROLE'] != role.removeprefix('daily-'):
        reason = 'ROLE must match custom subagent_type.'
    else:
        date, cid = mark['DAILY_DOCS_DATE'], mark['CHUNK_ID']
        try:
            validate_date(date)
            validate_chunk(cid)
        except ValueError:
            reason = 'Invalid date or chunk id.'
        if reason is None:
            task = root / date / 'tasks' / (cid + '.json')
            queue_path = root / 'queue.json'
            queue = json.loads(queue_path.read_text()) if queue_path.exists() else {'tasks': []}
            if not task.exists() or not any(Path(x).resolve() == task.resolve() for x in queue['tasks']):
                reason = 'Task must be present in the current prepared queue.'
            elif role == 'daily-reviewer' and not (root / date / 'chunks' / cid / 'writer.md').exists():
                reason = 'Wait for the writer completed response and its saved writer.md before reviewing.'
    if reason:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse',
                          'permissionDecision': 'deny', 'permissionDecisionReason': reason}}))
        return False
    return True


def post_agent(config_path, payload):
    cfg, root = config_at(config_path)
    mark = markers(payload.get('tool_input', {}).get('prompt', ''))
    if set(mark) != {'DAILY_DOCS_DATE', 'CHUNK_ID', 'ROLE'}:
        raise ValueError('Agent result has no prepared date/chunk/role markers')
    date, cid, role = validate_date(mark['DAILY_DOCS_DATE']), validate_chunk(mark['CHUNK_ID']), mark['ROLE']
    task_path = root / date / 'tasks' / (cid + '.json')
    if not task_path.exists() or role not in ('writer', 'reviewer'):
        raise ValueError('Unknown task or role')
    text = extract_agent_response(payload)
    if role == 'reviewer':
        task = json.loads(task_path.read_text())
        try:
            checked = read_review(text, task['sources'])
            writer = (root / date / 'chunks' / cid / 'writer.md').read_text()
            apply_review(writer, checked)
        except (ValueError, OSError) as exc:
            # Keep the rejected raw answer without locking the accepted role slot against retry.
            private_json(root / date / 'failures' / (cid + '-' + hashlib.sha256(text.encode()).hexdigest() + '.json'),
                         {'error': str(exc), 'raw_text': text, 'hook_payload': payload})
            print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
                  'additionalContext': 'Review format or exact patches failed validation: ' + str(exc) +
                  '. No published result. Retry only the same reviewer with corrected JSON; preserve the writer.'}}))
            return
    record_response(date, root / date, cid, role, text, {'hook_payload': payload,
                    'recorded_at': dt.datetime.now(KST).isoformat()})
    if role == 'reviewer':
        result = publish_chunk(date, root / date, cid, Path(cfg['vault']))
        all_path = root / 'queue-all.json'
        queue = json.loads(all_path.read_text())
        queue['tasks'] = [x for x in queue['tasks'] if Path(x).resolve() != task_path.resolve()]
        queue['no_work'] = not queue['tasks']
        save_queue(root, queue)
        status = result['status']
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
                         'additionalContext': 'Review verified and published: ' + str(result['publication']['target']) +
                         '. Day chunks ' + str(status['published_chunks']) + '/' + str(status['total_chunks']) +
                         '. Read queue.json again for the next bounded task window; pending ' + str(len(queue['tasks']))}}, ensure_ascii=False))
    else:
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
                         'additionalContext': 'Writer raw final saved exactly. Read the existing writer_file for review; do not regenerate or copy the draft.'}}))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['prepare', 'guard', 'post'])
    ap.add_argument('--config', required=True)
    args = ap.parse_args()
    os.umask(0o077)
    if args.command == 'prepare':
        _, root = config_at(args.config)
        # Serialise collectors; never race the same date's private manifest.
        with (root / 'prepare.lock').open('a') as lock:
            os.chmod(lock.name, 0o600)
            fcntl.flock(lock, fcntl.LOCK_EX)
            prepare(args.config)
    elif args.command == 'guard':
        agent_guard(args.config, json.load(sys.stdin))
    else:
        post_agent(args.config, json.load(sys.stdin))


if __name__ == '__main__':
    main()
