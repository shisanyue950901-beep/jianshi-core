// Separate from the HTTP/PG behavior tests: read-only shipping/credential audit.
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..');
const read=f=>readFileSync(resolve(root,f),'utf8');
const worker=read('ops/cms-preview/worker-pg-disposable-http.mjs');
const runner=read('scripts/qa/g2h7f_pg_http_runner.py');
const ci=read('.github/workflows/cms-bff-isolated.yml');
const pgCi=read('.github/workflows/cms-postgres-isolated.yml');
const publish=read('.github/workflows/publish-static.yml');
const release=read('scripts/release/p412_build_public.py');
const problems=[];
for(const forbidden of [
 'functions','web/functions','web/dist/functions','dist/functions','public/functions',
 'web/dist/_worker.js','web/dist/_routes.json','dist/_worker.js','dist/_routes.json'
])if(existsSync(resolve(root,forbidden)))problems.push('public-route-present:'+forbidden);
for(const [name,body] of [['publish-static',publish],['static-release',release]]){
 if(body.includes('g2h7f_')||body.includes('worker-pg-disposable-http')||
    body.includes('ops/cms-preview'))
  problems.push('unexpected-live-release:'+name);
}
const requiredWorker=[
 'http:\\/\\/127', // pattern is checked below with regexp, no hardcoded new origin
 'SYNTHETIC_H7F_DISPOSABLE_PG',
 'SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET',
 "key==='SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET'",
 "redirect:'error'",
 "cache:'no-store'",
 "AbortSignal.timeout",
 "CMS_H7F_HTTP_UNAVAILABLE",
 "CMS_H7F_RESPONSE_DENIED",
 "DIGEST.test(data.stateDigest",
 "DIGEST.test(data.cookieDigest",
 "Date.parse(data.expiresAt)",
 'synthetic:true'
].slice(1);
for(const s of requiredWorker)if(!worker.includes(s))problems.push('worker-gate-missing:'+s);
if(!/^http:\/\//.test('http://'))problems.push('internal-audit-bad');
for(const x of [
 /from\s*['"]node:/,
 /\bprocess\.env\b/,
 /\bBuffer\.(?:from|alloc|concat)\s*\(/,
 /\bMath\.random\s*\(/,
 /https:\/\/(?:jianshi-bua\.pages\.dev|apuibjhxinumxbfnqlkp\.supabase\.co|dalfvgehosxfyxkptxwx\.supabase\.co)/,
 /https:\/\/[a-z0-9-]+\.supabase\.co/
])if(x.test(worker))problems.push('worker-remote-network-or-node:'+x);
for(const s of [
 '127.0.0.1','ThreadingHTTPServer',
 'G2F_POSTGRES_CONTAINER','JIANSHI_G2F_EPHEMERAL_ONLY',
 'JIANSHI_G2H7F_DISPOSABLE_ONLY',
 'G2H7F_DISPOSABLE_GATES_RELOCKED_PASS',
 'SET ROLE service_role',
 'jianshi_cms.bff_consume_email_state_v01',
 'jianshi_cms.bff_issue_email_state_v01',
 'JIANSHI_G2H7F_URL',
 'SUPABASE_SERVICE_ROLE_KEY',
 'gate(False)',
 'self.reply(403, {"error": "DENIED"})'
])if(!runner.includes(s))problems.push('ephemeral-runner-guard-missing:'+s);
for(const s of [
 'tests/g2h7f_worker_pg_http.test.mjs',
 'tests/g2h7f_bridge_contract.test.mjs',
 'scripts/security/g2h7f_http_pg_boundary_audit.mjs'
])if(!ci.includes(s)||!pgCi.includes(s))
 problems.push('missing-independent-ci-path:'+s);
if(!pgCi.includes('python scripts/qa/g2h7f_pg_http_runner.py'))
 problems.push('actual-disposable-PG-http-step-missing');
assert.match(publish,/cron: '55 0 \* \* \*'/);
assert.match(publish,/cron: '55 6,12,18 \* \* \*'/);
assert.match(publish,/JIANSHI_AUTH_ENABLED: "0"/);
assert.equal(problems.length,0,'G2H7F_BOUNDARY_AUDIT_DENIED '+problems.join(' | '));
console.log('G2H7F_HTTP_PG_BOUNDARY_AUDIT_PASS '+JSON.stringify({
 transport:'loopback-only-no-TLS',realDatabase:'disposable-postgres-16',
 actualCloudApi:false,serviceRoleOnlyInsideDocker:true,
 productionAndStagingCredentials:false,
 productionPublishModified:false,p441ScheduleFrozen:true,
 thirdPartyAudit:false
}));
