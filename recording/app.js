const chapters = [
  ["왜 learning loop인가", "모델보다 중요한 것은 학습하는 시스템", "실행 → 평가 → 실패 분석 → 개선 → 재평가", ["기업 지식", "private eval", "운영 trace"]],
  ["계정·네 모델 준비", "대체 모델 없이, 실제 네 모델을 확인", "계정과 토큰 범위는 분리하고 버전과 quota를 고정합니다.", ["계정 검증", "4개 배포", "고정 judge"]],
  ["Foundry IQ", "조직의 기억을 조회 가능한 근거로", "일반 검색 이름표가 아니라 실제 knowledge base를 사용합니다.", ["Index", "Knowledge source", "Knowledge base"]],
  ["Python 에이전트", "코드는 연결하고, 계약은 검증한다", "Microsoft Agent Framework와 Foundry 프로젝트 SDK를 함께 사용합니다.", ["Agent.run()", "모델 교체", "JSON 검증"]],
  ["로컬 실행", "같은 코드로 먼저 작게 확인", "로컬 성공과 hosted 권한 성공은 별개의 확인입니다.", ["readiness", "실제 검색", "실제 모델"]],
  ["Hosted Agent", "소스 ZIP에서 관리형 agent로", "새 버전·instance identity·최소 데이터 접근 권한을 확인합니다.", ["Direct code deploy", "Managed identity", "Immutable version"]],
  ["Baseline·평가", "좋아 보이는 답변과 업무 합격은 다르다", "6문항 × 4모델. native evaluator와 업무 계약을 함께 봅니다.", ["Groundedness", "Relevance", "업무 계약"]],
  ["Trace → 회귀 데이터", "실패를 설명하고 학습 자산으로 남긴다", "점수가 아니라 근거와 trace를 연결해 개선 대상을 찾습니다.", ["실패 요청", "원인 구분", "Lineage"]],
  ["V2 지침·재배포", "측정한 실패에 맞춰 지침을 바꾼다", "적용 시점·실제 문서 ID·근거 없는 질문의 보류를 명시합니다.", ["명시적 기준", "새 버전", "동일 평가"]],
  ["재평가·Holdout", "같은 dev, 처음 쓰는 holdout", "후보를 고정한 뒤 holdout을 열고, 결과로 prompt를 재조정하지 않습니다.", ["24개 재평가", "16개 holdout", "회귀 재검사"]],
  ["Monitor·판단", "HTTP 성공률과 업무 품질을 분리", "모델별 지연·토큰·실패를 보고 운영 승격은 별도로 결정합니다.", ["64개 실제 trace", "비용 신호", "승격 gate"]],
  ["정리·남는 자산", "실습 자원은 정리하고 조직의 학습은 보존", "모델이 바뀌어도 지식·평가·판단·운영 증거는 남습니다.", ["임시 자원 정리", "공유 자원 보존", "Learning loop"]],
];
const sourceByChapter = ["agent","dependencies","knowledge","agent","host","host","evaluation","monitor","v2","dev","monitor","contract"];
const firstStep = ["dependencies","models","knowledge","preflight","local-start","deploy-v1","baseline","monitor-baseline","prompt-v2","improved","monitor-holdout","cleanup-plan"];
let config, state={jobs:{},events:[],results:{}}, chapter=0, view="overview", selectedRow=null, presented=false, sourceRequest=0;
const $ = selector => document.querySelector(selector);
function text(element, value){element.textContent=value}
function node(tag, value, className){const item=document.createElement(tag);if(value!==undefined)item.textContent=value;if(className)item.className=className;return item}
function showChapter(index){
  chapter=index;selectedRow=null;
  const row=chapters[index];
  text($("#eyebrow"),`${String(index+1).padStart(2,"0")} · LEARNING LOOP`);
  text($("#chapter-title"),row[1]);text($("#chapter-description"),row[2]);text($("#chapter-counter"),`${String(index+1).padStart(2,"0")} / 12`);
  document.querySelectorAll("#chapters button").forEach((button,i)=>button.classList.toggle("active",i===index));
  $("#step-select").value=firstStep[index];$("#source-select").value=sourceByChapter[index];
  if(index===9||index===10){$("#result-select").value="improved";$("#trace-select").value="improved"}
  renderOverview();loadSource();renderTerminal();renderResults();renderTrace();
}
function showView(value){view=value;document.querySelectorAll(".panel").forEach(p=>p.classList.toggle("active",p.id===value));document.querySelectorAll(".tabs button").forEach(b=>b.classList.toggle("selected",b.dataset.view===value));if(value==="code")loadSource();if(value==="diff")loadDiff();if(value==="results")renderResults();if(value==="trace")renderTrace()}
function renderOverview(){
  const panel=$("#overview");panel.replaceChildren();const hero=node("div",undefined,"hero");
  hero.append(node("div",chapters[chapter][1],"hero-title"),node("div",chapters[chapter][2],"hero-sub"));
  const flow=node("div",undefined,"flow");
  const items=chapter===2?[["합성 정책","현행 · 과거 · 승인"],["Foundry IQ","검색 계획 · 재정렬"],["근거 문서","id · references · activity"]]:chapter===7?[["실패 답변","평가 row_id"],["실제 trace","operation_Id"],["회귀 데이터","기준 정답 + lineage"]]:chapter===11?[["모델 교체","Sol · Terra · Luna · Astra"],["조직의 자산","지식 · 평가 · 지침"],["다음 개선","운영 증거 + 사람의 판단"]]:[["지식과 기준","Foundry IQ"],["실제 실행","Hosted Agent"],["평가와 관측","Evaluation · Monitor"],["개선과 검증","새 버전 · Holdout"]];
  items.forEach((item,i)=>{if(i)flow.append(node("div","→","arrow"));const box=node("div",undefined,`node ${i===1?"accent":i===items.length-1?"violet":""}`);box.append(node("strong",item[0]),node("small",item[1]));flow.append(box)});
  hero.append(flow);
  if([0,1,3,6,9,10].includes(chapter)){const models=node("div",undefined,"model-grid");[["Sol","gpt-5.6-sol"],["Terra","gpt-5.6-terra"],["Luna","gpt-5.6-luna"],["Astra","gpt-6-astra"]].forEach(m=>{const box=node("div",undefined,"model");box.append(node("strong",m[0]),node("small",m[1]));models.append(box)});hero.append(models)}
  const facts=node("div",undefined,"fact-grid");chapters[chapter][3].forEach((title,i)=>{const box=node("div",undefined,"fact");box.append(node("strong",title),node("span",i===0?"실제 실행과 증거로 확인":i===1?"모델과 독립적으로 보존":"자동 운영 승인과 구분"));facts.append(box)});hero.append(facts);
  const notice=chapter===11?"정리는 녹화 전용 이름에만 적용합니다. 기존 Foundry·Search·App Insights는 유지합니다.":chapter===10?"평가 완료는 운영 합격이 아닙니다. 남은 실패와 작은 표본의 한계를 숨기지 않습니다.":"이 화면은 녹화용 로컬 콘솔입니다. 표시되는 명령과 결과는 실제 Azure CLI / SDK 실행입니다.";
  hero.append(node("div",notice,"notice"));panel.append(hero);
}
async function loadSource(){const request=++sourceRequest,key=$("#source-select").value;const response=await fetch(`/api/source?key=${encodeURIComponent(key)}`);const data=await response.json();if(request!==sourceRequest)return;const pre=$("#source-code");pre.replaceChildren();if(!response.ok){pre.textContent=data.error;return}data.text.split("\n").forEach((line,i)=>{const span=node("span",line||" ","code-line"+(line.trim().startsWith("#")?" comment":""));span.dataset.line=i+1;pre.append(span)});pre.dataset.source=key;$("#code-scroll").scrollTop=0}
async function loadDiff(){for(const key of ["v1","v2"]){const data=await (await fetch(`/api/source?key=${key}`)).json();text($(`#${key}-code`),data.text)}}
function renderTerminal(){
  if(!config)return;const id=$("#step-select").value;const step=config.steps.find(s=>s.id===id);if(!step)return;
  text($("#command-text"),step.command);const job=state.jobs[id];const status=job?.status||"pending";
  const badge=$("#job-status");badge.className=`tag ${status}`;text(badge,{pending:"실행 전",running:"실제 실행 중",completed:"실제 실행 완료",failed:"실패 · 기록 보존"}[status]);
  $("#run-step").disabled=!!state.running||status==="completed"||presented;
  const log=$("#terminal-log"),oldScroll=log.scrollTop;const nearBottom=log.scrollHeight-log.scrollTop-log.clientHeight<100;const lines=state.events.filter(e=>e.step===id&&(!job||e.time>=job.started));log.replaceChildren();
  if(!lines.length)log.append(node("div","아직 실행하지 않았습니다. 성공 결과를 미리 표시하지 않습니다.","line dim"));
  lines.forEach(event=>log.append(node("div",event.text,"line "+(event.kind==="end"?(event.status==="completed"?"good":"bad"):event.kind==="start"?"good":""))));
  if(nearBottom||!presented)log.scrollTop=log.scrollHeight;else log.scrollTop=oldScroll;
  text($("#job-time"),job?`${Math.round((job.ended||Date.now()/1000)-job.started)}초 · 실제 경과`:"");
}
function resultTable(rows){
  const table=node("table");const head=node("tr");["모델","실제 응답","업무 계약 통과","입력 / 출력 토큰","p95 · 요청 내부"].forEach(v=>head.append(node("th",v)));table.append(head);
  ["sol","terra","luna","astra"].forEach(key=>{const selected=rows.filter(row=>row.model_key===key);const pass=selected.filter(row=>row.business_grade?.passed).length;const tr=node("tr");tr.append(node("td",key.toUpperCase()),node("td",`${selected.length}건`));const td=node("td",`${pass} / ${selected.length}`,pass===selected.length&&selected.length?"pass":"fail");const bar=node("div",undefined,"bar"),fill=node("span");fill.style.width=`${selected.length?pass/selected.length*100:0}%`;bar.append(fill);td.append(bar);tr.append(td,node("td",`${selected.reduce((n,r)=>n+(r.input_tokens||0),0).toLocaleString()} / ${selected.reduce((n,r)=>n+(r.output_tokens||0),0).toLocaleString()}`));const times=selected.map(r=>r.latency_seconds).sort((a,b)=>a-b);tr.append(node("td",times.length?`${times[Math.ceil(times.length*.95)-1].toFixed(2)}초`:"실행 전"));table.append(tr)});return table;
}
function renderResults(){
  const content=$("#result-content"),label=$("#result-select").value,data=state.results[label];content.replaceChildren();
  if(!data?.rows){content.append(node("div","아직 이 코호트의 실제 결과가 없습니다.","empty"));return}
  const rows=data.rows,stats=node("div",undefined,"stats");const completed=rows.filter(r=>r.business_grade?.passed).length;
  [["실제 응답",`${rows.length}`,`${label==="holdout"?16:24}개 예상`],["업무 계약 통과",`${completed}/${rows.length}`,"native 평가와 별개"],["Foundry 평가",data.evaluation?.status==="completed"?"완료":data.evaluation?.status||"실행 전","실제 service run"],["확인한 trace",data.telemetry?`${data.telemetry.observed_trace_count}/${data.telemetry.expected_trace_count}`:"대기","sample weight 1"]].forEach(item=>{const box=node("div",undefined,"stat");box.append(node("label",item[0]),node("strong",item[1]),node("small",item[2]));stats.append(box)});content.append(stats,resultTable(rows),node("div","작은 표본의 업무 시스템 비교입니다. HTTP 200, 평가 완료, 운영 품질 합격을 같은 뜻으로 읽지 않습니다.","notice"));
}
function renderTrace(){
  const content=$("#trace-content"),label=$("#trace-select").value,data=state.results[label];content.replaceChildren();
  if(!data?.rows){content.append(node("div","실제 응답 이후 trace를 선택할 수 있습니다.","empty"));return}
  const grid=node("div",undefined,"trace-grid"),list=node("div",undefined,"trace-list"),detail=node("div",undefined,"trace-detail");
  const row=data.rows.find(r=>r.row_id===selectedRow)||data.rows.find(r=>!r.business_grade.passed)||data.rows[0];selectedRow=row.row_id;
  data.rows.forEach(r=>{const button=node("button",`${r.model_key.toUpperCase()} · ${r.case_id} ${r.business_grade.passed?"✓":"검토"}`,r.row_id===selectedRow?"active":"");button.dataset.row=r.row_id;button.onclick=()=>{selectedRow=r.row_id;renderTrace()};list.append(button)});
  detail.append(node("h2",row.row_id),node("div",row.trace_id,"trace-id"));
  const blocks=[["실제 답변",row.answer],["판단 label",row.decision],["실제 인용",JSON.stringify(row.citations)],["검사 결과",Object.entries(row.business_grade.checks).map(([key,ok])=>`${ok?"✓":"✕"} ${key}`).join("  ")]];
  blocks.forEach(([title,value])=>{const box=node("div",undefined,"detail-block");box.append(node("small",title),node("div",value));detail.append(box)});
  const docs=node("div",undefined,"detail-block");docs.append(node("small","검색에서 실제 반환된 문서"));const chips=node("div",undefined,"chips");(row.source_ids||[]).forEach(id=>chips.append(node("span",id)));if(!row.source_ids?.length)chips.append(node("span","근거 0건 · 내용을 만들지 않음"));docs.append(chips);detail.append(docs);
  if(row.regression_source_trace_ids?.length){const lineage=node("div",undefined,"detail-block");lineage.append(node("small","이전 실패에서 재사용한 trace"),node("div",row.regression_source_trace_ids.join("\n"),"trace-id"));detail.append(lineage)}
  grid.append(list,detail);content.append(grid);
}
async function refresh(){try{const response=await fetch("/api/state");if(!response.ok)throw Error(`상태 조회 ${response.status}`);state=await response.json();if(view==="terminal")renderTerminal();if(view==="results")renderResults();if(view==="trace")renderTrace();window.recordingState=state}catch(error){text($("#caption-note"),`오류: ${error.message}`)}}
async function runSelected(){const step=$("#step-select").value;const response=await fetch("/api/run",{method:"POST",headers:{"Content-Type":"application/json","X-Recording-Token":config.token},body:JSON.stringify({step})});const result=await response.json();if(!response.ok){text($("#caption"),result.error);throw Error(result.error)}await refresh()}
async function init(){
  config=await (await fetch("/api/config")).json();
  chapters.forEach((row,index)=>{const button=node("button");button.append(node("span",String(index+1).padStart(2,"0")),node("div",row[0]));button.dataset.chapter=index;button.onclick=()=>showChapter(index);$("#chapters").append(button)});
  config.steps.forEach(step=>{const option=node("option",`${step.chapter} · ${step.title}`);option.value=step.id;$("#step-select").append(option)});
  document.querySelectorAll(".tabs button").forEach(button=>button.onclick=()=>showView(button.dataset.view));
  $("#step-select").onchange=renderTerminal;$("#source-select").onchange=loadSource;$("#run-step").onclick=()=>runSelected().catch(console.error);$("#result-select").onchange=renderResults;$("#trace-select").onchange=()=>{selectedRow=null;renderTrace()};
  showChapter(0);await refresh();setInterval(refresh,1200);
  window.lab={
    chapter:showChapter,view:showView,
    caption:(message,kicker="LEARNING LOOP",note="실제 실행기록 · 대기 구간 편집")=>{text($("#caption"),message);text($("#caption-kicker"),kicker);text($("#caption-note"),note)},
    presentation:(value=true)=>{presented=value;text($("#mode-badge"),value?"실제 실행기록 · 편집 보기":"실제 실행 콘솔");renderTerminal()},
    highlight:(start,end)=>{document.querySelectorAll(".code-line").forEach(line=>line.classList.toggle("mark",Number(line.dataset.line)>=start&&Number(line.dataset.line)<=end));const first=document.querySelector(`.code-line[data-line="${start}"]`);first?.scrollIntoView({block:"center",behavior:"smooth"})},
    row:(id)=>{selectedRow=id;renderTrace()},
    getState:()=>state
  };
  window.recordingReady=true;
}
init().catch(error=>text($("#caption"),`초기화 오류: ${error.message}`));
