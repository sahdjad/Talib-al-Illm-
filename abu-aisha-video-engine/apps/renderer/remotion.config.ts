import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95);
Config.setBrowserExecutable(process.env.REMOTION_BROWSER ?? null);
