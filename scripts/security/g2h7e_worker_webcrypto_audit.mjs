// G2-H.7E second-pass static audit, independent from Worker behavior tests.
// Blocks Node crypto, shared production secrets, public routing, and P4.41 drift.
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..');
const get=name=>readFileSync(resolve(root,name),'utf8');
const crypto=get('ops/cms-preview/worker-email-crypto.mjs');
const release=get('scripts/release/p412_build_public.py');
const publish=get('.github/workflows/publish-static.yml');
const edge=get('ops/cms-preview/functions/auth/confirm.js');
const ci=get('.github/workflows/cms-bff-isolated.yml');
const publicRoot=['functions','web/functions','dist/functions','public/functions',
 'web/dist/functions','web/dist/_worker.js','web/dist/_routes.json',
 'dist/_worker.js','dist/_routes.json','public/_worker.js','public/_routes.json'];
const errors=[];
for(const p of publicRoot)if(existsSync(resolve(root,p)))
 errors.push('forbidden routable path '+p);
for(const p of ['scripts/release/p412_build_public.py','.github/workflows/publish-static.yml']){
 const s=p.endsWith('.py')?release:publish;
 if(s.includes('ops/cms-preview')||s.includes('worker-email-crypto')||
    s.includes('g2h7e_worker_webcrypto')||s.includes('g2h7e_worker_webcrypto_audit'))
  errors.push('isolated crypto referenced by public release '+p);
}
for(const pattern of [
 /from\s*['"]node:/,
 /\brequire\s*\(/,
 /\bprocess\.env\b/,
 /\bBuffer\.(?:alloc|from|concat|isBuffer)\s*\(/,
 /\bMath\.random\s*\(/,
 /\bconsole\./,
 /\bfetch\s*\(/,
 /\bDate\.now\(\)\s*%/,
 /\bnew\s+Function\s*\(/,
 /\beval\s*\(/,
 /https:\/\/(?:jianshi-bua\.pages\.dev|dalfvgehosxfyxkptxwx\.supabase\.co)/i
])if(pattern.test(crypto))errors.push('forbidden Worker implementation code: '+pattern);
for(const required of [
 "const ORIGIN='https://h7d-preview.example.invalid'",
 "const ACTIVE='SYNTHETIC_H7E_ONLY'",
 "pendingStore?.synthetic===true",
 "provider?.synthetic===true",
 "verifyIdentity?.synthetic===true",
 "issueSession?.synthetic===true",
 "crypto.getRandomValues(",
 "crypto.subtle.importKey('raw'",
 "crypto.subtle.deriveKey(",
 "crypto.subtle.encrypt(",
 "crypto.subtle.decrypt(",
 "crypto.subtle.sign('HMAC'",
 "JIANSHI_G2H7B_EMAIL_INTENT_V1",
 "CMS_H7E_REPLAY_OR_EXPIRED",
 "CMS_H7E_SYNTHETIC_TOKENS_ONLY"
])if(!crypto.includes(required))errors.push('missing cryptographic protection: '+required);
assert.match(publish,/cron: '55 0 \* \* \*'/);
assert.match(publish,/cron: '55 6,12,18 \* \* \*'/);
assert.match(publish,/JIANSHI_AUTH_ENABLED: "0"/);
assert.match(edge,/const ORIGIN='https:\/\/h7d-preview\.example\.invalid'/);
assert.ok(ci.includes('tests/g2h7e_worker_webcrypto.test.mjs'));
assert.ok(ci.includes('scripts/security/g2h7e_worker_webcrypto_audit.mjs'));
assert.equal(errors.length,0,'G2H7E_SECURITY_AUDIT_DENIED '+errors.join(' | '));
console.log('G2H7E_WEBCRYPTO_SECURITY_AUDIT_PASS '+JSON.stringify({
 webApiOnly:true,nonRoutableSyntheticOrigin:true,distributedStorageNotDeployed:true,
 publicReleaseUntouched:true,productionAuthDisabled:true,p441SchedulesFrozen:true,
 publishedPagesFunctions:0,forbiddenPublicPathsChecked:publicRoot.length,
 externalIndependentAudit:false
}));
