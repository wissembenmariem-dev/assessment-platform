const APP_BUILD = "2026-05-07-submit-errors";
const API_BASE = (typeof window !== 'undefined' && window.ASSESSMENT_API_BASE) || 'http://localhost:8000';

function _extractToken() {
  const q = new URLSearchParams(location.search).get('token');
  if (q) return q;
  const m = location.pathname.match(/\/test\/([a-f0-9]{32})/i);
  return m ? m[1] : null;
}
const _token = _extractToken();
console.info(`[assessment] build=${APP_BUILD} api=${API_BASE} token=${(_token || '').slice(0, 8)}…`);

function _saveProgress() {
  if (!_token) return;
  try {
    localStorage.setItem(`kp_${_token}`, JSON.stringify({
      answers: state.answers,
      moduleIdx: state.moduleIdx,
      questionIdx: state.questionIdx,
      ts: Date.now()
    }));
  } catch(e) {}
}

function _restoreProgress() {
  if (!_token) return false;
  try {
    const raw = localStorage.getItem(`kp_${_token}`);
    if (!raw) return false;
    const d = JSON.parse(raw);
    if (Date.now() - d.ts > 7200000) { localStorage.removeItem(`kp_${_token}`); return false; }
    Object.assign(state, { answers: d.answers || {}, moduleIdx: d.moduleIdx || 0, questionIdx: d.questionIdx || 0 });
    return true;
  } catch(e) { return false; }
}

function _clearProgress() {
  if (_token) localStorage.removeItem(`kp_${_token}`);
}

function showError(type, msg) {
  const E = {
    token:     { icon:'🔗', titleKey:'err_invalid_title',   textKey:'err_invalid_text' },
    expired:   { icon:'⏰', titleKey:'err_expired_title',   textKey:'err_expired_text' },
    completed: { icon:'✅', titleKey:'err_completed_title', textKey:'err_completed_text' },
    network:   { icon:'📡', titleKey:'err_network_title',   textKey:'err_network_text' }
  };
  const e = E[type] || E.network;
  document.getElementById('error-icon').textContent  = e.icon;
  document.getElementById('error-title').textContent = K.t(e.titleKey);
  document.getElementById('error-text').textContent  = (type === 'network' && msg) ? msg : K.t(e.textKey);
  showScreen('screen-error');
}

async function initFromAPI() {
  if (!_token) {

    return showError('token');
  }

  showScreen('screen-loading');

  try {
    const sRes = await fetch(`${API_BASE}/api/v1/test/${_token}`);
    if (sRes.status === 404) return showError('token');
    if (!sRes.ok) throw new Error(`HTTP ${sRes.status}`);
    const session = await sRes.json();

    if (window.K && session.lang) K.setLang(session.lang);

    if (session.status === 'completed') return showError('completed');

    const nameEl = document.getElementById('candidate-name');
    if (nameEl && session.candidate_name) nameEl.textContent = session.candidate_name;

    const qRes = await fetch(`${API_BASE}/api/v1/test/${_token}/questions`);
    if (!qRes.ok) throw new Error(`Questions HTTP ${qRes.status}`);
    const questions = await qRes.json();

    MODULES.length = 0;
    _buildModulesFromAPI(questions).forEach(m => MODULES.push(m));
    if (MODULES.length === 0) {
      console.error('[assessment] API returned 0 questions for token', _token);
      return showError('network', 'Aucune question disponible pour cette session. Contactez votre recruteur.');
    }

    const restored = _restoreProgress();
    initIntro();
    showScreen('screen-intro');
    if (restored) setTimeout(() => showToast('✅ Progression restaurée'), 800);

  } catch(err) {
    console.error('[Acme Talent API]', err);
    showError('network', err.message);
  }
}

