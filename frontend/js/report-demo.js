const API_BASE = (window.ASSESSMENT_API_BASE || 'http://localhost:8000') + '/api/v1';
const _params  = new URLSearchParams(window.location.search);
const SESSION_ID = _params.get('session_id');
const JWT = localStorage.getItem('assessment_jwt');

function setUILang(lang) { K.saveLang(lang); K.setLang(lang); }
K.setLang(K.loadStoredLang('fr'));

function _globalLabel(key) {
  return ({
    tres_solide: K.t('global_label_very_solid'),
    solide: K.t('global_label_solid'),
    modere: K.t('global_label_moderate'),
    en_progression: K.t('global_label_progressing'),
    a_explorer: K.t('global_label_to_explore')
  })[key] || key;
}
const GLOBAL_LABELS = new Proxy({}, { get(_, prop) { return _globalLabel(prop); } });
const M1_LEVELS = {
  exceptionnel: 'Exceptionnel', eleve: 'Élevé', solide: 'Solide',
  modere: 'Modéré', a_developper: 'À développer'
};
const M1_LEVEL_CSS = {
  exceptionnel: 'level-exc', eleve: 'level-high', solide: 'level-solid',
  modere: 'level-mod', a_developper: 'level-low'
};
const ARCHETYPE_LABELS = {
  architect: {name:'ARCHITECT', desc:'Ouverture élevée + Conscienciosité dominante — vision structurée'},
  explorer:  {name:'EXPLORER',  desc:'Ouverture élevée + Extraversion marquée — créativité structurée'},
  diplomat:  {name:'DIPLOMAT',  desc:'Agréabilité dominante + Extraversion — harmonie relationnelle'},
  sentinel:  {name:'SENTINEL',  desc:'Conscienciosité + Stabilité — fiabilité opérationnelle'},
  logician:  {name:'LOGICIAN',  desc:'Ouverture + Introversion — analyse indépendante'},
  advocate:  {name:'ADVOCATE',  desc:'Agréabilité + Conscience — leadership par les valeurs'},
  commander: {name:'COMMANDER', desc:'Extraversion + Ouverture — leadership transformationnel'},
  mediator:  {name:'MEDIATOR',  desc:'Agréabilité + Ouverture — créativité collaborative'}
};
const VALUE_LABELS = {
  performance:          'Performance & Excellence',
  development_expertise:'Développement & Expertise',
  meaning_integrity:    'Sens & Intégrité',
  innovation_impact:    'Innovation & Impact',
  social_harmony:       'Harmonie Sociale',
  security_stability:   'Sécurité & Stabilité',
  autonomy:             'Autonomie',
  recognition_leadership:'Reconnaissance & Leadership'
};

