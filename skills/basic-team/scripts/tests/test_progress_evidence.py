import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import progress_evidence as ev

class EvidenceTests(unittest.TestCase):
    def test_immutable(self):
        records = [{'id':'a','value':1}]
        self.assertEqual(ev.append(records, records), records)
        with self.assertRaises(ValueError): ev.append(records, [{'id':'a','value':2}])
        with self.assertRaises(ValueError): ev.append(records, None)

    def test_no_derived_input(self):
        for patch in ({'_view':{}}, {'agents':[{'id':'a','status':'통과'}]}, {'gates':{'verdicts':{}}}):
            with self.assertRaises(ValueError): ev.check_input(patch)

    def test_report_parser(self):
        self.assertEqual(ev.parse_report('Text\n```json\n{"assignmentId":"a"}\n```')['assignmentId'], 'a')
        for text in ('no json', '{"assignmentId":"a","assignmentId":"b"}', '{"assignmentId":"a"}\n{"assignmentId":"b"}'):
            with self.assertRaises(ValueError): ev.parse_report(text)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        import tempfile, subprocess
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        def git(*args): subprocess.run(['git',*args],cwd=self.root,check=True,capture_output=True)
        git('init'); git('config','user.name','Tests'); git('config','user.email','test@example.invalid')
        (self.root/'src').mkdir(); (self.root/'src/a.py').write_text('old')
        git('add','.'); git('commit','-m','baseline')
        (self.root/'src/a.py').write_text('new')
        self.manifest=ev.snapshot(str(self.root),'HEAD',['src'],[])

    def fixture(self):
        data={'tasks':[],'agents':[],'evidence':[{'id':'manifest','source':'leader_record','sourceRef':None,'observedAt':None,'captured':self.manifest}], 'artifacts':[{'id':'r1','manifestEvidence':'manifest','digest':ev.digest(self.manifest)}], 'assignments':[], 'observations':[], 'assignmentBatches':[{'id':'batch','artifactId':'r1','requiredAssignments':['a-k','a-p']}], 'gates':{'reviewTarget':'r1','reviewBatch':'batch','requiredReviewers':['karpathy','ponytail']}}
        for short,name in [('k','karpathy'),('p','ponytail')]:
            aid='a-'+short; eid='dispatch-'+short
            data['tasks'].append({'id':'t-'+short,'owner':name,'phase':'review','title':name})
            data['agents'].append({'id':name,'name':name,'role':'reviewer','area':'all'})
            data['assignments'].append({'id':aid,'taskId':'t-'+short,'agentId':name,'artifactId':'r1','criteria':[{'id':'correct','target':'src','required':True,'applicable':True}]})
            data['evidence'].append({'id':eid,'source':'host_response','sourceRef':None,'observedAt':None,'captured':{'assignmentId':aid,'hostAgentId':'host-'+short,'accepted':True}})
            data['observations'].append({'id':eid,'kind':'dispatch_accepted','assignmentId':aid,'evidenceId':eid})
        return data

    def publish(self,data):
        import json
        reports={}
        for short in ['k','p']:
            aid='a-'+short; eid='report-'+short; reports[aid]=eid
            report={'assignmentId':aid,'revisionDigest':ev.digest(self.manifest),'verdict':'PASS','criteria':[{'id':'correct','state':'checked','evidence':['src/a.py:1']}],'findings':[],'reportedScope':['src/a.py'],'uncheckedScope':[]}
            data['evidence'].append({'id':eid,'source':'child_report','sourceRef':None,'observedAt':None,'purpose':'review_result','assignmentId':aid,'hostAgentId':'host-'+short,'captured':json.dumps(report)})
        data['reviewRounds']=[{'id':'round','batchId':'batch','artifactId':'r1','requiredAssignments':['a-k','a-p'],'reports':reports}]
        return data

    def test_pending_and_current_pass_then_untracked_invalidates(self):
        data=self.fixture(); view=ev.project(data)
        self.assertFalse(view['verdicts']); self.assertEqual(view['tasks'][0]['label'],'호출 수락'); self.assertIsNone(view['tasks'][0]['observedAt'])
        self.publish(data); self.assertEqual(len(ev.project(data)['verdicts']),2)
        self.assertEqual(ev.project(data)['tasks'][0]['resultEvidenceId'],'report-k')
        (self.root/'src/new.py').write_text('untracked')
        view=ev.project(data); self.assertFalse(view['verdicts']); self.assertTrue(any('REVISION_STALE' in p for p in view['problems']))
        self.assertEqual(len(data['reviewRounds']),1)

    def test_partial_reports_wrong_host_and_missing_criteria_rejected(self):
        import json
        base=self.publish(self.fixture())
        for mutate in [lambda d:d['reviewRounds'][0]['reports'].pop('a-p'), lambda d:d['evidence'][-1].update(hostAgentId='wrong'), lambda d:d['evidence'][-1].update(captured=json.dumps(dict(json.loads(d['evidence'][-1]['captured']),criteria=[]))), lambda d:d.pop('reviewRounds')]:
            data=copy.deepcopy(base); mutate(data)
            with self.assertRaises(ValueError): ev.project(data)

    def test_required_unchecked_and_findings_cannot_pass(self):
        import json
        for change in ({'criteria':[{'id':'correct','state':'unchecked','evidence':[]}]}, {'findings':[{'criterionId':'correct','severity':'required','location':'src/a.py:1','impact':'bug','requiredFix':'fix'}]}):
            data=self.publish(self.fixture()); report=json.loads(data['evidence'][-1]['captured']); report.update(change); data['evidence'][-1]['captured']=json.dumps(report)
            with self.assertRaises(ValueError): ev.project(data)

    def test_snapshot_scopes_exclusions_modification_and_deletion(self):
        (self.root/'other.txt').write_text('unrelated')
        self.assertEqual(self.manifest,ev.snapshot(str(self.root),'HEAD',['src'],[]))
        (self.root/'src/a.py').unlink()
        self.assertEqual(ev.snapshot(str(self.root),'HEAD',['src'],[])['changes'][0]['operation'],'delete')

    def test_dispatch_rebinding_requires_new_assignment(self):
        data=self.fixture(); source=copy.deepcopy(data['evidence'][-1]); source['id']='new'; source['captured']['hostAgentId']='replacement'; data['evidence'].append(source)
        data['observations'].append({'id':'new','kind':'dispatch_accepted','assignmentId':'a-p','evidenceId':'new'})
        with self.assertRaises(ValueError): ev.project(data)

    def test_graph_contains_only_explicit_evidence_relations(self):
        data=self.fixture(); self.assertEqual(ev.project(data)['relations'],[])
        data['relations']=[{'id':'edge','kind':'review_assignment','from':{'type':'artifact','id':'r1'},'to':{'type':'task','id':'t-k'},'assignmentId':'a-k','evidenceId':'dispatch-k'}]
        self.assertEqual(len(ev.project(data)['relations']),1)
        data['relations'][0]['to']['id']='t-p'
        with self.assertRaises(ValueError): ev.project(data)

    def test_current_relations_do_not_reuse_prior_review_batch(self):
        data=self.fixture()
        data['relations']=[{'id':'old-edge','kind':'review_assignment','from':{'type':'artifact','id':'r1'},'to':{'type':'task','id':'t-k'},'assignmentId':'a-k','evidenceId':'dispatch-k'}]
        self.assertEqual(len(ev.project(data)['relations']),1)
        new_assignments=[]
        for assignment in data['assignments']:
            new_assignments.append(dict(assignment,id=assignment['id']+'-new'))
        data['assignments']+=new_assignments
        data['assignmentBatches'].append({'id':'new-batch','artifactId':'r1','requiredAssignments':['a-k-new','a-p-new']})
        data['gates']['reviewBatch']='new-batch'
        self.assertEqual(ev.project(data)['relations'],[])
        self.assertEqual(len(data['relations']),1)

    def test_current_review_task_cannot_be_hidden_by_replacement_or_owner(self):
        data=self.publish(self.fixture())
        data['assignments'].append(dict(data['assignments'][0],id='replacement'))
        task=ev.project(data)['tasks'][0]
        self.assertTrue(task['applicable']); self.assertFalse(task['done'])
        data['tasks'][0]['owner']='other-owner'
        task=ev.project(data)['tasks'][0]
        self.assertTrue(task['applicable']); self.assertFalse(task['done'])
        data['gates'].pop('reviewBatch')
        self.assertTrue(all(t['applicable'] for t in ev.project(data)['tasks']))

    def test_whole_root_scope_is_not_empty_and_prunes_git(self):
        manifest=ev.snapshot(str(self.root),'HEAD',['.'],[])
        self.assertEqual([c['path'] for c in manifest['changes']],['src/a.py'])
        (self.root/'new.txt').write_text('new')
        self.assertEqual([c['path'] for c in ev.snapshot(str(self.root),'HEAD',['.'],[])['changes']],['new.txt','src/a.py'])

    def test_scoped_directory_scan_failure_is_not_a_deletion_manifest(self):
        from unittest.mock import patch
        def failed_walk(root, *, followlinks, onerror):
            onerror(PermissionError('cannot read approved src scope'))
            return []
        with patch('progress_evidence.os.walk', side_effect=failed_walk):
            with self.assertRaises(PermissionError): ev.snapshot(str(self.root),'HEAD',['src'],[])

    def test_review_pass_then_blocked_uses_blocked_label_and_tone(self):
        data=self.publish(self.fixture())
        data['evidence'].append({'id':'review-blocked','source':'child_report','sourceRef':None,'observedAt':None,'captured':{'assignmentId':'a-k','hostAgentId':'host-k','blocker':'required tool failed'}})
        data['observations'].append({'id':'review-blocked','kind':'blocked','assignmentId':'a-k','evidenceId':'review-blocked'})
        view=ev.project(data); task=view['tasks'][0]
        self.assertFalse(task['done']); self.assertEqual(task['status'],'blocked'); self.assertEqual(task['label'],'막힘 보고'); self.assertEqual(task['tone'],'warn'); self.assertEqual(task['label'],'막힘 보고'); self.assertEqual(task['tone'],'warn')
        self.assertEqual(view['verdicts']['karpathy']['verdict'],'PASS')
        self.assertTrue(any(p.startswith('TASK_BLOCKED:') for p in view['problems']))

    def test_glob_scope_reenumerates_new_matching_directory(self):
        scope=['src/pkg*']
        frozen=ev.snapshot(str(self.root),'HEAD',scope,[])
        (self.root/'src/pkg_new').mkdir()
        (self.root/'src/pkg_new/added.py').write_text('added')
        fresh=ev.snapshot(str(self.root),'HEAD',scope,[])
        self.assertNotEqual(frozen,fresh)
        self.assertEqual(fresh['changes'][0]['path'],'src/pkg_new/added.py')

    def test_review_receipts_never_publish_paths_or_extra_outcomes(self):
        for kind in ('dispatch_accepted','queued','unknown','result_received'):
            data=self.fixture()
            evidence=copy.deepcopy(data['evidence'][1]); evidence['id']='leak'; evidence['captured']['reportPath']='/private/reviews/karpathy.txt'
            if kind!='dispatch_accepted': evidence['captured'].pop('accepted')
            data['evidence'].append(evidence)
            data['observations'].append({'id':'leak','kind':kind,'assignmentId':'a-k','evidenceId':'leak'})
            with self.assertRaises(ValueError): ev.project(data)
        for collection in ('evidence','observations','assignments','assignmentBatches'):
            data=self.fixture(); data[collection][0]['reportPath']='/private/review.txt'
            with self.assertRaises(ValueError): ev.project(data)

    def executor(self,data):
        data['tasks'].append({'id':'build','owner':'executor','phase':'implementation','title':'Build'})
        data['agents'].append({'id':'executor','name':'Executor','role':'executor','area':'src'})
        data['assignments'].append({'id':'build-a','taskId':'build','agentId':'executor'})
        for ident,kind,body in [('build-dispatch','dispatch_accepted',{'accepted':True}),('build-result','result_received',{'completed':True,'paths':['src/a.py'],'verification':['test command exit 0']}),('build-stop','terminated',{})]:
            data['evidence'].append({'id':ident,'source':'host_response' if kind!='result_received' else 'child_report','sourceRef':None,'observedAt':None,'captured':dict(body,assignmentId='build-a',hostAgentId='host-build')})
            data['observations'].append({'id':ident,'kind':kind,'assignmentId':'build-a','evidenceId':ident})
        return data

    def test_task_completion_survives_termination_not_replacement(self):
        data=self.executor(self.fixture())
        task=ev.project(data)['tasks'][-1]; self.assertTrue(task['done']); self.assertEqual(task['label'],'종료 관측')
        data['assignments'].append({'id':'build-replacement','taskId':'build','agentId':'executor'})
        self.assertFalse(ev.project(data)['tasks'][-1]['done'])
        data['evidence'][-2]['source']='leader_record'
        with self.assertRaises(ValueError): ev.project(data)

    def test_completed_then_blocked_stays_incomplete_after_termination(self):
        data=self.executor(self.fixture())
        stop=data['observations'].pop()
        data['evidence'].append({'id':'blocked','source':'child_report','sourceRef':None,'observedAt':None,'captured':{'assignmentId':'build-a','hostAgentId':'host-build','blocker':'required test failed'}})
        data['observations'].append({'id':'blocked','kind':'blocked','assignmentId':'build-a','evidenceId':'blocked'})
        self.assertFalse(ev.project(data)['tasks'][-1]['done'])
        data['observations'].append(stop)
        task=ev.project(data)['tasks'][-1]
        self.assertFalse(task['done']); self.assertEqual(task['status'],'blocked'); self.assertEqual(task['label'],'막힘 보고'); self.assertEqual(task['tone'],'warn')

    def complete_fixture(self):
        import progress
        data=self.executor(self.publish(self.fixture()))
        data['tasks'].append({'id':'cleanup','owner':'main','phase':'completion','title':'Leader cleanup'})
        data['evidence'].append({'id':'cleanup-result','source':'leader_record','sourceRef':None,'observedAt':None,'purpose':'leader_task_result','captured':{'taskId':'cleanup','completed':True,'verification':['host close receipts checked']}})
        plan=self.root/'plan.md'; plan.write_text('approved')
        data['_progress']={'schemaVersion':4,'saved_at':'2026-10-11T00:00:00Z','checkpoint':'done','revision':1}
        data['taskPlanRevision']='p1'
        gates=data['gates']; gates.update(planApproved='p1',observationPolicy='invocation-evidence-v2',planReview={'method':'plan','revision':'p1','artifact':str(plan),'sha256':ev.hashlib.sha256(plan.read_bytes()).hexdigest(),'fallbackEvidence':'ralplan unavailable in fixture'},conditionalReviews={n:{'required':False,'reason':'backend fixture'} for n in ('impeccable','e2e')},models={},validation={'revision':'r1','status':'PASS','evidence':'tests exit 0','checks':[{'command':'tests','revision':'r1','exitCode':0,'evidence':'exit 0'}]},evidence={n:{'status':'함','evidence':'verified fixture'} for n in ('tasks','shutdown','cleanup')})
        for name,role in [('planner','planner'),('executor','executor'),('karpathy','reviewer'),('ponytail','reviewer')]:
            launch=progress.spawn_args('codex',role)
            gates['models'][name]={'role':role,'requested':launch['requested']['id'],'invocation':'accepted','invocationArguments':launch['arguments'],'invocationAccepted':True,'invocationEvidence':'host accepted','observed':launch['requested']['id'],'observedEffort':launch['requested']['effort'],'observationEvidence':'host record'}
        data['handoffs']=[{'id':ident,'transition':transition,'round':1,'revision':'r1','outcome':'ready','summary':'verified','evidence':['record'],'next':[],'pending':[]} for ident,transition in [('release','implementation-to-verification'),('done','completion')]]
        return data

    def test_complete_gate_and_compliance_revalidate_same_snapshot(self):
        import progress
        data=self.complete_fixture()
        self.assertEqual(progress.gate_problems(data,'complete'),[])
        self.assertIn('revision r1: karpathy PASS',progress.compliance_table(data))
        # A fresh batch uses new task IDs without deleting immutable history.
        newer=self.publish(self.fixture())
        for task in newer['tasks']: task['id'] += '-new'
        for assignment in newer['assignments']:
            assignment['id'] += '-new'; assignment['taskId'] += '-new'
        for observation in newer['observations']:
            observation['id'] += '-new'; observation['assignmentId'] += '-new'; observation['evidenceId'] += '-new'
        for evidence in newer['evidence'][1:]:
            evidence['id'] += '-new'
            if isinstance(evidence['captured'],dict): evidence['captured']['assignmentId'] += '-new'
            else:
                import json
                report=json.loads(evidence['captured']); report['assignmentId'] += '-new'; evidence['captured']=json.dumps(report); evidence['assignmentId'] += '-new'
        data['tasks'] += newer['tasks']; data['assignments'] += newer['assignments']; data['observations'] += newer['observations']
        data['assignmentBatches'].append({'id':'new-batch','artifactId':'r1','requiredAssignments':['a-k-new','a-p-new']})
        data['evidence'] += newer['evidence'][1:3]
        future_tasks=[t for t in ev.project(data)['tasks'] if t['id'].endswith('-new')]
        self.assertTrue(all(t['applicable'] and not t['done'] for t in future_tasks))
        self.assertIn('TASKS_INCOMPLETE: finish all phase tasks before completion',progress.gate_problems(data,'complete'))
        data['gates']['reviewBatch']='new-batch'
        view=ev.project(data)
        self.assertTrue(all(not t['applicable'] and not t['done'] for t in view['tasks'] if t['id'] in ('t-k','t-p')))
        self.assertIn('TASKS_INCOMPLETE: finish all phase tasks before completion',progress.gate_problems(data,'complete'))
        data['evidence'] += newer['evidence'][3:]
        data['reviewRounds'].append({'id':'new-round','batchId':'new-batch','artifactId':'r1','requiredAssignments':['a-k-new','a-p-new'],'reports':{'a-k-new':'report-k-new','a-p-new':'report-p-new'}})
        self.assertEqual(progress.gate_problems(data,'complete'),[])
        self.assertEqual(len(data['reviewRounds']),2)
        (self.root/'src/new.py').write_text('newly added')
        self.assertTrue(any('REVISION_STALE' in p for p in progress.gate_problems(data,'complete')))
        self.assertNotIn('revision r1: karpathy PASS',progress.compliance_table(data))

    def quiescent_fixture(self):
        data=self.complete_fixture()
        data['tasks'].append({'id':'plan-task','owner':'planner','phase':'planning','title':'Plan'})
        data['agents'].append({'id':'planner','name':'Planner','role':'planner','area':'all'})
        data['assignments'].append({'id':'plan-a','taskId':'plan-task','agentId':'planner'})
        for ident,kind,source,body in [('plan-dispatch','dispatch_accepted','host_response',{'accepted':True}),('plan-result','result_received','child_report',{'completed':True,'paths':[],'verification':['plan reviewed']})]:
            data['evidence'].append({'id':ident,'source':source,'sourceRef':None,'observedAt':None,'captured':dict(body,assignmentId='plan-a',hostAgentId='host-plan')})
            data['observations'].append({'id':ident,'kind':kind,'assignmentId':'plan-a','evidenceId':ident})
        data['gates']['lifecycle']={'host':'codex','mode':'task-quiescence','terminationSupported':False,'terminationRequired':False,'capabilityEvidence':'cap','snapshotEvidence':'inactive'}
        data['gates']['evidence']['shutdown']={'status':'부분','evidence':'termination unavailable; all tracked turns inactive'}
        data['observations']=[o for o in data['observations'] if o['kind']!='terminated']
        data['evidence'].extend([
            {'id':'cap','source':'leader_record','sourceRef':'native tool metadata','observedAt':None,'captured':{'tools':['collaboration.list_agents','collaboration.interrupt_agent'],'terminationSupported':False}},
            {'id':'inactive','source':'host_response','sourceRef':'list_agents response after work reconciled','observedAt':None,'captured':{'agents':[{'hostAgentId':host,'state':state} for host,state in [('host-k','idle'),('host-p','completed'),('host-build','interrupted'),('host-plan','idle')]],'pending':[],'observationsDigest':ev.digest(data['observations'])}}
        ])
        return data

    def test_quiescence_allows_completion_without_claiming_termination(self):
        import progress
        data=self.quiescent_fixture()
        progress.validate(data)
        self.assertEqual(progress.gate_problems(data,'complete'),[])
        # Even an inaccurate manually entered row cannot produce shutdown=done.
        data['gates']['evidence']['shutdown']['status']='함'
        self.assertIn('verification | 부분 | 종료 미확인',progress.compliance_table(data))
        self.assertFalse(any(o['kind']=='terminated' for o in data['observations']))

    def test_quiescence_blocks_missing_active_or_unsupported_evidence(self):
        import progress
        changes=[
            lambda d:d['evidence'][-1]['captured']['agents'][0].update(state='running'),
            lambda d:d['evidence'][-1]['captured']['agents'][0].update(state='unknown'),
            lambda d:d['evidence'][-1]['captured']['agents'].pop(),
            lambda d:d['evidence'][-1]['captured']['agents'][0].update(hostAgentId='wrong'),
            lambda d:d['evidence'][-1]['captured'].update(pending=['background write command still running']),
            lambda d:d['gates']['lifecycle'].update(host='claude'),
            lambda d:d['gates']['lifecycle'].update(terminationRequired=True),
            lambda d:d['gates']['lifecycle'].update(terminationSupported=True),
            lambda d:d['gates']['lifecycle'].update(capabilityEvidence='missing'),
            lambda d:d['evidence'][-2]['captured'].update(tools=[]),
            lambda d:d['evidence'][-1].update(source='leader_record'),
            lambda d:d['evidence'][-1]['captured'].update(observationsDigest='stale'),
            lambda d:d['gates']['models'].update(untracked=dict(d['gates']['models']['planner'])),
        ]
        for change in changes:
            with self.subTest(change=change):
                data=self.quiescent_fixture();change(data)
                self.assertTrue(any(p.startswith('LIFECYCLE_') for p in progress.gate_problems(data,'complete')))

    def test_interrupted_agent_is_not_a_completed_task_and_snapshot_expires(self):
        import progress
        data=self.quiescent_fixture()
        data['observations']=[o for o in data['observations'] if o['id']!='build-result']
        # Refreshing inactivity still cannot replace the missing task result.
        data['evidence'][-1]['captured']['observationsDigest']=ev.digest(data['observations'])
        self.assertIn('TASKS_INCOMPLETE: finish all phase tasks before completion',progress.gate_problems(data,'complete'))
        data=self.quiescent_fixture()
        data['observations'].append({'id':'new-progress','kind':'progress_reported','assignmentId':'plan-a','evidenceId':'plan-result'})
        self.assertTrue(any(p.startswith('LIFECYCLE_STALE:') for p in progress.gate_problems(data,'complete')))

    def test_leader_cleanup_result_cannot_complete_child_or_review_tasks(self):
        record={'id':'leader','source':'leader_record','sourceRef':None,'observedAt':None,'purpose':'leader_task_result','captured':{'taskId':'cleanup','completed':True,'verification':['host cleanup checked']}}
        base=self.fixture(); base['tasks'].append({'id':'cleanup','owner':'main','phase':'completion','title':'Cleanup'})
        data=copy.deepcopy(base); data['evidence'].append(record)
        task=ev.project(data)['tasks'][-1]
        self.assertTrue(task['done']); self.assertIsNone(task['hostAgentId']); self.assertEqual(task['label'],'리더 완료 보고')
        for change in ({'taskId':'t-k'},{'verification':[]},{'completed':'yes'}):
            data=copy.deepcopy(base); invalid=copy.deepcopy(record); invalid['captured'].update(change); data['evidence'].append(invalid)
            with self.assertRaises(ValueError): ev.project(data)
        data=copy.deepcopy(base); invalid=copy.deepcopy(record); invalid['hostAgentId']='fake'; data['evidence'].append(invalid)
        with self.assertRaises(ValueError): ev.project(data)

    def test_report_hash_and_severity(self):
        import json
        data=self.publish(self.fixture()); record=data['evidence'][-1]
        path=self.root/'report.json'; path.write_text(record.pop('captured')); record.update(artifact=str(path),sha256=ev.hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(ev.project(data)['verdicts']),2)
        path.write_text(path.read_text()+' ')
        with self.assertRaises(ValueError): ev.project(data)
        data=self.publish(self.fixture()); report=json.loads(data['evidence'][-1]['captured']); report['findings']=[{'criterionId':'correct','severity':'unknown','location':'src:1','impact':'bug','requiredFix':'fix'}]; data['evidence'][-1]['captured']=json.dumps(report)
        with self.assertRaises(ValueError): ev.project(data)


