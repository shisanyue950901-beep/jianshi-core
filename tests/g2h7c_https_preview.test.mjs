import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import https from 'node:https';
import {randomBytes} from 'node:crypto';
import {mkdtempSync,readFileSync,rmSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import {createEmailTokenHashConfirm} from '../scripts/qa/g2h7b_tokenhash_confirmation.mjs';
import {createLoopbackEmailHttpsPreview} from '../scripts/qa/g2h7c_loopback_https_preview.mjs';

process.env.JIANSHI_G2H7B_SYNTHETIC_ONLY='1';
process.env.JIANSHI_G2H7C_SYNTHETIC_ONLY='1';
const DIR=mkdtempSync(path.join(os.tmpdir(),'jianshi-h7c-'));
execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes',
 '-keyout',path.join(DIR,'key.pem'),'-out',path.join(DIR,'cert.pem'),
 '-days','1','-subj','/CN=localhost','-addext','subjectAltName=DNS:localhost'],
 {stdio:'ignore',timeout:14000});
const tls={key:readFileSync(path.join(DIR,'key.pem')),
 cert:readFileSync(path.join(DIR,'cert.pem'))};
after(()=>rmSync(DIR,{recursive:true,force:true}));
const EMAIL='SYNTHETIC_EDITOR@example.invalid';
const HASH='a'.repeat(64);
const USER='00000000-0000-4000-8000-00000000a001';
const SESSION='00000000-0000-4000-8000-00000000a002';
const JWT='SYNTHETIC_TEST_ACCESS_TOKEN_SECRET_SHOULD_NOT_LEAK';
const REFRESH='SYNTHETIC_TEST_REFRESH_TOKEN_SECRET_SHOULD_NOT_LEAK';
function fixture(){
 let sent=[],exchanges=[],issued=[],now=1791800000000;
 const challenges=new Map(),secret=randomBytes(32);
 const pendingStore={
  async issue(v){challenges.set(v.stateDigest,{...v,consumed:false});return true;},
  async consume(v){
   const row=challenges.get(v.stateDigest);
   if(!row||row.consumed||row.cookieDigest!==v.cookieDigest||
    Date.parse(v.at)>=Date.parse(row.expiresAt))return {used:false};
   row.consumed=true;return {used:true};
  }
 };
 const provider={
  synthetic:true,
  async requestEmail(arg){sent.push(arg);return {accepted:true,deliveryVerified:false};},
  async verifyTokenHash({tokenHash}){
   assert.equal(tokenHash,HASH);
   exchanges.push(tokenHash);
   return {access_token:JWT,refresh_token:REFRESH};
  }
 };
 const makeController=origin=>createEmailTokenHashConfirm({
  origin,secret,pendingStore,provider,now:()=>now,
  verifyIdentity:async access=>{
   assert.equal(access,JWT);
   return {userId:USER,sessionId:SESSION,role:'EDITOR'};
  },
  issueDurableSession:async values=>{
   assert.equal(values.jwt,JWT);issued.push(values);
   return {token:randomBytes(32).toString('base64url'),
    csrf:randomBytes(32).toString('base64url')};
  }
 });
 return {
  makeController,sent,exchanges,issued,challenges,
  advance:delta=>{now+=delta;}
 };
}
function request(origin,path,{method='GET',cookie='',headers={},body=''}={}){
 const url=new URL(origin+path);
 return new Promise((resolve,reject)=>{
  const req=https.request({
   hostname:'127.0.0.1',port:Number(url.port),servername:'localhost',
   method,path:url.pathname+url.search,host:'localhost',
   rejectUnauthorized:false,
   headers:{host:'localhost:'+url.port,...(cookie?{cookie}:{}),...headers},
   timeout:3500
  },res=>{
   const chunks=[];res.on('data',b=>chunks.push(b));
   res.on('end',()=>resolve({
    status:res.statusCode,headers:res.headers,
    body:Buffer.concat(chunks).toString('utf8')
   }));
  });
  req.on('error',reject);
  req.on('timeout',()=>req.destroy(Error('Synthetic HTTPS test timeout')));
  req.end(body);
 });
}
function firstSetCookie(headers,name){
 const v=headers['set-cookie']||[];
 const hit=v.find(x=>x.startsWith(name+'='));
 assert.ok(hit,'expected cookie '+name);
 return hit.split(';')[0];
}
function withoutSecrets(result){
 const rendered=JSON.stringify(result);
 for(const forbidden of [HASH,JWT,REFRESH,EMAIL]){
  assert.equal(rendered.includes(forbidden),false,'secret reflected in HTTPS response');
 }
}
async function makeServer(){
 const f=fixture(),app=createLoopbackEmailHttpsPreview({
  tls,makeController:f.makeController
 });
 const {origin,controller}=await app.listen();
 return {f,app,origin,controller,
  async close(){await new Promise((resolve,reject)=>app.server.close(err=>err?reject(err):resolve()));}
 };
}
async function openEmail(s){
 const begin=await s.controller.start({email:EMAIL});
 const origin=new URL(s.f.sent.at(-1).redirectTo).origin;
 assert.equal(origin,s.origin);
 const state=new URL(s.f.sent.at(-1).redirectTo).searchParams.get('state');
 const url='/auth/confirm?state='+state+'&type=email&token_hash='+HASH;
 const stateCookie=begin.setCookie.split(';')[0];
 return {begin,url,stateCookie};
}
function submission(origin,cookie,extra={}){
 return {method:'POST',cookie,headers:{
  'origin':origin,'sec-fetch-site':'same-origin',
  'content-type':'application/x-www-form-urlencoded',
  'content-length':'0',...(extra.headers||{})
 },body:extra.body||''};
}

