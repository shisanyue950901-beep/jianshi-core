// G2-H.6 — actual TLS and one-time passwordless callback contract tests.
// Provider is deliberately synthetic: NO email, Supabase network, real JWT.
import test,{after} from 'node:test';
import assert from 'node:assert/strict';
import https from 'node:https';
import {randomBytes} from 'node:crypto';
import {mkdtempSync,readFileSync,rmSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import os from 'node:os';
import path from 'node:path';
import {createPkceLoginContract} from '../scripts/qa/g2h6_pkce_login_contract.mjs';
process.env.JIANSHI_G2H6_SYNTHETIC_ONLY='1';
const DIR=mkdtempSync(path.join(os.tmpdir(),'jianshi-g2h6-'));
execFileSync('openssl',['req','-x509','-newkey','rsa:2048','-nodes',
 '-keyout',path.join(DIR,'a.key'),'-out',path.join(DIR,'a.crt'),
 '-days','1','-subj','/CN=127.0.0.1',
 '-addext','subjectAltName=IP:127.0.0.1'],{stdio:'ignore',timeout:12000});
const tls={key:readFileSync(path.join(DIR,'a.key')),cert:readFileSync(path.join(DIR,'a.crt'))};
after(()=>rmSync(DIR,{recursive:true,force:true}));
const U='00000000-0000-4000-8000-00000000a001';
const S='00000000-0000-4000-8000-00000000a002';
const TOKEN='SYNTHETIC_JWT_NO_REAL_SIGNATURE_1234567890ABCDE';
const REFRESH='SYNTHETIC_REFRESH_STAYS_ON_SERVER_1234567890';
const CODE='SYNTHETIC_PKCE_CODE_123456789';
function make({failure='',verifyFailure=false,issueFailure=false}={}){
 const states=new Map(),sent=[],exchanges=[],issued=[];
 let now=1791800000000;
 const pendingStore={
  async issue({stateDigest,cookieDigest,encryptedVerifier,expiresAt}){
   assert.match(stateDigest,/^[a-f0-9]{64}$/);
   assert.match(cookieDigest,/^[a-f0-9]{64}$/);
   assert.match(encryptedVerifier,/^v1\./);
   assert.ok(!encryptedVerifier.includes('SYNTHETIC_JWT'));
   if(states.has(stateDigest))return false;
   states.set(stateDigest,{cookieDigest,encryptedVerifier,expiresAt,used:false});
   return true;
  },
  async consume({stateDigest,cookieDigest,at}){
   const record=states.get(stateDigest);
   if(!record||record.used||record.cookieDigest!==cookieDigest||
      Date.parse(at)>=Date.parse(record.expiresAt))return {used:false};
   record.used=true;return {used:true,encryptedVerifier:record.encryptedVerifier};
  }
 };
 const provider={
  async sendMagicLink(args){sent.push(args);return failure!=='send';},
  async exchangeCodeForSession(args){
   exchanges.push(args);
   if(failure==='exchange')throw Error('Provider unavailable');
   if(args.code!==CODE)throw Error('Invalid code');
   return {access_token:TOKEN,refresh_token:REFRESH};
  }
 };
 const ctl=createPkceLoginContract({
  origin:'https://127.0.0.1',secret:randomBytes(32),pendingStore,provider,
  now:()=>now,
  verifyIdentity:async jwt=>{
   assert.equal(jwt,TOKEN);
   if(verifyFailure)throw Error('GoTrue revoked');
   return {userId:U,sessionId:S,role:'EDITOR'};
  },
  issueDurableSession:async args=>{
   issued.push(args);
   if(issueFailure)throw Error('BFF durable SQL issue rejected');
   return {token:randomBytes(32).toString('base64url'),csrf:randomBytes(32).toString('base64url')};
  }
 });
 function url(){
  const redirect=sent.at(-1).redirectTo;
  const state=new URL(redirect).searchParams.get('state');
  return '/auth/callback?state='+encodeURIComponent(state)+'&code='+CODE;
 }
 return {ctl,states,sent,exchanges,issued,url,clock:x=>{now=x;}};
}
function stateCookie(r){return r.setCookie.split(';')[0];}
function expectCode(fn,code){return assert.rejects(fn,e=>e.code===code);}
test('start creates only encrypted five-minute challenge and neutral output',async()=>{
 const s=make(),r=await s.ctl.start({email:'synthetic@example.test'});
 assert.match(r.setCookie,/__Host-jianshi_pkce=.*Secure; HttpOnly; SameSite=Lax; Path=\/; Max-Age=300/);
 assert.match(r.message,/若邮箱可以接收/);
 assert.equal(s.states.size,1);
 const row=[...s.states.values()][0];
 assert.ok(!('email' in row)&&!('verifier' in row));
 assert.match(row.encryptedVerifier,/^v1\./);
 assert.ok(!JSON.stringify(r).includes('synthetic@example.test'));
 assert.ok(!JSON.stringify(r).includes('access_token'));
 assert.match(s.sent[0].codeChallenge,/^[A-Za-z0-9_-]{43}$/);
 assert.equal(r.headers['referrer-policy'],'no-referrer');
});
test('same-origin HTTPS callback issues host cookie, burns state, never reflects JWT/code',async()=>{
 const s=make();
 const r=await s.ctl.start({email:'synthetic@example.test'});
 const server=https.createServer(tls,async(req,res)=>{
  try{
   const out=await s.ctl.callback({
    url:req.url,cookieHeader:req.headers.cookie,requestOrigin:'https://127.0.0.1'
   });
   res.writeHead(303,{...out.headers,'location':out.location,'set-cookie':out.setCookies});
   res.end('');
  }catch(e){res.writeHead(403,{'cache-control':'no-store'});res.end('CMS_DENIED');}
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 try{
  const url='https://127.0.0.1:'+server.address().port+s.url();
  async function req(){
   return await new Promise((resolve,reject)=>{
    https.get(url,{rejectUnauthorized:false,headers:{cookie:stateCookie(r)}},resp=>{
     let body='';resp.on('data',b=>body+=b);
     resp.on('end',()=>resolve({http:resp.statusCode,headers:resp.headers,body}));
    }).on('error',reject);
   });
  }
  const ok=await req();
  assert.equal(ok.http,303);assert.equal(ok.headers.location,'/cms/');
  assert.equal(ok.headers['referrer-policy'],'no-referrer');
  assert.match(ok.headers['set-cookie'].join(';'),/__Host-jianshi_cms=.*Secure; HttpOnly; SameSite=Strict/);
  assert.ok(!JSON.stringify(ok).includes(TOKEN));
  assert.ok(!JSON.stringify(ok).includes(REFRESH));
  assert.ok(!JSON.stringify(ok).includes(CODE));
  const replay=await req();assert.equal(replay.http,403);
  assert.equal(s.exchanges.length,1);assert.equal(s.issued.length,1);
  assert.equal(s.issued[0].jwt,TOKEN);
 }finally{await new Promise(resolve=>server.close(resolve));}
});
test('wrong cookie does not burn state, malformed query and cross-origin denied',async()=>{
 const s=make(),r=await s.ctl.start({email:'synthetic@example.test'});
 const wrong='__Host-jianshi_pkce='+randomBytes(32).toString('base64url');
 await expectCode(s.ctl.callback({url:s.url(),cookieHeader:wrong,requestOrigin:'https://127.0.0.1'}),
  'CMS_PKCE_EXPIRED_OR_REPLAYED');
 const valid={url:s.url(),cookieHeader:stateCookie(r),requestOrigin:'https://127.0.0.1'};
 await expectCode(s.ctl.callback({...valid,url:s.url()+'&code=duplicate'}),
  'CMS_PKCE_CALLBACK_INVALID');
 await expectCode(s.ctl.callback({...valid,requestOrigin:'https://evil.invalid'}),
  'CMS_PKCE_ORIGIN_REJECTED');
 const ok=await s.ctl.callback(valid);assert.equal(ok.status,303);
});
test('simultaneous callback attempts have exactly one state consumer',async()=>{
 const s=make(),r=await s.ctl.start({email:'synthetic@example.test'});
 const params={url:s.url(),cookieHeader:stateCookie(r),requestOrigin:'https://127.0.0.1'};
 const results=await Promise.allSettled(Array.from({length:8},()=>s.ctl.callback(params)));
 assert.equal(results.filter(x=>x.status==='fulfilled').length,1);
 assert.equal(results.filter(x=>x.status==='rejected'&&
  x.reason.code==='CMS_PKCE_EXPIRED_OR_REPLAYED').length,7);
});
test('expired, invalid or revoked provider code can never be replayed',async()=>{
 const s=make(),r=await s.ctl.start({email:'synthetic@example.test'});
 const args={url:s.url(),cookieHeader:stateCookie(r),requestOrigin:'https://127.0.0.1'};
 s.clock(1791800000000+301000);
 await expectCode(s.ctl.callback(args),'CMS_PKCE_EXPIRED_OR_REPLAYED');
 const bad=make({failure:'exchange'}),b=await bad.ctl.start({email:'synthetic@example.test'});
 const p={url:bad.url(),cookieHeader:stateCookie(b),requestOrigin:'https://127.0.0.1'};
 await expectCode(bad.ctl.callback(p),'CMS_PKCE_VERIFICATION_FAILED');
 await expectCode(bad.ctl.callback(p),'CMS_PKCE_EXPIRED_OR_REPLAYED');
 const revoked=make({verifyFailure:true}),q=await revoked.ctl.start({email:'synthetic@example.test'});
 await expectCode(revoked.ctl.callback({
  url:revoked.url(),cookieHeader:stateCookie(q),requestOrigin:'https://127.0.0.1'
 }),'CMS_PKCE_VERIFICATION_FAILED');
 assert.equal(revoked.issued.length,0);
});
test('invalid test origin and missing provider adapter never open live login',()=>{
 assert.throws(()=>createPkceLoginContract({origin:'https://jianshi-bua.pages.dev'}),
  e=>e.code==='CMS_PKCE_FIXED_TEST_ORIGIN');
 assert.throws(()=>createPkceLoginContract({origin:'https://127.0.0.1',secret:randomBytes(32),pendingStore:{issue:()=>{},consume:()=>{}}}),
  e=>e.code==='CMS_PKCE_TRUSTED_ADAPTER_REQUIRED');
});
