import test, {after} from 'node:test';
import assert from 'node:assert/strict';
import https from 'node:https';
import {randomBytes} from 'node:crypto';
import {launchSyntheticMtlsProxy,syntheticMtlsBinding}
 from '../scripts/qa/g2h7g_disposable_mtls_harness.mjs';
import {createSyntheticWorkerMtlsStateClient,SYNTHETIC_MTLS_ENDPOINT}
 from '../ops/cms-preview/worker-mtls-state-contract.mjs';
import {createSyntheticWorkerEmailConfirm,WORKER_CONTRACT_ORIGIN as ORIGIN}
 from '../ops/cms-preview/worker-email-crypto.mjs';
import {onRequest} from '../ops/cms-preview/functions/auth/confirm.js';

assert.equal(process.env.JIANSHI_G2F_EPHEMERAL_ONLY,'1');
assert.equal(process.env.JIANSHI_G2H7F_DISPOSABLE_ONLY,'1');
assert.equal(process.env.JIANSHI_G2H7G_MTLS_ONLY,'1');
const upstream=process.env.JIANSHI_G2H7F_URL;
assert.match(upstream||'',/^http:\/\/127\.0\.0\.1:[0-9]+\/v1\/email-state$/);
const proxy=await launchSyntheticMtlsProxy({upstreamUrl:upstream});
after(()=>proxy.close());
const DEFAULT='SYNTHETIC_G2H7G_MTLS_ONLY';
const GOOD='SYNTHETIC_TEST_EMAIL_EDITOR@example.invalid';
const HASH='a'.repeat(64);
const ACTOR='00000000-0000-4000-8000-00000000a001';
const SESSION='00000000-0000-4000-8000-00000000a002';

function client(cert,ca){
 const binding=syntheticMtlsBinding({
  proxy,certificate:cert,trust:ca
 });
 return createSyntheticWorkerMtlsStateClient({
  origin:SYNTHETIC_MTLS_ENDPOINT,profile:DEFAULT,binding
 });
}
function webReq(path,{method='GET',cookie='',headers={}}={}){
 return new Request(ORIGIN+path,{method,headers:{
  host:new URL(ORIGIN).host,...(cookie?{cookie}:{}),...headers
 },...(method==='POST'?{body:''}:{})});
}
function edge(controller,request){
 return onRequest({request,env:{
  JIANSHI_H7D_PROFILE:'SYNTHETIC_CONTRACT_ONLY',
  JIANSHI_H7D_CONTRACT_GATE:'1',
  JIANSHI_H7D_TEST_CONTROLLER:controller
 }});
}
function cookiesOnly(raw){return raw.split(';')[0];}
function setup(cert){
 const stateStore=client(cert);
 const logs={mail:[],verified:0,sessions:0};
 const key=new Uint8Array(randomBytes(32));
 const provider={synthetic:true,
  async requestEmail(args){logs.mail.push(args);return {accepted:true};},
  async verifyTokenHash({tokenHash}){
   assert.equal(tokenHash,HASH);logs.verified++;
   return {access_token:'SYNTHETIC_TOKEN',
    refresh_token:'SYNTHETIC_REFRESH'};
  }
 };
 const verifyIdentity={synthetic:true,async run(access){
  assert.equal(access,'SYNTHETIC_TOKEN');
  return {userId:ACTOR,sessionId:SESSION,role:'EDITOR'};
 }};
 const issueSession={synthetic:true,async run(){
  logs.sessions++;
  return {token:randomBytes(32).toString('base64url'),
   csrf:randomBytes(32).toString('base64url')};
 }};
 return {logs,store:stateStore,async controller(cert2=cert){
  return createSyntheticWorkerEmailConfirm({
   origin:ORIGIN,profile:'SYNTHETIC_H7E_ONLY',
   secret:key,pendingStore:client(cert2),provider,verifyIdentity,
   issueSession
  });
 }};
}
async function stage(f,cert){
 const ctl=await f.controller(cert);
 const issued=await ctl.start({email:GOOD});
 const state=new URL(f.logs.mail.at(-1).redirectTo).searchParams.get('state');
 const startCookie=cookiesOnly(issued.setCookie);
 const link='/auth/confirm?state='+state+'&token_hash='+HASH+'&type=email';
 const landing=await edge(ctl,webReq(link,{cookie:startCookie}));
 assert.equal(landing.status,303);
 const intentCookie=cookiesOnly(landing.headers.getSetCookie()[0]);
 return {ctl,cookie:startCookie+'; '+intentCookie,link,landing};
}
function post(cookie){
 return webReq('/auth/confirm',{method:'POST',cookie,headers:{
  origin:ORIGIN,'sec-fetch-site':'same-origin',
  'content-type':'application/x-www-form-urlencoded'
 }});
}
function issueFixture(){
 return {stateDigest:randomBytes(32).toString('hex'),
  cookieDigest:randomBytes(32).toString('hex'),
  expiresAt:new Date(Date.now()+120000).toISOString()};
}

