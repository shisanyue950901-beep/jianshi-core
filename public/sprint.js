/* T11: only checkbox completion status, stored locally and never sent to servers. */
(()=>{
  "use strict";
  const PREFIX="jianshi_t11_sprint_check_v1:";
  const boxes=[...document.querySelectorAll("input[type=checkbox][data-t11-check]")];
  const output=document.querySelector("[data-t11-progress]");
  const read=k=>{try{return localStorage.getItem(PREFIX+k)==="1"}catch{return false}};
  const write=(k,v)=>{try{if(v)localStorage.setItem(PREFIX+k,"1");else localStorage.removeItem(PREFIX+k)}catch{}};
  const refresh=()=>{if(output)output.textContent="已完成 "+boxes.filter(x=>x.checked).length+" / "+boxes.length+" 项"};
  boxes.forEach(box=>{
    const key=box.dataset.t11Check;
    if(!/^(week0|week1|week23|week4)-[0-9]{1,2}$/.test(key||""))return;
    box.checked=read(key);
    box.addEventListener("change",()=>{write(key,box.checked);refresh()});
  });
  refresh();
})();
