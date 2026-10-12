// JIANSHI G2-H.6 — closed-by-default passwordless PKCE CALLBACK CONTRACT.
// Not the live Supabase GoTrue adapter, not a browser-facing deployed server.
// A future HTTPS BFF must supply a transactional one-time pendingStore,
// vetted PKCE provider adapter and verified durable session issuer.
import {createHash,createHmac,randomBytes,createCipheriv,createDecipheriv,hkdfSync} from 'node:crypto';

const STATE_COOKIE='__Host-jianshi_pkce';
const SESSION_COOKIE='__Host-jianshi_cms';
const TTL=5*60*1000;
const STATE=/^[A-Za-z0-9_-]{43}$/;
const CODE=/^[A-Za-z0-9_-]{8,256}$/;
const ID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function fail(code){const e=new Error(code);e.code=code;throw e;}
function need(ok,code){if(!ok)fail(code);}
function hash(secret,label,value){
 return createHmac('sha256',secret).update(label).update('\0').update(value).digest('hex');
}
function random(){return randomBytes(32).toString('base64url');}
function requiredCookie(name,value,maxAge,site){
 return name+'='+value+'; Secure; HttpOnly; SameSite='+site+'; Path=/; Max-Age='+maxAge;
}
function hasOnlyValidCookie(header){
 const items=(header||'').split(';').map(v=>v.trim()).filter(v=>v.startsWith(STATE_COOKIE+'='));
 need(items.length===1,'CMS_PKCE_COOKIE_MISSING_OR_DUPLICATE');
 const value=items[0].slice(STATE_COOKIE.length+1);
 need(STATE.test(value),'CMS_PKCE_COOKIE_INVALID');
 return value;
}
function safeQuery(input){
 need(typeof input==='string'&&input.length<=2048,'CMS_PKCE_CALLBACK_INVALID');
 const u=new URL(input,'https://callback.invalid');
 need(u.pathname==='/auth/callback'&&!u.hash&&!u.username&&!u.password,'CMS_PKCE_CALLBACK_INVALID');
 need(u.searchParams.size===2&&u.searchParams.has('code')&&u.searchParams.has('state')&&
  u.searchParams.getAll('code').length===1&&u.searchParams.getAll('state').length===1,
  'CMS_PKCE_CALLBACK_INVALID');
 const code=u.searchParams.get('code'),state=u.searchParams.get('state');
 need(CODE.test(code||'')&&STATE.test(state||''),'CMS_PKCE_CALLBACK_INVALID');
 return {code,state};
}
function assertIdentity(value){
 need(value&&ID.test(value.userId||'')&&ID.test(value.sessionId||'')&&
  ['EDITOR','REVIEWER','PUBLISHER'].includes(value.role),
  'CMS_PKCE_VERIFIED_USER_REQUIRED');
}
export function createPkceLoginContract({
 origin,secret,pendingStore,provider,verifyIdentity,issueDurableSession,now=Date.now
}={}){
 need(process.env.JIANSHI_G2H6_SYNTHETIC_ONLY==='1','CMS_PKCE_LIVE_DISABLED');
 need(origin==='https://127.0.0.1'||origin==='https://localhost',
  'CMS_PKCE_FIXED_TEST_ORIGIN');
 need(Buffer.isBuffer(secret)&&secret.length===32,'CMS_PKCE_SECRET_INVALID');
 need(pendingStore?.issue&&pendingStore?.consume&&
  provider?.sendMagicLink&&provider?.exchangeCodeForSession&&
  typeof verifyIdentity==='function'&&typeof issueDurableSession==='function',
  'CMS_PKCE_TRUSTED_ADAPTER_REQUIRED');
 const key=Buffer.from(secret);
 const cipherKey=Buffer.from(hkdfSync('sha256',key,Buffer.alloc(0),'JIANSHI_G2H6_PKCE_PENDING_AES_GCM',32));
 function seal(verifier,stateDigest,cookieDigest){
  const iv=randomBytes(12),a=createCipheriv('aes-256-gcm',cipherKey,iv);
  a.setAAD(Buffer.from(stateDigest+'|'+cookieDigest));
  const ciphertext=Buffer.concat([a.update(verifier,'utf8'),a.final()]);
  return 'v1.'+iv.toString('base64url')+'.'+ciphertext.toString('base64url')+'.'+a.getAuthTag().toString('base64url');
 }
 function open(encrypted,stateDigest,cookieDigest){
  try{
   const parts=encrypted.split('.');
   need(parts.length===4&&parts[0]==='v1','CMS_PKCE_ENVELOPE_INVALID');
   const iv=Buffer.from(parts[1],'base64url'),tag=Buffer.from(parts[3],'base64url');
   need(iv.length===12&&tag.length===16,'CMS_PKCE_ENVELOPE_INVALID');
   const d=createDecipheriv('aes-256-gcm',cipherKey,iv);
   d.setAAD(Buffer.from(stateDigest+'|'+cookieDigest));d.setAuthTag(tag);
   const result=Buffer.concat([d.update(Buffer.from(parts[2],'base64url')),d.final()]).toString('utf8');
   need(STATE.test(result),'CMS_PKCE_ENVELOPE_INVALID');return result;
  }catch{fail('CMS_PKCE_ENVELOPE_INVALID');}
 }
 const publicHeaders=Object.freeze({
  'cache-control':'no-store, max-age=0',
  'referrer-policy':'no-referrer',
  'x-content-type-options':'nosniff'
 });
 return Object.freeze({
  async start({email}={}){
   need(typeof email==='string'&&email.length>=5&&email.length<=254&&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email),'CMS_PKCE_EMAIL_INVALID');
   const state=random(),cookie=random(),verifier=random();
   const stateDigest=hash(key,'state',state);
   const cookieDigest=hash(key,'cookie',cookie);
   const challenge=createHash('sha256').update(verifier).digest('base64url');
   // Transactional state storage must expire and consume atomically, even
   // across different BFF instances; never store raw state/cookie or email.
   const issued=await pendingStore.issue({
    stateDigest,cookieDigest,encryptedVerifier:seal(verifier,stateDigest,cookieDigest),
    expiresAt:new Date(now()+TTL).toISOString()
   });
   need(issued===true,'CMS_PKCE_PENDING_ISSUE_FAILED');
   const redirectTo=origin+'/auth/callback?state='+encodeURIComponent(state);
   try{
    const sent=await provider.sendMagicLink({email,redirectTo,codeChallenge:challenge});
    need(sent===true,'CMS_PKCE_MAIL_UNAVAILABLE');
   }catch{
    // Caller should show a neutral status to avoid email enumeration.
    // An unused pending record expires; it cannot authenticate without code.
    fail('CMS_PKCE_MAIL_UNAVAILABLE');
   }
   return Object.freeze({
    message:'若邮箱可以接收验证邮件，请按邮件说明继续。',
    setCookie:requiredCookie(STATE_COOKIE,cookie,300,'Lax'),
    headers:publicHeaders
   });
  },
  async callback({url,cookieHeader,requestOrigin}={}){
   // The HTTPS host routes only /auth/callback to this handler.
   // Never echo URL/code/verifier/JWT and never log request URLs at ingress.
   need(requestOrigin===origin,'CMS_PKCE_ORIGIN_REJECTED');
   const {code,state}=safeQuery(url);
   const cookie=hasOnlyValidCookie(cookieHeader);
   const pending=await pendingStore.consume({
    stateDigest:hash(key,'state',state),
    cookieDigest:hash(key,'cookie',cookie),
    at:new Date(now()).toISOString()
   });
   // consume is ATOMIC and one-time. A failed GoTrue exchange must still
   // permanently burn this challenge to prevent replay or parallel attempts.
   need(pending&&pending.used===true&&typeof pending.encryptedVerifier==='string','CMS_PKCE_EXPIRED_OR_REPLAYED');
   let result,actor,session;
   try{
    const verifier=open(pending.encryptedVerifier,
      hash(key,'state',state),hash(key,'cookie',cookie));
    result=await provider.exchangeCodeForSession({code,verifier});
    need(typeof result?.access_token==='string'&&result.access_token.length>=32&&
      typeof result?.refresh_token==='string'&&result.refresh_token.length>=32,
      'CMS_PKCE_PROVIDER_REJECTED');
    actor=await verifyIdentity(result.access_token);
    assertIdentity(actor);
    session=await issueDurableSession({jwt:result.access_token,actor});
    need(session&&STATE.test(session.token)&&
      typeof session.csrf==='string'&&session.csrf.length>=32,
      'CMS_PKCE_SESSION_ISSUE_FAILED');
   }catch{
    fail('CMS_PKCE_VERIFICATION_FAILED');
   }
   // Refresh token must remain server-side under the approved session
   // lifecycle contract; this callback does not store/echo it anywhere.
   return Object.freeze({
    status:303,location:'/cms/',
    headers:publicHeaders,
    setCookies:[
      requiredCookie(STATE_COOKIE,'',0,'Lax'),
      requiredCookie(SESSION_COOKIE,session.token,900,'Strict')
    ],
    csrf:session.csrf // only for trusted BFF response handler, never URL or log
   });
  }
 });
}
