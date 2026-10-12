import test from 'node:test';
import assert from 'node:assert/strict';
import {createStagingAuthAdapter,stagingOrigin} from '../scripts/qa/g2h2_trusted_auth_adapter.mjs';

const U='00000000-0000-4000-8000-00000000a001';
const SESSION='00000000-0000-4000-8000-00000000a002';
const serviceKey='synthetic_service_role_key_very_long_not_a_secret';
const anonKey='synthetic_publishable_very_long_not_a_secret';
const now=()=>1791800000000;
function token(fields={}){
 const claims={sub:U,role:'authenticated',aud:'authenticated',
   iss:stagingOrigin+'/auth/v1',session_id:SESSION,exp:1791803600,...fields};
 return 'eyJhbGciOiJIUzI1NiJ9.'+Buffer.from(JSON.stringify(claims)).toString('base64url')+
   '.SYNTHETIC_FAKE_SIGNATURE_NOT_A_REAL_TOKEN';
}
function fake(overrides={}){
 const trace=[];
 async function mock(url,options){
  const u=new URL(url);trace.push({path:u.pathname,query:u.search,method:options.method,
    hasSecretHeader:options.headers.apikey===serviceKey,
    hasBearer:!!options.headers.authorization,redirect:options.redirect});
  let v;
  if(u.pathname==='/rest/v1/product_feature_flags')
   v=overrides.flags??[{feature_key:'account_auth',enabled:true},{feature_key:'cms_editor',enabled:true}];
  else if(u.pathname==='/rest/v1/rpc/auth_launch_ready_v01')v=overrides.ready??true;
  else if(u.pathname==='/auth/v1/user')
   v=overrides.user??{id:U,email_confirmed_at:'2026-10-12T00:00:00Z'};
  else if(u.pathname==='/rest/v1/rpc/cms_internal_session_v01')v=overrides.session??true;
  else if(u.pathname==='/rest/v1/rpc/cms_internal_actor_role_v01')v=overrides.role??'EDITOR';
  else throw Error('unexpected network route');
  if(overrides.transport==='reject')throw Error('synthetic transport unavailable');
  return {ok:overrides.httpError!==true,json:async()=>v};
 }
 const adapter=createStagingAuthAdapter({url:stagingOrigin,anonKey,serviceKey,fetchImpl:mock,now});
 return {adapter,trace};
}
async function denied(adapter,jwt,expected){
 await assert.rejects(adapter.verify(jwt),e=>e.code===expected);
}
test('server obtains verified user and live session+role from pinned upstream',async()=>{
 const {adapter,trace}=fake();
 assert.deepEqual(await adapter.verify(token()),{userId:U,sessionId:SESSION,role:'EDITOR'});
 assert.deepEqual(trace.map(x=>x.path),[
  '/rest/v1/product_feature_flags','/rest/v1/rpc/auth_launch_ready_v01',
  '/auth/v1/user','/rest/v1/rpc/cms_internal_session_v01',
  '/rest/v1/rpc/cms_internal_actor_role_v01'
 ]);
 assert.ok(trace.every(x=>x.redirect==='error'));
 assert.ok(trace.filter(x=>x.path.startsWith('/rest/')).every(x=>x.hasSecretHeader));
 assert.equal(trace.find(x=>x.path==='/auth/v1/user').hasSecretHeader,false);
});
test('flags fail closed BEFORE any JWT account lookup or role lookup',async()=>{
 const f=fake({flags:[{feature_key:'cms_editor',enabled:false},{feature_key:'account_auth',enabled:true}]});
 await denied(f.adapter,token(),'CMS_WRITE_DISABLED');
 assert.deepEqual(f.trace.map(x=>x.path),['/rest/v1/product_feature_flags']);
 const r=fake({ready:false});await denied(r.adapter,token(),'CMS_AUTH_NOT_READY');
 assert.ok(!r.trace.some(x=>x.path==='/auth/v1/user'));
});
test('JWT claims cannot impersonate GoTrue user, session, origin, role or expiry',async()=>{
 for(const [field,value] of [
  ['sub','00000000-0000-4000-8000-00000000b001'],
  ['session_id','00000000-0000-4000-8000-00000000b001'],
  ['iss','https://evil.invalid/auth/v1'],['aud','anon'],
  ['role','service_role'],['exp',1791799999],['is_anonymous',true]
 ]){
  const f=fake(); const modified=field==='session_id'?{[field]:value}: {[field]:value};
  if(field==='session_id'){
   // A well-formed fake session identifier is not proof the session is active;
   // a *different* UUID gets checked against the live auth.sessions RPC.
   assert.equal((await f.adapter.verify(token(modified))).sessionId,value);
   assert.ok(f.trace.some(x=>x.path.endsWith('/cms_internal_session_v01')));
  }else await denied(f.adapter,token(modified),'CMS_TOKEN_CLAIMS');
 }
});
test('revoked auth session, unconfirmed user, revoked role, invalid role all denied',async()=>{
 for(const [opts,code] of [
  [{session:false},'CMS_SESSION_REVOKED'],
  [{user:{id:U,email_confirmed_at:null}},'CMS_GOTRUE_USER_REJECTED'],
  [{user:{id:'00000000-0000-4000-8000-00000000b001',email_confirmed_at:'yes'}},'CMS_TOKEN_CLAIMS'],
  [{role:null},'CMS_ROLE_FORBIDDEN'],
  [{role:'OWNER'},'CMS_ROLE_FORBIDDEN'],
 ]){const f=fake(opts);await denied(f.adapter,token(),code);}
});
test('invalid transport, failure responses, token format and wrong origin fail closed',async()=>{
 assert.throws(()=>createStagingAuthAdapter({
  url:'https://dalfvgehosxfyxkptxwx.supabase.co',anonKey,serviceKey
 }),e=>e.code==='CMS_STAGING_ORIGIN_PIN');
 for(const [opts,code] of [
  [{transport:'reject'},'CMS_UPSTREAM_UNAVAILABLE'],
  [{httpError:true},'CMS_UPSTREAM_DENIED']
 ]){const f=fake(opts);await denied(f.adapter,token(),code);}
 const f=fake();await denied(f.adapter,'malformed.jwt','CMS_TOKEN_INVALID');
});
test('adapter has no HTTP listener, token logging or public role setter',async()=>{
 const source=await import('node:fs/promises').then(f=>f.readFile(
  new URL('../scripts/qa/g2h2_trusted_auth_adapter.mjs',import.meta.url),'utf8'));
 for(const banned of ['console.log','listen(', 'createServer(', 'localStorage',
   'fetch("https://', 'https://dalfvgehosxfyxkptxwx', 'password=','SET ROLE']){
  assert.ok(!source.includes(banned),'unexpected '+banned);
 }
 assert.match(source,/cms_internal_session_v01/);
 assert.match(source,/cms_internal_actor_role_v01/);
});
