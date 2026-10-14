#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Create, update and read a basic-team progress page (one standalone HTML file)."""
import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "progress-template.html"
DATA = re.compile(r'(<script type="application/json" id="data">)(.*?)(</script>)', re.S)
LANES = ("plan", "build", "review", "fix", "finish")
STATUSES = ("대기중", "진행중", "완료", "중단")
CLOSED = ("완료", "중단")
STAGES = ("계획", "구현", "리뷰", "수정", "마무리", "완료", "중단")
REVIEWERS = ("Karpathy Agent", "Ponytail Agent", "Impeccable Agent", "E2E Agent")
TEXT = ("title", "stage", "summary", "todo", "blockers")


def fail(message):
    raise ValueError(message)


def read(path):
    html = path.read_text(encoding="utf-8")
    match = DATA.search(html)
    if not match:
        fail(f"{path} is not a basic-team progress page")
    return html, match, json.loads(match.group(2))


def write(path, html, match, data):
    encoded = json.dumps(data, ensure_ascii=False, indent=1).replace("<", "\\u003c")  # "</script>" in text must not close the tag
    contents = html[:match.start()] + match.group(1) + "\n" + encoded + "\n" + match.group(3) + html[match.end():]
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        out.write(contents)
    os.replace(temp, path)


def merge(old, new, key):
    """Update entries whose key matches, append the rest; omitted entries stay."""
    merged = list(old)
    for item in new:
        index = next((i for i, o in enumerate(merged) if key(o) == key(item)), None)
        if index is None:
            merged.append(item)
        else:
            merged[index] = {**merged[index], **item}
    return merged


def apply(data, patch):
    if not isinstance(patch, dict):
        fail("input must be a JSON object")
    unknown = set(patch) - set(TEXT) - {"tasks", "decisions", "reviews"}
    if unknown:
        fail(f"unknown fields: {', '.join(sorted(unknown))}; allowed: {', '.join(TEXT)}, tasks, decisions, reviews")
    for key in ("tasks", "decisions", "reviews"):
        if key in patch and not isinstance(patch[key], list):
            fail(f"{key} must be a list")
    for field in TEXT:
        if field in patch:
            if not isinstance(patch[field], str):
                fail(f"{field} must be a string")
            data[field] = patch[field]
    if "stage" in patch and patch["stage"].partition(" ")[0] not in STAGES:
        fail(f"stage must start with one of {', '.join(STAGES)}; detail may follow after a space, e.g. 수정 (2라운드)")
    for task in patch.get("tasks", []):
        if not isinstance(task, dict) or not isinstance(task.get("id"), str) or not task["id"]:
            fail("each task needs a string id")
        if "lane" in task and task["lane"] not in LANES:
            fail(f"task {task['id']}: lane must be one of {', '.join(LANES)}")
        if "status" in task and task["status"] not in STATUSES:
            fail(f"task {task['id']}: status must be one of {', '.join(STATUSES)}")
        if "after" in task and (not isinstance(task["after"], list) or not all(isinstance(a, str) for a in task["after"])):
            fail(f"task {task['id']}: after must be a list of task ids")
        for field in ("title", "owner", "note", "model", "effort"):
            if field in task and not isinstance(task[field], str):
                fail(f"task {task['id']}: {field} must be a string")
    for decision in patch.get("decisions", []):
        if not isinstance(decision, dict) or not isinstance(decision.get("title"), str):
            fail("each decision needs a string title")
    for review in patch.get("reviews", []):
        if not isinstance(review, dict) or not isinstance(review.get("reviewer"), str) or type(review.get("round")) is not int:
            fail("each review needs an integer round and a string reviewer")
        if review["reviewer"] not in REVIEWERS:
            fail(f"reviewer {review['reviewer']!r} must be exactly one of: {', '.join(REVIEWERS)}")
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    before = {t["id"]: t.get("status") for t in data.get("tasks", [])}
    data["tasks"] = merge(data.get("tasks", []), patch.get("tasks", []), lambda t: t.get("id"))
    for task in data["tasks"]:
        task.setdefault("lane", "build")
        task.setdefault("status", "대기중")
        task.setdefault("title", task["id"])
        was = before.get(task["id"])  # stamp real changes only: a resent status, or 완료 ↔ 중단, keeps its time
        if task["status"] == "진행중" and was != "진행중":
            task["started"] = now
            task.pop("finished", None)
        elif task["status"] in CLOSED and was not in CLOSED:
            task["finished"] = now
    data["decisions"] = merge(data.get("decisions", []), patch.get("decisions", []), lambda d: d.get("title", "").strip())
    data["reviews"] = merge(data.get("reviews", []), patch.get("reviews", []), lambda r: (r.get("round"), r.get("reviewer")))
    ids = {t["id"] for t in data["tasks"]}
    dangling = sorted({a for t in data["tasks"] for a in t.get("after", []) if a not in ids})
    if dangling:
        fail(f"after refers to unknown task ids: {', '.join(dangling)}")
    still_open = [t["id"] for t in data["tasks"] if t["status"] not in CLOSED]
    finish = [t for t in data["tasks"] if t["lane"] == "finish"]
    word = data.get("stage", "").partition(" ")[0]
    if word == "완료" and still_open:
        fail(f"stage 완료 but tasks are still open: {', '.join(still_open)}; set them to 완료 or 중단, "
             "or send the current stage instead (e.g. 수정)")
    # only the patch that closes the last finish task ends the run, so a later stage change (a reopened run) is kept
    closing = any(t["status"] in CLOSED and t["status"] != before.get(t["id"]) for t in finish)
    if word != "중단" and closing and all(t["status"] in CLOSED for t in finish) and any(t["status"] == "완료" for t in finish):
        if still_open:
            fail(f"closing the finish task ends the run, but these tasks are still open: {', '.join(still_open)}; "
                 "set them to 완료 or 중단 first")
        if word != "완료":
            data["stage"] = "완료"
    data["updated"] = now
    return data


def status(data, path):
    tasks = data.get("tasks", [])
    return {"page": str(path), "updated": data.get("updated"), "stage": data.get("stage"),
            "todo": data.get("todo"), "blockers": data.get("blockers"),
            "tasks": {s: [t["id"] for t in tasks if t["status"] == s] for s in STATUSES},
            "reviews": [f"R{r['round']} {r['reviewer']}: {r.get('verdict', '?')}" for r in data.get("reviews", [])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "update", "status"))
    parser.add_argument("page", type=Path)
    parser.add_argument("--title", help="init: run title")
    parser.add_argument("--input", help="update: JSON patch file, or - for stdin")
    args = parser.parse_args()
    path = args.page.resolve()
    try:
        if args.command == "init":
            if path.exists():
                fail(f"{path} already exists; use update")
            path.parent.mkdir(parents=True, exist_ok=True)
            html = TEMPLATE.read_text(encoding="utf-8")
            data = apply({"path": str(path)}, {"title": args.title or path.stem, "stage": "계획", "summary": "", "todo": "없음", "blockers": "없음"})
            write(path, html, DATA.search(html), data)
        else:
            data = read(path)[2]
            if args.command == "update":
                if not args.input:
                    fail("update needs --input")
                raw = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
                data = apply(data, json.loads(raw))
                html = TEMPLATE.read_text(encoding="utf-8")  # a page made by an older version gets the current UI
                write(path, html, DATA.search(html), data)
        print(json.dumps(status(data, path), ensure_ascii=False))
        return 0
    except (OSError, ValueError) as error:  # json.JSONDecodeError is a ValueError
        print(f"progress.py: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