function _buildModulesFromAPI(questions) {
  const byMod = {1:[], 2:[], 3:[], 4:[]};
  questions.forEach(q => { if (byMod[q.module]) byMod[q.module].push(q); });
  const mods = [];

  const T = (k) => (window.K ? K.t(k) : k);

  if (byMod[1].length) {
    mods.push({
      id:'m1_api', num: `${T('module_label')} 1`, title: T('m1_title'),
      desc: T('m1_intro_short'),
      time: 30*60, timeLabel:'30 minutes',
      instruction: T('m1_intro_short'),
      header: T('m1_section_label'),
      questions: byMod[1].map(q => ({
        id: q.id, section: q.category || T('m1_short_title'), type:'qcm',
        text: q.text, instruction: q.instruction || null,
        options: (q.options||[]).map(o=>({k:o.id, v:o.text})),
        _apiId: q.id, _apiModule: 1
      }))
    });
  }

  if (byMod[2].length) {
    const bsz = 5;
    const batches = [];
    for (let i=0; i<byMod[2].length; i+=bsz) {
      const slice = byMod[2].slice(i, i+bsz);
      batches.push({
        id:`m2b_${i}`, section: T('m2_title'), type:'likert', batchSize:bsz,
        items: slice.map(q => ({
          id: q.id,
          dim: T('ocean_' + ((q.meta||{}).dimension || 'O')),
          inv: (q.meta||{}).inverted || false,
          text: q.text, _apiId: q.id
        }))
      });
    }
    mods.push({
      id:'m2_api', num: `${T('module_label')} 2`, title: T('m2_title'),
      desc: T('m2_short_description'),
      time:10*60, timeLabel:'10 minutes',
      instruction: T('m2_likert_instruction'),
      header: `${T('module_label')} 2 · ${T('m2_title').toUpperCase()}`, questions: batches
    });
  }

  if (byMod[3].length) {
    mods.push({
      id:'m3_api', num: `${T('module_label')} 3`, title: T('m3_title'),
      desc: T('m3_description'),
      time:20*60, timeLabel:'20 minutes',
      instruction: T('m3_instruction'),
      header: `${T('module_label')} 3 · ${T('m3_title').toUpperCase()}`,
      questions: byMod[3].map((q,i) => ({
        id: q.id, section:`${i+1} / ${byMod[3].length}`, type:'sjt',
        scenario: q.text, instruction: q.instruction,
        options: (q.options||[]).map(o=>({k:o.id, text:o.text})),
        _apiId: q.id, _apiModule: 3
      }))
    });
  }

  if (byMod[4].length) {
    const rankQs  = byMod[4].filter(q => q.type === 'ranking');
    const likertQs = byMod[4].filter(q => q.type === 'likert');
    const m4Qs = [];
    const icons = {A:'🎯',B:'🤝',C:'📚',D:'🔑',E:'💡',F:'⚡',G:'🌱',H:'🏆'};

    rankQs.forEach((q, i) => {
      if ((q.options||[]).length >= 2) {
        m4Qs.push({
          id: q.id, type:'value_rank',
          section: T('m4_section_a'),
          groupTitle: q.text || '',
          groupNum: `${i+1} / ${rankQs.length}`,
          cards: q.options.map(o => ({k:o.id, icon:icons[o.id]||'✦', title:o.text, desc:''})),
          _apiId: q.id, _apiModule: 4
        });
      }
    });

    if (likertQs.length) {
      m4Qs.push({
        id:'m4_eng_api', type:'likert', batchSize: Math.min(6, likertQs.length),
        section: T('m4_title'),
        items: likertQs.map(q => ({
          id: q.id, dim: T('m4_title'), inv:(q.meta||{}).inverted||false,
          text: q.text, _apiId: q.id
        }))
      });
    }

    if (m4Qs.length) {
      mods.push({
        id:'m4_api', num: `${T('module_label')} 4`, title: T('m4_title'),
        desc: T('m4_description'),
        time:12*60, timeLabel:'12 minutes',
        instruction: T('m4_instruction'),
        header: `${T('module_label')} 4 · ${T('m4_title').toUpperCase()}`, questions: m4Qs
      });
    }
  }

  return mods;
}

