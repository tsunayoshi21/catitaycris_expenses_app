document.addEventListener('DOMContentLoaded', () => {
  function hashString(s){ let h = 0; for(let i=0;i<s.length;i++){ h = ((h<<5)-h) + s.charCodeAt(i); h|=0; } return h; }
  function colorForCategory(cat){ const hue = Math.abs(hashString(cat||'')) % 360; return `hsl(${hue} 70% 55%)`; }
  function peso(v){ try{ return new Intl.NumberFormat('es-CL', {style:'currency', currency:'CLP', maximumFractionDigits:0}).format(v||0);}catch{ return v; } }

  async function fetchTx(){
    const fromFilters = (window.Filters?.getQueryString && window.Filters.getQueryString()) || '';
    const qs = fromFilters;
    console.log('Fetching transactions with query:', qs);
    const url = '/api/transactions' + (qs? ('?' + qs) : '');
    const r = await fetch(url);
    if(r.status === 401){ window.location = '/login'; return []; }
    return await r.json();
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

    const barCfg = { type:'bar', data:{ labels, datasets:[{ label:'CLP', data: values, backgroundColor: colors }]}, options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } } } };
    const pieCfg = { type:'doughnut', data:{ labels, datasets:[{ data: values, backgroundColor: colors }]}, options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } } } };

    const barCanvas = document.getElementById('catChart');
    const pieCanvas = document.getElementById('pieChart');
    if(!barCanvas || !pieCanvas) return;
    const barCtx = barCanvas.getContext('2d');
    const pieCtx = pieCanvas.getContext('2d');
    if(barChart){ barChart.destroy(); }
    if(pieChart){ pieChart.destroy(); }
    // eslint-disable-next-line no-undef
    barChart = new Chart(barCtx, barCfg);
    // eslint-disable-next-line no-undef
    pieChart = new Chart(pieCtx, pieCfg);
    updateLegend(labels, colors, values);
  }

  // Usar Filters global para sincronización con backend únicamente (sin tocar la URL)
  const controller = window.Filters.init({ onChange: () => { render(); }, syncURL: false });
  // Primera carga
  render();
});
