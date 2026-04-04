export interface ClipData {
  src: string;
  startFrom?: number;
  durationInFrames?: number;
}

export interface TemplateProps {
  clips: ClipData[];
  text: string;
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
  };
  music: string | null;
  duration: number; // in seconds
}
