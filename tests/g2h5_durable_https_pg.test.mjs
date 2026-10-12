// G2-H.5 one real integration path:
// HTTPS -> HMAC Cookie -> private PostgreSQL row -> AES-GCM decrypt ->
// synthetic GoTrue verifier backed by LIVE disposable PostgreSQL ACL/session ->
// actual CMS SQL historical revision restoration. NO external network/data.
import test,{before,after} from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import https from 'node:https';
import {spawn,execFileSync} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createSessionVault} from '../scripts/qa/g2h4_session_vault.mjs';
import {createStagingAuthAdapter,stagingOrigin} from '../scripts/qa/g2h2_trusted_auth_adapter.mjs';
import {createDurableHttpsHarness} from '../scripts/qa/g2h5_durable_https_bff.mjs';

const C=process.env.G2F_POSTGRES_CONTAINER||'';
const DB=process.env.G2F_POSTGRES_DATABASE||'';
if(process.env.JIANSHI_G2H5_SYNTHETIC_ONLY!=='1'||
   process.env.JIANSHI_G2F_EPHEMERAL_ONLY!=='1'||
   !/^[a-f0-9]{12,64}$/.test(C)||DB!=='jianshi_g2f')
 throw new Error('CMS_QA_DISPOSABLE_PG_ONLY');
for(const k of ['DATABASE_URL','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY'])
 if(process.env[k])throw new Error('CMS_REAL_DATABASE_FORBIDDEN');

const A='00000000-0000-4000-8000-00000000a005';
const B='00000000-0000-4000-8000-00000000a004';
const vault=createSessionVault({hmacKey:crypto.randomBytes(32),csrfKey:crypto.randomBytes(32),
  keys:{k1:crypto.randomBytes(32),k2:crypto.randomBytes(32)},activeKeyId:'k2'});
const tokens=new Map(),vhosts=[],pgCalls=[];
const DIR=fs.mkdtempSync(path.join(os.tmpdir(),'jianshi-g2h5-'));
const key=path.join(DIR,'qa.key'),cert=path.join(DIR,'qa.crt');
execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes',
 '-keyout',key,'-out',cert,'-days','1','-subj','/CN=127.0.0.1',
 '-addext','subjectAltName=IP:127.0.0.1'],{stdio:'ignore',timeout:12000});
const tls={key:fs.readFileSync(key),cert:fs.readFileSync(cert)};
let itemId,auth,store,dispatcher,ctx1,ctx2,t1,t2,sa,sb;

