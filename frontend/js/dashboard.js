const APP_BUILD = "2026-05-07-dashboard-build-stamp";
const API_BASE  = (window.ASSESSMENT_API_BASE || 'http://localhost:8000') + '/api/v1';
const CANDIDATE_BASE = window.location.origin + '/test';
console.info(`[assessment] dashboard build=${APP_BUILD} api=${API_BASE}`);

let _jwt        = localStorage.getItem('assessment_jwt') || '';
let _user       = JSON.parse(localStorage.getItem('assessment_user') || 'null');
let _sessions   = [];
let _filtered   = [];
let _page       = 1;
const PAGE_SIZE = 15;
let _modalSession = null;

function el(id) { return document.getElementById(id); }
function setText(id, v) { const e=el(id); if(e) e.textContent=v; }
function show(id) { const e=el(id); if(e) { e.classList.add('active'); } }
function hide(id) { const e=el(id); if(e) { e.classList.remove('active'); } }

function toast(msg, duration=3000) {
  const t = el('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'), duration);
}

async function apiFetch(path, opts={}) {
  const headers = { 'Content-Type': 'application/json', ...(opts.headers||{}) };
  if (_jwt) headers['Authorization'] = `Bearer ${_jwt}`;
  const resp = await fetch(API_BASE + path, { ...opts, headers });
  if (resp.status === 401) { doLogout(); throw new Error('401'); }
  return resp;
}

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  const s = el(id); if(s) s.classList.add('active');
}

function showPanel(id) {
  document.querySelectorAll('.content-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  const panel = el('panel-'+id);
  if(panel) panel.classList.add('active');
  const nav = document.querySelector(`[data-panel="${id}"]`);
  if(nav) nav.classList.add('active');
  const titles = {sessions: K.t('sessions_title'), create: K.t('nav_new_session'), stats: K.t('nav_stats')};
  setText('panel-title', titles[id]||id);
  if(id==='stats') computeStats();
}

function setUILang(lang) {
  K.saveLang(lang);
  K.setLang(lang);
}

K.setLang(K.loadStoredLang('fr'));

async function doLogin() {
  const email = el('login-email').value.trim();
  const pwd   = el('login-password').value;
  const errEl = el('login-error');
  const btn   = el('login-btn');
  errEl.style.display = 'none';

  if (!email || !pwd) { errEl.textContent = K.t('err_fill_all_fields'); errEl.style.display='block'; return; }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + K.t('logging_in');

  try {
    btn.innerHTML = '<span class="spinner"></span> Réveil du serveur…';
    await fetch((window.ASSESSMENT_API_BASE || '') + '/health', {
      method: 'GET',
      signal: AbortSignal.timeout(60000),
    });
  } catch (e) {
    console.warn('[login] health-ping failed (continuing anyway):', e);
  }
  btn.innerHTML = '<span class="spinner"></span> ' + K.t('logging_in');

  try {
    const resp = await fetch(API_BASE + '/auth/login', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email, password: pwd}),
      signal: AbortSignal.timeout(30000),
    });

    if (!resp.ok) {
      const data = await resp.json().catch(()=>({}));
      throw new Error(data.detail || K.t('err_invalid_credentials'));
    }

    const data = await resp.json();
    _jwt = data.access_token;
    _user = data.user || {name: email.split('@')[0], role: 'advisor'};
    localStorage.setItem('assessment_jwt', _jwt);
    localStorage.setItem('assessment_user', JSON.stringify(_user));
    bootApp();

  } catch(e) {
    let msg = e.message || K.t('err_login_generic');

    if (/failed to fetch|network|aborted|timeout/i.test(String(e))) {
      msg = "Le serveur d'API n'a pas répondu (" + API_BASE + "). Réessayez dans 30s — il sort de veille.";
    }
    errEl.textContent = msg;
    errEl.style.display = 'block';
    console.error('[login] error:', e);
  } finally {
    btn.disabled = false;
    btn.textContent = K.t('btn_login');
  }
}

['login-email','login-password'].forEach(id=>{
  const inp = el(id);
  if(inp) inp.addEventListener('keydown', e=>{ if(e.key==='Enter') doLogin(); });
});

function doLogout() {
  _jwt = ''; _user = null;
  localStorage.removeItem('assessment_jwt');
  localStorage.removeItem('assessment_user');
  showScreen('screen-login');
}

