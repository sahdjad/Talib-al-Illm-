// Abu Aisha Video Engine – review UI (no build step). Talks to services/pipeline/abu_aisha/api.py.
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
let P = null; // current project view
let current = localStorage.getItem('aa.project') || null;

async function api(path, opts = {}) {
  const r = await fetch(path, {headers: opts.body && !(opts.body instanceof FormData) ? {'Content-Type': 'application/json'} : {}, ...opts,
    body: opts.body && !(opts.body instanceof FormData) ? JSON.stringify(opts.body) : opts.body});
  if (!r.ok) { const t = await r.text(); alert(`Fehler ${r.status}: ${t}`); throw new Error(t); }
  return r.json();
}
const post = (path, body = {}) => api(path, {method: 'POST', body});

/* ---------------- tabs ---------------- */
$$('#tabs button').forEach((b) => b.onclick = () => {
  $$('#tabs button').forEach((x) => x.classList.toggle('active', x === b));
  $$('.tab').forEach((t) => t.classList.toggle('active', t.id === 'tab-' + b.dataset.tab));
});

/* ---------------- projects ---------------- */
async function loadProjects() {
  const list = await api('/api/projects');
  $('#projectlist').innerHTML = list.map((p) => `<li><a href="#" data-p="${esc(p.name)}"><b>${esc(p.name)}</b></a>
    <span class="pill">${esc(p.state)}</span><br><span dir="auto">${esc(p.speaker)}</span> · ${esc(p.title || '')}</li>`).join('') || '<li>Noch keine Projekte.</li>';
  $$('#projectlist a').forEach((a) => a.onclick = (e) => { e.preventDefault(); open(a.dataset.p); });
}

$('#newform').onsubmit = async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  fd.set('intro', e.target.intro.checked ? 'true' : 'false');
  const r = await api('/api/projects', {method: 'POST', body: fd});
  await loadProjects();
  open(r.name);
};

async function open(name) {
  current = name; localStorage.setItem('aa.project', name);
  P = await api(`/api/projects/${name}`);
  renderAll();
}
const reload = async () => { if (current) { P = await api(`/api/projects/${current}`); renderAll(); } };

function renderAll() {
  if (!P) return;
  $('#ptitle').textContent = `${P.name} · ${P.speaker.arabic_display || P.speaker.user_supplied_name} · ${P.state}`;
  renderSegments(); renderTimelineTab(); renderQA(); renderFiles(); renderJob();
}

