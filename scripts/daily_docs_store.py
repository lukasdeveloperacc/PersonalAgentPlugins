#!/usr/bin/env python3
"""Preserve local agent responses and publish reviewed daily-log blocks safely."""
import argparse
from contextlib import contextmanager
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_date(value):
    if dt.date.fromisoformat(value).isoformat() != value:
        raise ValueError("date must be YYYY-MM-DD")
    return value


def validate_chunk(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ValueError("invalid chunk ID")
    return value


def private_dir(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("state directory cannot be a symlink")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.stat().st_uid != os.getuid():
        raise ValueError("state directory has a different owner")
    path.chmod(0o700)
    return path


_UNSET = object()


def atomic_write(path, data, expected=_UNSET):
    path = Path(path)
    if path.is_symlink():
        raise ValueError("refusing symlink destination")
    current = path.read_bytes() if path.exists() else None
    if expected is not _UNSET and current != expected:
        raise RuntimeError("destination changed before save")
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Compare again after the temporary file is ready, before replacing.
        if (path.read_bytes() if path.exists() else None) != current:
            raise RuntimeError("destination changed during save")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path, value):
    atomic_write(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())


def extract_agent_response(payload):
    response = payload.get("tool_response", payload)
    if isinstance(response, str):
        response = json.loads(response)
    if isinstance(response, dict) and isinstance(response.get("data"), dict):
        response = response["data"]
    if not isinstance(response, dict) or response.get("status") != "completed":
        raise ValueError("Agent has not returned a completed response")
    content = response.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [block["text"] for block in content
                 if isinstance(block, dict) and block.get("type") == "text"
                 and isinstance(block.get("text"), str)]
        if texts:
            return "\n".join(texts)
    if isinstance(response.get("text"), str):
        return response["text"]
    raise ValueError("completed Agent response has no final text")


def chunk_dir(state_dir, chunk_id):
    state_dir = private_dir(state_dir)
    chunks = private_dir(state_dir / "chunks")
    return private_dir(chunks / validate_chunk(chunk_id))


def record_response(date, state_dir, chunk_id, role, text, provenance=None):
    validate_date(date)
    if role not in ("writer", "reviewer") or not isinstance(text, str) or not text.strip():
        raise ValueError("nonempty writer/reviewer final text is required")
    folder = chunk_dir(state_dir, chunk_id)
    data = text.encode("utf-8")
    path = folder / (role + ".md")
    if path.exists() and path.read_bytes() != data:
        raise RuntimeError("refusing to replace an existing role result")
    metadata_path = folder / (role + ".json")
    if metadata_path.exists():
        existing = json.loads(metadata_path.read_text())
        if not path.exists() or existing.get("sha256") != digest(data) or existing.get("status") != "completed":
            raise RuntimeError("existing role provenance does not match response")
        return existing
    atomic_write(path, data)
    metadata = {"date": date, "chunk_id": chunk_id, "role": role,
                "sha256": digest(data), "bytes": len(data), "status": "completed",
                "provenance": provenance or {},
                "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    write_json(metadata_path, metadata)
    return metadata


def read_review(text, source_ids=None):
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", stripped, re.S)
        if not match:
            raise ValueError("review must be a single JSON object")
        stripped = match[1]
    review = json.loads(stripped)
    if not isinstance(review, dict) or set(review) != {"issues", "patches", "checked_sources"}:
        raise ValueError("review requires only issues, patches, checked_sources")
    if not isinstance(review["issues"], list) or not isinstance(review["patches"], list):
        raise ValueError("issues and patches must be arrays")
    refs = review["checked_sources"]
    if not isinstance(refs, list) or not refs or any(not isinstance(x, str) or not x for x in refs):
        raise ValueError("review must identify checked sources")
    if review["issues"] and not review["patches"]:
        raise ValueError("review has unresolved issues")
    for patch in review["patches"]:
        if not isinstance(patch, dict) or set(patch) != {"old", "new", "source"}:
            raise ValueError("patch requires only old, new, source")
        if any(not isinstance(patch[k], str) for k in patch) or not patch["old"] or not patch["source"].strip():
            raise ValueError("patch requires exact old text and a source")
        if patch["source"] not in refs:
            raise ValueError("patch source was not checked")
    if source_ids is not None and set(refs) != set(source_ids):
        raise ValueError("checked_sources must exactly cover the chunk source IDs")
    return review


parse_review = read_review


def apply_review(writer, review):
    rendered = writer
    for patch in review["patches"]:
        if rendered.count(patch["old"]) != 1:
            raise ValueError("patch old text must occur exactly once")
        rendered = rendered.replace(patch["old"], patch["new"], 1)
    if "<!-- daily-docs" in rendered:
        raise ValueError("model output contains reserved publication markers")
    return rendered


def manifest_chunks(manifest):
    chunks = manifest.get("chunks", [])
    if not isinstance(chunks, list):
        raise ValueError("manifest chunks must be an array")
    return [entry["id"] if isinstance(entry, dict) else entry for entry in chunks]


def processing_status(date, state_dir):
    validate_date(date)
    state_dir = Path(state_dir)
    manifest = json.loads((state_dir / "manifest.json").read_text())
    ids = manifest_chunks(manifest)
    pending = []
    invalid = {}
    checked_source_ids = set()
    pending_source_ids = set()
    all_source_ids = set()
    for chunk_id in ids:
        entry = next((x for x in manifest["chunks"] if isinstance(x, dict) and x["id"] == chunk_id), {})
        all_source_ids.update(entry.get("source_ids", []))
        validate_chunk(chunk_id)
        folder = state_dir / "chunks" / chunk_id
        try:
            meta = json.loads((folder / "publish.json").read_text())
            note = Path(meta["target"]).read_text()
            start = "<!-- daily-docs:" + chunk_id + ":start -->"
            end = "<!-- daily-docs:" + chunk_id + ":end -->"
            if note.count(start) != 1 or note.count(end) != 1:
                raise ValueError("published block is missing or duplicated")
            block = note[note.index(start):note.index(end) + len(end)]
            if digest(block.encode()) != meta["block_sha256"]:
                raise ValueError("published block differs from recorded content")
            writer = _load_role(folder, "writer")
            reviewer = _load_role(folder, "reviewer")
            entry = next((x for x in manifest["chunks"] if isinstance(x, dict) and x["id"] == chunk_id), {})
            if meta.get("status") != "published" or meta.get("chunk_sha256") != entry.get("sha256"):
                raise ValueError("publication does not match the collected chunk")
            review = read_review(reviewer, entry.get("source_ids"))
            if digest(writer.encode()) != meta["writer_sha256"] or digest(reviewer.encode()) != meta["reviewer_sha256"]:
                raise ValueError("published role sources changed")
            if digest(apply_review(writer, review).encode()) != meta["rendered_sha256"]:
                raise ValueError("published patch result changed")
            checked_source_ids.update(entry.get("source_ids", []))
        except (OSError, ValueError, KeyError) as exc:
            pending.append(chunk_id)
            invalid[chunk_id] = str(exc)
            pending_source_ids.update(entry.get("source_ids", []))
    collected = manifest.get("complete") is True and not manifest.get("errors")
    complete = collected and not pending
    status = "empty" if complete and not ids else ("complete" if complete else "partial")
    stale = sorted(path.parent.name for path in (state_dir / "chunks").glob("*/publish.json")
                   if path.parent.name not in ids)
    counts = manifest.get("counts", {})
    inference = {"status": status, "eligible_events": len(all_source_ids),
                 "reviewed_events": len(checked_source_ids - pending_source_ids),
                 "pending_events": len(pending_source_ids),
                 "archived_tool_outputs": counts.get("archived_tool_outputs", 0),
                 "archival_only_records": counts.get("archived_records", 0)}
    return {"date": date, "status": status, "stale_chunks_preserved": stale,
            "raw_archive": {"status": "complete" if collected else "partial",
                            "source_records": counts.get("source_records", 0)},
            "inference": inference,
            "source_counts": manifest.get("counts", {}),
            "collection_complete": collected,
            "total_chunks": len(ids), "pending_chunks": pending,
            "collection_errors": manifest.get("errors", []), "invalid_chunks": invalid,
            "published_chunks": len(ids) - len(pending)}


def _load_role(folder, role):
    data = (folder / (role + ".md")).read_bytes()
    meta = json.loads((folder / (role + ".json")).read_text())
    if meta.get("status") != "completed" or meta.get("sha256") != digest(data):
        raise ValueError(role + " final response is incomplete or modified")
    return data.decode("utf-8")


def _source_links(state_dir, manifest, source_ids):
    index = Path(manifest.get("sources_path", Path(state_dir) / "sources.jsonl")).resolve()
    lines = ["[비공개 원문 인덱스](" + index.as_uri() + ")"]
    sources = {}
    if index.exists():
        for line in index.read_text().splitlines():
            if line.strip():
                source = json.loads(line)
                sources.setdefault(source["source_id"], source)
    for ref in source_ids:
        source = sources.get(ref)
        destination = index.as_uri()
        if source and source.get("raw_path"):
            destination = Path(source["raw_path"]).resolve().as_uri() + "#L" + str(source["line"])
        lines.append("- [" + ref.replace("[", "").replace("]", "") + "](" + destination + ")")
    return "\n".join(lines)


@contextmanager
def _locked_note(date, vault):
    validate_date(date)
    daily = Path(vault).resolve(strict=True) / "Daily"
    if daily.is_symlink():
        raise ValueError("Daily directory cannot be a symlink")
    daily.mkdir(exist_ok=True)
    target = daily / (date + ".md")
    lock = daily / ("." + date + ".daily-docs.lock")
    try:
        lock.mkdir()
    except FileExistsError:
        raise RuntimeError("daily note is locked") from None
    try:
        if target.is_symlink():
            raise ValueError("daily note cannot be a symlink")
        yield target
    finally:
        lock.rmdir()


def _save_block(target, date, block, start, end, prior_path):
    original = target.read_bytes() if target.exists() else None
    existing = (original or b"").decode("utf-8")
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else None
    if existing.count(start) != existing.count(end) or existing.count(start) > 1:
        raise RuntimeError("duplicate or unbalanced generated block markers")
    if start in existing:
        begin = existing.index(start)
        finish = existing.index(end, begin) + len(end)
        old_block = existing[begin:finish]
        if not prior or prior.get("block_sha256") != digest(old_block.encode()):
            raise RuntimeError("generated block was modified outside this pipeline")
        updated = existing[:begin] + block + existing[finish:]
    else:
        if prior:
            raise RuntimeError("previously published block is missing")
        if not existing:
            existing = "# " + date + " 업무 로그\n\n"
        updated = existing + ("" if existing.endswith("\n\n") else "\n\n") + block + "\n"
    if updated.encode() != original:
        atomic_write(target, updated.encode(), expected=original)


def _markdown_cell(value):
    return str(value if value is not None else "미확인").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "\\|").replace("[", "&#91;").replace("]", "&#93;").replace("\n", " ").replace("\r", " ")


def _copy_transcript(entry, date, vault):
    data = Path(entry["path"]).read_bytes()
    sha = digest(data)
    if sha != entry["sha256"]:
        raise ValueError("transcript differs from collected content")
    sources = Path(vault) / "Sources"
    day = sources / validate_date(date)
    for folder in (sources, day):
        if folder.is_symlink():
            raise ValueError("transcript destination cannot be a symlink")
        folder.mkdir(exist_ok=True)
    session = re.sub(r"[^A-Za-z0-9_-]", "_", str(entry["session_id"]))[:80] or "session"
    name = session + "-" + sha + ".md"
    target = day / name
    if target.is_symlink():
        raise ValueError("transcript destination cannot be a symlink")
    if target.exists():
        if target.read_bytes() != data:
            raise RuntimeError("existing Vault transcript conflicts with collected content")
    else:
        atomic_write(target, data, expected=None)
    return "Sources/" + date + "/" + name[:-3]


def _transcript_inventory(manifest, date, vault):
    transcripts = manifest.get("transcripts", [])
    if not transcripts:
        return []
    lines = ["", "### 수집된 세션 · 프로젝트 원문", "",
             "아래 문서는 원본의 사용자·응답 메시지를 시간순으로 옮긴 기록이며 모델 검토 전에도 열람할 수 있습니다. 도구 출력 전체와 내부 기록은 비공개 원문 인덱스에 보존됩니다.", "",
             "| 제공자 | 세션 | 프로젝트 | 대화 이벤트 | 원문 |",
             "| --- | --- | --- | ---: | --- |"]
    for entry in transcripts:
        destination = _copy_transcript(entry, date, vault)
        cells = [_markdown_cell(entry.get(key)) for key in ("provider", "session_id", "project", "narrative_events")]
        lines.append("| " + " | ".join(cells) + " | [[" + destination + "\\|대화 원문]] |")
    return lines


def _publish_status(date, state_dir, target):
    manifest = json.loads((state_dir / "manifest.json").read_text())
    status = processing_status(date, state_dir)
    start = "<!-- daily-docs-status:" + date + ":start -->"
    end = "<!-- daily-docs-status:" + date + ":end -->"
    label = {"partial": "부분 처리", "complete": "처리 완료", "empty": "수집 완료 · 추론 대상 이벤트 없음"}[status["status"]]
    body = ["> 기록 처리 상태: " + label,
            "> 원문 수집: " + ("완료" if status["collection_complete"] else "불완전") +
            " | 분할 처리: " + str(status["published_chunks"]) + "/" + str(status["total_chunks"]) +
            " | 미처리: " + str(len(status["pending_chunks"])) +
            " | 수집 오류: " + str(len(status["collection_errors"])),
            "> 범위: 해당 날짜의 수집된 Codex/Claude 원본 이벤트. 장기기억 후보: 미반영."]
    inference = status["inference"]
    body.extend(["> 원본 보관과 모델 검토는 별도 단계입니다. 원본 보관 완료는 모든 원문을 모델이 검토했다는 뜻이 아닙니다.",
                 "> 모델 검토 범위: 추론 대상 " + str(inference["eligible_events"]) +
                 "건 | 검토·게시 완료 " + str(inference["reviewed_events"]) +
                 "건 | 미완료 " + str(inference["pending_events"]) + "건.",
                 "> 보관 전용: 도구 출력 " + str(inference["archived_tool_outputs"]) +
                 "건, 내부·기타 기록 " + str(inference["archival_only_records"]) +
                 "건. 이 원문 전체의 의미 검토 완료를 주장하지 않습니다."])
    if status["status"] == "empty":
        body.append("> 수집 범위에 추론 대상 이벤트가 없습니다. 실제 업무가 없었다는 뜻은 아닙니다.")
    elif not status["collection_complete"]:
        body.append("> 원문 수집이 불완전하므로 기록이 없다고 판정하지 않습니다.")
    if status["pending_chunks"]:
        body.append("> 미처리 분할: " + ", ".join(status["pending_chunks"]))
    if status["stale_chunks_preserved"]:
        body.append("> 이전 수집의 생성 블록 보존: " + ", ".join(status["stale_chunks_preserved"]))
    if status["source_counts"]:
        body.append("> 수집 수량: " + ", ".join(str(key) + "=" + str(value) for key, value in status["source_counts"].items()))
    body.append(_source_links(state_dir, manifest, []))
    body.extend(_transcript_inventory(manifest, date, target.parent.parent))
    block = start + "\n" + "\n".join(body) + "\n" + end
    prior_path = state_dir / "status-publication.json"
    _save_block(target, date, block, start, end, prior_path)
    write_json(prior_path, {"target": str(target), "block_sha256": digest(block.encode())})
    write_json(state_dir / "status.json", status)
    return status


def publish_empty(date, state_dir, vault):
    """Publish current collection status, including empty or still-pending days."""
    state_dir = private_dir(state_dir)
    with _locked_note(date, vault) as target:
        status = _publish_status(date, state_dir, target)
    return {"target": str(target), "status": status}


def publish_chunk(date, state_dir, chunk_id, vault):
    validate_date(date)
    validate_chunk(chunk_id)
    state_dir = private_dir(state_dir)
    manifest = json.loads((state_dir / "manifest.json").read_text())
    if chunk_id not in manifest_chunks(manifest):
        raise ValueError("chunk is absent from the collection manifest")
    folder = chunk_dir(state_dir, chunk_id)
    writer = _load_role(folder, "writer")
    entry = next((x for x in manifest["chunks"] if isinstance(x, dict) and x["id"] == chunk_id), {})
    reviewer = _load_role(folder, "reviewer")
    review = read_review(reviewer, entry.get("source_ids"))
    rendered = apply_review(writer, review)
    start = "<!-- daily-docs:" + chunk_id + ":start -->"
    end = "<!-- daily-docs:" + chunk_id + ":end -->"
    block = start + "\n" + rendered + "\n\n" + _source_links(state_dir, manifest, entry.get("source_ids", [])) + "\n" + end
    prior_path = folder / "publish.json"
    with _locked_note(date, vault) as target:
        if prior_path.exists():
            previous = json.loads(prior_path.read_text())
            if previous.get("chunk_sha256") != entry.get("sha256"):
                raise RuntimeError("same chunk ID now has different collected content")
        _save_block(target, date, block, start, end, prior_path)
        publication = {"date": date, "chunk_id": chunk_id, "target": str(target),
                       "status": "published", "chunk_sha256": entry.get("sha256"),
                       "block_sha256": digest(block.encode()), "writer_sha256": digest(writer.encode()),
                       "reviewer_sha256": digest(reviewer.encode()),
                       "rendered_sha256": digest(rendered.encode()), "patches_applied": len(review["patches"]),
                       "published_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        write_json(prior_path, publication)
        status = _publish_status(date, state_dir, target)
    return {"publication": publication, "status": status}


def hook_markers(payload):
    prompt = payload.get("tool_input", {}).get("prompt", "")
    if not isinstance(prompt, str):
        raise ValueError("Agent prompt is not text")
    result = {}
    for key in ("DAILY_DOCS_DATE", "CHUNK_ID", "ROLE"):
        matches = re.findall(r"^" + key + r"=([^\s]+)$", prompt, re.M)
        if len(matches) != 1:
            raise ValueError("Agent prompt requires one " + key + " marker")
        result[key] = matches[0]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["record", "hook", "publish", "publish-empty", "status"])
    parser.add_argument("--state-root", default=os.environ.get("DAILY_DOCS_STATE"))
    parser.add_argument("--date", default=os.environ.get("DAILY_DOCS_DATE"))
    parser.add_argument("--chunk-id", default=os.environ.get("DAILY_DOCS_CHUNK_ID"))
    parser.add_argument("--role", choices=["writer", "reviewer"], default=os.environ.get("DAILY_DOCS_ROLE"))
    parser.add_argument("--text-file")
    parser.add_argument("--vault")
    args = parser.parse_args()
    if not args.state_root:
        parser.error("--state-root or DAILY_DOCS_STATE is required")
    if args.command == "hook":
        payload = json.load(sys.stdin)
        if payload.get("tool_name") not in ("Agent", "Task"):
            return
        markers = hook_markers(payload)
        date, chunk_id, role = markers["DAILY_DOCS_DATE"], markers["CHUNK_ID"], markers["ROLE"]
        result = record_response(date, Path(args.state_root) / validate_date(date), chunk_id, role,
                                 extract_agent_response(payload), {"hook": payload})
    else:
        if not args.date:
            parser.error("--date is required")
        date = validate_date(args.date)
        state_dir = Path(args.state_root) / date
        if args.command == "record":
            if not args.chunk_id or not args.role or not args.text_file:
                parser.error("record requires --chunk-id, --role and --text-file")
            text = Path(args.text_file).read_bytes().decode("utf-8")
            result = record_response(date, state_dir, args.chunk_id, args.role, text,
                                     {"text_file": str(Path(args.text_file).resolve())})
        elif args.command == "publish-empty":
            if not args.vault:
                parser.error("publish-empty requires --vault")
            result = publish_empty(date, state_dir, args.vault)
        elif args.command == "publish":
            if not args.chunk_id or not args.vault:
                parser.error("publish requires --chunk-id and --vault")
            result = publish_chunk(date, state_dir, args.chunk_id, args.vault)
        else:
            result = processing_status(date, state_dir)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
