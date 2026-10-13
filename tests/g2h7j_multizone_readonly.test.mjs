import test from 'node:test';
import assert from 'node:assert/strict';
import {inspectMultiZoneReadOnly}
 from '../scripts/security/g2h7j_multizone_readonly.mjs';

const A='a'.repeat(32),Z1='1'.repeat(32),Z2='2'.repeat(32);
const TOKEN='SYNTHETIC_READONLY_TOKEN_FOR_G2H7J';
const TARGET='jianshi-cms-auth-admission-locked';
const ZINFO={page:1,count:2,total_pages:1,total_count:2};
const envelope=(result,info)=>new Response(JSON.stringify({
 success:true,errors:[],result,...(info===undefined?{}:{result_info:info})
}),{status:200,headers:{'content-type':'application/json'}});
function fixture({
 workers=[{id:'unrelated-worker'}],pages=[{name:'jianshi-bua'}],
 zones=[{id:Z1,account:{id:A}},{id:Z2,account:{id:A}}],
 routes={},domains=[],subdomain={enabled:false,previews_enabled:false},
 pagesDomains={},zoneInfo,override
}={}){
 const seen=[];
 const fetchImpl=async (url,opts)=>{
  seen.push({url,opts});
  const u=new URL(url),p=u.pathname;
  if(override){
   const result=override({url,path:p,query:u.searchParams,seen});
   if(result!==undefined)return result;
  }
  if(p.endsWith('/workers/scripts'))return envelope(workers,{total_pages:1});
  if(p.endsWith('/pages/projects')){
   return envelope(pages,{page:1,count:pages.length,total_pages:1,
    total_count:pages.length});
  }
  if(p==='/client/v4/zones')return envelope(zones,
   zoneInfo??{page:1,count:zones.length,total_pages:1,total_count:zones.length});
  if(p.endsWith('/workers/routes')){
   const zone=p.match(/zones\/([0-9a-f]{32})\/workers\/routes$/)?.[1];
   return envelope(routes[zone]??[]);
  }
  if(p.endsWith('/workers/domains'))return envelope(domains);
  if(p.endsWith('/scripts/'+TARGET+'/subdomain'))return new Response(
   JSON.stringify({success:true,errors:[],result:subdomain}),
   {status:200,headers:{'content-type':'application/json'}});
  if(p.endsWith('/domains')&&p.includes('/pages/projects/')){
   const name=p.split('/projects/')[1].split('/domains')[0];
   return envelope(pagesDomains[name]??[]);
  }
  throw Error('UNLISTED_API_PATH');
 };
 return {fetchImpl,seen};
}
function inspect(f,overrides={}){
 return inspectMultiZoneReadOnly({accountId:A,token:TOKEN,
  mode:'EXPLICIT_REMOTE_READONLY',fetchImpl:f.fetchImpl,...overrides});
}
test('account-wide token-visible multi-zone inventory, strict GET-only and bounded data',async()=>{
 const f=fixture({routes:{
  [Z1]:[{pattern:'app.example.invalid/*',script:'other'}],
  [Z2]:[{pattern:'jianshi-bua.example.invalid/*',script:'another'}]
 },pagesDomains:{'jianshi-bua':[{name:'www.example.invalid'}]}});
 const result=await inspect(f);
 assert.equal(result.status,'NO_CANDIDATE_SEEN_WITH_TOKEN_VISIBLE_SCOPE');
 assert.equal(result.zoneScope,'TOKEN_VISIBLE_ACCOUNT_ZONES_ONLY');
 assert.equal(result.accountPermissionScopeProven,false);
 assert.equal(result.totalAccessibleZones,2);
 assert.equal(result.workerRoutesObserved,2);
 assert.equal(result.mainSitePatternRoutesObserved,1);
 assert.equal(result.mainPagesCustomDomainsObserved,1);
 assert.equal(result.safeToDeploy,false);
 assert.equal(result.requestsMade,7);
 const endpoints=f.seen.map(x=>x.url);
 assert.ok(endpoints.some(x=>x.includes('/zones?account.id='+A)));
 assert.ok(endpoints.some(x=>x.endsWith('/workers/domains')));
 for(const {url,opts} of f.seen){
  assert.equal(opts.method,'GET');
  assert.equal(opts.redirect,'error');
  assert.equal(opts.cache,'no-store');
  assert.equal(opts.body,undefined);
  assert.equal(opts.headers.Authorization,'Bearer '+TOKEN);
  assert.ok(url.startsWith('https://api.cloudflare.com/client/v4/'));
 }
 const text=JSON.stringify(result);
 assert.ok(!text.includes(A));
 assert.ok(!text.includes(Z1));
 assert.ok(!text.includes('example.invalid'));
 assert.ok(!text.includes(TOKEN));
});
test('candidate Worker probes workers.dev and version-preview status, always rejects deployment',async()=>{
 const f=fixture({workers:[{id:TARGET}],routes:{
  [Z1]:[{pattern:'preview.example.invalid/*',script:TARGET}]
 },domains:[{hostname:'preview.example.invalid',service:TARGET,enabled:true,
  previews_enabled:true}],
 subdomain:{enabled:true,previews_enabled:true},
 pages:[{name:'jianshi-bua'},{name:TARGET}],
 pagesDomains:{'jianshi-bua':[] ,[TARGET]:[{name:'edge.example.invalid'}]}
 });
 const r=await inspect(f);
 assert.equal(r.status,'CANDIDATE_ASSET_REQUIRES_MANUAL_REVIEW');
 assert.equal(r.candidateRoutesObserved,1);
 assert.equal(r.candidateCustomDomainsObserved,1);
 assert.equal(r.candidateCustomDomainEnabled,true);
 assert.equal(r.candidateCustomDomainPreviewsEnabled,true);
 assert.equal(r.candidateWorkerSubdomainEnabled,true);
 assert.equal(r.candidateWorkerPreviewUrlsEnabled,true);
 assert.equal(r.candidatePagesCustomDomainsObserved,1);
 assert.equal(r.safeToDeploy,false);
 assert.ok(f.seen.some(x=>x.url.includes('/scripts/'+TARGET+'/subdomain')));
});
test('Worker domain alone is a collision, even with no candidate script in list',async()=>{
 const f=fixture({domains:[{hostname:'other.example.invalid',
  service:TARGET,enabled:false,previews_enabled:true}]});
 const r=await inspect(f);
 assert.equal(r.status,'CANDIDATE_ASSET_REQUIRES_MANUAL_REVIEW');
 assert.equal(r.candidateCustomDomainsObserved,1);
 assert.equal(r.candidateWorkerSubdomainEnabled,null);
});
test('zones with account ID mismatch rejected, not counted as verified inventory',async()=>{
 const f=fixture({zones:[{id:Z1,account:{id:'b'.repeat(32)}}]});
 await assert.rejects(inspect(f),e=>e.code==='CMS_H7J_FOREIGN_ZONE_IN_ACCOUNT_LIST');
});
test('a token with no Zones Read cannot assert no routes',async()=>{
 const f=fixture({override:({path})=>path==='/client/v4/zones'?
  new Response(JSON.stringify({success:false,errors:[{code:403}],result:[]}),
   {status:403,headers:{'content-type':'application/json'}}):undefined});
 await assert.rejects(inspect(f),e=>e.code==='CMS_H7J_HTTP_DENIED');
});
test('no pagination metadata fails shut rather than claiming all zones',async()=>{
 const f=fixture({override:({path})=>path==='/client/v4/zones'?
  envelope([{id:Z1,account:{id:A}}]):undefined});
 await assert.rejects(inspect(f),e=>e.code==='CMS_H7J_ZONES_COVERAGE_UNKNOWN');
});
test('insufficient zone budget fails shut; no route scan beyond ten zones',async()=>{
 const zones=Array.from({length:11},(_,i)=>({
  id:i.toString(16).padStart(32,'0'),account:{id:A}
 }));
 const f=fixture({zones});
 await assert.rejects(inspect(f),e=>e.code==='CMS_H7J_ZONE_COUNT_EXCEEDS_SAFE_BUDGET');
 assert.equal(f.seen.filter(x=>x.url.endsWith('/workers/routes')).length,0);
});
test('incomplete Worker domain metadata fails shut',async()=>{
 const f=fixture({override:({path})=>path.endsWith('/workers/domains')?
  envelope([{hostname:'fake.invalid',service:TARGET,enabled:true}],
   {page:1,count:1,total_pages:2,total_count:2}):undefined});
 await assert.rejects(inspect(f),e=>e.code==='CMS_H7J_WORKER_DOMAINS_INCOMPLETE');
});
test('bad page count, duplicate zones or wrong route metadata block proof',async()=>{
 const one=fixture({zoneInfo:{page:1,count:999,total_pages:1}});
 await assert.rejects(inspect(one),e=>e.code==='CMS_H7J_ZONES_COUNT_MISMATCH');
 const two=fixture({zones:[{id:Z1,account:{id:A}},{id:Z1,account:{id:A}}]});
 await assert.rejects(inspect(two),e=>e.code==='CMS_H7J_ZONE_DUPLICATE');
 const three=fixture({routes:{[Z1]:[{script:TARGET,pattern:null}]}});
 await assert.rejects(inspect(three),e=>e.code==='CMS_H7J_ROUTE_METADATA_INVALID');
});
test('Worker exposed subdomain response cannot be malformed or silently missing',async()=>{
 const f=fixture({workers:[{id:TARGET}],
  override:({path})=>path.endsWith('/scripts/'+TARGET+'/subdomain')?
    envelope({enabled:true}):undefined});
 await assert.rejects(inspect(f),e=>e.code==='CMS_H7J_WORKER_SUBDOMAIN_STATUS_UNKNOWN');
});
test('failed transport does not echo raw API errors, credentials, account ID or URL',async()=>{
 const f=fixture({override:({path})=>path==='/client/v4/zones'?
  Promise.reject(Error('SYNTHETIC_RAW_TOKEN_SHOULD_NEVER_LEAK')):undefined});
 await assert.rejects(inspect(f),e=>e.code==='CMS_H7J_NETWORK_UNAVAILABLE'&&
  !e.message.includes('RAW_TOKEN'));
});
test('caller cannot use wrong read mode, malformed account or missing token',async()=>{
 const f=fixture(),bad=[
  {mode:'LIVE_WRITE'},
  {accountId:'not-an-account'},
  {token:'x'},
  {fetchImpl:null}
 ];
 for(const v of bad)await assert.rejects(inspect(f,v),e=>
  e.code?.startsWith('CMS_H7J_'));
 assert.equal(f.seen.length,0);
});
