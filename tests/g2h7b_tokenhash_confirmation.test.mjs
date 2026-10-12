import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import {createEmailTokenHashConfirm} from '../scripts/qa/g2h7b_tokenhash_confirmation.mjs';
const ORIGIN='https://localhost',MAIL='SYNTHETIC_EDITOR@example.invalid';
const HASH='a'.repeat(64);
const USER='00000000-0000-4000-8000-00000000a001';
const SESSION='00000000-0000-4000-8000-00000000a002';
const JWT='SYNTHETIC_ACCESS_TOKEN_FOR_ISOLATED_EMAIL_CONFIRM';
const REFRESH='SYNTHETIC_REFRESH_NEVER_SHOWN_TO_BROWSER_01234';
process.env.JIANSHI_G2H7B_SYNTHETIC_ONLY='1';
function make({failure='',currentTime=1791800000000}={}){
 const states=new Map(),logs={mail:[],redeemed:[],issued:[]},key=randomBytes(32);
 let now=currentTime;
 const store={
  async issue(v){
   assert.match(v.stateDigest,/^[a-f0-9]{64}$/);
   assert.match(v.cookieDigest,/^[a-f0-9]{64}$/);
   if(states.has(v.stateDigest))return false;
   states.set(v.stateDigest,{...v,used:false});return true;
  },
  async consume({stateDigest,cookieDigest,at}){
   const v=states.get(stateDigest);
   if(!v||v.used||v.cookieDigest!==cookieDigest||
     Date.parse(at)>=Date.parse(v.expiresAt))return {used:false};
   v.used=true;return {used:true};
  }
 };
 const provider={
  synthetic:true,
  async requestEmail(args){logs.mail.push(args);if(failure==='mail')throw Error('secret mail server');return {accepted:true};},
  async verifyTokenHash({tokenHash}){
   logs.redeemed.push(tokenHash);
   if(failure==='verify')throw Error('secret upstream token');
   assert.equal(tokenHash,HASH);
   return {access_token:JWT,refresh_token:REFRESH};
  }
 };
 const args={origin:ORIGIN,secret:key,pendingStore:store,provider,
  now:()=>now,verifyIdentity:async token=>{
   assert.equal(token,JWT);
   if(failure==='identity')throw Error('invalid real user');
   return {userId:USER,sessionId:SESSION,role:'EDITOR'};
  },
  issueDurableSession:async values=>{
   assert.equal(values.jwt,JWT);
   assert.equal(values.actor.userId,USER);
   logs.issued.push(true);
   if(failure==='issue')throw Error('secret backend');
   return {token:randomBytes(32).toString('base64url'),
     csrf:randomBytes(32).toString('base64url')};
  }};
 const controller=()=>createEmailTokenHashConfirm(args);
 return {controller,logs,states,clock:v=>now=v};
}
function first(cookies,name){return cookies.find(v=>v.startsWith(name+'=')).split(';')[0];}
async function staged(s){
 const ctl=s.controller(),begin=await ctl.start({email:MAIL});
 const state=new URL(s.logs.mail.at(-1).redirectTo).searchParams.get('state');
 const raw='/auth/confirm?state='+state+'&token_hash='+HASH+'&type=email';
 const stateCookie=first([begin.setCookie],'__Host-jianshi_mail_state');
 const landing=await ctl.receiveLink({url:raw,
  cookieHeader:stateCookie,requestOrigin:ORIGIN});
 const intentCookie=first(landing.setCookies,'__Host-jianshi_mail_intent');
 const params={url:'/auth/confirm',method:'POST',requestOrigin:ORIGIN,
  fetchSite:'same-origin',cookieHeader:stateCookie+'; '+intentCookie};
 return {ctl,begin,landing,stateCookie,intentCookie,params};
}
function code(promise,want){
 return assert.rejects(promise,e=>{assert.equal(e.code,want);return true;});
}
test('production disabled and no trusted adapter accepted',()=>{
 delete process.env.JIANSHI_G2H7B_SYNTHETIC_ONLY;
 assert.throws(()=>make().controller(),/CMS_EMAIL_LIVE_DISABLED/);
 process.env.JIANSHI_G2H7B_SYNTHETIC_ONLY='1';
 assert.throws(()=>createEmailTokenHashConfirm({origin:'https://jianshi-bua.pages.dev'}),
  /CMS_EMAIL_LOCALHOST_ONLY/);
 assert.throws(()=>createEmailTokenHashConfirm({origin:ORIGIN,secret:randomBytes(32)}),
  /CMS_EMAIL_TRUSTED_ADAPTER_REQUIRED/);
});
test('GET link only encrypts intent, no token redemption or bearer leak',async()=>{
 const s=make(),{begin,landing}=await staged(s);
 assert.match(begin.setCookie,/Secure; HttpOnly; SameSite=Lax/);
 assert.equal(s.logs.mail.length,1);
 assert.equal(s.logs.mail[0].email,MAIL);
 assert.match(s.logs.mail[0].redirectTo,/^https:\/\/localhost\/auth\/confirm\?state=[A-Za-z0-9_-]{43}$/);
 assert.equal(landing.status,303);assert.equal(landing.location,'/auth/confirm');
 assert.equal(landing.redeemed,false);
 assert.match(landing.setCookies[0],/Secure; HttpOnly; SameSite=Strict/);
 assert.equal(s.logs.redeemed.length,0);
 assert.equal([...s.states.values()][0].used,false);
 const output=JSON.stringify({begin,landing});
 assert.ok(!output.includes(HASH)&&!output.includes(JWT)&&!output.includes(REFRESH));
 assert.equal(landing.headers['referrer-policy'],'no-referrer');
});
test('POST after explicit confirmation consumes state and issues opaque cookie',async()=>{
 const s=make(),v=await staged(s);
 const answer=await v.ctl.confirm(v.params);
 assert.equal(answer.status,303);assert.equal(answer.location,'/cms/');
 assert.match(answer.setCookies.join(';'),/__Host-jianshi_cms=.*Secure; HttpOnly; SameSite=Strict/);
 assert.equal(s.logs.redeemed.length,1);assert.equal(s.logs.issued.length,1);
 assert.equal([...s.states.values()][0].used,true);
 assert.ok(!JSON.stringify(answer).includes(HASH));
 assert.ok(!JSON.stringify(answer).includes(JWT));
 assert.ok(!JSON.stringify(answer).includes(REFRESH));
 await code(v.ctl.confirm(v.params),'CMS_EMAIL_REPLAY_OR_EXPIRED');
 assert.equal(s.logs.redeemed.length,1);
});
test('wrong cookie, forged intent, CSRF, duplicate params never burn state',async()=>{
 const s=make(),v=await staged(s);
 await code(v.ctl.confirm({...v.params,requestOrigin:'https://evil.invalid'}),'CMS_EMAIL_CSRF_DENIED');
 await code(v.ctl.confirm({...v.params,fetchSite:'cross-site'}),'CMS_EMAIL_CSRF_DENIED');
 await code(v.ctl.confirm({...v.params,method:'GET'}),'CMS_EMAIL_POST_REQUIRED');
 await code(v.ctl.confirm({...v.params,url:'/auth/confirm?token_hash='+HASH}),'CMS_EMAIL_POST_REQUIRED');
 await code(v.ctl.confirm({...v.params,
  cookieHeader:v.stateCookie+'; '+v.intentCookie+'; '+v.intentCookie}),
  'CMS_EMAIL_COOKIE_MISSING_OR_DUPLICATE');
 const fake='__Host-jianshi_mail_state='+randomBytes(32).toString('base64url');
 await code(v.ctl.confirm({...v.params,
  cookieHeader:fake+'; '+v.intentCookie}),'CMS_EMAIL_INTENT_INVALID');
 const raw='/auth/confirm?state='+new URL(s.logs.mail[0].redirectTo).searchParams.get('state')+
  '&token_hash='+HASH+'&type=email&extra=123';
 await code(v.ctl.receiveLink({url:raw,cookieHeader:v.stateCookie,requestOrigin:ORIGIN}),
  'CMS_EMAIL_LINK_INVALID');
 assert.equal([...s.states.values()][0].used,false);
 const ok=await v.ctl.confirm(v.params);assert.equal(ok.status,303);
});
test('email scanner without original cookie cannot stage or consume state',async()=>{
 const s=make(),v=await staged(s);
 const raw='/auth/confirm?state='+new URL(s.logs.mail[0].redirectTo).searchParams.get('state')+
  '&token_hash='+HASH+'&type=email';
 await code(v.ctl.receiveLink({url:raw,cookieHeader:'',requestOrigin:ORIGIN}),
  'CMS_EMAIL_COOKIE_MISSING_OR_DUPLICATE');
 assert.equal([...s.states.values()][0].used,false);
 assert.equal(s.logs.redeemed.length,0);
 await v.ctl.confirm(v.params);
});
test('two isolated controllers with one state: exactly 1 of 8 concurrent POST succeeds',async()=>{
 const s=make(),v=await staged(s),other=s.controller();
 const outcomes=await Promise.allSettled(Array.from({length:8},(_,i)=>
  (i%2===0?v.ctl:other).confirm(v.params)));
 assert.equal(outcomes.filter(x=>x.status==='fulfilled').length,1);
 assert.equal(outcomes.filter(x=>x.status==='rejected'&&
  x.reason.code==='CMS_EMAIL_REPLAY_OR_EXPIRED').length,7);
 assert.equal(s.logs.redeemed.length,1);
});
test('expired intent and consumed upstream failure deny reuse',async()=>{
 const s=make(),v=await staged(s);
 s.clock(1791800000000+301000);
 await code(v.ctl.confirm(v.params),'CMS_EMAIL_INTENT_INVALID');
 assert.equal(s.logs.redeemed.length,0);
 const failed=make({failure:'verify'}),v2=await staged(failed);
 await code(v2.ctl.confirm(v2.params),'CMS_EMAIL_VERIFICATION_FAILED');
 await code(v2.ctl.confirm(v2.params),'CMS_EMAIL_REPLAY_OR_EXPIRED');
 assert.equal(failed.logs.redeemed.length,1);
 assert.equal(failed.logs.issued.length,0);
});
