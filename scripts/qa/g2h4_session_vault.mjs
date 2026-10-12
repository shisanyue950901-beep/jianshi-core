// G2-H.4: BFF-side secure envelope primitives. NO server entrypoint or network.
// A future trusted HTTPS BFF supplies protected keys using its secrets manager.
// Postgres gets only HMAC digests and AES-256-GCM-encrypted JWT envelopes.
import {
  createCipheriv,createDecipheriv,createHmac,randomBytes,timingSafeEqual
} from 'node:crypto';

const ID=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const KID=/^[a-zA-Z0-9_-]{1,32}$/;
function fail(code){const e=new Error(code);e.code=code;throw e;}
function valid(ok,code){if(!ok)fail(code);}
function keyBytes(x){
 valid(Buffer.isBuffer(x)&&x.length===32,'CMS_VAULT_KEY_INVALID');
 return Buffer.from(x);
}
function aad(userId,sessionId){
 valid(ID.test(userId||'')&&ID.test(sessionId||''),'CMS_VAULT_BINDING_INVALID');
 return Buffer.from('JIANSHi.G2H4.JWT.v1|'+userId+'|'+sessionId,'utf8');
}
function digest(secret,kind,text){
 valid(typeof text==='string'&&text.length>=32&&text.length<=200,
  'CMS_VAULT_TOKEN_INVALID');
 return createHmac('sha256',secret).update(kind).update('\0').update(text).digest('hex');
}
export function createSessionVault({hmacKey,csrfKey,keys,activeKeyId}={}){
 const hmac=keyBytes(hmacKey),csrf=keyBytes(csrfKey);
 valid(!timingSafeEqual(hmac,csrf),'CMS_VAULT_KEYS_NOT_SEPARATED');
 valid(keys&&typeof keys==='object'&&!Array.isArray(keys) &&
  KID.test(activeKeyId||''),'CMS_VAULT_KEYRING_INVALID');
 const ring=new Map();
 for(const [name,key] of Object.entries(keys)){
  valid(KID.test(name),'CMS_VAULT_KEYRING_INVALID');
  ring.set(name,keyBytes(key));
 }
 valid(ring.has(activeKeyId),'CMS_VAULT_ACTIVE_KEY_MISSING');
 return Object.freeze({
  newCookie(){return randomBytes(32).toString('base64url');},
  newCsrf(){return randomBytes(32).toString('base64url');},
  cookieDigest:value=>digest(hmac,'cookie',value),
  csrfDigest:value=>digest(csrf,'csrf',value),
  issueEnvelope({jwt,userId,sessionId}={}){
   valid(typeof jwt==='string'&&jwt.length>=32&&jwt.length<=6000,
     'CMS_VAULT_JWT_INVALID');
   const iv=randomBytes(12),key=ring.get(activeKeyId);
   const c=createCipheriv('aes-256-gcm',key,iv);
   c.setAAD(aad(userId,sessionId));
   const ciphertext=Buffer.concat([c.update(jwt,'utf8'),c.final()]);
   return Object.freeze({
    key_id:activeKeyId,
    encrypted_jwt:'v1.'+iv.toString('base64url')+'.'+
      ciphertext.toString('base64url')+'.'+c.getAuthTag().toString('base64url')
   });
  },
  openEnvelope({encrypted_jwt,key_id,userId,sessionId}={}){
   valid(typeof encrypted_jwt==='string'&&encrypted_jwt.length<13000 &&
     KID.test(key_id||''),'CMS_VAULT_ENVELOPE_INVALID');
   const key=ring.get(key_id);
   valid(!!key,'CMS_VAULT_KEY_UNAVAILABLE');
   const pieces=encrypted_jwt.split('.');
   valid(pieces.length===4&&pieces[0]==='v1'&&
     pieces.slice(1).every(x=>/^[A-Za-z0-9_-]+$/.test(x)),
     'CMS_VAULT_ENVELOPE_INVALID');
   const iv=Buffer.from(pieces[1],'base64url');
   const ciphertext=Buffer.from(pieces[2],'base64url');
   const tag=Buffer.from(pieces[3],'base64url');
   valid(iv.length===12&&tag.length===16&&ciphertext.length>=1,
     'CMS_VAULT_ENVELOPE_INVALID');
   try{
    const d=createDecipheriv('aes-256-gcm',key,iv);
    d.setAAD(aad(userId,sessionId));
    d.setAuthTag(tag);
    const jwt=Buffer.concat([d.update(ciphertext),d.final()]).toString('utf8');
    valid(jwt.length>=32&&jwt.length<=6000,'CMS_VAULT_JWT_INVALID');
    return jwt;
   }catch{fail('CMS_VAULT_AUTHENTICATION_FAILED');}
  }
 });
}
