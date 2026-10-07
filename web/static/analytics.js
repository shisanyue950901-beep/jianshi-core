(()=>{
  const cfg=window.JIANSHI_ANALYTICS_CONFIG||{};
  const endpoint=String(cfg.endpoint||"").trim();
  if(!cfg.enabled||!endpoint) return;

  const OPT_OUT="jianshi_analytics_opt_out";
  const VISITOR="jianshi_visitor_v1";
  const SESSION="jianshi_session_v1";
  const ACQ="jianshi_acquisition_v1";
  const SEEN="jianshi_seen_opportunities_v1";
  const SECOND="jianshi_second_opportunity_v1";
  const ROTATE_MS=90*24*60*60*1000;

  const storageSafe=(storage,key)=>{
    try{return storage.getItem(key)}catch{return null}
  };
  const setSafe=(storage,key,value)=>{
    try{storage.setItem(key,value)}catch{}
  };
  const removeSafe=(storage,key)=>{
    try{storage.removeItem(key)}catch{}
  };
  const uuid=()=>{
    if(globalThis.crypto?.randomUUID) return crypto.randomUUID();
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,c=>{
      const r=Math.random()*16|0,v=c==="x"?r:(r&3|8);
      return v.toString(16);
    });
  };

  const privacyBlocked=()=>{
    if(storageSafe(localStorage,OPT_OUT)==="1") return true;
    if(navigator.globalPrivacyControl===true) return true;
    return navigator.doNotTrack==="1"||window.doNotTrack==="1";
  };

  const visitorId=()=>{
    const now=Date.now();
    try{
      const raw=storageSafe(localStorage,VISITOR);
      if(raw){
        const parsed=JSON.parse(raw);
        if(parsed?.id&&parsed?.created_at&&now-Number(parsed.created_at)<ROTATE_MS){
          return parsed.id;
        }
      }
    }catch{}
    const id=uuid();
    setSafe(localStorage,VISITOR,JSON.stringify({id,created_at:now}));
    return id;
  };

  const sessionId=()=>{
    let id=storageSafe(sessionStorage,SESSION);
    if(!id){id=uuid();setSafe(sessionStorage,SESSION,id)}
    return id;
  };

  const token=v=>{
    const x=String(v||"").trim();
    return /^[A-Za-z0-9._~-]{1,80}$/.test(x)?x:null;
  };

  const referrerDomain=()=>{
    try{
      if(!document.referrer) return null;
      const u=new URL(document.referrer);
      return u.origin===location.origin?null:u.hostname.toLowerCase();
    }catch{return null}
  };

  const acquisition=()=>{
    try{
      const prior=storageSafe(sessionStorage,ACQ);
      if(prior) return JSON.parse(prior);
    }catch{}
    const p=new URLSearchParams(location.search);
    const value={
      referrer_domain:referrerDomain(),
      utm_source:token(p.get("utm_source")),
      utm_medium:token(p.get("utm_medium")),
      utm_campaign:token(p.get("utm_campaign")),
    };
    setSafe(sessionStorage,ACQ,JSON.stringify(value));
    return value;
  };

  const deviceClass=()=>{
    const w=Math.max(document.documentElement.clientWidth||0,window.innerWidth||0);
    if(w<=640) return "MOBILE";
    if(w<=1024) return "TABLET";
    return "DESKTOP";
  };

  const currentSlug=()=>{
    const m=location.pathname.match(/^\/opportunity\/([a-z0-9-]{2,80})\/?$/);
    return m?m[1]:null;
  };

  const send=(eventType,extra={})=>{
    if(privacyBlocked()) return;
    const acq=acquisition();
    const body={
      event_id:uuid(),
      visitor_id:visitorId(),
      session_id:sessionId(),
      event_type:eventType,
      page_path:location.pathname.slice(0,200)||"/",
      opportunity_slug:extra.opportunity_slug||currentSlug(),
      referrer_domain:acq.referrer_domain,
      utm_source:acq.utm_source,
      utm_medium:acq.utm_medium,
      utm_campaign:acq.utm_campaign,
      device_class:deviceClass(),
      metadata:extra.metadata||{},
    };
    fetch(endpoint,{
      method:"POST",
      mode:"cors",
      credentials:"omit",
      keepalive:true,
      headers:{"content-type":"text/plain;charset=UTF-8"},
      body:JSON.stringify(body),
    }).catch(()=>{});
  };

  const markSecondOpportunity=slug=>{
    if(!slug) return;
    let seen=[];
    try{seen=JSON.parse(storageSafe(sessionStorage,SEEN)||"[]")}catch{}
    if(!Array.isArray(seen)) seen=[];
    if(!seen.includes(slug)){
      if(seen.length>=1&&storageSafe(sessionStorage,SECOND)!=="1"){
        setSafe(sessionStorage,SECOND,"1");
        send("SECOND_OPPORTUNITY_VIEW",{opportunity_slug:slug});
      }
      seen=[...seen,slug].slice(-20);
      setSafe(sessionStorage,SEEN,JSON.stringify(seen));
    }
  };

  const classifyHost=host=>{
    if(host==="github.com"||host.endsWith(".github.com")) return "GITHUB";
    if(/(empireflippers|acquire|flippa|microns|feinternational)\./.test(host)) return "MARKETPLACE";
    return "OTHER";
  };

  document.addEventListener("DOMContentLoaded",()=>{
    document.querySelectorAll("[data-analytics-opt-out]").forEach(btn=>{
      btn.addEventListener("click",()=>{
        setSafe(localStorage,OPT_OUT,"1");
        removeSafe(localStorage,VISITOR);
        document.querySelectorAll("[data-analytics-status]").forEach(n=>{
          n.textContent="匿名使用分析已关闭。之后的浏览不会发送行为分析事件。";
        });
      });
    });
    document.querySelectorAll("[data-analytics-opt-in]").forEach(btn=>{
      btn.addEventListener("click",()=>{
        removeSafe(localStorage,OPT_OUT);
        document.querySelectorAll("[data-analytics-status]").forEach(n=>{
          n.textContent="匿名使用分析已开启。不会收集姓名、邮箱、IP 或完整搜索词。";
        });
      });
    });

    if(privacyBlocked()) return;

    send("PAGE_VIEW");

    const slug=currentSlug();
    if(slug){
      send("OPPORTUNITY_DETAIL_VIEW",{opportunity_slug:slug});
      markSecondOpportunity(slug);
    }

    document.addEventListener("click",e=>{
      const a=e.target?.closest?.("a[href]");
      if(!a) return;
      let url;
      try{url=new URL(a.href,location.href)}catch{return}

      if(url.origin===location.origin){
        const m=url.pathname.match(/^\/opportunity\/([a-z0-9-]{2,80})\/?$/);
        if(m){
          send("OPPORTUNITY_CARD_CLICK",{
            opportunity_slug:m[1],
            metadata:{state:a.dataset?.state||undefined},
          });
        }
        return;
      }

      if(url.protocol==="https:"||url.protocol==="http:"){
        send("SOURCE_OUTBOUND_CLICK",{
          opportunity_slug:slug,
          metadata:{target_host:url.hostname.toLowerCase(),target_kind:classifyHost(url.hostname.toLowerCase())},
        });
      }
    },{capture:true});

    const catalogSearch=document.querySelector("[data-catalog-search]");
    if(catalogSearch){
      let timer=null;
      catalogSearch.addEventListener("input",()=>{
        clearTimeout(timer);
        timer=setTimeout(()=>{
          const q=String(catalogSearch.value||"").trim();
          if(!q) return;
          const visible=[...document.querySelectorAll("[data-catalog-grid] [data-card]")]
            .filter(x=>x.style.display!=="none").length;
          send("CATALOG_SEARCH",{metadata:{query_length:q.length,results_count:visible}});
        },700);
      });
    }

    document.querySelectorAll("[data-catalog-filter]").forEach(btn=>{
      btn.addEventListener("click",()=>{
        send("CATALOG_FILTER",{metadata:{filter:btn.dataset.catalogFilter||"all"}});
      });
    });

    let engaged=false;
    setTimeout(()=>{
      if(!engaged&&document.visibilityState==="visible"){
        engaged=true;
        send("ENGAGED_30S",{opportunity_slug:slug});
      }
    },30000);

    let sent50=false,sent90=false;
    const onScroll=()=>{
      const doc=document.documentElement;
      const max=Math.max(1,doc.scrollHeight-window.innerHeight);
      const pct=Math.min(100,Math.round((window.scrollY/max)*100));
      if(!sent50&&pct>=50){sent50=true;send("SCROLL_50",{opportunity_slug:slug})}
      if(!sent90&&pct>=90){sent90=true;send("SCROLL_90",{opportunity_slug:slug});window.removeEventListener("scroll",onScroll)}
    };
    window.addEventListener("scroll",onScroll,{passive:true});
  });
})();
