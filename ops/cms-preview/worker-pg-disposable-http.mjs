// JIANSHI G2-H.7F — HTTP boundary for a disposable PostgreSQL 16 test.
// NOT a Supabase Data API, Cloudflare Worker deployment, or real auth gateway.
// Intentionally restricted to 127.0.0.1 / RFC1918-free loopback and synthetic key.
const BASE=/^http:\/\/127\.0\.0\.1:([1-9][0-9]{0,4})\/v1\/email-state$/;
const DIGEST=/^[a-f0-9]{64}$/;
const TEST_KEY=/^SYNTHETIC_[A-Za-z0-9_-]{16,100}$/;
const GATE='SYNTHETIC_H7F_DISPOSABLE_PG';
function deny(code){const e=new Error(code);e.code=code;throw e;}
function need(ok,code){if(!ok)deny(code);}
export function createDisposableEmailStateHttpClient({
 url,profile,key,fetchImpl=globalThis.fetch
}={}){
 need(profile===GATE,'CMS_H7F_TEST_ONLY');
 need(typeof url==='string'&&BASE.test(url)&&
  Number(BASE.exec(url)[1])<=65535,'CMS_H7F_LOOPBACK_ONLY');
 need(typeof key==='string'&&TEST_KEY.test(key)&&
  key==='SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET','CMS_H7F_FAKE_KEY_ONLY');
 need(typeof fetchImpl==='function','CMS_H7F_HTTP_ADAPTER_REQUIRED');
 async function rpc(action,payload){
  let res;
  try{
   res=await fetchImpl(url,{
    method:'POST',redirect:'error',cache:'no-store',
    headers:{
     authorization:'Bearer '+key,
     'x-jianshi-test-boundary':'SYNTHETIC_H7F_ONLY',
     'content-type':'application/json',
     'accept':'application/json'
    },
    body:JSON.stringify({action,...payload}),
    signal:AbortSignal.timeout(12000)
   });
  }catch{deny('CMS_H7F_HTTP_UNAVAILABLE');}
  need(res?.status===200&&res?.ok===true,'CMS_H7F_HTTP_DENIED');
  need(/^application\/json(?:;|$)/i.test(res.headers?.get('content-type')||''),
   'CMS_H7F_CONTENT_TYPE_DENIED');
  let val;
  try{
   const raw=await res.text();
   need(raw.length>0&&raw.length<=128,'CMS_H7F_RESPONSE_DENIED');
   val=JSON.parse(raw);
  }catch{deny('CMS_H7F_RESPONSE_DENIED');}
  need(val&&typeof val==='object'&&!Array.isArray(val)&&
    Object.keys(val).length===1,'CMS_H7F_RESPONSE_DENIED');
  if(action==='issue'){
   need(val.issued===true,'CMS_H7F_STATE_ISSUE_DENIED');
   return true;
  }
  need(typeof val.used==='boolean','CMS_H7F_RESPONSE_DENIED');
  return Object.freeze({used:val.used});
 }
 function digests(data){
  need(data&&DIGEST.test(data.stateDigest||'')&&
   DIGEST.test(data.cookieDigest||''),'CMS_H7F_DIGEST_INVALID');
 }
 return Object.freeze({
  synthetic:true,
  async issue(data){
   digests(data);
   need(typeof data.expiresAt==='string'&&
    /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(data.expiresAt)&&
    Number.isFinite(Date.parse(data.expiresAt)),
    'CMS_H7F_EXPIRY_INVALID');
   return rpc('issue',{
    stateDigest:data.stateDigest,cookieDigest:data.cookieDigest,
    expiresAt:data.expiresAt
   });
  },
  async consume(data){
   digests(data);
   // Database clock is authoritative, not caller-provided at timestamp.
   return rpc('consume',{
    stateDigest:data.stateDigest,cookieDigest:data.cookieDigest
   });
  }
 });
}
export const DISPOSABLE_GATE_PROFILE=GATE;