function bootApp() {

  if (_user) {
    setText('user-name', _user.name || _user.email || 'Recruteur');
    setText('user-role', _user.role === 'admin' ? K.t('role_admin') : K.t('role_advisor'));
    const avatar = el('user-avatar');
    if(avatar) avatar.textContent = (_user.name||'R')[0].toUpperCase();
  }
  showScreen('screen-app');
  showPanel('sessions');
  loadSessions();

  document.querySelectorAll('.module-check input[type=checkbox]').forEach(cb=>{
    cb.addEventListener('change', function(){
      this.closest('.module-check').classList.toggle('checked', this.checked);
    });
  });
}

async function loadSessions() {
  const tbody = el('sessions-tbody');
  tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">⏳</div><div class="empty-text">${K.t('loading_dots')}</div></div></td></tr>`;

  try {
    const resp = await apiFetch('/sessions');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    _sessions = Array.isArray(data) ? data : (data.sessions || []);
    _filtered = [..._sessions];
    _page = 1;
    renderTable();
    renderStats();
  } catch(e) {
    tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-text">${K.t('err_loading_retry')} <button onclick="loadSessions()" style="background:none;border:none;color:var(--navy);font-weight:600;cursor:pointer;">${K.t('err_retry')}</button></div></div></td></tr>`;
  }
}

function filterTable() {
  const q     = (el('search-input').value||'').toLowerCase();
  const st    = el('filter-status').value;
  const lvl   = el('filter-level').value;
  _filtered = _sessions.filter(s=>{
    const matchQ  = !q || (s.candidate_name||'').toLowerCase().includes(q) || (s.candidate_email||'').toLowerCase().includes(q);
    const matchSt = !st || s.status===st;
    const matchLv = !lvl || s.level===lvl;
    return matchQ && matchSt && matchLv;
  });
  _page = 1;
  renderTable();
}

function renderTable() {
  const tbody = el('sessions-tbody');
  const total = _filtered.length;
  const start = (_page-1)*PAGE_SIZE;
  const slice = _filtered.slice(start, start+PAGE_SIZE);

  setText('table-count', `${total} ${K.t('results_suffix')}`);

  if (!total) {
    tbody.innerHTML = '<tr><td colspan="8"><div class="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">—</div></div></td></tr>';
    renderPager(0);
    return;
  }

  tbody.innerHTML = slice.map(s => {
    const statusBadge = {
      pending:     `<span class="badge badge-pending"><span class="badge-dot"></span>${K.t('status_pending')}</span>`,
      in_progress: `<span class="badge badge-in_progress"><span class="badge-dot"></span>${K.t('status_in_progress')}</span>`,
      completed:   `<span class="badge badge-completed"><span class="badge-dot"></span>${K.t('status_completed')}</span>`
    }[s.status] || s.status;

    const scoreCell = s.score_global != null
      ? `<span class="score-pill ${scoreClass(s.score_global)}">${s.score_global}/100</span>`
      : '<span style="color:#9CA3AF">—</span>';

    const reportBtn = s.status==='completed'
      ? `<button class="action-btn" onclick="event.stopPropagation();openReportForSession('${s.id}')">${K.t('btn_view_report')}</button>`
      : '';

    const mods = Array.isArray(s.modules) ? `M1–M${s.modules.length}` : '—';
    const dateLocale = ({fr:'fr-BE', nl:'nl-BE', en:'en-GB'}[K.getLang()] || 'fr-BE');
    const date = s.created_at ? new Date(s.created_at).toLocaleDateString(dateLocale) : '—';

    return `<tr onclick="openSessionModal('${s.id}')">
      <td>
        <div class="td-name">${escHtml(s.candidate_name||'—')}</div>
        <div class="td-email">${escHtml(s.candidate_email||'')}</div>
      </td>
      <td>${s.level==='master' ? K.t('level_master') : K.t('level_bachelor')}</td>
      <td>${escHtml(s.position_visee||'—')}</td>
      <td>${mods}</td>
      <td>${statusBadge}</td>
      <td>${scoreCell}</td>
      <td style="white-space:nowrap;color:var(--grey)">${date}</td>
      <td onclick="event.stopPropagation()" style="white-space:nowrap">
        <div style="display:flex;gap:6px;">${reportBtn}</div>
      </td>
    </tr>`;
  }).join('');

  renderPager(total);
}

function scoreClass(s) {
  if (s >= 75) return 'score-high';
  if (s >= 55) return 'score-solid';
  if (s >= 35) return 'score-mid';
  return 'score-low';
}