async function submitToAPI() {
  if (!_token) return {ok: false, error: 'No token'};
  const answers = [];

  MODULES.forEach((mod, mIdx) => {
    const modNum = mIdx + 1;
    mod.questions.forEach(q => {
      const qid = q._apiId || q.id;
      const mNum = q._apiModule || modNum;

      if (q.type === 'qcm') {
        const ans = state.answers[q.id];
        if (ans !== undefined) answers.push({question_id:qid, module:mNum, response:{selected:ans}});

      } else if (q.type === 'likert') {
        (q.items||[]).forEach(item => {
          const v = state.answers[item.id];
          const iq = item._apiId || item.id;
          if (v !== undefined) answers.push({question_id:iq, module:mNum, response:{value:v}});
        });

      } else if (q.type === 'sjt') {
        const r = state.answers[q.id];
        if (r && r.length) answers.push({question_id:qid, module:mNum, response:{ranking:r}});

      } else if (q.type === 'value_rank') {
        const saved = state.answers[q.id] || {};
        const order = Object.keys(saved).sort((a,b)=>+a-+b).map(k=>saved[k]);
        if (order.length) answers.push({question_id:qid, module:mNum, response:{ranking:order}});
      }
    });
  });

  console.info(`[assessment] submit — ${answers.length} answers across modules:`,
    [...new Set(answers.map(a => a.module))].sort());

  try {
    const res = await fetch(`${API_BASE}/api/v1/test/${_token}/submit`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({answers})
    });
    if (res.ok) {
      _clearProgress();
      return {ok: true};
    }
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch (_) {
      try { detail = await res.text(); } catch (_) {}
    }
    console.error('[submit] failed:', detail);
    return {ok: false, error: detail};
  } catch(e) {
    console.error('[submit] network error:', e);
    return {ok: false, error: e.message || 'Erreur réseau'};
  }
}

function updateStepper() {
  const el = document.getElementById('k-stepper');
  if (!el || !MODULES.length) return;
  el.innerHTML = MODULES.map((m, i) => {
    const cls = i < state.moduleIdx ? 'done' : i === state.moduleIdx ? 'active' : '';
    const label = i < state.moduleIdx ? '✓' : `M${i+1}`;
    const sep = i < MODULES.length - 1 ? '<div class="k-step-sep"></div>' : '';
    return `<div class="k-step ${cls}"><div class="k-step-dot"></div>${label}</div>${sep}`;
  }).join('');
}

function showFinalConfirm() {
  if (document.getElementById('final-submit-overlay')) return;
  const total = MODULES.reduce((s,m) => s + m.questions.length, 0);
  const answered = MODULES.reduce((s,m) => s + m.questions.filter(q => isQuestionAnswered(q)).length, 0);
  const unanswered = total - answered;

  const overlay = document.createElement('div');
  overlay.id = 'final-submit-overlay';
  const unansweredSuffix = unanswered > 1 ? K.t('end_unanswered_suffix_plural') : K.t('end_unanswered_suffix_singular');
  overlay.innerHTML = `<div class="fs-box">
    <div class="fs-icon">🎯</div>
    <div class="fs-title">${K.t('end_finish_title')}</div>
    <div class="fs-text">
      ${unanswered > 0
        ? `<strong style="color:#6366F1;">${unanswered} ${unansweredSuffix}.</strong><br>`
        : ''}
      ${K.t('end_irreversible')}
    </div>
    <div class="fs-actions">
      <button class="btn btn-ghost" style="border:2px solid #ddd;border-radius:6px;" onclick="document.getElementById('final-submit-overlay').remove()">${K.t('btn_back')}</button>
      <button class="btn btn-primary" onclick="document.getElementById('final-submit-overlay').remove(); _doSubmit()">${K.t('btn_confirm')}</button>
    </div>
  </div>`;
  document.body.appendChild(overlay);
}

async function _doSubmit() {
  stopTimer();
  showScreen('screen-loading');
  document.querySelector('#screen-loading div div:first-child + div').textContent = K.t('submitting');
  const result = await submitToAPI();
  if (!result.ok) {
    return showError('network', result.error || 'Erreur lors de l\'envoi des réponses.');
  }
  showComplete();
}

const MODULES = [];

