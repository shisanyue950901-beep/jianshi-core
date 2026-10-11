/* F2.1 G1-F: synthetic, volatile CMS workflow contract. No network, storage, Auth or actual publication.
 * Model is testable in Node and browser; never treat the actor selector as authentication.
 */
(function(root, factory) {
  "use strict";
  const exports = factory();
  if (typeof module === "object" && module.exports) module.exports = exports;
  else root.F21F_MODEL = exports;
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  "use strict";
  const roles = Object.freeze({
    TEST_AUTHOR_A:"EDITOR", TEST_AUTHOR_B:"EDITOR",
    TEST_REVIEWER_B:"REVIEWER", TEST_PUBLISHER_C:"PUBLISHER", TEST_VISITOR:"VISITOR"
  });
  const paths = Object.freeze({
    DRAFT:["IN_REVIEW"], IN_REVIEW:["APPROVED","REJECTED"], APPROVED:["PUBLISHED"],
    REJECTED:["DRAFT"], PUBLISHED:["UNPUBLISHED"], UNPUBLISHED:["IN_REVIEW"]
  });
  function fail(code) { const err = new Error(code); err.code = code; throw err; }
  function clone(data) { return JSON.parse(JSON.stringify(data)); }
  function ensure(condition, code) { if (!condition) fail(code); }
  function normalizeText(raw, maximum, label) {
    ensure(typeof raw === "string" && raw.trim().length > 0 && raw.trim().length <= maximum, "INVALID_" + label);
    return raw.trim();
  }
  function allowedSource(src) {
    if (!src || typeof src !== "object" || Array.isArray(src)) return false;
    const keys = Object.keys(src);
    return src.kind === "AUTHOR_ORIGINAL" && keys.length === 2 &&
      keys.includes("description") &&
      typeof src.description === "string" && src.description.trim().length > 0 &&
      src.description.length <= 300;
  }
  const sampleRecords = Object.freeze([
    {
      id:"SYNTHETIC_G1F_01", type:"SOLUTION_GUIDE", author:"TEST_AUTHOR_A", title:"合成示例：企业自动化方案",
      summary:"这是一条纯合成的内容治理测试记录，不能当成真实客户案例。",
      body:"问题：如何定义自动化项目的输入和验收？\n步骤：描述流程、人工复核、验证异常。\n结果：只有演示说明，不存在真实交付。",
      category:"方案指南", state:"DRAFT", revision:1,
      factsChecked:false, rightsConfirmed:false,
      sources:[{kind:"AUTHOR_ORIGINAL",description:"原创合成测试材料，不含真实客户"}],
      media:[{id:"SYNTHETIC_MEDIA_01",type:"IMAGE",name:"概念封面（未上传）",license:"UNKNOWN",scan:"PENDING"}],
      reviewer:null, publishedAt:null, privateNote:"合成内部审稿说明，禁止进入公开投影"
    },
    {
      id:"SYNTHETIC_G1F_02", type:"COURSE", author:"TEST_AUTHOR_B", title:"合成示例：AI 视频课程大纲",
      summary:"内部教学内容结构测试，不对应已经上线的视频课程。",
      body:"第一节：课程目标。\n第二节：样板练习。\n第三节：版权与素材检查。\n没有上传视频或提供付费课程。",
      category:"AIGC 学院", state:"DRAFT", revision:1,
      factsChecked:false, rightsConfirmed:true,
      sources:[{kind:"AUTHOR_ORIGINAL",description:"纯合成课程示例"}],
      media:[], reviewer:null, publishedAt:null,
      privateNote:"内部虚构课程，不对公网发布"
    }
  ]);
  class SyntheticCMS {
    constructor(fixtures) {
      const input = fixtures === undefined ? sampleRecords : fixtures;
      ensure(Array.isArray(input) && input.length <= 20, "INVALID_FIXTURES");
      this.records = new Map();
      this.history = new Map();
      this.events = [];
      this.sequence = 0;
      input.forEach((r) => {
        ensure(typeof r.id === "string" && r.id.startsWith("SYNTHETIC_"), "NOT_SYNTHETIC");
        ensure(!this.records.has(r.id) && roles[r.author] === "EDITOR" && r.state === "DRAFT", "INVALID_FIXTURE");
        const doc = clone(r);
        this.records.set(r.id, doc);
        this.history.set(r.id,[this._version(doc)]);
      });
    }
    _version(record) {
      return { revision:record.revision, state:record.state, title:record.title,
        summary:record.summary, body:record.body, factsChecked:record.factsChecked,
        rightsConfirmed:record.rightsConfirmed, media:clone(record.media) };
    }
    _get(id) { const r=this.records.get(id); ensure(r!==undefined,"NOT_FOUND"); return r; }
    _expected(r,expected) { ensure(Number.isInteger(expected) && expected===r.revision,"STALE_REVISION"); }
    _save(r,actor,event) {
      r.revision++;
      this.history.get(r.id).push(this._version(r));
      this.events.push(Object.freeze({
        seq:++this.sequence, id:r.id, actor, action:event, revision:r.revision, state:r.state
      }));
      return clone(r);
    }
    list() { return Array.from(this.records.values()).map(clone); }
    read(id) { return clone(this._get(id)); }
    revisions(id) { this._get(id); return clone(this.history.get(id)); }
    audit(id) { this._get(id); return this.events.filter((e)=>e.id===id).map(clone); }
    edit(id,actor,expected,patch) {
      const r=this._get(id);
      this._expected(r,expected);
      ensure(roles[actor]==="EDITOR" && r.author===actor,"OWNER_REQUIRED");
      ensure(r.state==="DRAFT","DRAFT_LOCKED");
      ensure(patch && typeof patch==="object" && !Array.isArray(patch),"INVALID_PATCH");
      const allowed=["title","summary","body","factsChecked","rightsConfirmed","mediaLicense","mediaScan"];
      ensure(Object.keys(patch).every((key)=>allowed.includes(key)),"UNKNOWN_FIELD");
      if ("title" in patch) r.title=normalizeText(patch.title,140,"TITLE");
      if ("summary" in patch) r.summary=normalizeText(patch.summary,1600,"SUMMARY");
      if ("body" in patch) r.body=normalizeText(patch.body,3000,"BODY");
      if ("factsChecked" in patch) {ensure(typeof patch.factsChecked==="boolean","INVALID_FACTS");r.factsChecked=patch.factsChecked;}
      if ("rightsConfirmed" in patch) {ensure(typeof patch.rightsConfirmed==="boolean","INVALID_RIGHTS");r.rightsConfirmed=patch.rightsConfirmed;}
      if ("mediaLicense" in patch || "mediaScan" in patch) {
        ensure(r.media.length > 0,"MEDIA_MISSING");
        if ("mediaLicense" in patch) {
          ensure(["UNKNOWN","OWNED","LICENSED"].includes(patch.mediaLicense),"INVALID_MEDIA_LICENSE");
          r.media[0].license=patch.mediaLicense;
        }
        if ("mediaScan" in patch) {
          ensure(["PENDING","PASSED","FAILED"].includes(patch.mediaScan),"INVALID_MEDIA_SCAN");
          r.media[0].scan=patch.mediaScan;
        }
      }
      return this._save(r,actor,"EDIT");
    }
    transition(id,actor,expected,next) {
      const r=this._get(id);
      this._expected(r,expected);
      ensure((paths[r.state]||[]).includes(next),"ILLEGAL_TRANSITION");
      if (next==="IN_REVIEW" || next==="DRAFT") {
        ensure(roles[actor]==="EDITOR" && r.author===actor,"OWNER_REQUIRED");
      } else if (next==="APPROVED"||next==="REJECTED") {
        ensure(roles[actor]==="REVIEWER" && actor!==r.author,"INDEPENDENT_REVIEW_REQUIRED");
      } else if (next==="PUBLISHED"||next==="UNPUBLISHED") {
        ensure(roles[actor]==="PUBLISHER" && actor!==r.author,"PUBLISHER_REQUIRED");
      }
      if (next==="APPROVED"||next==="PUBLISHED") {
        ensure(r.factsChecked && r.rightsConfirmed && r.sources.length>0 &&
          r.sources.every(allowedSource),"EVIDENCE_OR_RIGHTS_MISSING");
        ensure(r.media.every(m=>["OWNED","LICENSED"].includes(m.license)&&m.scan==="PASSED"),
          "MEDIA_RIGHTS_NOT_READY");
      }
      if (next==="APPROVED"||next==="REJECTED") r.reviewer=actor;
      if (next==="IN_REVIEW") r.reviewer=null;
      if (next==="PUBLISHED") {
        ensure(r.reviewer && r.reviewer!==r.author,"REVIEWER_REQUIRED");
        r.publishedAt="SYNTHETIC_ONLY";
      }
      if (next==="UNPUBLISHED") r.publishedAt=null;
      r.state=next;
      return this._save(r,actor,next);
    }
    publicProjection(id) {
      const r=this._get(id);
      ensure(r.state==="PUBLISHED","NOT_PUBLISHED");
      ensure(r.factsChecked && r.rightsConfirmed,"EVIDENCE_OR_RIGHTS_MISSING");
      ensure(r.sources.every(allowedSource),"UNSAFE_SOURCE");
      return {content_id:r.id,content_type:r.type,title:r.title,summary:r.summary,
        category:r.category,revision:r.revision,
        source_refs:r.sources.map(s=>({kind:s.kind,description:s.description})),
        published_at:"SYNTHETIC_NOT_REAL"};
    }
    publicList() {
      return this.list().filter(r=>r.state==="PUBLISHED").map(r=>this.publicProjection(r.id));
    }
  }
  return Object.freeze({SyntheticCMS,roles,paths});
});
