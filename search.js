document.addEventListener("DOMContentLoaded",()=>{
  const input=document.querySelector("[data-search]");
  if(input){
    const cards=[...document.querySelectorAll("[data-card]")];
    input.addEventListener("input",()=>{
      const q=input.value.trim().toLowerCase();
      cards.forEach(c=>{c.style.display=!q||c.textContent.toLowerCase().includes(q)?"":"none"})
    });
  }

  const params=new URLSearchParams(location.search);
  const state=params.get("newsletter");
  const statusNodes=[...document.querySelectorAll("[data-newsletter-status]")];
  const stateMessages={
    confirmed:"订阅已确认。之后会按计划向你发送见势每日机会。",
    unsubscribed:"已退订，不会再发送每日机会邮件。",
    invalid:"这个确认或退订链接已失效，请重新提交订阅。",
    error:"订阅状态处理失败，请稍后再试。"
  };
  if(state&&stateMessages[state]){
    statusNodes.forEach(n=>{n.textContent=stateMessages[state];n.dataset.state=state});
  }

  document.querySelectorAll("[data-newsletter-form]").forEach(form=>{
    form.addEventListener("submit",async(e)=>{
      e.preventDefault();
      const endpoint=form.dataset.endpoint||"";
      const status=form.querySelector("[data-newsletter-status]");
      const button=form.querySelector('button[type="submit"]');
      const email=form.querySelector('input[name="email"]').value.trim();
      const company=form.querySelector('input[name="company"]').value;
      if(!endpoint){
        status.textContent="订阅接口将在正式站启用。";
        status.dataset.state="error";
        return;
      }
      button.disabled=true;
      status.textContent="正在提交…";
      status.dataset.state="loading";
      try{
        const resp=await fetch(endpoint,{
          method:"POST",
          headers:{"content-type":"application/json"},
          body:JSON.stringify({email,company,source_path:location.pathname})
        });
        const data=await resp.json().catch(()=>({}));
        if(!resp.ok||data.ok===false) throw new Error(data.message||"暂时无法提交，请稍后再试。");
        status.textContent=data.message||"订阅请求已记录。";
        status.dataset.state=data.state||"ok";
        if(["WAITLIST","CHECK_EMAIL","PENDING_CONFIRMATION","ACTIVE"].includes(data.state)) form.reset();
      }catch(err){
        status.textContent=err?.message||"暂时无法提交，请稍后再试。";
        status.dataset.state="error";
      }finally{
        button.disabled=false;
      }
    });
  });
});
