"""Run an explicitly requested paid trial and retain its provenance and termination."""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def run(leader, label, plugin=None):
    here = Path(__file__).resolve().parent
    host = os.environ.get("EVAL_HOST", "claude")
    if host not in ("claude", "codex"):
        raise ValueError("EVAL_HOST must be claude or codex")
    if not label or Path(label).name != label or label in (".", ".."):
        raise ValueError("label must be a single directory name")
    case = json.loads((here / "evals.json").read_text())["evals"][int(os.environ.get("EVAL_INDEX", "0"))]
    source = Path(plugin).resolve() if plugin else here.parents[2]
    skill = source / "skills/basic-team"
    if not (skill / "SKILL.md").is_file():
        raise ValueError("source must contain skills/basic-team/SKILL.md")
    out = Path(os.environ.get("EVAL_OUT", str(here / "results"))).resolve() / (label + "-" + leader + "-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
    out.mkdir(parents=True)
    work = out / "work"
    shutil.copytree(here / case["fixture"], work)
    for command in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "-c", "user.email=e@e", "-c", "user.name=e", "commit", "-qm", "fixture"]):
        subprocess.run(command, cwd=work, check=True, capture_output=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True)
    hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(skill.rglob("*")) if p.is_file() and "evals" not in p.parts and "__pycache__" not in p.parts}
    cli_available = shutil.which(host) is not None
    version = subprocess.run([host, "--version"], capture_output=True, text=True) if cli_available else subprocess.CompletedProcess([], 127, stdout="", stderr="CLI not installed")
    effort = os.environ.get("LEADER_EFFORT", "max")
    args = ["claude", "-p", case["prompt"], "--model", leader, "--effort", effort,
            "--output-format", "stream-json", "--verbose", "--permission-mode", "bypassPermissions",
            "--max-budget-usd", os.environ.get("BUDGET", "8"), "--plugin-dir", str(source)]
    manifest = {"host": host, "cli_version": version.stdout.strip(), "case": case["name"],
                "kind": case.get("kind", "backend"), "source_commit": commit.stdout.strip(),
                "source_hashes": hashes, "requested_skill_path": str(skill / "SKILL.md"), "host_confirmed_skill_path": None,
                "source_dirty": bool(subprocess.run(["git", "status", "--porcelain"], cwd=source, capture_output=True).stdout),
                "leader": {"requested_model": leader, "requested_effort": effort, "invocation": args,
                           "observed_model": None, "observed_effort": None},
                "requested_observation_policy": "invocation-evidence-v2", "recorded_observation_policies": [], "approved_exceptions": [],
                "budget_usd": os.environ.get("BUDGET", "8"), "timeout_seconds": int(os.environ.get("TIMEOUT", "1800")),
                "started_at": now(), "exit_status": None, "stop_reason": None}
    if host == "codex" or not cli_available:
        manifest["leader"]["invocation"] = None
        manifest["stop_reason"] = "capability_blocked"
        manifest["capability_gap"] = "CLI not installed; no trial launched." if not cli_available else "Installed CLI supports --json; native spawn/result/termination JSON schema is unconfirmed. No Codex trial launched."
        (out / "stream.jsonl").write_text("")
        (out / "stderr.txt").write_text(manifest["capability_gap"])
    else:
        with (out / "stream.jsonl").open("w") as stdout, (out / "stderr.txt").open("w") as stderr:
            started = time.monotonic()
            proc = subprocess.Popen(args, cwd=work, stdout=stdout, stderr=stderr, start_new_session=True,
                                    env={**os.environ, "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"})
            def cancel(signum, frame):
                raise KeyboardInterrupt
            previous_handler = signal.signal(signal.SIGTERM, cancel)
            try:
                proc.wait(timeout=manifest["timeout_seconds"])
            except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
                manifest["stop_reason"] = "timed_out" if isinstance(exc, subprocess.TimeoutExpired) else "cancelled"
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()
            finally:
                signal.signal(signal.SIGTERM, previous_handler)
            manifest["exit_status"] = proc.returncode
            manifest["elapsed_seconds"] = round(time.monotonic() - started, 3)
    manifest["ended_at"] = now()
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    from analyze import analyze
    summary = analyze(out)
    manifest["child_invocations"] = summary["spawns"]
    manifest["recorded_observation_policies"] = summary["recorded_observation_policies"]
    manifest["settings_evidence"] = summary["settings_evidence"]
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({"run": str(out), "outcome": summary["outcome"], "exit_status": manifest["exit_status"]}))
    return manifest["exit_status"] if manifest["exit_status"] not in (None, 0) else (2 if manifest["stop_reason"] else 0)


if __name__ == "__main__":
    sys.exit(run(*sys.argv[1:]))
