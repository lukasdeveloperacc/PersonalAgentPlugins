#!/bin/sh
# Validate the marketplace manifest, skill frontmatter, curation entries,
# and the absence of secrets. Requires only POSIX sh, git and python3.
#
#   scripts/validate.sh            local checks only
#   scripts/validate.sh --online   also resolve every curated ref against its remote
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

ONLINE=0
[ "${1:-}" = "--online" ] && ONLINE=1

FAILED=0
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; FAILED=1; }
pass() { printf '  \033[32mok\033[0m    %s\n' "$1"; }
skip() { printf '  \033[33mskip\033[0m  %s\n' "$1"; }

printf '\n\033[1mV1  manifest schema\033[0m\n'
if command -v claude >/dev/null 2>&1; then
  if claude plugin validate . --strict >/tmp/pap-v1.$$ 2>&1; then
    pass "claude plugin validate --strict"
  else
    fail "claude plugin validate --strict"; sed 's/^/        /' /tmp/pap-v1.$$
  fi
  rm -f /tmp/pap-v1.$$
else
  skip "claude CLI not on PATH — schema check deferred to the release smoke test"
fi

printf '\n\033[1mV2-V8  structure, curation, hygiene\033[0m\n'
python3 - "$ONLINE" <<'PYEOF' || FAILED=1
import json, os, re, subprocess, sys

online = sys.argv[1] == "1"
bad = []
def fail(m): bad.append(m); print(f"  \033[31mFAIL\033[0m  {m}")
def ok(m):   print(f"  \033[32mok\033[0m    {m}")
def ok_if(mark, m):
    """실패 없이 통과한 그룹에만 요약 줄을 낸다."""
    if len(bad) == mark: ok(m)

man_path = ".claude-plugin/marketplace.json"
try:
    man = json.load(open(man_path, encoding="utf-8"))
except Exception as e:
    fail(f"V3 {man_path}: {e}"); sys.exit(1)
plugins = man.get("plugins", [])

# ---- V2 skill frontmatter -------------------------------------------------
mark_v2 = len(bad)
skill_dirs = sorted(
    d for d in (os.path.join("skills", n) for n in os.listdir("skills"))
    if os.path.isdir(d)
) if os.path.isdir("skills") else []

for d in skill_dirs:
    p = os.path.join(d, "SKILL.md")
    if not os.path.isfile(p):
        fail(f"V2 {d}: SKILL.md 없음"); continue
    text = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        fail(f"V2 {p}: YAML frontmatter 없음"); continue
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+?)\s*$", fm, re.M)
    desc = re.search(r"^description:\s*(.+?)\s*$", fm, re.M)
    if not name:
        fail(f"V2 {p}: name 없음")
    elif name.group(1).strip().strip('"\'') != os.path.basename(d):
        fail(f"V2 {p}: name '{name.group(1)}' != 폴더명 '{os.path.basename(d)}'")
    if not desc:
        fail(f"V2 {p}: description 없음")
    elif len(desc.group(1)) < 40:
        fail(f"V2 {p}: description이 너무 짧아 트리거로 쓰기 어렵다")
if skill_dirs:
    ok_if(mark_v2, f"V2 skill frontmatter ({len(skill_dirs)}개)")

# ---- V3 local path references + V4 orphans + V7/V8 curation ---------------
referenced = set()
mark_v3 = mark_v7 = len(bad)
local_entries = curated = 0
for p in plugins:
    nm, src = p.get("name", "?"), p.get("source")
    if isinstance(src, str):
        local_entries += 1
        for key in ("skills", "agents", "commands"):
            for rel in p.get(key, []):
                path = os.path.normpath(rel)
                if not os.path.exists(path):
                    fail(f"V3 [{nm}] {key} 참조가 없다: {rel}")
                elif key == "skills":
                    referenced.add(path)
    elif isinstance(src, dict):
        curated += 1
        kind, path = src.get("source"), src.get("path")
        if kind not in ("url", "git-subdir"):
            fail(f"V7 [{nm}] source '{kind}' 금지 — 'url' 또는 'git-subdir'만 허용 "
                 f"('github'은 SSH로 클론해 키 없는 머신에서 실패한다)")
        elif kind == "url" and path:
            fail(f"V7 [{nm}] 'url' 소스는 path를 무시한다 — 저장소 루트를 통째로 받고 "
                 f"빈 플러그인이 설치 성공으로 보고된다. 서브디렉토리는 'git-subdir'를 쓴다")
        elif kind == "git-subdir" and not path:
            fail(f"V7 [{nm}] 'git-subdir'에는 path가 필요하다")
        url = src.get("url", "")
        if not url.startswith("https://"):
            fail(f"V7 [{nm}] HTTPS가 아니다: {url}")
        if not src.get("ref") and not src.get("sha"):
            fail(f"V8 [{nm}] ref 또는 sha를 명시해야 한다")
    else:
        fail(f"V3 [{nm}] source 형식을 알 수 없다")

