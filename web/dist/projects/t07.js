(() => {
  'use strict';
  const selects = Object.fromEntries(['category','verdict','evidence_level','sort'].map(k => [k,document.getElementById(k)]));
  const holder = document.getElementById('project-list');
  const cards = Array.from(holder.querySelectorAll('[data-project]'));
  const params = new URLSearchParams(location.search);
  const allowedSort = ['total_score','mrr','last_30d'];
  for (const k of ['category','verdict','evidence_level']) {
    if (Array.from(selects[k].options).some(opt => opt.value === params.get(k))) selects[k].value = params.get(k);
  }
  if (allowedSort.includes(params.get('sort'))) selects.sort.value = params.get('sort');
  const display = () => {
    const [category,verdict,evidence,sort] = ['category','verdict','evidence_level','sort'].map(k=>selects[k].value);
    const qs = new URLSearchParams();
    if (category) qs.set('category',category);
    if (verdict) qs.set('verdict',verdict);
    if (evidence) qs.set('evidence_level',evidence);
    if (sort !== 'total_score') qs.set('sort',sort);
    history.replaceState(null,'',location.pathname + (qs.size ? '?' + qs.toString() : ''));
    const field = ({total_score:'score',mrr:'mrr',last_30d:'last30'})[sort];
    cards.sort((a,b) => {
      const av = a.dataset[field] === '' ? -Infinity : Number(a.dataset[field]);
      const bv = b.dataset[field] === '' ? -Infinity : Number(b.dataset[field]);
      return bv-av || a.dataset.name.localeCompare(b.dataset.name,'zh-CN');
    });
    let visible=0;
    for (const el of cards) {
      const pass = (!category || el.dataset.category===category)
        && (!verdict || el.dataset.verdict===verdict)
        && (!evidence || el.dataset.evidence===evidence);
      el.hidden = !pass;
      if (pass) visible++;
      holder.appendChild(el);
    }
    document.getElementById('result-count').textContent = '当前显示 '+visible+' / '+cards.length+' 个项目';
    document.getElementById('empty-message').hidden = visible !== 0;
  };
  Object.values(selects).forEach(el => el.addEventListener('change',display));
  window.addEventListener('popstate', () => { location.reload(); });
  display();
})();
