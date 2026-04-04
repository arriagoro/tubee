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

export const HighlightReel: React.FC<TemplateProps> = ({
  clips,
  text,
  colors,
  music,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = duration * fps;

  // Fast cuts — shorter clip durations with beat markers
  const beatInterval = Math.floor(fps * 0.5); // beat every 0.5s
  const clipDuration = clips.length > 0
    ? Math.max(Math.floor(totalFrames / clips.length), beatInterval)
    : totalFrames;

  // Flash on beat transitions
  const beatFlash = clips.map((_, i) => {
    const transitionFrame = i * clipDuration;
    return interpolate(
      frame,
      [transitionFrame, transitionFrame + 3, transitionFrame + 6],
      [1, 0, 0],
      { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
    );
  });

  const currentFlash = beatFlash.reduce((a, b) => Math.max(a, b), 0);

  // Zoom pulse effect
  const pulseScale = interpolate(
    frame % beatInterval,
    [0, beatInterval * 0.3, beatInterval],
    [1.05, 1, 1],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Fast-cut clips */}
      {clips.map((clip, i) => (
        <Sequence key={i} from={i * clipDuration} durationInFrames={clipDuration}>
          <AbsoluteFill style={{ transform: `scale(${pulseScale})` }}>
            <Video
              src={clip.src}
              startFrom={clip.startFrom || 0}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Beat flash overlay */}
      <AbsoluteFill
        style={{
          backgroundColor: colors.accent || "#fff",
          opacity: currentFlash * 0.6,
        }}
      />

      {/* Title text — appears in first second */}
      {frame < fps * 1.5 && (
        <AbsoluteFill
          style={{
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <div
            style={{
              color: colors.accent || "#fff",
              fontSize: 72,
              fontWeight: 900,
              textTransform: "uppercase",
              letterSpacing: 6,
              textShadow: "0 0 40px rgba(0,0,0,0.8)",
              opacity: interpolate(frame, [0, fps * 0.3, fps * 1, fps * 1.5], [0, 1, 1, 0], {
                extrapolateRight: "clamp",
              }),
              transform: `scale(${spring({ frame, fps, from: 1.4, to: 1, durationInFrames: fps * 0.5 })})`,
            }}
          >
            {text}
          </div>
        </AbsoluteFill>
      )}

      {/* Music */}
      {music && <Audio src={music} volume={1} />}
    </AbsoluteFill>
  );
};