let state = {
  moduleIdx: 0,
  questionIdx: 0,
  answers: {},
  timerInterval: null,
  timeLeft: 0,
  phase: 'intro',
  startTime: null
};

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function initIntro() {
  const list = document.getElementById('intro-modules-list');
  if (!list) return;
  const totalMin = Math.round(MODULES.reduce((s, m) => s + m.time, 0) / 60);
  list.innerHTML = MODULES.map((m, i) =>
    `<div class="intro-module">
      <div class="mod-label">${K.t('module_label')} ${i + 1}</div>
      <div class="mod-name">${escHtml(m.title)}</div>
      <div class="mod-time">⏱ ${m.timeLabel}</div>
    </div>`
  ).join('');
  const note = document.getElementById('intro-note');
  if (note) note.innerHTML = `${K.t('intro_duration_lead')} <strong>${totalMin} ${K.t('intro_duration_unit')}</strong>.<br>${K.t('intro_setup')}`;
}

initFromAPI();

async function startAssessment() {

  if (_token) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/test/${_token}/start`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({consent_given: true, consent_version: 'v1.0'})
      });
      if (!res.ok && res.status !== 400) {
        const err = await res.json().catch(() => ({}));
        if (err.detail && err.detail.includes('complété')) return showError('completed');
      }
    } catch(e) { console.warn('[start]', e);  }
  }

  const hasRestored = state.moduleIdx > 0 || state.questionIdx > 0;
  if (!hasRestored) {
    state.moduleIdx  = 0;
    state.questionIdx = 0;
  }
  state.startTime = Date.now();
  showModuleIntro();
}

function showComplete() {
  const elapsed = state.startTime ? Math.round((Date.now() - state.startTime) / 60000) : 0;
  const modSummary = MODULES.map((m, i) => {
    const mAnswered = m.questions.filter(q => isQuestionAnswered(q)).length;
    return `<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
      <span style="color:#ccc;font-size:14px;">${escHtml(m.title)}</span>
      <span style="color:var(--gold);font-size:13px;font-weight:600;">${mAnswered}/${m.questions.length} ${K.t('answered_suffix')}</span>
    </div>`;
  }).join('');
  document.getElementById('complete-content').innerHTML = `
    <div style="font-size:52px;margin-bottom:20px;">🎯</div>
    <div class="complete-title">${K.t('complete_title')}</div>
    <div style="color:#aaa;font-size:16px;line-height:1.8;margin-bottom:24px;">${K.t('complete_thanks')}</div>
    <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:20px 28px;margin-bottom:32px;text-align:left;">
      ${modSummary}
      <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0 0;">
        <span style="color:#aaa;font-size:13px;">${K.t('complete_total_duration')}</span>
        <span style="color:var(--gold);font-size:14px;font-weight:700;">${elapsed < 1 ? K.t('duration_under_one') : elapsed + ' ' + K.t('duration_minutes_suffix')}</span>
      </div>
    </div>
    <div style="color:#aaa;font-size:14px;line-height:1.8;margin-bottom:24px;">${K.t('complete_followup')}</div>
    <div style="color:#444;font-size:12px;">${K.t('footer_acme')}</div>`;
  showScreen('screen-complete');
}

function showModuleIntro() {
  window.scrollTo(0, 0);
  const mod = MODULES[state.moduleIdx];
  const seqNum = state.moduleIdx + 1;
  document.getElementById('mi-num').textContent = K.t('module_label') + ' ' + seqNum + ' / ' + MODULES.length;
  document.getElementById('mi-title').textContent = mod.title;
  document.getElementById('mi-desc').textContent = mod.desc;
  document.getElementById('mi-time').textContent = '⏱ ' + mod.timeLabel;
  document.getElementById('mi-instruction').textContent = mod.instruction;
  showScreen('screen-module-intro');
}

function startModule() {
  const mod = MODULES[state.moduleIdx];
  state.questionIdx = 0;
  state.timeLeft = mod.time;
  startTimer();
  renderQuestion();
  showScreen('screen-question');
}

function prevQuestion() {
  if (state.questionIdx > 0) {
    state.questionIdx--;
    renderQuestion();
  }
}

function isQuestionAnswered(q) {
  if (!q) return false;
  if (q.type === 'qcm') return state.answers[q.id] !== undefined;
  if (q.type === 'likert') return q.items.every(item => state.answers[item.id] !== undefined);
  if (q.type === 'sjt') return (state.answers[q.id] || []).length === q.options.length;
  if (q.type === 'value_rank') return Object.keys(state.answers[q.id] || {}).length === q.cards.length;
  return true;
}

let _toastTimer = null;
function showToast(msg) {
  const el = document.getElementById('k-toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('show'), 2500);
}

function advanceModule() {
  stopTimer();
  state.moduleIdx++;
  _saveProgress();
  if (state.moduleIdx < MODULES.length) {
    showModuleIntro();
  } else {

    showFinalConfirm();
  }
}

function showModuleEndConfirm(unansweredCount) {
  const existing = document.getElementById('module-end-overlay');
  if (existing) existing.remove();
  const isLastModule = state.moduleIdx === MODULES.length - 1;
  const continueLabel = isLastModule ? K.t('end_finish_now') : K.t('end_continue_module');
  const unansweredSuffix = unansweredCount > 1 ? K.t('end_unanswered_suffix_plural') : K.t('end_unanswered_suffix_singular');
  const overlay = document.createElement('div');
  overlay.id = 'module-end-overlay';
  overlay.innerHTML = `
    <div class="me-box">
      <div class="me-icon">⚠️</div>
      <div class="me-title">${unansweredCount} ${unansweredSuffix}</div>
      <div class="me-actions">
        <button class="btn btn-ghost" style="border:2px solid #ddd;border-radius:6px;" onclick="document.getElementById('module-end-overlay').remove()">${K.t('btn_back')}</button>
        <button class="btn btn-primary" onclick="document.getElementById('module-end-overlay').remove(); advanceModule();">${continueLabel}</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
}

