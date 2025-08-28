// Utilidad global para gestionar filtros de fecha/búsqueda y sincronizarlos con la URL
// Expuesto como window.Filters para mínimo cambio.
(function(){
  const api = {};
  const TYPES = ['debito','credito','transferencia'];
  const TYPE_LABELS = { debito:'Débito', credito:'Crédito', transferencia:'Transferencia' };
  let state = { dateMode:'ym', year:'', month:'', start:'', end:'', type:[], category:'', q:'' };
  let onChangeCb = null;
  let doSyncURL = true; // nuevo flag

  function qsFromObj(obj){
    const p = new URLSearchParams();
    // Modo de fecha
    if(obj.dateMode){ p.set('dateMode', obj.dateMode); }
    // Año/Mes (mes vacío permitido)
    if(obj.year){ p.set('year', obj.year); }
    if(obj.month !== undefined && obj.month !== null && obj.month !== ''){ p.set('month', obj.month); }
    // Rango de días
    if(obj.start){ p.set('start', obj.start); }
    if(obj.end){ p.set('end', obj.end); }
    // Tipos múltiples
    const arrTypes = Array.isArray(obj.type) ? obj.type : (obj.type ? [obj.type] : []);
    arrTypes.forEach(t => { if(t) p.append('type', t); });
    // Otros
    if(obj.category){ p.set('category', obj.category); }
    if(obj.q){ p.set('q', obj.q); }
    return p;
  }

  function readInputs(){
    const val = id => document.getElementById(id)?.value?.trim() || '';
    const types = Array.from(document.querySelectorAll('input[name="type"]:checked')).map(el=> el.value);
    const mode = document.querySelector('input[name="dateMode"]:checked')?.value || 'ym';
    return {
      dateMode: mode,
      year: val('year'),
      month: val('month'),
      start: val('start'),
      end: val('end'),
      type: types,
      category: val('category'),
      q: val('q'),
    };
  }

  function updateTypeDropdownLabel(){
    const btn = document.getElementById('typeDropdownBtn'); if(!btn) return;
    const selected = Array.from(document.querySelectorAll('input[name="type"]:checked')).map(el=> el.value);
    if(selected.length === TYPES.length){ btn.textContent = 'Todos'; return; }
    if(selected.length === 0){ btn.textContent = 'Ninguno'; return; }
    btn.textContent = selected.map(v=> TYPE_LABELS[v] || v).join(', ');
  }
  function syncTypeDropdownFromCheckboxes(){
    const selected = new Set(Array.from(document.querySelectorAll('input[name="type"]:checked')).map(el=> el.value));
    document.querySelectorAll('.type-option').forEach(a=>{
      const val = a?.dataset?.value;
      const isSel = selected.has(val);
      a.classList.toggle('selected', isSel);
      const cm = a.querySelector('.checkmark');
      if(cm){ cm.classList.toggle('opacity-0', !isSel); }
    });
    updateTypeDropdownLabel();
  }

  function applyToInputs(values){
    const set = (id, v)=>{ const el = document.getElementById(id); if(el) el.value = v ?? ''; };
    // date mode radios
    const mode = values.dateMode || 'ym';
    const rYm = document.getElementById('mode-ym');
    const rRange = document.getElementById('mode-range');
    if(rYm) rYm.checked = (mode === 'ym');
    if(rRange) rRange.checked = (mode === 'range');
    toggleDateModeSections(mode);

    set('year', values.year || '');
    set('month', values.month ?? ''); // mes vacío para Todos
    set('start', values.start || '');
    set('end', values.end || '');

    // tipos (checkboxes ocultos)
    const wanted = new Set(values.type || []);
    document.querySelectorAll('input[name="type"]').forEach(cb=>{
      cb.checked = wanted.size ? wanted.has(cb.value) : false;
    });
    // reflejar en el dropdown
    syncTypeDropdownFromCheckboxes();

    set('category', values.category || '');
    set('q', values.q || '');
  }

  function toggleDateModeSections(mode){
    const ym = document.getElementById('ym-controls');
    const rg = document.getElementById('range-controls');
    if(ym) ym.style.display = (mode === 'ym') ? '' : 'none';
    if(rg) rg.style.display = (mode === 'range') ? '' : 'none';
  }

  function ymDefaults(){
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth()+1); // 1..12 sin pad
    return { dateMode:'ym', year: String(y), month: m, start:'', end:'' };
  }
  function rangeDefaults(){
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth()+1).padStart(2,'0');
    const d = String(now.getDate()).padStart(2,'0');
    return { dateMode:'range', year:'', month:'', start: `${y}-${m}-01`, end: `${y}-${m}-${d}` };
  }

  function defaults(){
    // Default inicial: modo Año/Mes con año y mes actual
    const base = ymDefaults();
    return { ...base, type:[...TYPES], category:'', q:'' };
  }

  function getFromURL(){
    const p = new URLSearchParams(location.search);
    const types = p.getAll('type');
    let dm = p.get('dateMode') || '';
    let start = p.get('start') || '';
    let end = p.get('end') || '';
    const legacyDay = p.get('day') || '';
    const y = p.get('year') || '';
    const mRaw = p.get('month');
    const m = (mRaw === null) ? '' : mRaw; // puede ser '' (Todos)

    if(!start && !end && legacyDay){
      // Compat: map ?day=YYYY-MM-DD to range
      start = legacyDay;
      end = legacyDay;
      dm = 'range';
    }
    // Inferir modo si no viene explícito
    if(!dm){
      if(start || end){ dm = 'range'; }
      else if(y || (m !== '' && m !== null)){ dm = 'ym'; }
      else { dm = 'ym'; }
    }

    return {
      dateMode: dm,
      year: y,
      month: m,
      start,
      end,
      type: types,
      category: p.get('category') || '',
      q: p.get('q') || '',
    };
  }

  function updateURL(values, push){
    if(!doSyncURL) return; // no tocar la URL si está desactivado
    const qs = qsFromObj(values).toString();
    const url = qs ? ("?"+qs) : location.pathname;
    if(push) history.pushState(values, '', url); else history.replaceState(values, '', url);
  }

  // Exponer métodos también en el API global para evitar depender del objeto retornado
  api.getValues = () => ({ ...state });
  api.getQueryString = () => {
    const s = qsFromObj(state).toString();
    if (s) return s;
    const ls = location.search.startsWith('?') ? location.search.slice(1) : location.search;
    return ls;
  };
  api.apply = (v)=>{ applyToInputs(v); state = readInputs(); updateURL(state, true); onChangeCb && onChangeCb(state); };

  api.init = function({ onChange, syncURL=true }={}){
    onChangeCb = onChange || null;
    doSyncURL = !!syncURL;
    // Inicializar desde URL explícita o por defecto
    const raw = new URLSearchParams(location.search);
    const hasExplicit = ['year','month','start','end','type','category','q','dateMode','day'].some(k => raw.has(k));
    const initVals = hasExplicit ? getFromURL() : defaults();
    applyToInputs(initVals);
    state = { ...initVals };
    updateURL(state, false);

    // Bind comportamiento del dropdown de tipo
    document.querySelectorAll('.type-option').forEach(opt=>{
      opt.addEventListener('click', (e)=>{
        e.preventDefault();
        const val = opt.dataset.value;
        const cb = document.querySelector(`input[name="type"][value="${val}"]`);
        if(!cb) return;
        cb.checked = !cb.checked;
        // notificar cambio
        cb.dispatchEvent(new Event('change', { bubbles:true }));
        // UI
        syncTypeDropdownFromCheckboxes();
      });
    });

    // Bind eventos de inputs simples
    const ids = ['year','month','start','end','category','q'];
    ids.forEach(id=>{
      const el = document.getElementById(id); if(!el) return;
      const ev = el.tagName === 'SELECT' ? 'change' : 'input';
      el.addEventListener(ev, ()=>{
        state = readInputs();
        updateURL(state, true);
        onChangeCb && onChangeCb(state);
      });
    });
    // Bind checkboxes de tipo (ocultos)
    document.querySelectorAll('input[name="type"]').forEach(cb=>{
      cb.addEventListener('change', ()=>{
        state = readInputs();
        updateURL(state, true);
        onChangeCb && onChangeCb(state);
        syncTypeDropdownFromCheckboxes();
      });
    });
    // Bind radios de modo con defaults por modo
    document.querySelectorAll('input[name="dateMode"]').forEach(r=>{
      r.addEventListener('change', ()=>{
        const target = document.querySelector('input[name="dateMode"]:checked')?.value || 'ym';
        let defs = target === 'ym' ? ymDefaults() : rangeDefaults();
        // Mantener otros filtros (tipo, categoría, q)
        const merged = { ...state, ...defs, dateMode: target };
        applyToInputs(merged);
        state = readInputs();
        updateURL(state, true);
        onChangeCb && onChangeCb(state);
      });
    });

    const resetBtn = document.getElementById('resetFilters');
    if(resetBtn){
      resetBtn.addEventListener('click', (e)=>{
        e.preventDefault();
        const mode = state.dateMode || 'ym';
        const defs = mode === 'ym' ? ymDefaults() : rangeDefaults();
        const merged = { ...state, ...defs, dateMode: mode };
        applyToInputs(merged);
        state = readInputs();
        updateURL(state, true);
        onChangeCb && onChangeCb(state);
      });
    }

    if(doSyncURL){
      window.addEventListener('popstate', ()=>{
        const vals = getFromURL();
        const hasAny2 = Object.values(vals).some(v=> Array.isArray(v) ? v.length>0 : (v !== '' && v != null));
        const v = hasAny2 ? vals : defaults();
        applyToInputs(v);
        state = { ...v };
        updateURL(state, false);
        onChangeCb && onChangeCb(state);
      });
    }

    // Sincronizar UI de tipo al iniciar
    syncTypeDropdownFromCheckboxes();

    // Devolver un controlador por si se desea usar en local
    return {
      getValues: api.getValues,
      getQueryString: api.getQueryString,
      apply: api.apply,
    };
  };

  window.Filters = api;
})();
