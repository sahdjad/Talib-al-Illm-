// Usage: node render.mjs <render_input.json> <publicDir> <out.mp4> [--preview] [--frames=a-b] [--still=frame:out.png]
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const [inputPath, publicDir, out, ...flags] = process.argv.slice(2);
if (!inputPath || !publicDir || !out) {
  console.error('usage: node render.mjs <render_input.json> <publicDir> <out.mp4> [--preview] [--frames=a-b] [--still=frame]');
  process.exit(2);
}
const inputProps = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const preview = flags.includes('--preview');
const frames = flags.find((f) => f.startsWith('--frames='));
const still = flags.find((f) => f.startsWith('--still='));
const browserExecutable = process.env.REMOTION_BROWSER || findHeadlessShell();

function findHeadlessShell() {
  const base = '/opt/pw-browsers';
  if (!fs.existsSync(base)) return null;
  for (const d of fs.readdirSync(base)) {
    if (d.startsWith('chromium_headless_shell')) {
      const p = path.join(base, d, 'chrome-linux', 'headless_shell');
      if (fs.existsSync(p)) return p;
    }
  }
  return null;
}

const serveUrl = await bundle({
  entryPoint: path.join(here, 'src/index.ts'),
  publicDir: path.resolve(publicDir),
  onProgress: () => {},
});
const composition = await selectComposition({serveUrl, id: 'Classic', inputProps, browserExecutable});

if (still) {
  const list = still.slice('--still='.length).split(',').map(Number);
  for (const f of list) {
    const o = out.replace(/(\.png)?$/, `_${String(f).padStart(5, '0')}.png`);
    await renderStill({serveUrl, composition, inputProps, frame: f, output: o, browserExecutable, scale: preview ? 0.5 : 1});
    console.log('still', o);
  }
  process.exit(0);
}

let last = -1;
await renderMedia({
  serveUrl,
  composition,
  inputProps,
  codec: 'h264',
  crf: preview ? 28 : 16,
  x264Preset: preview ? 'veryfast' : 'slow',
  pixelFormat: 'yuv420p',
  audioCodec: 'aac',
  audioBitrate: '320k',
  scale: preview ? 0.5 : 1,
  outputLocation: out,
  browserExecutable,
  concurrency: Math.max(1, os.cpus().length),
  frameRange: frames ? frames.slice(9).split('-').map(Number) : undefined,
  imageFormat: 'jpeg',
  jpegQuality: 95,
  onProgress: ({progress}) => {
    const p = Math.floor(progress * 20);
    if (p !== last) {
      last = p;
      process.stdout.write(`render ${Math.round(progress * 100)}%\n`);
    }
  },
});
console.log('done', out);
