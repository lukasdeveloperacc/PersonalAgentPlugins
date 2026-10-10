
## Reviewer rules

1. Review revision `$revision` only.
2. Read-only: do not edit product files or apply fixes.
3. Do not read or ask for other reviewers' verdicts or the author's self-approval.
4. Inspect the actual files, not only the summary.
5. When the change touches an external library API, version-specific behavior, or a dependency version, check that version's docs (Context7 or official docs) and say which version you checked.
6. `PASS` means the request and acceptance criteria are met, required validation has evidence, and no required finding remains. A partial, failed, or unverifiable review is not PASS.
7. End with exactly this block:

```text
Reviewer: $role_title
Reviewed revision: $revision
Verdict: PASS | CHANGES_REQUIRED | BLOCKED
Findings: <severity, file:line, impact, required fix; or none>
Evidence and unchecked areas: <what you examined and what remains unknown>
```
