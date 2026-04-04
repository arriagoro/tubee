import React from "react";
import {
  AbsoluteFill,
  
  useCurrentFrame,
  useVideoConfig,
  Video,
  Audio,
  interpolate,
  spring,
} from "remotion";
import type { TemplateProps } from "../types";

export const Testimonial: React.FC<TemplateProps> = ({
  clips,
  text,
  colors,
  music,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const totalFrames = duration * fps;

  // Split text into caption segments (simulating word-by-word captions)
  const words = text.split(" ");
  const wordsPerSegment = 4;
  const segments: string[] = [];
  for (let i = 0; i < words.length; i += wordsPerSegment) {
    segments.push(words.slice(i, i + wordsPerSegment).join(" "));
  }

  const segmentDuration = segments.length > 0
    ? Math.floor((totalFrames * 0.8) / segments.length)
    : totalFrames;

  // Caption bar animation
  const captionBarHeight = 200;
  const barY = spring({
    frame: Math.max(0, frame - fps * 0.3),
    fps,
    from: captionBarHeight,
    to: 0,
    durationInFrames: fps * 0.4,
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Talking head video — full background */}
      {clips.length > 0 && (
        <AbsoluteFill>
          <Video
            src={clips[0].src}
            startFrom={clips[0].startFrom || 0}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </AbsoluteFill>
      )}

      {/* Slight vignette */}
      <AbsoluteFill
        style={{
          background: "radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)",
        }}
      />

      {/* Animated caption bar at bottom */}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: "100%",
            padding: "20px 40px 80px",
            transform: `translateY(${barY}px)`,
            background: "linear-gradient(transparent, rgba(0,0,0,0.85))",
          }}
        >
          {segments.map((seg, i) => {
            const segStart = fps * 0.5 + i * segmentDuration;
            const segEnd = segStart + segmentDuration;
            const isVisible = frame >= segStart && frame < segEnd;

            if (!isVisible) return null;

            const localFrame = frame - segStart;
            const wordOpacity = interpolate(localFrame, [0, 6], [0, 1], {
              extrapolateRight: "clamp",
            });
            const wordY = spring({
              frame: localFrame,
              fps,
              from: 20,
              to: 0,
              durationInFrames: 10,
            });

            return (
              <div
                key={i}
                style={{
                  opacity: wordOpacity,
                  transform: `translateY(${wordY}px)`,
                  color: "#fff",
                  fontSize: 42,
                  fontWeight: 800,
                  textAlign: "center",
                  textShadow: "0 2px 12px rgba(0,0,0,0.6)",
                  lineHeight: 1.3,
                }}
              >
                {seg.split(" ").map((word, wi) => (
                  <span key={wi}>
                    <span
                      style={{
                        color: wi === 0 ? (colors.accent || "#00AAFF") : "#fff",
                      }}
                    >
                      {word}
                    </span>{" "}
                  </span>
                ))}
              </div>
            );
          })}
        </div>
      </AbsoluteFill>

      {/* Music */}
      {music && <Audio src={music} volume={0.3} />}
    </AbsoluteFill>
  );
};