if local_entries: ok_if(mark_v3, f"V3 로컬 경로 참조 ({local_entries}개 번들)")
if curated:       ok_if(mark_v7, f"V7-V8 큐레이션 항목 형식 ({curated}개)")

orphans = [d for d in skill_dirs if d not in referenced]
if orphans:
    fail("V4 어떤 번들에도 배정되지 않은 스킬: " + ", ".join(orphans))
elif skill_dirs:
    ok("V4 고아 스킬 없음")

# ---- V5 secrets -----------------------------------------------------------
SELF = os.path.normpath("scripts/validate.sh")
PATTERNS = [
    (r"sk-ant-[A-Za-z0-9_-]{20,}",              "Anthropic key"),
    (r"\bsk-[A-Za-z0-9]{32,}",                  "OpenAI-style key"),
    (r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"\bgithub_pat_[A-Za-z0-9_]{30,}",         "GitHub PAT"),
    (r"\bAKIA[0-9A-Z]{16}\b",                   "AWS access key"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b",              "Google API key"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}",         "Slack token"),
    (r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----", "private key"),
]
FORBIDDEN = re.compile(r"(^|/)(auth\.json|\.credentials\.json|\.env)$|\.(pem|p12|pfx)$")

files = subprocess.run(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
    capture_output=True, text=True).stdout.split()
hits = 0
for f in files:
    if os.path.normpath(f) == SELF:
        continue
    if FORBIDDEN.search(f):
        fail(f"V5 커밋되면 안 되는 파일: {f}"); hits += 1
        continue
    try:
        body = open(f, encoding="utf-8", errors="ignore").read()
    except OSError:
        continue
    for pat, label in PATTERNS:
        if re.search(pat, body):
            fail(f"V5 {f}: {label} 형태의 값이 있다"); hits += 1
if not hits:
    ok(f"V5 비밀 스캔 ({len(files)}개 파일)")

# ---- V6 size / binary -----------------------------------------------------
LIMIT = 1_048_576
heavy = []
for f in files:
    try:
        if os.path.getsize(f) > LIMIT:
            heavy.append(f"{f} ({os.path.getsize(f)//1024}KB)")
        elif b"\0" in open(f, "rb").read(8192):
            heavy.append(f"{f} (바이너리)")
    except OSError:
        pass
if heavy:
    fail("V6 텍스트가 아니거나 1MB를 넘는 파일: " + ", ".join(heavy))
else:
    ok("V6 파일 크기·형식")

# ---- V9 remote refs (opt-in) ---------------------------------------------
if online:
    for p in plugins:
        src = p.get("source")
        if not isinstance(src, dict):
            continue
        url, ref = src.get("url", ""), src.get("ref")
        if not ref:
            continue
        r = subprocess.run(["git", "ls-remote", "--heads", "--tags", url, ref],
                           capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            fail(f"V9 [{p.get('name')}] 원격에 ref '{ref}'가 없다: {url}")
        else:
            ok(f"V9 [{p.get('name')}] {ref} @ {r.stdout.split()[0][:12]}")

sys.exit(1 if bad else 0)
PYEOF

printf '\n'
if [ "$FAILED" -eq 0 ]; then
  printf '\033[32m검증 통과\033[0m\n\n'
else
  printf '\033[31m검증 실패\033[0m\n\n'
  exit 1
fi
