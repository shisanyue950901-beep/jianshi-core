/* Staging-only email session smoke. Served only on Cloudflare preview branch.
   The publishable key is public by design. NEVER add a Supabase secret/service key. */
'use strict';
const AUTH_ROOT='https://apuibjhxinumxbfnqlkp.supabase.co';
const PUBLIC_KEY='sb_publishable_u1D2ab2cvdYqv0aYw2VF4w_4lTUDO2b';
// Only compare a one-way digest in the public staging preview; never publish test mailbox addresses.
const ALLOWED_ACCOUNT_HASHES=Object.freeze({
  'ff4b0c0ba542821f637b175bcfc06b16c91a8b91c13a6b7f9b48e64ac3a66c7a':'A',
  'd5dfd6daa5df559060648eebd051e4f77758917e76663933813fba5e1fd3491f':'B'
});
async function sha256hex(text){
  const bytes=new TextEncoder().encode(text);
  const hash=await crypto.subtle.digest('SHA-256',bytes);
  return [...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('');
}
const STORE='jianshi-staging-auth-smoke-v1';
const base='/_qa/staging-auth/';
const state=document.querySelector('#state');
const logoutBtn=document.querySelector('#logout');
const auditBtn=document.querySelector('#audit');
const auditResult=document.querySelector('#audit-result');
function display(value,kind='info'){state.textContent=value;state.dataset.kind=kind;}
function forget(){try{sessionStorage.removeItem(STORE);}catch(_err){}}
function remember(v){try{sessionStorage.setItem(STORE,JSON.stringify(v));}catch(_err){}}
function stored(){try{return JSON.parse(sessionStorage.getItem(STORE)||'null');}catch(_err){return null;}}
function validShape(v){return v&&typeof v.access_token==='string'&&v.access_token.length>20&&v.access_token.length<8192&&typeof v.refresh_token==='string'&&v.refresh_token.length<8192;}
const params=new URLSearchParams(location.hash.startsWith('#')?location.hash.slice(1):'');
const err=params.get('error')||params.get('error_code');
const candidate={access_token:params.get('access_token')||'',refresh_token:params.get('refresh_token')||''};
// Strip tokens synchronously, before any network action; URLs, history, page content, and logs must not disclose tokens.
if(location.hash||location.search)history.replaceState(null,'',base);
if(validShape(candidate))remember(candidate);
if(err&&!validShape(candidate)){forget();display('验证链接返回错误；请申请新的登录邮件。','error');}
const headers=(token)=>({'apikey':PUBLIC_KEY,'authorization':'Bearer '+token});
async function refreshSession(v){
  const reply=await fetch(AUTH_ROOT+'/auth/v1/token?grant_type=refresh_token',{
    method:'POST',headers:{apikey:PUBLIC_KEY,'content-type':'application/json'},
    body:JSON.stringify({refresh_token:v.refresh_token}),
    cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'
  });
  if(!reply.ok)return null;
  const data=await reply.json();
  const renewed={access_token:data.access_token,refresh_token:data.refresh_token};
  if(!validShape(renewed))return null;
  remember(renewed);
  return renewed;
}
async function whoami(v) {
  const request=async (t)=>fetch(AUTH_ROOT+'/auth/v1/user',{headers:headers(t),cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'});
  let reply=await request(v.access_token);
  if(reply.status===401){v=await refreshSession(v);if(!v)return false;reply=await request(v.access_token);}
  if(!reply.ok)return false;
  const user=await reply.json();
  if(!user||typeof user.id!=='string'||typeof user.email!=='string'||!user.email_confirmed_at)return null;
  const emailHash=await sha256hex(user.email.trim().toLowerCase());
  const account=ALLOWED_ACCOUNT_HASHES[emailHash];
  if(!account)return null;
  // Only a truncated non-reversible identity fingerprint is rendered; never an email or JWT.
  return {account,identity:(await sha256hex(user.id)).slice(0,12)};
}
async function check(){
  if(err&&!validShape(candidate))return;
  const v=stored();
  if(!validShape(v)){display('Staging 回调页面已就绪。请使用新的登录邮件进行测试。');return;}
  display('正在验证 Staging 账号…');
  try{
    const user=await whoami(v);
    if(user){logoutBtn.hidden=false;auditBtn.hidden=false;display('Staging 账号 '+user.account+' 登录验证通过：已确认邮箱，JWT 身份验证通过。身份指纹 '+user.identity+'。刷新页面可再次检查会话。','success');}
    else{forget();display('会话无效或邮箱尚未确认。','error');}
  }catch(_err){display('网络访问失败，尚不能判断登录是否通过。','error');}
}
// Minimal live rejection probes. Only logged-in user identity is used; no other
// users' IDs, private content, or writes. Never interpret a network error as PASS.
const REJECT_CODES=new Set([401,403,404,406]);
auditBtn.addEventListener('click',async()=>{
  auditBtn.disabled=true;
  auditResult.textContent='正在执行只读安全验收…';
  const v=stored();
  if(!validShape(v)){auditResult.textContent='BLOCKED：没有有效的 Staging 会话。';return;}
  try{
    const current=await whoami(v);
    if(!current){auditResult.textContent='BLOCKED：身份校验未通过。';return;}
    const auth=stored();
    if(!validShape(auth)){auditResult.textContent='BLOCKED：无法取得新的有效会话。';return;}
    // Source A: restricted organization schema / only response status is used.
    const org=await fetch(AUTH_ROOT+'/rest/v1/organizations?select=id&limit=0',{
      method:'GET',
      headers:{...headers(auth.access_token),'Accept-Profile':'jianshi_v2'},
      cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'
    });
    // Source B: internal CMS session RPC. A zero UUID is a synthetic negative
    // request and the function must not be executable by authenticated users.
    const rpc=await fetch(AUTH_ROOT+'/rest/v1/rpc/cms_internal_session_v01',{
      method:'POST',
      headers:{...headers(auth.access_token),'content-type':'application/json'},
      body:JSON.stringify({
        p_user_id:'00000000-0000-0000-0000-000000000000',
        p_session_id:'00000000-0000-0000-0000-000000000000'
      }),
      cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'
    });
    const orgDenied=REJECT_CODES.has(org.status);
    const rpcDenied=REJECT_CODES.has(rpc.status);
    // Status codes only. No response body, URL fragment, token or PII displayed.
    auditResult.textContent='Staging 账号 '+current.account+
      '｜私有组织接口 '+(orgDenied?'拒绝 PASS':'FAIL/未知')+
      '（HTTP '+org.status+'）｜CMS 内部 RPC '+
      (rpcDenied?'拒绝 PASS':'FAIL/未知')+'（HTTP '+rpc.status+'）。'+
      (orgDenied&&rpcDenied?'默认拒绝安全检查 PASS；A/B 互访 E2E 仍未完成。':'发现未确认拒绝状态；保持所有功能关闭。');
  }catch(_err){auditResult.textContent='NOT_TESTED：网络或 CORS 失败，不能判定权限通过。';}
});
logoutBtn.addEventListener('click',async()=>{
  const v=stored();forget();logoutBtn.hidden=true;auditBtn.hidden=true;auditResult.textContent='';
  if(validShape(v)){
    try{const res=await fetch(AUTH_ROOT+'/auth/v1/logout',{
      method:'POST',headers:headers(v.access_token),
      cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'
    });display(res.ok?'已退出并撤销当前测试会话。':'本地会话已清除；服务端退出尚未确认。',res.ok?'success':'error');}
    catch(_err){display('本地会话已清除；服务端退出请求失败。','error');}
  }else display('本地会话已清除。');
});
check();
