// JIANSHI G2-H.7 — GoTrue email token_hash HTTP wire-contract ONLY.
// Uses injected fake HTTP. NO live email, NO deployable BFF, NO CMS login.
// Real Supabase docs: /otp sends email, /verify token_hash returns a session;
// this is NOT the same as /token?grant_type=pkce with auth_code+verifier.
const STAGING='https://apuibjhxinumxbfnqlkp.supabase.co';
const STATE=/^[A-Za-z0-9_-]{43}$/;
const HASH=/^[a-f0-9]{64}$/i;
function deny(code){const e=new Error(code);e.code=code;throw e;}
function need(ok,code){if(!ok)deny(code);}
function safeRedirect(input){
 need(typeof input==='string'&&input.length<300,'CMS_H7_REDIRECT_DENIED');
 let u;try{u=new URL(input);}catch{deny('CMS_H7_REDIRECT_DENIED');}
 need(u.origin==='https://localhost'&&u.pathname==='/auth/confirm'&&
   u.username===''&&u.password===''&&u.hash===''&&
   [...u.searchParams.keys()].join(',')==='state'&&
   STATE.test(u.searchParams.get('state')||''),'CMS_H7_REDIRECT_DENIED');
 return u.href;
}
export function createStagingTokenHashWire({url,publishableKey,fetchImpl}={}){
 need(process.env.JIANSHI_G2H7_SYNTHETIC_ONLY==='1','CMS_H7_DISABLED');
 need(url===STAGING,'CMS_H7_STAGING_ONLY');
 // The mock-key constraint prevents accidental requests using genuine keys.
 need(typeof publishableKey==='string'&&
   /^SYNTHETIC_[A-Za-z0-9_-]{12,}$/.test(publishableKey),'CMS_H7_FAKE_KEY_REQUIRED');
 need(typeof fetchImpl==='function'&&fetchImpl!==globalThis.fetch,'CMS_H7_FAKE_HTTP_REQUIRED');
 async function post(path,body){
  let response;
  try{
   response=await fetchImpl(STAGING+path,{
    method:'POST',
    headers:{apikey:publishableKey,'content-type':'application/json',
      'cache-control':'no-store'},
    body:JSON.stringify(body),redirect:'error',cache:'no-store',
    signal:AbortSignal.timeout(3500)
   });
  }catch{deny('CMS_H7_UPSTREAM_FAILED');}
  need(response?.status===200&&response.ok===true,'CMS_H7_UPSTREAM_DENIED');
  need(/^application\/json(?:;|$)/i.test(response.headers?.get?.('content-type')||''),
    'CMS_H7_UPSTREAM_CONTENT_TYPE');
  try{
   const value=await response.json();
   need(value&&typeof value==='object'&&!Array.isArray(value),
     'CMS_H7_RESPONSE_INVALID');
   return value;
  }catch{deny('CMS_H7_RESPONSE_INVALID');}
 }
 return Object.freeze({
  async requestEmail({email,redirectTo}={}){
   need(typeof email==='string'&&email.length<255&&
     /^SYNTHETIC_[A-Za-z0-9_-]+@example\.invalid$/.test(email),
     'CMS_H7_SYNTHETIC_EMAIL_ONLY');
   const destination=safeRedirect(redirectTo);
   const p='/auth/v1/otp?redirect_to='+encodeURIComponent(destination);
   // GoTrue's /otp contract: create_user:false prevents auto-registration.
   // Do NOT send code_challenge: token_hash verifyOtp and auth-code PKCE are
   // distinct branches. Never infer that 200 proves an email was delivered.
   await post(p,{email,create_user:false});
   return Object.freeze({accepted:true,deliveryVerified:false});
  },
  async verifyTokenHash({tokenHash}={}){
   need(typeof tokenHash==='string'&&HASH.test(tokenHash),
     'CMS_H7_TOKEN_HASH_INVALID');
   const v=await post('/auth/v1/verify',{token_hash:tokenHash,type:'email'});
   need(typeof v.access_token==='string'&&v.access_token.length>=32&&
     typeof v.refresh_token==='string'&&v.refresh_token.length>=32&&
     v.token_type==='bearer'&&Number.isInteger(v.expires_in)&&v.expires_in>0,
     'CMS_H7_SESSION_INVALID');
   // Trusted server only. The caller MUST revalidate /user, auth.sessions,
   // feature gates and private CMS role before issuing an opaque BFF cookie.
   return Object.freeze({access_token:v.access_token,
     refresh_token:v.refresh_token,token_type:'bearer',expires_in:v.expires_in});
  }
 });
}
export const STAGING_GOTRUE_ORIGIN=STAGING;