function nextQuestion() {
  const mod = MODULES[state.moduleIdx];
  const q = mod.questions[state.questionIdx];

  if (state.questionIdx < mod.questions.length - 1) {

    if (!isQuestionAnswered(q)) showToast('⚠️ Question sans réponse');
    state.questionIdx++;
    renderQuestion();
  } else {

    const unanswered = mod.questions.filter(q => !isQuestionAnswered(q)).length;
    if (unanswered > 0) {
      showModuleEndConfirm(unanswered);
    } else {
      advanceModule();
    }
  }
}

function startTimer() {
  stopTimer();
  updateTimerDisplay();
  state.timerInterval = setInterval(() => {
    state.timeLeft--;
    updateTimerDisplay();
    if (state.timeLeft <= 0) {
      timeUp();
    }
  }, 1000);
}

function timeUp() {
  stopTimer();

  const existing = document.getElementById('time-up-overlay');
  if (existing) existing.remove();
  const overlay = document.createElement('div');
  overlay.id = 'time-up-overlay';
  overlay.style.cssText = [
    'position:fixed','inset:0','background:rgba(10,38,32,0.93)',
    'display:flex','flex-direction:column','align-items:center','justify-content:center',
    'z-index:9999','animation:fadeIn 0.3s ease'
  ].join(';');
  const isLastMod = state.moduleIdx === MODULES.length - 1;
  const nextLabel = isLastMod ? K.t('end_finish_now') : K.t('time_per_module');
  overlay.innerHTML = `
    <div style="font-size:60px;margin-bottom:20px;">⏰</div>
    <div style="color:#6366F1;font-size:26px;font-weight:700;letter-spacing:3px;margin-bottom:12px;">${K.t('time_up_title')}</div>
    <div style="color:#aaa;font-size:15px;">${nextLabel}</div>
  `;
  document.body.appendChild(overlay);
  setTimeout(() => {
    overlay.remove();
    state.moduleIdx++;
    if (state.moduleIdx < MODULES.length) {
      showModuleIntro();
    } else {
      showComplete();
    }
  }, 2800);
}

function stopTimer() {
  if (state.timerInterval) { clearInterval(state.timerInterval); state.timerInterval = null; }
}

function updateTimerDisplay() {
  const el = document.getElementById('k-timer');
  if (!el) return;
  const m = Math.floor(state.timeLeft / 60).toString().padStart(2, '0');
  const s = (state.timeLeft % 60).toString().padStart(2, '0');
  el.textContent = m + ':' + s;
  el.classList.toggle('warning', state.timeLeft <= 120);
}

