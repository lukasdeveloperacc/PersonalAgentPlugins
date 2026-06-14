#!/usr/bin/env python3
"""Reference implementation of the cmux-agent-harness-loop decision logic.

A SKILL.md is prose the agent follows, not executable code. To make the contracts testable
without a live cmux pane, this module implements a faithful reference of the load-bearing
mechanics the SKILL describes:

  - a fake cmux transport (records sends; returns canned read-screen frames)
  - request classification
  - the both-channels review round-trip (send -> read-screen sentinel -> file parse on .done)
  - verdict parsing with the exactly-one-of enum + unparseable/clarifying handling
  - the DECIDE mapping (ACCEPT/REJECT/NEEDS_CHECK/DEFER)
  - the termination guards (convergence / max_loops / no-progress)
  - template scaffolding from the canonical templates/ mirror, idempotently
  - safety filters (ask family / forbidden non-interactive exec transport /
    dangerous flags / secret patterns)

The tests in test_harness.py drive this reference against the repo fixtures and templates.
This is a verification artifact for the plugin contracts, not the plugin runtime itself.
"""
import fnmatch
import hashlib
import json
import os
import re
import shutil

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES = os.path.join(PLUGIN_ROOT, "templates")

DECISION_TOKENS = ("GO", "STOP", "NEEDS_CHECK")
SENTINEL_RE = re.compile(r"<<<HARNESS_VERDICT_DONE id=([A-Za-z0-9_]+)>>>")

ASK_FAMILY = ("/oh-my-claudecode:ask", ":ask", "/ask", "omc ask", "omx ask")
# A residual one-shot advisor token: a provider/omc/omx followed by "ask".
ASK_TOKEN_RE = re.compile(r"\b(?:omc|omx|claude|gemini|codex)\s+ask\b")
SLASH_ASK_RE = re.compile(r"(?:^|\s)/(?:oh-my-claudecode:)?ask\b")
# Non-interactive exec transports bypass the persistent pane conversation and are
# forbidden by default. The supported path is: start `omx`/`codex` in a cmux pane once,
# then inject prompts with cmux send / set-buffer / paste-buffer.
FORBIDDEN_EXEC_TRANSPORT_RE = re.compile(
    r"\b(?:cmux\s+omx\s+exec|omx\s+exec|codex\s+exec(?:\s+review)?)\b"
)
DANGEROUS_FLAGS = (
    "--dangerously-skip-permissions",
    "--yolo",
    "-a never",
    "--approval-mode never",
)
SECRET_PATTERNS = ("*_API_KEY", "*_TOKEN", "*_SECRET", "*_PASSWORD")
SECRET_VALUE_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,})")

# ----------------------------------------------------------------------------- classification

# Order matters: earlier rules win. "feature" and "bugfix" intent verbs take precedence
# over an incidental mention of "test"/"docs" (e.g. "add an endpoint AND a unit test" is a
# feature, not a test task). Pure-test / pure-docs requests still classify correctly because
# their leading verb is the testing/docs verb, not an add/fix verb.
_PRIMARY_VERB = ("add", "implement", "create", "build", "endpoint", "feature")
_FIX_VERB = ("fix", "bug", "typeerror", "crash", "regression")

_CLASS_RULES = [
    ("bugfix", _FIX_VERB),
    ("feature", _PRIMARY_VERB),
    ("test", ("test", "coverage", "unit test", "e2e")),
    ("docs", ("document", "readme", "docs", "comment")),
    ("refactor", ("refactor", "cleanup", "simplify", "rename")),
    ("security", ("security", "auth", "vulnerab", "secret", "cve")),
    ("performance", ("performance", "slow", "optimize", "latency")),
    ("architecture", ("architecture", "design", "boundary", "module")),
    ("review", ("review the", "review diff", "code review", "review this", "review my", "please review")),
    ("status", ("status",)),
    ("handoff", ("handoff", "hand off")),
    ("setup", ("setup", "set up", "scaffold the harness")),
]


def classify(request: str) -> str:
    r = request.lower()
    for label, kws in _CLASS_RULES:
        if any(k in r for k in kws):
            return label
    return "feature"


# ----------------------------------------------------------------------------- safety filters


def redact(text: str) -> str:
    return SECRET_VALUE_RE.sub("[REDACTED]", text)


