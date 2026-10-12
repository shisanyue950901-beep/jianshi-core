import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes,createHmac,hkdfSync,createDecipheriv} from 'node:crypto';
import {createSyntheticWorkerEmailConfirm,WORKER_CONTRACT_ORIGIN as ORIGIN}
 from '../ops/cms-preview/worker-email-crypto.mjs';
import {onRequest} from '../ops/cms-preview/functions/auth/confirm.js';
const EMAIL='SYNTHETIC_EDITOR@example.invalid';
const HASH='a'.repeat(64),TOKEN='SYNTHETIC_ACCESS_JWT_ONLY';
const REFRESH='SYNTHETIC_REFRESH_NOT_FOR_BROWSER';
const USER='00000000-0000-4000-8000-00000000a001';
const AUTH='00000000-0000-4000-8000-00000000a002';
const hex=s=>s.toString('hex');
const statePattern=/^[A-Za-z0-9_-]{43}$/;
function fixture({fail='',time=1791800000000}={}){
 const secret=new Uint8Array(randomBytes(32)),records=new Map();
 let current=time;
 const log={issue:[],emails:[],redeem:[],sessions:[],actors:[]};
 const pendingStore={
  synthetic:true,
  async issue(v){
   if(records.has(v.stateDigest))return false;
   records.set(v.stateDigest,{...v,used:false});log.issue.push(v);return true;
  },
  async consume({stateDigest,cookieDigest,at}){
   const record=records.get(stateDigest);
   if(!record||record.used||record.cookieDigest!==cookieDigest||
    Date.parse(at)>=Date.parse(record.expiresAt))return {used:false};
   record.used=true;return {used:true};
  }
 };
 const provider={synthetic:true,
  async requestEmail(v){
   log.emails.push(v);
   if(fail==='send')throw Error('SYNTHETIC_UPSTREAM_MAIL_SECRET');
   return {accepted:true};
  },
  async verifyTokenHash({tokenHash}){
   log.redeem.push(tokenHash);
   if(fail==='verify')throw Error('SYNTHETIC_UPSTREAM_VERIFY_SECRET');
   return {access_token:TOKEN,refresh_token:REFRESH};
  }
 };
 const verifyIdentity={synthetic:true,async run(jwt){
  assert.equal(jwt,TOKEN);
  log.actors.push(true);
  if(fail==='actor')return {userId:USER,sessionId:AUTH,role:'ADMIN'};
  return {userId:USER,sessionId:AUTH,role:'EDITOR'};
 }};
 const issueSession={synthetic:true,async run(v){
  log.sessions.push(v);
  if(fail==='session')throw Error('SYNTHETIC_SESSION_SECRET');
  return {token:randomBytes(32).toString('base64url'),
   csrf:randomBytes(32).toString('base64url')};
 }};
 const make=()=>createSyntheticWorkerEmailConfirm({
  origin:ORIGIN,profile:'SYNTHETIC_H7E_ONLY',secret,
  pendingStore,provider,verifyIdentity,issueSession,now:()=>current
 });
 return {make,log,secret,records,advance:ms=>current+=ms};
}
function cookie(line){return line.split(';')[0];}
function req(path,options={}){
 const {method='GET',headers={},body}=options;
 return new Request(ORIGIN+path,{method,headers:{host:new URL(ORIGIN).host,...headers},
  ...(body===undefined?{}:{body})});
}
function env(controller){return {JIANSHI_H7D_PROFILE:'SYNTHETIC_CONTRACT_ONLY',
 JIANSHI_H7D_CONTRACT_GATE:'1',JIANSHI_H7D_TEST_CONTROLLER:controller};}
