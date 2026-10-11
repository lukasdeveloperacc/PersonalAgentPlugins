# Basic-team trials

This harness evaluates the skill; editing the skill does not require launching a trial.
`run.sh` launches a paid Claude run only when explicitly called. It uses a fresh fixture repository,
loads the specified source plugin directory, and never installs or edits global configuration.

```sh
EVAL_INDEX=0 LEADER_EFFORT=max BUDGET=8 TIMEOUT=1800 ./skills/basic-team/evals/run.sh haiku candidate /absolute/plugin/source
python3 skills/basic-team/evals/test_analyze.py
python3 skills/basic-team/evals/test_runner.py
```

`EVAL_INDEX=1` selects the UI case. That case prohibits browser use: button/name/focus checks are
**source-only**, and theme behavior/visual verification remain unchecked. It cannot earn
`validated_completion`. Backend functionality uses fixed harness assertions outside the editable
fixture, separately from any tests the agent writes.

Each run saves `manifest.json`, `stream.jsonl`, `stderr.txt`, and `summary.json`. The manifest records
source commit, dirty status, skill/helper hashes, requested source path (host-loaded path remains unconfirmed), CLI version, leader arguments,
child invocation evidence, budget, start/end time, process exit status, and wrapper stop reason.
The requested plugin path is not host proof of which duplicate skill was resolved. Invocation evidence does not establish the actual child model/effort. Baseline/candidate comparisons
must match the intended hashes and policy; historical runs lacking identity are unverified.

Outcomes are `completed`, `workflow_blocked`, `cancelled`, `timed_out`, `budget_exhausted`,
`runtime_error`, or `unknown`. `completed` requires root success + zero exit + actual successful
complete-gate output, successful Planner/Executor results and matching required review results. Ralplan additionally requires actual Architect APPROVE before Critic dispatch, Critic APPROVE before Executor dispatch, and matching approved-plan revision; the plan fallback requires explicit stored evidence. A background spawn acknowledgement is not a completed result. `workflow_verified` additionally checks
settings, requested source identity, all required calls, intact transcript and the final compliance table.
`validated_completion` additionally requires independently verified functionality. A successful
helper result checks recorded evidence; it is not host proof of lifecycle authority or code quality.
Child terminal results cannot replace the leader final. Spawn roles come from explicit assignment
identifiers, not words inside prompts. Ambiguous/unknown identifiers fail the settings check.

Codex CLI `--json` exists, but the installed CLI's native spawn/result/terminal event schema has not
been confirmed for this harness. `EVAL_HOST=codex` saves a capability-blocked manifest and exits 2
before any live model invocation. Luna is therefore **unverified**; do not report Codex parity.

Timeout/cancellation kills only the process group created by this wrapper. Detached native teammates
may outlive it; the manifest and BLOCKED outcome do not prove native shutdown. Inspect host evidence
before another trial if cancellation left workers active. No runtime outcome is inferred from a
keyword, an interrupted score, or a missing terminal event.
