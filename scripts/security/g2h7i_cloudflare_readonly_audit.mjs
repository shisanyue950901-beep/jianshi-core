// G2-H.7I independent static read-only/cloud-deployment boundary audit.
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..');
const get=p=>readFileSync(resolve(root,p),'utf8');
const client=get('scripts/security/g2h7i_cloudflare_readonly_client.mjs');
const cli=get('scripts/security/g2h7i_cloudflare_readonly_cli.mjs');
const workflow=get('.github/workflows/cms-bff-isolated.yml');
const publish=get('.github/workflows/publish-static.yml');
const release=get('scripts/release/p412_build_public.py');
const blocked=get('ops/cms-preview/cloudflare/deploy-admission.json');
const candidate=get('ops/cms-preview/cloudflare/wrangler.json');
const problems=[];
for(const p of [
 'functions','web/functions','web/dist/functions','dist/functions',
 'web/dist/_worker.js','web/dist/_routes.json','public/_worker.js'
])if(existsSync(resolve(root,p)))problems.push('EXPOSED_PUBLIC_ROUTE:'+p);
for(const [name,source] of [['client',client],['cli',cli]]){
 if(/wrangler\s+(deploy|publish|secret|delete|tail)/i.test(source)||
  /fetchImpl\([^)]*https:\/\/(?!api.cloudflare.com)/.test(source)||
  /\b(?:PUT|POST|PATCH|DELETE)\s*:\s*['"]/.test(source)||
  /method\s*:\s*['"](?:PUT|POST|PATCH|DELETE)['"]/.test(source)||
  /\/upload-token|\/purge_build_cache|\/deployments\/[A-Za-z0-9]/.test(source))
  problems.push('REMOTE_MUTATION_CAPABILITY:'+name);
}
for(const marker of [
 "const API='https://api.cloudflare.com'",
 "method:'GET'",
 "redirect:'error'",
 "'EXPLICIT_REMOTE_READONLY'",
 "'CMS_H7I_CLOUDFLARE_API_REJECTED'",
 "'CMS_H7I_WORKERS_COVERAGE_INCOMPLETE'",
 "safeToDeploy:false",
 "containsCredentials:false"
])if(!client.includes(marker))
 problems.push('CLIENT_FAIL_CLOSED_MISSING:'+marker);
for(const marker of [
 "if(args.length===0)",
 "G2H7I_REMOTE_INVENTORY_NOT_CONNECTED",
 "JIANSHI_H7I_REMOTE_READONLY_APPROVED!=='1'",
 "JIANSHI_H7I_READ_TOKEN",
 "process.env.JIANSHI_H7I_ACCOUNT_ID",
 "console.error('G2H7I_REMOTE_READONLY_FAIL_CLOSED '"
])if(!cli.includes(marker))
 problems.push('CLI_OPT_IN_MISSING:'+marker);
for(const marker of [
 'node --test tests/g2h7i_cloudflare_readonly.test.mjs',
 'node scripts/security/g2h7i_cloudflare_readonly_audit.mjs',
 'scripts/security/g2h7i_cloudflare_readonly_client.mjs',
 'scripts/security/g2h7i_cloudflare_readonly_cli.mjs'
])if(!workflow.includes(marker))problems.push('CI_TEST_NOT_INCLUDED:'+marker);
if(workflow.includes('--remote-read-only')||
 workflow.includes('JIANSHI_H7I_READ_TOKEN')||
 workflow.includes('CLOUDFLARE_API_TOKEN'))
 problems.push('REAL_CLOUD_CONNECTION_IN_CI');
if(/g2h7i|cloudflare_readonly|ops\/cms-preview/.test(publish)||
 /g2h7i|cloudflare_readonly|ops\/cms-preview/.test(release))
 problems.push('PUBLIC_STATIC_BUILD_CONTAMINATION');
assert.match(publish,/cron: '55 0 \* \* \*'/);
assert.match(publish,/cron: '55 6,12,18 \* \* \*'/);
assert.match(publish,/JIANSHI_AUTH_ENABLED: "0"/);
const manifest=JSON.parse(blocked),config=JSON.parse(candidate);
if(manifest.gate!=='BLOCKED_BY_DEFAULT'||
 manifest.real_cloudflare_deployment!==false||
 manifest.explicit_future_remote_deploy_approval!==false||
 config.workers_dev!==false||
 config.preview_urls!==false||
 config.routes?.length!==0)
 problems.push('PREVIOUS_DEPLOYMENT_HARD_LOCK_BROKEN');
assert.deepEqual(problems,[],'G2H7I_INVENTORY_AUDIT_BLOCKED '+problems.join(' | '));
console.log('G2H7I_READONLY_CLOUDFLARE_INVENTORY_AUDIT_PASS '+
 JSON.stringify({
  httpMethods:['GET'],cloudflareCallsDuringCI:0,credentialExposure:false,
  publicDeployment:false,remoteCloudVerification:'NOT_CONNECTED',
  zoneScopeMayBePartial:true,manualSecurityReview:false,
  productionAuthEnabled:false,disposableAccountOnly:false
 }));
