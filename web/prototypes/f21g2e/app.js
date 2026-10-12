(function(){
 'use strict';
 const lib=window.JianShiCmsSimulation;
 if(!lib)return;
 let demo=new lib.Demo();
 const status=document.getElementById('cms-status');
 const revisions=document.getElementById('cms-versions');
 const events=document.getElementById('cms-events');
 const snapshots=document.getElementById('cms-snapshots');
 const notice=document.getElementById('cms-notice');
 const revision=document.getElementById('cms-revision');
 const actions=Array.from(document.querySelectorAll('button[data-action]'));
 function row(container,line){const li=document.createElement('li');li.textContent=line;container.appendChild(li);}
 function repaint(){
  const s=demo.summary();
  status.textContent=s.stateLabel+' · '+s.title;
  revision.textContent='当前修订 v'+s.revision+'；版权重新核验 '+(s.rights?'已模拟完成':'未完成')+'；事实重新核验 '+(s.facts?'已模拟完成':'未完成');
  revisions.replaceChildren();events.replaceChildren();snapshots.replaceChildren();
  s.versions.forEach(v=>row(revisions,'v'+v.rev+' · '+v.title+' · 权利 '+(v.rights?'已核':'待核')));
  s.events.forEach(e=>row(events,'v'+e.rev+' · '+e.op+' · '+(e.actor||'SYNTHETIC_AUTHOR')));
  s.snapshots.forEach(v=>row(snapshots,'v'+v.revision+' · '+v.state));
  if(!s.snapshots.length)row(snapshots,'尚未生成内部模拟快照');
 }
 actions.forEach(button=>button.addEventListener('click',()=>{
  const op=button.dataset.action;
  if(op==='RESET'){demo=new lib.Demo();notice.textContent='已重置全部合成内存状态。';repaint();return;}
  try{const s=demo.apply(op);notice.textContent='模拟操作 '+op+' 成功；当前 v'+s.revision+'。未发送任何请求。';}
  catch(err){notice.textContent='预期安全拒绝：'+(err.code||'UNKNOWN')+'；历史版本未改变。';}
  repaint();
 }));
 repaint();
})();
