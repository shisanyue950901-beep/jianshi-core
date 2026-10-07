import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.1/+esm";

const cfg=window.JIANSHI_AUTH_CONFIG||{};
if(cfg.enabled&&cfg.url&&cfg.key){
  const supabase=createClient(cfg.url,cfg.key,{
    auth:{persistSession:true,autoRefreshToken:true,detectSessionInUrl:true}
  });

  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];

  function textNode(tag,value,cls){
    const node=document.createElement(tag);
    if(cls) node.className=cls;
    node.textContent=value==null?"":String(value);
    return node;
  }

  function setStatus(node,message,state){
    if(!node) return;
    node.textContent=message||"";
    if(state) node.dataset.state=state;
    else delete node.dataset.state;
  }

  async function getSession(){
    const result=await supabase.auth.getSession();
    if(result.error) throw result.error;
    return result.data.session;
  }

  function renderEmpty(container,message){
    if(!container) return;
    container.replaceChildren(textNode("p",message,"muted"));
  }

  function renderRows(container,rows,kind){
    if(!container) return;
    container.replaceChildren();
    if(!rows||!rows.length){
      renderEmpty(
        container,
        kind==="alerts"?"还没有提醒。":kind==="saved"?"还没有收藏机会。":"还没有加入观察清单。"
      );
      return;
    }

    rows.forEach((row)=>{
      const wrapper=document.createElement("div");
      wrapper.className="account-list-row";

      const item=document.createElement("a");
      item.className="account-list-item";
      item.href=row.slug?"/opportunity/"+encodeURIComponent(String(row.slug))+"/":"#";
      if(kind==="alerts"&&row.alert_id!=null){
        item.dataset.alertId=String(row.alert_id);
      }

      const main=document.createElement("div");
      main.appendChild(textNode("b",row.headline_zh||row.title||"未命名"));
      if(kind==="alerts"&&row.body_zh){
        main.appendChild(textNode("span",row.body_zh));
      }else if(kind==="watch"){
        main.appendChild(textNode(
          "span",
          "验证提醒 "+(row.alert_on_validation?"开":"关")
          +" · 新证据 "+(row.alert_on_new_evidence?"开":"关")
          +" · 分数阈值 "+Number(row.score_change_threshold||0).toFixed(1)
        ));
      }else if(kind==="saved"){
        main.appendChild(textNode("span",row.category||""));
      }

      let meta="";
      if(kind==="alerts"){
        meta=(row.event_date||"")+" · "+(row.status==="UNREAD"?"未读":"已读");
      }else if(kind==="watch"){
        meta=row.watchlist_name||"我的观察清单";
      }else{
        meta="已收藏";
      }
      item.append(main,textNode("small",meta));
      wrapper.appendChild(item);

      if((kind==="saved"||kind==="watch")&&row.opportunity_id){
        const remove=document.createElement("button");
        remove.type="button";
        remove.className="account-row-remove";
        remove.textContent=kind==="saved"?"取消收藏":"移出观察";
        remove.dataset.removeKind=kind;
        remove.dataset.opportunityId=String(row.opportunity_id);
        wrapper.appendChild(remove);
      }

      container.appendChild(wrapper);
    });
  }

  async function loadSaved(){
    const container=$("[data-saved-list]");
    if(!container) return;
    const result=await supabase.rpc("get_my_saved_opportunities_v01");
    if(result.error){renderEmpty(container,"收藏读取失败，请稍后重试。");return;}
    renderRows(container,result.data||[],"saved");
  }

  async function loadWatch(){
    const container=$("[data-watch-list]");
    if(!container) return;
    const result=await supabase.rpc("get_my_watchlist_items_v01");
    if(result.error){renderEmpty(container,"观察清单读取失败，请稍后重试。");return;}
    renderRows(container,result.data||[],"watch");
  }

  async function loadAlerts(){
    const container=$("[data-alert-list]");
    if(!container) return;
    const result=await supabase.rpc("get_my_alert_events_v01",{p_limit:30});
    if(result.error){renderEmpty(container,"提醒读取失败，请稍后重试。");return;}
    renderRows(container,result.data||[],"alerts");
  }

  function bindAlertRead(){
    document.querySelectorAll("[data-alert-id]").forEach((node)=>{
      node.addEventListener("click",async()=>{
        const id=Number(node.dataset.alertId||0);
        if(!id) return;
        try{
          await supabase.rpc("mark_my_alert_read_v01",{p_alert_id:id});
        }catch(_err){}
      },{once:true});
    });
  }

  function bindRemoveActions(){
    document.querySelectorAll("[data-remove-kind]").forEach((button)=>{
      button.addEventListener("click",async()=>{
        const kind=button.dataset.removeKind;
        const opportunityId=button.dataset.opportunityId;
        if(!opportunityId) return;
        button.disabled=true;
        const fn=kind==="saved"?"unsave_my_opportunity_v01":"unwatch_my_opportunity_v01";
        const result=await supabase.rpc(fn,{p_opportunity_id:opportunityId});
        if(result.error){
          button.disabled=false;
          button.textContent="操作失败";
          return;
        }
        await (kind==="saved"?loadSaved():loadWatch());
        bindRemoveActions();
      },{once:true});
    });
  }

  async function loadPreferences(){
    const form=$("[data-alert-preferences-form]");
    if(!form) return;
    const result=await supabase.rpc("get_my_alert_preferences_v01");
    if(result.error||!result.data||!result.data.length) return;
    const p=result.data[0];
    const inApp=$('input[name="in_app_enabled"]',form);
    const email=$('input[name="email_enabled"]',form);
    const daily=$('input[name="daily_digest_enabled"]',form);
    const weekly=$('input[name="weekly_digest_enabled"]',form);
    if(inApp) inApp.checked=Boolean(p.in_app_enabled);
    if(email) email.checked=Boolean(p.email_enabled);
    if(daily) daily.checked=Boolean(p.daily_digest_enabled);
    if(weekly) weekly.checked=Boolean(p.weekly_digest_enabled);
  }

  function bindPreferenceForm(){
    const form=$("[data-alert-preferences-form]");
    if(!form) return;
    form.addEventListener("submit",async(event)=>{
      event.preventDefault();
      const status=$("[data-preferences-status]",form);
      const button=$('button[type="submit"]',form);
      button.disabled=true;
      setStatus(status,"正在保存…","loading");
      const result=await supabase.rpc("update_my_alert_preferences_v01",{
        p_in_app_enabled:Boolean($('input[name="in_app_enabled"]',form)?.checked),
        p_email_enabled:Boolean($('input[name="email_enabled"]',form)?.checked),
        p_daily_digest_enabled:Boolean($('input[name="daily_digest_enabled"]',form)?.checked),
        p_weekly_digest_enabled:Boolean($('input[name="weekly_digest_enabled"]',form)?.checked)
      });
      button.disabled=false;
      setStatus(status,result.error?"保存失败，请稍后重试。":"提醒偏好已保存。",result.error?"error":"ok");
    });
  }

  function bindClearData(){
    const button=$("[data-clear-my-data]");
    if(!button) return;
    button.addEventListener("click",async()=>{
      const status=$("[data-clear-my-data-status]");
      const confirmed=window.confirm("这会清空你的收藏、观察清单和站内提醒，但不会删除登录账号。确认继续吗？");
      if(!confirmed) return;
      button.disabled=true;
      setStatus(status,"正在清空…","loading");
      const result=await supabase.rpc("clear_my_jianshi_data_v01");
      button.disabled=false;
      if(result.error){
        setStatus(status,"清空失败，请稍后重试。","error");
        return;
      }
      setStatus(status,"收藏、观察和提醒数据已清空。","ok");
      await Promise.all([loadSaved(),loadWatch(),loadAlerts(),loadPreferences()]);
      bindRemoveActions();
      bindAlertRead();
    });
  }

  async function renderAccount(session){
    const loggedOut=$("[data-auth-logged-out]");
    const loggedIn=$("[data-auth-logged-in]");
    const emailNode=$("[data-auth-user-email]");

    if(!session){
      if(loggedOut) loggedOut.hidden=false;
      if(loggedIn) loggedIn.hidden=true;
      return;
    }

    if(loggedOut) loggedOut.hidden=true;
    if(loggedIn) loggedIn.hidden=false;
    if(emailNode) emailNode.textContent=(session.user&&session.user.email)||"";

    const next=new URLSearchParams(location.search).get("next");
    if(next&&next.startsWith("/")&&!next.startsWith("//")&&location.pathname==="/account/"){
      history.replaceState(null,"","/account/");
      location.assign(next);
      return;
    }

    await Promise.all([loadSaved(),loadWatch(),loadAlerts(),loadPreferences()]);
    bindAlertRead();
    bindRemoveActions();
  }

  const form=$("[data-auth-email-form]");
  if(form){
    form.addEventListener("submit",async(event)=>{
      event.preventDefault();
      const status=$("[data-auth-status]",form);
      const button=$('button[type="submit"]',form);
      const input=$('input[name="email"]',form);
      const email=input?input.value.trim():"";
      if(!email) return;

      button.disabled=true;
      setStatus(status,"正在发送登录链接…","loading");
      try{
        const next=new URLSearchParams(location.search).get("next");
        const redirect=new URL("/account/",cfg.site);
        if(next&&next.startsWith("/")&&!next.startsWith("//")){
          redirect.searchParams.set("next",next);
        }
        const result=await supabase.auth.signInWithOtp({
          email:email,
          options:{emailRedirectTo:redirect.toString(),shouldCreateUser:true}
        });
        if(result.error) throw result.error;
        setStatus(status,"登录链接已请求发送，请检查邮箱。","sent");
      }catch(err){
        setStatus(status,(err&&err.message)||"登录邮件发送失败，请稍后重试。","error");
      }finally{
        button.disabled=false;
      }
    });
  }

  const signout=$("[data-auth-signout]");
  if(signout){
    signout.addEventListener("click",async()=>{
      await supabase.auth.signOut();
      location.assign("/");
    });
  }

  async function requireSession(nextPath){
    const session=await getSession();
    if(session) return session;
    const target=new URL("/account/",cfg.site);
    target.searchParams.set("next",nextPath||location.pathname);
    location.assign(target.pathname+target.search);
    return null;
  }

  $$("[data-save-opportunity]").forEach((button)=>{
    button.addEventListener("click",async()=>{
      const panel=button.closest(".account-actions");
      const status=$("[data-account-action-status]",panel);
      const session=await requireSession(location.pathname);
      if(!session) return;

      button.disabled=true;
      setStatus(status,"正在收藏…","loading");
      const result=await supabase.rpc("save_my_opportunity_v01",{
        p_opportunity_id:button.dataset.saveOpportunity
      });
      button.disabled=false;
      setStatus(status,result.error?"收藏失败，请稍后重试。":"已收藏到我的见势。",result.error?"error":"ok");
    });
  });

  $$("[data-watch-opportunity]").forEach((button)=>{
    button.addEventListener("click",async()=>{
      const panel=button.closest(".account-actions");
      const status=$("[data-account-action-status]",panel);
      const session=await requireSession(location.pathname);
      if(!session) return;

      button.disabled=true;
      setStatus(status,"正在加入观察…","loading");

      const result=await supabase.rpc("watch_my_opportunity_v01",{
        p_opportunity_id:button.dataset.watchOpportunity
      });
      button.disabled=false;
      setStatus(status,result.error?"加入观察失败，请稍后重试。":"已加入观察清单。",result.error?"error":"ok");
    });
  });

  bindPreferenceForm();
  bindClearData();

  supabase.auth.onAuthStateChange((_event,session)=>{
    queueMicrotask(()=>renderAccount(session).catch(()=>{}));
  });

  getSession()
    .then(renderAccount)
    .catch(()=>{
      setStatus($("[data-auth-status]"),"账户状态读取失败，请刷新页面。","error");
    });
}
