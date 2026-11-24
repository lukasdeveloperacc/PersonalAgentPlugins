"""Remember the active Notion Task in this worktree's private Git directory."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from uuid import UUID


def canonical(url):
    parts = urlsplit(url)
    if parts.scheme == "https" and parts.netloc in {"notion.so", "www.notion.so", "app.notion.com", "www.notion.com", "notion.com"}:
        slug = parts.path.rstrip("/").rsplit("/", 1)[-1]
        match = re.search(r"(?:^|-)([0-9a-f]{32}|[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$", slug, re.I)
        if match:
            return "https://www.notion.so/" + UUID(match[1]).hex
    raise ValueError("Expected a Notion page URL with a page ID")


def state_path(cwd):
    git = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=cwd,
                         capture_output=True, text=True, check=True)
    return Path(git.stdout.rstrip("\n")) / "lukas-work-task"


def current(path):
    try:
        return canonical(path.read_text().strip())
    except FileNotFoundError:
        return None


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("remember", "clear"):
        commands.add_parser(name).add_argument("url")
    commands.add_parser("show")
    commands.add_parser("session-start")
    args = parser.parse_args()
    if args.action == "session-start":
        payload = json.load(sys.stdin)
        cwd = payload.get("cwd") if isinstance(payload, dict) else None
        if not isinstance(cwd, str) or not os.path.isabs(cwd):
            return
        url = current(state_path(cwd))
        if url:
            context = f"이 worktree의 work-task 기록: {url}. 관련 업무를 재개할 때 work-task 스킬로 현재 상태를 확인하세요."
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}, ensure_ascii=False))
        return
    path = state_path(None)
    if args.action == "show":
        url = current(path)
        if url:
            print(url)
        return
    url = canonical(args.url)
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        active = current(path)
        if active and active != url:
            raise ValueError(f"Another Task is active: {active}")
        if args.action == "clear":
            if active:
                path.unlink()
        elif not active:
            with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as out:
                out.write(url + "\n")
            os.replace(out.name, path)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        if sys.argv[1:] != ["session-start"]:
            sys.exit(str(exc))
