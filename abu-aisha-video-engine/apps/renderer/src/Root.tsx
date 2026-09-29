import React from 'react';
import {Composition} from 'remotion';
import {Classic} from './Classic';
import type {RenderInput} from './types';
import sample from './sample-input.json';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Classic"
    component={Classic as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={300}
    defaultProps={sample as unknown as Record<string, unknown>}
    calculateMetadata={({props}) => {
      const p = props as unknown as RenderInput;
      const intro = p.intro.enabled ? p.intro.duration : 0;
      return {
        durationInFrames: Math.round((intro + p.contentDuration) * p.fps),
        fps: p.fps,
        width: p.width,
        height: p.height,
      };
    }}
  />
);
