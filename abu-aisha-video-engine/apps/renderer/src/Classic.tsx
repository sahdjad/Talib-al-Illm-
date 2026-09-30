import React, {useMemo} from 'react';
import {
  AbsoluteFill,
  Easing,
  Html5Audio,
  Img,
  interpolate,
  OffthreadVideo,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {ARABIC_STACK, ensureFonts, SUBTITLE_STACK} from './fonts';
import type {EditorialItem, RenderInput, Segment} from './types';

const src = (p: string) => (/^https?:/.test(p) ? p : staticFile(p));

/* ------------------------------------------------------------------ mask */

/** Soft feathered transition from picture into black (smoothstep, no hard edge). */
const BlackMask: React.FC<{input: RenderInput}> = ({input}) => {
  const {height} = input;
  const a = input.mask.fadeStart * height;
  const b = input.mask.fadeEnd * height;
  const stops: string[] = [];
  const N = 12;
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    const s = t * t * (3 - 2 * t);
    stops.push(`rgba(0,0,0,${s.toFixed(3)}) ${(t * 100).toFixed(1)}%`);
  }
  return (
    <>
      {input.mask.topFade > 0 ? (
        <div
          style={{
            position: 'absolute', left: 0, right: 0, top: input.stage.y - 1, height: input.mask.topFade * height,
            background: `linear-gradient(to top, ${stops.join(',')})`,
          }}
        />
      ) : null}
      <div style={{position: 'absolute', left: 0, right: 0, top: a, height: b - a, background: `linear-gradient(to bottom, ${stops.join(',')})`}} />
      <div style={{position: 'absolute', left: 0, right: 0, top: b - 1, bottom: 0, background: '#000'}} />
    </>
  );
};

/* ----------------------------------------------------------------- stage */

