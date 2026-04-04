import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  useVideoConfig,
  Video,
  Audio,
  interpolate,
  spring,
} from "remotion";
import type { TemplateProps } from "../types";

const TitleCard: React.FC<{ text: string; colors: any; fps: number }> = ({
  text,
  colors,
  fps,
}) => {
  const frame = useCurrentFrame();
  const scale = spring({ frame, fps, from: 0.8, to: 1, durationInFrames: fps * 0.6 });
  const opacity = interpolate(frame, [0, fps * 0.3], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: colors.background || "#000",
      }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          textAlign: "center",
        }}
      >
        <div
          style={{
            color: colors.accent || "#00AAFF",
            fontSize: 18,
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: 8,
            marginBottom: 16,
          }}
        >
          Introducing
        </div>
        <div
          style={{
            color: colors.primary || "#fff",
            fontSize: 64,
            fontWeight: 900,
            lineHeight: 1.1,
            maxWidth: 800,
          }}
        >
          {text}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const EndCard: React.FC<{ text: string; colors: any; fps: number }> = ({
  text,
  colors,
  fps,
}) => {
  const frame = useCurrentFrame();
  const slideUp = spring({ frame, fps, from: 60, to: 0, durationInFrames: fps * 0.5 });
  const opacity = interpolate(frame, [0, fps * 0.3], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: colors.background || "#000",
      }}
    >
      <div style={{ opacity, transform: `translateY(${slideUp}px)`, textAlign: "center" }}>
        <div
          style={{
            color: colors.primary || "#fff",
            fontSize: 48,
            fontWeight: 800,
            marginBottom: 24,
          }}
        >
          {text}
        </div>
        <div
          style={{
            display: "inline-block",
            padding: "16px 48px",
            borderRadius: 12,
            backgroundColor: colors.accent || "#00AAFF",
            color: "#fff",
            fontSize: 24,
            fontWeight: 700,
          }}
        >
          Get Started →
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const BrandPromo: React.FC<TemplateProps> = ({
  clips,
  text,
  colors,
  music,
  duration,
}) => {
  const { fps } = useVideoConfig();
  const totalFrames = duration * fps;

  const titleDuration = Math.floor(fps * 2.5);
  const endCardDuration = Math.floor(fps * 3);
  const clipSectionDuration = totalFrames - titleDuration - endCardDuration;
  const perClip = clips.length > 0 ? Math.floor(clipSectionDuration / clips.length) : clipSectionDuration;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background || "#000" }}>
      {/* Title Card */}
      <Sequence from={0} durationInFrames={titleDuration}>
        <TitleCard text={text} colors={colors} fps={fps} />
      </Sequence>

      {/* Product clips */}
      {clips.map((clip, i) => (
        <Sequence
          key={i}
          from={titleDuration + i * perClip}
          durationInFrames={perClip}
        >
          <AbsoluteFill>
            <Video
              src={clip.src}
              startFrom={clip.startFrom || 0}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* End Card CTA */}
      <Sequence from={totalFrames - endCardDuration} durationInFrames={endCardDuration}>
        <EndCard text={text} colors={colors} fps={fps} />
      </Sequence>

      {/* Music */}
      {music && <Audio src={music} volume={0.7} />}
    </AbsoluteFill>
  );
};
