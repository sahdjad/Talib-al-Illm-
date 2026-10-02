// Builder: content/*.txt (lightweight markup)  ->  out/cover.html, out/front.html, out/body.html
const fs = require('fs');
const path = require('path');
const orn = require('./ornaments');
const { hyphenateSync } = require('hyphen/de-1996');
const quran = require('./data/quran.json');

const DIR = __dirname;
const OUT = path.join(DIR, 'out');
fs.mkdirSync(OUT, { recursive: true });

// ---------------------------------------------------------------- fonts
const FONT = (pkg, file) => path.join(DIR, 'node_modules/@fontsource', pkg, 'files', file);
const b64 = (p) => fs.readFileSync(p).toString('base64');
const LATIN_EXT = 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF';
function face(fam, file, w, s, range) {
  return `@font-face{font-family:'${fam}';font-style:${s};font-weight:${w};font-display:block;`
    + `src:url(data:font/woff2;base64,${b64(file)}) format('woff2');${range ? `unicode-range:${range};` : ''}}`;
}
const fonts = [];
for (const [w, s] of [[400, 'normal'], [500, 'normal'], [600, 'normal'], [400, 'italic'], [600, 'italic']]) {
  fonts.push(face('EB Garamond', FONT('eb-garamond', `eb-garamond-latin-${w}-${s}.woff2`), w, s));
  fonts.push(face('EB Garamond', FONT('eb-garamond', `eb-garamond-latin-ext-${w}-${s}.woff2`), w, s, LATIN_EXT));
}
for (const [w, s] of [[500, 'normal'], [600, 'normal'], [600, 'italic']]) {
  fonts.push(face('Cormorant', FONT('cormorant-garamond', `cormorant-garamond-latin-${w}-${s}.woff2`), w, s));
  fonts.push(face('Cormorant', FONT('cormorant-garamond', `cormorant-garamond-latin-ext-${w}-${s}.woff2`), w, s, LATIN_EXT));
}
fonts.push(face('Amiri', FONT('amiri', 'amiri-arabic-400-normal.woff2'), 400, 'normal'));
fonts.push(face('Amiri', FONT('amiri', 'amiri-arabic-700-normal.woff2'), 700, 'normal'));
fonts.push(face('Scheherazade', FONT('scheherazade-new', 'scheherazade-new-arabic-400-normal.woff2'), 400, 'normal'));
const FONTCSS = fonts.join('\n');

// ---------------------------------------------------------------- sura names (transliteration)
const SURA = ['', 'al-Fātiḥah', 'al-Baqarah', 'Āl ʿImrān', 'an-Nisāʾ', 'al-Māʾidah', 'al-Anʿām', 'al-Aʿrāf', 'al-Anfāl', 'at-Tawbah', 'Yūnus', 'Hūd', 'Yūsuf', 'ar-Raʿd', 'Ibrāhīm', 'al-Ḥijr', 'an-Naḥl', 'al-Isrāʾ', 'al-Kahf', 'Maryam', 'Ṭā-Hā', 'al-Anbiyāʾ', 'al-Ḥajj', 'al-Muʾminūn', 'an-Nūr', 'al-Furqān', 'aš-Šuʿarāʾ', 'an-Naml', 'al-Qaṣaṣ', 'al-ʿAnkabūt', 'ar-Rūm', 'Luqmān', 'as-Sajdah', 'al-Aḥzāb', 'Sabaʾ', 'Fāṭir', 'Yā-Sīn', 'aṣ-Ṣāffāt', 'Ṣād', 'az-Zumar', 'Ġāfir', 'Fuṣṣilat', 'aš-Šūrā', 'az-Zuḫruf', 'ad-Duḫān', 'al-Jāṯiyah', 'al-Aḥqāf', 'Muḥammad', 'al-Fatḥ', 'al-Ḥujurāt', 'Qāf', 'aḏ-Ḏāriyāt', 'aṭ-Ṭūr', 'an-Najm', 'al-Qamar', 'ar-Raḥmān', 'al-Wāqiʿah', 'al-Ḥadīd', 'al-Mujādalah', 'al-Ḥašr', 'al-Mumtaḥanah', 'aṣ-Ṣaff', 'al-Jumuʿah', 'al-Munāfiqūn', 'at-Taġābun', 'aṭ-Ṭalāq', 'at-Taḥrīm', 'al-Mulk', 'al-Qalam', 'al-Ḥāqqah', 'al-Maʿārij', 'Nūḥ', 'al-Jinn', 'al-Muzzammil', 'al-Muddaṯṯir', 'al-Qiyāmah', 'al-Insān', 'al-Mursalāt', 'an-Nabaʾ', 'an-Nāziʿāt', 'ʿAbasa', 'at-Takwīr', 'al-Infiṭār', 'al-Muṭaffifīn', 'al-Inšiqāq', 'al-Burūj', 'aṭ-Ṭāriq', 'al-Aʿlā', 'al-Ġāšiyah', 'al-Fajr', 'al-Balad', 'aš-Šams', 'al-Layl', 'aḍ-Ḍuḥā', 'aš-Šarḥ', 'at-Tīn', 'al-ʿAlaq', 'al-Qadr', 'al-Bayyinah', 'az-Zalzalah', 'al-ʿĀdiyāt', 'al-Qāriʿah', 'at-Takāṯur', 'al-ʿAṣr', 'al-Humazah', 'al-Fīl', 'Quraiš', 'al-Māʿūn', 'al-Kauṯar', 'al-Kāfirūn', 'an-Naṣr', 'al-Masad', 'al-Iḫlāṣ', 'al-Falaq', 'an-Nās'];