const StageLayer: React.FC<{input: RenderInput; frozen?: boolean; introFrames: number}> = ({input, frozen, introFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {stage} = input;
  if (input.mode === 'audio_visual' && stage.still) {
    const total = (input.contentDuration + input.intro.duration) * fps;
    const f = stage.flow ?? {zoomFrom: 1.0, zoomTo: 1.05, panX: 0, panY: 0};
    const t = Math.min(1, frame / Math.max(1, total));
    const e = Easing.inOut(Easing.sin)(t);
    const scale = f.zoomFrom + (f.zoomTo - f.zoomFrom) * e;
    return (
      <div style={{position: 'absolute', left: 0, top: stage.y, width: input.width, height: stage.height, overflow: 'hidden'}}>
        <Img
          src={src(stage.still)}
          style={{
            width: '100%', height: '100%', objectFit: 'cover',
            transform: `translate(${f.panX * e}px, ${f.panY * e}px) scale(${scale})`, transformOrigin: '50% 40%',
          }}
        />
      </div>
    );
  }
  if (frozen || !stage.video) {
    return input.intro.freezeFrame ? (
      <Img src={src(input.intro.freezeFrame)} style={{position: 'absolute', left: 0, top: stage.y, width: input.width, height: stage.height}} />
    ) : null;
  }
  return (
    <Sequence from={introFrames} layout="none">
      <OffthreadVideo muted src={src(stage.video)} style={{position: 'absolute', left: 0, top: stage.y, width: input.width, height: stage.height}} />
    </Sequence>
  );
};

/* ----------------------------------------------------------- brand lockup */

const BrandLockup: React.FC<{input: RenderInput}> = ({input}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {brand, width} = input;
  // Characteristic top-to-down entrance during the intro (spring with small overshoot).
  const enterAt = input.intro.enabled ? Math.round(0.95 * fps) : 0;
  const sp = input.intro.enabled ? spring({frame: frame - enterAt, fps, config: {damping: 11, stiffness: 120, mass: 0.8}}) : 1;
  const dy = interpolate(sp, [0, 1], [-(brand.top + brand.height), 0]);
  const opacity = input.intro.enabled
    ? interpolate(frame, [enterAt, enterAt + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
    : 1;
  return (
    <div
      style={{
        position: 'absolute', left: 0, width, top: brand.top, height: brand.height, display: 'flex',
        justifyContent: 'center', alignItems: 'center', transform: `translateY(${dy}px)`, opacity,
      }}
    >
      <Img src={src(brand.lockup)} style={{height: brand.height, width: 'auto', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.8))'}} />
    </div>
  );
};

/* ------------------------------------------------------------- subtitles */

const textStyle = (input: RenderInput, fontSize: number, color: string): React.CSSProperties => ({
  fontFamily: SUBTITLE_STACK,
  fontWeight: 800,
  fontSize,
  color,
  WebkitTextStroke: `${Math.max(4, Math.round(fontSize * input.style.strokeWidth))}px ${input.style.stroke}`,
  paintOrder: 'stroke fill',
  textShadow: `0 ${Math.round(fontSize * 0.05)}px ${Math.round(fontSize * 0.12)}px rgba(0,0,0,0.85)`,
  textAlign: 'center',
  whiteSpace: 'pre',
});

const SubtitleBlock: React.FC<{input: RenderInput; seg: Segment; durationFrames: number}> = ({input, seg, durationFrames}) => {
  const frame = useCurrentFrame();
  const box = input.subtitleBox;
  const fadeIn = interpolate(frame, [0, 3], [0, 1], {extrapolateRight: 'clamp'});
  const fadeOut = interpolate(frame, [durationFrames - 2, durationFrames], [1, 0], {extrapolateLeft: 'clamp'});
  const pop = interpolate(frame, [0, 4], [0.965, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const color = seg.accent === 'red' || seg.type === 'heading' ? input.style.accent : input.style.fill;
  return (
    <div
      style={{
        position: 'absolute', left: box.left, right: input.width - box.right, top: box.top, height: box.bottom - box.top,
        display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
        opacity: Math.min(fadeIn, fadeOut), transform: `scale(${pop})`,
      }}
    >
      {seg.layout.lines.map((line, i) => (
        <div key={i} style={{...textStyle(input, seg.layout.fontSize, color), lineHeight: `${seg.layout.lineHeight}px`}}>
          {line}
        </div>
      ))}
    </div>
  );
};

const EditorialLine: React.FC<{input: RenderInput; item: EditorialItem; durationFrames: number}> = ({input, item, durationFrames}) => {
  const frame = useCurrentFrame();
  const lane = input.editorialLane;
  const o = Math.min(
    interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'}),
    interpolate(frame, [durationFrames - 8, durationFrames], [1, 0], {extrapolateLeft: 'clamp'}),
  );
  const arabic = item.dir === 'rtl';
  return (
    <div
      style={{
        position: 'absolute', left: lane.left, right: input.width - lane.right, top: lane.top, height: lane.bottom - lane.top,
        display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: o,
      }}
    >
      <div
        dir={item.dir}
        style={{
          fontFamily: arabic ? ARABIC_STACK : SUBTITLE_STACK, fontWeight: arabic ? 700 : 700, fontSize: item.fontSize,
          color: input.style.editorialColor, textAlign: 'center', lineHeight: 1.25, fontStyle: arabic ? 'normal' : 'italic',
          padding: `${Math.round(item.fontSize * 0.18)}px ${Math.round(item.fontSize * 0.6)}px`,
          borderTop: '1px solid rgba(232,226,208,0.35)', borderBottom: '1px solid rgba(232,226,208,0.35)',
          textShadow: '0 2px 6px rgba(0,0,0,0.9)',
        }}
      >
        {item.text}
      </div>
    </div>
  );
};

/* ----------------------------------------------------------------- intro */

const Intro: React.FC<{input: RenderInput}> = ({input}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {intro, width} = input;
  const k = intro.intensity; // 1.0 soft/general … 2.0 rebuttal
  const total = Math.round(intro.duration * fps);
  const outStart = total - Math.round(0.35 * fps);

  // Speaker line: quick slide in from the right (RTL reading direction), then stable.
  const spIn = spring({frame: frame - Math.round(0.2 * fps), fps, config: {damping: 16, stiffness: 170}});
  const spX = interpolate(spIn, [0, 1], [width * 0.6, 0]);
  const spBlur = interpolate(spIn, [0, 0.8, 1], [10, 2, 0], {extrapolateRight: 'clamp'});

  // Title: blade slide — a light blade sweeps across and reveals the title behind it.
  const tStart = Math.round(0.45 * fps);
  const blade = interpolate(frame, [tStart, tStart + Math.round(0.38 * fps)], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.2, 0.8, 0.2, 1),
  });
  const titleX = interpolate(blade, [0, 1], [-width * 0.18, 0]);
  const landed = frame - (tStart + Math.round(0.38 * fps));
  // Bass impact: one short scale punch on landing, amplitude scales with content-profile intensity.
  const punch = landed >= 0 ? 1 + 0.045 * k * Math.exp(-landed / 3.2) * Math.cos(landed / 1.6) : 1;

  const out = interpolate(frame, [outStart, total], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const outY = interpolate(frame, [outStart, total], [0, 40], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.cubic)});
  const box = input.subtitleBox;
  const titleBlockH = intro.titleLines.length * intro.titleFontSize * 1.08;
  const titleTop = box.top + (box.bottom - box.top - titleBlockH) / 2 + intro.titleFontSize * 0.35;

  return (
    <AbsoluteFill style={{opacity: out, transform: `translateY(${outY}px)`}}>
      <div
        dir="rtl"
        style={{
          position: 'absolute', left: 60, right: 60, top: titleTop - intro.titleFontSize * 1.25, textAlign: 'center',
          fontFamily: ARABIC_STACK, fontWeight: 700, fontSize: 54, color: '#fff',
          transform: `translateX(${spX}px)`, filter: `blur(${spBlur}px)`, opacity: interpolate(spIn, [0, 0.3], [0, 1], {extrapolateRight: 'clamp'}),
          textShadow: '0 3px 10px rgba(0,0,0,0.95)', WebkitTextStroke: '6px #000', paintOrder: 'stroke fill',
        }}
      >
        {intro.speakerLine}
      </div>
      <div
        style={{
          position: 'absolute', left: input.subtitleBox.left, right: width - input.subtitleBox.right, top: titleTop,
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          clipPath: `inset(-20% ${(1 - blade) * 100}% -20% -5%)`, transform: `translateX(${titleX}px) scale(${punch})`,
        }}
      >
        {intro.titleLines.map((l, i) => (
          <div key={i} style={{...textStyle(input, intro.titleFontSize, '#fff'), fontWeight: 900, lineHeight: `${Math.round(intro.titleFontSize * 1.08)}px`, textTransform: 'uppercase'}}>
            {l}
          </div>
        ))}
      </div>
      {blade > 0 && blade < 1 ? (
        <div
          style={{
            position: 'absolute', top: titleTop - 30, height: titleBlockH + 60, width: 26,
            left: input.subtitleBox.left + (input.subtitleBox.right - input.subtitleBox.left) * blade - 13 + titleX,
            background: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.95), rgba(255,255,255,0))',
            transform: 'skewX(-14deg)', filter: 'blur(2px)',
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};

/** Flow-style settle of the frozen intro background + subtle bass shake. */
const IntroBackground: React.FC<{input: RenderInput; introFrames: number}> = ({input, introFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const k = input.intro.intensity;
  const settle = interpolate(frame, [0, Math.round(0.7 * fps)], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  const drift = interpolate(frame, [0, introFrames * 0.6, introFrames], [0, 0.02, 0], {extrapolateRight: 'clamp'});
  const scale = interpolate(settle, [0, 1], [1.14, 1.0]) + drift;
  const blur = interpolate(settle, [0, 1], [14, 0]);
  const landed = frame - Math.round(0.83 * fps);
  const shake = landed >= 0 && landed < 10 ? Math.sin(landed * 2.2) * 7 * k * Math.exp(-landed / 3) : 0;
  const dim = interpolate(frame, [introFrames - Math.round(0.35 * fps), introFrames], [0.38, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const {stage, height} = input;
  return (
    <AbsoluteFill style={{clipPath: `inset(${stage.y}px 0 ${height - stage.y - stage.height}px 0)`, background: '#000'}}>
      <AbsoluteFill style={{transform: `translate(${shake}px, ${shake * 0.4}px) scale(${scale})`, transformOrigin: '50% 30%', filter: `blur(${blur}px)`}}>
        <StageLayer input={input} frozen introFrames={introFrames} />
        <AbsoluteFill style={{background: `rgba(0,0,0,${dim})`}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/* ------------------------------------------------------------------ main */

export const Classic: React.FC<RenderInput> = (input) => {
  ensureFonts();
  const {fps} = useVideoConfig();
  const introFrames = input.intro.enabled ? Math.round(input.intro.duration * fps) : 0;
  const toFrame = (t: number) => introFrames + Math.round(t * fps);
  const segs = useMemo(() => input.segments.filter((s) => s.end > s.start), [input.segments]);

  return (
    <AbsoluteFill style={{background: '#000'}}>
      {/* live stage (video starts after intro) */}
      <StageLayer input={input} introFrames={introFrames} />
      {input.intro.enabled && input.mode === 'video' ? (
        <Sequence durationInFrames={introFrames} layout="none">
          <IntroBackground input={input} introFrames={introFrames} />
        </Sequence>
      ) : null}
      <BlackMask input={input} />

      {input.intro.enabled ? (
        <Sequence durationInFrames={introFrames} layout="none">
          <Intro input={input} />
        </Sequence>
      ) : null}

      {segs.map((s) => {
        const from = toFrame(s.start);
        const dur = Math.max(1, toFrame(s.end) - from);
        return (
          <Sequence key={s.id} from={from} durationInFrames={dur} layout="none">
            <SubtitleBlock input={input} seg={s} durationFrames={dur} />
          </Sequence>
        );
      })}

      {input.editorial.map((e) => {
        const from = toFrame(e.start);
        const dur = Math.max(1, toFrame(e.end) - from);
        return (
          <Sequence key={e.id} from={from} durationInFrames={dur} layout="none">
            <EditorialLine input={input} item={e} durationFrames={dur} />
          </Sequence>
        );
      })}

      <BrandLockup input={input} />

      <Sequence from={introFrames} layout="none">
        <Html5Audio src={src(input.audio)} />
      </Sequence>

      {input.debug?.safeZones ? <SafeZones input={input} /> : null}
    </AbsoluteFill>
  );
};

const SafeZones: React.FC<{input: RenderInput}> = ({input}) => {
  const b = input.subtitleBox;
  const e = input.editorialLane;
  const outline = (c: string): React.CSSProperties => ({position: 'absolute', border: `3px dashed ${c}`});
  return (
    <>
      <div style={{...outline('#0f0'), left: b.left, top: b.top, width: b.right - b.left, height: b.bottom - b.top}} />
      <div style={{...outline('#0af'), left: e.left, top: e.top, width: e.right - e.left, height: e.bottom - e.top}} />
      <div style={{...outline('#f0f'), left: 0, top: input.brand.top, width: input.width, height: input.brand.height}} />
      <div style={{...outline('#ff0'), left: 0, top: input.height - 210, width: input.width, height: 210}} />
    </>
  );
};