class V4CliTests(SnapshotTests):
    def call(self,*args,payload=None):
        import subprocess,json
        command=[sys.executable,str(Path(__file__).resolve().parents[1]/'progress.py'),*map(str,args)]
        if payload is not None: command += ['--input','-']
        return subprocess.run(command,cwd=self.root,text=True,capture_output=True,input=json.dumps(payload) if payload is not None else None)

    def test_cli_quiescence_gate_and_partial_shutdown(self):
        import json
        data=self.quiescent_fixture(); data.pop('_progress')
        page=self.root/'docs/inprogress/quiescent.html'
        result=self.call('init',page,'--checkpoint','complete',payload=data)
        self.assertEqual(result.returncode,0,result.stderr)
        result=self.call('gate',page,'--stage','complete')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])
        result=self.call('compliance',page)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('verification | 부분 | 종료 미확인',result.stdout)

    def test_snapshot_git_failure_is_tool_error(self):
        result=self.call('snapshot',payload={'root':str(self.root),'baseline':'missing-reference','scope':['src'],'exclusions':[]})
        self.assertEqual(result.returncode,2); self.assertNotIn('Traceback',result.stderr); self.assertIn('git',result.stderr.lower())

    def test_init_update_status_atomic_rejection(self):
        import json
        page=self.root/'docs/inprogress/run.html'
        result=self.call('init',page,'--checkpoint','start',payload=self.fixture())
        self.assertEqual(result.returncode,0,result.stderr)
        result=self.call('status',page); self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['_view']['tasks'][0]['label'],'호출 수락')
        self.assertEqual(json.loads(result.stdout)['lifecycleObservationsDigest'],ev.digest(self.fixture()['observations']))
        before=page.read_bytes()
        for patch in ({'agents':[{'id':'karpathy','status':'PASS'}]},{'assignments':None},{'gates':None},{'assignmentBatches':None},{'observations':[{'id':'bad','kind':'queued','assignmentId':[],'evidenceId':'dispatch-k'}]},{'gates':{'verdicts':{'karpathy':{'verdict':'PASS'}}}}):
            result=self.call('update',page,'--checkpoint','invalid',payload=patch)
            self.assertEqual(result.returncode,2,result.stderr); self.assertNotIn('Traceback',result.stderr); self.assertEqual(page.read_bytes(),before)
        data=self.publish(self.fixture()); result=self.call('update',page,'--checkpoint','published',payload={'evidence':data['evidence'][-2:],'reviewRounds':data['reviewRounds']})
        self.assertEqual(result.returncode,0,result.stderr)
        result=self.call('status',page); self.assertEqual(len(json.loads(result.stdout)['_view']['verdicts']),2)
        before=page.read_bytes(); result=self.call('update',page,'--checkpoint','conflict',payload={'assignmentBatches':[{'id':'batch','artifactId':'r1','requiredAssignments':['a-k']}]})
        self.assertEqual(result.returncode,2); self.assertEqual(page.read_bytes(),before)

if __name__ == '__main__': unittest.main()
