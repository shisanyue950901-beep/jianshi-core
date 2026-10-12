'use strict';
// Only interacts with relative, synthetic loopback BFF endpoints.
// CSRF is read from same-origin session response and kept in page memory.
let csrf=null,version=null,role=null;
const status=document.querySelector('#session');
const workflow=document.querySelector('#workflow');
const result=document.querySelector('#result');
const controls=Array.from(document.querySelectorAll('button[data-action]'));
function rows(id,values,format){
 const root=document.getElementById(id);root.replaceChildren();
 for(const v of values){const el=document.createElement('li');el.textContent=format(v);root.appendChild(el);}
}
function render(state){
 version=state.version;
 workflow.textContent='合成文章 '+state.document_id+' · '+state.status+' · 修订版 '+state.version;
 rows('revisions',state.revisions,v=>'v'+v.number+' '+v.title+'（版权：'+(v.rights?'已核':'未核')+'，事实：'+(v.facts?'已核':'未核')+'）');
 rows('events',state.events,e=>'v'+e.revision+' '+e.action);
 rows('snapshots',state.snapshots,s=>'v'+s.revision+' '+s.lifecycle);
 controls.forEach(btn=>{const op=btn.dataset.action;
  btn.disabled=!(role==='EDITOR'&&['RESTORE','EDIT','SUBMIT'].includes(op)||
                 role==='REVIEWER'&&['APPROVE','REJECT'].includes(op)||
                 role==='PUBLISHER'&&['PUBLISH','RETRACT'].includes(op));
 });
}
async function readJSON(url){
 const r=await fetch(url,{credentials:'same-origin',cache:'no-store'});
 const j=await r.json();if(!r.ok)throw new Error(j.status||'CMS_NETWORK_REJECTED');return j;
}
async function start(){
 try{
  const session=await readJSON('/qa/api/session');
  if(session.synthetic!==true)throw new Error('CMS_NOT_SYNTHETIC');
  csrf=session.csrf;role=session.role;
  status.textContent='隔离会话已确认 · 合成角色 '+role+'（非真实登录）';
  render(await readJSON('/qa/api/state'));
 }catch(_err){
  csrf=null;role=null;version=null;
  status.textContent='未取得有效隔离会话。正式网站账号不能在此使用。';
  controls.forEach(x=>x.disabled=true);
 }
}
controls.forEach(btn=>btn.addEventListener('click',async()=>{
 if(!csrf||!Number.isInteger(version))return;
 const op=btn.dataset.action,body={
  operation:op,expected_revision:version,request_id:crypto.randomUUID()
 };
 if(op==='RESTORE')body.source_revision=1;
 if(op==='EDIT'){
  body.title=document.getElementById('doc-title').value;
  body.rights_attested=document.getElementById('rights').checked;
  body.facts_attested=document.getElementById('facts').checked;
 }
 controls.forEach(x=>x.disabled=true);
 try{
  const r=await fetch('/qa/api/action',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'content-type':'application/json','x-csrf-token':csrf},
   body:JSON.stringify(body)
  });
  const j=await r.json();
  result.textContent=r.ok?'模拟操作成功 · '+op:'安全拒绝：'+(j.status||'CMS_DENIED');
  if(r.ok)render(j);
  else if(r.status===401)await start();
  else render(await readJSON('/qa/api/state'));
 }catch(_err){result.textContent='网络异常：未确认操作状态，停止继续提交。';}
 finally{if(role&&csrf&&Number.isInteger(version))render(await readJSON('/qa/api/state').catch(()=>({
   document_id:'SYNTHETIC_UNAVAILABLE',status:'NOT_TESTED',version,
   revisions:[],events:[],snapshots:[]
 }))); }
}));
start();
