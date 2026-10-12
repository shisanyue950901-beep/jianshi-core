import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import https from 'node:https';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,readFileSync,rmSync} from 'node:fs';
import {createEphemeralHttpsBff} from '../scripts/qa/g2h3_https_bff.mjs';
import {createStagingAuthAdapter,stagingOrigin} from '../scripts/qa/g2h2_trusted_auth_adapter.mjs';

process.env.JIANSHI_G2H3_SYNTHETIC_ONLY='1';
const DIR=mkdtempSync(path.join(os.tmpdir(),'jianshi-g2h3-'));
const keyPath=path.join(DIR,'test.key'),certPath=path.join(DIR,'test.crt');
execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes',
 '-keyout',keyPath,'-out',certPath,'-days','1','-subj','/CN=127.0.0.1',
 '-addext','subjectAltName=IP:127.0.0.1'],{stdio:'ignore',timeout:12000});
const tls={key:readFileSync(keyPath),cert:readFileSync(certPath)};
after(()=>rmSync(DIR,{recursive:true,force:true}));
const UID={
 A:'00000000-0000-4000-8000-00000000a001',
 B:'00000000-0000-4000-8000-00000000a002',
 REV:'00000000-0000-4000-8000-00000000a003',
 PUB:'00000000-0000-4000-8000-00000000a004'
};
const authKey='synthetic_publishable_not_an_actual_key',serviceKey='synthetic_server_not_an_actual_key_0001';
const jwtIssuer=stagingOrigin+'/auth/v1';

