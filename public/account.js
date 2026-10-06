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
      const item=document.createElement("a");
      item.className="account-list-item";
      item.href=row.slug?"/opportunity/"+encodeURIComponent(String(row.slug))+"/":"#";

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
      container.appendChild(item);
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

    await Promise.all([loadSaved(),loadWatch(),loadAlerts()]);
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
      const result=await supabase.from("saved_opportunities").upsert(
        {user_id:session.user.id,opportunity_id:button.dataset.saveOpportunity},
        {onConflict:"user_id,opportunity_id"}
      );
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

      const listResult=await supabase
        .from("watchlists")
        .select("id")
        .eq("is_default",true)
        .limit(1)
        .maybeSingle();

      if(listResult.error||!listResult.data||!listResult.data.id){
        button.disabled=false;
        setStatus(status,"默认观察清单不可用，请稍后重试。","error");
        return;
      }

      const result=await supabase.from("watchlist_items").upsert(
        {watchlist_id:listResult.data.id,opportunity_id:button.dataset.watchOpportunity},
        {onConflict:"watchlist_id,opportunity_id"}
      );
      button.disabled=false;
      setStatus(status,result.error?"加入观察失败，请稍后重试。":"已加入观察清单。",result.error?"error":"ok");
    });
  });

  supabase.auth.onAuthStateChange((_event,session)=>{
    queueMicrotask(()=>renderAccount(session).catch(()=>{}));
  });

  getSession()
    .then(renderAccount)
    .catch(()=>{
      setStatus($("[data-auth-status]"),"账户状态读取失败，请刷新页面。","error");
    });
}