/* ---------------- text tab ---------------- */
function renderSegments() {
  const words = P.transcript.word_timings;
  const rows = P.timeline.map((s, i) => {
    const st = s.en_status === 'OK' ? 'ok' : 'warn';
    const lay = s.layout || {};
    const size = (l) => lay[l] ? `${lay[l].fontSize}px · ${lay[l].lines.length} Z.` : '–';
    const flags = (P.transcript.confidence_flags || []).filter((f) => f.word >= s.source_word_start && f.word <= s.source_word_end);
    return `<div class="seg" data-id="${s.id}">
      <div class="meta"><b>${s.id}</b><br>${s.start.toFixed(2)}–${s.end.toFixed(2)} s<br>Wörter ${s.source_word_start}–${s.source_word_end}
        ${flags.length ? `<br><span class="pill warn" title="${esc(flags.map((f) => f.reason).join('\n'))}">⚠ Transkript prüfen</span>` : ''}
        ${(s.reference_ids || []).length ? `<br><span class="pill">${esc(s.reference_ids.join(', '))}</span>` : ''}</div>
      <div class="ar">${esc(s.ar)}</div>
      <div><textarea rows="4" data-f="de">${esc(s.de)}</textarea><div class="meta">DE ${size('de')}</div></div>
      <div><textarea rows="4" data-f="en">${esc(s.en || '')}</textarea><div class="meta">EN ${size('en')} <span class="pill ${st}">${s.en_status}</span></div>
        <div class="actions">
          <button class="small" data-a="save">Speichern</button>
          ${s.en_status === 'STALE_EN' ? '<button class="small" data-a="confirm">EN bestätigen</button>' : ''}
          ${i < P.timeline.length - 1 ? '<button class="small" data-a="merge">Mit nächstem verbinden</button>' : ''}
          ${s.source_word_end > s.source_word_start ? '<button class="small" data-a="split">Teilen…</button>' : ''}
        </div></div></div>`;
  });
  $('#segtable').innerHTML = `<div class="seg head"><div>Block</div><div>Arabisch (gesprochen)</div><div>Deutsch (Master)</div><div>Englisch (aus DE)</div></div>` + rows.join('');
  $$('#segtable .seg[data-id]').forEach((row) => {
    const id = row.dataset.id;
    const seg = P.timeline.find((s) => s.id === id);
    $$('button', row).forEach((b) => b.onclick = async () => {
      const a = b.dataset.a;
      if (a === 'save') {
        const de = $('[data-f=de]', row).value, en = $('[data-f=en]', row).value;
        if (de !== seg.de) P = await post(`/api/projects/${current}/segments/${id}/de`, {text: de});
        if (en !== (seg.en || '')) P = await post(`/api/projects/${current}/segments/${id}/en`, {text: en});
        renderAll();
      } else if (a === 'confirm') {
        P = await post(`/api/projects/${current}/segments/${id}/confirm-en`); renderAll();
      } else if (a === 'merge') {
        const idx = P.timeline.findIndex((s) => s.id === id);
        P = await post(`/api/projects/${current}/merge`, {first: id, second: P.timeline[idx + 1].id}); renderAll();
      } else if (a === 'split') {
        const ws = words.slice(seg.source_word_start, seg.source_word_end + 1).map((w, k) => `${seg.source_word_start + k}:${w.text}`).join('  ');
        const at = prompt(`Teilen vor welchem Wort (Index)?\n${ws}`);
        if (!at) return;
        const de = prompt('Deutsch Teil 1 || Teil 2', seg.de.replace(/\n/g, ' ') + ' || ');
        if (!de || !de.includes('||')) return;
        const en = prompt('Englisch Teil 1 || Teil 2 (leer = später neu erzeugen)', (seg.en || '').replace(/\n/g, ' ') + ' || ');
        P = await post(`/api/projects/${current}/segments/${id}/split`, {
          at_word: +at, de: de.split('||').map((x) => x.trim()),
          en: en && en.includes('||') && en.split('||').every((x) => x.trim()) ? en.split('||').map((x) => x.trim()) : null});
        renderAll();
      }
    });
  });
}
$('#btn-editorial').onclick = async () => {
  if (!confirm('KI-Redaktion (Claude API) ausführen? Vorhandene Blöcke bleiben, falls schon vorhanden.')) return;
  await post(`/api/projects/${current}/run`, {preview: false, final: false}); pollJob();
};
$('#btn-regen').onclick = async () => { await post(`/api/projects/${current}/regen-en`); pollJob(); };

