import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import worker from '../ops/cms-preview/cloudflare/locked-worker.mjs';
import {assessPreviewSafety,auditRepository}
 from '../scripts/security/g2h7h_preview_admission.mjs';
const root=resolve(import.meta.dirname,'..');
const read=p=>readFileSync(resolve(root,p),'utf8');
const baseline=()=>({
 config:JSON.parse(read('ops/cms-preview/cloudflare/wrangler.json')),
 manifest:JSON.parse(read('ops/cms-preview/cloudflare/deploy-admission.json')),
 workerSource:read('ops/cms-preview/cloudflare/locked-worker.mjs'),
 releaseSource:read('scripts/release/p412_build_public.py'),
 publishSource:read('.github/workflows/publish-static.yml'),
 bffSource:read('.github/workflows/cms-bff-isolated.yml')
});
const evaluate=change=>assessPreviewSafety({...baseline(),...change});

test('non-deployed preview config remains BLOCKED even when tests pass',()=>{
 const p=evaluate({});
 assert.equal(p.safeBlocked,true);
 assert.equal(p.remoteDeploymentAuthorized,false);
 assert.equal(p.authEnabled,false);
 assert.ok(p.reviewedGates>=12);
 assert.deepEqual(p.problems,[]);
});
test('deny-only Worker: no session, token_hash, routes, cookies, origin or method can log in',async()=>{
 for(const origin of [
  'https://jianshi-bua.pages.dev',
  'https://preview.jianshi-bua.pages.dev',
  'https://fake-worker.workers.dev',
  'https://h7g-state.example.invalid'
 ]){
  for(const method of ['GET','POST','OPTIONS']){
   const url=origin+'/auth/confirm?state=SYNTHETIC_STATE&token_hash='+
    'a'.repeat(64)+'&type=email';
   const response=await worker.fetch(new Request(url,{method,
    headers:{cookie:'__Host-jianshi_cms=SYNTHETIC_COOKIE',
     authorization:'Bearer SYNTHETIC_JWT'}}),{
     JIANSHI_AUTH_ENABLED:'1',SUPABASE_SERVICE_ROLE_KEY:'SYNTHETIC_FAKE_KEY'
    },{});
   assert.equal(response.status,404);
   assert.match(response.headers.get('cache-control'),/no-store/);
   assert.equal(response.headers.get('referrer-policy'),'no-referrer');
   assert.equal(response.headers.get('set-cookie'),null);
   const content=await response.text();
   assert.equal(content,'Not Found');
   for(const secret of ['token_hash','SYNTHETIC_JWT',
    'SYNTHETIC_FAKE_KEY','SYNTHETIC_COOKIE'])assert.ok(!content.includes(secret));
  }
 }
 const cms=await worker.fetch(new Request('https://preview.invalid/cms/'),{},{});
 assert.equal(cms.status,404);
});
test('turning on Worker workers.dev or version preview URLs must fail audit',()=>{
 for(const prop of ['workers_dev','preview_urls']){
  const x=baseline();x.config[prop]=true;
  const r=assessPreviewSafety(x);
  assert.equal(r.safeBlocked,false);
  assert.ok(r.problems.includes('UNSAFE_CLOUDFLARE_ROUTE_OR_BINDING'));
 }
});
test('custom hostname, production Pages route, mTLS binding or cron trigger denied',()=>{
 for(const mutate of [
  x=>{x.config.name='jianshi-bua';},
  x=>{x.config.routes=['jianshi-bua.pages.dev/*'];},
  x=>{x.config.mtls_certificates=[{
   binding:'CMS_AUTH_CERT',certificate_id:'SYNTHETIC_123'}];},
  x=>{x.config.route={pattern:'jianshi-bua.pages.dev/auth/*'};},
  x=>{x.config.triggers={crons:['* * * * *']};},
  x=>{x.config.vars.JIANSHI_AUTH_ENABLED='1';}
 ]){
  const x=baseline();mutate(x);
  assert.equal(assessPreviewSafety(x).safeBlocked,false);
 }
});
test('any claimed deployment, real identities, secrets or user approval must be blocked',()=>{
 const gates=Object.keys(baseline().manifest)
  .filter(k=>typeof baseline().manifest[k]==='boolean');
 for(const key of gates){
  const x=baseline();x.manifest[key]=true;
  const p=assessPreviewSafety(x);
  assert.equal(p.safeBlocked,false,'gate wrongly allowed '+key);
  assert.ok(p.problems.includes('PREVIEW_RELEASE_NOT_AUTHORIZED'));
 }
 const x=baseline();x.manifest.readiness_evidence_links=['https://fake.invalid/green'];
 assert.equal(assessPreviewSafety(x).safeBlocked,false);
});
test('any auth handler or outbound fetch inserted into Worker blocks release',()=>{
 for(const injected of [
  "\nconst token=await fetch('https://staging.invalid/rpc');",
  "\nconst auth=async()=>new Response('OK',{status:200});",
  "\n// auth mutation\nconst value=process.env.SUPABASE_KEY;",
  "\nconsole.log('SECRET');",
  "\nimport secret from './secrets.js';"
 ]){
  const x=baseline();x.workerSource+=injected;
  assert.equal(assessPreviewSafety(x).safeBlocked,false,
   'an unsafe injection passed: '+injected.slice(0,50));
 }
});
test('release drift, static cron/flag drift, and missing isolated workflow gate reject',()=>{
 for(const mutate of [
  x=>x.publishSource=x.publishSource.replace(
   "cron: '55 0 * * *'","cron: '* * * * *'"),
  x=>x.publishSource=x.publishSource.replace(
   'JIANSHI_AUTH_ENABLED: "0"','JIANSHI_AUTH_ENABLED: "1"'),
  x=>x.publishSource+='ops/cms-preview/cloudflare',
  x=>x.releaseSource+='ops/cms-preview/cloudflare',
  x=>x.bffSource=x.bffSource.replace(
   /tests\/g2h7h_preview_admission\.test\.mjs/g,'TEST_REMOVED'),
 ]){
  const x=baseline();mutate(x);
  assert.equal(assessPreviewSafety(x).safeBlocked,false);
 }
});
test('independent safety CLI passes only when launch is still BLOCKED',()=>{
 auditRepository();
});