test('mTLS 1.3 with trusted client A actually invokes disposable private SQL',async()=>{
 const a=client(proxy.certificates.a),data=issueFixture();
 assert.equal(await a.issue(data),true);
 assert.deepEqual(await a.consume({...data,cookieDigest:'f'.repeat(64)}),
  {used:false});
 assert.deepEqual(await a.consume(data),{used:true});
 assert.deepEqual(await a.consume(data),{used:false});
 assert.ok(proxy.metrics.forwarded>=4);
});
test('without certificate, foreign CA, wrong server trust and unauthorized same-CA identity fail',async()=>{
 const data=issueFixture();
 for(const [name,cert,ca,code] of [
  ['missing certificate',undefined,undefined,'CMS_H7G_MTLS_FAILURE'],
  ['foreign certificate',proxy.certificates.foreign,undefined,'CMS_H7G_MTLS_FAILURE'],
  ['server trust mismatch',proxy.certificates.a,proxy.certificates.clientCa,
   'CMS_H7G_MTLS_FAILURE'],
  ['unapproved valid cert',proxy.certificates.c,undefined,
   'CMS_H7G_TRANSPORT_DENIED']
 ]){
  await assert.rejects(client(cert,ca).issue(data),e=>{
   assert.equal(e.code,code,name);return true;
  });
 }
 // A wrong certificate cannot reach the SQL call, even with perfectly valid digests.
 const a=client(proxy.certificates.a);
 assert.equal(await a.issue(data),true);
 assert.deepEqual(await a.consume(data),{used:true});
});
test('forwarded Host, authorization and wrong method never reach PostgreSQL',async()=>{
 const cert=proxy.certificates.a,port=new URL(proxy.origin).port;
 async function raw({path='/v1/email-state',method='POST',headers={}}){
  return new Promise((resolve,reject)=>{
   const req=https.request({
    hostname:'127.0.0.1',port:Number(port),servername:'localhost',
    ca:proxy.certificates.serverCa,key:cert.key,cert:cert.cert,
    rejectUnauthorized:true,minVersion:'TLSv1.3',maxVersion:'TLSv1.3',
    method,path,
    headers:{
     host:'localhost:'+port,'content-type':'application/json',
     'x-jianshi-test-boundary':'SYNTHETIC_H7G_MTLS_ONLY',
     'content-length':'2',...headers
    }
   },r=>{r.resume();r.on('end',()=>resolve(r.statusCode));});
   req.on('error',reject);req.end('{}');
  });
 }
 assert.equal(await raw({headers:{'x-forwarded-host':'evil.invalid'}}),403);
 assert.equal(await raw({headers:{authorization:'Bearer stolen'}}),403);
 assert.equal(await raw({headers:{host:'evil.invalid'}}),403);
 assert.equal(await raw({path:'/v1/admin'}),403);
 assert.equal(await raw({method:'GET'}),403);
});
test('real WebCrypto + edge Request -> mTLS A -> disposable PG -> synthetic actor',async()=>{
 const f=setup(proxy.certificates.a),s=await stage(f);
 assert.equal(f.logs.verified,0);
 assert.equal((await edge(s.ctl,webReq('/auth/confirm',{cookie:s.cookie}))).status,200);
 const ok=await edge(s.ctl,post(s.cookie));
 assert.equal(ok.status,303);
 assert.equal(ok.headers.get('location'),'/cms/');
 assert.equal(f.logs.verified,1);assert.equal(f.logs.sessions,1);
 assert.equal((await edge(s.ctl,post(s.cookie))).status,403);
 assert.equal(f.logs.verified,1);
 assert.equal(JSON.stringify([...ok.headers]).includes(HASH),false);
});
test('two worker identities A+B, eight mTLS sessions: one SQL winner',async()=>{
 const f=setup(proxy.certificates.a),s=await stage(f);
 const b=await f.controller(proxy.certificates.b);
 const outcomes=await Promise.all(Array.from({length:8},(_,i)=>
  edge(i%2?b:s.ctl,post(s.cookie))));
 assert.equal(outcomes.filter(x=>x.status===303).length,1);
 assert.equal(outcomes.filter(x=>x.status===403).length,7);
 assert.equal(f.logs.verified,1);
 assert.equal(f.logs.sessions,1);
 console.log('G2H7G_MTLS_PG_8_WAY_SINGLE_WINNER_PASS');
});
test('rotate service identity B in, revoke A; A cannot consume while B remains valid',async()=>{
 const f=setup(proxy.certificates.a);
 const s=await stage(f,proxy.certificates.a);
 proxy.revokeA();
 const withA=await edge(s.ctl,post(s.cookie));
 assert.equal(withA.status,403);
 assert.equal(f.logs.verified,0);
 const b=await f.controller(proxy.certificates.b);
 const accepted=await edge(b,post(s.cookie));
 assert.equal(accepted.status,303);
 assert.equal(f.logs.verified,1);
 await assert.rejects(client(proxy.certificates.a).issue(issueFixture()),
  e=>e.code==='CMS_H7G_TRANSPORT_DENIED');
 const clientB=client(proxy.certificates.b);
 const fresh=issueFixture();
 assert.equal(await clientB.issue(fresh),true);
 assert.deepEqual(await clientB.consume(fresh),{used:true});
 console.log('G2H7G_CERT_ROTATION_REVOKED_A_PASS');
});
