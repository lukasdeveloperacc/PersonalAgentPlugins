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

    required_skills = ["socrates-partner", "socrates-document-specialist", "harness-reviewer"]
    for skill in required_skills:
        p = ROOT / f"skills/{skill}/SKILL.md"
        check(f"skill exists: {skill}", p.is_file(), str(p))
        text = p.read_text(encoding="utf-8")
        check(f"skill Korean default: {skill}", "Korean" in text or "한국어" in text or "Korean by default" in text)
        check(f"skill forbids ask-family: {skill}", "/ask" in text and "omx ask" in text)

    reviewer = (ROOT / "skills/harness-reviewer/SKILL.md").read_text(encoding="utf-8")
    for token in ["GO", "STOP", "NEEDS_CHECK", ".md.done", "HARNESS_VERDICT_DONE"]:
        check(f"reviewer contains {token}", token in reviewer)

    doc = (ROOT / "skills/socrates-document-specialist/SKILL.md").read_text(encoding="utf-8")
    for path in ["SOCRATES_BRIEF.md", "PRD.md", "OUT_OF_SCOPE.md", "HANDOFF.md"]:
        check(f"document specialist writes {path}", path in doc)

    partner = (ROOT / "skills/socrates-partner/SKILL.md").read_text(encoding="utf-8")
    for phrase in ["가장 강한 반론", "OUT 후보", "다음에 물어볼 질문 1개", "방향 선택 추천"]:
        check(f"partner output includes {phrase}", phrase in partner)

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    print(f"\n{passed}/{total} Codex companion checks passed")
    if passed != total:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
