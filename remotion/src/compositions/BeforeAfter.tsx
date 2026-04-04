import React from "react";
import {
  AbsoluteFill,
  
  useCurrentFrame,
  useVideoConfig,
  Video,
  Audio,
  interpolate,
} from "remotion";
import type { TemplateProps } from "../types";

export const BeforeAfter: React.FC<TemplateProps> = ({
  clips,
  text,
  colors,
  music,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const totalFrames = duration * fps;

  const beforeClip = clips[0] || null;
  const afterClip = clips[1] || clips[0] || null;

  // Split screen divider animation
  const splitPhase1End = Math.floor(totalFrames * 0.4); // show before
  const splitPhase2End = Math.floor(totalFrames * 0.6); // transition
  const splitPhase3End = totalFrames; // show after

  // Divider position: 100% (full before) → 50% (split) → 0% (full after)
  const dividerX = interpolate(
    frame,
    [0, splitPhase1End, splitPhase2End, splitPhase3End],
    [width, width / 2, width / 2, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  // Labels
  const beforeOpacity = interpolate(
    frame,
    [fps * 0.3, fps * 0.8, splitPhase2End - fps, splitPhase2End],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const afterOpacity = interpolate(
    frame,
    [splitPhase1End, splitPhase1End + fps * 0.5, splitPhase3End - fps, splitPhase3End],
    [0, 1, 1, 0.8],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* After clip — full background */}
      {afterClip && (
        <AbsoluteFill>
          <Video
            src={afterClip.src}
            startFrom={afterClip.startFrom || 0}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      )}

      {/* Before clip — clipped to left side */}
      {beforeClip && (
        <AbsoluteFill
          style={{
            clipPath: `inset(0 ${width - dividerX}px 0 0)`,
          }}
        >
          <Video
            src={beforeClip.src}
            startFrom={beforeClip.startFrom || 0}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      )}

      {/* Divider line */}
      <div
        style={{
          position: "absolute",
          left: dividerX - 2,
          top: 0,
          width: 4,
          height: "100%",
          backgroundColor: colors.accent || "#fff",
          boxShadow: `0 0 20px ${colors.accent || "#fff"}`,
        }}
      />

      {/* BEFORE label */}
      <div
        style={{
          position: "absolute",
          left: 40,
          top: 60,
          opacity: beforeOpacity,
          color: "#fff",
          fontSize: 28,
          fontWeight: 800,
          textTransform: "uppercase",
          letterSpacing: 4,
          textShadow: "0 2px 10px rgba(0,0,0,0.8)",
          padding: "8px 20px",
          backgroundColor: "rgba(0,0,0,0.4)",
          borderRadius: 8,
        }}
      >
        Before
      </div>

      {/* AFTER label */}
      <div
        style={{
          position: "absolute",
          right: 40,
          top: 60,
          opacity: afterOpacity,
          color: colors.accent || "#00AAFF",
          fontSize: 28,
          fontWeight: 800,
          textTransform: "uppercase",
          letterSpacing: 4,
          textShadow: "0 2px 10px rgba(0,0,0,0.8)",
          padding: "8px 20px",
          backgroundColor: "rgba(0,0,0,0.4)",
          borderRadius: 8,
        }}
      >
        After
      </div>

      {/* Bottom text */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", padding: "0 40px 100px" }}>
        <div
          style={{
            color: "#fff",
            fontSize: 40,
            fontWeight: 800,
            textAlign: "center",
            textShadow: "0 2px 16px rgba(0,0,0,0.7)",
            opacity: interpolate(frame, [fps, fps * 2], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          }}
        >
          {text}
        </div>
      </AbsoluteFill>

      {/* Music */}
      {music && <Audio src={music} volume={0.6} />}
    </AbsoluteFill>
  );
};