function drawGauge(score) {
  const canvas = document.getElementById('gaugeCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const cx=70, cy=70, r=56;
  const sA=Math.PI*0.75, eA=Math.PI*2.25;
  ctx.clearRect(0,0,140,140);
  ctx.beginPath(); ctx.arc(cx,cy,r,sA,eA);
  ctx.strokeStyle='rgba(255,255,255,0.1)'; ctx.lineWidth=10; ctx.lineCap='round'; ctx.stroke();
  if (score > 0) {
    const fillEnd = sA + (eA-sA)*(score/100);
    const grad = ctx.createLinearGradient(cx-r,cy,cx+r,cy);
    grad.addColorStop(0,'#22a380'); grad.addColorStop(1,'#6366F1');
    ctx.beginPath(); ctx.arc(cx,cy,r,sA,fillEnd);
    ctx.strokeStyle=grad; ctx.lineWidth=10; ctx.lineCap='round'; ctx.stroke();
  }
}

function drawGaugeAnimated(score) {
  let current = 0;
  function step() {
    if (current < score) { current = Math.min(current+1.5, score); drawGauge(current); requestAnimationFrame(step); }
    else drawGauge(score);
  }
  drawGauge(0); setTimeout(step, 300);
}

function drawRadar(values) {
  const canvas = document.getElementById('radarCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const cx=110, cy=110, maxR=90, maxVal=40;
  const labels=['O','C','E','A','Stab'], n=labels.length;
  function pt(i,r){ const a=(Math.PI*2*i/n)-Math.PI/2; return {x:cx+r*Math.cos(a),y:cy+r*Math.sin(a)}; }
  ctx.clearRect(0,0,220,220);
  [0.25,0.5,0.75,1].forEach(f=>{
    ctx.beginPath();
    for(let i=0;i<n;i++){const p=pt(i,maxR*f);i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);}
    ctx.closePath(); ctx.strokeStyle='rgba(30,41,59,0.1)'; ctx.lineWidth=1; ctx.stroke();
  });
  for(let i=0;i<n;i++){
    const p=pt(i,maxR);
    ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(p.x,p.y);
    ctx.strokeStyle='rgba(30,41,59,0.12)'; ctx.lineWidth=1; ctx.stroke();
    const lp=pt(i,maxR+16);
    ctx.fillStyle='#1E293B'; ctx.font='600 12px CircularStd,sans-serif';
    ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText(labels[i],lp.x,lp.y);
  }
  const grad=ctx.createRadialGradient(cx,cy,0,cx,cy,maxR);
  grad.addColorStop(0,'rgba(34,163,128,0.3)'); grad.addColorStop(1,'rgba(30,41,59,0.05)');
  ctx.beginPath();
  values.forEach((v,i)=>{const r2=(v/maxVal)*maxR;const p=pt(i,r2);i===0?ctx.moveTo(p.x,p.y):ctx.lineTo(p.x,p.y);});
  ctx.closePath(); ctx.fillStyle=grad; ctx.fill(); ctx.strokeStyle='#1E293B'; ctx.lineWidth=2; ctx.stroke();
  values.forEach((v,i)=>{
    const r2=(v/maxVal)*maxR; const p=pt(i,r2);
    ctx.beginPath(); ctx.arc(p.x,p.y,4,0,Math.PI*2);
    ctx.fillStyle='#6366F1'; ctx.fill(); ctx.strokeStyle='white'; ctx.lineWidth=1.5; ctx.stroke();
  });
}

function buildEngSegments(score) {
  const wrap = document.getElementById('engSegments');
  if (!wrap) return;
  wrap.innerHTML='';
  const total=60, segments=30;
  for(let i=0;i<segments;i++){
    const seg=document.createElement('div'); seg.className='eng-seg';
    const val=((i+1)/segments)*total;
    seg.style.width=(100/segments-0.3)+'%';
    seg.style.background = val<=score ? (val<=35?'#6366F1':val<=48?'#C7D2FE':'#1E293B') : '#F3F4F6';
    wrap.appendChild(seg);
  }
}

function el(id){ return document.getElementById(id); }
function setText(id, txt){ const e=el(id); if(e && txt!=null) e.textContent=txt; }
function setHtml(id, html){ const e=el(id); if(e) e.innerHTML=html; }

function downloadPDF() {
  if (!SESSION_ID || !JWT) { window.print(); return; }
  const btn = el('btn-export');
  if (btn) { btn.textContent = K.t('rep_loading'); btn.disabled = true; }
  fetch(`${API_BASE}/scores/${SESSION_ID}/pdf`, { headers:{Authorization:`Bearer ${JWT}`} })
    .then(r => { if(!r.ok) throw new Error(r.status); return r.blob(); })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href=url; a.download=`Rapport_${SESSION_ID.substring(0,8)}.pdf`; a.click();
      setTimeout(()=>URL.revokeObjectURL(url), 10000);
    })
    .catch(() => window.print())
    .finally(() => { if(btn){ btn.innerHTML='<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg> <span data-i18n="rep_export_pdf">' + K.t('rep_export_pdf') + '</span>'; btn.disabled=false; } });
}

function showReportError(type) {
  if(el('report-loading')) el('report-loading').style.display='none';
  const err=el('report-error'); if(err) err.style.display='block';
  const msgs = {
    no_session: K.t('rep_err_no_session'),
    no_auth:    K.t('rep_err_session_expired'),
    auth:       K.t('rep_err_forbidden'),
    not_found:  K.t('rep_err_not_found'),
    network:    K.t('rep_err_network')
  };
  setText('re-msg', msgs[type] || K.t('err_text_default'));
}

