import {continueRender, delayRender, staticFile} from 'remotion';

// Fonts are copied into the render public dir by the pipeline (packages/brand/fonts).
const FACES: Array<{family: string; file: string; weight: number}> = [
  {family: 'AA Slab', file: 'RobotoSlab-ExtraBold.ttf', weight: 800},
  {family: 'AA Slab', file: 'RobotoSlab-Black.ttf', weight: 900},
  {family: 'AA Slab', file: 'RobotoSlab-Bold.ttf', weight: 700},
  {family: 'AA Naskh', file: 'NotoNaskhArabic-Bold.ttf', weight: 700},
  {family: 'AA Amiri', file: 'Amiri-Bold.ttf', weight: 700},
  {family: 'AA Amiri', file: 'Amiri-Regular.ttf', weight: 400},
  {family: 'AA Brand', file: 'Montserrat-SemiBold.ttf', weight: 600},
  {family: 'AA Brand', file: 'Montserrat-Bold.ttf', weight: 700},
];

let loaded = false;

export const ensureFonts = () => {
  if (loaded || typeof document === 'undefined') return;
  loaded = true;
  const handle = delayRender('Loading brand fonts');
  const promises = FACES.map((f) => {
    const face = new FontFace(f.family, `url(${staticFile('fonts/' + f.file)}) format('truetype')`, {
      weight: String(f.weight),
    });
    return face.load().then((ff) => {
      document.fonts.add(ff);
    });
  });
  Promise.all(promises)
    .then(() => continueRender(handle))
    .catch((err) => {
      console.error('Font load failed', err);
      continueRender(handle);
    });
};

/** Latin subtitle stack: slab first, Amiri as glyph fallback for ḥ ʿ ﷺ ﷻ etc. */
export const SUBTITLE_STACK = "'AA Slab', 'AA Amiri', 'Noto Color Emoji', serif";
export const ARABIC_STACK = "'AA Naskh', 'AA Amiri', 'Noto Color Emoji', serif";
export const BRAND_STACK = "'AA Brand', 'AA Amiri', sans-serif";
