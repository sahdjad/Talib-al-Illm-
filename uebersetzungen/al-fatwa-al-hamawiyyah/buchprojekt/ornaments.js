// Geometric Islamic ornament generator (SVG strings).
// Rotational symmetry helpers -> mandala cover, page frame corners, chapter dividers.

const CX = 500, CY = 500;

// polar -> cartesian, theta measured from top (12 o'clock), clockwise, in degrees
function P(cx, cy, r, thetaDeg) {
  const t = (thetaDeg - 90) * Math.PI / 180; // 0deg => top
  return [cx + r * Math.cos(t), cy + r * Math.sin(t)];
}
function f(n) { return Number(n.toFixed(2)); }
function pt(cx, cy, r, th) { const [x, y] = P(cx, cy, r, th); return `${f(x)},${f(y)}`; }

// A symmetric pointed leaf/petal from rBase to rTip, bulge angle `a` (deg), centered at angle th
function petalPath(cx, cy, rBase, rTip, a, th) {
  const b0 = P(cx, cy, rBase, th);
  const tip = P(cx, cy, rTip, th);
  const midOut = rBase + 0.42 * (rTip - rBase);
  const nearTip = rTip - 0.14 * (rTip - rBase);
  const cR1 = P(cx, cy, midOut, th + a);
  const cR2 = P(cx, cy, nearTip, th + a * 0.55);
  const cL2 = P(cx, cy, nearTip, th - a * 0.55);
  const cL1 = P(cx, cy, midOut, th - a);
  return `M ${f(b0[0])} ${f(b0[1])} `
    + `C ${f(cR1[0])} ${f(cR1[1])} ${f(cR2[0])} ${f(cR2[1])} ${f(tip[0])} ${f(tip[1])} `
    + `C ${f(cL2[0])} ${f(cL2[1])} ${f(cL1[0])} ${f(cL1[1])} ${f(b0[0])} ${f(b0[1])} Z`;
}

function ring(count, offset, fn) {
  let s = '';
  const step = 360 / count;
  for (let i = 0; i < count; i++) s += fn(offset + i * step, i);
  return s;
}

function circle(r, attrs) { return `<circle cx="${CX}" cy="${CY}" r="${f(r)}" ${attrs}/>`; }

// Star polygon {n/m}
function starPolygon(cx, cy, r, n, m, attrs) {
  const pts = [];
  let idx = 0;
  for (let i = 0; i < n; i++) { pts.push(pt(cx, cy, r, (idx * 360 / n))); idx = (idx + m) % n; }
  return `<polygon points="${pts.join(' ')}" ${attrs}/>`;
}

// ---------------------------------------------------------------------------
// COVER MANDALA  (viewBox 0 0 1000 1000)
// ---------------------------------------------------------------------------
function coverMandala(pal) {
  const gLight = pal.ringLight;      // thin ring stroke
  const gMid = pal.ornMid;           // mid petals
  const gDeep = pal.ornDeep;         // deep petals
  const gold = pal.gold;
  let inner = '';

  // outermost thin guide rings
  inner += circle(492, `fill="none" stroke="${gLight}" stroke-width="1.4" opacity="0.55"`);
  inner += circle(486, `fill="none" stroke="${gLight}" stroke-width="0.8" opacity="0.4"`);

  // Ring A : 32 slim outward petals (scalloped mandala edge)
  inner += `<g fill="none" stroke="${gMid}" stroke-width="2" opacity="0.85">`
    + ring(32, 0, (th) => `<path d="${petalPath(CX, CY, 402, 480, 4.6, th)}"/>`) + `</g>`;
  // small dot at each petal tip
  inner += `<g fill="${gLight}" opacity="0.7">`
    + ring(32, 0, (th) => { const [x, y] = P(CX, CY, 486, th); return `<circle cx="${f(x)}" cy="${f(y)}" r="2.4"/>`; }) + `</g>`;

  // double ring
  inner += circle(398, `fill="none" stroke="${gLight}" stroke-width="2" opacity="0.7"`);
  inner += circle(388, `fill="none" stroke="${gLight}" stroke-width="0.9" opacity="0.5"`);

  // Ring B : 16 filled outward leaves overlapping the edge
  inner += `<g opacity="0.9">`
    + ring(16, 0, (th) => `<path d="${petalPath(CX, CY, 300, 392, 6.4, th)}" fill="${gDeep}" stroke="${gMid}" stroke-width="1.4"/>`)
    + ring(16, 11.25, (th) => `<path d="${petalPath(CX, CY, 312, 372, 4.4, th)}" fill="${gMid}" stroke="${gLight}" stroke-width="1" opacity="0.9"/>`)
    + `</g>`;

  // inner floret inside each big leaf
  inner += `<g fill="none" stroke="${gLight}" stroke-width="1.1" opacity="0.65">`
    + ring(16, 0, (th) => `<path d="${petalPath(CX, CY, 322, 372, 2.6, th)}"/>`) + `</g>`;

  // dotted ring
  inner += circle(296, `fill="none" stroke="${gLight}" stroke-width="1.6" opacity="0.6"`);
  inner += `<g fill="${gold}" opacity="0.9">`
    + ring(48, 0, (th) => { const [x, y] = P(CX, CY, 288, th); return `<circle cx="${f(x)}" cy="${f(y)}" r="2.1"/>`; }) + `</g>`;
  inner += circle(278, `fill="none" stroke="${gLight}" stroke-width="1.6" opacity="0.6"`);

  // Ring C : interlaced geometric star band
  inner += starPolygon(CX, CY, 268, 16, 6, `fill="none" stroke="${gMid}" stroke-width="1.7" opacity="0.85"`);
  inner += starPolygon(CX, CY, 268, 16, 5, `fill="none" stroke="${gLight}" stroke-width="1.1" opacity="0.55"`);

  // Ring D : 16 inward teardrops framing the medallion
  inner += `<g opacity="0.9">`
    + ring(16, 0, (th) => `<path d="${petalPath(CX, CY, 250, 214, 5.2, th)}" fill="${gDeep}" stroke="${gMid}" stroke-width="1.2"/>`)
    + `</g>`;

  // central medallion
  inner += circle(210, `fill="${pal.medallion}" stroke="${gold}" stroke-width="2.4"`);
  inner += circle(203, `fill="none" stroke="${gLight}" stroke-width="1" opacity="0.6"`);
  inner += circle(198, `fill="none" stroke="${gLight}" stroke-width="0.7" opacity="0.4"`);

  return `<svg viewBox="0 0 1000 1000" xmlns="http://www.w3.org/2000/svg" class="mandala" preserveAspectRatio="xMidYMid meet">${inner}</svg>`;
}