function renderPager(total) {
  const pages = Math.ceil(total / PAGE_SIZE);
  const wrap = el('page-btns');
  if (!wrap) return;
  if (pages <= 1) { wrap.innerHTML=''; return; }
  wrap.innerHTML = Array.from({length:pages},(_,i)=>
    `<button class="page-btn${_page===i+1?' active':''}" onclick="gotoPage(${i+1})">${i+1}</button>`
  ).join('');
}

function gotoPage(p) { _page=p; renderTable(); }

function renderStats() {
  const total     = _sessions.length;
  const inProg    = _sessions.filter(s=>s.status==='in_progress').length;
  const done      = _sessions.filter(s=>s.status==='completed').length;
  const withScore = _sessions.filter(s=>s.score_global!=null);
  const avg       = withScore.length ? Math.round(withScore.reduce((a,s)=>a+s.score_global,0)/withScore.length) : null;

  setText('stat-total',     total);
  setText('stat-progress',  inProg);
  setText('stat-completed', done);
  setText('stat-avg',       avg!=null ? avg+'/100' : '—');
}

function openSessionModal(id) {
  const s = _sessions.find(x=>x.id===id);
  if (!s) return;
  _modalSession = s;

  setText('modal-candidate', s.candidate_name||'—');
  setText('modal-sub',       s.candidate_email||'—');
  el('modal-status').innerHTML = {
    pending:     `<span class="badge badge-pending">${K.t('status_pending')}</span>`,
    in_progress: `<span class="badge badge-in_progress">${K.t('status_in_progress')}</span>`,
    completed:   `<span class="badge badge-completed">${K.t('status_completed')}</span>`
  }[s.status] || s.status;
  setText('modal-level',    s.level==='master' ? K.t('level_master') : K.t('level_bachelor'));
  setText('modal-position', s.position_visee||'—');
  setText('modal-company',  s.entreprise_cible||'—');
  setText('modal-lang',     {fr: K.t('lang_fr'), nl: K.t('lang_nl'), en: K.t('lang_en')}[s.lang] || s.lang || '—');
  setText('modal-modules',  Array.isArray(s.modules) ? s.modules.join(', ') : '—');
  const _modalLocale = ({fr:'fr-BE', nl:'nl-BE', en:'en-GB'}[K.getLang()] || 'fr-BE');
  setText('modal-date',     s.created_at ? new Date(s.created_at).toLocaleDateString(_modalLocale,{day:'numeric',month:'long',year:'numeric'}) : '—');
  setText('modal-score',    s.score_global!=null ? s.score_global+'/100' : '—');

  const link = `${CANDIDATE_BASE}/${s.token}`;
  const modalLink = el('modal-link'); if(modalLink) modalLink.textContent = link;

  const reportBtn = el('modal-report-btn');
  if(reportBtn) reportBtn.style.display = s.status==='completed' ? 'inline-flex' : 'none';

  el('session-modal').classList.add('open');
}

function closeModal() { el('session-modal').classList.remove('open'); _modalSession=null; }

function copyModalLink() {
  const link = el('modal-link');
  if (!link) return;
  navigator.clipboard.writeText(link.textContent).then(()=>toast('Lien copié !')).catch(()=>{
    const inp = document.createElement('input');
    inp.value = link.textContent; document.body.appendChild(inp);
    inp.select(); document.execCommand('copy'); document.body.removeChild(inp);
    toast('Lien copié !');
  });
}

function openReport() {
  if (!_modalSession) return;
  window.open(`report-demo.html?session_id=${_modalSession.id}`, '_blank');
  closeModal();
}

function openReportForSession(id) {
  window.open(`report-demo.html?session_id=${id}`, '_blank');
}

async function confirmDelete() {
  if (!_modalSession) return;
  if (!confirm(K.t('confirm_delete_session', {name: _modalSession.candidate_name}))) return;
  try {
    const resp = await apiFetch(`/sessions/${_modalSession.id}`, {method:'DELETE'});
    if (!resp.ok) throw new Error();
    toast(K.t('toast_session_deleted'));
    closeModal();
    loadSessions();
  } catch {
    toast(K.t('toast_delete_error'));
  }
}

document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeModal(); });

