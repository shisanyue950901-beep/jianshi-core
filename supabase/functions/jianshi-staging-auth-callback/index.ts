// F2.1 staging-only Auth callback. Never deploy this function to production.
const REF = 'apuibjhxinumxbfnqlkp';
const ROUTE = '/functions/v1/jianshi-staging-auth-callback';
const TEST_EMAIL = 'caps67@qq.com';
const securityHeaders = {
  'cache-control':'no-store, max-age=0',
  'referrer-policy':'no-referrer',
  'x-content-type-options':'nosniff',
  'x-frame-options':'DENY'
};
const script = "(function(){'use strict';const route='/functions/v1/jianshi-staging-auth-callback';const el=document.getElementById('state');const btn=document.getElementById('logout');const key='jianshi_staging_only_auth';function say(t){el.textContent=t}function clear(){try{sessionStorage.removeItem(key)}catch(_){}}function save(v){try{sessionStorage.setItem(key,JSON.stringify(v))}catch(_){}}function load(){try{return JSON.parse(sessionStorage.getItem(key)||'null')}catch(_){return null}}async function post(path,token){const r=await fetch(route+path,{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer '+token},body:'{}',credentials:'omit',cache:'no-store',referrerPolicy:'no-referrer'});return {ok:r.ok,data:await r.json().catch(()=>({}))}}async function verify(v){try{const r=await post('/session',v.access_token);if(r.ok&&r.data.ok){btn.hidden=false;say('Staging 邮箱已确认，JWT 身份验证通过。账号：'+r.data.masked_email+'。刷新本页可以复核会话。')}else{clear();say('登录会话无效或尚未确认。需要新的验证邮件。')}}catch(_){say('网络异常；尚不能确认登录成功。')}}const p=new URLSearchParams(location.hash.slice(1));const a=p.get('access_token'),r=p.get('refresh_token');const err=p.get('error_code')||p.get('error');if(location.hash)history.replaceState(null,'',location.pathname);if(a&&r){const v={access_token:a,refresh_token:r};save(v);verify(v)}else if(err){clear();say('链接验证失败：'+String(err).slice(0,64))}else{const v=load();if(v&&v.access_token)verify(v);else say('Staging 回调页已就绪。请使用新验证邮件进入此页。')}btn.addEventListener('click',async()=>{const v=load();clear();btn.hidden=true;if(v&&v.access_token){try{await post('/logout',v.access_token)}catch(_){}}say('本页临时登录信息已清除，退出请求已处理。')});})();";
const style = "html{color-scheme:dark;background:#0b1320;color:#edf4ff;font:16px system-ui}body{min-height:100vh;margin:0;display:grid;place-items:center;padding:16px;box-sizing:border-box}main{box-sizing:border-box;max-width:540px;background:#192537;border:1px solid #39506b;border-radius:16px;padding:30px}h1{font-size:24px}p{line-height:1.7;color:#b5c5d9}#state{background:#27384c;border-radius:8px;padding:16px;line-height:1.7;overflow-wrap:anywhere}button{padding:10px 16px;border:0;border-radius:8px;background:#3d84ce;color:white;cursor:pointer}small{color:#9fb2c9}";
const page = "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><meta name='robots' content='noindex,nofollow'><title>见势 Staging 邮箱回调</title><style>"+style+"</style></head><body><main><small>仅供见势 Staging 验收 · 不是正式账号页面</small><h1>见势｜邮箱验证</h1><p>本页面仅验证测试邮箱和 JWT 会话。令牌不会显示在页面上，也不会记录到日志。</p><div id='state' role='status' aria-live='polite'>正在检查...</div><p><button id='logout' hidden>退出测试会话</button></p><small>Production 的账号、CMS 和商机撮合始终关闭。</small></main><script>"+script+"</script></body></html>";
function result(body:unknown,status=200) {
  return new Response(JSON.stringify(body),{status,headers:{...securityHeaders,'content-type':'application/json; charset=utf-8'}});
}
async function authenticate(token:string) {
  if(token.length<32 || token.length>8192) return false;
  const url=Deno.env.get('SUPABASE_URL'), key=Deno.env.get('SUPABASE_ANON_KEY');
  if(url!=='https://'+REF+'.supabase.co' || !key) return false;
  const response=await fetch(url+'/auth/v1/user',{headers:{apikey:key,authorization:'Bearer '+token},signal:AbortSignal.timeout(8000),cache:'no-store'});
  if(!response.ok) return false;
  const user=await response.json().catch(()=>null);
  return user?.email===TEST_EMAIL && Boolean(user?.email_confirmed_at);
}
async function csp() {
  const digest=async (s:string)=>btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)))));
  return "default-src 'none'; script-src 'sha256-"+await digest(script)+"'; style-src 'sha256-"+await digest(style)+"'; connect-src 'self'; form-action 'none'; frame-ancestors 'none'; base-uri 'none'";
}
Deno.serve(async(req:Request)=>{
  const u=new URL(req.url);
  if(u.hostname!==REF+'.supabase.co')return result({ok:false,code:'STAGING_ONLY'},403);
  if(req.method==='GET')
    // HTML is forced to text/plain with CSP sandbox by the Supabase Edge gateway.
    // A pure HTTP redirect to the Cloudflare preview keeps the fragment in the
    // browser under RFC redirect fragment inheritance, without logging tokens.
    return new Response(null,{status:302,headers:{
      ...securityHeaders,
      location:'https://staging-auth-callback.jianshi-bua.pages.dev/_qa/staging-auth/'
    }});
  const action = u.pathname.split('/').filter(Boolean).pop();
  if(req.method!=='POST' || !['session','logout'].includes(action||''))return result({ok:false,code:'NOT_FOUND'},404);
  const origin=req.headers.get('origin');
  const site=req.headers.get('sec-fetch-site');
  if(origin&&origin!==u.origin || site&&site!=='same-origin'&&site!=='none')return result({ok:false,code:'ORIGIN_REJECTED'},403);
  const raw=req.headers.get('authorization')||'';
  if(!raw.startsWith('Bearer '))return result({ok:false,code:'NO_TOKEN'},401);
  const token=raw.slice(7);
  try {
    if(!await authenticate(token))return result({ok:false,code:'INVALID_SESSION'},403);
    if(action==='session')return result({ok:true,masked_email:'ca***@qq.com'});
    const url=Deno.env.get('SUPABASE_URL')!;
    const key=Deno.env.get('SUPABASE_ANON_KEY')!;
    const done=await fetch(url+'/auth/v1/logout',{method:'POST',headers:{apikey:key,authorization:'Bearer '+token},signal:AbortSignal.timeout(8000)});
    return result({ok:done.ok},done.ok?200:502);
  } catch(_error){return result({ok:false,code:'AUTH_BACKEND_UNAVAILABLE'},503)}
});