/* ---------------- timeline tab ---------------- */
function renderTimelineTab() {
  const eff = P.settings.mask.mode === 'manual' ? P.settings.mask : P.visual.mask_auto || {};
  $('#mask').value = eff.fade_start ?? 0.45; $('#maskval').textContent = `${(+$('#mask').value).toFixed(3)} (${P.settings.mask.mode})`;
  $('#intro-toggle').checked = !!P.settings.intro;
  $('#title-de').value = P.titles.chosen?.de || ''; $('#title-en').value = P.titles.chosen?.en || '';
  $('#titlesugs').innerHTML = (P.titles.suggestions || []).map((t, i) => `<button data-i="${i}" title="${esc(t.category)}">${esc(t.de)}</button>`).join('');
  $$('#titlesugs button').forEach((b) => b.onclick = () => { const t = P.titles.suggestions[b.dataset.i]; $('#title-de').value = t.de; $('#title-en').value = t.en || ''; });
  const [tin, tout] = P.trim_effective; const intro = P.settings.intro ? P.settings.intro_duration : 0; const total = intro + (tout - tin);
  const x = (t) => `${(t / total) * 100}%`;
  $('#timeline').innerHTML = (intro ? `<div class="intro" style="left:0;width:${x(intro)}">Intro</div>` : '') + P.timeline.map((s) =>
    `<div class="blk ${s.en_status !== 'OK' ? 'stale' : ''}" data-t="${intro + s.start - tin}" style="left:${x(intro + Math.max(s.start, tin) - tin)};width:${x(Math.min(s.end, tout) - Math.max(s.start, tin))}" title="${esc(s.de)}">${esc(s.de.split('\n')[0])}</div>`).join('');
  $$('#timeline .blk').forEach((b) => b.onclick = () => { $('#player').currentTime = +b.dataset.t; $('#player').play(); });
  const bounds = new Set(P.timeline.map((s) => s.source_word_end));
  $('#wordbar').innerHTML = P.transcript.word_timings.map((w) => `<span data-i="${w.i}" class="${bounds.has(w.i) ? 'b' : ''}" title="${w.i} · ${w.start.toFixed(2)}s">${esc(w.text)}</span>`).join(' ');
  $$('#wordbar span').forEach((sp) => sp.onclick = async () => {
    const i = +sp.dataset.i; const seg = P.timeline.find((s) => s.source_word_end + 1 >= i && s.source_word_start < i);
    if (!seg || !confirm(`Grenze nach ${seg.id} auf Wort ${i} („${sp.textContent}") setzen?`)) return;
    P = await post(`/api/projects/${current}/segments/${seg.id}/boundary`, {to_word: i}); renderAll();
  });
  const lang = $('#prevlang').value;
  const last = [...P.render_history].reverse().find((r) => r.lang === lang && r.status === 'OK');
  const key = last ? `${last.output}@${last.at}` : '';
  if (last && $('#player').dataset.key !== key) { $('#player').dataset.key = key; $('#player').src = `/api/projects/${current}/files/${last.output}?t=${Date.now()}`; }
}
$('#prevlang').onchange = renderTimelineTab;
$('#mask').oninput = () => $('#maskval').textContent = (+$('#mask').value).toFixed(3);
$('#mask-apply').onclick = async () => { const s = +$('#mask').value; P = await post(`/api/projects/${current}/mask`, {start: s, end: s + 0.16}); renderAll(); };
$('#mask-auto').onclick = async () => { P = await post(`/api/projects/${current}/mask`, {auto: true}); renderAll(); };
$('#btn-settings').onclick = async () => {
  P = await post(`/api/projects/${current}/settings`, {intro: $('#intro-toggle').checked, title_de: $('#title-de').value, title_en: $('#title-en').value});
  renderAll();
};
$('#btn-preview').onclick = async () => { await post(`/api/projects/${current}/render`, {lang: $('#prevlang').value, preview: true}); pollJob(); };
$('#btn-still').onclick = async () => {
  const f = Math.round(($('#player').currentTime || 5) * 30);
  await post(`/api/projects/${current}/render`, {lang: $('#prevlang').value, stills: [f]});
  pollJob(() => { $('#still').src = `/api/projects/${current}/files/previews/still_${$('#prevlang').value}_${String(f).padStart(5, '0')}.png?t=${Date.now()}`; });
};

