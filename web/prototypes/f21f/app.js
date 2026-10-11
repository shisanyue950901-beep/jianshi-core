/* F2.1 G1-F offline UI only. Never infer authentication from mock actor selector.
 * Only textContent/createElement and memory changes; no HTML injection, upload or network.
 */
(function() {
  "use strict";
  const {SyntheticCMS,roles} = window.F21F_MODEL;
  const cms=new SyntheticCMS();
  let currentId="SYNTHETIC_G1F_01";
  let view="editor";
  const $=(id)=>document.getElementById(id);
  const labels={DRAFT:"草稿",IN_REVIEW:"待审核",APPROVED:"已批准",
    REJECTED:"已驳回",PUBLISHED:"模拟已发布",UNPUBLISHED:"已撤回"};
  const actor=()=>$("actor").value;
  const record=()=>cms.read(currentId);
  const feedback=(message,error=false)=>{
    $("feedback").textContent=message;
    $("feedback").style.borderColor=error?"#e3b2a6":"#dcd4f7";
    $("feedback").style.background=error?"#fff0ec":"#f3f0ff";
  };
  function element(tag,text,className) {
    const e=document.createElement(tag);
    if(text!==undefined)e.textContent=String(text);
    if(className)e.className=className;
    return e;
  }
  function renderQueue(){
    const all=cms.list(),key=$("search").value.trim().toLocaleLowerCase(),filter=$("filter").value;
    const visible=all.filter(r=>(filter==="ALL"||r.state===filter) &&
      (!key||(r.title+" "+r.category+" "+r.type).toLocaleLowerCase().includes(key)));
    const container=$("queue-list");
    container.replaceChildren();
    for(const r of visible){
      const button=element("button",undefined,"queue-card");
      button.type="button";
      button.setAttribute("role","option");
      button.setAttribute("aria-selected",String(r.id===currentId));
      button.append(element("span",r.type,"label"),element("strong",r.title),
        element("small",labels[r.state]+" · v"+r.revision+" · "+r.category));
      button.addEventListener("click",()=>{
        currentId=r.id;
        $("preview-output").textContent="点击“纯文本预览”显示当前输入。";
        renderAll();
      });
      container.append(button);
    }
    $("queue-empty").hidden=visible.length!==0;
    $("queue-count").textContent=String(visible.length)+" 条";
    $("metric-all").textContent=String(all.length);
    $("metric-review").textContent=String(all.filter(r=>r.state==="IN_REVIEW").length);
    $("metric-published").textContent=String(all.filter(r=>r.state==="PUBLISHED").length);
    $("metric-events").textContent=String(all.reduce((num,r)=>num+cms.audit(r.id).length,0));
  }
  function renderEditor(){
    const r=record(), editable=roles[actor()]==="EDITOR" && r.author===actor() && r.state==="DRAFT";
    $("title").value=r.title;$("summary").value=r.summary;$("body").value=r.body;
    $("facts").checked=r.factsChecked;$("rights").checked=r.rightsConfirmed;
    for(const id of ["title","summary","body","facts","rights"]){$(id).disabled=!editable;}
    $("save").disabled=!editable;
    $("stale-test").disabled=!editable;
    $("record-id").textContent=r.id;$("record-kind").textContent=r.type;
    $("record-revision").textContent="版本 v"+r.revision;
    $("state").textContent=labels[r.state]||r.state;
    document.querySelectorAll("[data-action]").forEach(btn=>{
      const action=btn.getAttribute("data-action");
      const permitted={
        DRAFT:r.state==="REJECTED" && editable!==true && actor()===r.author && roles[actor()]==="EDITOR",
        IN_REVIEW:(r.state==="DRAFT"||r.state==="UNPUBLISHED") && actor()===r.author && roles[actor()]==="EDITOR",
        APPROVED:r.state==="IN_REVIEW" && roles[actor()]==="REVIEWER" && actor()!==r.author,
        REJECTED:r.state==="IN_REVIEW" && roles[actor()]==="REVIEWER" && actor()!==r.author,
        PUBLISHED:r.state==="APPROVED" && roles[actor()]==="PUBLISHER" && actor()!==r.author,
        UNPUBLISHED:r.state==="PUBLISHED" && roles[actor()]==="PUBLISHER" && actor()!==r.author
      };
      btn.disabled=!permitted[action];
    });
  }
  function renderVersions(){
    const rev=cms.revisions(currentId),from=$("version-from"),to=$("version-to");
    const previousFrom=Number(from.value)||rev[0].revision;
    const previousTo=Number(to.value)||rev[rev.length-1].revision;
    from.replaceChildren();to.replaceChildren();
    for(const r of rev){
      for(const field of [from,to]){
        const opt=element("option","v"+r.revision+" · "+(labels[r.state]||r.state));
        opt.value=String(r.revision);field.append(opt);
      }
    }
    from.value=String(rev.some(r=>r.revision===previousFrom)?previousFrom:rev[0].revision);
    to.value=String(rev.some(r=>r.revision===previousTo)?previousTo:rev[rev.length-1].revision);
    if(from.value===to.value && rev.length>1)from.value=String(rev[0].revision);
    const h=$("version-history");h.replaceChildren();
    for(const r of rev)h.append(element("span","v"+r.revision+" · "+(labels[r.state]||r.state)));
    showComparison();
  }
  function showComparison(){
    const revisions=cms.revisions(currentId);
    const from=revisions.find(r=>r.revision===Number($("version-from").value));
    const to=revisions.find(r=>r.revision===Number($("version-to").value));
    const describe=(r)=>r?
      "状态："+(labels[r.state]||r.state)+"\n标题："+r.title+"\n摘要："+r.summary+
      "\n正文：\n"+r.body+"\n事实核验："+(r.factsChecked?"是":"否")+
      "\n授权确认："+(r.rightsConfirmed?"是":"否"):"暂无版本";
    $("before").textContent=describe(from);$("after").textContent=describe(to);
  }
  function renderMedia(){
    const r=record(),canEdit=r.author===actor() && roles[actor()]==="EDITOR" && r.state==="DRAFT";
    $("license").disabled=!canEdit || r.media.length===0;
    $("scan").disabled=!canEdit || r.media.length===0;
    $("save-media").disabled=!canEdit || r.media.length===0;
    const m=r.media[0];
    $("media-list").textContent=m?
      "合成素材： "+m.name+"\n类别： "+m.type+"\n版权： "+m.license+"\n扫描： "+m.scan+
      "\n没有实际文件、对象存储或有效授权证明。":"没有关联素材，可继续编辑该合成文本。";
    $("license").value=m?m.license:"UNKNOWN";
    $("scan").value=m?m.scan:"PENDING";
  }
  function renderAudit(){
    const events=cms.audit(currentId);
    $("audit-count").textContent=events.length+" 条";
    $("audit-empty").hidden=events.length!==0;
    const tbody=$("audit-rows");tbody.replaceChildren();
    for(const e of events){
      const tr=document.createElement("tr");
      for(const cell of [e.seq,e.actor,e.action,"v"+e.revision,labels[e.state]||e.state])
        tr.append(element("td",cell));
      tbody.append(tr);
    }
  }
  function showView(name){
    view=name;
    for(const id of ["editor","versions","rights","audit"]) {
      $("view-"+id).hidden=id!==name;
    }
    document.querySelectorAll("[data-view]").forEach(btn=>{
      const yes=btn.getAttribute("data-view")===name;
      btn.classList.toggle("active",yes);
      if(yes)btn.setAttribute("aria-current","page");
      else btn.removeAttribute("aria-current");
    });
  }
  function renderAll(){
    renderQueue();renderEditor();renderVersions();renderMedia();renderAudit();showView(view);
  }
  function attempt(operation,success){
    try{
      operation();
      feedback(success);
      renderAll();
    }catch(e){
      feedback("操作被拒绝： "+(e.code||"INVALID_OPERATION")+"。未更新模拟审核状态。",true);
      renderAll();
    }
  }
  $("save").addEventListener("click",()=>{
    const r=record();
    attempt(()=>cms.edit(currentId,actor(),r.revision,{
      title:$("title").value,summary:$("summary").value,body:$("body").value,
      factsChecked:$("facts").checked,rightsConfirmed:$("rights").checked
    }),"本地草稿已保存为新版本；没有发送任何数据。");
  });
  $("preview").addEventListener("click",()=>{
    $("preview-output").textContent=
      "标题："+$("title").value+"\n摘要："+$("summary").value+"\n\n"+$("body").value;
    feedback("纯文本预览已刷新。HTML 和脚本不会被执行。");
  });
  $("stale-test").addEventListener("click",()=>{
    const r=record();
    attempt(()=>cms.edit(currentId,actor(),r.revision-1,{title:r.title}),
      "意外接受旧版本（不应发生）");
  });
  $("save-media").addEventListener("click",()=>{
    const r=record();
    attempt(()=>cms.edit(currentId,actor(),r.revision,{
      mediaLicense:$("license").value,mediaScan:$("scan").value
    }),"模拟版权和扫描状态已保存到本地新版本。");
  });
  document.querySelectorAll("[data-action]").forEach(btn=>{
    btn.addEventListener("click",()=>{
      const r=record(),next=btn.getAttribute("data-action");
      attempt(()=>cms.transition(currentId,actor(),r.revision,next),
        "完成本地模拟操作："+(labels[next]||next)+"。正式网站没有发布任何内容。");
    });
  });
  $("search").addEventListener("input",renderQueue);
  $("filter").addEventListener("change",renderQueue);
  $("actor").addEventListener("change",()=>{
    renderAll();feedback("已切换模拟身份，仅用于测试角色权限，不代表真实登录。");
  });
  $("version-from").addEventListener("change",showComparison);
  $("version-to").addEventListener("change",showComparison);
  document.querySelectorAll("[data-view]").forEach(btn=>{
    btn.addEventListener("click",()=>showView(btn.getAttribute("data-view")));
  });
  renderAll();
})();