function setup({maxWrites=8}={}){
 let clock=1791800000000;
 const roles=new Map([[UID.A,'EDITOR'],[UID.B,'EDITOR'],[UID.REV,'REVIEWER'],[UID.PUB,'PUBLISHER']]);
 const sessions=new Set(),tokens=new Map(),trace=[];
 let gates=true;
 function makeToken(userId){
  const sessionId=crypto.randomUUID(),payload={sub:userId,session_id:sessionId,
    role:'authenticated',aud:'authenticated',iss:jwtIssuer,exp:Math.floor(clock/1000)+3600};
  const token='eyJhbGciOiJIUzI1NiJ9.'+Buffer.from(JSON.stringify(payload)).toString('base64url')+
    '.SYNTHETIC_SIGNATURE_NO_PRODUCTION_VALIDITY';
  sessions.add(sessionId);tokens.set(token,{userId,sessionId});
  return {token,sessionId};
 }
 const issued={};for(const [name,id] of Object.entries(UID))issued[name]=makeToken(id);
 async function mock(url,options){
  const target=new URL(url),body=options.body?JSON.parse(options.body):null;
  trace.push(target.pathname);
  let value;
  if(target.pathname==='/rest/v1/product_feature_flags'){
   value=[{feature_key:'account_auth',enabled:gates},{feature_key:'cms_editor',enabled:gates}];
  }else if(target.pathname==='/rest/v1/rpc/auth_launch_ready_v01')value=gates;
  else if(target.pathname==='/auth/v1/user'){
   const token=options.headers.authorization?.replace(/^Bearer /,'');
   const match=tokens.get(token);
   if(!match)return {ok:false,json:async()=>({})};
   value={id:match.userId,email_confirmed_at:'2026-10-12T00:00:00Z',is_anonymous:false};
  }else if(target.pathname==='/rest/v1/rpc/cms_internal_session_v01'){
   value=sessions.has(body.p_session_id)&&
    [...tokens.values()].some(x=>x.sessionId===body.p_session_id&&x.userId===body.p_user_id);
  }else if(target.pathname==='/rest/v1/rpc/cms_internal_actor_role_v01'){
   value=roles.get(body.p_actor)||null;
  }else throw Error('unexpected route');
  return {ok:true,json:async()=>value};
 }
 const adapter=createStagingAuthAdapter({url:stagingOrigin,anonKey:authKey,
  serviceKey,fetchImpl:mock,now:()=>clock});
 let document={
  owner:UID.A,version:2,state:'DRAFT',
  revisions:[{version:1,title:'合成初稿',rights:false,facts:false},
             {version:2,title:'合成当前稿',rights:true,facts:true}],
  requests:new Set(),events:[],snapshots:[]
 };
 function reject(code,status=403){const e=new Error(code);e.code=code;e.status=status;throw e;}
 async function dispatch({kind,actor,data}){
  const state=document;
  const canRead=actor.role==='EDITOR'&&actor.userId===state.owner||
    actor.role==='REVIEWER'&&state.state==='IN_REVIEW'||
    actor.role==='PUBLISHER'&&['APPROVED','PUBLISHED','UNPUBLISHED'].includes(state.state);
  if(kind==='READ'){
   if(!canRead)reject('CMS_RESOURCE_FORBIDDEN');
   return {version:state.version,status:state.state,
    revisions:state.revisions.map(r=>({...r})),snapshots:state.snapshots.map(s=>({...s}))};
  }
  if(!canRead && !(actor.role==='REVIEWER'&&state.state==='IN_REVIEW')
       && !(actor.role==='PUBLISHER'&&state.state==='APPROVED'))reject('CMS_RESOURCE_FORBIDDEN');
  if(state.requests.has(data.request_id))reject('CMS_DUPLICATE_REQUEST',409);
  if(state.version!==data.expected_revision)reject('CMS_STALE_REVISION',409);
  const next={...state.revisions.at(-1),version:state.version+1};
  if(data.operation==='EDIT'){
   if(state.state!=='DRAFT')reject('CMS_DRAFT_LOCKED',422);
   if(actor.userId!==state.owner)reject('CMS_OWNER_DENIED');
   next.title=data.title;next.rights=data.rights_attested;next.facts=data.facts_attested;
  }else if(data.operation==='RESTORE'){
   if(state.state!=='DRAFT')reject('CMS_RESTORE_REQUIRES_DRAFT',422);
   if(state.snapshots.some(x=>x.state==='STAGED'))reject('CMS_PUBLISHED_DENIED');
   const source=state.revisions.find(x=>x.version===data.source_revision);
   if(!source)reject('CMS_SOURCE_REVISION_MISSING',422);
   Object.assign(next,{...source,version:state.version+1,rights:false,facts:false});
  }else if(data.operation==='SUBMIT'){
   if(state.state!=='DRAFT')reject('CMS_ILLEGAL_TRANSITION',422);
   state.state='IN_REVIEW';
  }else if(data.operation==='APPROVE'){
   if(state.state!=='IN_REVIEW'||!next.rights||!next.facts)
    reject('CMS_REVIEW_REQUIRED',422);
   state.state='APPROVED';
  }else if(data.operation==='PUBLISH'){
   if(state.state!=='APPROVED')reject('CMS_NOT_APPROVED',422);
   state.state='PUBLISHED';state.snapshots.push({revision:next.version,state:'STAGED'});
  }else if(data.operation==='RETRACT'){
   if(state.state!=='PUBLISHED')reject('CMS_NOT_PUBLISHED',422);
   state.state='UNPUBLISHED';
   state.snapshots.forEach(x=>{if(x.state==='STAGED')x.state='RETRACTED';});
  }else if(data.operation==='REJECT'){
   if(state.state!=='IN_REVIEW')reject('CMS_NOT_IN_REVIEW',422);
   state.state='REJECTED';
  }
  state.version++;state.revisions.push(next);state.requests.add(data.request_id);
  state.events.push({operation:data.operation,revision:state.version,actor:actor.userId});
  return {revision:state.version,status:state.state};
 }
 const harness=createEphemeralHttpsBff({tls,identity:adapter,dispatch,now:()=>clock,maxWrites});
 return {harness,issued,trace,roles,sessions,
  setGates:v=>{gates=v;},clock:x=>{clock=x;},
  snapshot:()=>({version:document.version,state:document.state,events:document.events.length,
    snapshots:document.snapshots.length})};
}
async function serve(ctx){
 await new Promise(resolve=>ctx.harness.server.listen(0,'127.0.0.1',resolve));
 return {base:'https://127.0.0.1:'+ctx.harness.server.address().port,
  stop:()=>new Promise(resolve=>ctx.harness.server.close(resolve))};
}
async function request(base,route,{method='GET',cookie,rawCookie,csrf,origin,body,host,fetchSite}={}){
 const u=new URL(base+route);
 const text=body===undefined?undefined:JSON.stringify(body);
 const headers={};
 if(cookie)headers.cookie=cookie.split(';')[0];
 if(rawCookie)headers.cookie=rawCookie;
 if(csrf)headers['x-csrf-token']=csrf;
 if(origin!==undefined)headers.origin=origin;
 if(host)headers.host=host;
 if(fetchSite)headers['sec-fetch-site']=fetchSite;
 if(text!==undefined){headers['content-type']='application/json';headers['content-length']=Buffer.byteLength(text);}
 return await new Promise((resolve,reject)=>{
  const req=https.request(u,{method,headers,rejectUnauthorized:false,timeout:5000},res=>{
   const chunks=[];
   res.on('data',chunk=>chunks.push(chunk));
   res.on('end',()=>{
    let parsed;
    try{parsed=JSON.parse(Buffer.concat(chunks).toString());}
    catch{parsed=null;}
    resolve({http:res.statusCode,headers:res.headers,body:parsed});
   });
  });
  req.on('error',reject);req.on('timeout',()=>req.destroy(Error('test timeout')));
  if(text)req.write(text);
  req.end();
 });
}
async function write(base,record,op,revision,extra={},headers={}){
 return request(base,'/qa/api/action',{method:'POST',cookie:record.setCookie,
  csrf:record.csrf,origin:base,body:{operation:op,expected_revision:revision,
    request_id:crypto.randomUUID(),...extra},...headers});
}
test('actual TLS: Secure HttpOnly session and strict host; no public login route',async()=>{
 const c=setup(),s=await serve(c);
 try{
  const a=await c.harness.issueVerifiedTestSession(c.issued.A.token);
  assert.match(a.setCookie,/Secure; HttpOnly; SameSite=Strict; Path=\/qa/);
  const r=await request(s.base,'/qa/api/session',{cookie:a.setCookie});
  assert.equal(r.http,200);assert.equal(r.body.role,'EDITOR');
  assert.equal(r.body.synthetic,true);
  assert.match(r.headers['strict-transport-security'],/max-age=/);
  assert.match(r.headers['content-security-policy'],/frame-ancestors 'none'/);
  assert.ok(!JSON.stringify(r).includes(c.issued.A.token));
  assert.equal((await request(s.base,'/qa/api/state')).http,401);
  assert.equal((await request(s.base,'/qa/login',{cookie:a.setCookie})).http,405);
  assert.equal((await request(s.base,'/qa/api/session',{cookie:a.setCookie,host:'bad.test'})).http,403);
  assert.equal((await request(s.base,'/qa/api/session',{rawCookie:a.setCookie.split(';')[0]+'; '+a.setCookie.split(';')[0]})).http,401);
 }finally{await s.stop();}
});
test('real HTTPS action enforces CSRF, Origin, Fetch-Site, strict payload and RBAC',async()=>{
 const c=setup(),s=await serve(c);
 try{
  const a=await c.harness.issueVerifiedTestSession(c.issued.A.token);
  const b=await c.harness.issueVerifiedTestSession(c.issued.B.token);
  const before=c.snapshot();
  let r=await write(s.base,a,'EDIT',2,{title:'注入尝试',rights_attested:true,facts_attested:true},{csrf:'wrong'});
  assert.equal(r.body.status,'CMS_CSRF_DENIED');
  r=await write(s.base,a,'EDIT',2,{title:'注入尝试',rights_attested:true,facts_attested:true},{origin:'https://evil.invalid'});
  assert.equal(r.body.status,'CMS_ORIGIN_DENIED');
  r=await write(s.base,a,'EDIT',2,{title:'注入尝试',rights_attested:true,facts_attested:true},{fetchSite:'cross-site'});
  assert.equal(r.body.status,'CMS_FETCH_SITE_DENIED');
  r=await write(s.base,a,'EDIT',2,{title:'注入尝试',rights_attested:true,facts_attested:true,actor:UID.A});
  assert.equal(r.body.status,'CMS_PAYLOAD_DENIED');
  r=await write(s.base,b,'EDIT',2,{title:'别人的内容',rights_attested:true,facts_attested:true});
  assert.equal(r.body.status,'CMS_RESOURCE_FORBIDDEN');
  assert.equal((await request(s.base,'/qa/api/state',{cookie:b.setCookie})).body.status,'CMS_RESOURCE_FORBIDDEN');
  assert.deepEqual(c.snapshot(),before);
 }finally{await s.stop();}
});
test('real HTTPS A/B reviewer/publisher scopes, restore recheck, safe stages',async()=>{
 const c=setup({maxWrites:20}),s=await serve(c);
 try{
  const author=await c.harness.issueVerifiedTestSession(c.issued.A.token);
  const review=await c.harness.issueVerifiedTestSession(c.issued.REV.token);
  const publisher=await c.harness.issueVerifiedTestSession(c.issued.PUB.token);
  let r=await write(s.base,author,'RESTORE',2,{source_revision:1});
  assert.equal(r.http,200);assert.equal(r.body.result.revision,3);
  assert.equal((await request(s.base,'/qa/api/state',{cookie:author.setCookie})).body.revisions.at(-1).rights,false);
  r=await write(s.base,author,'SUBMIT',3);assert.equal(r.http,200);
  r=await write(s.base,review,'APPROVE',4);assert.equal(r.body.status,'CMS_REVIEW_REQUIRED');
  assert.equal((await request(s.base,'/qa/api/state',{cookie:review.setCookie})).http,200);
  assert.equal((await request(s.base,'/qa/api/state',{cookie:publisher.setCookie})).http,403);
  // New fixture for the successful editor-recheck/approval path.
  // Separate contexts avoid pretending a rejected draft was silently reopened.
 }finally{await s.stop();}
 const d=setup({maxWrites:20}),t=await serve(d);
 try{
  const a=await d.harness.issueVerifiedTestSession(d.issued.A.token);
  const reviewer=await d.harness.issueVerifiedTestSession(d.issued.REV.token);
  const publisher=await d.harness.issueVerifiedTestSession(d.issued.PUB.token);
  assert.equal((await write(t.base,a,'EDIT',2,{title:'复核版',rights_attested:true,facts_attested:true})).http,200);
  assert.equal((await write(t.base,a,'SUBMIT',3)).http,200);
  assert.equal((await write(t.base,reviewer,'APPROVE',4)).http,200);
  assert.equal((await request(t.base,'/qa/api/state',{cookie:publisher.setCookie})).http,200);
  assert.equal((await write(t.base,publisher,'PUBLISH',5)).http,200);
  assert.equal((await write(t.base,publisher,'RETRACT',6)).http,200);
  assert.deepEqual((await request(t.base,'/qa/api/state',{cookie:publisher.setCookie})).body.snapshots,
   [{revision:6,state:'RETRACTED'}]);
 }finally{await t.stop();}
});
test('verified GoTrue adapter rechecks session/role on every request, no stale grants',async()=>{
 const c=setup(),s=await serve(c);
 try{
  const a=await c.harness.issueVerifiedTestSession(c.issued.A.token);
  assert.equal((await request(s.base,'/qa/api/state',{cookie:a.setCookie})).http,200);
  c.roles.delete(UID.A);
  const blocked=await request(s.base,'/qa/api/state',{cookie:a.setCookie});
  assert.equal(blocked.http,401);assert.equal(blocked.body.status,'CMS_IDENTITY_REVOKED');
  assert.equal((await request(s.base,'/qa/api/session',{cookie:a.setCookie})).http,401);
  const b=await c.harness.issueVerifiedTestSession(c.issued.B.token);
  c.sessions.delete(c.issued.B.sessionId);
  assert.equal((await request(s.base,'/qa/api/session',{cookie:b.setCookie})).http,401);
  const rev=await c.harness.issueVerifiedTestSession(c.issued.REV.token);
  c.setGates(false);
  assert.equal((await request(s.base,'/qa/api/session',{cookie:rev.setCookie})).http,401);
  assert.equal(c.harness.activeTestSessions(),0);
 }finally{await s.stop();}
});
test('cookie revocation, expiry and server rate limiting are effective across HTTPS',async()=>{
 const c=setup({maxWrites:2}),s=await serve(c);
 try{
  const a=await c.harness.issueVerifiedTestSession(c.issued.A.token);
  assert.equal((await write(s.base,a,'EDIT',2,{title:'版本三',rights_attested:true,facts_attested:true})).http,200);
  assert.equal((await write(s.base,a,'SUBMIT',3)).http,200);
  assert.equal((await write(s.base,a,'SUBMIT',3)).body.status,'CMS_RATE_LIMITED');
  c.harness.revokeTestSession(a.id);
  assert.equal((await request(s.base,'/qa/api/session',{cookie:a.setCookie})).http,401);
  const b=await c.harness.issueVerifiedTestSession(c.issued.B.token);
  c.clock(1791800000000+15*60*1000+1);
  assert.equal((await request(s.base,'/qa/api/session',{cookie:b.setCookie})).body.status,'CMS_SESSION_EXPIRED');
 }finally{await s.stop();}
});
