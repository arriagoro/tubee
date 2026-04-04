import React from "react";
import { Composition } from "remotion";
import { SocialReel } from "./compositions/SocialReel";
import { HighlightReel } from "./compositions/HighlightReel";
import { BrandPromo } from "./compositions/BrandPromo";
import { Testimonial } from "./compositions/Testimonial";
import { BeforeAfter } from "./compositions/BeforeAfter";
import type { TemplateProps } from "./types";

const FPS = 30;

const defaultProps: TemplateProps = {
  clips: [],
  text: "Your Text Here",
  colors: {
    primary: "#FFFFFF",
    secondary: "#AAAAAA",
    accent: "#00AAFF",
    background: "#000000",
  },
  music: null,
  duration: 15,
};

// Remotion v5 uses Zod schema typing; we cast to satisfy the generic
// while keeping full type safety in the individual compositions.
const comp = (c: React.FC<any>) => c as React.FC<Record<string, unknown>>;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SocialReel"
        component={comp(SocialReel)}
        durationInFrames={defaultProps.duration * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps as unknown as Record<string, unknown>}
      />
      <Composition
        id="HighlightReel"
        component={comp(HighlightReel)}
        durationInFrames={defaultProps.duration * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps as unknown as Record<string, unknown>}
      />
      <Composition
        id="BrandPromo"
        component={comp(BrandPromo)}
        durationInFrames={defaultProps.duration * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps as unknown as Record<string, unknown>}
      />
      <Composition
        id="Testimonial"
        component={comp(Testimonial)}
        durationInFrames={defaultProps.duration * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps as unknown as Record<string, unknown>}
      />
      <Composition
        id="BeforeAfter"
        component={comp(BeforeAfter)}
        durationInFrames={defaultProps.duration * FPS}
        fps={FPS}
        width={1080}
        height={1920}
        defaultProps={defaultProps as unknown as Record<string, unknown>}
      />
    </>
  );
};
