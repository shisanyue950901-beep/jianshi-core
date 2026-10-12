// JIANSHI G2-H.7D independent static shipping-boundary guard.
// Run as a separate CI step after the handler's behavioral tests.
// Negative checks prevent an isolated Pages preview candidate from accidentally
// being activated by the existing public static release/build pipeline.
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {resolve} from 'node:path';

const root=resolve(import.meta.dirname,'../..');
const file=path=>readFileSync(resolve(root,path),'utf8');
const candidate='ops/cms-preview/functions/auth/confirm.js';
const source=file(candidate);
const workflow=file('.github/workflows/publish-static.yml');
const release=file('scripts/release/p412_build_public.py');
const staticRedirects=file('web/static/_redirects');
const ci=file('.github/workflows/cms-bff-isolated.yml');
const excluded=[
 'functions','web/functions','web/dist/functions','dist/functions',
 'public/functions','web/dist/_worker.js','dist/_worker.js',
 'web/dist/_routes.json','dist/_routes.json','public/_worker.js',
 'public/_routes.json'
];
const problems=[];
for(const p of excluded)if(existsSync(resolve(root,p)))problems.push('unexpected routable asset '+p);
for(const [p,s] of [
 ['publish-static.yml',workflow],
 ['p412_build_public.py',release],
 ['web/static/_redirects',staticRedirects]
]){
 if(s.includes(candidate)||s.includes('g2h7d_pages_preview_contract')||
    s.includes('ops/cms-preview')||s.includes('g2h7d-preview'))
  problems.push('preview candidate referenced by public release '+p);
}
for(const bad of [
 /from\s+['"]node:/,
 /\bprocess\.env\b/,
 /\bBuffer\b/,
 /\brequire\(/,
 /\bfetch\(/,
 /\bnext\(/,
 /\bconsole\./,
 /\bwrangler\b/,
 /https:\/\/jianshi-bua\.pages\.dev/
])if(bad.test(source))problems.push('forbidden Worker candidate pattern '+bad);
for(const expected of [
 "const ORIGIN='https://h7d-preview.example.invalid'",
 "const PROFILE='SYNTHETIC_CONTRACT_ONLY'",
 "JIANSHI_H7D_CONTRACT_GATE!=='1'",
 'new Response(',
 "request.headers.get('origin')!==u.origin",
 "request.headers.get('sec-fetch-site')!=='same-origin'",
 'async function isEmptyBody(request)',
 'no-store',
 "'referrer-policy':'no-referrer'"
])if(!source.includes(expected))problems.push('missing critical fail-closed guard '+expected);
assert.match(workflow,/cron: '55 0 \* \* \*'/);
assert.match(workflow,/cron: '55 6,12,18 \* \* \*'/);
assert.match(workflow,/JIANSHI_AUTH_ENABLED: "0"/);
assert.ok(ci.includes('tests/g2h7d_pages_preview_contract.test.mjs'),
 'isolated CI missing behavior test');
assert.ok(ci.includes('g2h7d_preview_deployment_guard.mjs'),
 'isolated CI missing static audit');
assert.ok(!problems.length,
 'G2H7D_SHIPPING_BOUNDARY_FAILED: '+problems.join(' | '));
console.log('G2H7D_PREVIEW_ISOLATION_AUDIT_PASS '+JSON.stringify({
 rootPagesFunctions:false,
 previewRoutePublished:false,
 productionAuthDisabled:true,
 scheduleIntact:true,
 failClosedSyntheticOrigin:true,
 blockedPaths:excluded.length,
 explicitHumanReviewStillRequired:true
}));
