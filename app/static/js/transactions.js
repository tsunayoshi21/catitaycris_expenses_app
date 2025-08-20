document.addEventListener('DOMContentLoaded', () => {
  let table;
  function peso(v){
    try{ return new Intl.NumberFormat('es-CL', {style:'currency', currency:'CLP', maximumFractionDigits:0}).format(v||0); }catch{ return v; }
  }
  function buildParams(){
    const p = new URLSearchParams();
    const y = document.getElementById('year')?.value; if(y) p.set('year', y);
    const m = document.getElementById('month')?.value; if(m) p.set('month', m);
    const w = document.getElementById('week')?.value; if(w) p.set('week', w);
    const d = document.getElementById('day')?.value; if(d) p.set('day', d);
    const t = document.getElementById('type')?.value; if(t) p.set('type', t);
    const c = document.getElementById('category')?.value; if(c) p.set('category', c);
    const q = document.getElementById('q')?.value; if(q) p.set('q', q);
    return p.toString();
  }
  async function fetchData(){
    try{
      const qs = buildParams();
      const res = await fetch('/api/transactions' + (qs? ('?' + qs) : ''));
      if(res.status === 401){ window.location = '/login'; return []; }
      if(!res.ok){ console.error('API error', res.status); showErr('Error cargando transacciones ('+res.status+').'); return []; }
      return await res.json();
    }catch(e){
      console.error(e);
      showErr('No se pudo conectar al servidor.');
      return [];
    }
  }
  function showErr(msg){
    const el = document.getElementById('err');
    if(!el) return;
    el.textContent = msg; el.classList.remove('d-none');
  }
  function toRow(t){
    const dt = new Date(t.date);
    const ts = isNaN(dt.getTime()) ? 0 : dt.getTime();
    return [
      dt.toLocaleString(),
      Number(t.amount||0),
      t.merchant||'',
      t.type||'',
      t.category||'',
      t.description||'',
      t.id,
      ts // hidden timestamp for proper sorting
    ];
  }
  async function saveChange(id, field, value){
    try{
      const res = await fetch('/api/update_transaction', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({id, [field]: value})
      });
      if(res.status === 401){ window.location = '/login'; return; }
      if(!res.ok){ showErr('No se pudo guardar el cambio.'); }
    }catch(e){ showErr('No se pudo guardar el cambio.'); }
  }
  async function reload(){
    const data = await fetchData();
    const rows = data.map(toRow);
    table.clear().rows.add(rows).draw();
  }
  async function init(){
    const data = await fetchData();
    const rows = data.map(toRow);
    table = $('#txTable').DataTable({
      data: rows,
      columns: [
        { title: 'Fecha' },
        { title: 'Monto' },
        { title: 'Comercio' },
        { title: 'Tipo' },
        { title: 'Categoría' },
        { title: 'Descripción' },
        { title: 'ID', visible:false },
        { title: 'TS', visible:false }
      ],
      order: [[0, 'desc']],
      columnDefs: [
        { targets: 0, orderData: 7 },
        { targets: 1, render: function(data, type){
            if(type === 'display') return peso(Number(data)||0);
            return data;
          }
        }
      ]
    });
    // Inline editing for category & description
    $('#txTable tbody').on('dblclick','td', function(){
      const cell = table.cell(this);
      const idx = cell.index().column;
      if(idx !== 4 && idx !== 5) return; // only category & description
      const rowData = table.row(this).data();
      const id = rowData[6];
      const current = cell.data();
      const input = $('<input type="text" class="form-control form-control-sm"/>').val(current);
      $(this).empty().append(input);
      input.focus();
      input.on('blur keydown', async (e)=>{
        if(e.type==='blur' || e.key==='Enter'){
          const val = input.val();
          cell.data(val).draw();
          await saveChange(id, idx===4?'category':'description', val);
        }
      });
    });

    ['year','month','week','day','type','category','q'].forEach(id=>{
      const el = document.getElementById(id);
      if(!el) return;
      el.addEventListener('input', reload);
    });
    const resetBtn = document.getElementById('resetFilters');
    if(resetBtn){
      resetBtn.addEventListener('click', function(){
        ['year','month','week','day','type','category','q'].forEach(id=>{
          const el = document.getElementById(id);
          if(!el) return;
          if(el.tagName === 'SELECT') el.selectedIndex = 0; else el.value = '';
        });
        reload();
      });
    }
  }
  init();
});
