// G2-H: loopback-only CMS BFF contract harness, not a real login/deployment.
// Node 20 built-ins only. No Supabase/network adapter; all content synthetic.
import http from 'node:http';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const DIR=path.dirname(fileURLToPath(import.meta.url));
const MAX_BODY=8192,TTL=15*60*1000,COOKIE='jianshi_g2h_qa';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ACTORS=new Map([
 ['SYNTHETIC_AUTHOR_A','EDITOR'],['SYNTHETIC_AUTHOR_B','EDITOR'],
 ['SYNTHETIC_REVIEWER','REVIEWER'],['SYNTHETIC_PUBLISHER','PUBLISHER']]);
const FIELDS={
 EDIT:['operation','request_id','expected_revision','title','rights_attested','facts_attested'],
 SUBMIT:['operation','request_id','expected_revision'],
 APPROVE:['operation','request_id','expected_revision'],
 REJECT:['operation','request_id','expected_revision'],
 PUBLISH:['operation','request_id','expected_revision'],
 RETRACT:['operation','request_id','expected_revision'],
 RESTORE:['operation','request_id','expected_revision','source_revision']
};
function gate(ok,code,status=403){
 if(!ok){const e=new Error(code);e.code=code;e.status=status;throw e;}
}
function fresh(){
 return {id:'SYNTHETIC_DOCUMENT_01',author:'SYNTHETIC_AUTHOR_A',
  status:'DRAFT',version:2,lastReviewer:null,
  revisions:[{number:1,title:'合成初稿',rights:false,facts:false},
             {number:2,title:'合成当前稿',rights:true,facts:true}],
  events:[{revision:1,action:'CREATE'},{revision:2,action:'EDIT'}],
  snapshots:[],requests:[]};
}
function publicState(doc){
 return {document_id:doc.id,status:doc.status,version:doc.version,
  revisions:doc.revisions.map(x=>({...x})),
  events:doc.events.map(x=>({...x})),snapshots:doc.snapshots.map(x=>({...x}))};
}
function apply(doc,actor,role,body){
 const name=body.operation;
 gate(typeof name==='string'&&Object.hasOwn(FIELDS,name),'CMS_OPERATION_INVALID',422);
 const expected=FIELDS[name];
 gate(Object.keys(body).length===expected.length&&Object.keys(body).every(k=>expected.includes(k)),
      'CMS_PAYLOAD_ALLOWLIST',422);
 gate(UUID.test(body.request_id),'CMS_REQUEST_ID_INVALID',422);
 gate(Number.isInteger(body.expected_revision)&&body.expected_revision>=1,'CMS_REVISION_INVALID',422);
 gate(!doc.requests.includes(body.request_id),'CMS_DUPLICATE_REQUEST',409);
 gate(doc.version===body.expected_revision,'CMS_STALE_REVISION',409);
 if(['EDIT','SUBMIT','RESTORE'].includes(name)){
  gate(role==='EDITOR'&&actor===doc.author,'CMS_OWNER_DENIED');
 }else if(['APPROVE','REJECT'].includes(name)){
  gate(role==='REVIEWER'&&actor!==doc.author,'CMS_INDEPENDENT_REVIEW_REQUIRED');
 }else{
  gate(role==='PUBLISHER'&&actor!==doc.author,'CMS_PUBLISHER_DENIED');
 }
 const current=doc.revisions.at(-1);
 let next={...current,number:doc.version+1};
 const from=doc.status;
 if(name==='EDIT'){
  gate(from==='DRAFT','CMS_DRAFT_LOCKED',422);
  gate(typeof body.title==='string'&&body.title.length>=2&&body.title.length<=80 &&
   typeof body.rights_attested==='boolean'&&typeof body.facts_attested==='boolean',
   'CMS_EDIT_VALIDATION',422);
  next.title=body.title;next.rights=body.rights_attested;next.facts=body.facts_attested;
 }else if(name==='RESTORE'){
  gate(['DRAFT','REJECTED'].includes(from),'CMS_RESTORE_REQUIRES_DRAFT',422);
  gate(Number.isInteger(body.source_revision)&&body.source_revision>=1 &&
       body.source_revision<doc.version,'CMS_INVALID_SOURCE_REVISION',422);
  gate(!doc.snapshots.some(s=>s.lifecycle==='STAGED'),'CMS_PUBLIC_SNAPSHOT_BLOCKS_RESTORE');
  const source=doc.revisions.find(v=>v.number===body.source_revision);
  gate(!!source,'CMS_SOURCE_REVISION_NOT_FOUND',422);
  next={...source,number:doc.version+1,rights:false,facts:false};
  doc.lastReviewer=null;doc.status='DRAFT';
 }else if(name==='SUBMIT'){
  gate(from==='DRAFT','CMS_ILLEGAL_TRANSITION',422);doc.status='IN_REVIEW';
 }else if(['APPROVE','REJECT'].includes(name)){
  gate(from==='IN_REVIEW','CMS_ILLEGAL_TRANSITION',422);
  if(name==='APPROVE')gate(current.rights&&current.facts,'CMS_RECHECK_REQUIRED',422);
  doc.status=name==='APPROVE'?'APPROVED':'REJECTED';doc.lastReviewer=actor;
 }else if(name==='PUBLISH'){
  gate(from==='APPROVED'&&current.rights&&current.facts,'CMS_NOT_APPROVED',422);
  doc.status='PUBLISHED';doc.snapshots.push({revision:next.number,lifecycle:'STAGED'});
 }else if(name==='RETRACT'){
  gate(from==='PUBLISHED','CMS_ILLEGAL_TRANSITION',422);
  doc.status='UNPUBLISHED';
  doc.snapshots.forEach(s=>{if(s.lifecycle==='STAGED')s.lifecycle='RETRACTED';});
 }
 doc.version++;doc.revisions.push(next);
 doc.events.push({revision:doc.version,action:name});doc.requests.push(body.request_id);
}
const H={
 'cache-control':'no-store, max-age=0','x-content-type-options':'nosniff',
 'x-frame-options':'DENY','referrer-policy':'no-referrer',
 'content-security-policy':"default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
};
function reply(res,status,body){
 res.writeHead(status,{'content-type':'application/json; charset=utf-8',...H});
 res.end(JSON.stringify(body));
}
function allowFixture(){
 gate(process.env.JIANSHI_G2H_SYNTHETIC_ONLY==='1','CMS_QA_ENV_DISABLED',503);
 for(const key of ['SUPABASE_SERVICE_ROLE_KEY','SUPABASE_URL','DATABASE_URL','SUPABASE_DB_URL']){
  gate(!process.env[key],'CMS_EXTERNAL_CREDENTIALS_FORBIDDEN',503);
 }
}
export function createQaServer({now=()=>Date.now(),maxRequests=8}={}){
 allowFixture();
 const sessions=new Map(),usage=new Map();
 let current=fresh();
 const server=http.createServer(async (req,res)=>{
  try{
   const port=server.address()?.port;
   const host=req.headers.host;
   gate(host==='127.0.0.1:'+port,'CMS_HOST_DENIED');
   const u=new URL(req.url,'http://'+host);
   gate(!u.search&&!u.hash,'CMS_QUERY_DENIED',400);
   if(req.method==='GET'&&['/qa/cms','/qa/cms/app.js','/qa/cms/style.css'].includes(u.pathname)){
    const name=u.pathname==='/qa/cms'?'index.html':u.pathname.endsWith('app.js')?'app.js':'style.css';
    const type=name.endsWith('.js')?'text/javascript':name.endsWith('.css')?'text/css':'text/html';
    res.writeHead(200,{'content-type':type+'; charset=utf-8',...H,
      'x-robots-tag':'noindex, nofollow'});
    res.end(fs.readFileSync(path.join(DIR,name)));return;
   }
   gate(u.pathname.startsWith('/qa/api/'),'CMS_ROUTE_NOT_FOUND',404);
   const cookiePattern=new RegExp('(?:^|;\\s*)'+COOKIE+'=([a-f0-9]{64})(?:;|$)');
   const match=cookiePattern.exec(req.headers.cookie||'');
   const session=match?sessions.get(match[1]):null;
   gate(!!session&&now()<session.expiresAt,'CMS_SESSION_INVALID',401);
   if(req.method==='GET'&&u.pathname==='/qa/api/session'){
    return reply(res,200,{synthetic:true,role:session.role,csrf:session.csrf});
   }
   if(req.method==='GET'&&u.pathname==='/qa/api/state'){
    const canRead=session.role==='EDITOR'&&session.actor===current.author ||
      session.role==='REVIEWER'&&current.status==='IN_REVIEW' ||
      session.role==='PUBLISHER'&&['APPROVED','PUBLISHED','UNPUBLISHED'].includes(current.status);
    gate(canRead,'CMS_RESOURCE_FORBIDDEN',403);
    return reply(res,200,publicState(current));
   }
   gate(req.method==='POST'&&u.pathname==='/qa/api/action','CMS_METHOD_OR_ROUTE_DENIED',405);
   gate(req.headers.origin==='http://127.0.0.1:'+port,'CMS_ORIGIN_DENIED',403);
   gate(!req.headers['sec-fetch-site']||req.headers['sec-fetch-site']==='same-origin',
        'CMS_FETCH_SITE_DENIED',403);
   gate(req.headers['x-csrf-token']===session.csrf,'CMS_CSRF_DENIED',403);
   gate((req.headers['content-type']||'').toLowerCase().split(';')[0]==='application/json',
        'CMS_JSON_REQUIRED',415);
   const state=usage.get(session.id)||{since:now(),count:0};
   if(now()-state.since>=60_000){state.since=now();state.count=0;}
   state.count++;usage.set(session.id,state);
   gate(state.count<=maxRequests,'CMS_RATE_LIMITED',429);
   let raw='';
   for await(const part of req){
    raw+=part.toString('utf8');
    gate(Buffer.byteLength(raw,'utf8')<=MAX_BODY,'CMS_BODY_TOO_LARGE',413);
   }
   let body;try{body=JSON.parse(raw);}catch{gate(false,'CMS_INVALID_JSON',400);}
   gate(body&&typeof body==='object'&&!Array.isArray(body),'CMS_INVALID_PAYLOAD',422);
   const candidate=structuredClone(current);
   apply(candidate,session.actor,session.role,body);
   current=candidate;
   return reply(res,200,{status:'SYNTHETIC_OK',...publicState(current)});
  }catch(err){
   const code=typeof err.code==='string'&&/^CMS_[A-Z_]+$/.test(err.code)?err.code:'CMS_FAIL_CLOSED';
   reply(res,err.status||503,{status:code});
  }
 });
 return {
  server,
  issueFixture(actor){
   gate(ACTORS.has(actor),'CMS_SYNTHETIC_ACTOR_ONLY');
   const id=crypto.randomBytes(32).toString('hex'),csrf=crypto.randomBytes(24).toString('hex');
   const session={id,csrf,actor,role:ACTORS.get(actor),expiresAt:now()+TTL};
   sessions.set(id,session);
   return {cookie:COOKIE+'='+id+'; HttpOnly; SameSite=Strict; Path=/qa',
     csrf,actor,role:session.role,id};
  },
  revokeFixture(id){sessions.delete(id);usage.delete(id);},
  resetFixtures(){current=fresh();},snapshot(){return publicState(current);}
 };
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 allowFixture();const harness=createQaServer();
 harness.server.listen(0,'127.0.0.1',()=>console.log('G2-H synthetic-only loopback QA ready'));
}