function esc(v){return "'"+String(v).replaceAll("'","''")+"'";}
function safeError(error){
 const text=String(error?.message||error);
 const m=/\bCMS_[A-Z_]+\b/.exec(text);
 const e=new Error(m?.[0]||'CMS_SQL_REJECTED');
 e.code=m?.[0]||'CMS_SQL_REJECTED';
 return e;
}
async function query(sql){
 // docker exec uses unix socket INSIDE disposable PG container; never TCP.
 const args=['exec','-i','-u','postgres',C,
  'psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-d',DB];
 return await new Promise((resolve,reject)=>{
  const p=spawn('docker',args,{stdio:['pipe','pipe','pipe']});
  let stdout='',stderr='';
  p.stdout.on('data',x=>{stdout+=x.toString();if(stdout.length>20000)p.kill();});
  p.stderr.on('data',x=>{stderr+=x.toString();if(stderr.length>20000)p.kill();});
  p.on('error',reject);
  p.on('close',code=>code===0?resolve(stdout.trim()):reject(safeError(stderr)));
  p.stdin.on('error',()=>{});
  p.stdin.end(sql);
 });
}
const svc=sql=>"SET ROLE service_role;\n"+sql+"\nRESET ROLE;";
async function scalar(sql){return await query(sql);}
async function scalarSvc(sql){return await scalar(svc(sql));}
async function jsonSvc(sql){return JSON.parse(await scalarSvc(sql));}
function sessionActor(ident){
 const sessionId=crypto.randomUUID();
 const payload={sub:ident,role:'authenticated',aud:'authenticated',
  iss:stagingOrigin+'/auth/v1',session_id:sessionId,
  exp:Math.floor(Date.now()/1000)+3600};
 const token='eyJhbGciOiJIUzI1NiJ9.'+Buffer.from(JSON.stringify(payload)).toString('base64url')+
  '.SYNTHETIC_SIGNATURE_NON_REAL';
 tokens.set(token,{id:ident,sessionId});
 return {token,sessionId};
}
async function mockFetch(url,options){
 const p=new URL(url),b=options.body?JSON.parse(options.body):{};
 pgCalls.push(p.pathname);
 let out;
 if(p.pathname==='/rest/v1/product_feature_flags'){
  out=await jsonSvc("SELECT json_agg(json_build_object('feature_key',feature_key,'enabled',enabled))::text "+
   "FROM public.product_feature_flags WHERE feature_key IN ('account_auth','cms_editor');");
 }else if(p.pathname==='/rest/v1/rpc/auth_launch_ready_v01'){
  out=(await scalarSvc('SELECT public.auth_launch_ready_v01()::text;'))==='true';
 }else if(p.pathname==='/auth/v1/user'){
  const t=options.headers.authorization?.slice(7),info=tokens.get(t);
  if(!info)return {ok:false,json:async()=>({})};
  out={id:info.id,email_confirmed_at:'2026-10-12T00:00:00Z',is_anonymous:false};
 }else if(p.pathname==='/rest/v1/rpc/cms_internal_session_v01'){
  out=(await scalarSvc('SELECT public.cms_internal_session_v01('+
   esc(b.p_user_id)+'::uuid,'+esc(b.p_session_id)+'::uuid)::text;'))==='true';
 }else if(p.pathname==='/rest/v1/rpc/cms_internal_actor_role_v01'){
  out=await scalarSvc('SELECT public.cms_internal_actor_role_v01('+
    esc(b.p_actor)+'::uuid);');
 }else throw new Error('UNEXPECTED_UPSTREAM_ROUTE');
 return {ok:true,json:async()=>out};
}
function makeStore(){
 return Object.freeze({
  async issue({actor,authSession,cookieDigest,csrfDigest,envelope,expiresAt}){
   return (await scalarSvc('SELECT jianshi_cms.bff_issue_session('+
    esc(actor)+'::uuid,'+esc(authSession)+'::uuid,'+esc(cookieDigest)+','+
    esc(envelope.encrypted_jwt)+','+esc(envelope.key_id)+','+
    esc(csrfDigest)+','+esc(expiresAt)+'::timestamptz)::text;'))==='true';
  },
  async consume({cookieDigest,isWrite,csrfDigest}){
   return await jsonSvc('SELECT jianshi_cms.bff_consume_session('+
    esc(cookieDigest)+','+(isWrite?'true':'false')+','+
    (csrfDigest?esc(csrfDigest):'NULL')+')::text;');
  },
  async revoke({cookieDigest}){
   return (await scalarSvc('SELECT jianshi_cms.bff_revoke_session('+
    esc(cookieDigest)+')::text;'))==='true';
  }
 });
}
async function dispatch({kind,actor,data}){
 // This test deliberately touches the real CMS PostgreSQL item and 0058 RPC.
 const item=await jsonSvc("SELECT json_build_object('id',id,'owner',owner_user_id,"+
  "'revision',current_revision,'state',workflow_state)::text "+
  "FROM jianshi_cms.content_items WHERE id="+esc(itemId)+"::uuid;");
 if(actor.userId!==item.owner){const e=new Error('CMS_OWNER_DENIED');e.code=e.message;e.status=403;throw e;}
 if(kind==='READ')return {revision:item.revision,state:item.state};
 if(data.operation!=='RESTORE'){const e=new Error('CMS_OPERATION_DENIED');e.code=e.message;throw e;}
 return await jsonSvc('SELECT public.cms_internal_restore_v01('+
  esc(actor.userId)+'::uuid,'+esc(JSON.stringify({
   content_id:data.content_id,expected_revision:data.expected_revision,
   source_revision:data.source_revision,request_id:data.request_id
  }))+'::jsonb)::text;');
}
async function start(h){
 await new Promise(resolve=>h.server.listen(0,'127.0.0.1',resolve));
 const base='https://127.0.0.1:'+h.server.address().port;
 vhosts.push({h,base});
 return base;
}
async function request(base,endpoint,{session,csrf,method='GET',body,origin,host}={}){
 const u=new URL(base+endpoint),headers={};
 if(session)headers.cookie=session.cookie.split(';')[0];
 if(csrf)headers['x-csrf-token']=csrf;
 if(origin!==undefined)headers.origin=origin;
 if(host)headers.host=host;
 let input;
 if(body!==undefined){
  input=JSON.stringify(body);headers['content-type']='application/json';
  headers['content-length']=Buffer.byteLength(input);
 }
 return await new Promise((resolve,reject)=>{
  const r=https.request(u,{method,headers,rejectUnauthorized:false,timeout:12000},res=>{
   const chunks=[];res.on('data',x=>chunks.push(x));
   res.on('end',()=>{
    try{resolve({http:res.statusCode,body:JSON.parse(Buffer.concat(chunks).toString())});}
    catch{reject(new Error('BAD_RESPONSE_SCHEMA'));}
   });
  });
  r.on('error',reject);r.on('timeout',()=>r.destroy(new Error('TIMEOUT')));
  if(input)r.write(input);
  r.end();
 });
}
function restoreBody(revision){
 return {operation:'RESTORE',content_id:itemId,
  source_revision:1,expected_revision:revision,request_id:crypto.randomUUID()};
}
before(async()=>{
 // All configuration mutations below target disposable GitHub PG only.
 await query("UPDATE public.product_feature_flags SET enabled=true "+
  "WHERE feature_key IN ('account_auth','cms_editor');");
 itemId=await scalar("SELECT id FROM jianshi_cms.content_items "+
  "WHERE content_key='SYNTHETIC_G2F_CONCURRENT';");
 assert.match(itemId,/^[a-f0-9-]{36}$/);
 sa=sessionActor(A);sb=sessionActor(B);
 await query("INSERT INTO auth.sessions(id,user_id,not_after) VALUES "+
  '('+esc(sa.sessionId)+'::uuid,'+esc(A)+"::uuid,now()+interval '10 minutes'),"+
  '('+esc(sb.sessionId)+'::uuid,'+esc(B)+"::uuid,now()+interval '10 minutes');");
 auth=createStagingAuthAdapter({url:stagingOrigin,anonKey:'SYNTHETIC_ANON_ONLY__123456',
  serviceKey:'SYNTHETIC_SERVER_ONLY__123456',fetchImpl:mockFetch});
 store=makeStore();dispatcher=dispatch;
 ctx1=createDurableHttpsHarness({tls,vault,store,identity:auth,dispatch:dispatcher});
 ctx2=createDurableHttpsHarness({tls,vault,store,identity:auth,dispatch:dispatcher});
 t1=await start(ctx1);t2=await start(ctx2);
});
after(async()=>{
 for(const x of vhosts)await new Promise(resolve=>x.h.server.close(resolve));
 fs.rmSync(DIR,{recursive:true,force:true});
});
test('full path across two HTTPS hosts uses one durable encrypted DB session',async()=>{
 const session=await ctx1.issueSyntheticVerifiedSession(sa.token);
 const noCookie=await request(t1,'/qa/api/session');
 assert.equal(noCookie.http,401);
 let r=await request(t1,'/qa/api/session',{session});
 assert.equal(r.http,200);assert.equal(r.body.role,'EDITOR');
 assert.ok(!JSON.stringify(r).includes(sa.token));
 // Same opaque cookie, second BFF instance: no shared JS session memory.
 r=await request(t2,'/qa/api/state',{session});
 assert.equal(r.http,200);assert.equal(r.body.result.revision,3);
 const saved=await jsonSvc('SELECT json_build_object('+
  "'jwt',encrypted_jwt,'cookie',cookie_digest,'csrf',csrf_digest)::text "+
  'FROM jianshi_cms.bff_sessions WHERE cookie_digest='+esc(session.sessionDigest)+';');
 assert.ok(saved.jwt.startsWith('v1.'));
 assert.ok(!saved.jwt.includes(sa.token));
 assert.notEqual(saved.cookie,session.cookie.split(';')[0].split('=')[1]);
 assert.ok(!JSON.stringify(saved).includes(session.csrf));
 r=await request(t2,'/qa/api/action',{method:'POST',session,csrf:session.csrf,
  origin:t2,body:restoreBody(3)});
 assert.equal(r.http,200,JSON.stringify(r.body));
 assert.equal(r.body.result.revision,4);
 assert.equal(await scalar("SELECT (NOT rights_declared AND NOT facts_checked)::text "+
  "FROM jianshi_cms.content_revisions WHERE item_id="+esc(itemId)+"::uuid AND revision=4;"),
 'true');
 assert.ok(pgCalls.includes('/auth/v1/user'));
 assert.ok(pgCalls.includes('/rest/v1/rpc/cms_internal_session_v01'));
 assert.ok(pgCalls.includes('/rest/v1/rpc/cms_internal_actor_role_v01'));
 await ctx2.revokeSyntheticSession(session.sessionDigest);
 r=await request(t1,'/qa/api/state',{session});
 assert.equal(r.http,401);assert.equal(r.body.status,'CMS_SESSION_INVALID');
});
test('another editor cannot read owner record; invalid CSRF never changes revision',async()=>{
 const a=await ctx1.issueSyntheticVerifiedSession(sa.token);
 const b=await ctx2.issueSyntheticVerifiedSession(sb.token);
 let r=await request(t1,'/qa/api/state',{session:b});
 assert.equal(r.http,403);assert.equal(r.body.status,'CMS_OWNER_DENIED');
 r=await request(t1,'/qa/api/action',{method:'POST',session:a,
  csrf:vault.newCsrf(),origin:t1,body:restoreBody(4)});
 assert.equal(r.http,403);assert.equal(r.body.status,'CMS_CSRF_DENIED');
 assert.equal(await scalar("SELECT current_revision::text FROM jianshi_cms.content_items "+
  'WHERE id='+esc(itemId)+'::uuid;'),'4');
 await ctx1.revokeSyntheticSession(a.sessionDigest);
 await ctx2.revokeSyntheticSession(b.sessionDigest);
});
test('HTTP concurrent writes share PostgreSQL atomic quota across BFF instances',async()=>{
 const a=await ctx1.issueSyntheticVerifiedSession(sa.token);
 const calls=Array.from({length:12},(_,i)=>request(i%2?t1:t2,'/qa/api/action',{
  method:'POST',session:a,csrf:a.csrf,origin:i%2?t1:t2,body:restoreBody(4)
 }));
 const results=await Promise.all(calls);
 assert.equal(results.filter(r=>r.http===429&&r.body.status==='CMS_RATE_LIMITED').length,4);
 assert.equal(results.filter(r=>r.http!==429).length,8);
 assert.equal(await scalar('SELECT write_count::text FROM jianshi_cms.bff_sessions '+
  'WHERE cookie_digest='+esc(a.sessionDigest)+';'),'8');
 await query('UPDATE auth.sessions SET not_after=now()-interval \'1 second\' '+
  'WHERE id='+esc(sa.sessionId)+'::uuid;');
 const revoked=await request(t1,'/qa/api/session',{session:a});
 assert.equal(revoked.http,401);assert.equal(revoked.body.status,'CMS_SESSION_REVOKED');
 await ctx1.revokeSyntheticSession(a.sessionDigest);
});
test('closed gate rejects new session issue; no public login or remote credentials',async()=>{
 await query("UPDATE public.product_feature_flags SET enabled=false "+
  "WHERE feature_key IN ('account_auth','cms_editor');");
 await assert.rejects(ctx1.issueSyntheticVerifiedSession(sb.token),
  e=>e.code==='CMS_WRITE_DISABLED');
 const response=await request(t1,'/qa/login');
 assert.equal(response.http,404);
 // The preceding G2-F durable SQL fixture persists one synthetic row.
 assert.equal(await scalar('SELECT count(*)::text FROM jianshi_cms.bff_sessions;'),'5');
 // Every row contains only synthetic encrypted envelopes/digests.
 console.log('G2H5_HTTPS_DURABLE_SQL_CHAIN_PASS',JSON.stringify({
  tls:true,actual_postgres:true,two_instances:true,raw_jwt_database:false,
  daily_source_requests:0,real_gotrue_logins:0
 }));
});
