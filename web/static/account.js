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

  const AUTH_COOLDOWN_MS=60_000;
  const AUTH_COOLDOWN_KEY="jianshi_auth_otp_cooldown_until";

  function authCooldownRemaining(){
    try{
      const until=Number(localStorage.getItem(AUTH_COOLDOWN_KEY)||0);
      return Math.max(0,until-Date.now());
    }catch(_err){
      return 0;
    }
  }

  function setAuthCooldown(){
    try{
      localStorage.setItem(AUTH_COOLDOWN_KEY,String(Date.now()+AUTH_COOLDOWN_MS));
    }catch(_err){}
  }

  // Normal password accounts use Supabase Auth (never store or log passwords).
  // Keep the previous Magic Link alternative behind the same production gate.
  const authPanels=$("[data-auth-panel]");
  const authSwitches=$("[data-auth-switch]");
  // Hidden panels must not retain secrets or trap keyboard focus.
  function clearSensitiveInputs(form){
    if(!form)return;
    $('input[type="password"]',form).forEach((input)=>{input.value="";});
  }
  $("[data-toggle-password]").forEach((button)=>{
    button.addEventListener("click",()=>{
      const input=document.getElementById(button.dataset.togglePassword);
      if(!input)return;
      const showing=input.type==="password";
      input.type=showing?"text":"password";
      button.textContent=showing?"隐藏":"显示";
      button.setAttribute("aria-pressed",String(showing));
      input.focus({preventScroll:true});
    });
  });
  const registerStrength=$("[data-auth-register-form] input[name='password']");
  if(registerStrength){
    const label=$("#register-strength");
    const bar=$("#register-meter-bar");
    registerStrength.addEventListener("input",()=>{
      const value=registerStrength.value;
      const kinds=[/[a-z]/i.test(value),/[0-9]/.test(value),/[^A-Za-z0-9]/.test(value)].filter(Boolean).length;
      const level=!value?0:value.length<8?1:value.length>=12&&kinds>=2?3:2;
      bar.dataset.level=String(level);
      label.textContent=[
        "至少 8 位，建议使用 12 位以上的独立密码。",
        "密码太短，还需至少 8 位。",
        "长度已达标；建议用 12 位以上且不与其他网站重复。",
        "密码长度及字符组合更好；请确保没有在其他网站使用。"
      ][level];
    });
  }
  function showAuthPanel(mode){
    authPanels.forEach((panel)=>{
      const visible=panel.dataset.authPanel===mode;
      if(!visible)clearSensitiveInputs(panel);
      panel.hidden=!visible;
    });
    authSwitches.forEach((button)=>{
      button.setAttribute("aria-pressed",String(button.dataset.authSwitch===mode));
    });
  }
  authSwitches.forEach((button)=>button.addEventListener("click",()=>showAuthPanel(button.dataset.authSwitch)));
  const forgot=$("[data-auth-forgot]");
  if(forgot) forgot.addEventListener("click",()=>showAuthPanel("reset"));
  const back=$("[data-auth-back]");
  if(back) back.addEventListener("click",()=>showAuthPanel("login"));

  function authRedirect(){
    // The dashboard must whitelist this origin as an Auth redirect URL.
    return new URL("/account/",cfg.site).toString();
  }
  function passwordPair(form){
    const input=$('input[name="password"]',form);
    const confirmation=$('input[name="confirm_password"]',form);
    const password=input?.value||"";
    if(password.length<8||password.length>128) return {error:"密码长度应在 8–128 位之间。"};
    if(confirmation && password!==confirmation.value)return {error:"两次输入的密码不一致。"};
    return {password};
  }
  const registerForm=$("[data-auth-register-form]");
  if(registerForm){
    registerForm.addEventListener("submit",async(event)=>{
      event.preventDefault();
      const status=$("[data-auth-register-status]",registerForm);
      const button=$('button[type="submit"]',registerForm);
      const email=$('input[name="email"]',registerForm).value.trim();
      const pass=passwordPair(registerForm);
      if(pass.error){setStatus(status,pass.error,"error");return;}
      if(!$('[name="privacy_consent"]',registerForm)?.checked){
        setStatus(status,"请先阅读并确认隐私政策与必要账户邮件说明。","error");return;
      }
      if(authCooldownRemaining()>0){
        setStatus(status,"邮件刚刚请求过，请稍后再试。","error");
        return;
      }
      button.disabled=true;
      setStatus(status,"正在创建账户…","loading");
      $("[data-auth-verification]").hidden=true;
      try{
        const response=await supabase.auth.signUp({
          email,password:pass.password,
          options:{emailRedirectTo:authRedirect()}
        });
        if(response.error)throw response.error;
        clearSensitiveInputs(registerForm);
        setAuthCooldown();
        if(response.data.session){
          setStatus(status,"账户已创建并登录。","sent");
          await renderAccount(response.data.session);
        }else{
          setStatus(status,"如果该邮箱可以注册，我们已请求发送验证邮件，请检查收件箱和垃圾邮件。","sent");
          $("[data-auth-verification]").hidden=false;
        }
      }catch(_err){
        setStatus(status,"注册未完成，请核对邮箱或稍后重试。","error");
      }finally{button.disabled=false;}
    });
  }

  // Resend does not disclose whether an email already owns an account.
  const resendButton=$("[data-auth-resend]");
  if(resendButton){
    resendButton.addEventListener("click",async()=>{
      const status=$("[data-auth-resend-status]");
      const remaining=authCooldownRemaining();
      if(remaining>0){
        setStatus(status,"请约 "+Math.ceil(remaining/1000)+" 秒后再发送。","error");return;
      }
      const email=$('input[name="email"]',registerForm)?.value.trim();
      if(!email){setStatus(status,"请先填写注册邮箱。","error");return;}
      resendButton.disabled=true;
      setStatus(status,"正在请求验证邮件…","loading");
      try{
        const response=await supabase.auth.resend({
          type:"signup",email,options:{emailRedirectTo:authRedirect()}
        });
        if(response.error)throw response.error;
        setAuthCooldown();
        setStatus(status,"已请求发送。如果该邮箱有待确认的注册，请查收邮件。","sent");
      }catch(_err){
        setStatus(status,"暂时无法发送，请稍后重试。","error");
      }finally{resendButton.disabled=false;}
    });
  }

  const loginForm=$("[data-auth-login-form]");
  if(loginForm){
    loginForm.addEventListener("submit",async(event)=>{
      event.preventDefault();
      const status=$("[data-auth-login-status]",loginForm);
      const button=$('button[type="submit"]',loginForm);
      const email=$('input[name="email"]',loginForm).value.trim();
      const input=$('input[name="password"]',loginForm);
      button.disabled=true;
      setStatus(status,"正在登录…","loading");
      try{
        const response=await supabase.auth.signInWithPassword({email,password:input.value});
        if(response.error)throw response.error;
        clearSensitiveInputs(loginForm);
        setStatus(status,"登录成功。","sent");
        await renderAccount(response.data.session);
      }catch(_err){
        setStatus(status,"邮箱或密码错误，或邮箱尚未验证。","error");
      }finally{button.disabled=false;}
    });
  }

  const resetForm=$("[data-auth-reset-form]");
  if(resetForm){
    resetForm.addEventListener("submit",async(event)=>{
      event.preventDefault();
      const status=$("[data-auth-reset-status]",resetForm);
      const button=$('button[type="submit"]',resetForm);
      if(authCooldownRemaining()>0){
        setStatus(status,"邮件刚刚请求过，请稍后再试。","error");
        return;
      }
      button.disabled=true;
      setStatus(status,"正在请求找回密码邮件…","loading");
      try{
        const email=$('input[name="email"]',resetForm).value.trim();
        const response=await supabase.auth.resetPasswordForEmail(email,{
          redirectTo:authRedirect()
        });
        if(response.error)throw response.error;
        setAuthCooldown();
        setStatus(status,"如果该邮箱已有账户，请检查密码重置邮件。","sent");
      }catch(_err){
        setStatus(status,"重置邮件暂未发送成功，请稍后重试。","error");
      }finally{button.disabled=false;}
    });
  }

  const changeForm=$("[data-auth-change-form]");
  if(changeForm){
    changeForm.addEventListener("submit",async(event)=>{
      event.preventDefault();
      const status=$("[data-auth-change-status]",changeForm);
      const button=$('button[type="submit"]',changeForm);
      const pass=passwordPair(changeForm);
      if(pass.error){setStatus(status,pass.error,"error");return;}
      button.disabled=true;
      setStatus(status,"正在设置新密码…","loading");
      try{
        const response=await supabase.auth.updateUser({password:pass.password});
        if(response.error)throw response.error;
        changeForm.querySelectorAll('input[type="password"]').forEach((el)=>{el.value="";});
        setStatus(status,"密码已更新。","sent");
      }catch(_err){
        setStatus(status,"密码更新失败，请重新登录后重试。","error");
      }finally{button.disabled=false;}
    });
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

      const remaining=authCooldownRemaining();
      if(remaining>0){
        setStatus(status,"登录链接刚刚请求过，请约 "+Math.ceil(remaining/1000)+" 秒后再试。","error");
        return;
      }

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
        setAuthCooldown();
        setStatus(status,"登录链接已请求发送，请检查邮箱。60 秒内请勿重复请求。","sent");
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
      signout.disabled=true;
      try{
        const result=await supabase.auth.signOut();
        if(result.error)throw result.error;
        location.assign("/");
      }catch(_err){
        signout.disabled=false;
        setStatus($("[data-auth-change-status]"),"退出失败，请刷新页面后重试。","error");
      }
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

  supabase.auth.onAuthStateChange((event,session)=>{
    queueMicrotask(()=>{
      renderAccount(session).then(()=>{
        if(event==="PASSWORD_RECOVERY"){
          const status=$("[data-auth-change-status]");
          setStatus(status,"邮箱验证成功，请在这里设置新密码。","sent");
          $("[data-auth-change-form]")?.scrollIntoView({block:"center"});
        }
      }).catch(()=>{});
    });
  });

  getSession()
    .then(renderAccount)
    .catch(()=>{
      setStatus($("[data-auth-status]"),"账户状态读取失败，请刷新页面。","error");
    });
}