function refLabel(ref) {
  const m = /^(\d+):(\d+)(?:[-–](\d+))?$/.exec(ref.trim());
  if (!m) return ref.trim();
  return `${SURA[+m[1]]} ${m[1]}:${m[2]}${m[3] ? '–' + m[3] : ''}`;
}

// ---------------------------------------------------------------- quran lookup
const MARK = (c) => (c >= 0x064B && c <= 0x065F) || c === 0x0670 || (c >= 0x06D6 && c <= 0x06ED) || c === 0x0640 || (c >= 0x08D3 && c <= 0x08FF);
const DROP = new Set([...'اوىيءؤئأإآٱ']);
function skeleton(s) {
  const n = []; const map = [];
  for (let i = 0; i < s.length; i++) {
    const code = s.codePointAt(i);
    if (MARK(code) || DROP.has(s[i]) || /\s/.test(s[i]) || s[i] === '۞') continue;
    n.push(s[i]); map.push(i);
  }
  return { n: n.join(''), map };
}
const quranReport = [];
function verseText(ref) {
  const m = /^(\d+):(\d+)(?:[-–](\d+))?$/.exec(ref.trim());
  if (!m) throw new Error('bad quran ref ' + ref);
  const s = quran[+m[1] - 1]; const a = +m[2]; const b = m[3] ? +m[3] : a;
  const parts = [];
  for (let k = a; k <= b; k++) { const v = s.verses.find((x) => x.id === k); if (!v) throw new Error('no verse ' + ref); parts.push(v.text); }
  return parts.join(' ');
}
function quranArabic(ref, fragment) {
  const full = verseText(ref);
  const trimStop = (x) => x.replace(/[\u06D6-\u06DC\u06DE\u06E9\s]+$/u, '');
  if (!fragment) { const f0 = trimStop(full); quranReport.push(`${ref}\t${f0}`); return f0; }
  const fr = skeleton(fragment).n;
  const sk = skeleton(full);
  const idx = sk.n.indexOf(fr);
  if (idx < 0) throw new Error(`Qur'an fragment not found in ${ref}: ${fragment}\n  verse: ${full}`);
  let start = sk.map[idx];
  let end = sk.map[idx + fr.length - 1] + 1;
  while (start > 0 && !/\s/.test(full[start - 1])) start--;
  while (end < full.length && !/\s/.test(full[end])) end++;
  const out = trimStop(full.slice(start, end).trim());
  quranReport.push(`${ref}\t${out}`);
  return out;
}

