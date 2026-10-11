"""Schema 4: immutable captured facts and conservative, byte-checked projections."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from datetime import datetime

LISTS = ('evidence', 'observations', 'artifacts', 'assignments', 'relations', 'reviewRounds', 'assignmentBatches')
LABELS = {'queued':'대기', 'dispatch_accepted':'호출 수락', 'progress_reported':'작업 보고 수신', 'result_received':'결과 수신', 'blocked':'막힘', 'terminated':'종료 관측', 'unknown':'미확인'}
LEGACY = 'Legacy schema: statuses and relationships are not evidence-verified; existing renderer is preserved.'


def fail(message):
    raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def append(existing, incoming):
    if not isinstance(incoming, list): fail('immutable records must be arrays; null/deletion is forbidden')
    result = copy.deepcopy(existing)
    by_id = {item['id']:item for item in result}
    for item in incoming:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not item['id']: fail('record needs a nonempty id')
        if item['id'] in by_id:
            if by_id[item['id']] != item: fail(f"immutable record conflict: {item['id']}")
        else:
            result.append(item)
            by_id[item['id']] = item
    return result


def check_update(existing, incoming):
    if 'assignmentBatches' in incoming and not isinstance(incoming['assignmentBatches'],list): fail('assignmentBatches must be an array; null is forbidden')
    dispatched = {o['assignmentId'] for o in existing.get('observations', []) if o['kind']=='dispatch_accepted'}
    for batch in incoming.get('assignmentBatches', []):
        old = next((b for b in existing.get('assignmentBatches',[]) if b['id']==batch.get('id')), None)
        if old is None and dispatched.intersection(batch.get('requiredAssignments', [])):
            fail('new review batch must be frozen before any member dispatch; create new assignments')


def check_input(data):
    if 'gates' in data and not isinstance(data['gates'],dict): fail('gates must be an object')
    if '_view' in data or 'reviews' in data: fail('schema 4 review summaries and _view are derived')
    if 'verdicts' in data.get('gates', {}): fail('schema 4 gates.verdicts are derived from reports')
    for key in ('tasks', 'agents'):
        for item in data.get(key, []):
            if set(item) & {'status','tone','result','reported','observation','dependsOn'}: fail(f'{key}: semantic state is derived from evidence, not caller supplied')


def parse_report(text):
    def pairs(items):
        result = {}
        for k,v in items:
            if k in result: fail('duplicate JSON key in report')
            result[k] = v
        return result
    blocks = re.findall(r'```(?:json)?\s*\n(.*?)```', text, re.S)
    candidates = blocks or [text.strip()]
    if len(candidates) != 1 or (blocks and re.search(r'"assignmentId"\s*:', re.sub(r'```(?:json)?\s*\n.*?```', '', text, flags=re.S))): fail('exactly one structured JSON report required')
    try: result = json.loads(candidates[0], object_pairs_hook=pairs)
    except json.JSONDecodeError as error: fail(f'invalid structured report: {error}')
    if not isinstance(result, dict): fail('report must be an object')
    return result


def snapshot(root, baseline, scope, exclusions):
    root = Path(root).resolve()
    if not scope or not all(isinstance(p,str) and p and not p.startswith('/') and '..' not in Path(p).parts for p in scope + exclusions): fail('scope/exclusions require relative roots or glob patterns')
    resolved = subprocess.check_output(['git','rev-parse',baseline+'^{commit}'], cwd=root, text=True).strip()
    from fnmatch import fnmatch
    def included(p):
        def matches(pattern): return pattern == '.' or p == pattern.rstrip('/') or p.startswith(pattern.rstrip('/')+'/') or fnmatch(p,pattern)
        return any(matches(s) for s in scope) and not any(matches(e) for e in exclusions)
    listing = subprocess.check_output(['git','ls-tree','-r','--name-only','-z',resolved],cwd=root).decode().split('\0')
    inventory = {}
    for p in listing:
        if p and included(p): inventory[p] = hashlib.sha256(subprocess.check_output(['git','show',f'{resolved}:{p}'],cwd=root)).hexdigest()
    current = {}
    prefixes = []
    for pattern in scope:
        parts = re.split(r'[?*\[]', pattern, maxsplit=1)
        prefixes.append(parts[0].rpartition('/')[0] if len(parts) > 1 else pattern.rstrip('/'))
    def visit_directory(p):
        if any(p == e.rstrip('/') or p.startswith(e.rstrip('/')+'/') or fnmatch(p,e) for e in exclusions): return False
        return any(prefix in ('', '.') or p == prefix or p.startswith(prefix+'/') or prefix.startswith(p+'/') for prefix in prefixes)
    def traversal_error(error):
        raise error
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=traversal_error):
        relative = Path(directory).relative_to(root)
        dirs[:] = [d for d in dirs if d != '.git' and visit_directory((relative/d).as_posix())]
        for name in dirs + files:
            file = Path(directory)/name
            p = file.relative_to(root).as_posix()
            if not included(p): continue
            if file.is_symlink(): fail(f'snapshot does not follow symlinks: {p}')
            if file.is_file(): current[p] = hashlib.sha256(file.read_bytes()).hexdigest()
    changes = [{'path':p,'operation':'delete' if p not in current else 'add' if p not in inventory else 'modify','sha256':current.get(p)} for p in sorted(set(inventory)|set(current)) if inventory.get(p) != current.get(p)]
    return {'root':str(root),'baseline':resolved,'scope':scope,'exclusions':exclusions,'baselineInventory':inventory,'changes':changes}


def evidence_body(record):
    if ('captured' in record) == ('artifact' in record): fail('evidence needs exactly one captured body or artifact')
    if 'captured' in record: return record['captured']
    content = Path(record['artifact']).read_bytes()
    if hashlib.sha256(content).hexdigest() != record.get('sha256'): fail(f"evidence hash mismatch: {record['id']}")
    return content.decode()


def validate(data):
    indexes = {}
    fields = {
        'evidence': {'id','source','sourceRef','observedAt','captured','artifact','sha256','purpose','assignmentId','hostAgentId'},
        'observations': {'id','kind','assignmentId','evidenceId'},
        'artifacts': {'id','manifestEvidence','digest'},
        'assignments': {'id','taskId','agentId','artifactId','criteria'},
        'relations': {'id','kind','from','to','evidenceId','assignmentId'},
        'reviewRounds': {'id','batchId','artifactId','requiredAssignments','reports'},
        'assignmentBatches': {'id','artifactId','requiredAssignments'},
    }
    for key in LISTS:
        rows = data.get(key, [])
        append([], rows)
        if any(set(r) - fields[key] for r in rows): fail(f'unknown {key} fields; report outcomes belong only in published report evidence')
        if len({r['id'] for r in rows}) != len(rows): fail(f'duplicate {key} id')
        indexes[key] = {r['id']:r for r in rows}
    evidence = indexes['evidence']; assignments = indexes['assignments']; artifacts = indexes['artifacts']
    tasks = {t['id']:t for t in data.get('tasks', [])}; agents = {a['id']:a for a in data.get('agents', [])}
    bodies = {}
    for eid, record in evidence.items():
        if record.get('purpose') not in (None,'review_result','leader_task_result'): fail('unknown evidence purpose')
        for key in ('assignmentId','hostAgentId'):
            if key in record and (not isinstance(record[key],str) or not record[key]): fail(f'{key} must be a nonempty string')
        if record.get('source') not in ('host_response','child_report','command_result','leader_record'): fail('unknown evidence source')
        if 'sourceRef' not in record or 'observedAt' not in record: fail('sourceRef and observedAt must explicitly record null when unknown')
        if record['observedAt'] is not None:
            if not isinstance(record['observedAt'],str): fail('observedAt must be ISO text or null')
            if datetime.fromisoformat(record['observedAt'].replace('Z','+00:00')).utcoffset() is None: fail('observedAt needs timezone')
        if record.get('sourceRef') is not None and not isinstance(record['sourceRef'], str): fail('sourceRef must be text or null')
        bodies[eid] = evidence_body(record)
        if record.get('purpose') == 'leader_task_result':
            body = bodies[eid]
            if record['source'] != 'leader_record' or set(record)-{'id','source','sourceRef','observedAt','purpose','captured'} or not isinstance(body,dict) or set(body) != {'taskId','completed','verification'}: fail('leader task result requires captured taskId/completed/verification and leader_record source')
            task = tasks.get(body.get('taskId'))
            if not task or task.get('owner') != 'main' or task.get('phase') in ('review','verification') or any(a.get('taskId')==task['id'] for a in assignments.values()): fail('leader task result is only for unassigned main-owned non-review tasks')
            if type(body['completed']) is not bool or not isinstance(body['verification'],list) or not all(isinstance(v,str) and v.strip() for v in body['verification']) or (body['completed'] and not body['verification']): fail('completed leader task requires verification references')
    for aid, artifact in artifacts.items():
        manifest = bodies.get(artifact.get('manifestEvidence'))
        if isinstance(manifest,str): manifest = json.loads(manifest)
        if not isinstance(manifest,dict) or digest(manifest) != artifact.get('digest'): fail(f'invalid manifest digest: {aid}')
        if set(manifest) != {'root','baseline','scope','exclusions','baselineInventory','changes'}: fail('invalid scoped manifest')
    for agent in agents.values():
        if set(agent) & {'status','tone','result','reported','observation','dependsOn'}: fail('agent state must be derived')
    for task in tasks.values():
        if set(task) & {'status','tone','result'}: fail('task state must be derived')
    selected = indexes['assignmentBatches'].get(data.get('gates',{}).get('reviewBatch'),{})
    required_tasks = {assignments[aid]['taskId'] for aid in selected.get('requiredAssignments',[]) if aid in assignments}
    for task in tasks.values():
        chain = {task['id']}; current = task
        while 'supersededBy' in current:
            replacement = current['supersededBy']
            if not isinstance(replacement,str) or replacement not in tasks or replacement in chain: fail('supersededBy must name an existing task without cycles')
            if current['id'] in required_tasks: fail('current required review task cannot be superseded')
            chain.add(replacement); current = tasks[replacement]
    if 'verdicts' in data.get('gates', {}): fail('verdicts must be derived')
    for aid, assignment in assignments.items():
        if assignment.get('taskId') not in tasks or assignment.get('agentId') not in agents: fail('assignment task/agent missing')
        if 'artifactId' in assignment:
            if assignment['artifactId'] not in artifacts: fail('assignment artifact missing')
            criteria = assignment.get('criteria', [])
            if not criteria or len({c['id'] for c in criteria}) != len(criteria): fail('unique frozen criteria required')
            for c in criteria:
                if set(c) - {'id','target','required','applicable','reason'}: fail('unknown frozen criterion fields')
                if type(c.get('required')) is not bool or type(c.get('applicable')) is not bool or not c.get('target'): fail('criterion requires target, required and applicable')
                if not c['applicable'] and not c.get('reason'): fail('not-applicable criterion requires approved reason')
    hosts = {}; latest = {}
    for obs in data.get('observations', []):
        if not isinstance(obs.get('assignmentId'),str) or not isinstance(obs.get('evidenceId'),str): fail('observation assignmentId/evidenceId must be strings')
        assignment = assignments.get(obs.get('assignmentId')); body = bodies.get(obs.get('evidenceId'))
        if not assignment or not isinstance(body,dict) or obs.get('kind') not in LABELS: fail('observation needs assignment and captured structured receipt')
        if body.get('assignmentId') != assignment['id']: fail('observation assignment mismatch')
        if 'artifactId' in assignment:
            allowed = {'assignmentId','hostAgentId','receipt'} | ({'accepted'} if obs['kind']=='dispatch_accepted' else set()) | ({'blocker'} if obs['kind']=='blocked' else set())
            if 'captured' not in evidence[obs['evidenceId']] or set(body)-allowed: fail('review receipt must not expose report outcomes or paths')
            if body.get('receipt') is not None and body['receipt'] is not True: fail('review receipt is boolean, not report text')
            if body.get('hostAgentId') is not None and not isinstance(body['hostAgentId'],str): fail('receipt host identity must be text or null')
            if 'blocker' in body and not isinstance(body['blocker'],str): fail('tool blocker must be text')
        if obs['kind'] == 'result_received' and 'artifactId' not in assignment:
            if evidence[obs['evidenceId']]['source'] != 'child_report' or (body.get('completed') is True and (not isinstance(body.get('paths'), list) or not all(isinstance(p,str) and p for p in body['paths']) or not isinstance(body.get('verification'),list) or not body['verification'] or not all(isinstance(v,str) and v for v in body['verification']))): fail('completed task needs child report paths and verification evidence')
        if obs['kind'] == 'dispatch_accepted':
            if 'artifactId' in assignment and not any(assignment['id'] in b.get('requiredAssignments',[]) for b in indexes['assignmentBatches'].values()): fail('freeze review batch before dispatch')
            if evidence[obs['evidenceId']]['source'] != 'host_response' or body.get('accepted') is not True or not isinstance(body.get('hostAgentId'),str) or not body['hostAgentId']: fail('dispatch requires accepted host response')
            if assignment['id'] in hosts and hosts[assignment['id']] != body['hostAgentId']: fail('accepted host identity cannot change')
            hosts[assignment['id']] = body['hostAgentId']
        elif obs['kind'] not in ('queued','unknown'):
            if not hosts.get(assignment['id']) or body.get('hostAgentId') != hosts[assignment['id']]: fail('observation host mismatch or missing dispatch')
        latest[assignment['id']] = obs
    for bid,batch in indexes['assignmentBatches'].items():
        required = batch.get('requiredAssignments', [])
        if not required or len(set(required)) != len(required): fail('batch requires unique assignments')
        members = [assignments.get(a,{}) for a in required]
        if any(a.get('artifactId') != batch.get('artifactId') for a in members): fail('batch artifact/assignment mismatch')
        reviewers = [a.get('agentId') for a in members]
        if len(set(reviewers)) != len(reviewers) or not {'karpathy','ponytail'} <= set(reviewers): fail('batch requires distinct mandatory reviewers')
    reviews = {}; used_reports = set(); used_batches = set()
    for round_ in data.get('reviewRounds', []):
        batch = indexes['assignmentBatches'].get(round_.get('batchId'))
        if not batch or round_.get('artifactId') != batch['artifactId'] or round_.get('requiredAssignments') != batch['requiredAssignments'] or set(round_.get('reports',{})) != set(batch['requiredAssignments']): fail('publish exactly the frozen complete review batch')
        if batch['id'] in used_batches: fail('one published round per batch')
        used_batches.add(batch['id']); parsed = {}
        for aid,eid in round_['reports'].items():
            assignment = assignments[aid]; source = evidence.get(eid,{})
            if not hosts.get(aid) or source.get('hostAgentId') != hosts[aid] or source.get('assignmentId') != aid or source.get('source') != 'child_report' or source.get('purpose') != 'review_result': fail('review report requires matching captured host/assignment source')
            body = bodies[eid]
            report = parse_report(body if isinstance(body,str) else json.dumps(body))
            if set(report) != {'assignmentId','revisionDigest','verdict','criteria','findings','reportedScope','uncheckedScope'}: fail('structured report fields mismatch')
            if report['assignmentId'] != aid or report['revisionDigest'] != artifacts[assignment['artifactId']]['digest'] or report['verdict'] not in ('PASS','CHANGES_REQUIRED','BLOCKED'): fail('report assignment/revision/verdict mismatch')
            if not isinstance(report['criteria'],list) or not all(isinstance(c,dict) and isinstance(c.get('id'),str) for c in report['criteria']) or not isinstance(report['findings'],list) or not all(isinstance(f,dict) for f in report['findings']): fail('criteria/findings must be record arrays')
            expected = {c['id']:c for c in assignment['criteria'] if c['applicable']}
            criteria = report['criteria']
            if len(criteria) != len(expected) or {c['id'] for c in criteria} != set(expected): fail('criteria must match every applicable obligation exactly once')
            for c in criteria:
                if set(c) - {'id','state','evidence'} or c.get('state') not in ('checked','unchecked'): fail('invalid criterion outcome or reviewer-created waiver')
                if c['state'] == 'checked' and (not isinstance(c.get('evidence'),list) or not c['evidence'] or not all(isinstance(x,str) and x.strip() for x in c['evidence'])): fail('checked criterion needs evidence')
                if report['verdict'] == 'PASS' and expected[c['id']]['required'] and c['state'] != 'checked': fail('PASS cannot omit required checks')
            for finding in report['findings']:
                if finding.get('severity') not in ('required','advisory') or finding.get('criterionId') not in expected or not all(finding.get(k) for k in ('severity','location','impact','requiredFix')): fail('invalid finding')
                if finding['severity'] == 'required' and report['verdict'] == 'PASS': fail('PASS cannot contain unresolved required finding')
            for key in ('reportedScope','uncheckedScope'):
                if not isinstance(report[key],list) or not all(isinstance(x,str) for x in report[key]): fail('reported scopes must be text arrays')
            parsed[assignment['agentId']] = {**report,'revision':assignment['artifactId'],'reportEvidence':eid,'taskId':assignment['taskId'],'agentId':assignment['agentId'],'artifactId':assignment['artifactId']}
            used_reports.add(eid)
        reviews[batch['id']] = parsed
    for eid, record in evidence.items():
        if record.get('purpose') == 'review_result' and eid not in used_reports: fail('unpublished review evidence cannot enter page')
        body = bodies[eid]
        if eid not in used_reports:
            if isinstance(body,str) and re.search(r'"(?:verdict|findings|reportedScope|uncheckedScope)"\s*:',body): fail('partial structured review outcomes forbidden')
            if isinstance(body,dict) and set(body)&{'verdict','findings','criteria','reportedScope','uncheckedScope'}: fail('partial review outcomes forbidden')
            if record.get('assignmentId') in assignments and 'artifactId' in assignments[record['assignmentId']] and record.get('source') == 'child_report' and eid not in {o['evidenceId'] for o in data.get('observations',[])}: fail('review source bodies stay private until full publication')
    for eid, record in evidence.items():
        if record['source'] == 'child_report' and eid not in used_reports:
            body=bodies[eid]
            aid=record.get('assignmentId') or (body.get('assignmentId') if isinstance(body,dict) else None)
            host=record.get('hostAgentId') or (body.get('hostAgentId') if isinstance(body,dict) else None)
            if aid not in assignments or not hosts.get(aid) or host != hosts[aid]: fail('child report source must match accepted assignment host')
            if 'artifactId' in assignments[aid] and (not isinstance(body,dict) or set(body)-{'assignmentId','hostAgentId','receipt','blocker'}): fail('review bodies stay private until full publication')
    for rel in data.get('relations', []):
        kind = rel.get('kind'); src = rel.get('from',{}); dst = rel.get('to',{}); body = bodies.get(rel.get('evidenceId'))
        types = {'prerequisite':('task','task'),'contributes':('task','artifact'),'review_assignment':('artifact','task'),'delivery':('task','task')}
        if set(src) != {'type','id'} or set(dst) != {'type','id'}: fail('relation endpoints require exactly type/id')
        if kind not in types or (src.get('type'),dst.get('type')) != types[kind] or rel.get('evidenceId') not in evidence: fail('invalid relation endpoints/evidence')
        for endpoint in (src,dst):
            if endpoint.get('id') not in (tasks if endpoint['type']=='task' else artifacts): fail('dangling relation endpoint')
        if kind == 'prerequisite':
            if evidence[rel['evidenceId']]['source'] != 'leader_record' or not isinstance(body,dict) or body.get('fromTaskId') != src['id'] or body.get('toTaskId') != dst['id'] or not body.get('planRevision'): fail('prerequisite requires declared plan task endpoints and revision')
        if kind == 'review_assignment':
            a = assignments.get(rel.get('assignmentId'),{})
            if a.get('taskId') != dst['id'] or a.get('artifactId') != src['id'] or not hosts.get(a.get('id')) or not any(o['kind']=='dispatch_accepted' and o['assignmentId']==a['id'] and o['evidenceId']==rel['evidenceId'] for o in data.get('observations',[])): fail('review edge requires exact accepted assignment')
        if kind == 'contributes':
            a = assignments.get(body.get('assignmentId') if isinstance(body,dict) else None,{})
            manifest = bodies[artifacts[dst['id']]['manifestEvidence']]
            if isinstance(manifest,str): manifest=json.loads(manifest)
            if evidence[rel['evidenceId']]['source'] != 'child_report' or not any(o['kind']=='result_received' and o['evidenceId']==rel['evidenceId'] for o in data.get('observations',[])): fail('contribution requires child result receipt')
            if not hosts.get(a.get('id')) or a.get('taskId') != src['id'] or body.get('hostAgentId') != hosts.get(a.get('id')) or body.get('completed') is not True or not body.get('paths') or not set(body['paths']) <= {c['path'] for c in manifest['changes']}: fail('contribution requires completed source-bound output paths in manifest')
        if kind == 'delivery':
            if not isinstance(body,dict) or body.get('state') not in ('sent','acknowledged'): fail('delivery needs captured sent/acknowledged receipt')
            for prefix,endpoint in (('source',src),('destination',dst)):
                a=assignments.get(body.get(prefix+'AssignmentId'),{})
                if a.get('taskId')!=endpoint['id'] or not hosts.get(a.get('id')) or body.get(prefix+'HostAgentId') != hosts[a['id']]: fail('delivery ownership mismatch')
            if body['state']=='acknowledged' and (evidence[rel['evidenceId']]['source']!='child_report' or evidence[rel['evidenceId']].get('hostAgentId')!=body['destinationHostAgentId']): fail('acknowledgement requires recipient source')
    gates=data.get('gates',{})
    if gates.get('reviewTarget') and gates['reviewTarget'] not in artifacts: fail('reviewTarget must select a frozen artifact')
    if gates.get('reviewBatch'):
        batch=indexes['assignmentBatches'].get(gates['reviewBatch'])
        if not batch or batch['artifactId']!=gates.get('reviewTarget') or {assignments[a]['agentId'] for a in batch['requiredAssignments']} != set(gates.get('requiredReviewers',[])): fail('selected batch must match target and requiredReviewers')
    return indexes,bodies,hosts,latest,reviews


def project(data):
    indexes,bodies,hosts,latest,reviews=validate(data)
    problems=[]; target=data.get('gates',{}).get('reviewTarget'); batch=data.get('gates',{}).get('reviewBatch')
    if target:
        manifest=bodies[indexes['artifacts'][target]['manifestEvidence']]
        if isinstance(manifest,str): manifest=json.loads(manifest)
        try:
            fresh=snapshot(manifest['root'],manifest['baseline'],manifest['scope'],manifest['exclusions'])
            if fresh!=manifest: problems.append('REVISION_STALE: scoped membership or bytes changed; freeze a new artifact')
        except (OSError,ValueError,subprocess.SubprocessError) as error: problems.append(f'REVISION_UNVERIFIED: {error}')
    verdicts=reviews.get(batch,{}) if not problems else {}
    current_assignments = set(indexes['assignmentBatches'].get(batch,{}).get('requiredAssignments',[]))
    current_tasks = {indexes['assignments'][aid]['taskId'] for aid in current_assignments}
    batches = data.get('assignmentBatches',[])
    selected_batch_index = next((i for i,b in enumerate(batches) if b['id']==batch), -1)
    labels={'pending':'대기중','in_progress':'진행중','done':'완료'}
    assignment_views=[]
    for assignment in data.get('assignments',[]):
        aid=assignment['id']; obs=latest.get(aid,{}); kind=obs.get('kind','unknown')
        source=indexes['evidence'].get(obs.get('evidenceId'),{})
        results=[o for o in data.get('observations',[]) if o['assignmentId']==aid and o['kind'] in ('result_received','blocked')]
        result=results[-1] if results else {}; body=bodies.get(result.get('evidenceId'),{})
        report=next((r for r in verdicts.values() if r['assignmentId']==aid),None)
        blocked=kind=='blocked' or result.get('kind')=='blocked' or bool(report and report['verdict']=='BLOCKED')
        done=not blocked and (bool(report and report['verdict']=='PASS') or ('artifactId' not in assignment and body.get('completed') is True))
        status='done' if done else 'in_progress' if hosts.get(aid) or kind not in ('queued','unknown') else 'pending'
        blocker=body.get('blocker','') if blocked else ''
        if not isinstance(blocker,str): blocker=''
        if report and report['verdict']!='PASS':
            blocker='; '.join(f['requiredFix'] for f in report['findings'] if f['severity']=='required') or report['verdict']
        detail=body.get('summary') or body.get('result') or ('; '.join(body['verification']) if done and not report else '')
        if not isinstance(detail,str): detail=''
        assignment_views.append({'id':aid,'taskId':assignment['taskId'],'agentId':assignment['agentId'],'status':status,'label':labels[status],'tone':'warn' if blocked or (report and report['verdict']!='PASS') else 'good' if done else 'neutral','done':done,'blocked':blocked,'blocker':blocker,'result':detail,'resultEvidenceId':report['reportEvidence'] if report else result.get('evidenceId'),'hostAgentId':hosts.get(aid),'observedAt':source.get('observedAt'),'evidenceId':obs.get('evidenceId')})
    task_views=[]
    for task in data.get('tasks',[]):
        task_assignments=[a for a in data.get('assignments',[]) if a['taskId']==task['id']]
        owned=[a for a in task_assignments if a['agentId']==task['owner']]
        # Main owns grouped reviews; each reviewer's latest assignment still matters.
        selected=list({a['agentId']:a for a in task_assignments}.values()) if task['owner']=='main' else owned[-1:]
        if task['owner']=='main' and task['id'] in current_tasks:
            selected=[a for a in task_assignments if a['id'] in current_assignments]
        members=[v for v in assignment_views if v['id'] in {a['id'] for a in selected}]
        containing_batches=[i for i,b in enumerate(batches) if any(a['id'] in b['requiredAssignments'] for a in task_assignments)]
        is_review=any('artifactId' in a for a in task_assignments)
        applicable=not task.get('supersededBy') and not (selected_batch_index>=0 and task['id'] not in current_tasks and is_review and containing_batches and all(i<selected_batch_index for i in containing_batches))
        done=bool(members) and all(v['done'] for v in members)
        if is_review and (problems or any(a.get('artifactId')!=target or a['id'] not in current_assignments for a in selected)): done=False
        if task['id'] in current_tasks and not current_assignments.intersection(a['id'] for a in selected): done=False
        blocked=any(v['blocked'] for v in members)
        status='done' if done else 'in_progress' if any(v['status']!='pending' for v in members) else 'pending'
        first=members[-1] if members else {}
        leader_results=[e for e in indexes['evidence'].values() if e.get('purpose')=='leader_task_result' and bodies[e['id']]['taskId']==task['id']]
        if leader_results:
            source=leader_results[-1]; body=bodies[source['id']]; done=body['completed']; status='done' if done else 'in_progress'
            first={'observedAt':source.get('observedAt'),'evidenceId':source['id'],'resultEvidenceId':source['id'],'result':'; '.join(body['verification'])}
        task_views.append({'id':task['id'],'applicable':applicable,'status':status,'label':labels[status],'tone':'warn' if blocked else 'good' if done else 'neutral','done':done,'blocked':blocked,'blocker':'; '.join(v['blocker'] for v in members if v['blocker']),'result':first.get('result',''),'resultEvidenceId':first.get('resultEvidenceId'),'assignmentId':selected[-1]['id'] if len(selected)==1 else None,'assignmentIds':[a['id'] for a in selected],'agentId':task['owner'],'agentIds':[a['agentId'] for a in selected],'hostAgentId':first.get('hostAgentId'),'observedAt':first.get('observedAt'),'evidenceId':first.get('evidenceId')})
    active_ids={aid for t in task_views if t['applicable'] for aid in t['assignmentIds']}
    agent_views=[]
    for agent in data.get('agents',[]):
        members=[v for v in assignment_views if v['id'] in active_ids and v['agentId']==agent['id']]
        status='done' if members and all(v['done'] for v in members) else 'in_progress' if any(v['status']!='pending' for v in members) else 'pending'
        agent_views.append({'id':agent['id'],'status':status,'label':labels[status],'tone':'warn' if any(v['blocked'] for v in members) else 'good' if status=='done' else 'neutral','observedAt':members[-1]['observedAt'] if members else None})
    if not batch or not verdicts: problems.append('REVIEW_PENDING: complete current frozen batch has no applicable published reports')
    problems += [f"TASK_BLOCKED: {t['id']} has an unresolved blocked observation" for t in task_views if t['applicable'] and t['blocked']]
    problems += [f"REVIEW_{r['verdict']}: {name} reported {r['verdict']}" for name,r in verdicts.items() if r['verdict'] != 'PASS']
    relations = [r for r in data.get('relations',[]) if (r['kind'] != 'contributes' or r['to']['id'] == target) and (r['kind'] != 'review_assignment' or r.get('assignmentId') in current_assignments)]
    return {'verifiedAt':datetime.now().astimezone().isoformat(timespec='seconds'),'problems':problems,'tasks':task_views,'assignments':assignment_views,'agents':agent_views,'verdicts':verdicts,'reviews':list(verdicts.values()),'relations':[{**r, **({'deliveryState':bodies[r['evidenceId']]['state']} if r['kind']=='delivery' else {})} for r in relations]}
