// F2.1 G2-H.7J: additional scoped Cloudflare read-only admission evidence.
// NEVER a release authorization. No secrets, scripts, real worker endpoints,
// credentials, DNS names or raw Cloudflare API documents are returned.
// All calls are GET to exact official endpoints and happen ONLY on explicit opt-in.
// Zone discovery uses the supplied token's *visible subset*; it cannot prove
// that an unknown restricted API token is allowed to enumerate all zones.
import {inspectCloudflareReadOnly} from './g2h7i_cloudflare_readonly_client.mjs';

const API='https://api.cloudflare.com';
const P='/client/v4';
const ID=/^[0-9a-f]{32}$/i;
const TARGET='jianshi-cms-auth-admission-locked';
const MAIN='jianshi-bua';
const MAX_ZONES=10;
const MAX_PAGES=20;
const MAX_CALLS=40;
function deny(code){const e=new Error(code);e.code=code;throw e;}
function ensure(ok,code){if(!ok)deny('CMS_H7J_'+code);}
function single(data,label){
 ensure(data&&typeof data==='object'&&!Array.isArray(data)&&
  data.success===true&&Array.isArray(data.result)&&
  (!data.errors||Array.isArray(data.errors)&&data.errors.length===0),
  label+'_API_REJECTED');
 ensure(data.result.length<=1000,label+'_RESULT_LIMIT');
 return data;
}
function pageInfo(value,page,resultLength,label,{allowNoInfo=false}={}){
 const info=value.result_info;
 if(info===undefined){
  ensure(allowNoInfo,label+'_COVERAGE_UNKNOWN');
  return resultLength<50?1:null;
 }
 ensure(info&&Number.isInteger(info.total_pages)&&
  info.total_pages>=0&&info.total_pages<=MAX_PAGES,
  label+'_COVERAGE_UNKNOWN');
 ensure(info.page===undefined||info.page===page,label+'_PAGE_MISMATCH');
 if(Number.isInteger(info.count))
  ensure(info.count===resultLength,label+'_COUNT_MISMATCH');
 if(info.total_pages===0){
  ensure(resultLength===0&&page===1,label+'_EMPTY_INVALID');
  return 0;
 }
 ensure(page<=info.total_pages,label+'_PAGE_OVERFLOW');
 return info.total_pages;
}
function unique(items,label){
 const set=new Set(items);
 ensure(set.size===items.length,label+'_DUPLICATE');
 return set;
}
export async function inspectMultiZoneReadOnly({
 accountId,token,mode,fetchImpl
}={}){
 ensure(mode==='EXPLICIT_REMOTE_READONLY','NOT_AUTHORIZED');
 ensure(typeof accountId==='string'&&ID.test(accountId),'ACCOUNT_INVALID');
 ensure(typeof token==='string'&&token.length>=20&&token.length<=512&&
  !/\s/.test(token),'TOKEN_INVALID');
 ensure(typeof fetchImpl==='function','FETCH_INVALID');
 let used=0;
 async function get(path,{expectObject=false}={}){
  // Strictly-bound paths constructed by local functions only.
  ensure(path.startsWith(P+'/')&&path.length<350&&
   !/[\s#]/.test(path),'PATH_INVALID');
  used++;
  ensure(used<=MAX_CALLS,'BUDGET_EXCEEDED');
  let response;
  try{
   response=await fetchImpl(API+path,{
    method:'GET',redirect:'error',cache:'no-store',
    headers:{Authorization:'Bearer '+token,Accept:'application/json'},
    signal:AbortSignal.timeout(9000)
   });
  }catch{deny('CMS_H7J_NETWORK_UNAVAILABLE');}
  ensure(response?.status===200&&response?.ok===true,'HTTP_DENIED');
  ensure(/^application\/json(?:;|$)/i.test(response.headers?.get('content-type')||''),
   'CONTENT_TYPE_DENIED');
  let data;
  try{
   const raw=await response.text();
   ensure(raw.length>0&&raw.length<=262144,'RESPONSE_LIMIT');
   data=JSON.parse(raw);
  }catch{deny('CMS_H7J_JSON_DENIED');}
  if(expectObject){
   ensure(data&&data.success===true&&data.result&&
    typeof data.result==='object'&&!Array.isArray(data.result)&&
    (!data.errors||Array.isArray(data.errors)&&data.errors.length===0),
    'RESPONSE_OBJECT_API_REJECTED');
   return data;
  }
  return single(data,'RESPONSE');
 }
 // Reuse H7I's existing strict scripts/pages search. No user-provided zone ID.
 const base=await inspectCloudflareReadOnly({
  accountId,token,mode,fetchImpl
 });
 ensure(base.safeToDeploy===false&&base.accountAuthEnabled===false,
  'BASE_GATE_DRIFT');

 // Zones: official account-filtered GET with strict pagination metadata.
 const zones=[];
 for(let page=1;page<=MAX_PAGES;page++){
  const x=await get(P+'/zones?account.id='+accountId+
   '&page='+page+'&per_page=50');
  const total=pageInfo(x,page,x.result.length,'ZONES');
  ensure(x.result.every(z=>typeof z?.id==='string'&&ID.test(z.id)&&
   z.account?.id===accountId),'FOREIGN_ZONE_IN_ACCOUNT_LIST');
  zones.push(...x.result.map(z=>z.id));
  ensure(zones.length<=MAX_ZONES,'ZONE_COUNT_EXCEEDS_SAFE_BUDGET');
  if(page>=total)break;
 }
 unique(zones,'ZONE');

 // If the zone access scope hides resources, a "0 routes" result is limited
 // to the token's visible zones; coverage cannot be upgraded by this script.
 let routeTotal=0,candidateRoutes=0,mainSiteRoutes=0;
 for(const zoneId of zones){
  const x=await get(P+'/zones/'+zoneId+'/workers/routes');
  const total=pageInfo(x,1,x.result.length,'ROUTES',{allowNoInfo:true});
  ensure(total===0||total===1,'ROUTES_COVERAGE_INCOMPLETE');
  ensure(x.result.every(r=>typeof r?.pattern==='string'&&
   r.pattern.length>0&&r.pattern.length<=255&&
   (r.script===undefined||typeof r.script==='string')),
   'ROUTE_METADATA_INVALID');
  routeTotal+=x.result.length;
  candidateRoutes+=x.result.filter(r=>r.script===TARGET).length;
  mainSiteRoutes+=x.result.filter(r=>
   r.pattern.toLowerCase().includes(MAIN)).length;
 }
 const domainData=await get(P+'/accounts/'+accountId+'/workers/domains');
 const domainPages=pageInfo(domainData,1,domainData.result.length,
  'WORKER_DOMAINS',{allowNoInfo:true});
 ensure(domainPages===0||domainPages===1,'WORKER_DOMAINS_INCOMPLETE');
 ensure(domainData.result.every(d=>typeof d?.service==='string'&&
  typeof d?.hostname==='string'&&d.hostname.length<254&&
  typeof d.enabled==='boolean'&&
  (d.previews_enabled===undefined||typeof d.previews_enabled==='boolean')),
  'WORKER_DOMAIN_INVALID');
 const targetDomains=domainData.result.filter(d=>d.service===TARGET);
 const candidateDomainEnabled=targetDomains.some(d=>d.enabled===true);
 const candidateDomainPreviews=targetDomains.some(d=>d.previews_enabled===true);
 let workerSubdomainEnabled=null,workerPreviewUrlsEnabled=null;
 if(base.candidateWorkerDetected){
  const x=await get(P+'/accounts/'+accountId+
   '/workers/scripts/'+TARGET+'/subdomain',{expectObject:true});
  ensure(x?.result&&typeof x.result.enabled==='boolean'&&
   typeof x.result.previews_enabled==='boolean',
   'WORKER_SUBDOMAIN_STATUS_UNKNOWN');
  workerSubdomainEnabled=x.result.enabled;
  workerPreviewUrlsEnabled=x.result.previews_enabled;
 }
 let mainPagesDomains=null,candidatePagesDomains=null;
 for(const name of [MAIN,TARGET]){
  if(name===MAIN&&!base.mainPagesProjectDetected||
   name===TARGET&&!base.candidatePagesProjectDetected)continue;
  const x=await get(P+'/accounts/'+accountId+'/pages/projects/'+
   name+'/domains');
  const total=pageInfo(x,1,x.result.length,
   'PAGES_DOMAINS',{allowNoInfo:true});
  ensure(total===0||total===1,'PAGES_DOMAINS_INCOMPLETE');
  ensure(x.result.every(d=>typeof d?.name==='string'&&
   d.name.length>0&&d.name.length<=253),
   'PAGES_DOMAINS_INVALID');
  if(name===MAIN)mainPagesDomains=x.result.length;
  else candidatePagesDomains=x.result.length;
 }
 const found=base.candidateWorkerDetected||
  base.candidatePagesProjectDetected||
  candidateRoutes>0||targetDomains.length>0;
 // No status can ever mean 'ready'. A negative is always scoped to token's
 // visibility, not all Cloudflare accounts nor control-plane configurations.
 return Object.freeze({
  source:'CLOUDFLARE_READONLY_TOKEN_VISIBLE',
  status:found?'CANDIDATE_ASSET_REQUIRES_MANUAL_REVIEW':
   'NO_CANDIDATE_SEEN_WITH_TOKEN_VISIBLE_SCOPE',
  workerSeen:base.candidateWorkerDetected,
  pagesCandidateSeen:base.candidatePagesProjectDetected,
  mainPagesSeen:base.mainPagesProjectDetected,
  zoneScope:'TOKEN_VISIBLE_ACCOUNT_ZONES_ONLY',
  accountPermissionScopeProven:false,
  totalAccessibleZones:zones.length,
  workerRoutesObserved:routeTotal,
  mainSitePatternRoutesObserved:mainSiteRoutes,
  candidateRoutesObserved:candidateRoutes,
  candidateCustomDomainsObserved:targetDomains.length,
  candidateCustomDomainEnabled:candidateDomainEnabled,
  candidateCustomDomainPreviewsEnabled:candidateDomainPreviews,
  candidateWorkerSubdomainEnabled:workerSubdomainEnabled,
  candidateWorkerPreviewUrlsEnabled:workerPreviewUrlsEnabled,
  mainPagesCustomDomainsObserved:mainPagesDomains,
  candidatePagesCustomDomainsObserved:candidatePagesDomains,
  requestsMade:used+base.requestsMade,
  remoteDeploymentPerformed:false,
  stagingAuthEnabled:false,
  productionAuthEnabled:false,
  safeToDeploy:false,
  credentialsIncluded:false
 });
}
