import test from 'node:test';
import assert from 'node:assert/strict';
import {createSyntheticWorkerMtlsStateClient,SYNTHETIC_MTLS_ENDPOINT}
 from '../ops/cms-preview/worker-mtls-state-contract.mjs';

const DIGEST='a'.repeat(64);
const PROFILE='SYNTHETIC_G2H7G_MTLS_ONLY';
function make(binding){
 return createSyntheticWorkerMtlsStateClient({
  origin:SYNTHETIC_MTLS_ENDPOINT,profile:PROFILE,binding
 });
}
function fake(fetch){
 return {synthetic:true,fetch};
}
test('no mTLS binding, real origin, wrong profile, untrusted binding denied',()=>{
 for(const options of [
  {origin:'https://jianshi-bua.pages.dev'},
  {origin:'https://apuibjhxinumxbfnqlkp.supabase.co'},
  {origin:'https://h7g-state.example.invalid/v1/email-state?forward=1'},
  {profile:'production'},
  {binding:undefined},
  {binding:{fetch:async()=>new Response('{"used":true}')}},
  {binding:{synthetic:false,fetch:async()=>new Response('{"used":true}')}},
  {binding:fake(null)}
 ]){
  assert.throws(()=>createSyntheticWorkerMtlsStateClient({
   origin:SYNTHETIC_MTLS_ENDPOINT,profile:PROFILE,
   binding:fake(async()=>new Response('{"used":true}')),...options
  }));
 }
});
test('synthetic binding, whitelist HMAC digests and never forward user credentials',async()=>{
 let seen;
 const client=make(fake(async(url,init)=>{
  seen={url,init};
  return new Response('{"issued":true}',{
   status:200,headers:{'content-type':'application/json'}
  });
 }));
 assert.equal(await client.issue({stateDigest:DIGEST,cookieDigest:DIGEST,
  expiresAt:'2026-10-13T00:00:00.000Z',
  jwt:'SYNTHETIC_SHOULD_NOT_APPEAR',token_hash:'a'.repeat(64),
  email:'SYNTHETIC_SECRET@example.invalid'}),true);
 assert.equal(seen.url,SYNTHETIC_MTLS_ENDPOINT);
 assert.equal(seen.init.method,'POST');
 assert.equal(seen.init.redirect,'error');
 assert.equal(seen.init.cache,'no-store');
 assert.deepEqual(Object.keys(JSON.parse(seen.init.body)).sort(),
  ['action','stateDigest','cookieDigest','expiresAt'].sort());
 assert.ok(!/authorization|cookie|jwt|token_hash|@example.invalid/i.test(
  JSON.stringify(seen.init.headers)));
 assert.equal(seen.init.body.includes('SYNTHETIC_SHOULD_NOT_APPEAR'),false);
});
test('consume returns only strict used boolean and trusts DB clock, not caller time',async()=>{
 let body;
 const client=make(fake(async(_url,init)=>{
  body=JSON.parse(init.body);
  return new Response('{"used":false}',{status:200,
   headers:{'content-type':'application/json'}});
 }));
 assert.deepEqual(await client.consume({stateDigest:DIGEST,cookieDigest:DIGEST,
  at:'2099-01-01T00:00:00Z'}),{used:false});
 assert.deepEqual(Object.keys(body).sort(),[
  'action','cookieDigest','stateDigest'].sort());
});
test('untrusted HTML, redirect, wrong status, extra fields and network errors fail closed',async()=>{
 for(const [reply,want] of [
  [new Response('<html>oops</html>',{status:200,
   headers:{'content-type':'text/html'}}),'CMS_H7G_JSON_ONLY'],
  [new Response('{"used":true,"key":"fake"}',{status:200,
   headers:{'content-type':'application/json'}}),'CMS_H7G_BODY_DENIED'],
  [new Response('{"used":"true"}',{status:200,
   headers:{'content-type':'application/json'}}),'CMS_H7G_CONSUME_DENIED'],
  [new Response('{"used":true}',{status:403,
   headers:{'content-type':'application/json'}}),'CMS_H7G_TRANSPORT_DENIED'],
  [new Response('not json',{status:200,
   headers:{'content-type':'application/json'}}),'CMS_H7G_BODY_DENIED']
 ]){
  await assert.rejects(make(fake(async()=>reply)).consume({
   stateDigest:DIGEST,cookieDigest:DIGEST
  }),e=>e.code===want);
 }
 await assert.rejects(make(fake(async()=>{throw Error('SYNTHETIC_CA_SECRET')}))
  .consume({stateDigest:DIGEST,cookieDigest:DIGEST}),
  e=>e.code==='CMS_H7G_MTLS_FAILURE'&&
   !e.message.includes('SYNTHETIC_CA_SECRET'));
});