// ---------------------------------------------------------------- inline formatting
const AR_RE = /([؀-ۿﭐ-﷿ﹰ-﻿]+(?:[  ][؀-ۿﭐ-﷿ﹰ-﻿]+)*)/g;
const NOHY = /(iyy|yy|ah$|iya$|ūn$|ʿ|ʾ)/;
function hyphenText(s) {
  return s.replace(/[A-Za-zÄÖÜäöüß]{8,}/g, (w) => {
    if (NOHY.test(w)) return w;
    if (/^[A-Z][a-z]+(ah|ih|iyyah)$/.test(w)) return w;
    return hyphenateSync(w, { hyphenChar: '­', minWordLength: 8 });
  });
}
function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function inline(s, coll) {
  let t = esc(s);
  // inline Qur'an quotation: {{text|ref}} or {{text|ref|arabic fragment}}
  t = t.replace(/\{\{([\s\S]+?)\|([^|}]+?)(?:\|([^}]+?))?\}\}/g, (m, txt, ref, frag) => {
    if (coll && /^\d+:\d+/.test(ref.trim())) coll.push({ ref: ref.trim(), frag: frag ? frag.trim() : '' });
    return `<span class="qv">{&#8239;${txt}&#8239;}</span>&#8202;<span class="qvref">[${refLabel(ref)}]</span>`;
  });
  t = t.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
  t = t.replace(/\*([^*]+)\*/g, '<i>$1</i>');
  t = t.replace(/\[ar\]([\s\S]*?)\[\/ar\]/g, '<span lang="ar" dir="rtl" class="arw">$1</span>');
  t = t.replace(/\[\[(.+?)\]\]/g, '<span class="ins">[$1]</span>');
  // wrap remaining Arabic runs outside tags
  t = t.split(/(<[^>]+>)/).map((seg, i, arr) => {
    if (seg.startsWith('<')) return seg;
    return seg.replace(AR_RE, (m0, run) => (run === 'ﷺ' || run === 'ﷻ')
      ? `<span lang="ar" dir="rtl" class="arw hon">${run}</span>`
      : `<span lang="ar" dir="rtl" class="arw">${run}</span>`);
  }).join('');
  // hyphenation on text segments (skip inside Arabic spans)
  let inAr = 0;
  t = t.split(/(<[^>]+>)/).map((seg) => {
    if (seg.startsWith('<')) {
      if (/^<span[^>]*lang="ar"/.test(seg)) inAr++;
      else if (inAr && seg === '</span>') inAr--;
      return seg;
    }
    return inAr ? seg : hyphenText(seg);
  }).join('');
  return t;
}

// ---------------------------------------------------------------- parser
function parseFile(file) {
  const lines = fs.readFileSync(file, 'utf8').replace(/\r/g, '').split('\n');
  const nodes = [];
  let i = 0;
  const readUntil = (endTag) => {
    const buf = [];
    while (i < lines.length && lines[i].trim() !== endTag) { buf.push(lines[i]); i++; }
    if (i >= lines.length) throw new Error(`${file}: missing ${endTag}`);
    i++;
    return buf;
  };
  while (i < lines.length) {
    const ln = lines[i];
    const t = ln.trim();
    if (!t || t.startsWith('//')) { i++; continue; }
    if (t.startsWith('## ')) { nodes.push({ type: 'section', title: t.slice(3).trim() }); i++; continue; }
    if (t.startsWith('# ')) {
      const [a, b] = t.slice(2).split('|').map((x) => x.trim());
      nodes.push({ type: 'part', title: a, sub: b || '' }); i++; continue;
    }
    let mm;
    if ((mm = /^\[\[(MATN|SHARH)(?: (.+))?\]\]$/.exec(t))) {
      const kind = mm[1] === 'MATN' ? 'matn' : 'sharh';
      i++;
      const body = readUntil(kind === 'matn' ? '[[/MATN]]' : '[[/SHARH]]');
      nodes.push({ type: kind, label: mm[2] || '', items: parseBlock(body, file) });
      continue;
    }
    if (t === '[[NOTE]]') {
      i++;
      const body = readUntil('[[/NOTE]]');
      nodes.push({ type: 'note', text: body.map((x) => x.trim()).join(' ') });
      continue;
    }
    if (t.startsWith('[[ARB ')) { // arabic-only centered line (e.g. basmalah)
      nodes.push({ type: 'html', html: t.replace(/^\[\[ARB (.*)\]\]$/, '<div class="bism" lang="ar" dir="rtl">$1</div>') }); i++; continue;
    }
    throw new Error(`${file}:${i + 1}: unexpected line: ${t.slice(0, 80)}`);
  }
  return nodes;
}