def safety_violations(emitted_commands):
    """Return a list of safety violations across emitted transport strings.

    The harness forbids one-shot advisor tokens (`omx ask`, `omc ask`, `/ask`,
    `/oh-my-claudecode:ask`, and `cmux omx ask`) and also forbids default-use
    non-interactive exec transports (`cmux omx exec`, `omx exec`, `codex exec`,
    `codex exec review`). Plain interactive pane bootstrap such as `cmux send ... "omx\n"`
    or `cmux omc` remains allowed because it preserves a live pane conversation.
    """
    violations = []
    for cmd in emitted_commands:
        low = cmd.lower()
        if ASK_TOKEN_RE.search(low) or SLASH_ASK_RE.search(low):
            violations.append(("ask_family", "one-shot advisor", cmd))
        if FORBIDDEN_EXEC_TRANSPORT_RE.search(low):
            violations.append(("exec_transport", "non-interactive exec", cmd))
        for f in DANGEROUS_FLAGS:
            if f in cmd:
                violations.append(("dangerous_flag", f, cmd))
        if SECRET_VALUE_RE.search(cmd):
            violations.append(("secret_value", "literal-secret", cmd))
    return violations


def is_secret_env_name(name: str) -> bool:
    return any(fnmatch.fnmatch(name, p) for p in SECRET_PATTERNS)


# ----------------------------------------------------------------------------- verdict parsing


class Verdict:
    def __init__(self, decision, findings, questions):
        self.decision = decision          # one of DECISION_TOKENS, or None if unparseable
        self.findings = findings          # list of strings
        self.questions = questions        # list of strings

    @property
    def parseable(self):
        return self.decision in DECISION_TOKENS


def _section(md_text: str, heading: str) -> str:
    m = re.search(r"##\s*" + re.escape(heading) + r"\s*\n(.*?)(?:\n##|\Z)", md_text, re.DOTALL)
    return m.group(1) if m else ""


def parse_verdict(md_text: str) -> Verdict:
    decision = None
    # Robust to **GO**, `STOP`, lowercase, and an inline "Review Decision: GO" form.
    m = re.search(r"##\s*Review Decision\b[:\s]*\n?[\s>*`]*([A-Za-z_]+)", md_text)
    if m:
        token = m.group(1).upper()
        if token in DECISION_TOKENS:
            decision = token
    # Findings are scoped to the "## Findings" section only (not the whole document).
    findings_section = _section(md_text, "Findings")
    findings = re.findall(r"^\s*\d+\.\s*(.+)$", findings_section, re.MULTILINE)
    questions = [q.strip("- ").strip()
                 for q in _section(md_text, "Questions For Orchestrator").splitlines()
                 if q.strip().startswith("-")]
    return Verdict(decision, findings, questions)


def should_parse(changes_dir: str, loop_id: str, attempt: int) -> bool:
    """Parse gate: the orchestrator may parse the verdict ONLY when the attempt-keyed
    `.done` marker exists. The screen sentinel is never the parse trigger."""
    base = os.path.join(changes_dir, f"REVIEW_{loop_id}_{attempt}.md")
    return os.path.exists(base + ".done") and os.path.exists(base)


def findings_hash(findings) -> str:
    return hashlib.sha256("\n".join(findings).encode()).hexdigest()[:16]


# ----------------------------------------------------------------------------- fake transport


class FakeCmux:
    """Records sends/notifies; returns scripted read-screen frames per surface."""

    def __init__(self):
        self.sends = []          # list of (surface, text)
        self.notifies = []       # list of (title, body, surface)
        self.splits = []         # list of direction
        self.respawns = []       # list of surface
        self._frames = {}        # surface -> list of frames (popped per read)
        self._panel_lists = []   # successive list-panels outputs
        self.surface_seq = 10

    def script_frames(self, surface, frames):
        self._frames[surface] = list(frames)

    def script_panel_lists(self, lists):
        self._panel_lists = list(lists)

    # transport verbs
    def new_split(self, direction, focus=False):
        self.splits.append(direction)
        self.surface_seq += 1
        return f"surface:{self.surface_seq}"

    def send(self, surface, text):
        self.sends.append((surface, text))

    def read_screen(self, surface, lines=200, scrollback=False):
        frames = self._frames.get(surface, [])
        return frames.pop(0) if frames else ""

    def list_panels(self):
        return self._panel_lists.pop(0) if self._panel_lists else ""

    def respawn_pane(self, surface, command=None):
        self.respawns.append(surface)
        return True

    def notify(self, title, body, surface=None):
        self.notifies.append((title, body, surface))


# ----------------------------------------------------------------------------- scaffolding


