'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const DIR=path.join(ROOT,'web/prototypes/f21g2e');
const {Demo,Refused}=require(path.join(DIR,'model.js'));
function expectRefusal(demo,op,code){
 const before=JSON.stringify(demo.summary());
 assert.throws(()=>demo.apply(op),e=>e instanceof Refused&&e.code===code);
 assert.equal(JSON.stringify(demo.summary()),before);
}
test('restored historical version is a NEW unapproved draft',()=>{
 const d=new Demo();
 const before=d.summary().versions.slice(0,3);
 const result=d.apply('RESTORE');
 assert.equal(result.revision,4);
 assert.equal(result.state,'DRAFT');
 assert.equal(result.versions[3].title,before[0].title);
 assert.equal(result.versions[3].rights,false);
 assert.equal(result.versions[3].facts,false);
 assert.deepEqual(result.versions.slice(0,3),before);
 assert.equal(result.events.at(-1).op,'RESTORE');
 assert.equal(result.snapshots.length,0);
});
test('fresh check and independent approval create only staged projection',()=>{
 const d=new Demo();
 d.apply('RESTORE');d.apply('EDIT');d.apply('SUBMIT');d.apply('APPROVE');
 const p=d.apply('PUBLISH');
 assert.equal(p.state,'PUBLISHED');
 assert.equal(p.snapshots[0].state,'STAGED');
 expectRefusal(d,'RESTORE','CMS_RESTORE_REQUIRES_DRAFT');
 const r=d.apply('RETRACT');
 assert.equal(r.state,'UNPUBLISHED');
 assert.equal(r.snapshots[0].state,'RETRACTED');
 d.apply('RESUBMIT');d.apply('APPROVE');const last=d.apply('PUBLISH');
 assert.equal(last.snapshots.length,2);
 assert.deepEqual(last.snapshots.map(s=>s.state),['RETRACTED','STAGED']);
});
test('invalid transitions do not mutate state or audit',()=>{
 const d=new Demo();
 expectRefusal(d,'PUBLISH','CMS_ILLEGAL_TRANSITION');
 expectRefusal(d,'APPROVE','CMS_ILLEGAL_TRANSITION');
 d.apply('SUBMIT');
 expectRefusal(d,'RESTORE','CMS_RESTORE_REQUIRES_DRAFT');
 const s=d.apply('REJECT');
 assert.equal(s.state,'REJECTED');
 d.apply('RETURN_TO_DRAFT');
 assert.equal(d.summary().state,'DRAFT');
});
test('prototype has no remote data, writable forms or public auth surface',()=>{
 const contents=['index.html','app.js','model.js'].map(n=>fs.readFileSync(path.join(DIR,n),'utf8')).join('\n');
 for(const forbidden of ['fetch(','XMLHttpRequest','WebSocket','sendBeacon','localStorage',
   'sessionStorage','document.cookie','service_role','/auth/v1','/rest/v1','contenteditable',
   '<form','payment','finance','真实用户'])assert.ok(!contents.includes(forbidden),'unexpected '+forbidden);
 assert.match(contents,/隔离合成演示/);
 assert.match(contents,/noindex,nofollow/);
 assert.match(contents,/data-action="RESTORE"/);
});
