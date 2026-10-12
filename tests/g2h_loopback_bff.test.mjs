import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
process.env.JIANSHI_G2H_SYNTHETIC_ONLY='1';
import {createQaServer} from '../scripts/qa/g2h_loopback_bff/server.mjs';

async function setup(config={}){
 const h=createQaServer(config);
 await new Promise(resolve=>h.server.listen(0,'127.0.0.1',resolve));
 return {h,base:'http://127.0.0.1:'+h.server.address().port,
   close:()=>new Promise(resolve=>h.server.close(resolve))};
}
function cookie(session){return session.cookie.split(';')[0];}
async function get(s,path,session){
 const r=await fetch(s.base+path,{headers:session?{cookie:cookie(session)}:{}});
 return {http:r.status,body:await r.json()};
}
async function action(s,session,operation,revision,overrides={},headers={}){
 const data={operation,request_id:crypto.randomUUID(),expected_revision:revision,...overrides};
 const r=await fetch(s.base+'/qa/api/action',{method:'POST',
  headers:{'content-type':'application/json','origin':s.base,
   cookie:session?cookie(session):'','x-csrf-token':session?.csrf||'',...headers},
  body:JSON.stringify(data)});
 return {http:r.status,body:await r.json(),request:data.request_id};
}

test('fail-closed synthetic runtime, fixed loopback host, and non-public UI',async()=>{
 const s=await setup();try{
  const r=await get(s,'/qa/api/session');
  assert.equal(r.http,401);
  assert.equal(r.body.status,'CMS_SESSION_INVALID');
  const page=await fetch(s.base+'/qa/cms');
  assert.equal(page.status,200);
  assert.match(await page.text(),/仅用于本机安全测试/);
  assert.match(page.headers.get('content-security-policy'),/frame-ancestors 'none'/);
  assert.match(page.headers.get('x-robots-tag'),/noindex/);
  const bad=await new Promise((resolve,reject)=>{
   http.get(s.base+'/qa/api/state',{headers:{Host:'unsafe.example'}},r=>{
    r.resume();r.on('end',()=>resolve(r.statusCode));
   }).on('error',reject);
  });
  assert.equal(bad,403);
  const a=s.h.issueFixture('SYNTHETIC_AUTHOR_A');
  assert.match(a.cookie,/HttpOnly; SameSite=Strict; Path=\/qa/);
  assert.equal((await get(s,'/qa/api/session',a)).body.role,'EDITOR');
  assert.throws(()=>s.h.issueFixture('SYNTHETIC_ATTACKER'),/CMS_SYNTHETIC_ACTOR_ONLY/);
 }finally{await s.close();}
});

test('CSRF, strict Origin, and RBAC deny mutations with zero side-effects',async()=>{
 const s=await setup();try{
  const a=s.h.issueFixture('SYNTHETIC_AUTHOR_A');
  const b=s.h.issueFixture('SYNTHETIC_AUTHOR_B');
  const reviewer=s.h.issueFixture('SYNTHETIC_REVIEWER');
  const before=JSON.stringify(s.h.snapshot());
  assert.equal((await action(s,a,'EDIT',2,{title:'非法尝试',rights_attested:true,facts_attested:true},
    {'x-csrf-token':'wrong'})).body.status,'CMS_CSRF_DENIED');
  assert.equal((await action(s,a,'EDIT',2,{title:'非法尝试',rights_attested:true,facts_attested:true},
    {origin:'https://attacker.invalid'})).body.status,'CMS_ORIGIN_DENIED');
  assert.equal((await action(s,a,'EDIT',2,{title:'非法尝试',rights_attested:true,facts_attested:true},
    {'sec-fetch-site':'cross-site'})).body.status,'CMS_FETCH_SITE_DENIED');
  assert.equal((await action(s,b,'EDIT',2,{title:'伪装作者',rights_attested:true,facts_attested:true})).body.status,'CMS_OWNER_DENIED');
  assert.equal((await action(s,reviewer,'EDIT',2,{title:'审核者冒充作者',rights_attested:true,facts_attested:true})).body.status,'CMS_OWNER_DENIED');
  assert.equal((await action(s,a,'APPROVE',2)).body.status,'CMS_INDEPENDENT_REVIEW_REQUIRED');
  assert.equal((await action(s,a,'EDIT',2,{title:'非法参数',rights_attested:true,facts_attested:true,p_actor:'SYNTHETIC_ADMIN'})).body.status,'CMS_PAYLOAD_ALLOWLIST');
  assert.equal(JSON.stringify(s.h.snapshot()),before);
 }finally{await s.close();}
});

