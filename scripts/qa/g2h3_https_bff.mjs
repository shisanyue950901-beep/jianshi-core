// JianShi G2-H.3: HTTPS same-origin BFF TEST HARNESS — never a production entrypoint.
// TLS transport is REAL, GoTrue/CMS adapters are INJECTED TEST DOUBLEs.
// No HTTP login, public JWT exchange, Supabase keys, customer data or listener CLI.
import https from 'node:https';
import crypto from 'node:crypto';

const COOKIE='jianshi_g2h3';
const TTL=15*60*1000;
const MAX_BODY=8192;
const ID=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const TARGET_ROLES=Object.freeze({
 EDIT:['EDITOR','ADMIN'],RESTORE:['EDITOR','ADMIN'],SUBMIT:['EDITOR','ADMIN'],
 APPROVE:['REVIEWER','ADMIN'],REJECT:['REVIEWER','ADMIN'],
 PUBLISH:['PUBLISHER','ADMIN'],RETRACT:['PUBLISHER','ADMIN']
});
const PARAMS=Object.freeze({
 EDIT:['operation','expected_revision','request_id','title','rights_attested','facts_attested'],
 RESTORE:['operation','expected_revision','request_id','source_revision'],
 SUBMIT:['operation','expected_revision','request_id'],
 APPROVE:['operation','expected_revision','request_id'],
 REJECT:['operation','expected_revision','request_id'],
 PUBLISH:['operation','expected_revision','request_id'],
 RETRACT:['operation','expected_revision','request_id']
});
const FIXED_HEADERS={
 'cache-control':'no-store, max-age=0',
 'content-security-policy':"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
 'strict-transport-security':'max-age=31536000',
 'x-content-type-options':'nosniff',
 'x-frame-options':'DENY',
 'referrer-policy':'no-referrer',
 'permissions-policy':'camera=(), microphone=(), geolocation=()'
};
function fail(code,status=403){
 const e=new Error(code);e.code=code;e.status=status;throw e;
}
function required(ok,code,status){if(!ok)fail(code,status);}
function publicCode(error){
 return typeof error?.code==='string'&&/^CMS_[A-Z_]+$/.test(error.code)?error.code:'CMS_FAIL_CLOSED';
}
function json(res,status,body){
 res.writeHead(status,{'content-type':'application/json; charset=utf-8',...FIXED_HEADERS});
 res.end(JSON.stringify(body));
}
function freezeIdentity(x){
 required(x&&typeof x==='object'&&ID.test(x.userId||'')&&ID.test(x.sessionId||'')&&
  ['EDITOR','REVIEWER','PUBLISHER','ADMIN'].includes(x.role),'CMS_VERIFIED_IDENTITY_REQUIRED',401);
 return {userId:x.userId,sessionId:x.sessionId,role:x.role};
}
function parseCookies(header){
 const matches=(header||'').split(';').map(x=>x.trim()).filter(x=>x.startsWith(COOKIE+'='));
 required(matches.length<=1,'CMS_DUPLICATE_SESSION_COOKIE',401);
 if(!matches.length)return null;
 const value=matches[0].slice(COOKIE.length+1);
 required(/^[a-f0-9]{64}$/.test(value),'CMS_COOKIE_INVALID',401);
 return value;
}
async function collectJson(req){
 required((req.headers['content-type']||'').toLowerCase().split(';')[0]==='application/json',
  'CMS_CONTENT_TYPE',415);
 const parts=[];let bytes=0;
 for await(const chunk of req){
  bytes+=chunk.length;
  required(bytes<=MAX_BODY,'CMS_BODY_TOO_LARGE',413);
  parts.push(chunk);
 }
 let value;
 try{value=JSON.parse(Buffer.concat(parts).toString('utf8'));}
 catch{fail('CMS_JSON_INVALID',400);}
 required(value&&typeof value==='object'&&!Array.isArray(value),'CMS_JSON_INVALID',400);
 return value;
}
function validateAction(body,identity){
 const operation=body.operation;
 required(typeof operation==='string'&&Object.hasOwn(PARAMS,operation),'CMS_OPERATION_DENIED',422);
 const expected=PARAMS[operation];
 required(Object.keys(body).length===expected.length&&Object.keys(body).every(x=>expected.includes(x)),
  'CMS_PAYLOAD_DENIED',422);
 required(ID.test(body.request_id||''),'CMS_REQUEST_ID_DENIED',422);
 required(Number.isInteger(body.expected_revision)&&body.expected_revision>=1,
  'CMS_REVISION_DENIED',422);
 if(operation==='RESTORE'){
  required(Number.isInteger(body.source_revision)&&body.source_revision>=1&&
   body.source_revision<body.expected_revision,'CMS_SOURCE_REVISION_DENIED',422);
 }
 if(operation==='EDIT'){
  required(typeof body.title==='string'&&body.title.length>=2&&body.title.length<=140&&
   typeof body.rights_attested==='boolean'&&typeof body.facts_attested==='boolean',
   'CMS_EDIT_DENIED',422);
 }
 required(TARGET_ROLES[operation].includes(identity.role),'CMS_ROLE_DENIED');
}
// This library is intentionally impossible to boot as a public entrypoint.
// A production HTTPS BFF still requires a durable server-side session store,
// trusted proxy/TLS configuration, a separately audited CMS dispatcher and
// explicit authenticated session exchange design.
export function createEphemeralHttpsBff({tls,identity,dispatch,now=Date.now,
 maxWrites=8}={}){
 required(process.env.JIANSHI_G2H3_SYNTHETIC_ONLY==='1','CMS_QA_NOT_ARMED',503);
 for(const key of ['SUPABASE_SERVICE_ROLE_KEY','SUPABASE_URL','DATABASE_URL','SUPABASE_DB_URL']){
  required(!process.env[key],'CMS_REAL_CREDENTIALS_FORBIDDEN',503);
 }
 required(tls?.key&&tls?.cert,'CMS_TLS_REQUIRED',503);
 required(typeof identity?.verify==='function'&&typeof dispatch==='function',
  'CMS_TRUSTED_COMPONENTS_REQUIRED',503);
 const sessions=new Map(),limits=new Map();
 const server=https.createServer({key:tls.key,cert:tls.cert},async(req,res)=>{
  try{
   const expectedHost='127.0.0.1:'+server.address()?.port;
   required(req.socket.encrypted===true,'CMS_HTTPS_REQUIRED');
   required(req.headers.host===expectedHost,'CMS_HOST_DENIED');
   required(typeof req.url==='string'&&req.url.startsWith('/qa/'),'CMS_ROUTE_DENIED',404);
   const url=new URL(req.url,'https://'+expectedHost);
   required(!url.search&&!url.hash,'CMS_URL_PARAMETERS_DENIED',400);
   const cookie=parseCookies(req.headers.cookie);
   const record=cookie?sessions.get(cookie):undefined;
   required(!!record&&now()<record.expiresAt,'CMS_SESSION_EXPIRED',401);
   // Critical: no cached roles. A GoTrue/session revocation or role change must
   // apply to the very NEXT HTTPS request, including GET/read operations.
   let actor;
   try{actor=freezeIdentity(await identity.verify(record.jwt));}
   catch{sessions.delete(cookie);limits.delete(cookie);fail('CMS_IDENTITY_REVOKED',401);}
   required(actor.userId===record.userId&&actor.sessionId===record.sessionId,
    'CMS_SESSION_SUBSTITUTION',401);
   if(req.method==='GET'&&url.pathname==='/qa/api/session'){
    return json(res,200,{synthetic:true,role:actor.role,csrf:record.csrf});
   }
   if(req.method==='GET'&&url.pathname==='/qa/api/state'){
    // Dispatcher must authorize per-record reads with current server identity.
    const state=await dispatch({kind:'READ',actor});
    return json(res,200,state);
   }
   required(req.method==='POST'&&url.pathname==='/qa/api/action',
    'CMS_METHOD_OR_ROUTE_DENIED',405);
   required(req.headers.origin==='https://'+expectedHost,'CMS_ORIGIN_DENIED');
   required(!req.headers['sec-fetch-site']||req.headers['sec-fetch-site']==='same-origin',
    'CMS_FETCH_SITE_DENIED');
   required(req.headers['x-csrf-token']===record.csrf,'CMS_CSRF_DENIED');
   const rate=limits.get(cookie)||{since:now(),count:0};
   if(now()-rate.since>=60000){rate.since=now();rate.count=0;}
   rate.count++;limits.set(cookie,rate);
   required(rate.count<=maxWrites,'CMS_RATE_LIMITED',429);
   const data=await collectJson(req);
   validateAction(data,actor);
   const answer=await dispatch({kind:'WRITE',actor,data});
   return json(res,200,{status:'SYNTHETIC_OK',result:answer});
  }catch(error){
   // No upstream token, private body, stack trace, or SQL result in errors.
   json(res,error?.status||503,{status:publicCode(error)});
  }
 });
 return Object.freeze({
  server,
  // Tests only: issuing a cookie is a DIRECT in-process action.
  // There is deliberately NO public login, token-exchange, or grant endpoint.
  async issueVerifiedTestSession(jwt){
   const actor=freezeIdentity(await identity.verify(jwt));
   const sid=crypto.randomBytes(32).toString('hex');
   const csrf=crypto.randomBytes(24).toString('hex');
   sessions.set(sid,{jwt,userId:actor.userId,sessionId:actor.sessionId,
    expiresAt:now()+TTL,csrf});
   return Object.freeze({id:sid,csrf,actor,
    setCookie:COOKIE+'='+sid+'; Secure; HttpOnly; SameSite=Strict; Path=/qa; Max-Age=900'});
  },
  revokeTestSession(id){sessions.delete(id);limits.delete(id);},
  activeTestSessions(){return sessions.size;}
 });
}
