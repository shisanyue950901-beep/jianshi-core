import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const JSON_BASE = "https://pypi.org/pypi";
const sleep = (ms:number)=>new Promise((resolve)=>setTimeout(resolve,ms));

async function sha256(value: unknown): Promise<string> {
  const bytes=new TextEncoder().encode(JSON.stringify(value));
  const digest=await crypto.subtle.digest("SHA-256",bytes);
  return Array.from(new Uint8Array(digest))
    .map((b)=>b.toString(16).padStart(2,"0")).join("");
}

function xmlDecode(value:string):string {
  return value
    .replaceAll("&amp;","&")
    .replaceAll("&lt;","<")
    .replaceAll("&gt;",">")
    .replaceAll("&quot;",'"')
    .replaceAll("&#39;","'");
}

function tag(block:string,name:string):string|null {
  const m=block.match(new RegExp("<"+name+"(?:\\s[^>]*)?>(?:<!\\[CDATA\\[)?([\\s\\S]*?)(?:\\]\\]>)?<\\/"+name+">","i"));
  return m?xmlDecode(m[1].trim()):null;
}

function parseFeed(xml:string,maxItems:number):Array<{title:string,link:string}> {
  const items=[...xml.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)]
    .slice(0,maxItems);
  return items.map((m)=>{
    const block=m[1];
    return {title:tag(block,"title")||"",link:tag(block,"link")||""};
  }).filter((x)=>x.title||x.link);
}

function normalizeName(value:string):string|null {
  const x=value.trim();
  if(!/^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,198}[A-Za-z0-9])?$/.test(x)) return null;
  return x;
}

function projectNameFromItem(item:{title:string,link:string},kind:string):string|null {
  try{
    const u=new URL(item.link);
    const parts=u.pathname.split("/").filter(Boolean);
    if(parts[0]==="project"&&parts[1]) return normalizeName(decodeURIComponent(parts[1]));
  }catch{}
  if(kind==="pypi_newest") return normalizeName(item.title);
  const first=item.title.split(/\s+/)[0]||"";
  return normalizeName(first);
}

const CATEGORY_RULES: Array<[string,RegExp]> = [
  ["AI_AGENT",/\b(agent|agents|agentic|rag|llm|openai|anthropic|langchain|langgraph|ollama|embedding|vector)\b/i],
  ["AUTOMATION",/\b(automation|workflow|scheduler|orchestrat|browser automation|robotic|rpa)\b/i],
  ["DATA_ANALYTICS",/\b(analytics|etl|data pipeline|dataframe|database|warehouse|observability|monitoring)\b/i],
  ["SAAS_INFRA",/\b(saas|billing|subscription|stripe|auth|authentication|multi[- ]?tenant|webhook)\b/i],
  ["ECOMMERCE",/\b(ecommerce|e-commerce|shopify|woocommerce|amazon seller|marketplace)\b/i],
  ["CREATOR_MEDIA",/\b(creator|newsletter|youtube|podcast|video|subtitle|social media)\b/i],
  ["MARKETING_GROWTH",/\b(marketing|seo|affiliate|lead generation|crm|email campaign|growth)\b/i],
  ["DEVTOOLS",/\b(cli|sdk|developer tool|testing|debug|api client|codegen|linter|formatter)\b/i],
];

function candidateCategories(info:Record<string,any>):string[] {
  const text=[
    info.name,info.summary,
    Array.isArray(info.keywords)?info.keywords.join(" "):info.keywords,
    ...(Array.isArray(info.classifiers)?info.classifiers:[]),
  ].filter(Boolean).join(" ");
  return CATEGORY_RULES.filter(([,re])=>re.test(text)).map(([name])=>name);
}

async function fetchJson(name:string):Promise<any> {
  const response=await fetch(`${JSON_BASE}/${encodeURIComponent(name)}/json`,{
    headers:{
      "accept":"application/json",
      "user-agent":"JianShi/0.1 PyPI-metadata-signal (https://jianshi-bua.pages.dev)"
    },
    signal:AbortSignal.timeout(20000),
  });
  if(!response.ok) throw new Error(`PYPI_JSON_HTTP_${response.status}`);
  return await response.json();
}