function populateReport(d) {
  const session = d.session || {};
  const report  = d.report_text || {};

  const name = session.candidate_name || '—';
  const parts = name.trim().split(' ');
  setHtml('cover-candidate-name', parts.length>1 ? parts.slice(0,-1).join(' ')+'<br>'+parts[parts.length-1] : name);
  const lvl = session.level==='master' ? 'Master' : 'Bachelier';
  setText('cover-candidate-role', `Candidat(e) — ${session.position_visee||'Évaluation générale'} · ${lvl}`);

  const cDate = d.computed_at ? new Date(d.computed_at) : new Date();
  const dateStr = cDate.toLocaleDateString('fr-BE',{day:'numeric',month:'long',year:'numeric'});
  setText('meta-date', dateStr);
  setText('meta-package', Array.isArray(session.modules) ? `M1–M${session.modules.length}` : '—');
  if (session.started_at && session.completed_at) {
    const mins = Math.round((new Date(session.completed_at)-new Date(session.started_at))/60000);
    setText('meta-duration', mins>=60 ? `${Math.floor(mins/60)}h ${mins%60} min` : `${mins} min`);
  }

  const gScore = d.global || 0;
  setText('gauge-score-text', gScore);
  setText('cover-global-label', GLOBAL_LABELS[d.global_label] || d.global_label || '—');
  drawGaugeAnimated(gScore);

  if (d.m1_raw != null) setText('pill-m1', `${d.m1_raw}/26 · ${M1_LEVELS[d.m1_level]||d.m1_level||'—'}`);
  if (d.m2_ocean) {
    const a = ARCHETYPE_LABELS[d.m2_ocean.archetype] || {name: (d.m2_ocean.archetype||'').toUpperCase()};
    setText('pill-m2', `${a.name} · Solide`);
  }
  if (d.m3_raw != null) setText('pill-m3', `${d.m3_raw}/60 · ${d.m3_level||'—'}`);
  if (d.m4_engagement != null) {
    const eL = d.m4_engagement>=49?'Élevé':d.m4_engagement>=36?'Modéré':'Faible';
    setText('pill-m4', `${d.m4_engagement}/60 · ${eL}`);
  }

  if (Array.isArray(d.signals) && d.signals.length) {
    setHtml('signals-wrap', d.signals.map(s=>`
      <div class="signal ${escHtml(s.type||'neutral')}">
        <div class="signal-dot"></div>
        ${escHtml(s.label)}${s.detail?' — '+escHtml(s.detail):''}
      </div>`).join(''));
  }

  setText('global-narrative', report.global_narrative);

  if (d.m1_raw != null) {
    setHtml('m1-score-val', `${d.m1_raw} <span>/ 26</span>`);
    const lvlKey = d.m1_level || 'solide';
    const badge = el('m1-level-badge');
    if (badge) { badge.textContent = M1_LEVELS[lvlKey]||lvlKey; badge.className=`mod-level ${M1_LEVEL_CSS[lvlKey]||'level-solid'}`; }
    const m1b = el('m1bar'); if(m1b) setTimeout(()=>{ m1b.style.width=(d.m1_raw/26*100)+'%'; },400);
    setText('m1-narrative', report.m1_narrative);
    const by = d.m1_by_section || {};
    if (by.numeric_figural!=null) setText('m1-dim-num', by.numeric_figural);
    if (by.verbal!=null)          setText('m1-dim-verb', by.verbal);
    if (by.deductive!=null)       setText('m1-dim-ded',  by.deductive);
  }

  if (d.m2_ocean) {
    const o = d.m2_ocean;
    const arch = ARCHETYPE_LABELS[o.archetype] || {name:(o.archetype||'').toUpperCase(), desc:''};
    setText('archetype-name', arch.name);
    setText('archetype-desc', arch.desc);
    ['O','C','E','A','N'].forEach(dim => {
      const score = o[dim]||0;
      setText(`ocean-score-${dim}`, `${score} / 40`);
      const bar = el(`ocean-bar-${dim}`); if(bar) bar.style.width=(score/40*100).toFixed(1)+'%';
    });

    const radarVals = [o.O||34, o.C||32, o.E||30, o.A||29, 40-(o.N||16)];
    setTimeout(()=>drawRadar(radarVals), 100);
    setText('m2-narrative', report.m2_narrative);
  }

  if (d.m3_raw != null) {
    setHtml('m3-score-val', `${d.m3_raw} <span>/ 60</span>`);
    const m3b = el('m3bar'); if(m3b) setTimeout(()=>{ m3b.style.width=(d.m3_raw/60*100)+'%'; },500);
    const m3badge = el('m3-level-badge');
    if (m3badge && d.m3_level) { m3badge.textContent=M1_LEVELS[d.m3_level]||d.m3_level; }
    setText('m3-narrative', report.m3_narrative);
  }

  if (d.m4_engagement != null) {
    setText('m4-eng-num', d.m4_engagement);
    setText('m4-eng-label', d.m4_engagement>=49?'ÉLEVÉ':d.m4_engagement>=36?'MODÉRÉ':'FAIBLE');
    buildEngSegments(d.m4_engagement);
  }
  if (d.m4_values) {
    const top3 = d.m4_values.top3 || [];
    const bot2 = d.m4_values.bottom2 || [];
    const topCol = el('values-top-col');
    if (topCol && top3.length) {
      const title = topCol.querySelector('.values-title');
      topCol.innerHTML=''; if(title) topCol.appendChild(title);
      top3.forEach((v,i)=>{ topCol.innerHTML+=`<div class="value-item top"><div class="value-rank">${i+1}</div><div><div class="value-name">${escHtml(VALUE_LABELS[v]||v)}</div></div></div>`; });
    }
    const botCol = el('values-bottom-col');
    if (botCol && bot2.length) {
      const title = botCol.querySelector('.values-title');
      botCol.innerHTML=''; if(title) botCol.appendChild(title);
      bot2.forEach(v=>{ botCol.innerHTML+=`<div class="value-item bottom"><div class="value-rank">↓</div><div><div class="value-name">${escHtml(VALUE_LABELS[v]||v)}</div></div></div>`; });
    }
    setText('m4-narrative', report.m4_narrative);
  }

  if (Array.isArray(report.interview_questions) && report.interview_questions.length) {
    setHtml('iq-list', report.interview_questions.map((q,i)=>`
      <div class="iq-item">
        <div class="iq-num">${i+1}</div>
        <div><div class="iq-text">${escHtml(q)}</div></div>
      </div>`).join(''));
  }

  setText('footer-date', dateStr);
  setText('footer-model', d.model_used || 'Claude Opus 4.6');

  if(el('report-error')) el('report-error').style.display='none';
}

