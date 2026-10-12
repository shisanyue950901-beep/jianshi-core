// JIANSHI F2.1 G2-H.7G: synthetic-only Worker mTLS Fetcher contract.
// A real Cloudflare Workers mTLS binding exposes env.BINDING.fetch(...).
// This module never creates a certificate, imports a secret, or calls global fetch.
// The .invalid upstream is deliberately unreachable in a real deployment.
const ENDPOINT='https://h7g-state.example.invalid/v1/email-state';
const PROFILE='SYNTHETIC_G2H7G_MTLS_ONLY';
const DIGEST=/^[a-f0-9]{64}$/;
function deny(code){const e=new Error(code);e.code=code;throw e;}
function need(ok,code){if(!ok)deny(code);}
function strictJson(response,action){
 need(response?.status===200&&response?.ok===true,'CMS_H7G_TRANSPORT_DENIED');
 need(/^application\/json(?:;|$)/i.test(response.headers?.get('content-type')||''),
   'CMS_H7G_JSON_ONLY');
 let data;
 try{
  const text=await response.text();
  need(text.length>0&&text.length<=128,'CMS_H7G_BODY_DENIED');
  data=JSON.parse(text);
 }catch{deny('CMS_H7G_BODY_DENIED');}
 need(data&&typeof data==='object'&&!Array.isArray(data)&&
  Object.keys(data).length===1,'CMS_H7G_BODY_DENIED');
 if(action==='issue'){
  need(data.issued===true,'CMS_H7G_ISSUE_DENIED');return true;
 }
 need(typeof data.used==='boolean','CMS_H7G_CONSUME_DENIED');
 return Object.freeze({used:data.used});
}
export function createSyntheticWorkerMtlsStateClient({
 origin,profile,binding
}={}){
 need(origin===ENDPOINT&&profile===PROFILE,'CMS_H7G_UNROUTABLE_ONLY');
 need(binding?.synthetic===true&&typeof binding.fetch==='function',
  'CMS_H7G_TEST_BINDING_REQUIRED');
 async function rpc(action,body){
  let answer;
  try{
   answer=await binding.fetch(ENDPOINT,{
    method:'POST',redirect:'error',cache:'no-store',
    headers:{
     'content-type':'application/json',
     'accept':'application/json',
     'x-jianshi-test-boundary':'SYNTHETIC_H7G_MTLS_ONLY'
    },
    body:JSON.stringify({action,...body}),
    signal:AbortSignal.timeout(12000)
   });
  }catch{deny('CMS_H7G_MTLS_FAILURE');}
  return strictJson(answer,action);
 }
 function digests(value){
  need(value&&DIGEST.test(value.stateDigest||'')&&
   DIGEST.test(value.cookieDigest||''),'CMS_H7G_DIGEST_DENIED');
 }
 return Object.freeze({
  synthetic:true,
  async issue(value){
   digests(value);
   need(typeof value.expiresAt==='string'&&
    /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(value.expiresAt)&&
    Number.isFinite(Date.parse(value.expiresAt)),
    'CMS_H7G_EXPIRY_DENIED');
   return rpc('issue',{
    stateDigest:value.stateDigest,cookieDigest:value.cookieDigest,
    expiresAt:value.expiresAt
   });
  },
  async consume(value){
   digests(value);
   return rpc('consume',{
    stateDigest:value.stateDigest,cookieDigest:value.cookieDigest
   });
  }
 });
}
export const SYNTHETIC_MTLS_ENDPOINT=ENDPOINT;
