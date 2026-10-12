import test from 'node:test';
import assert from 'node:assert/strict';
import {randomBytes} from 'node:crypto';
import {createSessionVault} from '../scripts/qa/g2h4_session_vault.mjs';

const A='00000000-0000-4000-8000-00000000a001';
const B='00000000-0000-4000-8000-00000000a002';
const S='00000000-0000-4000-8000-00000000a003';
const OTHER='00000000-0000-4000-8000-00000000a004';
const JWT='SYNTHETIC_ONLY_JWT_NEVER_VALID_FROM_GOTRUE.HEADER.PAYLOAD.SIGNATURE';
const k1=randomBytes(32),k2=randomBytes(32),hm=randomBytes(32),csrf=randomBytes(32);
function vault(active='k1',keys={k1,k2},hmacKey=hm,csrfKey=csrf){
 return createSessionVault({keys,activeKeyId:active,hmacKey,csrfKey});
}
function refused(fn,code){assert.throws(fn,e=>e.code===code);}
test('opaque random cookie and CSRF digests: distinct, stable and never plaintext',()=>{
 const v=vault(),cookie=v.newCookie(),token=v.newCsrf();
 assert.notEqual(cookie,token);assert.ok(cookie.length>=40);
 const a=v.cookieDigest(cookie),b=v.csrfDigest(cookie);
 assert.equal(a.length,64);assert.equal(b.length,64);assert.notEqual(a,b);
 assert.equal(v.cookieDigest(cookie),a);
 assert.notEqual(v.cookieDigest(v.newCookie()),a);
 assert.notEqual(v.csrfDigest(token),v.cookieDigest(token));
 assert.ok(!a.includes(cookie));
});
test('AES-256-GCM binds JWT to verified user and GoTrue auth.session',()=>{
 const v=vault(),envelope=v.issueEnvelope({jwt:JWT,userId:A,sessionId:S});
 assert.equal(envelope.key_id,'k1');
 assert.ok(envelope.encrypted_jwt.startsWith('v1.'));
 assert.ok(!envelope.encrypted_jwt.includes(JWT));
 assert.equal(v.openEnvelope({...envelope,userId:A,sessionId:S}),JWT);
 refused(()=>v.openEnvelope({...envelope,userId:B,sessionId:S}),
  'CMS_VAULT_AUTHENTICATION_FAILED');
 refused(()=>v.openEnvelope({...envelope,userId:A,sessionId:OTHER}),
  'CMS_VAULT_AUTHENTICATION_FAILED');
});
test('tampered ciphertext, tag, IV, envelope and unknown key all fail closed',()=>{
 const v=vault(),e=v.issueEnvelope({jwt:JWT,userId:A,sessionId:S});
 for(const pos of [1,2,3]){
  const parts=e.encrypted_jwt.split('.');
  parts[pos]=(parts[pos][0]==='A'?'B':'A')+parts[pos].slice(1);
  refused(()=>v.openEnvelope({...e,encrypted_jwt:parts.join('.'),userId:A,sessionId:S}),
   'CMS_VAULT_AUTHENTICATION_FAILED');
 }
 refused(()=>v.openEnvelope({...e,encrypted_jwt:'v2.a.b.c',userId:A,sessionId:S}),
  'CMS_VAULT_ENVELOPE_INVALID');
 refused(()=>v.openEnvelope({...e,key_id:'deleted',userId:A,sessionId:S}),
  'CMS_VAULT_KEY_UNAVAILABLE');
});
test('rotation uses active key for new sessions and explicitly retains or retires old key',()=>{
 const previous=vault('k1'),newVersion=vault('k2');
 const old=previous.issueEnvelope({jwt:JWT,userId:A,sessionId:S});
 const next=newVersion.issueEnvelope({jwt:JWT,userId:A,sessionId:S});
 assert.equal(old.key_id,'k1');assert.equal(next.key_id,'k2');
 assert.equal(newVersion.openEnvelope({...old,userId:A,sessionId:S}),JWT);
 assert.equal(newVersion.openEnvelope({...next,userId:A,sessionId:S}),JWT);
 const retired=vault('k2',{k2});
 refused(()=>retired.openEnvelope({...old,userId:A,sessionId:S}),
  'CMS_VAULT_KEY_UNAVAILABLE');
 assert.equal(retired.openEnvelope({...next,userId:A,sessionId:S}),JWT);
});
test('reject separated-key violation, malformed JWT, key material and oversized token',()=>{
 refused(()=>vault('k1',{k1},hm,hm),'CMS_VAULT_KEYS_NOT_SEPARATED');
 refused(()=>createSessionVault({hmacKey:Buffer.alloc(6),csrfKey:csrf,
   keys:{k1},activeKeyId:'k1'}),'CMS_VAULT_KEY_INVALID');
 const v=vault();
 refused(()=>v.issueEnvelope({jwt:'abc',userId:A,sessionId:S}),'CMS_VAULT_JWT_INVALID');
 refused(()=>v.issueEnvelope({jwt:'a'.repeat(6001),userId:A,sessionId:S}),
  'CMS_VAULT_JWT_INVALID');
 refused(()=>v.issueEnvelope({jwt:JWT,userId:'NOT_UUID',sessionId:S}),
  'CMS_VAULT_BINDING_INVALID');
});
test('key material never leaks in database envelope and encrypted output is randomized',()=>{
 const v=vault(),first=v.issueEnvelope({jwt:JWT,userId:A,sessionId:S});
 const second=v.issueEnvelope({jwt:JWT,userId:A,sessionId:S});
 assert.notEqual(first.encrypted_jwt,second.encrypted_jwt);
 assert.deepEqual(Object.keys(first).sort(),['encrypted_jwt','key_id']);
 assert.ok(!JSON.stringify(first).includes('SYNTHETIC_ONLY_JWT'));
});
