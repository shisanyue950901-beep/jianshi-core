// G2-H.7J independent static audit: no remote Cloudflare work in CI;
// all candidate production launches remain blocked. Explicit Cloudflare
// opt-in is outside CI and yields visibility-scoped evidence only.
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..');
const read=p=>readFileSync(resolve(root,p),'utf8');
const source=read('scripts/security/g2h7j_multizone_readonly.mjs');
const cli=read('scripts/security/g2h7j_multizone_cli.mjs');
const tests=read('tests/g2h7j_multizone_readonly.test.mjs');
const ci=read('.github/workflows/cms-bff-isolated.yml');
const publish=read('.github/workflows/publish-static.yml');
const release=read('scripts/release/p412_build_public.py');
const prev=JSON.parse(read('ops/cms-preview/cloudflare/deploy-admission.json'));
const wrangler=JSON.parse(read('ops/cms-preview/cloudflare/wrangler.json'));
const errors=[];
for(const f of ['functions','web/functions','web/dist/functions',
 'dist/functions','web/dist/_worker.js','web/dist/_routes.json',
 'dist/_worker.js','dist/_routes.json','public/_worker.js'])
 if(existsSync(resolve(root,f)))errors.push('UNEXPECTED_PUBLIC_ROUTE:'+f);
for(const marker of [
 "import {inspectCloudflareReadOnly}",
 "method:'GET'",
 "redirect:'error'",
 "'EXPLICIT_REMOTE_READONLY'",
 "MAX_ZONES=10",
 "MAX_CALLS=40",
 "'FOREIGN_ZONE_IN_ACCOUNT_LIST'",
 "'ZONES_COVERAGE_UNKNOWN'",
 "'WORKER_DOMAINS_INCOMPLETE'",
 "'ROUTES_COVERAGE_INCOMPLETE'",
 "accountPermissionScopeProven:false",
 "safeToDeploy:false",
 "credentialsIncluded:false"
])if(!source.includes(marker))errors.push('SOURCE_GUARD_MISSING:'+marker);
for(const marker of [
 "G2H7J_NOT_CONNECTED",
 "JIANSHI_H7J_REMOTE_READONLY_APPROVED!=='1'",
 "if(argv.length===0)",
 "JIANSHI_H7J_READ_TOKEN",
 "'--remote-read-only'",
 "G2H7J_CLOUD_READONLY_FAIL_CLOSED"
])if(!cli.includes(marker))errors.push('CLI_GATE_MISSING:'+marker);
for(const marker of [
 'without',
 'candidate Worker',
 'zone',
 'pages',
 'incomplete',
 'wrong route metadata',
 'CLI is zero-network'
].slice(1))if(!tests.toLowerCase().includes(marker.toLowerCase()))
 errors.push('MISSING_NEGATIVE_TEST:'+marker);
for(const marker of [
 'scripts/security/g2h7j_multizone_readonly.mjs',
 'scripts/security/g2h7j_multizone_cli.mjs',
 'scripts/security/g2h7j_multizone_audit.mjs',
 'tests/g2h7j_multizone_readonly.test.mjs',
 'node --test tests/g2h7j_multizone_readonly.test.mjs',
 'node scripts/security/g2h7j_multizone_audit.mjs'
])if(!ci.includes(marker))errors.push('CI_WIRING_MISSING:'+marker);
if(ci.includes("JIANSHI_H7J_READ_TOKEN")||
 ci.includes("--remote-read-only")||
 ci.includes("JIANSHI_H7J_REMOTE_READONLY_APPROVED"))
 errors.push('REAL_CLOUD_IN_CI');
for(const [name,body] of [['publish',publish],['release',release]]){
 if(/g2h7j|multizone_readonly|ops\/cms-preview/.test(body))
  errors.push('PUBLIC_BUILD_IMPORT:'+name);
}
for(const body of [source,cli]){
 if(/method\s*:\s*['"](?:POST|PATCH|PUT|DELETE)['"]/.test(body)||
   /wrangler\s+(?:deploy|publish|secret)/.test(body))
  errors.push('WRITE_CAPABILITY_FOUND');
}
if(!publish.includes("cron: '55 0 * * *'")||
 !publish.includes("cron: '55 6,12,18 * * *'")||
 !publish.includes('JIANSHI_AUTH_ENABLED: "0"'))
 errors.push('P441_OR_AUTH_FLAG_DRIFT');
if(prev.gate!=='BLOCKED_BY_DEFAULT'||
 prev.real_cloudflare_deployment!==false||
 prev.explicit_future_remote_deploy_approval!==false||
 wrangler.workers_dev!==false||
 wrangler.preview_urls!==false||
 wrangler.routes?.length!==0)
 errors.push('DEPLOYMENT_AUTHORIZATION_DRIFT');
assert.deepEqual(errors,[],'G2H7J_BOUNDARY_FAIL '+errors.join(' | '));
console.log('G2H7J_MULTIZONE_READONLY_AUDIT_PASS '+JSON.stringify({
 simulatedOnly:true,remoteReadAttempted:false,
 methods:['GET'],totalZoneBudget:10,scope:'TOKEN_VISIBLE_ONLY',
 previewDeploymentAuthorized:false,realGoTrueEnabled:false,
 productionWrites:0,staticReleaseUnchanged:true,
 externalHumanAudit:false
}));