Deno.serve(async (req:Request)=>{
  if(req.method!=="POST"){
    return new Response(JSON.stringify({error:"POST_REQUIRED"}),{status:405,headers:{"content-type":"application/json"}});
  }

  const supabaseUrl=Deno.env.get("SUPABASE_URL");
  const serviceKey=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if(!supabaseUrl||!serviceKey){
    return new Response(JSON.stringify({error:"SERVER_CONFIG_MISSING"}),{status:500,headers:{"content-type":"application/json"}});
  }

  const admin=createClient(supabaseUrl,serviceKey,{auth:{persistSession:false,autoRefreshToken:false}});

  const {data:source,error:sourceError}=await admin
    .from("source_policy_effective_v01")
    .select("source_id,code,source_status,auto_collect,source_redisplay_allowed,commercial_use_allowed,automated_collection_allowed,redisplay_allowed")
    .eq("code","pypi").single();

  if(sourceError||!source){
    return new Response(JSON.stringify({error:"SOURCE_NOT_FOUND"}),{status:500,headers:{"content-type":"application/json"}});
  }

  const allowed=
    source.source_status==="GREEN" &&
    source.auto_collect===true &&
    source.source_redisplay_allowed===true &&
    source.commercial_use_allowed===true &&
    source.automated_collection_allowed===true &&
    source.redisplay_allowed===true;

  if(!allowed){
    return new Response(JSON.stringify({error:"SOURCE_POLICY_GATE_BLOCKED"}),{status:403,headers:{"content-type":"application/json"}});
  }

  const {data:queries,error:queryError}=await admin
    .from("external_signal_queries")
    .select("id,code,query_spec")
    .eq("source_id",source.source_id)
    .eq("query_type","PYPI_RSS")
    .eq("enabled",true)
    .order("code");

  if(queryError||!queries?.length){
    return new Response(JSON.stringify({error:"NO_PYPI_QUERIES"}),{status:500,headers:{"content-type":"application/json"}});
  }

  const {data:run,error:runError}=await admin.from("pipeline_runs").insert({
    source_id:source.source_id,
    run_type:"PYPI_SIGNAL_COLLECTOR",
    status:"RUNNING",
    started_at:new Date().toISOString(),
    quality_gate_status:"PENDING",
  }).select("id").single();

  if(runError||!run){
    return new Response(JSON.stringify({error:"RUN_CREATE_FAILED"}),{status:500,headers:{"content-type":"application/json"}});
  }

  let rssItems=0;
  let metadataAttempts=0;
  let metadataSuccess=0;
  let parserErrors=0;
  let newSnapshots=0;
  const discovered=new Map<string,Set<string>>();

  try{
    for(const q of queries as any[]){
      const feedUrl=String(q.query_spec?.feed_url||"");
      const maxItems=Math.max(10,Math.min(60,Number(q.query_spec?.max_items||40)));
      if(!feedUrl.startsWith("https://pypi.org/rss/")) continue;

      const response=await fetch(feedUrl,{
        headers:{"accept":"application/rss+xml, application/xml, text/xml","user-agent":"JianShi/0.1 PyPI-RSS-signal"},
        signal:AbortSignal.timeout(20000),
      });
      if(!response.ok) throw new Error(`PYPI_RSS_HTTP_${response.status}`);

      const items=parseFeed(await response.text(),maxItems);
      rssItems+=items.length;
      for(const item of items){
        const name=projectNameFromItem(item,String(q.code));
        if(!name){parserErrors+=1;continue;}
        const hit=discovered.get(name.toLowerCase())??new Set<string>();
        hit.add(String(q.code));
        discovered.set(name.toLowerCase(),hit);
      }
    }

    const names=[...discovered.keys()].slice(0,60);
    const normalized:Array<Record<string,any>>=[];

    for(let i=0;i<names.length;i+=5){
      const batch=names.slice(i,i+5);
      const results=await Promise.all(batch.map(async(name)=>{
        metadataAttempts+=1;
        try{
          const payload=await fetchJson(name);
          metadataSuccess+=1;
          return payload;
        }catch{
          return null;
        }
      }));

      for(const payload of results){
        if(!payload?.info?.name) continue;
        const info=payload.info as Record<string,any>;
        const name=String(info.name);
        const categories=candidateCategories(info);
        const projectUrls=(info.project_urls&&typeof info.project_urls==="object")
          ? Object.fromEntries(Object.entries(info.project_urls).slice(0,12))
          : {};
        const classifiers=Array.isArray(info.classifiers)
          ? info.classifiers.filter((x:any)=>typeof x==="string").slice(0,25)
          : [];
        const keywordCount=Array.isArray(info.keywords)
          ? info.keywords.length
          : (typeof info.keywords==="string"&&info.keywords.trim()?info.keywords.split(/[ ,]+/).filter(Boolean).length:0);

        normalized.push({
          source_external_id:name,
          title:name,
          source_url:`https://pypi.org/project/${encodeURIComponent(name)}/`,
          metadata:{
            latest_version:info.version??null,
            requires_python:info.requires_python??null,
            license_expression:info.license_expression??null,
            classifiers,
            project_urls:projectUrls,
            keyword_count:keywordCount,
            candidate_categories:categories,
            candidate_match:categories.length>0,
            full_description_stored:false,
            deprecated_downloads_used:false,
          },
          candidate_categories:categories,
        });
      }

      if(i+5<names.length) await sleep(180);
    }

    const successRate=metadataAttempts?metadataSuccess/metadataAttempts:0;
    if(normalized.length<20||successRate<0.80){
      throw new Error(`QUALITY_GATE_FAILED normalized=${normalized.length} metadata_success_rate=${successRate.toFixed(3)}`);
    }

    const entityRows=normalized.map((row)=>({
      source_id:source.source_id,
      source_external_id:row.source_external_id,
      entity_type:"PYPI_PACKAGE",
      title:row.title,
      source_url:row.source_url,
      metadata:row.metadata,
      last_seen_at:new Date().toISOString(),
      updated_at:new Date().toISOString(),
    }));

    const {data:upserted,error:upsertError}=await admin
      .from("external_signal_entities")
      .upsert(entityRows,{onConflict:"source_id,source_external_id"})
      .select("id,source_external_id");
    if(upsertError) throw upsertError;

    const idByName=new Map((upserted??[]).map((x:any)=>[String(x.source_external_id).toLowerCase(),x.id]));
    const queryIdByCode=new Map((queries as any[]).map((q:any)=>[String(q.code),q.id]));

    const discoveryRows:Array<Record<string,any>>=[];
    for(const [lowerName,codes] of discovered.entries()){
      const entityId=idByName.get(lowerName);
      if(!entityId) continue;
      for(const code of codes){
        const queryId=queryIdByCode.get(code);
        if(queryId) discoveryRows.push({entity_id:entityId,query_id:queryId,last_seen_at:new Date().toISOString()});
      }
    }
    if(discoveryRows.length){
      const {error}=await admin.from("external_signal_discoveries")
        .upsert(discoveryRows,{onConflict:"entity_id,query_id"});
      if(error) throw error;
    }

    const snapshots=[];
    for(const row of normalized){
      const entityId=idByName.get(String(row.source_external_id).toLowerCase());
      if(!entityId) continue;
      const metrics={
        candidate_match:row.candidate_categories.length>0?1:0,
        candidate_category_count:row.candidate_categories.length,
      };
      snapshots.push({
        entity_id:entityId,
        source_id:source.source_id,
        observed_at:new Date().toISOString(),
        snapshot_hash:await sha256({version:row.metadata.latest_version,categories:row.candidate_categories}),
        metrics,
        metadata:{
          latest_version:row.metadata.latest_version,
          candidate_categories:row.candidate_categories,
          full_description_stored:false,
          deprecated_downloads_used:false,
        },
      });
    }

    if(snapshots.length){
      const {data:inserted,error}=await admin.from("external_signal_snapshots")
        .upsert(snapshots,{onConflict:"entity_id,snapshot_hash",ignoreDuplicates:true})
        .select("id");
      if(error) throw error;
      newSnapshots=inserted?.length??0;
    }

    const candidateCount=normalized.filter((x)=>x.candidate_categories.length>0).length;
    const categoryCounts:Record<string,number>={};
    for(const row of normalized){
      for(const cat of row.candidate_categories) categoryCounts[cat]=(categoryCounts[cat]??0)+1;
    }

    await admin.from("pipeline_runs").update({
      status:"SUCCESS",
      finished_at:new Date().toISOString(),
      fetched_count:rssItems,
      accepted_count:normalized.length,
      parser_error_count:parserErrors,
      quality_gate_status:"PASS",
      quality_gate_reason:{
        rss_items:rssItems,
        unique_discovered:discovered.size,
        metadata_attempts:metadataAttempts,
        metadata_success:metadataSuccess,
        metadata_success_rate:Number(successRate.toFixed(4)),
        candidate_count:candidateCount,
        candidate_match_rate:Number((candidateCount/normalized.length).toFixed(4)),
        candidate_categories:categoryCounts,
        new_snapshots:newSnapshots,
        bigquery_used:false,
        package_content_stored:false,
        deprecated_json_downloads_used:false,
        source_role:"TECHNICAL_SUPPLY_DISCOVERY_SHADOW_ONLY",
        scoring_changed:false,
      },
    }).eq("id",run.id);

    await admin.from("data_sources").update({last_success_at:new Date().toISOString()}).eq("id",source.source_id);

    return new Response(JSON.stringify({
      ok:true,
      rss_items:rssItems,
      unique_discovered:discovered.size,
      accepted_packages:normalized.length,
      metadata_success_rate:Number(successRate.toFixed(4)),
      candidate_count:candidateCount,
      candidate_match_rate:Number((candidateCount/normalized.length).toFixed(4)),
      candidate_categories:categoryCounts,
      new_snapshots:newSnapshots,
      bigquery_used:false,
      package_content_stored:false,
      scoring_changed:false,
    }),{status:200,headers:{"content-type":"application/json"}});
  }catch(error){
    await admin.from("pipeline_runs").update({
      status:"FAILED",
      finished_at:new Date().toISOString(),
      fetched_count:rssItems,
      accepted_count:metadataSuccess,
      parser_error_count:parserErrors,
      quality_gate_status:"FAIL",
      quality_gate_reason:{
        error:String(error),
        bigquery_used:false,
        package_content_stored:false,
        scoring_changed:false,
      },
    }).eq("id",run.id);

    return new Response(JSON.stringify({error:"COLLECTOR_FAILED",detail:String(error)}),{
      status:500,headers:{"content-type":"application/json"}
    });
  }
});