let _pollTimer = null;

async function pollForReport() {
  try {
    const resp = await fetch(`${API_BASE}/scores/${SESSION_ID}`, {
      headers: { Authorization: `Bearer ${JWT}` }
    });

    if (resp.status === 202) {
      const data = await resp.json().catch(()=>({}));
      setText('rl-text', data.message || 'Génération du rapport en cours…');
      _pollTimer = setTimeout(pollForReport, 3000);
      return;
    }
    if (resp.status === 401 || resp.status === 403) { showReportError('auth'); return; }
    if (resp.status === 404) { showReportError('not_found'); return; }
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const data = await resp.json();
    if(el('report-loading')) el('report-loading').style.display='none';
    populateReport(data);

  } catch(e) {
    console.error('Report fetch error:', e);
    showReportError('network');
  }
}

async function initReport() {

  if (!SESSION_ID) {
    if(el('report-loading')) el('report-loading').style.display='none';

    drawGaugeAnimated(81);
    setTimeout(()=>drawRadar([34,32,30,29,24]),100);
    setTimeout(()=>{
      const m1=el('m1bar'); if(m1) m1.style.width=(22/26*100)+'%';
      const m3=el('m3bar'); if(m3) m3.style.width=(48/60*100)+'%';
    },400);
    buildEngSegments(51);
    return;
  }

  if (!JWT) { showReportError('no_auth'); return; }

  if(el('report-loading')) el('report-loading').style.display='flex';
  await pollForReport();
}

initReport();
