# Temitayo Agoro — Cinematic Color Grade (FFmpeg)

## Style Profile
- **Look:** Warm cinematic — teal-orange split, lifted blacks, rich skin tones
- **Source:** Analysis of @arriagoro Instagram Reels
- **Use case:** Miami outdoor/event footage, fitness content, product promos

## The Grade Filter Chain

```
eq=brightness=0.02:contrast=1.1:saturation=1.2,colorbalance=rs=0.05:gs=-0.02:bs=-0.05:rm=0.03:gm=-0.01:bm=-0.04,curves=all='0/0 0.1/0.15 0.5/0.5 0.9/0.88 1/1'
```

### Breakdown

| Filter | What It Does |
|--------|-------------|
| `eq=brightness=0.02:contrast=1.1:saturation=1.2` | Slight brightness lift, punchy contrast, rich saturation |
| `colorbalance=rs=0.05:gs=-0.02:bs=-0.05:rm=0.03:gm=-0.01:bm=-0.04` | Warm shadows (push red), teal mids (pull green/blue slightly) |
| `curves=all='0/0 0.1/0.15 0.5/0.5 0.9/0.88 1/1'` | Lifted blacks (0.1→0.15), slightly rolled-off highlights (0.9→0.88) = filmic |

## Full Pipeline (Vertical Reels)

### Extract + Grade + Scale a Segment
```bash
ffmpeg -y -ss <START> -i <INPUT> -t <DURATION> \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=brightness=0.02:contrast=1.1:saturation=1.2,colorbalance=rs=0.05:gs=-0.02:bs=-0.05:rm=0.03:gm=-0.01:bm=-0.04,curves=all='0/0 0.1/0.15 0.5/0.5 0.9/0.88 1/1'" \
  -c:v libx264 -crf 14 -preset fast -r 30 -pix_fmt yuv420p -an \
  segment_output.mp4
```

### Concatenate Segments (Hard Cuts Only)
```bash
# Create concat.txt with lines like:
# file 'segment_01.mp4'
# file 'segment_02.mp4'

ffmpeg -y -f concat -safe 0 -i concat.txt \
  -c:v libx264 -crf 16 -preset slow -r 30 -pix_fmt yuv420p \
  -movflags +faststart \
  final_output.mp4
```

## Edit Style Rules
- **Cuts:** Hard jump cuts ONLY — no dissolves, no transitions
- **Pacing:** 0.5–2 seconds per clip, build energy toward climax
- **Framing:** Center-framed compositions
- **Format:** Vertical 1080×1920 (Instagram Reels native)
- **Effects:** Clean, minimal — NO cheesy effects
- **Export:** H.264, CRF 16, slow preset, 30fps, faststart

## First Used
- **Project:** Strip Energy Miami Fitness Event Promo (v4)
- **Date:** 2026-03-28
- **Output:** `strip_promo_v4_temitayo_style.mp4` (24s, ~37MB)
