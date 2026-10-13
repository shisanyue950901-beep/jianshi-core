// F2.1 G2-H.7I — read-only Cloudflare account inventory. No deployment.
// The default CLI does NO network work; only --remote-read-only + explicit
// opt-in and an env-only read-scoped API token can call official GET endpoints.
// Deliberately does NOT inspect bindings/secrets, deploy or authorize release.
const API='https://api.cloudflare.com';
const CLIENT='/client/v4';
const ID=/^[a-f0-9]{32}$/i;
const TARGET='jianshi-cms-auth-admission-locked';
const MAIN_PAGES='jianshi-bua';
function fail(code){const e=new Error(code);e.code=code;throw e;}
function need(v,code){if(!v)fail(code);}
const NAME=/^[a-z0-9][a-z0-9_-]{0,100}$/;
function checkResult(o){
 need(o&&o.success===true&&Array.isArray(o.result)&&
  (!o.errors||Array.isArray(o.errors)&&o.errors.length===0),
  'CMS_H7I_CLOUDFLARE_API_REJECTED');
 need(o.result.length<=1000,'CMS_H7I_RESULT_TOO_LARGE');
 return o;
}
export function planReadOnlyQueries({accountId,zoneId}={}){
 need(typeof accountId==='string'&&ID.test(accountId),
  'CMS_H7I_ACCOUNT_ID_INVALID');
 need(zoneId===undefined||typeof zoneId==='string'&&ID.test(zoneId),
  'CMS_H7I_ZONE_ID_INVALID');
 const q=[
  CLIENT+'/accounts/'+accountId+'/workers/scripts',
  CLIENT+'/accounts/'+accountId+'/pages/projects?page=1&per_page=25'
 ];
 if(zoneId)q.push(CLIENT+'/zones/'+zoneId+'/workers/routes');
 return Object.freeze(q);
}
export async function inspectCloudflareReadOnly({
 accountId,zoneId,token,mode,fetchImpl
}={}){
 need(mode==='EXPLICIT_REMOTE_READONLY','CMS_H7I_REMOTE_NOT_AUTHORIZED');
 need(typeof token==='string'&&token.length>=20&&token.length<=512&&
  !/[\s\r\n]/.test(token),'CMS_H7I_TOKEN_ENV_REQUIRED');
 need(typeof fetchImpl==='function','CMS_H7I_READONLY_FETCH_REQUIRED');
 const paths=planReadOnlyQueries({accountId,zoneId});
 let requests=0;
 const visit=async path=>{
  need(paths.includes(path)||/^\/client\/v4\/accounts\/[a-f0-9]{32}\/pages\/projects\?page=(?:[2-9]|1[0-9]|20)&per_page=25$/i.test(path)&&
   path.includes('/accounts/'+accountId+'/'),'CMS_H7I_ENDPOINT_NOT_ALLOWED');
  requests++;
  need(requests<=22,'CMS_H7I_BUDGET_EXCEEDED');
  let response;
  try{
   response=await fetchImpl(API+path,{
    method:'GET',redirect:'error',cache:'no-store',
    headers:{Authorization:'Bearer '+token,Accept:'application/json'},
    signal:AbortSignal.timeout(9000)
   });
  }catch{fail('CMS_H7I_NETWORK_UNAVAILABLE');}
  need(response?.status===200&&response?.ok===true,
   'CMS_H7I_HTTP_DENIED');
  need(/^application\/json(?:;|$)/i.test(response.headers?.get('content-type')||''),
   'CMS_H7I_INVALID_CONTENT_TYPE');
  let value;
  try{
   const body=await response.text();
   need(body.length>0&&body.length<=262144,'CMS_H7I_RESPONSE_TOO_LARGE');
   value=JSON.parse(body);
  }catch{fail('CMS_H7I_INVALID_JSON');}
  return checkResult(value);
 };
 const workers=await visit(paths[0]);
 // Worker list is a single-page API. If the API advertises more than one page
 // our evidence cannot be called complete; never silently trust partial list.
 need(workers.result_info===undefined||
  Number(workers.result_info?.total_pages)===1,
  'CMS_H7I_WORKERS_COVERAGE_INCOMPLETE');
 const names=workers.result.map(s=>s?.id).filter(n=>NAME.test(n||''));
 need(names.length===workers.result.length,
  'CMS_H7I_WORKER_METADATA_INVALID');
 const workerCount=names.length;
 const exists=names.includes(TARGET);
 const projects=[];
 for(let page=1;page<=20;page++){
  const path=page===1?paths[1]:
   CLIENT+'/accounts/'+accountId+'/pages/projects?page='+page+'&per_page=25';
  const value=await visit(path);
  const result=value.result;
  need(result.every(p=>typeof p?.name==='string'&&NAME.test(p.name)),
   'CMS_H7I_PAGES_METADATA_INVALID');
  projects.push(...result.map(p=>p.name));
  need(projects.length<=500,'CMS_H7I_PAGES_BUDGET_EXCEEDED');
  if(value.result_info?.total_pages!==undefined){
   const total=value.result_info.total_pages;
   need(Number.isInteger(total)&&total>=1&&total<=20,
    'CMS_H7I_PAGES_COVERAGE_INCOMPLETE');
   if(page===total)break;
   need(page<total,'CMS_H7I_PAGES_COVERAGE_INCOMPLETE');
  }else if(result.length<25)break;
  else need(page<20,'CMS_H7I_PAGES_COVERAGE_INCOMPLETE');
 }
 let routeCount=null,attachedToCandidate=null;
 if(zoneId){
  const routes=await visit(paths[2]);
  need(routes.result_info===undefined||
   Number(routes.result_info?.total_pages)===1,
   'CMS_H7I_ROUTES_COVERAGE_INCOMPLETE');
  need(routes.result.every(r=>typeof r?.pattern==='string'&&
   r.pattern.length<=255&&
   (r.script===undefined||typeof r.script==='string')),
   'CMS_H7I_ROUTE_METADATA_INVALID');
  routeCount=routes.result.length;
  attachedToCandidate=routes.result.filter(r=>r.script===TARGET).length;
 }
 const coverage=zoneId?'ACCOUNT_AND_SUPPLIED_ZONE_ONLY':'ACCOUNT_ONLY_ZONE_UNVERIFIED';
 const status=exists||attachedToCandidate?
  'EXISTING_WORKER_OR_ROUTE_REQUIRES_MANUAL_REVIEW':
  'NO_TARGET_SEEN_IN_LIMITED_READONLY_SCOPE';
 return Object.freeze({
  source:'CLOUDFLARE_API_READ_ONLY',
  coverage,
  status,
  candidateWorkerDetected:exists,
  mainPagesProjectDetected:projects.includes(MAIN_PAGES),
  candidatePagesProjectDetected:projects.includes(TARGET),
  workersObserved:workerCount,
  pagesProjectsObserved:projects.length,
  zoneRoutesObserved:routeCount,
  targetRoutesObserved:attachedToCandidate,
  requestsMade:requests,
  cloudflarePreviewDeployedVerified:false,
  identityPermissionScopeVerified:false,
  safeToDeploy:false,
  accountAuthEnabled:false,
  containsCredentials:false
 });
}
// Redacted summary. Never serialize raw API payload, account IDs or tokens.
export function summarizeReadOnlyOutcome(outcome){
 return Object.freeze({
  ...outcome,
  // Explicitly prevent new response properties when changed upstream.
  safeToDeploy:false,accountAuthEnabled:false,containsCredentials:false
 });
}
