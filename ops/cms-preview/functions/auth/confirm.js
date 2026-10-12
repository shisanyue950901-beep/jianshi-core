// JIANSHI G2-H.7D — Pages Functions Web Request/Response contract ONLY.
// Intentionally located under ops/; NEVER under repo-root functions/.
// Hardcoded RFC 2606 .invalid origin means real Cloudflare hosts ALWAYS deny.
// Synthetic controller is TEST-INJECTED: no GoTrue, no DB, no live secrets.
const ORIGIN='https://h7d-preview.example.invalid';
const PROFILE='SYNTHETIC_CONTRACT_ONLY';
const HEADERS={
 'cache-control':'private, no-store, max-age=0',
 'pragma':'no-cache',
 'referrer-policy':'no-referrer',
 'x-content-type-options':'nosniff',
 'x-frame-options':'DENY',
 'x-robots-tag':'noindex, nofollow, noarchive',
 'content-security-policy':"default-src 'none'; script-src 'none'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
};
const HTML='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'+
 '<meta name="robots" content="noindex,nofollow">'+
 '<title>见势隔离测试确认</title></head><body><main>'+
 '<h1>见势隔离邮箱确认</h1><p>这是合成协议测试，不是正式账号登录。</p>'+
 '<form method="post" action="/auth/confirm">'+
 '<button type="submit">手动确认测试</button></form></main></body></html>';
const DENIED='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'+
 '<title>请求已拒绝</title></head><body>该隔离验证请求无法继续。</body></html>';
const STATE=/^__Host-jianshi_mail_state=[A-Za-z0-9_-]{43}$/;
const INTENT=/^__Host-jianshi_mail_intent=v1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;
function hasTwoCookies(header){
 const a=String(header||'').split(';').map(x=>x.trim());
 return a.filter(x=>STATE.test(x)).length===1 &&
   a.filter(x=>INTENT.test(x)).length===1;
}
function respond(code,body='',extras={}){
 const h=new Headers(HEADERS);
 h.set('content-type','text/html; charset=utf-8');
 for(const [key,value] of Object.entries(extras)){
  if(key==='set-cookie'){
   if(!Array.isArray(value))throw Error('CMS_H7D_BAD_SET_COOKIE');
   for(const v of value)h.append('set-cookie',v);
  }else h.set(key,value);
 }
 return new Response(body,{status:code,headers:h});
}
function validCookies(values,expected){
 return Array.isArray(values)&&values.length===expected&&values.every(v=>
  typeof v==='string'&&v.startsWith('__Host-jianshi_')&&
  v.includes('; Secure; HttpOnly; SameSite=')&&
  v.includes('; Path=/; Max-Age=')&&
  !/[\r\n]/.test(v));
}
async function isEmptyBody(request){
 // Do not Buffer the request unboundedly. Browser forms with no inputs are empty.
 const n=request.headers.get('content-length');
 if(n!==null&&n!=='0')return false;
 if(!request.body)return true;
 const reader=request.body.getReader();
 try{
  const next=await reader.read();
  return next.done===true || next.value?.byteLength===0 && (await reader.read()).done===true;
 }finally{await reader.cancel().catch(()=>{});}
}
// Pages compatible signature (context.request/context.env). Does not use node:,
// process, Buffer, Node TLS or runtime global DB/auth settings.
export async function onRequest(context){
 try{
  const env=context?.env,request=context?.request;
  if(!env||env.JIANSHI_H7D_PROFILE!==PROFILE||
    env.JIANSHI_H7D_CONTRACT_GATE!=='1'||
    !env.JIANSHI_H7D_TEST_CONTROLLER ||
    env.JIANSHI_H7D_TEST_CONTROLLER.synthetic!==true ||
    typeof env.JIANSHI_H7D_TEST_CONTROLLER.receiveLink!=='function' ||
    typeof env.JIANSHI_H7D_TEST_CONTROLLER.confirm!=='function' ||
    !(request instanceof Request)) return respond(404,DENIED);

  const u=new URL(request.url);
  // .invalid origin is an UNROUTABLE deployment kill-switch. A production
  // host can never pass, even if misconfigured with synthetic bindings.
  if(u.origin!==ORIGIN || u.username!=='' || u.password!=='' ||
    request.url.length>2048 || request.headers.get('host')!==u.host ||
    request.headers.has('x-forwarded-host') ||
    request.headers.has('x-forwarded-proto') ||
    u.pathname!=='/auth/confirm'||u.hash!=='')return respond(404,DENIED);
  const controller=env.JIANSHI_H7D_TEST_CONTROLLER;
  if(request.method==='GET'&&u.search){
   const result=await controller.receiveLink({
    url:u.pathname+u.search,
    cookieHeader:request.headers.get('cookie')||'',
    requestOrigin:u.origin
   });
   if(result?.status!==303||result.location!=='/auth/confirm'||
     !validCookies(result.setCookies,1))throw Error('CMS_H7D_BAD_RECEIVE');
   return respond(303,'',{location:'/auth/confirm','set-cookie':result.setCookies});
  }
  if(request.method==='GET'&&!u.search){
   if(!hasTwoCookies(request.headers.get('cookie')))return respond(403,DENIED);
   return respond(200,HTML);
  }
  if(request.method==='POST'&&!u.search){
   if(request.headers.get('origin')!==u.origin ||
     request.headers.get('sec-fetch-site')!=='same-origin' ||
     request.headers.get('content-type')!=='application/x-www-form-urlencoded' ||
     !(await isEmptyBody(request)))return respond(403,DENIED);
   const result=await controller.confirm({
    method:'POST',url:'/auth/confirm',
    requestOrigin:request.headers.get('origin'),
    fetchSite:request.headers.get('sec-fetch-site'),
    cookieHeader:request.headers.get('cookie')||''
   });
   if(result?.status!==303||result.location!=='/cms/'||
     !validCookies(result.setCookies,3))throw Error('CMS_H7D_BAD_CONFIRM');
   return respond(303,'',{location:'/cms/','set-cookie':result.setCookies});
  }
  return respond(405,DENIED,{allow:'GET, POST'});
 }catch{
  // Suppress GoTrue / SQL / email / raw Request errors; never log or reflect.
  return respond(403,DENIED);
 }
}
export const PREVIEW_CONTRACT_ORIGIN=ORIGIN;
