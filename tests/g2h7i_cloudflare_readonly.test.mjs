import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync,spawnSync} from 'node:child_process';
import {planReadOnlyQueries,inspectCloudflareReadOnly}
 from '../scripts/security/g2h7i_cloudflare_readonly_client.mjs';
const account='a'.repeat(32),zone='b'.repeat(32);
const token='SYNTHETIC_LOCAL_READONLY_0123456789';
const candidate='jianshi-cms-auth-admission-locked';
function reply(result,info={total_pages:1}){
 return new Response(JSON.stringify({success:true,errors:[],result,result_info:info}),
  {status:200,headers:{'content-type':'application/json'}});
}
function fixture({scripts=[{id:'some-public-worker'}],
 pages=[{name:'jianshi-bua'}],routes=[],morePages=false,
 altered=null}={}){
 const seen=[];
 const fetchImpl=async (url,init)=>{
  seen.push({url,init});
  if(altered)return altered;
  if(url.includes('/workers/scripts'))return reply(scripts);
  if(url.includes('/pages/projects')){
   if(morePages){
    return url.includes('page=1')?reply(
     Array.from({length:25},(_,i)=>({name:'page-'+i})),{total_pages:2}):
     reply(pages,{total_pages:2});
   }
   return reply(pages);
  }
  if(url.includes('/workers/routes'))return reply(routes);
  throw Error('UNLISTED_API');
 };
 return {seen,fetchImpl};
}
const inspect=(f,withZone=true)=>inspectCloudflareReadOnly({
 accountId:account,zoneId:withZone?zone:undefined,
 token,mode:'EXPLICIT_REMOTE_READONLY',fetchImpl:f.fetchImpl
});
test('default CLI makes no remote call',()=>{
 const x=execFileSync(process.execPath,[
  'scripts/security/g2h7i_cloudflare_readonly_cli.mjs'
 ],{encoding:'utf8',env:{PATH:process.env.PATH}});
 assert.match(x,/G2H7I_REMOTE_INVENTORY_NOT_CONNECTED/);
 assert.match(x,/"safeToDeploy":false/);
});
test('CLI refuses remote access without explicit runtime permission',()=>{
 const x=spawnSync(process.execPath,[
  'scripts/security/g2h7i_cloudflare_readonly_cli.mjs','--remote-read-only'
 ],{encoding:'utf8',env:{PATH:process.env.PATH}});
 assert.equal(x.status,2);
 assert.match(x.stderr,/G2H7I_REMOTE_READONLY_DENIED/);
});
test('strictly three official GET paths with no request body',async()=>{
 const f=fixture(),r=await inspect(f);
 const expected=planReadOnlyQueries({accountId:account,zoneId:zone});
 assert.deepEqual(f.seen.map(x=>x.url),expected.map(p=>
  'https://api.cloudflare.com'+p));
 for(const x of f.seen){
  assert.equal(x.init.method,'GET');
  assert.equal(x.init.redirect,'error');
  assert.equal(x.init.body,undefined);
 }
 assert.equal(r.workersObserved,1);
 assert.equal(r.pagesProjectsObserved,1);
 assert.equal(r.mainPagesProjectDetected,true);
 assert.equal(r.status,'NO_TARGET_SEEN_IN_LIMITED_READONLY_SCOPE');
 assert.equal(r.safeToDeploy,false);
 assert.equal(JSON.stringify(r).includes(account),false);
 assert.equal(JSON.stringify(r).includes(token),false);
});
test('candidate present or matching route cannot authorize any deploy',async()=>{
 const f=fixture({scripts:[{id:candidate}],routes:[
  {pattern:'www.example.invalid/*',script:candidate}
 ]});
 const r=await inspect(f);
 assert.equal(r.candidateWorkerDetected,true);
 assert.equal(r.targetRoutesObserved,1);
 assert.equal(r.status,'EXISTING_WORKER_OR_ROUTE_REQUIRES_MANUAL_REVIEW');
 assert.equal(r.safeToDeploy,false);
});
test('zone omitted means routes unverified, never implicitly empty',async()=>{
 const f=fixture(),r=await inspect(f,false);
 assert.equal(f.seen.length,2);
 assert.equal(r.coverage,'ACCOUNT_ONLY_ZONE_UNVERIFIED');
 assert.equal(r.zoneRoutesObserved,null);
 assert.equal(r.safeToDeploy,false);
});
test('Pages pagination loads subsequent read-only pages',async()=>{
 const f=fixture({morePages:true}),r=await inspect(f);
 assert.equal(r.pagesProjectsObserved,26);
 assert.equal(f.seen.filter(x=>x.url.includes('/pages/projects')).length,2);
});
test('invalid API payload and stale scopes fail closed',async()=>{
 for(const altered of [
  new Response('{}',{status:403,headers:{'content-type':'application/json'}}),
  new Response('<html>error</html>',{status:200,
   headers:{'content-type':'text/html'}}),
  new Response('broken',{status:200,
   headers:{'content-type':'application/json'}}),
  new Response(JSON.stringify({success:false,result:[],errors:[]}),{
   status:200,headers:{'content-type':'application/json'}})
 ]){
  await assert.rejects(inspect(fixture({altered})),
   e=>String(e.code).startsWith('CMS_H7I_'));
 }
});
test('incomplete Worker inventory and invalid account identity are denied',async()=>{
 const f=fixture({altered:reply([], {total_pages:2})});
 await assert.rejects(inspect(f),
  e=>e.code==='CMS_H7I_WORKERS_COVERAGE_INCOMPLETE');
 await assert.rejects(inspectCloudflareReadOnly({
  accountId:'not-an-account',zoneId:zone,token,
  mode:'EXPLICIT_REMOTE_READONLY',fetchImpl:f.fetchImpl
 }),e=>e.code==='CMS_H7I_ACCOUNT_ID_INVALID');
});
