// F2.1 G2-H.5 — real HTTPS <-> durable PostgreSQL contract harness.
// One full synthetic integration path. NOT public, NOT real login, no network
// service listener in this module. The host must supply an injected safe store,
// real TLS keys, a verified identity adapter, and a private CMS dispatcher.
import https from 'node:https';
const COOKIE='jianshi_g2h5';
const H={
 'cache-control':'no-store, max-age=0','x-content-type-options':'nosniff',
 'strict-transport-security':'max-age=31536000',
 'content-security-policy':"default-src 'none'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'",
 'referrer-policy':'no-referrer','x-frame-options':'DENY'
};
const U=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const O=/^[A-Za-z0-9_-]{43}$/;
const OPS=new Set(['RESTORE']);
function failure(code,status=403){const e=new Error(code);e.code=code;e.status=status;throw e;}
function requireThat(ok,code,status){if(!ok)failure(code,status);}
function respond(res,http,body){
 res.writeHead(http,{'content-type':'application/json; charset=utf-8',...H});
 res.end(JSON.stringify(body));
}
function verified(v){
 requireThat(v&&U.test(v.userId||'')&&U.test(v.sessionId||'')&&
  ['EDITOR','REVIEWER','PUBLISHER'].includes(v.role),'CMS_INVALID_VERIFIED_ACTOR',401);
 return {userId:v.userId,sessionId:v.sessionId,role:v.role};
}
function cookie(header){
 const hits=(header||'').split(';').map(x=>x.trim()).filter(x=>x.startsWith(COOKIE+'='));
 requireThat(hits.length<=1,'CMS_DUPLICATE_COOKIE',401);
 if(!hits.length)failure('CMS_COOKIE_MISSING',401);
 const value=hits[0].slice(COOKIE.length+1);
 requireThat(O.test(value),'CMS_COOKIE_INVALID',401);
 return value;
}
async function jsonBody(req){
 requireThat((req.headers['content-type']||'').toLowerCase().split(';')[0]==='application/json',
  'CMS_JSON_REQUIRED',415);
 const buffers=[];let bytes=0;
 for await(const chunk of req){
  bytes+=chunk.length;
  requireThat(bytes<=4096,'CMS_BODY_TOO_LARGE',413);buffers.push(chunk);
 }
 let obj;
 try{obj=JSON.parse(Buffer.concat(buffers).toString('utf8'));}
 catch{failure('CMS_JSON_INVALID',400);}
 requireThat(obj&&typeof obj==='object'&&!Array.isArray(obj),'CMS_JSON_INVALID',400);
 const keys=['operation','expected_revision','source_revision','request_id','content_id'];
 requireThat(Object.keys(obj).length===keys.length&&
   Object.keys(obj).every(k=>keys.includes(k)),'CMS_PAYLOAD_DENIED',422);
 requireThat(OPS.has(obj.operation)&&
   Number.isInteger(obj.expected_revision)&&obj.expected_revision>=2&&
   Number.isInteger(obj.source_revision)&&obj.source_revision>=1&&
   obj.source_revision<obj.expected_revision&&
   U.test(obj.content_id||'')&&U.test(obj.request_id||''),
   'CMS_RESTORE_PAYLOAD_INVALID',422);
 return obj;
}
function errorStatus(e){
 if(e?.status)return e.status;
 if(['CMS_SESSION_INVALID','CMS_SESSION_REVOKED','CMS_WRITE_DISABLED',
  'CMS_AUTH_NOT_READY','CMS_PERMISSION_DENIED','CMS_ROLE_FORBIDDEN'].includes(e?.code))return 401;
 if(e?.code==='CMS_RATE_LIMITED')return 429;
 if(['CMS_OWNER_DENIED','CMS_CSRF_DENIED','CMS_ROLE_DENIED',
     'CMS_ORIGIN_DENIED','CMS_FETCH_SITE_DENIED'].includes(e?.code))return 403;
 if(['CMS_STALE_REVISION','CMS_DUPLICATE_REQUEST'].includes(e?.code))return 409;
 if(['CMS_INVALID_RESTORE_PAYLOAD','CMS_RESTORE_REQUIRES_DRAFT'].includes(e?.code))return 422;
 return 503;
}
export function createDurableHttpsHarness({tls,vault,store,identity,dispatch,now=Date.now}={}){
 requireThat(process.env.JIANSHI_G2H5_SYNTHETIC_ONLY==='1','CMS_QA_NOT_ARMED',503);
 for(const key of ['SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','DATABASE_URL','SUPABASE_DB_URL']){
  requireThat(!process.env[key],'CMS_EXTERNAL_CREDENTIALS_FORBIDDEN',503);
 }
 requireThat(tls?.key&&tls?.cert,'CMS_TLS_REQUIRED',503);
 requireThat(vault?.cookieDigest&&vault?.csrfDigest&&vault?.openEnvelope&&vault?.issueEnvelope,
  'CMS_VAULT_REQUIRED',503);
 requireThat(store?.issue&&store?.consume&&store?.revoke,'CMS_DURABLE_STORE_REQUIRED',503);
 requireThat(identity?.verify&&typeof dispatch==='function','CMS_IDENTITY_DISPATCH_REQUIRED',503);
 const server=https.createServer({key:tls.key,cert:tls.cert},async(req,res)=>{
  try{
   const host='127.0.0.1:'+server.address()?.port;
   requireThat(req.socket.encrypted===true&&req.headers.host===host,'CMS_HOST_TLS_DENIED');
   const u=new URL(req.url,'https://'+host);
   requireThat(!u.search&&!u.hash&&u.pathname.startsWith('/qa/api/'),
    'CMS_ROUTE_DENIED',404);
   const isWrite=req.method==='POST'&&u.pathname==='/qa/api/action';
   const isRead=req.method==='GET'&&
    ['/qa/api/state','/qa/api/session'].includes(u.pathname);
   requireThat(isWrite||isRead,'CMS_ROUTE_DENIED',404);
   if(isWrite){
    requireThat(req.headers.origin==='https://'+host,'CMS_ORIGIN_DENIED');
    requireThat(!req.headers['sec-fetch-site']||
      req.headers['sec-fetch-site']==='same-origin','CMS_FETCH_SITE_DENIED');
   }
   const token=cookie(req.headers.cookie);
   let csrfDigest=null;
   if(isWrite){
    requireThat(typeof req.headers['x-csrf-token']==='string'&&
      O.test(req.headers['x-csrf-token']),'CMS_CSRF_DENIED');
    csrfDigest=vault.csrfDigest(req.headers['x-csrf-token']);
   }
   // Actual DB row is locked and quota consumed atomically; even GET calls
   // revalidate the real auth.sessions row and current role gate.
   let row;
   try{row=await store.consume({
    cookieDigest:vault.cookieDigest(token),isWrite,csrfDigest
   });}catch(e){
    if(['CMS_SESSION_INVALID','CMS_SESSION_REVOKED','CMS_CSRF_DENIED',
      'CMS_WRITE_DISABLED','CMS_PERMISSION_DENIED'].includes(e?.code))throw e;
    failure('CMS_SESSION_STORE_UNAVAILABLE',503);
   }
   requireThat(row&&typeof row==='object','CMS_STORE_SCHEMA_INVALID',503);
   if(row.allowed===false&&row.status==='CMS_RATE_LIMITED')
    failure('CMS_RATE_LIMITED',429);
   requireThat(row.allowed===true&&U.test(row.user_id||'')&&
     U.test(row.auth_session_id||'')&&typeof row.encrypted_jwt==='string'&&
     typeof row.encryption_key_id==='string',
     'CMS_STORE_SCHEMA_INVALID',503);
   let jwt,actor;
   try{
    jwt=vault.openEnvelope({
     encrypted_jwt:row.encrypted_jwt,key_id:row.encryption_key_id,
     userId:row.user_id,sessionId:row.auth_session_id
    });
    actor=verified(await identity.verify(jwt));
   }catch{failure('CMS_IDENTITY_REJECTED',401);}
   requireThat(actor.userId===row.user_id&&actor.sessionId===row.auth_session_id,
    'CMS_IDENTITY_BINDING_FAILED',401);
   if(u.pathname==='/qa/api/session'){
    // Raw CSRF token is deliberately NOT recoverable from the database.
    // The future trusted login exchange must pass it once to the client.
    return respond(res,200,{synthetic:true,role:actor.role,csrfRequired:true});
   }
   if(u.pathname==='/qa/api/state'){
    const r=await dispatch({kind:'READ',actor});
    return respond(res,200,{synthetic:true,result:r});
   }
   requireThat(actor.role==='EDITOR','CMS_ROLE_DENIED');
   const data=await jsonBody(req);
   const result=await dispatch({kind:'WRITE',actor,data});
   return respond(res,200,{synthetic:true,result});
  }catch(e){
   const code=typeof e?.code==='string'&&/^CMS_[A-Z_]+$/.test(e.code)
    ?e.code:'CMS_FAIL_CLOSED';
   respond(res,errorStatus(e),{status:code});
  }
 });
 return Object.freeze({
  server,
  // TEST HARNESS ONLY. A public login/token-exchange endpoint is forbidden.
  // This method may only be invoked inside the isolated CI process.
  async issueSyntheticVerifiedSession(jwt){
   const actor=verified(await identity.verify(jwt));
   const token=vault.newCookie(),csrf=vault.newCsrf();
   const envelope=vault.issueEnvelope({jwt,userId:actor.userId,sessionId:actor.sessionId});
   const digest=vault.cookieDigest(token);
   const result=await store.issue({
    actor:actor.userId,authSession:actor.sessionId,cookieDigest:digest,
    csrfDigest:vault.csrfDigest(csrf),envelope,
    expiresAt:new Date(now()+15*60*1000).toISOString()
   });
   requireThat(result===true,'CMS_SESSION_ISSUE_DENIED',403);
   return Object.freeze({
    cookie:COOKIE+'='+token+'; Secure; HttpOnly; SameSite=Strict; Path=/qa; Max-Age=900',
    csrf,role:actor.role,
    // The ID is a server-held HMAC digest, never an actual browser cookie.
    sessionDigest:digest
   });
  },
  async revokeSyntheticSession(sessionDigest){
   requireThat(/^[a-f0-9]{64}$/.test(sessionDigest||''),'CMS_SESSION_INPUT_INVALID');
   return store.revoke({cookieDigest:sessionDigest});
  }
 });
}
