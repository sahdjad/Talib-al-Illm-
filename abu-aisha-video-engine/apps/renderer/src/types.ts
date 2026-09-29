// Render input contract. Produced by the pipeline (services/pipeline/abu_aisha/render_input.py)
// from project.json. The renderer never invents editorial content: every text it draws is in here.

export type Lang = 'de' | 'en';

export type Box = {top: number; bottom: number; left: number; right: number};

export type SubtitleLayout = {
  /** Font size in px chosen by the fitter (dynamic, per block). */
  fontSize: number;
  /** Final visual lines (semantic line breaks preserved, then wrapped). */
  lines: string[];
  lineHeight: number;
};

export type Segment = {
  id: string;
  /** Seconds on the SOURCE timeline (after trim_in), i.e. 0 = first frame of the used clip. */
  start: number;
  end: number;
  type: 'spoken' | 'heading';
  text: string;
  accent?: 'red' | null;
  layout: SubtitleLayout;
};

export type EditorialItem = {
  id: string;
  start: number;
  end: number;
  kind: 'source' | 'context' | 'quran_ref' | 'hadith_ref';
  text: string;
  dir: 'rtl' | 'ltr';
  fontSize: number;
};

export type Stage = {
  /** Pre-scaled stage video (1080 wide) produced by FFmpeg; placed at y. */
  video: string | null;
  still: string | null;
  y: number;
  height: number;
  /** Audio+Visual mode: slow Flow / Ken-Burns amount (fractional zoom over the whole clip). */
  flow: {zoomFrom: number; zoomTo: number; panX: number; panY: number} | null;
};

export type RenderInput = {
  projectId: string;
  lang: Lang;
  theme: 'classic';
  width: number;
  height: number;
  fps: number;
  mode: 'video' | 'audio_visual';
  /** Used clip length in seconds (trim_out - trim_in). */
  contentDuration: number;
  audio: string;
  stage: Stage;
  mask: {fadeStart: number; fadeEnd: number; topFade: number};
  intro: {
    enabled: boolean;
    duration: number;
    freezeFrame: string | null;
    speakerLine: string;
    title: string;
    titleFontSize: number;
    titleLines: string[];
    intensity: number;
  };
  subtitleBox: Box;
  editorialLane: Box;
  segments: Segment[];
  editorial: EditorialItem[];
  brand: {
    calligraphy: string;
    wordmark: string;
    top: number;
    height: number;
    socials: Array<'instagram' | 'tiktok' | 'youtube' | 'facebook' | 'telegram' | 'x'>;
  };
  style: {
    subtitleFont: string;
    arabicFont: string;
    brandFont: string;
    fill: string;
    stroke: string;
    strokeWidth: number;
    accent: string;
    editorialColor: string;
  };
  debug?: {safeZones?: boolean};
};
