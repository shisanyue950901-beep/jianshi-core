// JIANSHI G2-H.7E — Workers-native WebCrypto, SYNTHETIC contract only.
// No process / Buffer / node:crypto / network / real secrets / Cloudflare deployment.
// Both controller and route fail closed outside non-routable .invalid test origin.
const ORIGIN='https://h7d-preview.example.invalid';
const ACTIVE='SYNTHETIC_H7E_ONLY';
const STATE=/^[A-Za-z0-9_-]{43}$/;
const HASH=/^[a-f0-9]{64}$/i;
const USER=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const EMAIL=/^SYNTHETIC_[A-Za-z0-9_-]+@example\.invalid$/;
const INTENT=/^v1\.[A-Za-z0-9_-]{16}\.[A-Za-z0-9_-]{1,800}\.[A-Za-z0-9_-]{22}$/;
const TTL_MS=300000;
const utf8=new TextEncoder();
const decode=new TextDecoder('utf-8',{fatal:true});
function deny(code){const error=new Error(code);error.code=code;throw error;}
function must(ok,code){if(!ok)deny(code);}
function bytesToUrl(bytes){
 let result='';
 for(let i=0;i<bytes.length;i+=4096)
  result+=String.fromCharCode(...bytes.subarray(i,i+4096));
 return btoa(result).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
}
function urlToBytes(value){
 must(typeof value==='string'&&/^[A-Za-z0-9_-]+$/.test(value)&&value.length<=1024,
  'CMS_H7E_INTENT_INVALID');
 try{
  const raw=atob(value.replace(/-/g,'+').replace(/_/g,'/')+
    '='.repeat((4-value.length%4)%4));
  const result=Uint8Array.from(raw,c=>c.charCodeAt(0));
  must(bytesToUrl(result)===value,'CMS_H7E_INTENT_INVALID');
  return result;
 }catch{deny('CMS_H7E_INTENT_INVALID');}
}
function randomState(){
 const b=new Uint8Array(32);crypto.getRandomValues(b);return bytesToUrl(b);
}
function extractCookie(header,name,pattern){
 const found=String(header||'').split(';').map(x=>x.trim())
  .filter(x=>x.startsWith(name+'='));
 must(found.length===1,'CMS_H7E_COOKIE_INVALID');
 const value=found[0].slice(name.length+1);
 must(pattern.test(value),'CMS_H7E_COOKIE_INVALID');
 return value;
}
function cookie(name,value,ttl,sameSite){
 return name+'='+value+'; Secure; HttpOnly; SameSite='+sameSite+
  '; Path=/; Max-Age='+ttl;
}
function strictLink(raw){
 must(typeof raw==='string'&&raw.startsWith('/auth/confirm?')&&
  raw.length<=1024,'CMS_H7E_LINK_INVALID');
 let u;try{u=new URL(raw,ORIGIN);}catch{deny('CMS_H7E_LINK_INVALID');}
 must(u.origin===ORIGIN&&u.pathname==='/auth/confirm'&&!u.hash&&
  [...u.searchParams.keys()].sort().join(',')==='state,token_hash,type'&&
  u.searchParams.size===3&&
  u.searchParams.getAll('state').length===1&&
  u.searchParams.getAll('token_hash').length===1&&
  u.searchParams.getAll('type').length===1&&
  u.searchParams.get('type')==='email','CMS_H7E_LINK_INVALID');
 const state=u.searchParams.get('state'),tokenHash=u.searchParams.get('token_hash');
 must(STATE.test(state||'')&&HASH.test(tokenHash||''),'CMS_H7E_LINK_INVALID');
 return {state,tokenHash};
}
async function deriveKeys(raw){
 const hmac=await crypto.subtle.importKey('raw',raw,{name:'HMAC',hash:'SHA-256'},
  false,['sign']);
 const root=await crypto.subtle.importKey('raw',raw,'HKDF',false,['deriveKey']);
 const aes=await crypto.subtle.deriveKey({
  name:'HKDF',hash:'SHA-256',salt:new Uint8Array(0),
  // Same HKDF string as the H.7B Node AES-GCM envelope; interoperability
  // must still be verified with independent known vectors before live use.
  info:utf8.encode('JIANSHI_G2H7B_EMAIL_INTENT_V1')
 },root,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
 return {hmac,aes};
}
function noSecretsReturned(){
 return Object.freeze({
  'cache-control':'private, no-store, max-age=0',
  'referrer-policy':'no-referrer','x-content-type-options':'nosniff'
 });
}
export async function createSyntheticWorkerEmailConfirm({
 origin,profile,secret,pendingStore,provider,verifyIdentity,issueSession,
 now=Date.now
}={}){
 must(origin===ORIGIN&&profile===ACTIVE,'CMS_H7E_NONROUTABLE_ONLY');
 must(secret instanceof Uint8Array&&secret.byteLength===32,'CMS_H7E_TEST_KEY_INVALID');
 must(pendingStore?.synthetic===true&&
  typeof pendingStore.issue==='function'&&typeof pendingStore.consume==='function'&&
  provider?.synthetic===true&&typeof provider.requestEmail==='function'&&
  typeof provider.verifyTokenHash==='function'&&
  verifyIdentity?.synthetic===true&&typeof verifyIdentity.run==='function'&&
  issueSession?.synthetic===true&&typeof issueSession.run==='function',
  'CMS_H7E_SYNTHETIC_ADAPTER_REQUIRED');
 const keys=await deriveKeys(secret);
 async function digest(kind,content){
  const signature=await crypto.subtle.sign('HMAC',keys.hmac,
   utf8.encode(kind+'\0'+content));
  return [...new Uint8Array(signature)].map(x=>x.toString(16).padStart(2,'0')).join('');
 }
 async function seal(state,tokenHash,browserCookie){
  const expiry=now()+TTL_MS;
  const binding=await digest('cookie',browserCookie);
  const iv=new Uint8Array(12);crypto.getRandomValues(iv);
  const data=utf8.encode(JSON.stringify({state,tokenHash,expiresAt:expiry}));
  const sealed=new Uint8Array(await crypto.subtle.encrypt({
   name:'AES-GCM',iv,additionalData:utf8.encode(binding),tagLength:128
  },keys.aes,data));
  return 'v1.'+bytesToUrl(iv)+'.'+bytesToUrl(sealed.subarray(0,-16))+
   '.'+bytesToUrl(sealed.subarray(-16));
 }
 async function unseal(envelope,browserCookie){
  try{
   must(INTENT.test(envelope),'CMS_H7E_INTENT_INVALID');
   const [,iv,body,tag]=envelope.split('.').map((x,i)=>i===0?x:urlToBytes(x));
   must(iv.length===12&&tag.length===16&&body.length>0&&body.length<=600,
    'CMS_H7E_INTENT_INVALID');
   const full=new Uint8Array(body.length+tag.length);
   full.set(body);full.set(tag,body.length);
   const clear=await crypto.subtle.decrypt({
    name:'AES-GCM',iv,additionalData:utf8.encode(await digest('cookie',browserCookie)),
    tagLength:128
   },keys.aes,full);
   const data=JSON.parse(decode.decode(clear));
   must(data&&STATE.test(data.state||'')&&HASH.test(data.tokenHash||'')&&
    Number.isSafeInteger(data.expiresAt)&&data.expiresAt>now()&&
    data.expiresAt<=now()+TTL_MS,'CMS_H7E_INTENT_INVALID');
   return data;
  }catch{deny('CMS_H7E_INTENT_INVALID');}
 }
 return Object.freeze({
  synthetic:true,
  async start({email}={}){
   must(typeof email==='string'&&EMAIL.test(email)&&email.length<=255,
    'CMS_H7E_SYNTHETIC_EMAIL_ONLY');
   const state=randomState(),browserCookie=randomState();
   const issued=await pendingStore.issue({
    stateDigest:await digest('state',state),
    cookieDigest:await digest('cookie',browserCookie),
    expiresAt:new Date(now()+TTL_MS).toISOString()
   });
   must(issued===true,'CMS_H7E_STATE_ISSUE_DENIED');
   try{
    const sent=await provider.requestEmail({
     email,redirectTo:ORIGIN+'/auth/confirm?state='+state
    });
    must(sent?.accepted===true,'CMS_H7E_PROVIDER_UNAVAILABLE');
   }catch{deny('CMS_H7E_PROVIDER_UNAVAILABLE');}
   return Object.freeze({
    accepted:true,deliveryVerified:false,
    setCookie:cookie('__Host-jianshi_mail_state',browserCookie,300,'Lax'),
    headers:noSecretsReturned()
   });
  },
  async receiveLink({url,cookieHeader,requestOrigin}={}){
   must(requestOrigin===ORIGIN,'CMS_H7E_ORIGIN_DENIED');
   const {state,tokenHash}=strictLink(url);
   const browserCookie=extractCookie(cookieHeader,'__Host-jianshi_mail_state',STATE);
   const envelope=await seal(state,tokenHash,browserCookie);
   return Object.freeze({
    status:303,location:'/auth/confirm',redeemed:false,
    headers:noSecretsReturned(),
    setCookies:[cookie('__Host-jianshi_mail_intent',envelope,300,'Strict')]
   });
  },
  async confirm({url,method,requestOrigin,fetchSite,cookieHeader}={}){
   must(method==='POST'&&url==='/auth/confirm','CMS_H7E_POST_REQUIRED');
   must(requestOrigin===ORIGIN&&fetchSite==='same-origin','CMS_H7E_CSRF_DENIED');
   const browserCookie=extractCookie(cookieHeader,'__Host-jianshi_mail_state',STATE);
   const envelope=extractCookie(cookieHeader,'__Host-jianshi_mail_intent',INTENT);
   const {state,tokenHash}=await unseal(envelope,browserCookie);
   // This is the ONLY boundary at which token_hash may be redeemed.
   // A distributed store MUST return {used:true} to at most one caller.
   const consumed=await pendingStore.consume({
    stateDigest:await digest('state',state),
    cookieDigest:await digest('cookie',browserCookie),
    at:new Date(now()).toISOString()
   });
   must(consumed?.used===true,'CMS_H7E_REPLAY_OR_EXPIRED');
   let session;
   try{
    const otp=await provider.verifyTokenHash({tokenHash});
    must(typeof otp?.access_token==='string'&&
     otp.access_token.startsWith('SYNTHETIC_')&&
     typeof otp?.refresh_token==='string'&&
     otp.refresh_token.startsWith('SYNTHETIC_'),
     'CMS_H7E_SYNTHETIC_TOKENS_ONLY');
    const actor=await verifyIdentity.run(otp.access_token);
    must(USER.test(actor?.userId||'')&&USER.test(actor?.sessionId||'')&&
     ['EDITOR','REVIEWER','PUBLISHER'].includes(actor.role),
     'CMS_H7E_ACTOR_DENIED');
    session=await issueSession.run({accessToken:otp.access_token,actor});
    must(STATE.test(session?.token||'')&&STATE.test(session?.csrf||''),
     'CMS_H7E_SESSION_DENIED');
   }catch{deny('CMS_H7E_AUTH_DENIED');}
   return Object.freeze({
    status:303,location:'/cms/',synthetic:true,headers:noSecretsReturned(),
    setCookies:[
     cookie('__Host-jianshi_mail_state','',0,'Lax'),
     cookie('__Host-jianshi_mail_intent','',0,'Strict'),
     cookie('__Host-jianshi_cms',session.token,900,'Strict')
    ]
   });
  }
 });
}
export const WORKER_CONTRACT_ORIGIN=ORIGIN;