CANONICAL_RUNTIME_FILES = {
    "harness.yaml.tmpl": ".agent-harness/harness.yaml",
    "state.json.tmpl": ".agent-harness/state.json",
    "panes.json.tmpl": ".agent-harness/panes.json",
    "prompts/orchestrator.md.tmpl": ".agent-harness/prompts/orchestrator.md",
    "prompts/reviewer.md.tmpl": ".agent-harness/prompts/reviewer.md",
    "prompts/worker.md.tmpl": ".agent-harness/prompts/worker.md",
    "prompts/handoff.md.tmpl": ".agent-harness/prompts/handoff.md",
    "docs-changes/TASK_SPEC.md.tmpl": "docs/changes/TASK_SPEC.md",
    "docs-changes/DECISIONS.md.tmpl": "docs/changes/DECISIONS.md",
    "docs-changes/REVIEW_LOG.md.tmpl": "docs/changes/REVIEW_LOG.md",
    "docs-changes/TODO.md.tmpl": "docs/changes/TODO.md",
    "docs-changes/HANDOFF.md.tmpl": "docs/changes/HANDOFF.md",
}


def resolve_template_source(plugin_root_env=None):
    """Mimic the SKILL resolution order; returns (path, label)."""
    if plugin_root_env:
        cand = os.path.join(plugin_root_env, "skills", "cmux-agent-harness-loop", "templates")
        if os.path.isdir(cand):
            return cand, cand
    if os.path.isdir(TEMPLATES):
        return TEMPLATES, TEMPLATES
    return None, "inlined (SKILL.md heredocs)"


def is_plugin_repo(target_dir):
    """setup guard: refuse to scaffold into the plugin repo itself."""
    cur = os.path.abspath(target_dir)
    while True:
        if os.path.isdir(os.path.join(cur, ".claude-plugin")):
            return True
        mp = os.path.join(cur, "claude", ".claude-plugin", "marketplace.json")
        if os.path.isfile(mp):
            try:
                data = json.load(open(mp))
                if any(p.get("name", "").startswith("cmux-agent-harness-loop")
                       for p in data.get("plugins", [])):
                    return True
            except Exception:
                pass
        parent = os.path.dirname(cur)
        if parent == cur:
            return False
        cur = parent


def setup_scaffold(target_dir, src_templates):
    """Idempotent: write missing files only; never clobber non-empty existing files."""
    written, skipped = [], []
    for tmpl_rel, runtime_rel in CANONICAL_RUNTIME_FILES.items():
        src = os.path.join(src_templates, tmpl_rel)
        dest = os.path.join(target_dir, runtime_rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skipped.append(runtime_rel)
            continue
        shutil.copyfile(src, dest)
        written.append(runtime_rel)
    return written, skipped


# ----------------------------------------------------------------------------- DECIDE / loop


def decide(verdict: Verdict):
    """Map a STOP verdict's findings to per-finding decisions. Returns list of (sev, decision)."""
    out = []
    for f in verdict.findings:
        low = f.lower()
        if "[critical]" in low or "[major]" in low:
            out.append((f, "ACCEPT"))
        elif "[minor]" in low:
            out.append((f, "DEFER"))
        else:
            out.append((f, "NEEDS_CHECK"))
    return out


class LoopState:
    def __init__(self, max_loops=5):
        self.stage = "IDLE"
        self.loop_count = 0
        self.max_loops = max_loops
        self.converged = False
        self.last_decision = None
        self.last_stop_findings_hash = None
        self.terminated_reason = None  # DONE | NEEDS_CHECK | NO_PROGRESS | None


def evaluate_termination(state: LoopState, verdict: Verdict, remaining_criteria: int):
    """Apply the termination spec. Returns the terminal reason or None (NEXT_LOOP)."""
    state.last_decision = verdict.decision
    if verdict.decision == "GO" and remaining_criteria == 0:
        state.converged = True
        state.terminated_reason = "DONE"
        return "DONE"
    if verdict.decision == "NEEDS_CHECK":
        state.terminated_reason = "NEEDS_CHECK"
        return "NEEDS_CHECK"
    if verdict.decision == "STOP":
        h = findings_hash(verdict.findings)
        if state.last_stop_findings_hash == h:
            state.terminated_reason = "NO_PROGRESS"
            return "NO_PROGRESS"
        state.last_stop_findings_hash = h
    state.loop_count += 1
    if state.loop_count >= state.max_loops and not state.converged:
        state.terminated_reason = "NEEDS_CHECK"  # ceiling hit, never silent
        return "NEEDS_CHECK"
    return None  # NEXT_LOOP