/* ---------------- QA tab ---------------- */
function renderQA() {
  const q = P.qa || {};
  $('#gates').innerHTML = (q.gates || []).map((g) => `<tr><td>${g.ok ? '✅' : '❌'}</td><td>${g.n}. ${esc(g.gate)}</td><td class="hint">${esc(g.detail)}</td></tr>`).join('') || '<tr><td>Noch nicht geprüft.</td></tr>';
  $('#qaitems').innerHTML = (q.review_items || []).map((it) => `<li><span class="pill warn">${esc(it.kind)}</span> ${it.time != null ? `@ ${(+it.time).toFixed(1)} s` : ''}
    ${it.text ? `<b dir="auto">„${esc(it.text)}“</b>` : ''}<br><span class="hint">${esc(it.detail)}</span></li>`).join('') || '<li>Keine offenen Punkte.</li>';
  $('#notes').innerHTML = (P.editorial_notes || []).map((n) => `<li><span class="pill ${n.status.startsWith('VERIFIED') || n.status === 'APPROVED' ? 'ok' : 'warn'}">${n.status}</span>
    <b dir="auto">${esc(n.text.all || n.text.de)}</b> (${n.kind}, ${n.start.toFixed(1)}–${n.end.toFixed(1)} s)<br><span class="hint">${esc(n.provenance || '')}</span><br>
    <label class="check"><input type="checkbox" data-n="${n.id}" ${n.enabled ? 'checked' : ''}> einblenden</label>
    ${n.status === 'CHECK_REQUIRED' ? `<button class="small" data-ap="${n.id}">Quelle geprüft → freigeben</button>` : ''}</li>`).join('') || '<li>Keine.</li>';
  $$('#notes input[data-n]').forEach((c) => c.onchange = async () => { P = await post(`/api/projects/${current}/notes/${c.dataset.n}`, {enabled: c.checked}); renderAll(); });
  $$('#notes button[data-ap]').forEach((b) => b.onclick = async () => { P = await post(`/api/projects/${current}/notes/${b.dataset.ap}`, {approve: true}); renderAll(); });
  $('#checklist').innerHTML = (q.checklist || []).map((c) => `<li><label class="check"><input type="checkbox"> ${esc(c)}</label></li>`).join('');
}
$('#btn-qa').onclick = async () => { await post(`/api/projects/${current}/qa`); reload(); };
$('#btn-approve').onclick = async () => {
  if ($$('#checklist input').some((c) => !c.checked)) return alert('Bitte zuerst die Checkliste vollständig abhaken.');
  P = await post(`/api/projects/${current}/approve`); renderAll();
};

/* ---------------- export tab ---------------- */
function renderFiles() {
  const files = ['renders/AbuAisha_DE_1080x1920.mp4', 'renders/AbuAisha_EN_1080x1920.mp4', 'captions/de.srt', 'captions/en.srt',
    'text/transcript_ar.txt', 'text/translation_de.txt', 'text/translation_en.txt', 'text/segments.json', 'text/references.md',
    'text/qa_report.md', 'project.json'];
  $('#files').innerHTML = files.map((f) => `<li><a href="/api/projects/${current}/files/${f}" target="_blank">${f}</a></li>`).join('');
}
$('#btn-final-de').onclick = async () => { await post(`/api/projects/${current}/render`, {lang: 'de', preview: false}); pollJob(); };
$('#btn-final-en').onclick = async () => { await post(`/api/projects/${current}/render`, {lang: 'en', preview: false}); pollJob(); };

/* ---------------- jobs ---------------- */
function renderJob() {
  const j = P?.job; $('#jobbar').textContent = j ? `${j.label}: ${j.status}${j.error ? ' – ' + j.error.split('\n')[0] : ''}` : '';
}
let polling = null;
function pollJob(then) {
  clearInterval(polling);
  polling = setInterval(async () => {
    const j = await api(`/api/projects/${current}/job`);
    $('#jobbar').textContent = `${j.label || ''}: ${j.status}`;
    if (j.status !== 'running') { clearInterval(polling); await reload(); then && then(); if (j.status === 'failed') alert(j.error); }
  }, 2500);
}

loadProjects().then(() => current && open(current).catch(() => {}));
