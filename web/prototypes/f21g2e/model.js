/* G2-E isolated editorial workbench. ALL data is synthetic and transient.
   Never import this into Cloudflare public builds or real Supabase CMS. */
(function(factory){
  'use strict';
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(typeof window==='object')window.JianShiCmsSimulation=api;
})(function(){
 'use strict';
 const STATES=Object.freeze({DRAFT:'草稿',IN_REVIEW:'待审核',APPROVED:'已审核',REJECTED:'已驳回',PUBLISHED:'内部已发布模拟',UNPUBLISHED:'已撤回'});
 const OWN='SYNTHETIC_AUTHOR',REV='SYNTHETIC_REVIEWER',PUB='SYNTHETIC_PUBLISHER';
 class Refused extends Error{constructor(code){super(code);this.code=code;}}
 class Demo{
  constructor(){
   this.state='DRAFT';this.revision=3;this.actor=OWN;
   this.revisions=[
    {rev:1,title:'合成指南初稿',rights:false,facts:false},
    {rev:2,title:'合成指南第二稿',rights:true,facts:true},
    {rev:3,title:'合成指南最新稿',rights:true,facts:true}
   ];
   this.events=[{op:'CREATE',rev:1},{op:'EDIT',rev:2},{op:'EDIT',rev:3}];
   this.snapshots=[];this.lastReviewer=null;
  }
  apply(operation){
   const current=this.revisions[this.revisions.length-1];
   let next,actor;
   if(operation==='RESTORE'){
     if(this.state!=='DRAFT'&&this.state!=='REJECTED')throw new Refused('CMS_RESTORE_REQUIRES_DRAFT');
     if(this.snapshots.some(s=>s.state==='STAGED'))throw new Refused('CMS_ACTIVE_PUBLICATION_BLOCKS_RESTORE');
     next={...this.revisions[0],rev:this.revision+1,rights:false,facts:false};
     actor=OWN;this.state='DRAFT';this.lastReviewer=null;
   }else if(operation==='EDIT'){
     if(this.state!=='DRAFT')throw new Refused('CMS_DRAFT_LOCKED');
     next={...current,rev:this.revision+1,rights:true,facts:true};
     actor=OWN;
   }else if(operation==='SUBMIT'){
     if(this.state!=='DRAFT')throw new Refused('CMS_ILLEGAL_TRANSITION');
     next={...current,rev:this.revision+1};
     actor=OWN;this.state='IN_REVIEW';
   }else if(operation==='APPROVE'||operation==='REJECT'){
     if(this.state!=='IN_REVIEW')throw new Refused('CMS_ILLEGAL_TRANSITION');
     if(operation==='APPROVE'&&!(current.rights&&current.facts))
       throw new Refused('CMS_EVIDENCE_OR_RIGHTS_MISSING');
     next={...current,rev:this.revision+1};
     actor=REV;this.state=operation==='APPROVE'?'APPROVED':'REJECTED';this.lastReviewer=REV;
   }else if(operation==='PUBLISH'){
     if(this.state!=='APPROVED')throw new Refused('CMS_ILLEGAL_TRANSITION');
     if(!(current.rights&&current.facts))throw new Refused('CMS_EVIDENCE_OR_RIGHTS_MISSING');
     next={...current,rev:this.revision+1};
     actor=PUB;this.state='PUBLISHED';
     this.snapshots.push({revision:next.rev,state:'STAGED'});
   }else if(operation==='RETRACT'){
     if(this.state!=='PUBLISHED')throw new Refused('CMS_ILLEGAL_TRANSITION');
     next={...current,rev:this.revision+1};actor=PUB;this.state='UNPUBLISHED';
     this.snapshots.forEach(s=>{if(s.state==='STAGED')s.state='RETRACTED';});
   }else if(operation==='RESUBMIT'){
     if(this.state!=='UNPUBLISHED')throw new Refused('CMS_ILLEGAL_TRANSITION');
     next={...current,rev:this.revision+1};actor=OWN;this.state='IN_REVIEW';this.lastReviewer=null;
   }else if(operation==='RETURN_TO_DRAFT'){
     if(this.state!=='REJECTED')throw new Refused('CMS_ILLEGAL_TRANSITION');
     next={...current,rev:this.revision+1};actor=OWN;this.state='DRAFT';
   }else throw new Refused('CMS_UNKNOWN_ACTION');
   this.revision++;
   this.revisions.push(next);
   this.events.push({op:operation,rev:this.revision,actor});
   return this.summary();
  }
  summary(){
   const last=this.revisions[this.revisions.length-1];
   return {state:this.state,stateLabel:STATES[this.state],revision:this.revision,
    title:last.title,rights:last.rights,facts:last.facts,
    events:this.events.map(x=>({...x})),
    versions:this.revisions.map(x=>({...x})),
    snapshots:this.snapshots.map(x=>({...x}))};
  }
 }
 return Object.freeze({Demo,Refused,STATES});
});