function parseBlock(body, file) {
  const items = [];
  let j = 0;
  const para = [];
  const flush = () => {
    if (!para.length) return;
    // lists
    const joined = para.slice();
    para.length = 0;
    if (joined.every((l) => /^- /.test(l))) { items.push({ k: 'ul', li: joined.map((l) => l.slice(2)) }); return; }
    if (joined.every((l) => /^\d+\. /.test(l))) { items.push({ k: 'ol', li: joined.map((l) => l.replace(/^\d+\. /, '')) }); return; }
    items.push({ k: 'p', text: joined.join(' ') });
  };
  while (j < body.length) {
    const ln = body[j]; const t = ln.trim();
    if (!t) { flush(); j++; continue; }
    if (t.startsWith('### ')) { flush(); items.push({ k: 'h3', text: t.slice(4) }); j++; continue; }
    let m;
    if ((m = /^\[\[Q (.+)\]\]$/.exec(t))) {
      flush(); j++;
      const buf = [];
      while (j < body.length && body[j].trim() !== '[[/Q]]') { buf.push(body[j].trim()); j++; }
      j++;
      let ar = '', de = '';
      for (const b of buf) { if (b.startsWith('ar:')) ar = b.slice(3).trim(); else if (b.startsWith('de:')) de = b.slice(3).trim(); else de += ' ' + b; }
      items.push({ k: 'q', ref: m[1].trim(), ar, de: de.trim() });
      continue;
    }
    if ((m = /^\[\[H(?: (.+))?\]\]$/.exec(t))) {
      flush(); j++;
      const buf = [];
      while (j < body.length && body[j].trim() !== '[[/H]]') { buf.push(body[j].trim()); j++; }
      j++;
      items.push({ k: 'h', src: (m[1] || '').trim(), text: buf.join(' ') });
      continue;
    }
    if (t === '[[PULL]]') {
      flush(); j++;
      const buf = [];
      while (j < body.length && body[j].trim() !== '[[/PULL]]') { buf.push(body[j].trim()); j++; }
      j++;
      items.push({ k: 'pull', text: buf.join(' ') });
      continue;
    }
    if (t === '[[P]]') {
      flush(); j++;
      const buf = [];
      while (j < body.length && body[j].trim() !== '[[/P]]') { buf.push(body[j].trim()); j++; }
      j++;
      items.push({ k: 'poem', lines: buf });
      continue;
    }
    if (t === '[[NOTE]]') {
      flush(); j++;
      const buf = [];
      while (j < body.length && body[j].trim() !== '[[/NOTE]]') { buf.push(body[j].trim()); j++; }
      j++;
      items.push({ k: 'note', text: buf.join(' ') });
      continue;
    }
    if ((m = /^\[\[SRC (.+)\]\]$/.exec(t))) { flush(); items.push({ k: 'src', text: m[1] }); j++; continue; }
    para.push(t); j++;
  }
  flush();
  return items;
}

// ---------------------------------------------------------------- html renderers
const MATN_LABEL = `<div class="lab lab-matn"><span class="lab-t">Text von Šayḫ al-Islām Ibn Taymiyyah</span><span class="lab-ar" lang="ar" dir="rtl">رحمه الله</span><span class="lab-rule"></span><span class="lab-ar lab-end" lang="ar" dir="rtl">هذا المتن</span></div>`;
const SHARH_LABEL = `<div class="lab lab-sharh"><span class="lab-t">Erklärung von Abū Muḥammad as-Sanzakī</span><span class="lab-rule"></span><span class="lab-ar lab-end" lang="ar" dir="rtl">وهذا الشرح</span></div>`;

function mini(coll) {
  if (!coll.length) return '';
  const rows = coll.map((c) => `<div class="am-row"><span class="am-ar" lang="ar" dir="rtl">&#xFD3F;${quranArabic(refOnly(c.ref), c.frag)}&#xFD3E;</span><span class="am-ref">${refLabel(c.ref)}</span></div>`).join('');
  return `<div class="ayah-mini">${rows}</div>`;
}
function renderItems(items) {
  return items.map((it) => {
    switch (it.k) {
      case 'p': { const c = []; const h = inline(it.text, c); return `<p>${h}</p>${mini(c)}`; }
      case 'h3': return `<h3>${inline(it.text)}</h3>`;
      case 'ul': { const c = []; const h = it.li.map((l) => `<li>${inline(l, c)}</li>`).join(''); return `<ul>${h}</ul>${mini(c)}`; }
      case 'ol': { const c = []; const h = it.li.map((l) => `<li>${inline(l, c)}</li>`).join(''); return `<ol>${h}</ol>${mini(c)}`; }
      case 'q': {
        const ar = it.ar === '-' ? '' : quranArabic(refOnly(it.ref), it.ar);
        return `<div class="ayah">${ar ? `<div class="ayah-ar" lang="ar" dir="rtl">&#xFD3F;${ar}&#xFD3E;</div>` : ''}<div class="ayah-de">${inline(it.de)}</div><div class="ayah-ref">${refLabel(it.ref)}</div></div>`;
      }
      case 'h': return `<div class="hadith"><div class="hadith-de">${inline(it.text)}</div>${it.src ? `<div class="hadith-ref">${inline(it.src)}</div>` : ''}</div>`;
      case 'pull': { const c = []; const h = inline(it.text, c); return `<div class="pull">${h}</div>${mini(c)}`; }
      case 'poem': return `<div class="poem">${it.lines.map((l) => `<span>${inline(l)}</span>`).join('<br>')}</div>`;
      case 'note': return `<div class="note">${inline(it.text)}</div>`;
      case 'src': return `<div class="src">${inline(it.text)}</div>`;
      default: return '';
    }
  }).join('\n');
}
function refOnly(ref) { return ref.replace(/^.*?(\d+:\d+(?:[-–]\d+)?)$/, '$1'); }