test('real same-origin HTTP path completes mock restoration, re-review, publish and retract',async()=>{
 const s=await setup({maxRequests:30});try{
  const author=s.h.issueFixture('SYNTHETIC_AUTHOR_A');
  const review=s.h.issueFixture('SYNTHETIC_REVIEWER');
  const publish=s.h.issueFixture('SYNTHETIC_PUBLISHER');
  const versions=s.h.snapshot().revisions;
  let r=await action(s,author,'RESTORE',2,{source_revision:1});
  assert.equal(r.http,200,JSON.stringify(r.body));
  assert.equal(r.body.version,3);
  assert.equal(r.body.revisions.at(-1).title,versions[0].title);
  assert.equal(r.body.revisions.at(-1).rights,false);
  assert.deepEqual(r.body.revisions.slice(0,2),versions);
  r=await action(s,author,'SUBMIT',3);assert.equal(r.http,200);
  r=await action(s,review,'APPROVE',4);
  assert.equal(r.http,422);assert.equal(r.body.status,'CMS_RECHECK_REQUIRED');
  r=await action(s,review,'REJECT',4);assert.equal(r.http,200);
  // A rejected restore does NOT become editable without explicit workflow reset.
  r=await action(s,author,'EDIT',5,{title:'复核稿',rights_attested:true,facts_attested:true});
  assert.equal(r.body.status,'CMS_DRAFT_LOCKED');
  // Reset only from test-side fixture, not from public HTTP.
  s.h.resetFixtures();
  r=await action(s,author,'EDIT',2,{title:'重新核验完成的合成稿',rights_attested:true,facts_attested:true});
  assert.equal(r.http,200);assert.equal(r.body.version,3);
  r=await action(s,author,'SUBMIT',3);assert.equal(r.http,200);
  r=await action(s,review,'APPROVE',4);assert.equal(r.http,200);
  r=await action(s,publish,'PUBLISH',5);assert.equal(r.http,200);
  assert.deepEqual(r.body.snapshots.map(x=>x.lifecycle),['STAGED']);
  r=await action(s,publish,'RETRACT',6);assert.equal(r.http,200);
  assert.deepEqual(r.body.snapshots.map(x=>x.lifecycle),['RETRACTED']);
  assert.equal((await get(s,'/qa/api/state',author)).body.status,'UNPUBLISHED');
 }finally{await s.close();}
});

test('idempotency, stale revision, revoked and expired sessions and rate limit',async()=>{
 let tick=1000;
 const s=await setup({now:()=>tick,maxRequests:4});try{
  const a=s.h.issueFixture('SYNTHETIC_AUTHOR_A');
  const bad=await action(s,a,'EDIT',2,{title:'小标题',rights_attested:true,facts_attested:true});
  assert.equal(bad.http,200);
  const duplicate=await action(s,a,'SUBMIT',3,{request_id:bad.request});
  assert.equal(duplicate.body.status,'CMS_DUPLICATE_REQUEST');
  assert.equal((await action(s,a,'SUBMIT',2)).body.status,'CMS_STALE_REVISION');
  assert.equal((await action(s,a,'PUBLISH',3)).body.status,'CMS_PUBLISHER_DENIED');
  const over=await action(s,a,'SUBMIT',3);
  assert.equal(over.http,429);assert.equal(over.body.status,'CMS_RATE_LIMITED');
  s.h.revokeFixture(a.id);
  assert.equal((await get(s,'/qa/api/state',a)).http,401);
  const b=s.h.issueFixture('SYNTHETIC_AUTHOR_A');
  tick+=15*60*1000+1;
  assert.equal((await get(s,'/qa/api/session',b)).http,401);
 }finally{await s.close();}
});

test('public build never imports local QA app or stores actual identities',()=>{
 const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
 const build=fs.readFileSync(path.join(root,'scripts/release/p412_build_public.py'),'utf8');
 const workflow=fs.readFileSync(path.join(root,'.github/workflows/publish-static.yml'),'utf8');
 const source=fs.readFileSync(path.join(root,'scripts/qa/g2h_loopback_bff/server.mjs'),'utf8');
 assert.ok(!build.includes('g2h_loopback_bff'));
 assert.ok(!workflow.includes('g2h_loopback_bff'));
 assert.ok(!source.includes('sb_secret_')&&!source.includes('@gmail.com'));
 assert.ok(!source.includes('https://api.')&&!source.includes('https://apuibjhxinumxbfnqlkp'));
 assert.equal(workflow.match(/cron: '55 0 \* \* \*'/g)?.length,1);
 assert.equal(workflow.match(/cron: '55 6,12,18 \* \* \*'/g)?.length,1);
 assert.equal(fs.existsSync(path.join(root,'web/dist/qa/cms/index.html')),false);
});
