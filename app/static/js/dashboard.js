document.addEventListener('DOMContentLoaded', () => {
  function hashString(s){
    let h = 0; for(let i=0;i<s.length;i++){ h = ((h<<5)-h) + s.charCodeAt(i); h|=0; }
    return h;
  }
  function colorForCategory(cat){
    const hue = Math.abs(hashString(cat)) % 360;
    return `hsl(${hue} 70% 55%)`;
  }
  async function fetchTx(){
    const p = new URLSearchParams();
    const y = document.getElementById('year').value; if(y) p.set('year', y);
    const m = document.getElementById('month').value; if(m) p.set('month', m);
    const w = document.getElementById('week').value; if(w) p.set('week', w);
    const d = document.getElementById('day').value; if(d) p.set('day', d);
    const t = document.getElementById('type').value; if(t) p.set('type', t);
    const c = document.getElementById('category').value; if(c) p.set('category', c);
    const q = document.getElementById('q').value; if(q) p.set('q', q);
    const r = await fetch('/api/transactions?'+p.toString());
    if(r.status === 401){ window.location = '/login'; return []; }
    return await r.json();
  }
  function peso(v){
    return new Intl.NumberFormat('es-CL', {style:'currency', currency:'CLP', maximumFractionDigits:0}).format(v);
  }
  let barChart; let pieChart;
  function updateLegend(labels, colors, values){
    const el = document.getElementById('legend'); if(!el) return;
    el.innerHTML = '';
    labels.forEach((lab, i)=>{
      const item = document.createElement('div');
      item.className = 'd-flex align-items-center justify-content-between border rounded px-2 py-1';
      const left = document.createElement('div'); left.className = 'd-flex align-items-center gap-2';
      const swatch = document.createElement('span'); swatch.style.cssText = `display:inline-block;width:12px;height:12px;border-radius:50%;background:${colors[i]}`;
      const name = document.createElement('span'); name.textContent = lab;
      const val = document.createElement('span'); val.textContent = peso(values[i]);
      left.appendChild(swatch); left.appendChild(name);
      item.appendChild(left); item.appendChild(val);
      el.appendChild(item);
    });
  }
  async function render(){
    const data = await fetchTx();
    const total = data.reduce((s,t)=> s + (t.amount||0), 0);
    const totalEl = document.getElementById('total'); if(totalEl) totalEl.textContent = peso(total);
    const byCat = {};
    data.forEach(t=>{ const c=(t.category||'otros').toLowerCase(); byCat[c]=(byCat[c]||0)+(t.amount||0); });
    const labels = Object.keys(byCat);
    const values = labels.map(k=> byCat[k]);
    const colors = labels.map(cat=> colorForCategory(cat));
    // Bar chart
    const barCfg = {
      type:'bar',
      data:{ labels, datasets:[{ label:'CLP', data: values, backgroundColor: colors }]},
      options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } } }
    };
    // Pie chart
    const pieCfg = {
      type:'doughnut',
      data:{ labels, datasets:[{ data: values, backgroundColor: colors }]},
      options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } } }
    };
    const barCanvas = document.getElementById('catChart');
    const pieCanvas = document.getElementById('pieChart');
    if(!barCanvas || !pieCanvas) return;
    const barCtx = barCanvas.getContext('2d');
    const pieCtx = pieCanvas.getContext('2d');
    if(barChart){ barChart.destroy(); }
    if(pieChart){ pieChart.destroy(); }
    // Chart is provided globally by Chart.js loaded in the template head
    // eslint-disable-next-line no-undef
    barChart = new Chart(barCtx, barCfg);
    // eslint-disable-next-line no-undef
    pieChart = new Chart(pieCtx, pieCfg);
    updateLegend(labels, colors, values);
  }
  ['year','month','week','day','type','category','q'].forEach(id=> {
    const el = document.getElementById(id);
    if(el) el.addEventListener('input', render);
  });

  const resetBtn = document.getElementById('resetFilters');
  if(resetBtn){
    resetBtn.addEventListener('click', function(){
      ['year','month','week','day','type','category','q'].forEach(id=>{
        const el = document.getElementById(id);
        if(!el) return;
        if(el.tagName === 'SELECT') el.selectedIndex = 0; else el.value = '';
      });
      render();
    });
  }

  render();
});
