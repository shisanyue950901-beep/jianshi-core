import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import {createDisposableEmailStateHttpClient}
 from '../ops/cms-preview/worker-pg-disposable-http.mjs';
import {createSyntheticWorkerEmailConfirm,WORKER_CONTRACT_ORIGIN as ORIGIN}
 from '../ops/cms-preview/worker-email-crypto.mjs';
import {onRequest} from '../ops/cms-preview/functions/auth/confirm.js';

const URL=process.env.JIANSHI_G2H7F_URL||'';
const KEY='SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET';
const USER='00000000-0000-4000-8000-00000000a001';
const SESSION='00000000-0000-4000-8000-00000000a002';
const HASH='a'.repeat(64);
const TOKEN='SYNTHETIC_ACCESS_ONLY_NO_REAL_JWT';
const REFRESH='SYNTHETIC_REFRESH_ONLY_NO_REAL_SESSION';
const EMAIL='SYNTHETIC_G2H7F_EDITOR@example.invalid';
assert.equal(process.env.JIANSHI_G2F_EPHEMERAL_ONLY,'1');
assert.equal(process.env.JIANSHI_G2H7F_DISPOSABLE_ONLY,'1');
assert.match(URL,/^http:\/\/127\.0\.0\.1:\d+\/v1\/email-state$/);
for(const name of [
 'SUPABASE_URL','SUPABASE_DB_URL','DATABASE_URL','SUPABASE_SERVICE_ROLE_KEY',
 'SUPABASE_ACCESS_TOKEN','CLOUDFLARE_API_TOKEN'
])assert.equal(process.env[name],undefined);
function client(){
 return createDisposableEmailStateHttpClient({url:URL,
  profile:'SYNTHETIC_H7F_DISPOSABLE_PG',key:KEY});
}
function context(controller,request){
 return {request,env:{
  JIANSHI_H7D_PROFILE:'SYNTHETIC_CONTRACT_ONLY',
  JIANSHI_H7D_CONTRACT_GATE:'1',
  JIANSHI_H7D_TEST_CONTROLLER:controller
 }};
}
function request(path,{method='GET',headers={},body}={}){
 return new Request(ORIGIN+path,{method,headers:{host:new URL(ORIGIN).host,...headers},
  ...(body===undefined?{}:{body})});
}
function cookie(line){return line.split(';')[0];}
function setup(){
 const secret=new Uint8Array(randomBytes(32)),log={sent:[],verified:[],issued:[]};
 const pendingStore=client();
 const provider={synthetic:true,
  async requestEmail({email,redirectTo}){log.sent.push({email,redirectTo});return {accepted:true};},
  async verifyTokenHash({tokenHash}){assert.equal(tokenHash,HASH);
   log.verified.push(true);return {access_token:TOKEN,refresh_token:REFRESH};}
 };
 const verifyIdentity={synthetic:true,async run(token){
  assert.equal(token,TOKEN);return {userId:USER,sessionId:SESSION,role:'EDITOR'};
 }};
 const issueSession={synthetic:true,async run(v){
  assert.equal(v.actor.userId,USER);log.issued.push(true);
  return {token:randomBytes(32).toString('base64url'),
   csrf:randomBytes(32).toString('base64url')};
 }};
 return {log,pendingStore,async controller(){
  return createSyntheticWorkerEmailConfirm({origin:ORIGIN,
   profile:'SYNTHETIC_H7E_ONLY',secret,pendingStore,provider,
   verifyIdentity,issueSession});
 }};
}
async function staged(f){
 const controller=await f.controller(),started=await controller.start({email:EMAIL});
 assert.equal(started.accepted,true);
 const state=new URL(f.log.sent.at(-1).redirectTo).searchParams.get('state');
 const url='/auth/confirm?state='+state+'&token_hash='+HASH+'&type=email';
 const stateCookie=cookie(started.setCookie);
 const landed=await onRequest(context(controller,request(url,{headers:{cookie:stateCookie}})));
 assert.equal(landed.status,303);
 assert.equal(landed.headers.get('location'),'/auth/confirm');
 const intentCookie=cookie(landed.headers.getSetCookie()[0]);
 const cookies=stateCookie+'; '+intentCookie;
 return {controller,cookies,landed};
}
function post(cookies,headers={}){
 return request('/auth/confirm',{method:'POST',body:'',headers:{
  cookie:cookies,origin:ORIGIN,'sec-fetch-site':'same-origin',
  'content-type':'application/x-www-form-urlencoded',...headers
 }});
}
test('only fake-key localhost disposable transport is constructible',()=>{
 for(const bad of [
  {url:'https://apuibjhxinumxbfnqlkp.supabase.co/rest/v1/rpc/bff_consume_email_state_v01'},
  {url:'https://jianshi-bua.pages.dev/v1/email-state'},
  {url:'http://127.0.0.1:99999/v1/email-state'},
  {url:'http://127.0.0.1:1234/v1/email-state?redirect=http://evil.invalid'},
  {url:'http://localhost:1234/v1/email-state'},
  {profile:'PRODUCTION'},
  {key:'sb_secret_should_never_be_used'},
  {key:'SYNTHETIC_THIRD_PARTY_KEY_SHOULD_FAIL'}
 ]){
  assert.throws(()=>createDisposableEmailStateHttpClient({
   url:URL,profile:'SYNTHETIC_H7F_DISPOSABLE_PG',key:KEY,...bad
  }));
 }
});
test('real SQL issue and consume through live localhost HTTP, including wrong cookie',async()=>{
 const store=client();
 const state=randomBytes(32).toString('hex');
 const cookieHash=randomBytes(32).toString('hex');
 assert.equal(await store.issue({stateDigest:state,cookieDigest:cookieHash,
  expiresAt:new Date(Date.now()+120000).toISOString()}),true);
 assert.deepEqual(await store.consume({
  stateDigest:state,cookieDigest:'e'.repeat(64)}),{used:false});
 assert.deepEqual(await store.consume({stateDigest:state,cookieDigest:cookieHash}),{used:true});
 assert.deepEqual(await store.consume({stateDigest:state,cookieDigest:cookieHash}),{used:false});
 await assert.rejects(store.issue({stateDigest:state,cookieDigest:cookieHash,
  expiresAt:new Date(Date.now()+120000).toISOString()}));
});
test('real HTTP denies wrong bearer, unexpected endpoint and untrusted payload',async()=>{
 const wrong=await fetch(URL,{method:'POST',
  headers:{authorization:'Bearer SYNTHETIC_BUT_NOT_VALID',
   'x-jianshi-test-boundary':'SYNTHETIC_H7F_ONLY',
   'content-type':'application/json'},
  body:JSON.stringify({action:'consume',stateDigest:'a'.repeat(64),
   cookieDigest:'b'.repeat(64)})});
 assert.equal(wrong.status,403);
 const unknown=await fetch(URL.replace('/v1/email-state','/v1/admin'),{
  method:'POST',headers:{authorization:'Bearer '+KEY,
  'x-jianshi-test-boundary':'SYNTHETIC_H7F_ONLY',
  'content-type':'application/json'},body:'{}'});
 assert.equal(unknown.status,403);
 assert.equal((await wrong.text()).includes(KEY),false);
 const noRead=await fetch(URL);
 assert.equal(noRead.status,404);
});
test('Worker -> HTTP -> real PostgreSQL -> synthetic provider: one POST, replay 403',async()=>{
 const f=setup(),s=await staged(f);
 assert.equal(f.log.verified.length,0);
 const page=await onRequest(context(s.controller,
  request('/auth/confirm',{headers:{cookie:s.cookies}})));
 assert.equal(page.status,200);
 const accepted=await onRequest(context(s.controller,post(s.cookies)));
 assert.equal(accepted.status,303);
 assert.equal(accepted.headers.get('location'),'/cms/');
 assert.equal(f.log.verified.length,1);
 assert.equal(f.log.issued.length,1);
 const again=await onRequest(context(s.controller,post(s.cookies)));
 assert.equal(again.status,403);
 assert.equal(f.log.verified.length,1);
 const content=JSON.stringify([...accepted.headers]);
 for(const secret of [HASH,TOKEN,REFRESH,EMAIL,KEY])
  assert.equal(content.includes(secret),false);
});
test('8 separate HTTP/psql transactions, 2 Worker instances: exactly one redeem',async()=>{
 const f=setup(),s=await staged(f),second=await f.controller();
 const results=await Promise.all(Array.from({length:8},(_,i)=>
  onRequest(context(i%2?second:s.controller,post(s.cookies)))));
 assert.equal(results.filter(x=>x.status===303).length,1);
 assert.equal(results.filter(x=>x.status===403).length,7);
 assert.equal(f.log.verified.length,1);
 assert.equal(f.log.issued.length,1);
 console.log('G2H7F_REAL_PG_HTTP_8_WAY_ONE_WINNER_PASS');
});
test('wrong browser and cross-origin HTTP POST never burn real SQL state',async()=>{
 const f=setup(),s=await staged(f);
 const wrong='__Host-jianshi_mail_state='+randomBytes(32).toString('base64url');
 const intent=s.cookies.split('; ')[1];
 const result=await onRequest(context(s.controller,
  post(wrong+'; '+intent)));
 assert.equal(result.status,403);
 const cross=await onRequest(context(s.controller,
  post(s.cookies,{origin:'https://evil.invalid'})));
 assert.equal(cross.status,403);
 assert.equal(f.log.verified.length,0);
 const correct=await onRequest(context(s.controller,post(s.cookies)));
 assert.equal(correct.status,303);
 assert.equal(f.log.verified.length,1);
});
