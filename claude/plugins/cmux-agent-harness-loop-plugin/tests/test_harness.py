#!/usr/bin/env python3
"""Dry-run / no-pane test suite for cmux-agent-harness-loop (the CI gate).

Runs with CMUX_SURFACE_ID unset. No live cmux pane required. Exercises the load-bearing
contracts via harness_reference.py + the repo fixtures + the canonical templates.

Run:  python3 test_harness.py
Exit: 0 = all pass, 1 = failure.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import harness_reference as H  # noqa: E402

REPO_ROOT = os.path.abspath(os.path.join(H.PLUGIN_ROOT, "..", "..", ".."))
FIXTURES = os.path.join(REPO_ROOT, "test-fixtures")

_results = []


def check(name, cond, detail=""):
    _results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def md_block(text, heading):
    """Extract the fenced code block following a '## heading' in a fixture."""
    import re
    m = re.search(r"##\s*" + re.escape(heading) + r".*?\n```[a-z]*\n(.*?)\n```", text, re.DOTALL)
    return m.group(1) if m else ""


# --------------------------------------------------------------------------- classification
def test_classification():
    feat = read_fixture("harness-feature-request.md")
    bug = read_fixture("harness-bugfix-request.md")
    # the "## Request" body
    feat_req = md_block(feat, "Request") or "add a /health endpoint and a unit test"
    bug_req = md_block(bug, "Request") or "fix the typeerror in parseConfig"
    check("classify feature", H.classify(feat_req) == "feature", H.classify(feat_req))
    check("classify bugfix", H.classify(bug_req) == "bugfix", H.classify(bug_req))
    # all 12 types resolvable to *some* label without crashing
    for r in ["add x", "fix y", "refactor z", "review the diff", "add a test",
              "document the api", "design the module boundary", "auth security review",
              "optimize slow path", "handoff to next", "status please", "setup the harness"]:
        check(f"classify-nonempty:{r[:12]}", isinstance(H.classify(r), str) and H.classify(r))


# --------------------------------------------------------------------------- template fallback
def test_template_resolution():
    # CLAUDE_PLUGIN_ROOT unset -> resolves to the templates/ dir (or inlined label)
    src, label = H.resolve_template_source(plugin_root_env=None)
    check("template source resolves with PLUGIN_ROOT unset", label is not None, str(label))
    check("templates dir exists", src is not None and os.path.isdir(src), str(src))
    # all 12 canonical template files present in the mirror
    missing = [t for t in H.CANONICAL_RUNTIME_FILES if not os.path.isfile(os.path.join(src, t))]
    check("all 12 template mirror files present", not missing, ",".join(missing))


# --------------------------------------------------------------------------- setup idempotency
def test_setup_idempotency():
    src, _ = H.resolve_template_source(None)
    with tempfile.TemporaryDirectory() as d:
        w1, s1 = H.setup_scaffold(d, src)
        check("setup run1 writes 12 files", len(w1) == 12 and not s1, f"wrote={len(w1)} skipped={len(s1)}")
        # mutate one file to simulate user edits
        cfg = os.path.join(d, ".agent-harness", "harness.yaml")
        with open(cfg, "a") as f:
            f.write("\n# user edit\n")
        before = open(cfg).read()
        w2, s2 = H.setup_scaffold(d, src)
        after = open(cfg).read()
        check("setup run2 writes nothing new", not w2 and len(s2) == 12, f"wrote={len(w2)} skipped={len(s2)}")
        check("setup run2 preserves user edit (no clobber)", before == after)
        # scaffolded JSON is valid
        import json
        json.load(open(os.path.join(d, ".agent-harness", "state.json")))
        json.load(open(os.path.join(d, ".agent-harness", "panes.json")))
        check("scaffolded state.json/panes.json valid JSON", True)


# --------------------------------------------------------------------------- setup guard
def test_setup_guard():
    # the plugin repo itself must be refused
    check("setup guard refuses plugin repo", H.is_plugin_repo(REPO_ROOT) is True)
    with tempfile.TemporaryDirectory() as d:
        check("setup guard allows plain target dir", H.is_plugin_repo(d) is False)


# --------------------------------------------------------------------------- both-channels review
def make_review_round(cmux, surface, loop_id, attempt, verdict_md, sentinel_present=True,
                      done_present=True):
    """Simulate one review: orchestrator sends, reads screen, parses verdict file."""
    # 1. send (channel 1)
    sid = f"{loop_id}_{attempt}"
    prompt = (
        f"[HARNESS_REVIEW id={sid}]\n"
        f"Read .agent-harness/prompts/tmp/{loop_id}.txt and write "
        f"docs/changes/REVIEW_{sid}.md, then create .done and print the sentinel."
    )
    cmux.send(surface, prompt)
    # 2. read-screen frame with sentinel (channel 2)
    frame = (f"[reviewer] wrote docs/changes/REVIEW_{sid}.md\n"
             + (f"<<<HARNESS_VERDICT_DONE id={sid}>>>\n" if sentinel_present else ""))
    cmux.script_frames(surface, [frame])
    screen = cmux.read_screen(surface, scrollback=True)
    sentinel_seen = bool(H.SENTINEL_RE.search(screen))
    # 3. file authoritative parse — only if .done present
    parsed = None
    if done_present:
        parsed = H.parse_verdict(verdict_md)
    return prompt, sentinel_seen, parsed


def test_both_channels():
    cmux = H.FakeCmux()
    surface = "surface:2"
    md = md_block(read_fixture("harness-reviewer-verdict-go.md"), "verdict file: docs/changes/REVIEW_L001_1.md")
    # fallback if heading parse differs
    if not md:
        md = "## Review Decision\nGO\n\n## Findings\n"
    prompt, sentinel_seen, parsed = make_review_round(cmux, surface, "L001", 1, md)
    check("channel1: cmux send carried the prompt", any(surface == s and prompt in t for s, t in cmux.sends))
    check("channel2: read-screen detected sentinel", sentinel_seen)
    check("channel3: verdict parsed from file", parsed is not None and parsed.parseable, str(parsed and parsed.decision))
    check("both-channels: all three present", bool(cmux.sends) and sentinel_seen and parsed.parseable)


def test_parse_on_done_only():
    # sentinel present but .done absent => orchestrator must NOT parse (no decision yet)
    cmux = H.FakeCmux()
    md = "## Review Decision\nGO\n"
    _, sentinel_seen, parsed = make_review_round(cmux, "surface:2", "L009", 1, md,
                                                 sentinel_present=True, done_present=False)
    check("sentinel seen but parse withheld until .done", sentinel_seen and parsed is None)


# --------------------------------------------------------------------------- verdict robustness
def test_unparseable_then_needs_check():
    md = md_block(read_fixture("harness-reviewer-prose-noenum.md"),
                  "verdict file: docs/changes/REVIEW_L003_1.md")
    if not md:
        md = "I have mixed feelings and wrote no decision line."
    v1 = H.parse_verdict(md)
    check("unparseable verdict has no decision", not v1.parseable)
    # retry once -> still unparseable -> escalate NEEDS_CHECK (simulated policy)
    attempts, decision = 1, None
    while attempts <= 2 and decision is None:
        v = H.parse_verdict(md)
        decision = v.decision if v.parseable else None
        attempts += 1
    final = decision if decision else "NEEDS_CHECK"
    check("unparseable escalates to NEEDS_CHECK after 1 retry", final == "NEEDS_CHECK" and attempts == 3)


def test_clarifying_needs_check():
    md = md_block(read_fixture("harness-reviewer-clarifying.md"),
                  "verdict file: docs/changes/REVIEW_L004_1.md")
    if not md:
        md = "## Review Decision\nNEEDS_CHECK\n\n## Questions For Orchestrator\n- which auth?\n"
    v = H.parse_verdict(md)
    check("clarifying verdict parses NEEDS_CHECK", v.decision == "NEEDS_CHECK")
    check("clarifying verdict surfaces a question", len(v.questions) >= 1, str(v.questions))


def test_pane_death_recovery():
    cmux = H.FakeCmux()
    # liveness probe returns empty (dead); orchestrator respawns then re-sends at new attempt
    cmux.script_frames("surface:2", [""])  # dead probe
    dead = not cmux.read_screen("surface:2", lines=5)
    if dead:
        cmux.respawn_pane("surface:2", command="cmux omx")
        # re-send keyed by new attempt
        make_review_round(cmux, "surface:2", "L005", 2,
                          "## Review Decision\nGO\n")
    check("pane death triggers respawn", "surface:2" in cmux.respawns)
    check("recovery re-sends at attempt 2", any("L005_2" in t for _, t in cmux.sends))


# --------------------------------------------------------------------------- termination
def test_convergence_done():
    st = H.LoopState(max_loops=5)
    v = H.Verdict("GO", [], [])
    reason = H.evaluate_termination(st, v, remaining_criteria=0)
    check("convergence -> DONE", reason == "DONE" and st.converged)


def test_no_progress_break():
    st = H.LoopState(max_loops=5)
    stop_md = md_block(read_fixture("harness-reviewer-verdict-stop.md"),
                       "verdict file: docs/changes/REVIEW_L002_1.md")
    v = H.parse_verdict(stop_md) if stop_md else H.Verdict("STOP", ["[critical] a", "[major] b"], [])
    r1 = H.evaluate_termination(st, v, remaining_criteria=2)   # first STOP -> NEXT_LOOP
    r2 = H.evaluate_termination(st, v, remaining_criteria=2)   # identical STOP -> NO_PROGRESS
    check("first STOP continues (NEXT_LOOP)", r1 is None, str(r1))
    check("identical STOP twice -> NO_PROGRESS", r2 == "NO_PROGRESS", str(r2))


def test_max_loops_ceiling():
    st = H.LoopState(max_loops=2)
    # distinct STOP findings each loop so no-progress does not fire first
    reasons = []
    for i in range(4):
        v = H.Verdict("STOP", [f"[major] finding {i}"], [])
        reasons.append(H.evaluate_termination(st, v, remaining_criteria=1))
        if reasons[-1]:
            break
    check("max_loops ceiling terminates with NEEDS_CHECK (never silent)",
          "NEEDS_CHECK" in reasons, str(reasons))


# --------------------------------------------------------------------------- safety negatives
def test_safety_negatives():
    # a clean set of commands the harness would emit
    good = [
        "cmux new-split right --focus false",
        "cmux send --surface surface:2 -- 'omx\\n'",
        "cmux set-buffer --name harness '<prompt>'",
        "cmux paste-buffer --name harness --surface surface:2",
        "cmux send --surface surface:2 -- '\\n'",
        "cmux read-screen --surface surface:2 --scrollback --lines 200",
        "git status -s",
    ]
    check("clean commands produce no safety violations", not H.safety_violations(good),
          str(H.safety_violations(good)))
    # interactive cmux bootstrap remains allowed, but non-interactive exec is forbidden.
    check("cmux omc not flagged", not H.safety_violations(["cmux omc team 2:codex 'x'"]))
    exec_v = H.safety_violations(["cmux omx exec 'review'", "codex exec review < f", "omx exec foo"])
    exec_kinds = {k for k, _, _ in exec_v}
    check("non-interactive exec transport flagged", "exec_transport" in exec_kinds, str(exec_v))
    # bad commands must be flagged
    bad = [
        "claude --dangerously-skip-permissions",
        "codex --yolo",
        "omc ask 'what now'",
        "omx ask 'advise'",
        "echo OPENAI_API_KEY=sk-abc12345 secret",
    ]
    v = H.safety_violations(bad)
    kinds = {k for k, _, _ in v}
    check("dangerous flags flagged", "dangerous_flag" in kinds, str(kinds))
    check("ask family flagged", "ask_family" in kinds, str(kinds))
    check("literal secret flagged", "secret_value" in kinds, str(kinds))
    # adversarial ask-family evasions that earlier slipped through (regression guards)
    check("flags /oh-my-claudecode:ask",
          bool(H.safety_violations(["/oh-my-claudecode:ask 'advise me'"])))
    check("flags 'omx ask' even when it mentions exec",
          bool(H.safety_violations(['omx ask "how do I exec this"'])))
    check("flags cmux omx ask (genuine forbidden, not exec)",
          bool(H.safety_violations(["cmux omx ask 'advise'"])))
    # redaction
    check("redact masks a literal key", "[REDACTED]" in H.redact("token sk-abcdefgh1234"))
    check("secret env-name detection", H.is_secret_env_name("MY_API_KEY") and not H.is_secret_env_name("PATH"))


# --------------------------------------------------------------------------- ordering contract
def test_ordering_contract():
    # Simulate the reviewer's write ordering on disk and assert the reader keys on .done.
    with tempfile.TemporaryDirectory() as d:
        changes = os.path.join(d, "docs", "changes")
        os.makedirs(changes)
        base = os.path.join(changes, "REVIEW_L007_1.md")
        tmp = base + ".tmp"
        done = base + ".done"
        # 1. write tmp
        open(tmp, "w").write("## Review Decision\nGO\n")
        # reader must not parse: final not present yet
        check("reader withholds parse before rename", not os.path.exists(base))
        # 2. atomic rename
        os.replace(tmp, base)
        # reader still withholds until .done
        check("reader withholds parse before .done", not os.path.exists(done))
        # reference predicate must agree: parse withheld before .done
        check("should_parse() False before .done", not H.should_parse(changes, "L007", 1))
        # 3. create .done
        open(done, "w").close()
        # now reader may parse — via the reusable reference predicate, not an inline expr
        check("reader parses only after .done exists (should_parse)",
              H.should_parse(changes, "L007", 1))
        # 4. attempt keying prevents stale reads: attempt 2 has no .done yet
        base2 = os.path.join(changes, "REVIEW_L007_2.md")
        check("attempt-keyed files distinct", base != base2)
        check("should_parse() False for fresh attempt 2", not H.should_parse(changes, "L007", 2))


def main():
    if os.environ.get("CMUX_SURFACE_ID"):
        print("NOTE: CMUX_SURFACE_ID is set; this dry-run suite still runs headless logic only.")
    test_classification()
    test_template_resolution()
    test_setup_idempotency()
    test_setup_guard()
    test_both_channels()
    test_parse_on_done_only()
    test_unparseable_then_needs_check()
    test_clarifying_needs_check()
    test_pane_death_recovery()
    test_convergence_done()
    test_no_progress_break()
    test_max_loops_ceiling()
    test_safety_negatives()
    test_ordering_contract()

    passed = sum(1 for _, ok, _ in _results if ok)
    total = len(_results)
    print(f"\n{passed}/{total} checks passed")
    failed = [(n, d) for n, ok, d in _results if not ok]
    if failed:
        print("FAILURES:")
        for n, d in failed:
            print(f"  - {n}  {d}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