// ---------------------------------------------------------------- css
const C = { deep: '#0b3a2b', deep2: '#08301f', emerald: '#14543f', matn: '#0c2f24', sharh: '#2f3a46', head: '#8a6a2c', gold: '#b0863a', rule: '#cfc4a8', paper: '#ffffff', tint: '#f5f1e4', tintG: '#ebf2ee' };
const palCover = { ringLight: '#79b096', ornMid: '#1f6f52', ornDeep: '#123f2f', gold: '#c9a24e', medallion: '#0e4636' };
const palPage = { dividerInk: C.emerald, gold: C.gold, frameInk: '#2c6b51', medallion: '#fff' };

const CSS = `
${FONTCSS}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-print-color-adjust:exact;print-color-adjust:exact;}
body{font-family:'EB Garamond',serif;font-size:11.6pt;line-height:1.46;color:${C.sharh};background:#fff;text-align:justify;hyphens:manual;text-rendering:optimizeLegibility;font-variant-ligatures:common-ligatures;}
i,em{font-style:italic}
b{font-weight:600}
[lang=ar]{font-family:'Amiri','Scheherazade',serif;}
.arw{font-size:1.08em;line-height:1;unicode-bidi:isolate;}
p{margin:0 0 2.2mm 0;orphans:2;widows:2;}
.ins{font-style:italic}
.hon{font-size:1.28em;vertical-align:-.06em;margin:0 .04em}

/* --- part & section headings --- */
.part{break-before:page;text-align:center;padding:2mm 0 5mm 0;margin-bottom:3mm;}
.part:first-child{break-before:auto}
.part-title{font-family:'Cormorant',serif;font-weight:600;font-size:21pt;letter-spacing:.04em;color:${C.matn};line-height:1.15;}
.part-sub{font-family:'Cormorant',serif;font-style:italic;font-weight:600;font-size:12.5pt;color:${C.head};margin-top:1.5mm}
.part-orn svg{width:70mm;height:auto;display:block;margin:2.5mm auto 0}
.sec{margin:6.5mm 0 2.6mm 0;break-after:avoid;break-inside:avoid;text-align:left;}
.sec-h{display:flex;align-items:baseline;gap:3mm;border-bottom:.35mm solid ${C.rule};padding-bottom:1.1mm}
.sec-n{font-family:'Cormorant',serif;font-weight:600;font-size:13pt;color:${C.gold};min-width:7mm}
.sec-t{font-family:'Cormorant',serif;font-weight:600;font-size:14.2pt;color:${C.head};line-height:1.2;letter-spacing:.01em}

/* --- labels --- */
.lab{display:flex;align-items:center;gap:2.2mm;margin:3.2mm 0 1.6mm 0;break-after:avoid;break-inside:avoid;text-align:left}
.lab-t{font-family:'Cormorant',serif;font-weight:600;font-size:9.1pt;letter-spacing:.11em;text-transform:uppercase;white-space:nowrap}
.lab-ar{font-family:'Amiri',serif;font-size:11pt;line-height:1}
.lab-end{font-size:12pt;font-weight:700}
.lab-rule{flex:1;height:0;border-top:.3mm solid currentColor;opacity:.45}
.lab-matn{color:${C.emerald}}
.lab-sharh{color:${C.head}}

/* --- matn block --- */
.matn{background:${C.tint};border-left:1.1mm solid ${C.emerald};padding:2.6mm 4mm 1.2mm 4.2mm;margin:0 0 3mm 0;color:${C.matn};border-radius:0 1mm 1mm 0}
.matn-alt{background:#f8f6ee;border-left-color:#7ea593}
.lab-alt{color:#4d7a66}
.matn p{color:${C.matn}}
.matn h3{color:${C.matn}}
/* --- sharh block --- */
.sharh{color:${C.sharh};margin:0 0 3mm 0;padding:0 0 0 0}
.sharh h3{font-family:'Cormorant',serif;font-weight:600;font-size:12.2pt;color:${C.head};margin:3.4mm 0 1.2mm 0;break-after:avoid;text-align:left;letter-spacing:.01em}
.sharh ul,.sharh ol,.matn ul,.matn ol{margin:0 0 2.2mm 6mm;text-align:justify}
.sharh li,.matn li{margin-bottom:1mm}
.sharh ul{list-style:none;margin-left:3mm}
.sharh ul li{position:relative;padding-left:4mm}
.sharh ul li::before{content:'';position:absolute;left:0;top:.58em;width:1.3mm;height:1.3mm;background:${C.gold};transform:rotate(45deg)}

/* --- verse / hadith boxes --- */
.ayah{background:${C.tintG};border:.25mm solid #b7cdc2;border-radius:1.2mm;padding:2.2mm 4mm 1.6mm 4mm;margin:2.2mm 0 3mm 0;text-align:center;break-inside:avoid;color:${C.matn}}
.ayah-ar{font-family:'Amiri',serif;font-size:17.5pt;line-height:1.75;color:#0a2a20;margin-bottom:.8mm}
.ayah-de{font-style:italic;font-size:11.3pt;line-height:1.38;text-align:center;color:${C.matn}}
.ayah-ref{font-family:'Cormorant',serif;font-weight:600;font-size:9.2pt;letter-spacing:.09em;color:${C.emerald};margin-top:1mm}
.ayah-mini{background:${C.tintG};border:.25mm solid #c3d6cc;border-radius:1mm;padding:1.1mm 3mm .6mm 3mm;margin:-.6mm 0 2.6mm 0;break-inside:avoid;text-align:left}
.am-row{display:flex;justify-content:space-between;align-items:baseline;gap:4mm;direction:ltr;padding:.3mm 0}
.am-ar{font-family:'Amiri',serif;font-size:14.2pt;line-height:1.7;color:#0a2a20;direction:rtl;text-align:right;flex:1}
.am-ref{font-family:'Cormorant',serif;font-weight:600;font-size:8.6pt;letter-spacing:.08em;color:${C.emerald};white-space:nowrap;order:-1}
.hadith{background:#f6eedc;border-left:1mm solid ${C.gold};padding:2mm 3.6mm 1.3mm 4mm;margin:2.2mm 0 3mm 0;break-inside:avoid;border-radius:0 1mm 1mm 0;color:${C.matn}}
.hadith-de{font-size:11.3pt;line-height:1.4}
.hadith-ref{font-size:9.6pt;font-style:italic;color:#6b5a30;margin-top:.8mm;text-align:right}
.qv{font-style:italic}
.qvref{font-size:.86em;color:${C.emerald};white-space:nowrap}
.pull{text-align:center;font-style:italic;color:${C.matn};margin:2mm 5mm 2.6mm 5mm;line-height:1.42;break-inside:avoid}
.poem{text-align:center;font-style:italic;color:${C.matn};margin:2mm 0 3mm 0;line-height:1.5;break-inside:avoid}
.src{font-size:9.6pt;font-style:italic;color:#6b5a30;margin:-1.2mm 0 2.4mm 0;text-align:left}
.note{font-size:10pt;font-style:italic;color:#59636d;border-top:.25mm dashed ${C.rule};border-bottom:.25mm dashed ${C.rule};padding:1.2mm 2mm;margin:2mm 0 3mm 0;text-align:left}
.bism{text-align:center;font-family:'Amiri',serif;font-size:19pt;color:${C.matn};margin:1mm 0 2mm 0}

/* --- TOC --- */
.toc h2{font-family:'Cormorant',serif;font-size:20pt;color:${C.matn};text-align:center;margin-bottom:5mm;font-weight:600;letter-spacing:.05em}
.toc .tp{font-family:'Cormorant',serif;font-weight:600;font-size:13.2pt;color:${C.matn};margin:4.2mm 0 1mm 0;display:flex;gap:2mm;text-align:left}
.toc .ts{font-size:10.9pt;display:flex;gap:2mm;margin-left:6mm;line-height:1.28;text-align:left;color:${C.sharh}}
.toc .tn{min-width:7mm;color:${C.gold};font-family:'Cormorant',serif;font-weight:600}
.toc .tl{flex:1;border-bottom:.25mm dotted #b9ae92;margin:0 1mm 1.1mm 1mm;min-width:6mm;order:2}
.toc .tt{order:1}
.toc .tpg{order:3;min-width:7mm;text-align:right}
.toc .ts .tn{order:0}
.toc .tp .tt{order:1}
.toc .tp .tl{order:2}
.toc .tp .tpg{order:3}

/* --- title page / notes page --- */
.title{text-align:center;padding-top:34mm;color:${C.matn}}
.title .ar{font-family:'Amiri',serif;font-size:42pt;line-height:1.35;color:${C.emerald}}
.title h1{font-family:'Cormorant',serif;font-weight:600;font-size:30pt;letter-spacing:.03em;margin-top:6mm;line-height:1.15}
.title .sub{font-family:'Cormorant',serif;font-style:italic;font-weight:600;font-size:15pt;color:${C.head};margin-top:3mm}
.title .orn svg{width:90mm;display:block;margin:8mm auto}
.title .who{font-size:12.6pt;line-height:1.7;margin-top:6mm}
.title .who b{font-weight:600}
.pg{break-before:page}
.hn h2{font-family:'Cormorant',serif;font-size:19pt;color:${C.matn};font-weight:600;margin-bottom:4mm;text-align:center;letter-spacing:.04em}
.hn p{margin-bottom:2.6mm}
.hn .tbl{width:100%;border-collapse:collapse;margin:2mm 0 4mm 0;font-size:11pt}
.hn .tbl td{padding:1.3mm 2.5mm;border-bottom:.25mm solid ${C.rule};vertical-align:top;text-align:left}
.hn .tbl td:first-child{width:46mm}
.sw{display:inline-block;width:9mm;height:3.4mm;vertical-align:middle;margin-right:2mm;border-radius:.6mm}
`;

