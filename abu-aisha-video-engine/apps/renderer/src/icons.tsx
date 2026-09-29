import React from 'react';

// Simple monochrome line glyphs for the brand lockup (white, transparent background).
type P = {size: number; color: string};

const Instagram: React.FC<P> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2}>
    <rect x="3" y="3" width="18" height="18" rx="5" />
    <circle cx="12" cy="12" r="4.2" />
    <circle cx="17.3" cy="6.7" r="1.1" fill={color} stroke="none" />
  </svg>
);

const TikTok: React.FC<P> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <path d="M14.2 2.5h3.1c.2 1.9 1.6 3.5 3.6 3.8v3.1c-1.4 0-2.7-.4-3.8-1.1v6.6a5.9 5.9 0 1 1-5.9-5.9c.3 0 .6 0 .9.1v3.2a2.8 2.8 0 1 0 2.1 2.7V2.5z" />
  </svg>
);

const YouTube: React.FC<P> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="1.8" y="5" width="20.4" height="14" rx="4" stroke={color} strokeWidth={2} />
    <path d="M10 9.2v5.6l4.8-2.8z" fill={color} />
  </svg>
);

const Facebook: React.FC<P> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <path d="M13.5 21v-7.6h2.6l.4-3h-3V8.5c0-.9.3-1.5 1.5-1.5h1.6V4.3c-.3 0-1.2-.1-2.3-.1-2.3 0-3.9 1.4-3.9 4v2.2H7.8v3h2.6V21h3.1z" />
  </svg>
);

const Telegram: React.FC<P> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <path d="M20.7 4.1 2.9 11c-1.2.5-1.2 1.2-.2 1.5l4.6 1.4 1.7 5.4c.2.6.4.8.9.8.4 0 .6-.2.9-.5l2.2-2.1 4.6 3.4c.8.5 1.4.2 1.6-.8l3-14c.3-1.2-.5-1.8-1.5-1.3zM8.2 13.6l9.4-5.9c.5-.3.9-.1.5.2l-8 7.2-.3 3.4-1.6-4.9z" />
  </svg>
);

const X: React.FC<P> = ({size, color}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
    <path d="M17.8 3h3.1l-6.8 7.8 8 10.2h-6.3l-4.9-6.4L5.3 21H2.2l7.3-8.3L1.9 3h6.4l4.4 5.8L17.8 3zm-1.1 16.2h1.7L7.4 4.7H5.6l11.1 14.5z" />
  </svg>
);

export const SOCIAL_ICONS = {instagram: Instagram, tiktok: TikTok, youtube: YouTube, facebook: Facebook, telegram: Telegram, x: X};
