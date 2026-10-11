// Run with an existing Playwright installation on NODE_PATH; adds no project dependency.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
const template = fs.readFileSync(path.resolve(__dirname, '../../assets/progress-template.html'), 'utf8');
const tag = /(<script type="application\/json" id="progress-data">)([\s\S]*?)(<\/script>)/;
const base = JSON.parse(template.match(tag)[2]);
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'basic-team-browser-'));
const data = {...base, updated:'2026-10-11T15:00:00+09:00', _progress:{schemaVersion:4},
  gates:{reviewTarget:'r2'}, artifacts:[{id:'r2',digest:'fixture-digest',manifestEvidence:'manifest'}],
  evidence:[{id:'manifest',source:'leader_record',sourceRef:null,observedAt:null,captured:{fixture:true}}],
  assignments:[], relations:[], reviewRounds:[], _view:{verifiedAt:'2026-10-11T15:00:00+09:00',problems:[],tasks:[],verdicts:{},relations:[]}};
for (let i=0;i<10;i++) {
  const review=i>=6, agentId='agent-'+i, taskId='task-'+i, evidenceId='evidence-'+i, assignmentId='assignment-'+i;
  data.agents.push({id:agentId,name:(review?'리뷰어 ':'Executor ')+i,role:review?'Reviewer':'Executor',area:'Shared',stage:review?'review':'implementation'});
  data.tasks.push({id:taskId,title:i===0?'공급상품 <img src=x onerror=alert(1)>':(review?'리뷰 작업 ':'구현 작업 ')+i,owner:agentId,phase:review?'검토':'구현'});
  data.assignments.push({id:assignmentId,agentId,taskId,...(review?{artifactId:'r2'}:{})});
  data.evidence.push({id:evidenceId,source:review?'host_response':'child_report',sourceRef:'fixture-'+i,observedAt:null,captured:{assignmentId,hostAgentId:'host-'+i}});
  data._view.tasks.push({id:taskId,assignmentId,agentId,hostAgentId:'host-'+i,evidenceId,observedAt:null,status:'pending',label:review?'호출 수락':'결과 수신',tone:'neutral'});
  data.relations.push({id:'relation-'+i,kind:review?'review_assignment':'contributes',from:review?{type:'artifact',id:'r2'}:{type:'task',id:taskId},to:review?{type:'task',id:taskId}:{type:'artifact',id:'r2'},evidenceId,assignmentId});
}
data._view.relations=data.relations;
function fixture(name, payload) {
  const file=path.join(root,name+'.html');
  fs.writeFileSync(file,template.replace(tag,(_,open,body,close)=>open+JSON.stringify(payload).replaceAll('<','\\u003c')+close));
  return pathToFileURL(file).href;
}
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  try {
    for(const [width,height] of [[1194,801],[390,844]]) {
      const page=await browser.newPage({viewport:{width,height}}),errors=[];
      page.setDefaultTimeout(10000);page.on('pageerror',error=>errors.push(error.message));
      await page.goto(fixture('graph-'+width,data));
      const compact=JSON.parse(JSON.stringify(data));
      compact.summary='전체 검증 중';compact.stage='저장된 관측';
      compact.flow=[{title:'통합 진행 중',body:'오래된 수동 기록'}];
      compact._view.tasks.forEach((task,i)=>Object.assign(task,{status:i<6?'done':'in_progress',label:'결과 수신'}));
      await page.goto(fixture('compact-'+width,compact));
      assert.equal(await page.locator('#stage').innerText(),'진행중');
      assert.match(await page.locator('#summary').innerText(),/현재:.*검토.*4개 진행중/s);
      assert.match(await page.locator('#summary').innerText(),/완료:.*6/s);
      assert.doesNotMatch(await page.locator('#summary').innerText(),/전체 검증 중/);
      assert.equal(await page.getByText('통합 진행 중',{exact:true}).count(),0);
      assert.equal(await page.locator('#tasks .badge').evaluateAll(items=>items.every(el=>['대기중','진행중','완료'].includes(el.textContent))),true);
      assert.equal(await page.locator('#tasks input:checked').count(),6);
      assert.equal(await page.locator('#agent-graph').isVisible(),false);
      await page.screenshot({path:path.join(root,'overview-'+width+'.png'),fullPage:true});
      await page.goto(fixture('graph-'+width,data));
      await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);
      await page.waitForFunction(()=>document.querySelectorAll('.graphedge').length===10&&getComputedStyle(document.querySelector('.graphedge path')).animationName==='none');
      const edges=await page.evaluate(()=>[...document.querySelectorAll('.graphedge')].map(el=>({id:el.dataset.id,kind:el.dataset.kind,from:el.dataset.from,to:el.dataset.to,animation:getComputedStyle(el.querySelector('path')).animationName})));
      assert.equal(edges.filter(e=>e.kind==='contributes').length,6);
      assert.equal(edges.filter(e=>e.kind==='review_assignment').length,4);
      for(const edge of edges) {
        assert.equal(edge.animation,'none');
        assert.ok(edge.kind==='contributes'?edge.to==='artifact:r2':edge.from==='artifact:r2');
      }
      assert.equal(await page.locator('.artifactnode').count(),1);
      assert.equal(await page.locator('.noderelations').count(),11);
      if(width<760)assert.equal(await page.locator('.graphedges').evaluate(el=>getComputedStyle(el).display),'none');
      assert.equal(await page.locator('.relationrecords details').count(),10);
      assert.equal(await page.locator('img').count(),0,'report values must remain text');
      assert.match(await page.locator('.snapshot-note').innerText(),/실시간 상태가 아닙니다/);
      assert.equal(await page.locator('#agent-graph .nodemodel, #agent-graph .nodereport').count(),0,'repeated model/time metadata belongs in task details');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'no horizontal page overflow');
      const first=page.locator('.agentnode').first();
      await first.focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator('dialog').evaluate(el=>el.open),true);
      assert.match(await page.locator('#agent-details').innerText(),/host-0/);
      await page.evaluate(()=>document.querySelector('dialog').addEventListener('close',()=>window.testDialogClosed=true,{once:true}));
      await page.keyboard.press('Escape');
      await page.waitForFunction(()=>window.testDialogClosed&&!document.querySelector('dialog').open);
      assert.equal(await first.evaluate(el=>document.activeElement===el),true,'dialog returns focus');
      await page.locator('.relationrecords summary').first().focus();await page.keyboard.press('Enter');
      await page.waitForFunction(()=>document.querySelector('.relationrecords details').open);
      assert.match(await page.locator('.relationrecords details').first().innerText(),/근거 출처/);
      await page.getByRole('tab',{name:'리뷰와 검증'}).click();
      assert.match(await page.locator('#reviews').innerText(),/전체 리뷰 결과가 아직 없습니다/);
      await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);
      await page.screenshot({path:path.join(root,'graph-'+width+'.png'),fullPage:true});
      assert.deepEqual(errors,[]);
      await page.close();
    }
    const page=await browser.newPage();
    const legacy={...base,_progress:{schemaVersion:3},agents:[
      {id:'a',name:'구현',role:'Executor',area:'Frontend',stage:'implementation',status:'완료',tone:'good'},
      {id:'b',name:'검토',role:'Reviewer',area:'Frontend',stage:'review',status:'재검토 대기',tone:'active',dependsOn:['a']}]};
    await page.goto(fixture('legacy',legacy));await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);
    await page.waitForFunction(()=>document.querySelector('.graphedge'));
    assert.equal(await page.evaluate(()=>getComputedStyle(document.querySelector('.graphedge path')).animationName),'none');
    assert.match(await page.locator('#agents').innerText(),/이전 형식/);
    // A changed target must not display an earlier round's PASS as current.
    const pending=JSON.parse(JSON.stringify(data));pending.reviewRounds=[{id:'round-r1',artifactId:'r1',reports:{old:'old-report'}}];
    await page.goto(fixture('new-target',pending));await page.getByRole('tab',{name:'리뷰와 검증'}).click();
    assert.match(await page.locator('#reviews').innerText(),/전체 리뷰 결과가 아직 없습니다/);
    assert.equal(await page.getByText('통과 보고',{exact:false}).count(),0);
    const excluded=JSON.parse(JSON.stringify(data));
    excluded.assignments[6].criteria=[{id:'backend',target:'Backend API',applicable:false,reason:'Visual review only'}];
    excluded._view.verdicts={'agent-6':{assignmentId:'assignment-6',revision:'r2',verdict:'PASS',criteria:[],findings:[],reportedScope:['UI'],uncheckedScope:[]}};
    await page.goto(fixture('exclusions',excluded));await page.getByRole('tab',{name:'리뷰와 검증'}).click();
    await page.locator('#reviews summary').first().click();
    assert.match(await page.locator('#reviews').innerText(),/사전에 제외한 검토 범위/);
    assert.match(await page.locator('#reviews').innerText(),/backend · Backend API · 제외 이유: Visual review only/);
    const historyTasks=JSON.parse(JSON.stringify(data));
    historyTasks.tasks.push({id:'old-review',title:'이전 차수 검토',owner:'agent-6',phase:'검토'},{id:'cleanup',title:'리더 정리',owner:'main',phase:'정리'});
    historyTasks._view.tasks.push({id:'old-review',applicable:false,status:'pending',label:'이전 차수'},{id:'cleanup',status:'done',label:'리더 완료 보고'});
    await page.goto(fixture('task-history',historyTasks));
    assert.equal(await page.getByText('이전 차수 검토',{exact:true}).count(),0);
    assert.equal(await page.locator('#tasks input:checked').count(),1);
    await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);
    assert.equal(await page.locator('.agentnode').count(),11,'Main cleanup belongs in checklist, not agent graph');
    const terminated=JSON.parse(JSON.stringify(data));
    terminated._view.tasks[0]={...terminated._view.tasks[0],status:'done',label:'종료 관측',resultEvidenceId:'completion-0'};
    terminated.evidence.push({id:'completion-0',source:'child_report',sourceRef:'result-ref',observedAt:null,captured:{completed:true,verification:['test passed']}});
    await page.goto(fixture('completed-terminated',terminated));
    await page.locator('#tasks details').first().evaluate(el=>el.open=true);
    assert.match(await page.locator('#tasks').innerText(),/완료 판단 근거: completion-0/);
    await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);await page.locator('.agentnode').first().click();
    assert.match(await page.locator('#agent-details').innerText(),/작업 결과 · 근거 ID/);
    assert.match(await page.locator('#agent-details').innerText(),/test passed/);
    const grouped=JSON.parse(JSON.stringify(data));
    grouped.tasks[6].owner='main';grouped.tasks.splice(7,1);
    grouped.assignments[7].taskId='task-6';grouped._view.tasks.splice(7,1);
    Object.assign(grouped._view.tasks[6],{status:'in_progress',assignmentId:null,assignmentIds:['assignment-6','assignment-7'],agentIds:['agent-6','agent-7']});
    Object.assign(grouped._view.tasks[0],{status:'in_progress',blocked:true,blocker:'테스트 서버 연결 문제'});
    await page.goto(fixture('grouped-blocked',grouped));
    assert.match(await page.locator('#summary').innerText(),/막힌 일:.*테스트 서버 연결 문제/s);
    assert.match(await page.locator('#tasks').innerText(),/담당: 리뷰어 6, 리뷰어 7/);
    assert.equal(await page.locator('#tasks .badge').evaluateAll(items=>items.every(el=>['대기중','진행중','완료'].includes(el.textContent))),true);
    await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);
    await page.getByRole('button',{name:/리뷰 작업 6/}).click();
    assert.match(await page.locator('#agent-details').innerText(),/assignment-6/);
    assert.match(await page.locator('#agent-details').innerText(),/assignment-7/);
    assert.equal(await page.getByRole('button',{name:/리뷰 작업 6/}).evaluate(el=>el.closest('.graphlane').querySelector('h3').textContent),'리뷰 담당자의 작업');
    // Several sequential tasks assigned to one Executor must not look like new agents.
    const reused=JSON.parse(JSON.stringify(data));
    reused.tasks.push({id:'verify',title:'전체 검사 실행',owner:'agent-0',phase:'검증'});
    reused.assignments.push({id:'verify-assignment',agentId:'agent-0',taskId:'verify'});
    reused._view.tasks.push({id:'verify',assignmentId:'verify-assignment',agentId:'agent-0',status:'in_progress'});
    reused._view.agents=reused.agents.map(agent=>({id:agent.id,status:agent.id==='agent-0'?'in_progress':'pending'}));
    await page.goto(fixture('reused-executor',reused));await page.getByRole('tab',{name:'에이전트 진행'}).click();
    assert.equal(await page.locator('#agent-roster li').count(),10,'one row per agent, not per assignment');
    assert.match(await page.locator('#agent-roster').innerText(),/등록된 담당자 10명 · 현재 작업 11개/);
    assert.match(await page.locator('#agent-roster li').first().innerText(),/진행중.*Executor 0/s);
    assert.equal(await page.locator('#agent-graph').isVisible(),false);
    assert.equal(await page.locator('#agent-roster .badge').evaluateAll(items=>items.every(el=>['대기중','진행중','완료'].includes(el.textContent))),true);
    const delivery=JSON.parse(JSON.stringify(data));
    for(const state of ['sent','acknowledged'])delivery._view.relations.push({id:state,kind:'delivery',deliveryState:state,from:{type:'task',id:'task-0'},to:{type:'task',id:'task-1'},evidenceId:'evidence-0'});
    await page.goto(fixture('delivery',delivery));await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);
    assert.match(await page.locator('[data-relation-id=sent] summary').innerText(),/전송 수락 · 수신 미확인/);
    assert.match(await page.locator('[data-relation-id=acknowledged] summary').innerText(),/수신 확인 · 보고/);
    if(process.argv[2]){
      await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
      const saved=await page.locator('#progress-data').textContent(),actual=JSON.parse(saved);
      assert.equal(actual._progress.schemaVersion,4);assert.ok(actual._view);
      await page.getByRole('tab',{name:'에이전트 진행'}).click();await page.locator('#agent-evidence').evaluate(el=>el.open=true);
      const current=(actual._view.relations||[]).filter(r=>r.from.type!=='artifact'||r.from.id===actual.gates.reviewTarget).filter(r=>r.to.type!=='artifact'||r.to.id===actual.gates.reviewTarget);
      await page.waitForFunction(count=>document.querySelectorAll('.graphedge').length===count,current.length);
      await page.getByRole('tab',{name:'리뷰와 검증'}).click();
      for(const report of Object.values(actual._view.verdicts||{}))assert.match(await page.locator('#reviews').innerText(),report.verdict==='PASS'?/통과 보고/:report.verdict==='CHANGES_REQUIRED'?/수정 필요 보고/:/확인 보류 보고/);
      assert.equal(await page.locator('.error').count(),0);
    }
    await page.close();
    console.log('PASS: explicit 6+4 relationships, static pending state, evidence details, escaping, keyboard/modal, history, legacy; desktop/mobile screenshots: '+root);
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