// ---------------------------------------------------------------- cover
const mandala = orn.coverMandala(palCover);
const COVER = `<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
${FONTCSS}
@page{size:210mm 297mm;margin:0}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:210mm;height:297mm;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.cover{position:relative;width:210mm;height:297mm;overflow:hidden;background:radial-gradient(120% 90% at 50% 38%, #10493690 0%, ${C.deep} 46%, ${C.deep2} 100%), ${C.deep};display:flex;flex-direction:column;align-items:center;color:#fff;}
.kick{margin-top:25mm;font-family:'Cormorant',serif;font-weight:600;letter-spacing:.34em;font-size:12pt;color:#c9a24e;text-transform:uppercase}
.mand{position:absolute;left:50%;top:50%;transform:translate(-50%,-46%);width:176mm;height:176mm}
.mand svg{width:100%;height:100%}
.ar{position:absolute;left:0;right:0;top:50%;transform:translateY(-92%);text-align:center;font-family:'Amiri',serif;font-size:50pt;line-height:1.5;color:#fff;text-shadow:0 0 6mm #0b3a2b}
.ar2{position:absolute;left:0;right:0;top:50%;transform:translateY(-8%);text-align:center;font-family:'Amiri',serif;font-size:50pt;line-height:1.5;color:#fff;text-shadow:0 0 6mm #0b3a2b}
.bot{position:absolute;left:0;right:0;bottom:19mm;text-align:center}
.bot .t{font-family:'Cormorant',serif;font-weight:600;font-size:23pt;letter-spacing:.03em}
.bot .s{font-family:'Cormorant',serif;font-style:italic;font-weight:600;font-size:13.5pt;color:#d8bf80;margin-top:1.5mm}
.bot .w{font-size:11.4pt;line-height:1.6;margin-top:5mm;color:#e8efe9}
.bot .w span{color:#c9a24e}
.bot .rule{width:60mm;height:0;border-top:.3mm solid #c9a24e;margin:4mm auto 0 auto;opacity:.8}
</style></head><body><div class="cover">
<div class="kick">Šarḥ</div>
<div class="mand">${mandala}</div>
<div class="ar" lang="ar" dir="rtl">الفتوى</div>
<div class="ar2" lang="ar" dir="rtl">الحموية</div>
<div class="bot"><div class="t">al-Fatwā al-Ḥamawiyyah</div><div class="s">Text und Erklärung – eine deutsche Ausgabe</div><div class="rule"></div>
<div class="w"><span>Text:</span> Šayḫ al-Islām Ibn Taymiyyah <span lang="ar" dir="rtl" style="font-family:Amiri">رحمه الله</span><br><span>Erklärung:</span> Abū Muḥammad as-Sanzakī</div></div>
</div></body></html>`;