// ---------------------------------------------------------------------------
// CHAPTER DIVIDER  (horizontal, central rosette)  viewBox 0 0 640 90
// ---------------------------------------------------------------------------
function chapterDivider(pal) {
  const g = pal.dividerInk, gold = pal.gold;
  const cx = 320, cy = 45;
  let s = `<svg viewBox="0 0 640 90" xmlns="http://www.w3.org/2000/svg" class="divider" preserveAspectRatio="xMidYMid meet">`;
  // tapering side rules with terminal dots
  const line = (x1, x2, dir) =>
    `<line x1="${x1}" y1="${cy}" x2="${x2}" y2="${cy}" stroke="${g}" stroke-width="1.4"/>`
    + `<circle cx="${dir > 0 ? x2 : x1}" cy="${cy}" r="3" fill="${gold}"/>`
    + `<circle cx="${dir > 0 ? x1 : x2}" cy="${cy}" r="2" fill="${g}"/>`;
  s += line(40, 250, 1);
  s += line(390, 600, -1);
  // small leaves flanking the rosette
  s += `<g fill="none" stroke="${g}" stroke-width="1.3">`;
  s += `<path d="${petalPathXY(268, cy, 292, cy, 12)}"/>`;
  s += `<path d="${petalPathXY(372, cy, 348, cy, 12)}"/>`;
  s += `</g>`;
  // central 8-point rosette
  s += rosette(cx, cy, 26, 15, g, gold);
  s += `</svg>`;
  return s;
}

// petal between two points along horizontal axis (helper for divider)
function petalPathXY(x0, y0, x1, y1, w) {
  const mx = (x0 + x1) / 2;
  return `M ${x0} ${y0} C ${mx} ${y0 - w} ${mx} ${y1 - w} ${x1} ${y1} C ${mx} ${y1 + w} ${mx} ${y0 + w} ${x0} ${y0} Z`;
}

function rosette(cx, cy, rOut, rIn, ink, gold) {
  let s = `<g>`;
  s += `<g fill="${ink}" opacity="0.9">`;
  for (let i = 0; i < 8; i++) s += `<path d="${petalPath(cx, cy, rIn * 0.35, rOut, 11, i * 45)}"/>`;
  s += `</g>`;
  s += `<circle cx="${cx}" cy="${cy}" r="${rIn * 0.5}" fill="${gold}"/>`;
  s += `<circle cx="${cx}" cy="${cy}" r="${rIn * 0.25}" fill="${ink}"/>`;
  s += `</g>`;
  // rebind petalPath center (petalPath uses global CX/CY) -> use local variant
  return s;
}

// A small corner flourish for the page frame  viewBox 0 0 120 120 (drawn for top-left)
function frameCorner(pal) {
  const g = pal.frameInk, gold = pal.gold;
  return `<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" class="corner" preserveAspectRatio="xMidYMid meet">`
    + `<path d="M 6 60 C 6 26 26 6 60 6" fill="none" stroke="${g}" stroke-width="1.6"/>`
    + `<path d="M 14 60 C 14 30 30 14 60 14" fill="none" stroke="${g}" stroke-width="0.9" opacity="0.6"/>`
    + `<path d="M 6 60 C 6 40 12 22 40 18 C 22 30 22 46 24 60 Z" fill="${g}" opacity="0.85"/>`
    + `<circle cx="60" cy="6" r="3" fill="${gold}"/>`
    + `<circle cx="6" cy="60" r="3" fill="${gold}"/>`
    + `<circle cx="18" cy="18" r="2.4" fill="${gold}"/>`
    + `</svg>`;
}

// tiny inline rosette (for verse/hadith markers)  viewBox 0 0 40 40
function miniRosette(pal, ink) {
  ink = ink || pal.gold;
  let s = `<svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg" class="mini" preserveAspectRatio="xMidYMid meet">`;
  s += `<g fill="${ink}">`;
  for (let i = 0; i < 8; i++) s += `<path d="${petalPath(20, 20, 3, 17, 12, i * 45)}"/>`;
  s += `</g><circle cx="20" cy="20" r="4.4" fill="${pal.medallion}"/><circle cx="20" cy="20" r="2" fill="${ink}"/>`;
  s += `</svg>`;
  return s;
}

module.exports = { coverMandala, chapterDivider, frameCorner, miniRosette };
