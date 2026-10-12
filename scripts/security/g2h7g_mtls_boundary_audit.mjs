// G2-H.7G: independent security/release boundary audit, no network calls.
// It does not replace independent professional review or real Cloudflare runtime.
import assert from 'node:assert/strict';
import {readFileSync,existsSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..');
const read=p=>readFileSync(resolve(root,p),'utf8');
const worker=read('ops/cms-preview/worker-mtls-state-contract.mjs');
const proxy=read('scripts/qa/g2h7g_disposable_mtls_harness.mjs');
const integration=read('tests/g2h7g_mtls_pg.test.mjs');
const runner=read('scripts/qa/g2h7f_pg_http_runner.py');
const bff=read('.github/workflows/cms-bff-isolated.yml');
const pg=read('.github/workflows/cms-postgres-isolated.yml');
const publish=read('.github/workflows/publish-static.yml');
const release=read('scripts/release/p412_build_public.py');
const problems=[];
for(const p of ['functions','web/functions','public/functions',
 'web/dist/functions','dist/functions','web/dist/_worker.js',
 'web/dist/_routes.json','public/_worker.js','public/_routes.json'])
 if(existsSync(resolve(root,p)))problems.push('PUBLIC_AUTH_ROUTE_EXISTS:'+p);
for(const [name,source] of [['release',release],['publish',publish]]){
 if(/g2h7g|worker-mtls-state-contract|disposable_mtls_harness|ops\/cms-preview/.test(source))
  problems.push('PUBLIC_RELEASE_CONTAMINATION:'+name);
}
for(const p of [
 'ops/cms-preview','scripts/qa'
])for(const entry of readdirSync(resolve(root,p))){
 if(/\.(?:pem|key|p12|pfx|crt|csr)$/i.test(entry))
  problems.push('COMMITTED_CERTIFICATE_FILE:'+p+'/'+entry);
}
for(const regex of [
 /\bprocess\.env\b/,/\bBuffer\.(?:from|alloc|concat)\s*\(/,
 /from\s+['"]node:/,/\bMath\.random\s*\(/,
 /https:\/\/(?:jianshi-bua\.pages\.dev|[\w-]+\.supabase\.co)/,
 /\bglobalThis\.fetch\s*\(/,
 /\bconsole\./,
 /SYNTHETIC_H7F_LOCAL_ONLY_NON_SECRET/,
 /key:\s*['"](?:sb_|eyJ)/,
 /service_role/
])if(regex.test(worker))problems.push('UNTRUSTED_WORKER_CRYPTO_OR_SECRET:'+regex);
for(const required of [
 "const ENDPOINT='https://h7g-state.example.invalid/v1/email-state'",
 "const PROFILE='SYNTHETIC_G2H7G_MTLS_ONLY'",
 "binding?.synthetic===true",
 "typeof binding.fetch==='function'",
 "redirect:'error'",
 "cache:'no-store'",
 "'CMS_H7G_MTLS_FAILURE'",
 "'CMS_H7G_JSON_ONLY'",
 "'CMS_H7G_DIGEST_DENIED'"
])if(!worker.includes(required))problems.push('WORKER_MTLS_GUARD_MISSING:'+required);
for(const required of [
 "minVersion:'TLSv1.3'",
 "maxVersion:'TLSv1.3'",
 'requestCert:true,rejectUnauthorized:true',
 'req.socket.authorized!==true',
 '!allowed.has(peer?.fingerprint256)',
 'revokeA(){allowed.delete(a.fingerprint);}',
 'new X509Certificate(cert).fingerprint256',
 "server.listen(0,'127.0.0.1'",
 'rmSync(dir,{recursive:true,force:true})',
 "process.env.JIANSHI_G2H7G_MTLS_ONLY==='1'",
 'authorization:\x27Bearer \x27+KEY'
])if(!proxy.includes(required))problems.push('MTLS_HARNESS_GUARD_MISSING:'+required);
for(const required of [
 'G2H7G_MTLS_PG_8_WAY_SINGLE_WINNER_PASS',
 'G2H7G_CERT_ROTATION_REVOKED_A_PASS',
 'foreign certificate',
 'without certificate',
 'SYNTHETIC_H7G_WORKER_B'
])if(!integration.includes(required))problems.push('IDENTITY_REGRESSION_MISSING:'+required);
for(const required of [
 'JIANSHI_G2H7G_MTLS_ONLY',
 'tests/g2h7g_mtls_pg.test.mjs',
 'G2H7G_REAL_MTLS_POSTGRES_PASS',
 'gate(False)'
])if(!runner.includes(required))problems.push('PG_RESET_OR_MTLS_RUN_MISSING:'+required);
for(const item of [
 'ops/cms-preview/worker-mtls-state-contract.mjs',
 'scripts/qa/g2h7g_disposable_mtls_harness.mjs',
 'tests/g2h7g_mtls_contract.test.mjs',
 'tests/g2h7g_mtls_pg.test.mjs',
 'scripts/security/g2h7g_mtls_boundary_audit.mjs'
])if(!bff.includes(item)||!pg.includes(item))
 problems.push('MISSING_WORKFLOW_TRIGGER:'+item);
if(!bff.includes('node scripts/security/g2h7g_mtls_boundary_audit.mjs'))
 problems.push('INDEPENDENT_AUDIT_STEP_MISSING');
if(!pg.includes('python scripts/qa/g2h7f_pg_http_runner.py'))
 problems.push('REAL_PG_STEP_MISSING');
assert.match(publish,/cron: '55 0 \* \* \*'/);
assert.match(publish,/cron: '55 6,12,18 \* \* \*'/);
assert.match(publish,/JIANSHI_AUTH_ENABLED: "0"/);
assert.equal(problems.length,0,'G2H7G_MTLS_AUDIT_BLOCKED '+problems.join('|'));
console.log('G2H7G_MTLS_STATIC_BOUNDARY_AUDIT_PASS '+JSON.stringify({
 isolated:true,authEnabled:false,edgeDeployment:false,
 tls13EphemeralTest:true,nonRoutableWorkerDestination:true,
 publicSecretFiles:0,stagingWrites:0,productionWrites:0,
 thirdPartyReview:false
}));