async function mailStart(f){
 const controller=await f.make(),begin=await controller.start({email:EMAIL});
 const stateCookie=cookie(begin.setCookie);
 const state=new URL(f.log.emails.at(-1).redirectTo).searchParams.get('state');
 const path='/auth/confirm?state='+state+'&token_hash='+HASH+'&type=email';
 return {controller,begin,stateCookie,path,state};
}
async function landing(f){
 const data=await mailStart(f);
 const get=await onRequest({request:req(data.path,{headers:{cookie:data.stateCookie}}),
  env:env(data.controller)});
 assert.equal(get.status,303);
 assert.equal(get.headers.get('location'),'/auth/confirm');
 const intentCookie=cookie(get.headers.getSetCookie()[0]);
 return {...data,get,intentCookie,cookies:data.stateCookie+'; '+intentCookie};
}
function post(cookieHeader,headers={}){
 return req('/auth/confirm',{method:'POST',
  headers:{cookie:cookieHeader,origin:ORIGIN,'sec-fetch-site':'same-origin',
   'content-type':'application/x-www-form-urlencoded',...headers},body:''});
}
async function reject(p,code){
 await assert.rejects(p,e=>{assert.equal(e.code,code);return true;});
}
test('no live origin, wrong key, or non-synthetic adapters can construct controller',async()=>{
 const f=fixture();
 const defaults={origin:ORIGIN,profile:'SYNTHETIC_H7E_ONLY',
  secret:f.secret,pendingStore:{synthetic:true,issue(){},consume(){}},
  provider:{synthetic:true,requestEmail(){},verifyTokenHash(){}},
  verifyIdentity:{synthetic:true,run(){}},
  issueSession:{synthetic:true,run(){}}};
 await reject(createSyntheticWorkerEmailConfirm({...defaults,origin:'https://jianshi-bua.pages.dev'}),
  'CMS_H7E_NONROUTABLE_ONLY');
 await reject(createSyntheticWorkerEmailConfirm({...defaults,profile:'production'}),
  'CMS_H7E_NONROUTABLE_ONLY');
 await reject(createSyntheticWorkerEmailConfirm({...defaults,secret:new Uint8Array(31)}),
  'CMS_H7E_TEST_KEY_INVALID');
 await reject(createSyntheticWorkerEmailConfirm({...defaults,provider:{...defaults.provider,synthetic:false}}),
  'CMS_H7E_SYNTHETIC_ADAPTER_REQUIRED');
});
test('edge route integrates WebCrypto AES-256-GCM and POST-only redemption',async()=>{
 const f=fixture(),v=await landing(f);
 assert.equal(v.get.headers.get('referrer-policy'),'no-referrer');
 assert.match(v.intentCookie,/^__Host-jianshi_mail_intent=v1\./);
 assert.equal(f.log.redeem.length,0);
 assert.equal(f.log.sessions.length,0);
 const html=await onRequest({request:req('/auth/confirm',{headers:{cookie:v.cookies}}),
  env:env(v.controller)});
 assert.equal(html.status,200);assert.match(await html.text(),/手动确认测试/);
 assert.equal(f.log.redeem.length,0);
 const ok=await onRequest({request:post(v.cookies),env:env(v.controller)});
 assert.equal(ok.status,303);assert.equal(ok.headers.get('location'),'/cms/');
 assert.equal(ok.headers.getSetCookie().length,3);
 assert.equal(f.log.redeem.length,1);assert.equal(f.log.sessions.length,1);
 const output=JSON.stringify({status:ok.status,headers:[...ok.headers]});
 for(const secret of [HASH,TOKEN,REFRESH,EMAIL])assert.equal(output.includes(secret),false);
 const again=await onRequest({request:post(v.cookies),env:env(v.controller)});
 assert.equal(again.status,403);assert.equal(f.log.redeem.length,1);
 assert.equal((await onRequest({request:req('/cms/'),env:env(v.controller)})).status,404);
});
test('independent Node crypto validates Worker HKDF, HMAC digest and AES-GCM intent',async()=>{
 const f=fixture(),v=await landing(f);
 assert.equal(f.log.issue.length,1);
 const stateHash=hex(createHmac('sha256',f.secret).update('state\0'+v.state).digest());
 assert.equal(f.log.issue[0].stateDigest,stateHash);
 const cookieValue=v.stateCookie.split('=')[1];
 const cookieHash=hex(createHmac('sha256',f.secret).update('cookie\0'+cookieValue).digest());
 assert.equal(f.log.issue[0].cookieDigest,cookieHash);
 const parts=v.intentCookie.split('=')[1].split('.');
 assert.equal(parts.length,4);
 const key=Buffer.from(hkdfSync('sha256',f.secret,Buffer.alloc(0),
  'JIANSHI_G2H7B_EMAIL_INTENT_V1',32));
 const decipher=createDecipheriv('aes-256-gcm',key,Buffer.from(parts[1],'base64url'));
 decipher.setAAD(Buffer.from(cookieHash,'utf8'));
 decipher.setAuthTag(Buffer.from(parts[3],'base64url'));
 const clear=Buffer.concat([decipher.update(Buffer.from(parts[2],'base64url')),
  decipher.final()]);
 const obj=JSON.parse(clear.toString('utf8'));
 assert.equal(obj.state,v.state);assert.equal(obj.tokenHash,HASH);
 assert.equal(obj.expiresAt,1791800000000+300000);
});
test('wrong browser, forged AES-GCM tag and duplicate cookie fail without state burn',async()=>{
 const f=fixture(),v=await landing(f);
 const wrong='__Host-jianshi_mail_state='+randomBytes(32).toString('base64url');
 await reject(v.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:wrong+'; '+v.intentCookie,requestOrigin:ORIGIN,
  fetchSite:'same-origin'}),'CMS_H7E_INTENT_INVALID');
 const forged=v.intentCookie.slice(0,-1)+(v.intentCookie.endsWith('A')?'B':'A');
 await reject(v.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:v.stateCookie+'; '+forged,requestOrigin:ORIGIN,
  fetchSite:'same-origin'}),'CMS_H7E_INTENT_INVALID');
 await reject(v.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:v.cookies+'; '+v.intentCookie,requestOrigin:ORIGIN,
  fetchSite:'same-origin'}),'CMS_H7E_COOKIE_INVALID');
 assert.equal([...f.records.values()][0].used,false);
 assert.equal(f.log.redeem.length,0);
 const ok=await v.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:v.cookies,requestOrigin:ORIGIN,fetchSite:'same-origin'});
 assert.equal(ok.status,303);
});
test('browserless mail scanner cannot redeem and duplicate token parameters fail closed',async()=>{
 const f=fixture(),v=await mailStart(f);
 await reject(v.controller.receiveLink({url:v.path,requestOrigin:ORIGIN,cookieHeader:''}),
  'CMS_H7E_COOKIE_INVALID');
 await reject(v.controller.receiveLink({url:v.path+'&type=email',requestOrigin:ORIGIN,
  cookieHeader:v.stateCookie}),'CMS_H7E_LINK_INVALID');
 assert.equal([...f.records.values()][0].used,false);
 assert.equal(f.log.redeem.length,0);
});
test('different Worker controllers, shared atomic state: exactly one of sixteen POSTS succeeds',async()=>{
 const f=fixture(),v=await landing(f);
 const second=await f.make();
 const results=await Promise.allSettled(Array.from({length:16},(_,i)=>
  (i%2?v.controller:second).confirm({method:'POST',url:'/auth/confirm',
   cookieHeader:v.cookies,requestOrigin:ORIGIN,fetchSite:'same-origin'})));
 assert.equal(results.filter(x=>x.status==='fulfilled').length,1);
 assert.equal(results.filter(x=>x.status==='rejected'&&
  x.reason.code==='CMS_H7E_REPLAY_OR_EXPIRED').length,15);
 assert.equal(f.log.redeem.length,1);
 assert.equal(f.log.sessions.length,1);
});
test('expired intent and invalid role fail closed; failure consumes one-time state',async()=>{
 const f=fixture(),v=await landing(f);
 f.advance(301000);
 await reject(v.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:v.cookies,requestOrigin:ORIGIN,fetchSite:'same-origin'}),
 'CMS_H7E_INTENT_INVALID');
 assert.equal(f.log.redeem.length,0);
 const f2=fixture({fail:'actor'}),w=await landing(f2);
 await reject(w.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:w.cookies,requestOrigin:ORIGIN,fetchSite:'same-origin'}),'CMS_H7E_AUTH_DENIED');
 assert.equal([...f2.records.values()][0].used,true);
 assert.equal(f2.log.sessions.length,0);
 await reject(w.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:w.cookies,requestOrigin:ORIGIN,fetchSite:'same-origin'}),
  'CMS_H7E_REPLAY_OR_EXPIRED');
});
test('controller rejects simulated real tokens and does not leak upstream faults',async()=>{
 const f=fixture({fail:'verify'}),v=await landing(f);
 await reject(v.controller.confirm({method:'POST',url:'/auth/confirm',
  cookieHeader:v.cookies,requestOrigin:ORIGIN,fetchSite:'same-origin'}),
 'CMS_H7E_AUTH_DENIED');
 assert.equal(f.log.redeem.length,1);
 assert.equal(f.log.sessions.length,0);
});
