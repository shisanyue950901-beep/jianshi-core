import test from 'node:test';
import assert from 'node:assert/strict';
import {onRequest,PREVIEW_CONTRACT_ORIGIN as ORIGIN}
 from '../ops/cms-preview/functions/auth/confirm.js';

const STATE='s'.repeat(43),HASH='a'.repeat(64),JWT='SYNTHETIC_DO_NOT_RETURN_JWT';
const CS='__Host-jianshi_mail_state='+STATE;
const IC='__Host-jianshi_mail_intent=v1.'+
 'c'.repeat(16)+'.'+'d'.repeat(16)+'.'+'e'.repeat(22);
const COOKIE=CS+'; '+IC;
const path='/auth/confirm?state='+STATE+'&token_hash='+HASH+'&type=email';
function make(){
 const metrics={stage:0,confirm:0,exchange:0};
 let used=false;
 const fake=Object.freeze({
  synthetic:true,
  async receiveLink({url,cookieHeader,requestOrigin}){
   metrics.stage++;
   assert.equal(url,path);assert.equal(requestOrigin,ORIGIN);
   assert.equal(cookieHeader,CS);
   return {status:303,location:'/auth/confirm',setCookies:[
    IC+'; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=300'
   ]};
  },
  async confirm({method,url,cookieHeader,requestOrigin,fetchSite}){
   assert.equal(method,'POST');assert.equal(url,'/auth/confirm');
   assert.equal(cookieHeader,COOKIE);assert.equal(requestOrigin,ORIGIN);
   assert.equal(fetchSite,'same-origin');
   if(used)throw Error('SYNTHETIC_REPLAY_REJECTED');
   used=true;metrics.confirm++;metrics.exchange++;
   return {status:303,location:'/cms/',setCookies:[
    '__Host-jianshi_mail_state=; Secure; HttpOnly; SameSite=Lax; Path=/; Max-Age=0',
    '__Host-jianshi_mail_intent=; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=0',
    '__Host-jianshi_cms='+'j'.repeat(43)+
     '; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=900'
   ]};
  }
 });
 return {metrics,fake,env:{
  JIANSHI_H7D_PROFILE:'SYNTHETIC_CONTRACT_ONLY',
  JIANSHI_H7D_CONTRACT_GATE:'1',
  JIANSHI_H7D_TEST_CONTROLLER:fake
 }};
}
function request(path,{method='GET',headers={},body,origin=ORIGIN}={}){
 return new Request(origin+path,{method,headers:{
  'host':new URL(origin).host,...headers
 },...(body!==undefined?{body}:{})});
}
async function invoke(f,req,override={}){
 return onRequest({request:req,env:{...f.env,...override}});
}
function safe(result){
 const text=JSON.stringify({status:result.status,headers:[...result.headers],body:result.bodyText});
 for(const v of [HASH,JWT])assert.equal(text.includes(v),false);
}
test('runtime bindings default-deny and real Pages hosts fail with no provider invocation',async()=>{
 const f=make();
 for(const change of [
  {JIANSHI_H7D_PROFILE:'PRODUCTION'},
  {JIANSHI_H7D_PROFILE:undefined},
  {JIANSHI_H7D_CONTRACT_GATE:undefined},
  {JIANSHI_H7D_TEST_CONTROLLER:undefined},
  {JIANSHI_H7D_TEST_CONTROLLER:{synthetic:false}},
  {JIANSHI_H7D_TEST_CONTROLLER:{synthetic:true}}
 ]){
  const r=await invoke(f,request(path,{headers:{cookie:CS}}),change);
  assert.equal(r.status,404);
 }
 for(const origin of [
  'https://jianshi-bua.pages.dev',
  'https://g2h7d-preview.jianshi-bua.pages.dev',
  'http://h7d-preview.example.invalid',
  'https://evil.example.invalid'
 ]){
  const r=await invoke(f,request(path,{origin,headers:{cookie:CS}}));
  assert.equal(r.status,404);
 }
 assert.equal(f.metrics.stage,0);assert.equal(f.metrics.exchange,0);
});
test('edge Request/Response GET strips token hash and serves scriptless manual form',async()=>{
 const f=make();
 const landing=await invoke(f,request(path,{headers:{cookie:CS}}));
 assert.equal(landing.status,303);
 assert.equal(landing.headers.get('location'),'/auth/confirm');
 assert.equal(landing.headers.get('referrer-policy'),'no-referrer');
 assert.equal(landing.headers.get('x-robots-tag'),'noindex, nofollow, noarchive');
 assert.match(landing.headers.get('cache-control'),/no-store/);
 assert.equal(f.metrics.stage,1);assert.equal(f.metrics.exchange,0);
 const preview=await invoke(f,request('/auth/confirm',{headers:{cookie:COOKIE}}));
 assert.equal(preview.status,200);
 const html=await preview.text();
 assert.match(html,/<form method="post" action="\/auth\/confirm">/);
 assert.doesNotMatch(html,/<script\b/i);
 assert.doesNotMatch(html,/token_hash/);
 assert.equal(f.metrics.exchange,0);
 safe({headers:landing.headers,status:landing.status,bodyText:''});
});
test('explicit same-origin POST gets only 303, second attempt fail closed',async()=>{
 const f=make();
 const hdr={cookie:COOKIE,origin:ORIGIN,'sec-fetch-site':'same-origin',
  'content-type':'application/x-www-form-urlencoded'};
 const first=await invoke(f,request('/auth/confirm',{method:'POST',headers:hdr,body:''}));
 assert.equal(first.status,303);
 assert.equal(first.headers.get('location'),'/cms/');
 assert.equal(first.headers.getSetCookie().length,3);
 assert.equal(f.metrics.confirm,1);assert.equal(f.metrics.exchange,1);
 const replay=await invoke(f,request('/auth/confirm',{method:'POST',headers:hdr,body:''}));
 assert.equal(replay.status,403);assert.equal(f.metrics.exchange,1);
 assert.equal((await invoke(f,request('/cms/'))).status,404);
 safe({headers:first.headers,status:first.status,bodyText:''});
});
test('CSRF, forwarded spoofing and unsupported methods fail without touching adapter',async()=>{
 const f=make();
 const hdr={cookie:COOKIE,origin:ORIGIN,'sec-fetch-site':'same-origin',
  'content-type':'application/x-www-form-urlencoded'};
 for(const opts of [
  {headers:{...hdr,origin:'https://evil.example.invalid'},method:'POST',body:''},
  {headers:{...hdr,'sec-fetch-site':'cross-site'},method:'POST',body:''},
  {headers:{...hdr,'content-type':'text/plain'},method:'POST',body:''},
  {headers:{...hdr},method:'POST',body:'x'},
  {headers:{...hdr,'content-length':'1000000'},method:'POST',body:''},
  {headers:{cookie:CS,'x-forwarded-host':'evil.invalid'}},
  {headers:{cookie:CS,host:'evil.invalid'}},
  {headers:{cookie:CS,'x-forwarded-proto':'http'}}
 ]){
  const r=await invoke(f,request('/auth/confirm',opts));
  assert.ok([403,404].includes(r.status),'expected deny '+r.status);
 }
 assert.equal((await invoke(f,request('/auth/confirm',{method:'DELETE'}))).status,405);
 assert.equal((await invoke(f,request('/auth/start'))).status,404);
 assert.equal((await invoke(f,request('/auth/confirm',{headers:{cookie:CS}}))).status,403);
 assert.equal(f.metrics.exchange,0);assert.equal(f.metrics.stage,0);
});
test('no query reflection or handler exception leakage in deny path',async()=>{
 const f=make();
 f.env.JIANSHI_H7D_TEST_CONTROLLER={
  synthetic:true,
  async receiveLink(){throw Error('SYNTHETIC_SECRET_IN_ERROR '+HASH);},
  async confirm(){throw Error('SHOULD_NOT_CALL');}
 };
 const r=await invoke(f,request(path,{headers:{cookie:CS}}));
 assert.equal(r.status,403);
 const body=await r.text();
 assert.equal(body.includes(HASH),false);
 assert.equal(body.includes('SYNTHETIC_SECRET_IN_ERROR'),false);
 assert.equal([...r.headers].some(([k,v])=>v.includes(HASH)),false);
});
test('malicious controller redirects and cookies rejected even if synthetic flag set',async()=>{
 const f=make();
 f.env.JIANSHI_H7D_TEST_CONTROLLER={
  synthetic:true,
  async receiveLink(){
   return {status:303,location:'https://evil.invalid',setCookies:[
    '__Host-jianshi_mail_intent=x; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=300'
   ]};
  },
  async confirm(){return {status:303,location:'/cms/',setCookies:[]};}
 };
 assert.equal((await invoke(f,request(path,{headers:{cookie:CS}}))).status,403);
 const r=await invoke(f,request('/auth/confirm',{method:'POST',headers:{
  cookie:COOKIE,origin:ORIGIN,'sec-fetch-site':'same-origin',
  'content-type':'application/x-www-form-urlencoded'
 },body:''}));
 assert.equal(r.status,403);
});