function renderQuestion() {
  window.scrollTo(0, 0);
  const mod = MODULES[state.moduleIdx];
  const q = mod.questions[state.questionIdx];
  const total = mod.questions.length;
  const pct = ((state.questionIdx + 1) / total * 100).toFixed(0);

  document.getElementById('hdr-module').textContent = 'MODULE ' + (state.moduleIdx + 1) + ' · ' + mod.title.toUpperCase();
  document.getElementById('hdr-progress').textContent = 'Q' + (state.questionIdx+1) + ' / ' + total + ' · Module ' + (state.moduleIdx+1) + '/' + MODULES.length;
  document.getElementById('progress-fill').style.width = pct + '%';
  document.getElementById('btn-prev').style.visibility = state.questionIdx === 0 ? 'hidden' : 'visible';
  updateStepper();
  _saveProgress();

  const isLast = state.questionIdx === total - 1;
  const isLastModule = state.moduleIdx === MODULES.length - 1;
  document.getElementById('btn-next').textContent = isLast
    ? (isLastModule ? 'Terminer l\'évaluation ✓' : 'Module suivant →')
    : 'Suivant →';

  const container = document.getElementById('question-content');
  container.className = 'k-content fade-in';

  if (q.type === 'qcm') renderQCM(container, q);
  else if (q.type === 'likert') renderLikert(container, q);
  else if (q.type === 'sjt') renderSJT(container, q);
  else if (q.type === 'value_rank') renderValueRank(container, q);
}

function renderQCM(container, q) {
  const saved = state.answers[q.id] || null;
  container.innerHTML = `
    <div class="q-section">${escHtml(q.section)}</div>
    <div class="q-text">${escHtml(q.text)}</div>
    <div class="qcm-options">
      ${q.options.map(o => `
        <div class="qcm-opt ${saved===o.k?'selected':''}" onclick="selectQCM('${q.id}','${o.k}',this.parentElement)">
          <div class="opt-key">${o.k}</div>
          <div class="opt-text">${escHtml(o.v)}</div>
        </div>
      `).join('')}
    </div>`;
}

function selectQCM(qid, key, parent) {
  state.answers[qid] = key;
  parent.querySelectorAll('.qcm-opt').forEach(el => {
    el.classList.toggle('selected', el.querySelector('.opt-key').textContent === key);
  });
}

function _likertLabels() { return [K.t('likert_1'), K.t('likert_2'), K.t('likert_3'), K.t('likert_4'), K.t('likert_5')]; }
const LIKERT_LABELS = new Proxy({}, { get(_, prop) { const arr = _likertLabels(); return arr[prop]; } });

function renderLikert(container, q) {
  const sectionHtml = q.section ? `<div class="q-section">${escHtml(q.section)}</div>` : '';
  container.innerHTML = `
    ${sectionHtml}
    <div class="likert-items">
      ${q.items.map(item => {
        const saved = state.answers[item.id];
        const isAnswered = saved !== undefined;
        const displayVal = isAnswered ? saved : 3;
        const pct = isAnswered ? ((saved-1)/4*100).toFixed(0) : 0;
        return `
        <div class="likert-item ${isAnswered ? '' : 'unanswered'}">
          <div class="li-dim">${escHtml(item.dim)}${item.inv ? ' · ' + K.t('likert_inverted_tag') : ''}</div>
          <div class="li-text">${escHtml(item.text)}</div>
          <div class="likert-scale">
            <div style="position:relative;height:22px;">
              <div class="likert-track" style="margin-top:8px;">
                <div class="likert-fill" id="lf-${item.id}" style="width:${pct}%"></div>
              </div>
              <input type="range" class="likert-input ${isAnswered ? '' : 'likert-untouched'}" min="1" max="5" value="${displayVal}"
                id="li-${item.id}"
                oninput="updateLikert('${item.id}',this.value)"
                style="position:absolute;top:0;left:0;width:100%;"/>
            </div>
            <div class="likert-labels">
              <span>1 — ${K.t('likert_1')}</span>
              <span style="text-align:center;">3 — ${K.t('likert_3')}</span>
              <span style="text-align:right;">5 — ${K.t('likert_5')}</span>
            </div>
            <div class="likert-value-display">
              <strong id="lv-${item.id}">${isAnswered ? LIKERT_LABELS[saved-1] : '—'}</strong>
            </div>
          </div>
        </div>`;
      }).join('')}
    </div>`;
}

