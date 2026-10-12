// JIANSHI G2-H.7B: SYNTHETIC-only server-side token_hash confirmation.
// A GET from an email client NEVER redeems the token. Explicit same-origin
// user POST consumes a durable 5-minute PostgreSQL state before GoTrue verify.
// Distinct from H.6 auth-code PKCE. No real sender/server/database in module.
import {createHmac,randomBytes,hkdfSync,createCipheriv,createDecipheriv} from 'node:crypto';
const TEST_ORIGIN=/^https:\/\/localhost(?::([1-9][0-9]{0,4}))?$/;
function isTestOrigin(origin){
 const m=typeof origin==='string'&&TEST_ORIGIN.exec(origin);
 return Boolean(m&&(!m[1]||Number(m[1])<=65535));
}
const STATE=/^[A-Za-z0-9_-]{43}$/;
const HASH=/^[a-f0-9]{64}$/i;
const COOKIE_STATE='__Host-jianshi_mail_state';
const COOKIE_INTENT='__Host-jianshi_mail_intent';
const COOKIE_SESSION='__Host-jianshi_cms';
const TTL=300000;
const ID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const HEADERS=Object.freeze({
 'cache-control':'no-store, max-age=0','referrer-policy':'no-referrer',
 'x-content-type-options':'nosniff','content-security-policy':"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
});
function fail(code){const e=new Error(code);e.code=code;throw e;}
function need(condition,code){if(!condition)fail(code);}
function rnd(){return randomBytes(32).toString('base64url');}
function cookie(name,value,maxAge,site){
 return name+'='+value+'; Secure; HttpOnly; SameSite='+site+'; Path=/; Max-Age='+maxAge;
}
function extract(header,name,pattern){
 const parts=String(header||'').split(';').map(x=>x.trim())
  .filter(x=>x.startsWith(name+'='));
 need(parts.length===1,'CMS_EMAIL_COOKIE_MISSING_OR_DUPLICATE');
 const value=parts[0].slice(name.length+1);
 need(pattern.test(value),'CMS_EMAIL_COOKIE_INVALID');
 return value;
}
function requireQuery(url,origin){
 need(typeof url==='string'&&url.length<=2048&&url.startsWith('/auth/confirm?'),
  'CMS_EMAIL_LINK_INVALID');
 let u;try{u=new URL(url,origin);}catch{fail('CMS_EMAIL_LINK_INVALID');}
 need(u.pathname==='/auth/confirm'&&!u.hash&&u.searchParams.size===3&&
  [...u.searchParams.keys()].sort().join(',')==='state,token_hash,type'&&
  u.searchParams.getAll('state').length===1&&
  u.searchParams.getAll('token_hash').length===1&&
  u.searchParams.getAll('type').length===1&&
  u.searchParams.get('type')==='email','CMS_EMAIL_LINK_INVALID');
 const state=u.searchParams.get('state'),tokenHash=u.searchParams.get('token_hash');
 need(STATE.test(state||'')&&HASH.test(tokenHash||''),'CMS_EMAIL_LINK_INVALID');
 return {state,tokenHash};
}
export function createEmailTokenHashConfirm({
 origin,secret,pendingStore,provider,verifyIdentity,issueDurableSession,now=Date.now
}={}){
 need(process.env.JIANSHI_G2H7B_SYNTHETIC_ONLY==='1','CMS_EMAIL_LIVE_DISABLED');
 need(isTestOrigin(origin),'CMS_EMAIL_LOCALHOST_ONLY');
 need(Buffer.isBuffer(secret)&&secret.length===32,'CMS_EMAIL_SECRET_REQUIRED');
 need(pendingStore&&typeof pendingStore.issue==='function'&&
  typeof pendingStore.consume==='function'&&provider?.synthetic===true&&
  typeof provider.requestEmail==='function'&&
  typeof provider.verifyTokenHash==='function'&&
  typeof verifyIdentity==='function'&&typeof issueDurableSession==='function',
  'CMS_EMAIL_TRUSTED_ADAPTER_REQUIRED');
 const key=Buffer.from(secret);
 const aes=Buffer.from(hkdfSync('sha256',key,Buffer.alloc(0),
  'JIANSHI_G2H7B_EMAIL_INTENT_V1',32));
 const digest=(label,v)=>createHmac('sha256',key).update(label+'\0'+v).digest('hex');
 function seal(data,bind){
  const iv=randomBytes(12),c=createCipheriv('aes-256-gcm',aes,iv);
  c.setAAD(Buffer.from(bind));
  const raw=Buffer.concat([c.update(JSON.stringify(data),'utf8'),c.final()]);
  return 'v1.'+iv.toString('base64url')+'.'+raw.toString('base64url')+
   '.'+c.getAuthTag().toString('base64url');
 }
 function unseal(payload,bind){
  try{
   const p=payload.split('.');
   need(p.length===4&&p[0]==='v1','CMS_EMAIL_INTENT_INVALID');
   const iv=Buffer.from(p[1],'base64url'),tag=Buffer.from(p[3],'base64url');
   need(iv.length===12&&tag.length===16,'CMS_EMAIL_INTENT_INVALID');
   const c=createDecipheriv('aes-256-gcm',aes,iv);
   c.setAAD(Buffer.from(bind));c.setAuthTag(tag);
   const obj=JSON.parse(Buffer.concat([c.update(Buffer.from(p[2],'base64url')),
    c.final()]).toString('utf8'));
   need(obj&&STATE.test(obj.state||'')&&HASH.test(obj.tokenHash||'')&&
    Number.isFinite(obj.expiresAt)&&obj.expiresAt>now()&&
    obj.expiresAt<=now()+TTL,'CMS_EMAIL_INTENT_INVALID');
   return obj;
  }catch{fail('CMS_EMAIL_INTENT_INVALID');}
 }
 return Object.freeze({
  async start({email}={}){
   need(typeof email==='string'&&/^SYNTHETIC_[A-Za-z0-9_-]+@example\.invalid$/.test(email),
    'CMS_EMAIL_SYNTHETIC_ONLY');
   const state=rnd(),browserCookie=rnd();
   const recorded=await pendingStore.issue({
    stateDigest:digest('state',state),cookieDigest:digest('cookie',browserCookie),
    expiresAt:new Date(now()+TTL).toISOString()
   });
   need(recorded===true,'CMS_EMAIL_ISSUE_DENIED');
   const redirectTo=origin+'/auth/confirm?state='+state;
   try{
    const accepted=await provider.requestEmail({email,redirectTo});
    need(accepted?.accepted===true,'CMS_EMAIL_PROVIDER_UNAVAILABLE');
   }catch{fail('CMS_EMAIL_PROVIDER_UNAVAILABLE');}
   return Object.freeze({
    message:'如果此测试邮箱允许接收邮件，请手动打开链接并确认。',
    setCookie:cookie(COOKIE_STATE,browserCookie,300,'Lax'),headers:HEADERS,
    deliveryVerified:false
   });
  },
  // Only stages an encrypted intent; never calls verifyOtp or consumes SQL.
  async receiveLink({url,cookieHeader,requestOrigin}={}){
   need(requestOrigin===origin,'CMS_EMAIL_ORIGIN_DENIED');
   const {state,tokenHash}=requireQuery(url,origin);
   const browserCookie=extract(cookieHeader,COOKIE_STATE,STATE);
   const payload=seal({state,tokenHash,expiresAt:now()+TTL},
    digest('cookie',browserCookie));
   return Object.freeze({status:303,location:'/auth/confirm',
    setCookies:[cookie(COOKIE_INTENT,payload,300,'Strict')],
    headers:HEADERS,redeemed:false});
  },
  // POST should only be dispatched after an explicit, same-origin user action.
  async confirm({url,method,requestOrigin,fetchSite,cookieHeader}={}){
   need(method==='POST'&&url==='/auth/confirm','CMS_EMAIL_POST_REQUIRED');
   need(requestOrigin===origin&&fetchSite==='same-origin','CMS_EMAIL_CSRF_DENIED');
   const browserCookie=extract(cookieHeader,COOKIE_STATE,STATE);
   const intent=extract(cookieHeader,COOKIE_INTENT,/^v1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/);
   const {state,tokenHash}=unseal(intent,digest('cookie',browserCookie));
   const consumed=await pendingStore.consume({
    stateDigest:digest('state',state),cookieDigest:digest('cookie',browserCookie),
    at:new Date(now()).toISOString()
   });
   need(consumed?.used===true,'CMS_EMAIL_REPLAY_OR_EXPIRED');
   let result,actor,issued;
   try{
    result=await provider.verifyTokenHash({tokenHash});
    need(typeof result?.access_token==='string'&&
     typeof result?.refresh_token==='string','CMS_EMAIL_GOTRUE_INVALID');
    actor=await verifyIdentity(result.access_token);
    need(actor&&ID.test(actor.userId||'')&&ID.test(actor.sessionId||'')&&
     ['EDITOR','REVIEWER','PUBLISHER'].includes(actor.role),
     'CMS_EMAIL_VERIFIED_ACTOR_REQUIRED');
    // Opaque 15-minute session only. Refresh-token lifecycle is NOT deployed.
    issued=await issueDurableSession({jwt:result.access_token,actor});
    need(STATE.test(issued?.token||'')&&
      typeof issued?.csrf==='string'&&issued.csrf.length>=32,
      'CMS_EMAIL_DURABLE_SESSION_DENIED');
   }catch{fail('CMS_EMAIL_VERIFICATION_FAILED');}
   return Object.freeze({status:303,location:'/cms/',headers:HEADERS,
    setCookies:[
      cookie(COOKIE_STATE,'',0,'Lax'),cookie(COOKIE_INTENT,'',0,'Strict'),
      cookie(COOKIE_SESSION,issued.token,900,'Strict')
    ],csrf:issued.csrf,synthetic:true});
  }
 });
}