async function createSession() {
  const name     = el('f-name').value.trim();
  const email    = el('f-email').value.trim();
  const level    = el('f-level').value;
  const lang     = el('f-lang').value;
  const position = el('f-position').value.trim();
  const company  = el('f-company').value.trim();
  const errEl    = el('create-error');
  const btn      = el('create-btn');

  errEl.style.display = 'none';

  if (!name || !email) {
    errEl.textContent = K.t('err_fill_all_fields'); errEl.style.display='block'; return;
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errEl.textContent = K.t('err_fill_all_fields'); errEl.style.display='block'; return;
  }

  const modules = Array.from(document.querySelectorAll('.module-check input:checked')).map(c=>c.value);
  if (!modules.length) {
    errEl.textContent = K.t('err_fill_all_fields'); errEl.style.display='block'; return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> ' + K.t('logging_in');

  try {
    const resp = await apiFetch('/sessions', {
      method: 'POST',
      body: JSON.stringify({ candidate_name:name, candidate_email:email, level, lang, modules, position_visee:position||null, entreprise_cible:company||null })
    });
    if (!resp.ok) {
      const d = await resp.json().catch(()=>({}));
      const detail = Array.isArray(d.detail)
        ? d.detail.map(e => e.msg || JSON.stringify(e)).join(', ')
        : (typeof d.detail === 'string' ? d.detail : `HTTP ${resp.status}`);
      throw new Error(detail);
    }
    const data = await resp.json();
    const token = data.token || data.id;
    const link  = `${CANDIDATE_BASE}/${token}`;

    const banner = el('success-banner');
    banner.style.display = 'block';
    el('success-link').textContent = link;
    banner.scrollIntoView({behavior:'smooth', block:'start'});

    ['f-name','f-email','f-position','f-company'].forEach(id=>{ const e=el(id); if(e) e.value=''; });
    document.querySelectorAll('.module-check input').forEach(cb=>{ cb.checked=true; cb.closest('.module-check').classList.add('checked'); });

    loadSessions();

  } catch(e) {
    errEl.textContent = e.message || K.t('err_login_generic');
    errEl.style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.textContent = K.t('btn_create_session');
  }
}

function copyLink() {
  const link = el('success-link');
  if (!link) return;
  navigator.clipboard.writeText(link.textContent)
    .then(()=>{ toast('Lien copié !'); el('copy-btn') && (el('copy-btn').textContent='✓ Copié'); })
    .catch(()=>{
      const inp=document.createElement('input'); inp.value=link.textContent;
      document.body.appendChild(inp); inp.select(); document.execCommand('copy');
      document.body.removeChild(inp); toast('Lien copié !');
    });
}

const GLOBAL_LABEL_NAMES = {
  tres_solide:'Très solide', solide:'Solide', modere:'Modéré',
  en_progression:'En progression', a_explorer:'À explorer'
};
const LABEL_COLORS = {
  tres_solide:'#1E293B', solide:'#22a380', modere:'#C7D2FE',
  en_progression:'#6366F1', a_explorer:'#9CA3AF'
};

function computeStats() {
  const total  = _sessions.length;
  const done   = _sessions.filter(s=>s.status==='completed').length;
  const rate   = total ? Math.round(done/total*100) : 0;
  const withSc = _sessions.filter(s=>s.score_global!=null);
  const avg    = withSc.length ? Math.round(withSc.reduce((a,s)=>a+s.score_global,0)/withSc.length) : null;
  const now    = new Date();
  const month  = _sessions.filter(s=>{ const d=new Date(s.created_at); return d.getMonth()===now.getMonth()&&d.getFullYear()===now.getFullYear(); }).length;
  const master = _sessions.filter(s=>s.level==='master').length;
  const bach   = _sessions.filter(s=>s.level==='bachelier').length;

  setText('s-total',  total);
  setText('s-rate',   rate+'%');
  setText('s-avg',    avg!=null ? avg+'/100' : '—');
  setText('s-month',  month);
  setText('s-master', master);
  setText('s-bach',   bach);

  const dist = {};
  _sessions.filter(s=>s.global_label).forEach(s=>{ dist[s.global_label]=(dist[s.global_label]||0)+1; });
  const distEl = el('label-dist');
  if(distEl) {
    const doneCount = done || 1;
    distEl.innerHTML = Object.entries(GLOBAL_LABEL_NAMES).map(([k,lbl])=>{
      const n = dist[k]||0;
      const pct = Math.round(n/doneCount*100);
      const color = LABEL_COLORS[k]||'#9CA3AF';
      return `<div>
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
          <span style="color:var(--text);font-weight:500">${lbl}</span>
          <span style="color:var(--grey)">${n} (${pct}%)</span>
        </div>
        <div style="background:#F3F4F6;border-radius:4px;height:8px;">
          <div style="background:${color};width:${pct}%;height:100%;border-radius:4px;transition:width 0.5s"></div>
        </div>
      </div>`;
    }).join('');
  }
}

(function init() {

  if (_jwt && _user) {
    bootApp();
  } else {
    showScreen('screen-login');
  }
})();
