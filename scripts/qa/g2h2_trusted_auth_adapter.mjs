// F2.1 G2-H.2: STAGING-only GoTrue server adapter. NOT a public BFF.
// No HTTP listener/login routes, no browser storage, no credentials embedded.
// Every call requires existing CMS launch gates, VERIFIED GoTrue user,
// validated token claims, active auth.sessions and fresh server-only role RPC.
const STAGING = 'https://apuibjhxinumxbfnqlkp.supabase.co';
const ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ROLES = new Set(['EDITOR','REVIEWER','PUBLISHER','ADMIN']);
const APPS = new Set(['account_auth','cms_editor']);
function deny(code){const e=new Error(code);e.code=code;throw e;}
function check(value,code){if(!value)deny(code);}
function claimsAfterVerification(jwt,userId,now){
 try{
  const a=jwt.split('.');
  check(a.length===3&&a[1].length<=12000,'CMS_TOKEN_FORMAT');
  const payload=JSON.parse(Buffer.from(a[1],'base64url').toString('utf8'));
  check(payload.sub===userId&&payload.role==='authenticated'&&
    (payload.aud==='authenticated'||Array.isArray(payload.aud)&&payload.aud.includes('authenticated'))&&
    payload.iss===STAGING+'/auth/v1'&&
    ID.test(payload.session_id||'')&&payload.is_anonymous!==true&&
    typeof payload.exp==='number'&&Number.isFinite(payload.exp)&&payload.exp*1000>now(),
    'CMS_TOKEN_CLAIMS');
  return payload.session_id;
 }catch(e){deny(e.code||'CMS_TOKEN_CLAIMS');}
}
export function createStagingAuthAdapter({url,anonKey,serviceKey,fetchImpl=fetch,now=Date.now}={}){
 check(url===STAGING,'CMS_STAGING_ORIGIN_PIN');
 check(typeof anonKey==='string'&&anonKey.length>=16,'CMS_ANON_KEY_REQUIRED');
 check(typeof serviceKey==='string'&&serviceKey.length>=16,'CMS_SERVER_KEY_REQUIRED');
 check(anonKey!==serviceKey,'CMS_DISTINCT_KEY_REQUIRED');
 const base=new URL(url);
 async function call(route,{method='GET',jwt=null,body=null,server=false}={}){
  const target=new URL(route,base);
  check(target.origin===base.origin && target.protocol==='https:' &&
    target.pathname.startsWith('/auth/v1/')||target.origin===base.origin &&
    target.protocol==='https:'&&target.pathname.startsWith('/rest/v1/'),
    'CMS_UPSTREAM_NOT_ALLOWED');
  const key=server?serviceKey:anonKey;
  const headers={apikey:key,'cache-control':'no-store'};
  if(jwt)headers.authorization='Bearer '+jwt;
  else if(server)headers.authorization='Bearer '+serviceKey;
  if(body!==null)headers['content-type']='application/json';
  let res;
  try{
   res=await fetchImpl(target.toString(),{
    method,headers,body:body===null?undefined:JSON.stringify(body),
    redirect:'error',signal:AbortSignal.timeout(6000),cache:'no-store'
   });
  }catch{deny('CMS_UPSTREAM_UNAVAILABLE');}
  check(res&&res.ok===true,'CMS_UPSTREAM_DENIED');
  try{return await res.json();}catch{deny('CMS_UPSTREAM_SCHEMA');}
 }
 async function ensureGates(){
  const features=await call('/rest/v1/product_feature_flags?select=feature_key,enabled&feature_key=in.(account_auth,cms_editor)',
    {server:true});
  check(Array.isArray(features)&&features.length===2&&
    features.every(r=>APPS.has(r.feature_key)&&r.enabled===true)&&
    new Set(features.map(r=>r.feature_key)).size===2,'CMS_WRITE_DISABLED');
  const ready=await call('/rest/v1/rpc/auth_launch_ready_v01',{method:'POST',body:{},server:true});
  check(ready===true,'CMS_AUTH_NOT_READY');
 }
 async function verify(jwt){
  check(typeof jwt==='string'&&jwt.length>=32&&jwt.length<=9000&&
    /^[A-Za-z0-9_.-]+$/.test(jwt),'CMS_TOKEN_INVALID');
  await ensureGates();
  // GoTrue validates signature and current account state. Parsing JWT alone
  // is never authentication. Never trust a client-supplied actor or role.
  const user=await call('/auth/v1/user',{jwt});
  const userId=user?.id;
  check(typeof userId==='string'&&ID.test(userId)&&user.email_confirmed_at &&
    user.is_anonymous!==true,'CMS_GOTRUE_USER_REJECTED');
  const sessionId=claimsAfterVerification(jwt,userId,now);
  const session=await call('/rest/v1/rpc/cms_internal_session_v01',{
   server:true,method:'POST',body:{p_user_id:userId,p_session_id:sessionId}});
  check(session===true,'CMS_SESSION_REVOKED');
  const role=await call('/rest/v1/rpc/cms_internal_actor_role_v01',{
   server:true,method:'POST',body:{p_actor:userId}});
  check(ROLES.has(role),'CMS_ROLE_FORBIDDEN');
  return Object.freeze({userId,sessionId,role});
 }
 return Object.freeze({verify});
}
export const stagingOrigin=STAGING;
