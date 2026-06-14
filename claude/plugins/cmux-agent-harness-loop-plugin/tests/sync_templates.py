#!/usr/bin/env python3
"""Sync / verify the templates/ mirror against the canonical heredocs in SKILL.md.

The inlined fenced code blocks under the "# Inlined Canonical Templates" section of
SKILL.md are the source of truth. Each block is introduced by a heading of the form
`## <relative/path>` and followed by a fenced code block whose body is the template.

Usage:
  sync_templates.py write    # (re)generate templates/*.tmpl from SKILL.md
  sync_templates.py check    # exit 1 if any mirror file differs from the canonical heredoc
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
SKILL = os.path.join(PLUGIN_ROOT, "skills", "cmux-agent-harness-loop", "SKILL.md")
TEMPLATES = os.path.join(PLUGIN_ROOT, "templates")

# Map the heading path (as written in SKILL.md) -> mirror file path (relative to templates/).
PATH_MAP = {
    ".agent-harness/harness.yaml": "harness.yaml.tmpl",
    ".agent-harness/state.json": "state.json.tmpl",
    ".agent-harness/panes.json": "panes.json.tmpl",
    ".agent-harness/prompts/orchestrator.md": "prompts/orchestrator.md.tmpl",
    ".agent-harness/prompts/reviewer.md": "prompts/reviewer.md.tmpl",
    ".agent-harness/prompts/worker.md": "prompts/worker.md.tmpl",
    ".agent-harness/prompts/handoff.md": "prompts/handoff.md.tmpl",
    "docs/changes/TASK_SPEC.md": "docs-changes/TASK_SPEC.md.tmpl",
    "docs/changes/DECISIONS.md": "docs-changes/DECISIONS.md.tmpl",
    "docs/changes/REVIEW_LOG.md": "docs-changes/REVIEW_LOG.md.tmpl",
    "docs/changes/TODO.md": "docs-changes/TODO.md.tmpl",
    "docs/changes/HANDOFF.md": "docs-changes/HANDOFF.md.tmpl",
}


def parse_heredocs(skill_text):
    """Return {heading_path: body} for blocks after the Inlined Canonical Templates header.

    INVARIANT: template bodies in the canonical heredocs must NOT contain a nested ``` fence.
    The block regex stops at the first closing fence, so an embedded fence would truncate
    that block and shift subsequent ones. None of the current templates use code fences.
    """
    marker = "# Inlined Canonical Templates"
    idx = skill_text.find(marker)
    if idx == -1:
        raise SystemExit("error: '# Inlined Canonical Templates' section not found in SKILL.md")
    section = skill_text[idx:]
    blocks = {}
    # Heading "## <path>" then a fenced block ```lang\n<body>```
    pattern = re.compile(r"^##\s+(\S+)\s*?\n+```[^\n]*\n(.*?)\n```", re.MULTILINE | re.DOTALL)
    for m in pattern.finditer(section):
        heading = m.group(1).strip()
        body = m.group(2)
        if heading in PATH_MAP:
            blocks[heading] = body + "\n"  # trailing newline at EOF
    return blocks


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("write", "check"):
        raise SystemExit(__doc__)
    mode = sys.argv[1]
    with open(SKILL, "r", encoding="utf-8") as f:
        skill_text = f.read()
    blocks = parse_heredocs(skill_text)
    missing_headings = [h for h in PATH_MAP if h not in blocks]
    if missing_headings:
        raise SystemExit("error: missing canonical heredocs for: " + ", ".join(missing_headings))

    drift = []
    for heading, rel in PATH_MAP.items():
        body = blocks[heading]
        target = os.path.join(TEMPLATES, rel)
        if mode == "write":
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as out:
                out.write(body)
        else:  # check
            if not os.path.exists(target):
                drift.append(f"MISSING {rel}")
                continue
            with open(target, "r", encoding="utf-8") as cur:
                if cur.read() != body:
                    drift.append(f"DRIFT   {rel}")

    if mode == "write":
        print(f"wrote {len(PATH_MAP)} template mirror files under templates/")
        return 0
    if drift:
        print("TEMPLATE MIRROR DRIFT (heredocs in SKILL.md are canonical — fix templates/):")
        for d in drift:
            print("  " + d)
        return 1
    print(f"OK: all {len(PATH_MAP)} template mirror files match the canonical heredocs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
