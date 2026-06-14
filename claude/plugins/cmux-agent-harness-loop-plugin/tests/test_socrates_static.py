#!/usr/bin/env python3
"""Static checks for the Socrates workshop surface.

These checks do not try to simulate a whole conversation. They assert that the plugin ships the
load-bearing pieces required by the video-style flow: mode/experience capture, Codex reflection,
direction menu, document-specialist handoff, and planning artifact templates.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]

checks = []


def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def read(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8")


def main():
    soc = ROOT / "skills/socrates/SKILL.md"
    agent = ROOT / "agents/document-specialist.md"
    contract = ROOT / "contracts/socrates-workshop-contract.md"

    check("socrates skill exists", soc.is_file(), str(soc))
    check("document-specialist agent exists", agent.is_file(), str(agent))
    check("socrates contract exists", contract.is_file(), str(contract))

    text = soc.read_text(encoding="utf-8")
    for phrase in [
        "인터뷰모드",
        "토론모드",
        "질문최소로 빠르게",
        "거의처음",
        "튜토리얼 정도",
        "혼자 만들 수 있음",
        "실무개발자",
        "Codex",
        "cmux send",
        "cmux read-screen",
        "document-specialist",
        "이대로 진행",
        "문제/타겟 다시 잡기",
        "기능/차별화 다시 잡기",
        "OUT 목록 조정",
    ]:
        check(f"socrates includes {phrase}", phrase in text)

    forbidden_runtime = ["omx ask", "omc ask", "/ask"]
    # They may appear only as explicitly forbidden strings, never as a recommended command.
    check("socrates Korean default policy", "Korean by default" in text and "한국어" in text)

    for bad in forbidden_runtime:
        check(f"socrates forbids {bad}", bad in text and "Do **not** use" in text)

    agent_text = agent.read_text(encoding="utf-8")
    check("agent is document-only", "do not write application source code" in agent_text.lower())
    check("agent writes PRD", "docs/changes/PRD.md" in agent_text)

    for rel in [
        "templates/socrates/SOCRATES_BRIEF.md.tmpl",
        "templates/socrates/PRD.md.tmpl",
        "templates/socrates/OUT_OF_SCOPE.md.tmpl",
        "templates/socrates/HANDOFF.md.tmpl",
        "templates/socrates/EXPERIMENT_PLAN.md.tmpl",
        "templates/project-commands/socrates.md.tmpl",
    ]:
        check(f"template exists: {rel}", (ROOT / rel).is_file())

    readme = (REPO / "README.md").read_text(encoding="utf-8")
    check("README documents socrates invocation", "/cmux-agent-harness-loop-plugin:socrates" in readme)
    check("README documents bare alias", "bare `/socrates`" in readme)
    prd_template = (ROOT / "templates/socrates/PRD.md.tmpl").read_text(encoding="utf-8")
    check("template uses Korean PRD heading", "제품 요구사항 문서" in prd_template)

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    print(f"\n{passed}/{total} Socrates checks passed")
    failed = [(n, d) for n, ok, d in checks if not ok]
    if failed:
        print("FAILURES:")
        for n, d in failed:
            print(f"  - {n} {d}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
