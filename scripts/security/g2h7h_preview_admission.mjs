// F2.1 G2-H.7H: independently executable NON-DEPLOYED admission safety audit.
// A green result means "safe because remote deployment remains BLOCKED",
// not approval to authenticate, provision credentials, or deploy to Cloudflare.
import assert from 'node:assert/strict';
import {readFileSync,existsSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const read=path=>readFileSync(resolve(root,path),'utf8');

export const EXPECTED_WORKER='jianshi-cms-auth-admission-locked';
const EXPECTED_VARS={
 JIANSHI_AUTH_ENABLED:'0',
 JIANSHI_PREVIEW_ADMISSION:'DENY_ALL'
};
const GATES=[
 'real_cloudflare_deployment',
 'dedicated_worker_account_authorized',
 'separate_worker_identity_verified',
 'cloudflare_mtls_certificate_bound',
 'verified_unproxied_mtls_origin',
 'isolated_secret_store_reviewed',
 'verified_go_true_email_template',
 'real_staging_login_ab_idor_pass',
 'independent_human_security_review',
 'explicit_future_remote_deploy_approval',
 'production_auth_activation',
 'production_schema_mutation'
];
function keys(o){return o&&typeof o==='object'&&!Array.isArray(o)?
 Object.keys(o).sort():[];}
function sameKeys(a,b){return JSON.stringify(keys(a))===JSON.stringify(b.slice().sort());}
const CONFIG_KEYS=['name','main','compatibility_date','workers_dev','preview_urls',
 'routes','mtls_certificates','vars'];
const MANIFEST_KEYS=['version','stage','scope','gate',...GATES,'readiness_evidence_links'];
export function assessPreviewSafety({config,manifest,workerSource,releaseSource,
 publishSource, bffSource}={}){
 const problems=[];
 const reject=msg=>problems.push(msg);
 if(!sameKeys(config,CONFIG_KEYS))reject('WRANGLER_UNKNOWN_OR_MISSING_CONFIGURATION');
 if(config?.name!==EXPECTED_WORKER||
  config?.main!=='./locked-worker.mjs'||
  config?.workers_dev!==false||
  config?.preview_urls!==false||
  !Array.isArray(config?.routes)||config.routes.length!==0||
  !Array.isArray(config?.mtls_certificates)||config.mtls_certificates.length!==0||
  config?.compatibility_date!=='2026-10-13'||
  !sameKeys(config?.vars,Object.keys(EXPECTED_VARS))||
  Object.keys(EXPECTED_VARS).some(k=>config?.vars?.[k]!==EXPECTED_VARS[k]))
  reject('UNSAFE_CLOUDFLARE_ROUTE_OR_BINDING');
 if(!sameKeys(manifest,MANIFEST_KEYS)||manifest?.version!==1||
  manifest?.stage!=='G2-H.7H'||
  manifest?.scope!=='ISOLATED_DENY_ALL_NON_DEPLOYED'||
  manifest?.gate!=='BLOCKED_BY_DEFAULT'||
  !Array.isArray(manifest?.readiness_evidence_links)||
  manifest.readiness_evidence_links.length!==0||
  GATES.some(g=>manifest?.[g]!==false))
  reject('PREVIEW_RELEASE_NOT_AUTHORIZED');
 if(typeof workerSource!=='string'||
  !/async fetch\s*\(/.test(workerSource)||
  !/new Response\('Not Found',\{status:404,headers:HEADERS\}\)/.test(workerSource)||
  /\b(?:import|require|eval|Function)\s*(?:\(|.*from\b)/.test(workerSource)||
  /\b(?:fetch|console|Math\.random|WebSocket|EventSource)\s*\(/.test(
   workerSource.replace(/async fetch\s*\(/,'async handler('))||
  /\bprocess\.env\b/.test(workerSource)||
  /(?:authorization|token_hash|service_role|supabase|pages\.dev)/i.test(
   workerSource.replace(/token_hash/g,'MOCK_ONLY'))){
  reject('WORKER_IS_NOT_UNCONDITIONAL_DENY_ONLY');
 }
 if(typeof publishSource!=='string'||
  !publishSource.includes("cron: '55 0 * * *'")||
  !publishSource.includes("cron: '55 6,12,18 * * *'")||
  !publishSource.includes('JIANSHI_AUTH_ENABLED: "0"')||
  !publishSource.includes("github.event_name == 'schedule'")||
  /ops\/cms-preview|g2h7h|deploy-admission/.test(publishSource))
  reject('PUBLIC_STATIC_PUBLISH_DRIFT');
 if(typeof releaseSource!=='string'||
  /ops\/cms-preview|g2h7h|deploy-admission/.test(releaseSource))
  reject('RELEASE_ARTIFACT_CONTAMINATION');
 if(typeof bffSource!=='string'||
  !bffSource.includes("tests/g2h7h_preview_admission.test.mjs")||
  !bffSource.includes("scripts/security/g2h7h_preview_admission.mjs"))
  reject('ISOLATED_CI_GATE_NOT_WIRED');
 return Object.freeze({
  safeBlocked:problems.length===0,
  remoteDeploymentAuthorized:false,
  authEnabled:false,
  reviewedGates:GATES.length,
  problems
 });
}
export function auditRepository(){
 const paths=[
  'functions','web/functions','public/functions','web/dist/functions',
  'web/dist/_worker.js','web/dist/_routes.json',
  'dist/_worker.js','dist/_routes.json','public/_worker.js',
  'public/_routes.json'
 ];
 const unsafe=paths.filter(p=>existsSync(resolve(root,p)));
 // Candidate tree can contain only source JSON/JS and README. No private keys,
 // Wrangler .dev.vars, or vendor-specific environment secrets may be committed.
 const candidateDir=resolve(root,'ops/cms-preview/cloudflare');
 for(const f of readdirSync(candidateDir)){
  if(/\.(pem|key|p12|pfx|crt|csr|env)$/i.test(f)||
   /^\.dev\.vars/.test(f)||/\.secret/i.test(f))unsafe.push('CREDENTIAL_FILE:'+f);
 }
 const p=assessPreviewSafety({
  config:JSON.parse(read('ops/cms-preview/cloudflare/wrangler.json')),
  manifest:JSON.parse(read('ops/cms-preview/cloudflare/deploy-admission.json')),
  workerSource:read('ops/cms-preview/cloudflare/locked-worker.mjs'),
  releaseSource:read('scripts/release/p412_build_public.py'),
  publishSource:read('.github/workflows/publish-static.yml'),
  bffSource:read('.github/workflows/cms-bff-isolated.yml')
 });
 assert.equal(unsafe.length,0,'G2H7H_SHIPPING_AUDIT_UNSAFE '+unsafe.join(','));
 assert.equal(p.safeBlocked,true,
  'G2H7H_PREVIEW_ADMISSION_REJECTED '+p.problems.join(','));
 assert.equal(p.remoteDeploymentAuthorized,false);
 assert.equal(p.authEnabled,false);
 console.log('G2H7H_CLOUDFLARE_PREVIEW_BLOCKED_SAFE_PASS '+JSON.stringify({
  workerConfig:'deny_only_non_deployed',workersDev:false,previewUrls:false,
  attachedRoutes:0,mTlsCertificatesInRepo:0,
  launchReadinessGates:p.reviewedGates,independentHumanReview:false,
  publicShippingRiskDetected:false,productionAuthEnabled:false,
  remoteDeploymentAuthorized:false
 }));
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))
 auditRepository();
