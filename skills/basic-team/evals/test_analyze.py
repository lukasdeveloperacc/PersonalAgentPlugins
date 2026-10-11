"""Offline negative transcripts keep interrupted/keyword-only runs out of success."""
import json
import tempfile
import unittest
from pathlib import Path
from analyze import analyze


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        (self.run / "work").mkdir()
        (self.run / "work/util.py").write_text("import re\ndef add(a,b): return a+b\ndef slugify(text): return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')\n")
        self.manifest = {"exit_status": 0, "kind": "backend", "source_commit": "abc", "source_hashes": {"SKILL.md": "hash"}}
        self.events = []

    def score(self):
        (self.run / "manifest.json").write_text(json.dumps(self.manifest))
        (self.run / "stream.jsonl").write_text('\n'.join(json.dumps(e) for e in self.events))
        return analyze(self.run)

    def call(self, ident, name, data, result=None):
        self.events.append({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": ident, "name": name, "input": data}]}})
        if result is not None:
            self.events.append({"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": ident, "content": result}]}})

    def complete(self):
        for name, model, effort in [('planner', 'opus', 'medium'), ('architect', 'opus', 'medium'), ('critic', 'opus', 'medium'), ('executor', 'haiku', 'max'), ('karpathy', 'sonnet', 'high'), ('ponytail', 'sonnet', 'high')]:
            self.call(name, 'Agent', {'name': 'basic_team_' + name, 'model': model, 'effort': effort}, 'Reviewed revision: plan1\nVerdict: APPROVE' if name in ('architect', 'critic') else 'Reviewed revision: rev1\nVerdict: PASS')
        self.call('gate', 'Bash', {'command': 'uv run /source/progress.py gate page.html --stage complete'}, json.dumps({'gate': 'complete', 'ok': True, 'problems': [], 'path': str((self.run / 'work/docs/inprogress/task-progress.html').resolve()), 'reviewTarget': 'rev1', 'progressRevision': 1}))
        page = self.run / 'work/docs/inprogress/task-progress.html'
        page.parent.mkdir(parents=True)
        page.write_text('<script type="application/json" id="progress-data">' + json.dumps({'_progress': {'revision': 1}, 'gates': {'planApproved': 'plan1', 'planReview': {'method': 'ralplan', 'revision': 'plan1', 'reviews': [{'role': r, 'revision': 'plan1', 'verdict': 'APPROVE'} for r in ('architect', 'critic')]}, 'reviewTarget': 'rev1', 'verdicts': {n: {'revision': 'rev1', 'verdict': 'PASS'} for n in ('karpathy', 'ponytail')}}}) + '</script>')
        self.events.append({'type': 'result', 'subtype': 'success', 'result': 'leader final\n' + '| item | 함 | evidence |\n' * 10})

    def test_complete(self):
        self.complete()
        result = self.score()
        self.assertTrue(result['workflow_verified'])
        self.assertTrue(result['product']['passed'])

    def test_v4_requires_structured_transcript_to_match_derived_report(self):
        from unittest.mock import patch
        self.complete()
        reports = {name: {"assignmentId": name + "-a", "revisionDigest": "digest", "verdict": "PASS", "criteria": [], "findings": [], "reportedScope": ["util.py"], "uncheckedScope": []} for name in ("karpathy", "ponytail")}
        for event in self.events:
            if event.get("type") == "user":
                result = event["message"]["content"][0]
                if result.get("tool_use_id") in reports:
                    result["content"] = json.dumps(reports[result["tool_use_id"]])
        page = self.run / "work/docs/inprogress/task-progress.html"
        content = page.read_text().replace('"revision": 1}', '"revision": 1, "schemaVersion": 4}')
        page.write_text(content)
        view = {"verdicts": {name: dict(report, revision="rev1") for name, report in reports.items()}}
        with patch("analyze.progress_evidence.project", return_value=view):
            self.assertTrue(self.score()["workflow_verified"])
            for event in self.events:
                if event.get("type") == "user" and event["message"]["content"][0].get("tool_use_id") == "karpathy":
                    event["message"]["content"][0]["content"] = json.dumps(dict(reports["karpathy"], verdict="CHANGES_REQUIRED"))
            self.assertFalse(self.score()["workflow_verified"])

    def test_keywords_do_not_spawn_reviewers(self):
        self.call('plan', 'Agent', {'name': 'planner', 'prompt': 'karpathy ponytail impeccable', 'model': 'opus', 'effort': 'medium'}, 'done')
        self.assertFalse(self.score()['checks']['mandatory_review_calls_succeeded'])

    def test_child_terminal_never_overwrites_leader(self):
        self.complete()
        self.events.append({'type': 'result', 'parent_tool_use_id': 'karpathy', 'subtype': 'success', 'result': 'child final'})
        self.assertTrue(self.score()['leader_final'].startswith('leader final'))

    def test_timeout_cancel_budget_runtime_unknown(self):
        for stop, status, subtype, expected in [('timed_out', -15, None, 'timed_out'), ('cancelled', -15, None, 'cancelled'), (None, 1, 'error_max_budget_usd', 'budget_exhausted'), (None, 1, None, 'runtime_error'), (None, 0, None, 'unknown')]:
            with self.subTest(expected=expected):
                self.manifest.update(stop_reason=stop, exit_status=status)
                self.events = [{'type': 'result', 'subtype': subtype}] if subtype else []
                self.assertEqual(self.score()['outcome'], expected)

    def test_command_without_receipt_is_not_gate(self):
        self.complete()
        self.events = [e for e in self.events if not (e.get('type') == 'user' and e['message']['content'][0].get('tool_use_id') == 'gate')]
        self.assertFalse(self.score()['workflow_verified'])

    def test_wrong_revision_and_partial_reviews(self):
        self.complete()
        next(e['message']['content'][0] for e in self.events if e.get('type') == 'user' and e['message']['content'][0]['tool_use_id'] == 'karpathy')['content'] = 'Reviewed revision: stale\nVerdict: PASS'
        self.assertFalse(self.score()['workflow_verified'])

    def test_unknown_role_wrong_settings(self):
        self.complete()
        self.call('other', 'Agent', {'name': 'unknown', 'model': 'opus', 'effort': 'medium'}, 'done')
        self.assertFalse(self.score()['workflow_verified'])

    def test_external_oracle_ignores_fake_agent_tests(self):
        (self.run / 'work/util.py').write_text('def add(a,b): return a+b\ndef slugify(text): return "hello-world"')
        (self.run / 'work/test_util.py').write_text('assert True')
        self.assertFalse(self.score()['product']['passed'])

    def test_inert_ui_is_never_runtime_pass(self):
        self.manifest['kind'] = 'ui'
        (self.run / 'work/index.html').write_text('<button>Dark mode</button>')
        result = self.score()['product']
        self.assertEqual(result['level'], 'source-only')
        self.assertIsNone(result['runtime_passed'])
        self.assertFalse(result['checks']['focus_style'])

    def test_gate_wrong_page_or_target(self):
        self.complete()
        receipt = next(e['message']['content'][0] for e in self.events if e.get('type') == 'user' and e['message']['content'][0]['tool_use_id'] == 'gate')
        for key, value in [('path', '/other/page.html'), ('reviewTarget', 'old'), ('progressRevision', 0)]:
            with self.subTest(key=key):
                data = json.loads(receipt['content'])
                original = data[key]
                data[key] = value
                receipt['content'] = json.dumps(data)
                self.assertFalse(self.score()['workflow_verified'])
                data[key] = original
                receipt['content'] = json.dumps(data)

    def test_required_e2e_missing(self):
        self.complete()
        page = self.run / 'work/docs/inprogress/task-progress.html'
        html = page.read_text()
        html = html.replace('"reviewTarget": "rev1"', '"reviewTarget": "rev1", "requiredReviewers": ["karpathy", "ponytail", "e2e"]')
        page.write_text(html)
        self.assertFalse(self.score()['workflow_verified'])

    def test_required_role_missing_or_failed(self):
        self.complete()
        baseline = json.loads(json.dumps(self.events))
        for assigned in ('planner', 'executor', 'architect', 'critic'):
            for failed in (False, True):
                with self.subTest(role=assigned, failed=failed):
                    self.events = json.loads(json.dumps(baseline))
                    if failed:
                        result = next(e['message']['content'][0] for e in self.events if e.get('type') == 'user' and e['message']['content'][0]['tool_use_id'] == assigned)
                        result['is_error'] = True
                    else:
                        self.events = [e for e in self.events if not (e.get('type') in ('assistant', 'user') and any(b.get('id') == assigned or b.get('tool_use_id') == assigned for b in e['message']['content']))]
                    result = self.score()
                    self.assertFalse(result['workflow_verified'])
                    self.assertFalse(result['validated_completion'])

    def test_plan_order_and_revision(self):
        self.complete()
        architect = next(e for e in self.events if e.get('type') == 'user' and e['message']['content'][0]['tool_use_id'] == 'architect')
        architect['message']['content'][0]['content'] = 'Reviewed revision: stale\nVerdict: APPROVE'
        self.assertFalse(self.score()['workflow_verified'])
        architect['message']['content'][0]['content'] = 'Reviewed revision: plan1\nVerdict: APPROVE'
        self.events.remove(architect)
        self.events.insert(next(i for i, e in enumerate(self.events) if e.get('type') == 'user' and e['message']['content'][0]['tool_use_id'] == 'critic') + 1, architect)
        self.assertFalse(self.score()['workflow_verified'])

    def test_background_ack_is_not_approval(self):
        self.complete()
        call = next(e['message']['content'][0] for e in self.events if e.get('type') == 'assistant' and e['message']['content'][0]['id'] == 'architect')
        call['input']['run_in_background'] = True
        self.assertFalse(self.score()['workflow_verified'])

    def test_fallback_requires_explicit_evidence(self):
        self.complete()
        page = self.run / 'work/docs/inprogress/task-progress.html'
        prefix = '<script type="application/json" id="progress-data">'
        data = json.loads(page.read_text()[len(prefix):-len('</script>')])
        data['gates']['planReview'] = {'method': 'plan', 'revision': 'plan1'}
        page.write_text(prefix + json.dumps(data) + '</script>')
        self.assertFalse(self.score()['workflow_verified'])
        data['gates']['planReview']['fallbackEvidence'] = 'ralplan absent from installed catalog'
        page.write_text(prefix + json.dumps(data) + '</script>')
        self.assertTrue(self.score()['workflow_verified'])
        del data['gates']['planReview']['method']
        page.write_text(prefix + json.dumps(data) + '</script>')
        self.assertFalse(self.score()['workflow_verified'])

    def test_malformed_transcript(self):
        self.complete()
        self.score()
        with (self.run / 'stream.jsonl').open('a') as file:
            file.write('\n{"type":')
        self.assertFalse(analyze(self.run)['workflow_verified'])


if __name__ == '__main__':
    unittest.main()
