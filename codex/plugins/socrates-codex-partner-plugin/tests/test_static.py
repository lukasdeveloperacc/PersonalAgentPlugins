#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MARKET = ROOT.parents[1] / ".agents/plugins/marketplace.json"
checks = []

def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))


def main():
    manifest = ROOT / ".codex-plugin/plugin.json"
    check("manifest exists", manifest.is_file())
    data = json.loads(manifest.read_text(encoding="utf-8"))
    check("manifest name", data.get("name") == "socrates-codex-partner-plugin", data.get("name"))
    check("skills path declared", data.get("skills") == "./skills/")
    check("marketplace exists", MARKET.is_file(), str(MARKET))
    market = json.loads(MARKET.read_text(encoding="utf-8"))
    check("marketplace name", market.get("name") == "personal-agent-plugins-codex", market.get("name"))
    check("marketplace entry", any(p.get("name") == "socrates-codex-partner-plugin" for p in market.get("plugins", [])))

    core_skills = ["socrates-partner", "socrates-document-specialist", "harness-reviewer"]
    role_skills = [
        "socrates-pm",
        "idea-reviewer",
        "design-reviewer",
        "code-reviewer",
        "ai-researcher",
        "surfer-researcher",
        "ralplan-partner",
    ]
    required_skills = core_skills + role_skills
    for skill in required_skills:
        p = ROOT / f"skills/{skill}/SKILL.md"
        agent_yaml = ROOT / f"skills/{skill}/agents/openai.yaml"
        check(f"skill exists: {skill}", p.is_file(), str(p))
        text = p.read_text(encoding="utf-8")
        check(f"skill Korean default: {skill}", "Korean" in text or "한국어" in text or "Korean by default" in text)
        check(f"skill forbids ask-family: {skill}", "/ask" in text or "ask-family" in text or "ask/exec" in text)
        check(f"skill forbids exec-family: {skill}", "exec" in text.lower())
        check(f"agent profile exists: {skill}", agent_yaml.is_file(), str(agent_yaml))
        agent_text = agent_yaml.read_text(encoding="utf-8") if agent_yaml.is_file() else ""
        check(f"agent profile has display name: {skill}", "display_name:" in agent_text)
        check(f"agent profile has default prompt: {skill}", "default_prompt:" in agent_text)
        check(f"agent profile declares invocation policy: {skill}", "allow_implicit_invocation:" in agent_text)

    contract = (ROOT / "contracts/codex-partner-contract.md").read_text(encoding="utf-8")
    for skill in core_skills:
        check(f"contract preserves core role: {skill}", skill in contract)
    for skill in role_skills:
        p = ROOT / f"skills/{skill}/SKILL.md"
        text = p.read_text(encoding="utf-8")
        check(f"contract lists role lane: {skill}", skill in contract)
        check(f"role references shared contract: {skill}", "../../contracts/codex-partner-contract.md" in text)
        check(f"role is structured markdown: {skill}", "```md" in text and "##" in text)
        check(f"role no source edits by default: {skill}", "source" in text.lower() and ("No source" in text or "Do not edit" in text or "Read-only" in text))
        check(f"role persistent cmux: {skill}", "cmux" in text and ("persistent" in text.lower() or "Persistent" in text))

    reviewer = (ROOT / "skills/harness-reviewer/SKILL.md").read_text(encoding="utf-8")
    for token in ["GO", "STOP", "NEEDS_CHECK", ".md.done", "HARNESS_VERDICT_DONE"]:
        check(f"reviewer contains {token}", token in reviewer)

    doc = (ROOT / "skills/socrates-document-specialist/SKILL.md").read_text(encoding="utf-8")
    bundle_files = [
        "RALPLAN_BRIEF.md",
        "INTERVIEW_EVIDENCE.md",
        "RALPLAN_DR_SEED.md",
        "ULTRAGOAL_DRAFT.md",
        "ROLE_PANE_MAP.md",
        "MCP_READINESS_CHECKLIST.md",
    ]
    for path in ["SOCRATES_BRIEF.md", "PRD.md", "OUT_OF_SCOPE.md", "HANDOFF.md"] + bundle_files:
        check(f"document specialist writes {path}", path in doc)
        if path in bundle_files:
            check(f"contract references bundle {path}", path in contract)
            check(f"bundle template exists: {path}", (ROOT / f"templates/socrates/{path}.tmpl").is_file())

    check("ULTRAGOAL draft-only wording in document specialist", "draft only" in doc.lower() and "auto-run" in doc.lower())
    check("ULTRAGOAL draft owner/validator in contract", "document-specialist" in contract and "claude-codex-orchestrator" in contract)

    for tmpl in ["CODEX_ROLE_PROFILE.md.tmpl", "RESEARCH_NOTE.md.tmpl", "REVIEW_NOTE.md.tmpl"]:
        check(f"support template exists: {tmpl}", (ROOT / f"templates/socrates/{tmpl}").is_file())

    partner = (ROOT / "skills/socrates-partner/SKILL.md").read_text(encoding="utf-8")
    for phrase in ["가장 강한 반론", "OUT 후보", "다음에 물어볼 질문 1개", "방향 선택 추천"]:
        check(f"partner output includes {phrase}", phrase in partner)

    docs = (ROOT.parents[2] / "docs/codex-companion-plugin.md").read_text(encoding="utf-8")
    for skill in role_skills:
        check(f"docs list role lane: {skill}", skill in docs)
    check("docs mention persistent cmux transport", "cmux send" in docs and "cmux read-screen" in docs)

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    print(f"\n{passed}/{total} Codex companion checks passed")
    if passed != total:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