function updateLikert(id, val) {
  val = parseInt(val);
  state.answers[id] = val;
  const pct = ((val-1)/4*100).toFixed(0);
  const fill = document.getElementById('lf-'+id);
  const lbl = document.getElementById('lv-'+id);
  const input = document.getElementById('li-'+id);
  if (fill) fill.style.width = pct + '%';
  if (lbl) lbl.textContent = LIKERT_LABELS[val-1];

  if (input) {
    input.classList.remove('likert-untouched');
    input.closest('.likert-item').classList.remove('unanswered');
  }
}

function renderSJT(container, q) {
  const saved = state.answers[q.id] || [];
  container.innerHTML = `
    <div class="q-section">${escHtml(q.section)}</div>
    ${q.illustration ? `
    <div style="display:flex;align-items:center;gap:14px;background:${q.illustration.color}18;border-left:4px solid ${q.illustration.color};border-radius:0 8px 8px 0;padding:12px 18px;margin-bottom:16px;">
      <span style="font-size:32px;line-height:1;">${q.illustration.icon}</span>
      <span style="font-size:12px;font-weight:700;color:${q.illustration.color};letter-spacing:1px;text-transform:uppercase;">${q.illustration.label}</span>
    </div>` : ''}
    <div class="sjt-scenario">
      <div class="sjt-label">${K.t('m3_situation_label')}</div>
      ${escHtml(q.scenario)}
    </div>
    <div class="sjt-instruction">${K.t('m3_drag_hint')}</div>
    <div class="sjt-columns">
      <div class="sjt-col">
        <div class="sjt-col-label">${K.t('m3_col_available')}</div>
        <div class="drop-zone" id="sjt-source" ondragover="dragOver(event)" ondragleave="dragLeave(event)" ondrop="dropToSource(event)">
          ${q.options.filter(o => !saved.includes(o.k)).map(o => `
            <div class="sjt-card" draggable="true" data-key="${o.k}"
              ondragstart="dragStart(event,'${o.k}')"
              ondragend="dragEnd(event)">
              <div class="card-key">${o.k}</div>
              <div>${escHtml(o.text)}</div>
            </div>`).join('')}
        </div>
      </div>
      <div class="sjt-col">
        <div class="sjt-col-label">${K.t('m3_col_ranked')}</div>
        <div class="drop-zone" id="sjt-ranked" ondragover="dragOver(event)" ondragleave="dragLeave(event)" ondrop="dropToRanked(event,'${q.id}')">
          ${saved.map((k,i) => {
            const opt = q.options.find(o=>o.k===k);
            return `<div class="sjt-card" draggable="true" data-key="${k}"
              ondragstart="dragStart(event,'${k}')"
              ondragend="dragEnd(event)">
              <div class="card-rank">${i+1}</div>
              <div>${escHtml(opt.text)}</div>
            </div>`;
          }).join('')}
        </div>
      </div>
    </div>`;
}

let draggedKey = null;

function dragStart(e, key) {
  draggedKey = key;
  e.currentTarget.classList.add('dragging');
  e.dataTransfer.effectAllowed = 'move';
}
function dragEnd(e) { e.currentTarget.classList.remove('dragging'); draggedKey = null; }
function dragOver(e) { e.preventDefault(); e.currentTarget.classList.add('drag-over'); }
function dragLeave(e) { e.currentTarget.classList.remove('drag-over'); }