// ---------------------------------------------------------------- front matter
function frontHtml(tocHtml) {
  return `<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@page{size:210mm 297mm;margin:16mm 17mm 18mm 17mm}${CSS}</style></head><body>
<section class="title">
  <div class="ar" lang="ar" dir="rtl">شرح الفتوى الحموية</div>
  <h1>Šarḥ al-Fatwā al-Ḥamawiyyah</h1>
  <div class="sub">Text von Šayḫ al-Islām Ibn Taymiyyah und Erklärung des Šāriḥ</div>
  <div class="orn">${orn.chapterDivider(palPage)}</div>
  <div class="who"><b>Text (Matn):</b> Šayḫ al-Islām Aḥmad ibn ʿAbd al-Ḥalīm ibn Taymiyyah <span lang="ar" dir="rtl">رحمه الله</span><br>
  <b>Erklärung (Šarḥ):</b> Abū Muḥammad as-Sanzakī<br>
  <b>Aus dem Arabischen und Deutschen redigiert</b></div>
</section>
<section class="hn pg">
${fs.existsSync(path.join(DIR, 'content/_hinweise.html')) ? fs.readFileSync(path.join(DIR, 'content/_hinweise.html'), 'utf8') : ''}
</section>
<section class="toc pg">${tocHtml}</section>
</body></html>`;
}

