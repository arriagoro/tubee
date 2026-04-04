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

export const SocialReel: React.FC<TemplateProps> = ({
  clips,
  text,
  colors,
  music,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = duration * fps;
  const clipDuration = clips.length > 0 ? Math.floor(totalFrames / clips.length) : totalFrames;

  // Animated text overlay
  const textOpacity = interpolate(frame, [0, fps * 0.5, totalFrames - fps, totalFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const textY = spring({ frame, fps, from: 50, to: 0, durationInFrames: fps });

  // Color grade overlay
  const gradeOpacity = 0.15;

  return (
    <AbsoluteFill style={{ backgroundColor: colors.background || "#000" }}>
      {/* Video clips */}
      {clips.map((clip, i) => (
        <Sequence key={i} from={i * clipDuration} durationInFrames={clipDuration}>
          <AbsoluteFill>
            <Video
              src={clip.src}
              startFrom={clip.startFrom || 0}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Color grade overlay */}
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, ${colors.primary}00 0%, ${colors.primary}${Math.round(gradeOpacity * 255).toString(16).padStart(2, "0")} 100%)`,
          mixBlendMode: "overlay",
        }}
      />

      {/* Animated text */}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          padding: "0 40px 120px",
        }}
      >
        <div
          style={{
            opacity: textOpacity,
            transform: `translateY(${textY}px)`,
            color: colors.accent || "#fff",
            fontSize: 56,
            fontWeight: 900,
            textAlign: "center",
            textShadow: "0 4px 20px rgba(0,0,0,0.7)",
            lineHeight: 1.2,
            letterSpacing: -1,
          }}
        >
          {text}
        </div>
      </AbsoluteFill>

      {/* Music */}
      {music && <Audio src={music} volume={0.8} />}
    </AbsoluteFill>
  );
};