function dropToRanked(e, qid) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!draggedKey) return;
  const q = MODULES[state.moduleIdx].questions[state.questionIdx];
  const ranked = [...(state.answers[qid] || [])];

  const existingIdx = ranked.indexOf(draggedKey);
  if (existingIdx > -1) ranked.splice(existingIdx, 1);

  const cards = e.currentTarget.querySelectorAll('.sjt-card');
  let insertIdx = ranked.length;
  for (let i = 0; i < cards.length; i++) {
    const rect = cards[i].getBoundingClientRect();
    if (e.clientY < rect.top + rect.height / 2) { insertIdx = i; break; }
  }
  ranked.splice(insertIdx, 0, draggedKey);
  state.answers[qid] = ranked;
  renderSJT(document.getElementById('question-content'), q);
}

function dropToSource(e) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!draggedKey) return;
  const q = MODULES[state.moduleIdx].questions[state.questionIdx];
  const ranked = state.answers[q.id] || [];
  const idx = ranked.indexOf(draggedKey);
  if (idx > -1) { ranked.splice(idx,1); state.answers[q.id] = ranked; }
  renderSJT(document.getElementById('question-content'), q);
}

function renderValueRank(container, q) {
  const saved = state.answers[q.id] || {};
  const usedKeys = Object.values(saved);
  container.innerHTML = `
    <div class="q-section">${escHtml(q.section)}</div>
    <div class="value-group-title">${q.groupNum} · ${escHtml(q.groupTitle)}</div>
    <div class="value-drag-hint">${K.t('m4_drag_hint')}</div>

    <div class="value-rank-slots">
      ${[1,2,3,4].map(n => {
        const cardKey = saved[n];
        const card = cardKey ? q.cards.find(c=>c.k===cardKey) : null;
        return `<div class="rank-slot ${card?'filled':''}" id="slot-${q.id}-${n}"
          ondragover="dragOver(event)" ondragleave="dragLeave(event)"
          ondrop="dropValueCard(event,'${q.id}',${n})">
          <div class="slot-badge">${n}</div>
          ${card
            ? `<div class="value-card" style="border:none;box-shadow:none;cursor:grab;width:100%;margin-top:4px;" draggable="true" data-key="${card.k}"
                ondragstart="dragStart(event,'${card.k}')" ondragend="dragEnd(event)">
                <div class="vc-drag">⠿</div>
                <span class="vc-icon">${card.icon}</span>
                <div class="vc-title">${card.title}</div>
              </div>`
            : `<div class="slot-label">déposez ici</div><div class="slot-arrow">⬇</div>`}
        </div>`;
      }).join('')}
    </div>

    <div class="sjt-col-label" style="margin-bottom:10px;">${K.t('m4_available_cards')}</div>
    <div class="value-cards-source" id="cards-source-${q.id}"
      ondragover="dragOver(event)" ondragleave="dragLeave(event)"
      ondrop="dropValueToSource(event,'${q.id}')">
      ${q.cards.filter(c => !usedKeys.includes(c.k)).map(c => `
        <div class="value-card" draggable="true" data-key="${c.k}"
          ondragstart="dragStart(event,'${c.k}')" ondragend="dragEnd(event)">
          <div class="vc-drag">⠿</div>
          <span class="vc-icon">${c.icon}</span>
          <div class="vc-title">${c.title}</div>
          <div class="vc-desc">${c.desc}</div>
        </div>`).join('')}
      ${usedKeys.length === 4
        ? `<div style="color:#2d9e6b;font-size:13px;font-weight:600;padding:16px;text-align:center;width:100%;">${K.t('m4_all_placed')}</div>`
        : ''}
    </div>`;
}

function dropValueCard(e, qid, rank) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!draggedKey) return;
  const q = MODULES[state.moduleIdx].questions[state.questionIdx];
  const saved = state.answers[qid] || {};

  Object.keys(saved).forEach(r => { if (saved[r] === draggedKey) delete saved[r]; });
  saved[rank] = draggedKey;
  state.answers[qid] = saved;
  renderValueRank(document.getElementById('question-content'), q);
}

function dropValueToSource(e, qid) {
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!draggedKey) return;
  const q = MODULES[state.moduleIdx].questions[state.questionIdx];
  const saved = state.answers[qid] || {};
  Object.keys(saved).forEach(r => { if (saved[r] === draggedKey) delete saved[r]; });
  state.answers[qid] = saved;
  renderValueRank(document.getElementById('question-content'), q);
}