// ---------------------------------------------------------------- body
function build(pageMap) {
  const files = fs.readdirSync(path.join(DIR, 'content')).filter((f) => /^\d.*\.txt$/.test(f)).sort();
  const nodes = [];
  for (const f of files) nodes.push(...parseFile(path.join(DIR, 'content', f)));
  let secN = 0;
  const toc = [];
  const html = [];
  let partN = 0;
  for (const nd of nodes) {
    if (nd.type === 'part') {
      partN++;
      const id = `p${partN}`;
      toc.push({ kind: 'part', id, title: nd.title });
      html.push(`<section class="part" id="${id}"><div class="part-title">${inline(nd.title)}</div>${nd.sub ? `<div class="part-sub">${inline(nd.sub)}</div>` : ''}<div class="part-orn">${orn.chapterDivider(palPage)}</div></section>`);
    } else if (nd.type === 'section') {
      secN++;
      const id = `s${secN}`;
      toc.push({ kind: 'sec', id, n: secN, title: nd.title });
      html.push(`<div class="sec" id="${id}"><div class="sec-h"><span class="sec-n">${secN}</span><span class="sec-t">${inline(nd.title)}</span></div></div>`);
    } else if (nd.type === 'matn') {
      const lab = nd.label
        ? `<div class="lab lab-matn lab-alt"><span class="lab-t">${inline(nd.label)}</span><span class="lab-rule"></span></div>`
        : MATN_LABEL;
      html.push(`${lab}<div class="matn${nd.label ? ' matn-alt' : ''}">${renderItems(nd.items)}</div>`);
    } else if (nd.type === 'sharh') {
      html.push(`${SHARH_LABEL}<div class="sharh">${renderItems(nd.items)}</div>`);
    } else if (nd.type === 'note') {
      html.push(`<div class="note">${inline(nd.text)}</div>`);
    } else if (nd.type === 'html') {
      html.push(nd.html);
    }
  }
  const tocHtml = '<h2>Inhalt</h2>' + toc.map((t) => {
    const pg = pageMap && pageMap[t.id] != null ? pageMap[t.id] : '';
    if (t.kind === 'part') return `<div class="tp"><span class="tt">${inline(t.title)}</span><span class="tl"></span><span class="tpg">${pg}</span></div>`;
    return `<div class="ts"><span class="tn">${t.n}</span><span class="tt">${inline(t.title)}</span><span class="tl"></span><span class="tpg">${pg}</span></div>`;
  }).join('\n');
  const bodyHtml = `<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@page{size:210mm 297mm;margin:16mm 16mm 18mm 16mm}${CSS}</style></head><body>
${html.join('\n')}
</body></html>`;
  return { bodyHtml, tocHtml, toc };
}

module.exports = { build, frontHtml, COVER, quranReport, OUT };

if (require.main === module) {
  const { bodyHtml, tocHtml, toc } = build(null);
  fs.writeFileSync(path.join(OUT, 'body.html'), bodyHtml);
  fs.writeFileSync(path.join(OUT, 'front.html'), frontHtml(tocHtml));
  fs.writeFileSync(path.join(OUT, 'cover.html'), COVER);
  fs.writeFileSync(path.join(OUT, 'toc.json'), JSON.stringify(toc, null, 1));
  fs.writeFileSync(path.join(OUT, 'quran-report.txt'), quranReport.join('\n'));
  console.log('built', toc.length, 'toc entries;', quranReport.length, 'quran refs');
}