test('requires explicit isolation gate and rejects actual database credentials',()=>{
 delete process.env.JIANSHI_G2H7C_SYNTHETIC_ONLY;
 assert.throws(()=>createLoopbackEmailHttpsPreview({tls,makeController:()=>({})}),
  /CMS_H7C_LIVE_DISABLED/);
 process.env.JIANSHI_G2H7C_SYNTHETIC_ONLY='1';
 assert.throws(()=>createLoopbackEmailHttpsPreview({makeController:()=>({})}),
  /CMS_H7C_TEST_TLS_AND_FACTORY_REQUIRED/);
 process.env.SUPABASE_SERVICE_ROLE_KEY='SYNTHETIC_MUST_BE_REJECTED';
 assert.throws(()=>createLoopbackEmailHttpsPreview({tls,makeController:()=>({})}),
  /CMS_H7C_EXTERNAL_CREDENTIALS_DENIED/);
 delete process.env.SUPABASE_SERVICE_ROLE_KEY;
});
test('real TLS GET strips token query, manual HTML form, POST issues opaque cookie',async()=>{
 const s=await makeServer();
 try{
  const l=await openEmail(s);
  const landing=await request(s.origin,l.url,{cookie:l.stateCookie});
  assert.equal(landing.status,303);
  assert.equal(landing.headers.location,'/auth/confirm');
  assert.match(landing.headers['set-cookie'][0],/Secure; HttpOnly; SameSite=Strict/);
  assert.equal(landing.headers['referrer-policy'],'no-referrer');
  assert.match(landing.headers['content-security-policy'],/form-action 'self'/);
  assert.equal(landing.headers['cache-control'],'no-store, max-age=0');
  const intent=firstSetCookie(landing.headers,'__Host-jianshi_mail_intent');
  assert.equal(s.f.exchanges.length,0);
  assert.equal([...s.f.challenges.values()][0].consumed,false);
  const both=l.stateCookie+'; '+intent;
  const confirmPage=await request(s.origin,'/auth/confirm',{cookie:both});
  assert.equal(confirmPage.status,200);
  assert.match(confirmPage.headers['content-type'],/^text\/html/);
  assert.match(confirmPage.body,/<form method="post" action="\/auth\/confirm">/);
  assert.match(confirmPage.body,/确认测试登录/);
  assert.doesNotMatch(confirmPage.body,/<script\b/i);
  withoutSecrets(confirmPage);
  const confirmed=await request(s.origin,'/auth/confirm',submission(s.origin,both));
  assert.equal(confirmed.status,303);
  assert.equal(confirmed.headers.location,'/cms/');
  assert.match(confirmed.headers['set-cookie'].join(';'),/__Host-jianshi_cms=.*Secure; HttpOnly; SameSite=Strict/);
  assert.equal(s.f.exchanges.length,1);
  assert.equal(s.f.issued.length,1);
  withoutSecrets(landing);withoutSecrets(confirmed);
  // No CMS is hosted at this isolated TLS fixture; a redirect isn't a UI launch.
  const cms=await request(s.origin,'/cms/');
  assert.equal(cms.status,404);
 }finally{await s.close();}
});
test('scanner GET without original cookie cannot verify or consume the state',async()=>{
 const s=await makeServer();
 try{
  const l=await openEmail(s);
  const scanner=await request(s.origin,l.url);
  assert.equal(scanner.status,403);
  const page=await request(s.origin,'/auth/confirm');
  assert.equal(page.status,403);
  assert.equal(s.f.exchanges.length,0);
  assert.equal([...s.f.challenges.values()][0].consumed,false);
  const ok=await request(s.origin,l.url,{cookie:l.stateCookie});
  assert.equal(ok.status,303);
 }finally{await s.close();}
});
test('network-level host header and forwarded spoofing fail closed',async()=>{
 const s=await makeServer();
 try{
  const l=await openEmail(s);
  for(const headers of [
   {host:'evil.example'},
   {'x-forwarded-host':'localhost'},
   {'x-forwarded-proto':'http'}
  ]){
   const res=await request(s.origin,l.url,{cookie:l.stateCookie,headers});
   assert.equal(res.status,403);
  }
  assert.equal(s.f.exchanges.length,0);
  assert.equal([...s.f.challenges.values()][0].consumed,false);
 }finally{await s.close();}
});
test('GET never redeems; POST CSRF, content and route protections hold',async()=>{
 const s=await makeServer();
 try{
  const l=await openEmail(s);
  const staged=await request(s.origin,l.url,{cookie:l.stateCookie});
  const cookie=l.stateCookie+'; '+firstSetCookie(staged.headers,'__Host-jianshi_mail_intent');
  for(const req of [
   submission(s.origin,cookie,{headers:{origin:'https://evil.example'}}),
   submission(s.origin,cookie,{headers:{'sec-fetch-site':'cross-site'}}),
   submission(s.origin,cookie,{headers:{'content-type':'text/plain'}}),
   submission(s.origin,cookie,{headers:{'content-length':'1'},body:'x'})
  ]){
   const res=await request(s.origin,'/auth/confirm',req);
   assert.ok([403,413,415].includes(res.status));
  }
  assert.equal((await request(s.origin,'/auth/confirm?extra=1',submission(s.origin,cookie))).status,405);
  assert.equal((await request(s.origin,'/api/internal',submission(s.origin,cookie))).status,404);
  assert.equal((await request(s.origin,'/auth/start')).status,404);
  assert.equal(s.f.exchanges.length,0);
  assert.equal([...s.f.challenges.values()][0].consumed,false);
  const ok=await request(s.origin,'/auth/confirm',submission(s.origin,cookie));
  assert.equal(ok.status,303);
 }finally{await s.close();}
});
test('8 real HTTPS POST requests, two TLS clients, only one exchanges email',async()=>{
 const s=await makeServer();
 try{
  const l=await openEmail(s);
  const staged=await request(s.origin,l.url,{cookie:l.stateCookie});
  const cookie=l.stateCookie+'; '+firstSetCookie(staged.headers,'__Host-jianshi_mail_intent');
  const r=await Promise.all(Array.from({length:8},()=>
   request(s.origin,'/auth/confirm',submission(s.origin,cookie))));
  assert.equal(r.filter(x=>x.status===303).length,1);
  assert.equal(r.filter(x=>x.status===403).length,7);
  assert.equal(s.f.exchanges.length,1);
  assert.equal(s.f.issued.length,1);
  const replay=await request(s.origin,'/auth/confirm',submission(s.origin,cookie));
  assert.equal(replay.status,403);
  r.forEach(withoutSecrets);
 }finally{await s.close();}
});
test('expired challenge and invalid input yield only generic responses',async()=>{
 const s=await makeServer();
 try{
  const l=await openEmail(s);
  const malformed=await request(s.origin,l.url+'&token_hash='+HASH,{cookie:l.stateCookie});
  assert.equal(malformed.status,403);
  withoutSecrets(malformed);
  const staged=await request(s.origin,l.url,{cookie:l.stateCookie});
  const cookie=l.stateCookie+'; '+firstSetCookie(staged.headers,'__Host-jianshi_mail_intent');
  s.f.advance(301000);
  const expired=await request(s.origin,'/auth/confirm',submission(s.origin,cookie));
  assert.equal(expired.status,403);
  assert.equal(s.f.exchanges.length,0);
  assert.equal([...s.f.challenges.values()][0].consumed,false);
  withoutSecrets(expired);
 }finally{await s.close();}
});
