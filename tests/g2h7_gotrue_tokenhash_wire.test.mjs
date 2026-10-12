import test from 'node:test';
import assert from 'node:assert/strict';
import {createStagingTokenHashWire,STAGING_GOTRUE_ORIGIN} from '../scripts/qa/g2h7_gotrue_tokenhash_wire.mjs';

const KEY='SYNTHETIC_TEST_ONLY_abcdef123456';
const EMAIL='SYNTHETIC_EDITOR@example.invalid';
const STATE='A'.repeat(43);
const REDIRECT='https://localhost/auth/confirm?state='+STATE;
const HASH='b'.repeat(64);
const SESSION={access_token:'SYNTHETIC_ACCESS_TOKEN_'.padEnd(64,'A'),
 refresh_token:'SYNTHETIC_REFRESH_TOKEN_'.padEnd(64,'B'),
 token_type:'bearer',expires_in:3600};
function response(data={},status=200,type='application/json'){
 return {ok:status===200,status,headers:{get(name){return name==='content-type'?type:null;}},
  async json(){return data;}};
}
function setup(fn=async()=>response({})){
 return createStagingTokenHashWire({url:STAGING_GOTRUE_ORIGIN,
  publishableKey:KEY,fetchImpl:fn});
}
test('G2-H.7 disabled unless synthetic gate is armed; no real keys or HTTP',()=>{
 delete process.env.JIANSHI_G2H7_SYNTHETIC_ONLY;
 assert.throws(()=>setup(),/CMS_H7_DISABLED/);
 process.env.JIANSHI_G2H7_SYNTHETIC_ONLY='1';
 assert.throws(()=>createStagingTokenHashWire({url:'https://other.example',
  publishableKey:KEY,fetchImpl:async()=>response()}),/CMS_H7_STAGING_ONLY/);
 assert.throws(()=>createStagingTokenHashWire({url:STAGING_GOTRUE_ORIGIN,
  publishableKey:'sb_secret_should_not_be_used',fetchImpl:async()=>response()}),
  /CMS_H7_FAKE_KEY_REQUIRED/);
 assert.throws(()=>createStagingTokenHashWire({url:STAGING_GOTRUE_ORIGIN,
  publishableKey:KEY,fetchImpl:globalThis.fetch}),/CMS_H7_FAKE_HTTP_REQUIRED/);
});
test('G2-H.7 /otp uses create_user:false, loopback state redirect, no bogus PKCE',async()=>{
 process.env.JIANSHI_G2H7_SYNTHETIC_ONLY='1';
 let calls=0;
 const provider=setup(async(url,options)=>{
  calls++;
  const u=new URL(url);
  assert.equal(u.origin,STAGING_GOTRUE_ORIGIN);
  assert.equal(u.pathname,'/auth/v1/otp');
  assert.equal(u.searchParams.get('redirect_to'),REDIRECT);
  assert.equal(options.method,'POST');
  assert.equal(options.redirect,'error');
  assert.equal(options.cache,'no-store');
  assert.equal(options.headers.apikey,KEY);
  assert.deepEqual(JSON.parse(options.body),{email:EMAIL,create_user:false});
  return response({});
 });
 const answer=await provider.requestEmail({email:EMAIL,redirectTo:REDIRECT});
 assert.deepEqual(answer,{accepted:true,deliveryVerified:false});
 assert.equal(calls,1);
 for(const url of ['https://evil.example/auth/confirm?state='+STATE,
    'https://localhost/auth/confirm?state='+STATE+'&next=https://evil.example',
    'https://localhost/auth/confirm?state='+STATE+'#bad',
    'https://localhost/auth/confirm?state=A',
    'http://localhost/auth/confirm?state='+STATE]){
  await assert.rejects(provider.requestEmail({email:EMAIL,redirectTo:url}),
   /CMS_H7_REDIRECT_DENIED/);
 }
 await assert.rejects(provider.requestEmail({email:'real@example.com',
   redirectTo:REDIRECT}),/CMS_H7_SYNTHETIC_EMAIL_ONLY/);
 assert.equal(calls,1);
});
test('G2-H.7 token_hash verification uses separate /verify email flow',async()=>{
 process.env.JIANSHI_G2H7_SYNTHETIC_ONLY='1';
 let calls=0;
 const provider=setup(async(url,options)=>{
  calls++;
  assert.equal(url,STAGING_GOTRUE_ORIGIN+'/auth/v1/verify');
  assert.deepEqual(JSON.parse(options.body),{token_hash:HASH,type:'email'});
  assert.equal(options.method,'POST');
  assert.equal(options.redirect,'error');
  return response(SESSION);
 });
 const result=await provider.verifyTokenHash({tokenHash:HASH});
 assert.deepEqual(result,SESSION);
 assert.equal(Object.isFrozen(result),true);
 await assert.rejects(provider.verifyTokenHash({tokenHash:'SYNTHETIC_LINK'}),
  /CMS_H7_TOKEN_HASH_INVALID/);
 assert.equal(calls,1);
});
test('G2-H.7 fail closed for upstream denial, timeout, HTML and missing JWT',async()=>{
 process.env.JIANSHI_G2H7_SYNTHETIC_ONLY='1';
 for(const [impl,code] of [
  [async()=>{throw new Error('secret upstream response');},'CMS_H7_UPSTREAM_FAILED'],
  [async()=>response({},429),'CMS_H7_UPSTREAM_DENIED'],
  [async()=>response({},200,'text/html'),'CMS_H7_UPSTREAM_CONTENT_TYPE'],
  [async()=>response({access_token:'anything'}),'CMS_H7_SESSION_INVALID'],
  [async()=>({ok:true,status:200,headers:{get:()=> 'application/json'},
   json:async()=>{throw new Error('private error');}}),'CMS_H7_RESPONSE_INVALID']
 ]){
  const provider=setup(impl);
  await assert.rejects(provider.verifyTokenHash({tokenHash:HASH}),err=>{
   assert.equal(err.code,code);
   assert.ok(!err.message.includes('secret upstream'));
   return true;
  });
 }
});
