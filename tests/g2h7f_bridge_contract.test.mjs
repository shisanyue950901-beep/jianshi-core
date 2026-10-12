import test from 'node:test';
import assert from 'node:assert/strict';
import {createDisposableEmailStateHttpClient}
 from '../ops/cms-preview/worker-pg-disposable-http.mjs';

const URL='http://127.0.0.1:54321/v1/email-state';
const KEY='SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET';
const OPT={url:URL,profile:'SYNTHETIC_H7F_DISPOSABLE_PG',key:KEY};
const STATE='a'.repeat(64),COOKIE='b'.repeat(64);
function mk(fetchImpl){return createDisposableEmailStateHttpClient({...OPT,fetchImpl});}
test('strict loopback key gate refuses all real origins, redirect parameters and credentials',()=>{
 for(const bad of [
  {url:'https://jianshi-bua.pages.dev/v1/email-state'},
  {url:'https://apuibjhxinumxbfnqlkp.supabase.co/rest/v1/rpc'},
  {url:'http://127.0.0.1:54321/v1/email-state?next=http://evil.invalid'},
  {url:'http://localhost:54321/v1/email-state'},
  {url:'http://127.0.0.1:54321@evil.invalid/v1/email-state'},
  {url:'http://127.0.0.1:65536/v1/email-state'},
  {key:'sb_secret_abc'},
  {key:'SYNTHETIC_WRONG_TEST_KEY_0123456'},
  {profile:'staging'},
  {fetchImpl:null}
 ]){
  assert.throws(()=>createDisposableEmailStateHttpClient({...OPT,...bad}));
 }
});
test('only whitelisted digests, no cookies/email/token hashes, strict synthetic HTTP',async()=>{
 const seen=[];
 const fetchImpl=async(url,opts)=>{
  seen.push({url,opts});
  const body=JSON.parse(opts.body);
  assert.deepEqual(Object.keys(body).sort(),[
   'action','cookieDigest','expiresAt','stateDigest'].sort());
  assert.match(opts.headers.authorization,/^Bearer SYNTHETIC_H7F_/);
  assert.equal(opts.redirect,'error');
  assert.equal(opts.cache,'no-store');
  assert.equal(body.action,'issue');
  assert.equal(body.stateDigest,STATE);assert.equal(body.cookieDigest,COOKIE);
  return new Response('{"issued":true}',{
   status:200,headers:{'content-type':'application/json'}
  });
 };
 const client=mk(fetchImpl);
 const result=await client.issue({stateDigest:STATE,cookieDigest:COOKIE,
  expiresAt:'2026-10-13T00:00:00.000Z',
  email:'SYNTHETIC_NOT_SENT@example.invalid',
  token_hash:'a'.repeat(64),jwt:'SYNTHETIC_NEVER_LEAK'
 });
 assert.equal(result,true);
 assert.equal(seen.length,1);
 for(const secret of ['SYNTHETIC_NOT_SENT@example.invalid','token_hash','jwt'])
  assert.equal(seen[0].opts.body.includes(secret),false);
});
test('consume trusts only single boolean used and never caller clock',async()=>{
 const fetchImpl=async(_,opts)=>{
  const b=JSON.parse(opts.body);
  assert.deepEqual(Object.keys(b).sort(),[
   'action','cookieDigest','stateDigest'].sort());
  assert.equal(b.action,'consume');
  assert.equal(opts.signal.aborted,false);
  return new Response('{"used":false}',{status:200,
   headers:{'content-type':'application/json'}});
 };
 assert.deepEqual(await mk(fetchImpl).consume({
  stateDigest:STATE,cookieDigest:COOKIE,at:'2099-01-01T00:00:00.000Z'
 }),{used:false});
});
test('rejects malformed responses, HTML, redirect, failure and network errors',async()=>{
 for(const [response,code] of [
  [new Response('<html>x</html>',{status:200,
   headers:{'content-type':'text/html'}}),'CMS_H7F_CONTENT_TYPE_DENIED'],
  [new Response('{"used":"yes"}',{status:200,
   headers:{'content-type':'application/json'}}),'CMS_H7F_RESPONSE_DENIED'],
  [new Response('{"used":true,"jwt":"LEAK"}',{status:200,
   headers:{'content-type':'application/json'}}),'CMS_H7F_RESPONSE_DENIED'],
  [new Response('{"used":true}',{status:403,
   headers:{'content-type':'application/json'}}),'CMS_H7F_HTTP_DENIED'],
  [new Response('invalid',{status:200,
   headers:{'content-type':'application/json'}}),'CMS_H7F_RESPONSE_DENIED']
 ]){
  const client=mk(async()=>response);
  await assert.rejects(client.consume({stateDigest:STATE,cookieDigest:COOKIE}),
   e=>e.code===code);
 }
 const client=mk(async()=>{throw Error('SYNTHETIC_SQL_SECRET');});
 await assert.rejects(client.consume({stateDigest:STATE,cookieDigest:COOKIE}),
  e=>e.code==='CMS_H7F_HTTP_UNAVAILABLE'&&!e.message.includes('SECRET'));
});
