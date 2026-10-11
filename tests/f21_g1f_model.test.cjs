"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {SyntheticCMS,roles} = require("../web/prototypes/f21f/model.js");

const AUTHOR="TEST_AUTHOR_A", REVIEWER="TEST_REVIEWER_B", PUBLISHER="TEST_PUBLISHER_C";
const ID="SYNTHETIC_G1F_01";
const expectError=(fn,code)=>assert.throws(fn,e=>e.code===code);

function ready(cms) {
  let r=cms.read(ID);
  r=cms.edit(ID,AUTHOR,r.revision,{factsChecked:true,rightsConfirmed:true,
    mediaLicense:"OWNED",mediaScan:"PASSED"});
  assert.equal(r.revision,2);
  return r;
}

test("fresh data is genuinely synthetic, in memory, and unpublished",()=>{
  const c=new SyntheticCMS();
  assert.equal(c.list().length,2);
  assert.deepEqual(c.publicList(),[]);
  for(const r of c.list()){
    assert.match(r.id,/^SYNTHETIC_/);
    assert.equal(r.state,"DRAFT");
  }
  assert.equal(c.audit(ID).length,0);
  assert.equal(roles.TEST_VISITOR,"VISITOR");
});

test("role isolation, unsupported fields, and stale version are rejected without mutation",()=>{
  const c=new SyntheticCMS();
  const before=c.read(ID);
  expectError(()=>c.edit(ID,"TEST_AUTHOR_B",1,{title:"篡改"}),"OWNER_REQUIRED");
  expectError(()=>c.edit(ID,AUTHOR,0,{title:"冲突"}),"STALE_REVISION");
  expectError(()=>c.edit(ID,AUTHOR,1,{secret:"leak"}),"UNKNOWN_FIELD");
  expectError(()=>c.edit(ID,AUTHOR,1,{title:"有效标题",summary:""}),"INVALID_SUMMARY");
  assert.deepEqual(c.read(ID),before, "a failing partial patch must be rolled back");
  assert.equal(c.audit(ID).length,0);
});

test("two-person editorial workflow with rights gates, published projection and retraction",()=>{
  const c=new SyntheticCMS();
  let r=c.read(ID);
  r=c.transition(ID,AUTHOR,r.revision,"IN_REVIEW");
  expectError(()=>c.transition(ID,AUTHOR,r.revision,"APPROVED"),"INDEPENDENT_REVIEW_REQUIRED");
  expectError(()=>c.transition(ID,REVIEWER,r.revision,"APPROVED"),"EVIDENCE_OR_RIGHTS_MISSING");
  assert.equal(c.read(ID).revision,r.revision);
  r=c.transition(ID,REVIEWER,r.revision,"REJECTED");
  r=c.transition(ID,AUTHOR,r.revision,"DRAFT");
  r=c.edit(ID,AUTHOR,r.revision,{factsChecked:true,rightsConfirmed:true});
  r=c.transition(ID,AUTHOR,r.revision,"IN_REVIEW");
  expectError(()=>c.transition(ID,REVIEWER,r.revision,"APPROVED"),"MEDIA_RIGHTS_NOT_READY");
  r=c.transition(ID,REVIEWER,r.revision,"REJECTED");
  r=c.transition(ID,AUTHOR,r.revision,"DRAFT");
  r=c.edit(ID,AUTHOR,r.revision,{mediaLicense:"LICENSED",mediaScan:"PASSED"});
  r=c.transition(ID,AUTHOR,r.revision,"IN_REVIEW");
  r=c.transition(ID,REVIEWER,r.revision,"APPROVED");
  expectError(()=>c.transition(ID,AUTHOR,r.revision,"PUBLISHED"),"PUBLISHER_REQUIRED");
  r=c.transition(ID,PUBLISHER,r.revision,"PUBLISHED");
  assert.equal(c.publicList().length,1);
  const publicDoc=c.publicProjection(ID);
  assert.equal(publicDoc.title,r.title);
  assert.deepEqual(Object.keys(publicDoc).sort(),[
    "category","content_id","content_type","published_at","revision",
    "source_refs","summary","title"
  ]);
  assert.equal(JSON.stringify(publicDoc).includes("privateNote"),false);
  assert.equal(JSON.stringify(publicDoc).includes("body"),false);
  assert.equal(JSON.stringify(publicDoc).includes("SYNTHETIC_MEDIA"),false);
  r=c.transition(ID,PUBLISHER,r.revision,"UNPUBLISHED");
  assert.deepEqual(c.publicList(),[]);
  expectError(()=>c.publicProjection(ID),"NOT_PUBLISHED");
  assert.ok(c.audit(ID).length >= 9);
});

test("published or submitted documents are locked against edits",()=>{
  const c=new SyntheticCMS();
  let r=ready(c);
  r=c.transition(ID,AUTHOR,r.revision,"IN_REVIEW");
  expectError(()=>c.edit(ID,AUTHOR,r.revision,{body:"未经审批覆盖"}),"DRAFT_LOCKED");
  expectError(()=>c.transition(ID,AUTHOR,r.revision,"IN_REVIEW"),"ILLEGAL_TRANSITION");
  assert.equal(c.read(ID).revision,r.revision);
});

test("synthetic rights and source references must stay safe",()=>{
  const c=new SyntheticCMS();
  const r=c.read(ID);
  expectError(()=>c.edit(ID,AUTHOR,r.revision,{mediaLicense:"USER_UPLOAD_URL"}),"INVALID_MEDIA_LICENSE");
  assert.deepEqual(c.read(ID),r);
  const tainted=Object.assign({},r,{id:"SYNTHETIC_TAINT",sources:[{kind:"PUBLIC_URL",url:"https://fake.test?token=SECRET"}]});
  const c2=new SyntheticCMS([tainted]);
  let v=c2.read(tainted.id);
  v=c2.edit(v.id,AUTHOR,v.revision,{rightsConfirmed:true,factsChecked:true,mediaLicense:"OWNED",mediaScan:"PASSED"});
  v=c2.transition(v.id,AUTHOR,v.revision,"IN_REVIEW");
  expectError(()=>c2.transition(v.id,REVIEWER,v.revision,"APPROVED"),"EVIDENCE_OR_RIGHTS_MISSING");
  assert.equal(c2.read(v.id).state,"IN_REVIEW");
});

test("version history is ordered and changes do not mutate previous snapshots",()=>{
  const c=new SyntheticCMS();
  const initial=c.revisions(ID)[0];
  const r=c.edit(ID,AUTHOR,1,{title:"模拟第二稿：仅本地内存"});
  const versions=c.revisions(ID);
  assert.equal(versions.length,2);
  assert.equal(initial.revision,1);
  assert.notEqual(initial.title,r.title);
  assert.equal(versions[0].title,initial.title);
  assert.equal(versions[1].title,r.title);
  const entries=c.audit(ID);
  assert.equal(entries.length,1);
  assert.equal(entries[0].actor,AUTHOR);
});

test("document state filters derive exclusively from memory, no user data or network",()=>{
  const c=new SyntheticCMS();
  const all=c.list();
  assert.equal(all.filter(r=>r.state==="IN_REVIEW").length,0);
  c.transition(ID,AUTHOR,1,"IN_REVIEW");
  assert.equal(c.list().filter(r=>r.state==="IN_REVIEW").length,1);
  assert.equal(new SyntheticCMS().list().filter(r=>r.state==="IN_REVIEW").length,0);
});
