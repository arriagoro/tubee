# DaVinci Resolve Mastery Guide
### A Professional Videographer's Complete Post-Production Reference
*Compiled from official Blackmagic documentation, top YouTube educators (Casey Faris, JayAreTV, MrAlexTech, Alex Jordan, Patrick Stirling), professional colorist workflows, and community knowledge.*

---

## Table of Contents
1. [Basics: Project Setup & Foundation](#1-basics-project-setup--foundation)
2. [Cut Page vs Edit Page](#2-cut-page-vs-edit-page)
3. [Advanced Editing Techniques](#3-advanced-editing-techniques)
4. [Transitions](#4-transitions)
5. [Color Grading (Color Page)](#5-color-grading-color-page)
6. [Audio (Fairlight Page)](#6-audio-fairlight-page)
7. [Fusion Page](#7-fusion-page)
8. [Effects](#8-effects)
9. [Keyboard Shortcuts (Quick Reference)](#9-keyboard-shortcuts-quick-reference)
10. [Export Settings](#10-export-settings)
11. [Workflow Tips](#11-workflow-tips)
12. [Scripting & Automation](#12-scripting--automation)
13. [Pro Tips: Amateur vs Professional](#13-pro-tips-amateur-vs-professional)
14. [Trending Styles 2025-2026](#14-trending-styles-2025-2026)

---

## 1. Basics: Project Setup & Foundation

### Initial Project Configuration

**Creating a New Project:**
1. Open DaVinci Resolve → Project Manager appears
2. Click "New Project" → name it descriptively (e.g., `ClientName_ProjectType_Date`)
3. Before importing anything, configure project settings

**Critical Project Settings (File → Project Settings):**

| Setting | Recommendation | Why |
|---------|---------------|-----|
| Timeline Resolution | Match your delivery (1920×1080 or 3840×2160) | Prevents scaling artifacts |
| Timeline Frame Rate | Match your primary footage (23.976, 24, 25, 29.97, 30, 60) | Mismatched = stuttering |
| Playback Frame Rate | Same as timeline | Ensures smooth playback |
| Color Science | DaVinci YRGB Color Managed | Best for mixed camera sources |
| Timeline Color Space | DaVinci Wide Gamut / Intermediate | Maximum flexibility |
| Output Color Space | Rec.709 Gamma 2.4 (for SDR delivery) | Standard for web/broadcast |

**Frame Rate Rules:**
- **24fps** → Cinematic content, narrative films, music videos
- **25fps** → PAL regions (Europe, Australia)
- **29.97fps** → NTSC broadcast (North America)
- **30fps** → Web content, social media
- **60fps** → Sports, action, slow-motion source (conformed to 24 = 2.5× slow motion)
- **120fps** → Slow-motion source (conformed to 24 = 5× slow motion)

### Importing Media

**Methods:**
1. **Media Page** → Navigate to folders in the Media Storage panel (left) → drag to Media Pool
2. **Edit Page** → Right-click Media Pool → "Import Media" → browse
3. **Drag and Drop** → From Finder/Explorer directly into Media Pool

**Supported Formats (no transcoding needed):**
- Video: H.264, H.265/HEVC, ProRes (all variants), DNxHR/DNxHD, BRAW, R3D, CinemaDNG, MXF, MKV, AVI, MOV, MP4
- Audio: WAV, AIFF, MP3, AAC, FLAC
- Images: JPEG, PNG, TIFF, DPX, EXR, BMP

**Import Best Practices:**
- Always import entire folders, not individual files
- Let Resolve handle frame rates — don't transcode before importing
- Use "Copy" rather than "Move" for external drives to avoid broken links
- For BRAW (Blackmagic RAW): adjustments available in Camera Raw tab in the Color page

### Timeline Navigation

**Creating a Timeline:**
- Drag clips from Media Pool to the viewer area → auto-creates timeline
- Or: File → New Timeline → set name, tracks, start timecode
- Multiple timelines allowed per project (useful for versioning)

**Navigation Essentials:**
- **J/K/L** — Reverse / Stop / Forward playback (tap L multiple times for 2×, 4×, 8× speed)
- **Up/Down Arrow** — Jump to next/previous edit point
- **Home/End** — Go to start/end of timeline
- **Shift + Z** — Zoom to fit entire timeline in view
- **Ctrl/Cmd + Plus/Minus** — Zoom in/out on timeline
- **Alt/Opt + Scroll** — Zoom timeline at cursor position

### Basic Cuts and Trimming

**Blade Tool (B):**
- Click anywhere on a clip to split it at that point
- Ctrl/Cmd + B — Blade at playhead on all tracks
- Blade is destructive-looking but non-destructive (original media untouched)

**Selection Tool (A):**
- Default tool for moving and selecting clips
- Drag clip edges to trim (ripple or roll depending on position)

**Trim Modes:**
| Mode | What It Does | How |
|------|-------------|-----|
| Ripple Trim | Extends/shortens clip AND moves everything after it | Drag edge (default on Edit page) |
| Roll Trim | Moves the edit point between two clips (one gets longer, other shorter) | Place cursor directly on edit point |
| Slip | Changes which portion of source clip is shown (duration stays same) | Drag middle of clip with Trim mode |
| Slide | Moves clip in timeline without changing its content (neighbors resize) | Shift + drag with Trim mode |

**Trim Tool (T):**
- Dedicated tool for trimming operations
- Hover over different parts of a clip to switch between ripple, roll, slip, slide

**Three-Point Editing:**
1. Set In (I) and Out (O) points in Source Viewer
2. Set In or Out on timeline
3. Press F9 (Insert) or F10 (Overwrite)
- Insert: pushes everything right
- Overwrite: replaces what's on the timeline

---

## 2. Cut Page vs Edit Page

### Cut Page — Built for Speed

**When to Use:**
- First assembly / rough cut
- Vlog editing, talking-head content
- Quick turnaround projects
- Reviewing and selecting footage rapidly

**Key Features:**
- **Source Tape Mode** — All clips in the bin play as one long tape. Scrub through everything fast.
- **Dual Timeline** — Full timeline on top, zoomed-in view on bottom. Always see the big picture.
- **Smart Insert** — Places clip at nearest edit point (not just playhead)
- **Smart Bins** — Auto-filter by camera, date, clip type
- **Sync Bin** — Multi-camera syncing on the fly
- **Fast Review** — Plays timeline at 2× speed, stops at each edit for review

**Cut Page Workflow:**
1. Import footage (drag into Media Pool)
2. Use Source Tape to review all clips
3. Mark In/Out on interesting portions
4. Use Smart Insert, Append, or Close-Up to place clips
5. Trim in the timeline using the dual-timeline view
6. Add transitions with the transition palette
7. Add titles from the Titles panel

### Edit Page — Full Control

**When to Use:**
- Detailed editing with precise control
- Complex multi-track timelines
- Audio sync, B-roll layering, effects work
- Client-facing edits requiring precision

**Key Features:**
- **Full Timeline Control** — Unlimited video and audio tracks
- **Inspector Panel** — Transform, crop, speed, compositing, stabilization per clip
- **Effects Library** — Full access to all transitions, effects, generators
- **Keyframe Editor** — Visual keyframe control in timeline
- **Multicam Editing** — Native multicam support

**Rule of Thumb:**
- Use Cut Page for assembly → Switch to Edit Page for fine-tuning
- Anything on the Cut Page is reflected on the Edit Page (same timeline, different views)

---

## 3. Advanced Editing Techniques

### J-Cuts and L-Cuts

**J-Cut (audio leads video):**
The audio from the next clip starts before its video appears. Creates anticipation.

**How to create:**
1. Place two clips adjacent on V1
2. Unlink audio and video (Alt/Opt + click on the link icon, or select clip → right-click → Link Clips to unlink)
3. Extend the audio of Clip B to the left, under Clip A
4. Or: extend Clip A's video to the right, over Clip B's audio

**L-Cut (video leads audio):**
The video from the next clip appears while the audio from the previous clip continues. Used in interviews — show reaction while voice continues.

**How to create:**
1. Same unlinking process
2. Extend Clip A's audio to the right, under Clip B's video

**Pro tip:** Place dialogue on A1/A2, B-roll on V2. This naturally creates L-cuts and J-cuts.

### Match Cuts

A match cut connects two scenes through visual or thematic similarity (shape, movement, color, action).

**Technique:**
1. Find the exit frame in Scene A (e.g., throwing a ball upward)
2. Find the entry frame in Scene B with similar composition (e.g., rocket launching)
3. Cut precisely at the moment of maximum similarity
4. Consider using a 2-4 frame dissolve to smooth the transition

### Jump Cuts

An intentional cut within the same shot, creating a jarring time skip. Standard in YouTube/vlog content.

**Best practices:**
- Cut out pauses, "ums," and repeated takes
- Ensure the subject has moved at least 30% between cuts (otherwise it feels accidental)
- Zoom in 10-20% on alternating clips for a "two-camera" feel
- Add a subtle 2-3 frame dissolve if the jump feels too harsh

### Speed Ramps

**Creating a Speed Ramp:**
1. Right-click clip → "Retime Controls" (or Ctrl/Cmd + R)
2. Move playhead to the ramp point
3. Click the dropdown arrow on the speed indicator → "Add Speed Point"
4. Drag the speed segment to change speed (e.g., 25% for slow, 200% for fast)
5. Click the dropdown → "Retime Curve" for smooth easing
6. In the Retime Curve, select the speed point → right-click → "Smooth" for a gradual transition

**Speed Ramp Settings:**
| Speed | Effect | Use Case |
|-------|--------|----------|
| 10-25% | Dramatic slow motion | Impact moments, reveals |
| 25-50% | Smooth slow motion | B-roll beauty shots |
| 50-75% | Subtle slowdown | Emphasis without drama |
| 150-200% | Time lapse feel | Montage, travel sequences |
| 400-800% | Hyperlapse | Walking sequences, timelapses |

**Important:** For clean slow motion, your source footage must be higher frame rate than your timeline. 60fps in a 24fps timeline = 2.5× slow motion without frame interpolation.

**Optical Flow (for smoother slow-mo):**
- Right-click clip → "Retime and Scaling" → set Motion Estimation to "Optical Flow" → Quality: "Better" or "Enhanced"
- This generates intermediate frames. Works great for 2-4× slowdowns. Artifacts appear on complex motion.

### Freeze Frames

1. Place playhead on the exact frame
2. Right-click → "Retime Controls"
3. Click dropdown at playhead → "Freeze Frame"
4. Adjust duration by dragging the freeze frame boundary

**Alternative:** Export frame as still (Color Page → right-click → Grab Still), then import it back as a clip for more control.

### Multicam Editing

**Setup:**
1. Import all camera angles into a bin
2. Select all clips → right-click → "Create New Multicam Clip Using Selected Clips"
3. Sync method: **Timecode** (if cameras were synced), **Audio Waveform** (most reliable for independent cameras), or **In Point**
4. Set the multicam clip's resolution and frame rate

**Editing:**
1. Drag multicam clip to timeline
2. Right-click → "Open in Multicam Viewer"
3. Enable "Multicam" mode in the viewer
4. Play the timeline and **click on the angle** you want in real-time
5. Go back and trim edits precisely afterward

**Pro tip:** Record a "switching pass" first — just click through angles in real-time. Then do a cleanup pass with the Selection tool.

---

## 4. Transitions

### Best Practices

**The Golden Rule:** The best edit is the one the audience doesn't notice. Most professional editing uses **straight cuts** 95% of the time.

**When to Use Transitions:**
- Indicating passage of time
- Changing location or subject
- Montage sequences
- Stylistic choice (music videos, brand content)

### Transition Types & When to Use Them

| Transition | Duration | Use Case |
|-----------|----------|----------|
| Cross Dissolve | 12-24 frames (0.5-1 sec) | Time passage, soft scene change |
| Dip to Black | 24-48 frames | End of sequence, chapter break |
| Dip to White | 12-24 frames | Dreamy, flashback feel |
| Wipe | 12-24 frames | Stylistic choice only (documentary, retro) |
| Film Burn / Light Leak | 12-30 frames | Music videos, trendy content |

**Applying Transitions:**
1. Ensure there are "handles" — extra footage beyond the in/out points on both clips (at least 12 frames each side)
2. Effects Library → Video Transitions → Dissolve → drag "Cross Dissolve" to the edit point
3. Or: select edit point → press Ctrl/Cmd + T for default transition
4. Adjust duration by dragging the edges of the transition in the timeline

### Custom Transitions in Fusion

For unique transitions (glitch, ink splatter, zoom warp):
1. Create a Fusion Composition on the Edit page
2. In Fusion: use Merge nodes with animated masks to reveal Clip B from Clip A
3. Save as a Macro for reuse: select nodes → right-click → "Create Macro"

### Transitions to Avoid

- **Star Wipes, Page Curls, 3D Cube** — Look dated and amateur
- **Too many dissolves** — Makes the edit feel lazy
- **Long transitions on short clips** — Transition should never be more than 25% of clip duration
- **Random transitions** — Every transition should have a storytelling reason

---

## 5. Color Grading (Color Page)

### Understanding the Color Page Layout

**Left Panel:** Node Editor (your correction pipeline)
**Center:** Viewer with split-screen comparison
**Bottom Left:** Color Wheels / Bars / Log / Curves
**Bottom Right:** Scopes (Waveform, Vectorscope, Parade, Histogram)
**Right Panel:** Qualifier, Power Windows, Tracker, Magic Mask

### Color Correction vs Color Grading

| Color Correction | Color Grading |
|-----------------|---------------|
| Making footage look "correct" | Making footage look "intended" |
| Fix white balance, exposure | Create mood, style, emotion |
| Done first | Done second |
| Technical process | Creative process |

### The Professional Node Tree

**Recommended Node Order (based on CROMO Studio / professional colorist workflow):**

```
[Input CST: Camera → DaVinci WG/Int] → [Parallel Secondaries] → [Exposure] → [White Balance] → [Contrast/Texture] → [Color Scheme/Hue] → [Output CST: DWG/Int → Rec.709 2.4] → [Creative LUT] → [Vignette] → [Glows/Halation] → [Blur] → [Film Grain] → [Final Out]
```

**Node-by-Node Breakdown:**

1. **Input CST (Color Space Transform)** — Converts camera color space to DaVinci Wide Gamut / Intermediate
   - Effects → Color Space Transform → drag onto node
   - Input: Your camera's color space (e.g., Sony S-Log3 / SGamut3.Cine)
   - Output: DaVinci WG / Intermediate

2. **Secondaries (Parallel Nodes)** — Targeted corrections
   - Skin tone isolation (use Qualifier → select skin → refine with Matte Finesse)
   - Sky enhancement
   - Background adjustment
   - Place before primaries so masks don't shift when exposure changes

3. **Exposure** — Lift, Gamma, Gain corrections
   - Use Parade scope to balance RGB channels
   - Lift: Shadows should kiss the bottom of the waveform (not crushed)
   - Gain: Highlights should approach but not clip at 100 IRE

4. **White Balance** — Temperature + Tint
   - Use the eyedropper on something that should be neutral gray/white
   - Fine-tune with Offset wheel

5. **Contrast & Texture** — Overall punch
   - Contrast slider + Pivot adjustment
   - Texture Pop, Contrast Pop (ResolveFX)
   - Custom contrast masks for local contrast

6. **Color Scheme** — Hue shifts, tinting
   - Hue vs Hue curves for targeted color shifts
   - Color Warper for complex remapping
   - Mononodes DCTLs for advanced color work

7. **Output CST** — DaVinci WG/Intermediate → Rec.709 Gamma 2.4

8. **Creative LUT** — Film emulation, creative looks
   - Built-in: Film Emulation LUTs (Kodak, Fuji)
   - Third-party: Ground Control, Tropic Colour, Lutify.me
   - Reduce intensity with Key Output slider

9. **Vignette** — Window → Circular → Invert, soften, reduce exposure

10. **Glows/Halation** — In parallel nodes (so they don't interact)

11. **Film Grain** — Always LAST serial node. Grain responds to luminosity.

12. **Final OUT** — Fine-tune blacks, whites, cap saturation

### Color Wheels Deep Dive

**Primaries — Color Wheels:**
- **Lift** → Shadows (darks). Moving the wheel adds color to shadows only.
- **Gamma** → Midtones. Most of your image. Handle with care.
- **Gain** → Highlights. Moving the wheel tints the bright areas.
- **Offset** → Entire image. Global color shift.

**The bars below each wheel control luminance:**
- Drag down to darken that range, up to brighten

**Log Wheels (more refined):**
- **Shadow / Midtone / Highlight** with adjustable ranges
- Better for S-Log / LOG footage
- More subtle, more control

**HDR Wheels:**
- **Dark / Shadow / Light / Highlight** plus separate zones
- Each zone's range is adjustable
- Essential for HDR delivery but useful for SDR too

### Curves

**Custom Curves (most versatile):**
- RGB Master: Contrast control (S-curve for contrast)
- Individual R, G, B channels: Color balance fine-tuning
- Place point on the curve → drag up to brighten, down to darken
- Classic S-Curve: Add 2 points. Raise highlights slightly, lower shadows slightly.

**Hue vs Hue:**
- Shift specific colors without affecting others
- Click on the color you want to shift → drag the point up/down
- Example: Shift green grass → more teal, shift orange skin → more natural

**Hue vs Saturation:**
- Increase or decrease saturation of specific hues
- Useful for desaturating everything except skin tones

**Hue vs Luminance:**
- Brighten or darken specific colors
- Example: Darken blue sky for drama without affecting skin

**Luma vs Saturation:**
- Control saturation based on brightness
- Reduce saturation in very dark/very bright areas (prevents noise and clipping)

### LUTs (Look Up Tables)

**Technical LUTs:**
- Convert LOG/RAW to Rec.709
- Camera-specific (Sony S-Log3 to Rec.709, Canon C-Log to Rec.709, etc.)
- Applied as input transform or first node

**Creative LUTs:**
- Film emulation, stylistic looks
- Applied AFTER color correction
- Always adjust intensity (Key Output in the Key tab)
- Popular: Kodak 2383 (cinema standard), FujiFilm Eterna

**Installing LUTs:**
- Mac: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT/`
- Windows: `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\LUT\`
- Or: Project Settings → Color Management → Open LUT Folder

### CSTs vs LUTs

| Feature | LUT | CST |
|---------|-----|-----|
| Device-independent | No (camera-specific) | Yes |
| Information preservation | Clips data | Mathematically remaps |
| Multi-camera workflow | Needs separate LUTs | One workflow for all cameras |
| Recommended for | Quick looks, creative grading | Professional workflows, HDR |

**CST Setup:**
1. Project Settings → Color Management → Timeline Color Space: DaVinci Wide Gamut / Intermediate
2. Output Color Space: Rec.709 Gamma 2.4
3. First node: CST (Camera → DaVinci WG/Int)
4. Last node before effects: CST (DaVinci WG/Int → Rec.709 2.4)

### Skin Tone Correction

**The Vectorscope Skin Tone Line:**
- On the Vectorscope, there's a line extending from center toward the upper-left (roughly 11 o'clock)
- ALL skin tones (regardless of ethnicity) should fall on or near this line
- If skin is too red, green, or yellow, it's off the line

**Correction Workflow:**
1. Use Qualifier tool → pick skin tone with eyedropper
2. Refine selection with Matte Finesse (denoise, clean black/white)
3. Enable Highlight (View → Highlight) to see your selection
4. Use Hue vs Hue curve to shift skin toward the skin tone line
5. Use Hue vs Sat to slightly desaturate if oversaturated
6. ColorSlice tool (Resolve 19+): advanced skin tone isolation

**Key Numbers:**
- Skin tones on Vectorscope: approximately 123° (between yellow and red)
- Saturation: typically 30-50% on the Vectorscope
- Use the Qualifier's Luminance range to avoid selecting similarly-colored non-skin areas

### Cinematic Look Recipes

**Teal & Orange (Blockbuster Look):**
1. Push Lift wheel toward teal (cool blue-green)
2. Push Gain wheel toward warm orange
3. Use Hue vs Hue to protect skin tones from going too orange
4. Reduce saturation slightly (-10 to -15)
5. Add gentle S-curve for contrast

**Bleach Bypass (Desaturated, High-Contrast):**
1. Reduce saturation to 25-40%
2. Increase contrast significantly (+20 to +30)
3. Push Lift slightly toward blue
4. Add film grain
5. Optional: slight halation/glow

**Vintage/Film Look:**
1. Lift blacks (raise the bottom of the custom curve to ~5-10 IRE = faded blacks)
2. Reduce highlights slightly
3. Shift Offset toward yellow/orange
4. Reduce saturation to 60-80%
5. Add vignette and film grain

**Clean Modern / Commercial:**
1. Nail the white balance perfectly
2. Slight S-curve contrast
3. Boost saturation +5-10
4. Skin tones: ensure they're warm and natural
5. Clean, no grain, no heavy tinting

### Shot Matching

**Method 1: Copy Grade**
- Right-click graded clip in Color Page timeline → "Copy" → select target clips → Ctrl/Cmd + Middle-Click

**Method 2: Reference Still**
- Grade your hero shot → Gallery → right-click viewer → "Grab Still"
- Split-screen view: Gallery → double-click reference still → use Wipe mode to compare

**Method 3: ColorChecker / Shot Match**
- Use Resolve's automatic Color Match (right-click → Shot Match to this clip)
- Works best when clips have similar content

**Method 4: Scopes-Based Matching**
- Match the Parade waveform patterns between clips
- Get the skin tone on the same Vectorscope position
- Match histogram distributions

### HDR Grading Basics

**HDR Delivery Requirements:**
- Timeline Color Space: Rec.2020 / PQ (for HDR10) or Rec.2020 / HLG
- Monitor: Must be HDR-capable (1000+ nits for mastering)
- Use HDR Wheels instead of standard color wheels
- Peak white: 1000 nits (HDR10), 4000 nits (Dolby Vision)
- Use DaVinci Resolve Studio for Dolby Vision metadata

---

## 6. Audio (Fairlight Page)

### Fairlight Page Overview

Fairlight is a professional-grade DAW (Digital Audio Workstation) built into Resolve. It's the same technology used in feature film sound post-production.

**Layout:**
- **Top:** Toolbar, transport controls
- **Center:** Timeline with audio tracks
- **Right:** Inspector, Mixer
- **Bottom:** Effects rack per track

### Audio Levels — The Numbers That Matter

| Content Type | Target Level (LUFS) | Peak Maximum |
|-------------|---------------------|--------------|
| YouTube | -14 LUFS integrated | -1 dBTP |
| Broadcast TV | -24 LUFS (EBU R128) | -1 dBTP |
| Podcast | -16 LUFS | -1 dBTP |
| Film/Cinema | -27 LUFS (dialogue) | -3 dBFS |
| Instagram/TikTok | -14 LUFS | -1 dBTP |

**Dialog Levels:**
- Target: -12 to -6 dB on the Resolve meter
- LUFS: -14 to -16 (integrated) for YouTube

**Music Levels Under Dialog:**
- Music bed: -20 to -30 dB (duck under dialogue)
- Music alone (no dialog): -12 to -14 dB

**Sound Effects:**
- 3-6 dB below dialogue level
- Impact moments (hits, whooshes): can briefly match or exceed dialogue

### EQ (Equalization)

**Fairlight EQ:** 6-band parametric EQ available on every track.

**Essential EQ Settings:**

| Frequency Range | What It Controls | Common Adjustments |
|----------------|-----------------|-------------------|
| Below 80 Hz | Sub-bass, rumble | **High-Pass Filter at 80-100 Hz** on ALL dialogue tracks |
| 80-250 Hz | Body, warmth | Reduce muddy frequencies (200-300 Hz) |
| 250-2000 Hz | Clarity, body | Presence range for voice |
| 2-4 kHz | Presence, intelligibility | Boost 2-3 dB for dialogue clarity |
| 4-8 kHz | Sibilance, brightness | De-ess or reduce if harsh (5-8 kHz) |
| 8-20 kHz | Air, sparkle | Gentle shelf boost for "air" |

**Dialogue EQ Preset:**
1. High-Pass at 80 Hz (12 dB/oct rolloff)
2. Cut 300 Hz by -3 dB (reduce muddiness, Q: 1.5)
3. Boost 3 kHz by +2 dB (add presence, Q: 2.0)
4. High shelf at 10 kHz: +1 dB (add air)

### Compression

**What it does:** Reduces the dynamic range — makes quiet parts louder and loud parts softer.

**Fairlight Compressor Settings for Dialogue:**
| Parameter | Setting | Why |
|-----------|---------|-----|
| Threshold | -20 to -15 dB | Where compression kicks in |
| Ratio | 3:1 to 4:1 | Gentle compression |
| Attack | 5-10 ms | Fast enough to catch transients |
| Release | 50-100 ms | Smooth release |
| Makeup Gain | +3-6 dB | Compensate for volume reduction |
| Knee | Soft | Gradual onset |

**For Music/Sound Design:**
- Ratio: 2:1 to 3:1 (lighter)
- Attack: 10-30 ms (preserve transients)
- Release: 100-200 ms

### Noise Reduction

**Built-in Noise Reduction (Fairlight FX):**
1. Select track → Effects → Fairlight FX → "Noise Reduction"
2. Set "Threshold" to match your noise floor (play a silent section to gauge)
3. Start with Auto mode → adjust manually if artifacts appear
4. Typical settings: Threshold -30 to -40 dB, Sensitivity: medium

**De-Hum (remove 50/60 Hz electrical hum):**
1. Fairlight FX → De-Hum
2. Select 50 Hz (Europe) or 60 Hz (North America)
3. Enable harmonics removal

**De-Esser:**
1. Fairlight FX → De-Esser
2. Frequency: 5-8 kHz
3. Threshold: adjust until sibilance is tamed without making speech "lispy"

**For heavy noise:** Use third-party plugins like iZotope RX (industry standard) or CrumplePop.

### Audio Ducking

**Method 1: Manual Ducking**
1. On the music track, use the Volume automation (click the diamond icon to enable automation)
2. At points where dialogue starts, keyframe the music down 10-15 dB
3. Add a gradual fade (0.5-1 second) for smooth transitions

**Method 2: Sidechain Compression**
1. Add a Compressor to the music track
2. Set the sidechain input to the dialogue track
3. Threshold: -20 dB, Ratio: 4:1, Attack: 20ms, Release: 200ms
4. Music automatically ducks when dialogue is present

**Method 3: Fairlight Automatic Ducking (Resolve 18+)**
1. Right-click the dialogue track → "Enable Auto Duck"
2. Adjust duck amount and sensitivity

### Music Sync Editing

**Beat-Synced Editing:**
1. Import music track first, place on A1
2. Play the music and tap "M" at each beat to place markers
3. Use markers as snap points for video cuts
4. Enable snapping (N) and cuts will snap to markers

**Pro Technique:**
- Mark major beats (downbeats) with one color
- Mark minor beats / upbeats with another color
- Cut on downbeats for emphasis, on upbeats for flow

---

## 7. Fusion Page

### Understanding Node-Based Compositing

**Key Concept:** Unlike After Effects' layer system, Fusion uses a node-based workflow. Signal flows left to right, from inputs through effects to outputs.

**Four Main Node Types:**
1. **Generator Nodes** — Create content (Text+, Background, sRectangle, sEllipse, pEmitter)
2. **Effect Nodes** — Modify content (Blur, Glow, ColorCorrector, Transform)
3. **Merge Nodes** — Combine content (Merge, sMerge for shapes)
4. **Mask Nodes** — Define areas (Rectangle, Ellipse, Polygon, Bitmap)

**Node Connections:**
- **Green input** = Foreground (on top)
- **Orange input** = Background (behind)
- **Blue input/output** = Effect mask / Alpha channel
- **White** = Data connections

### Essential Fusion Workflows

**Adding Text:**
1. Edit Page → Effects → Titles → "Fusion Title" → drag to timeline
2. Switch to Fusion page
3. Select Text+ node → Inspector: type text, choose font, size, color
4. Animate: keyframe Position X/Y, Size, or Opacity over time

**Lower Third Animation (Step-by-Step):**
1. Add "Fusion Composition" from Effects to timeline, set duration
2. In Fusion, add: Background node (set to your bar color + low height) → Merge → MediaOut
3. Add Text+ → Merge with the Background bar
4. Add Rectangle mask on Background for shape
5. Animate: Keyframe the bar's X position from offscreen to final position
6. Keyframe text opacity from 0 to 1 (slight delay after bar appears)
7. Save as Macro: select all nodes → right-click → "Create Macro" for reuse

**Motion Graphics with Vector Shapes:**
1. Right-click node graph → Add Tool → Shape → sNGon (or sRectangle, sEllipse)
2. Add sRender node → connect shape output to sRender input → sRender to MediaOut
3. Add sGrid between shape and sRender for grid duplication
4. Add sTransform between shape and sGrid for individual element animation
5. Keyframe rotation, position, scale in sTransform
6. Add sMerge to combine multiple shape layers
7. Standard Merge node to composite shapes with Text+ or video

### Compositing a 2D Element in 3D Space

1. Select clip on Edit page → go to Fusion
2. Add Camera Tracker: Shift + Space → search "Camera Tracker"
3. Inspector → enable "Preview Auto Track Locations"
4. Lower Minimum Feature Separation for more tracking points
5. Click "Auto Track"
6. Go to Solve tab → "Solve" → aim for Average Solve Error < 1.0
7. Export tab → "Export" → adds camera data nodes
8. Delete Ground Plane node (visual artifact)
9. Add Image Plane 3D node → connect your PNG element
10. Adjust scale/position in Inspector → Transform tab
11. Add Blur to element if needed for depth-of-field matching

### Particle Effects

1. Add pEmitter node (particle emitter) → set shape, rate, lifespan
2. Add pRender node to render particles
3. Connect: pEmitter → pRender → Merge (over your background) → MediaOut
4. Adjust in Inspector: Number (particle count), Velocity, Spin, Color over life
5. Add pTurbulence, pGravity, or pBounce between Emitter and Render for behavior

### Saving Fusion Templates

- Select nodes → right-click → "Create Macro"
- Name it descriptively
- Save to: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Templates/Edit/`
- Access from Edit page Effects panel under "Titles" or "Effects"

---

## 8. Effects

### Speed Ramps (Detailed)

See [Advanced Editing > Speed Ramps](#speed-ramps) for full technique.

**Additional tip:** Use the Retime Curve editor for precise easing. Select the speed point → right-click → choose "Smooth" or manually adjust bezier handles for custom acceleration/deceleration curves.

### Dynamic Zoom (Ken Burns Effect)

1. Select clip → Inspector → enable "Dynamic Zoom"
2. Set start frame (green box) and end frame (red box) in the viewer
3. Swap direction with the swap button
4. Choose Ease: Linear, Ease In, Ease Out, or Ease In and Out

**Pro Alternative (more control):**
1. Use Transform keyframes on the Edit page
2. Keyframe Zoom at start and end of clip
3. Add Position keyframes to pan while zooming
4. Set interpolation to "Smooth" for natural movement

### Shake/Handheld Effect

**Method 1: Resolve FX Camera Shake**
1. Effects Library → ResolveFX Transform → "Camera Shake"
2. Drag onto clip
3. Adjust: Motion Scale, Speed Scale, Randomness
4. Keep it subtle: Motion Scale 0.5-2.0 for realistic handheld

**Method 2: Fusion (more control)**
1. Select clip → Fusion page
2. Add Transform node between MediaIn and MediaOut
3. Right-click Center X → "Modify With" → "Perturb"
4. Set Strength to 0.002-0.005, Speed to 0.5-2.0
5. Repeat for Center Y
6. This creates random organic camera movement

### Glow Effect

**ResolveFX Glow:**
1. Color Page → OpenFX panel → "Glow"
2. Drag to a node
3. Shine Threshold: 0.5-0.7 (determines what glows)
4. Spread: 0.3-0.5 (glow size)
5. Composite: Screen mode, Gain: 0.3-0.5

**Halation (Film-Style Glow):**
1. Use "Resolve FX Light" → "Halation"
2. Simulates light bleeding through film stock
3. Add AFTER the creative LUT, in a parallel node
4. Intensity: 0.1-0.3 for subtlety

### Film Grain

**ResolveFX Film Grain:**
1. Color Page → OpenFX → "Film Grain" or "Resolve FX Texture → Film Grain"
2. Apply to the LAST node in your node tree
3. Settings:
   - Grain Size: 0.3-0.6 (larger = more visible)
   - Softness: 0.3 (keep some detail)
   - Strength: 0.15-0.30 for subtle, 0.4-0.6 for heavy vintage
4. Check: Grain should be visible at 100% zoom but not distracting at normal viewing distance

**Why last node?** Grain responds to luminosity. If luminosity changes after grain is applied, the grain pattern won't match the image correctly.

### Zoom Transitions / Zoom Effects

**Punch Zoom (Edit Page):**
1. Cut the clip where you want the zoom
2. On the second half: Inspector → Zoom: increase to 1.5-2.0×
3. First frame of the zoomed portion creates a "punch-in" effect
4. For smooth zoom: add 4-8 frame transition with keyframed Zoom

**Whip Zoom (Fusion):**
1. Add Transform node
2. Keyframe Size from 1.0 to 2.0 over 6-10 frames
3. Add Directional Blur during the zoom for motion feel
4. Ease: start fast, end slow (ease out)

---

## 9. Keyboard Shortcuts (Quick Reference)

*See the separate `davinci_shortcuts.md` file for the complete reference.*

**Top 20 Shortcuts You Must Know:**

| Shortcut | Action |
|----------|--------|
| J / K / L | Reverse / Stop / Forward |
| I / O | Mark In / Mark Out |
| B | Blade tool |
| A | Selection tool |
| T | Trim tool |
| Ctrl/Cmd + B | Blade at playhead (all tracks) |
| Ctrl/Cmd + Shift + [ | Ripple delete clip |
| Ctrl/Cmd + T | Apply default transition |
| N | Toggle snapping |
| Shift + Z | Fit timeline to window |
| Alt/Opt + S | Add serial node (Color page) |
| Alt/Opt + P | Add parallel node (Color page) |
| Ctrl/Cmd + D | Disable node (Color page) |
| Shift + D | Bypass all grading (Color page) |
| Ctrl/Cmd + R | Retime controls |
| F9 | Insert edit |
| F10 | Overwrite edit |
| Shift + F9 | Insert with ripple |
| Space | Play / Stop |
| Ctrl/Cmd + Z | Undo |

---

## 10. Export Settings

### YouTube

**Optimal Settings:**
| Parameter | Value |
|-----------|-------|
| Format | QuickTime or MP4 |
| Codec | H.264 (free) or H.265 (Studio) |
| Resolution | 3840×2160 (upload in 4K even if content is 1080p — YouTube allocates higher bitrate) |
| Frame Rate | Match project (23.976, 24, 30, 60) |
| Quality | Restrict to 80,000 Kbps (4K) or 30,000 Kbps (1080p) |
| Or | Automatic → Best quality |
| Audio Codec | AAC |
| Audio Bitrate | 320 Kbps |
| Data Levels | Auto |
| Color Space Tag | Rec.709-A |

**Pro tip:** Upload in 4K even for 1080p content. YouTube's compression is gentler on 4K uploads, resulting in better-looking 1080p playback.

### Instagram Reels / TikTok

| Parameter | Value |
|-----------|-------|
| Format | MP4 |
| Codec | H.264 |
| Resolution | 1080×1920 (9:16 vertical) |
| Frame Rate | 30fps |
| Bitrate | 20,000-30,000 Kbps |
| Audio | AAC, 256 Kbps |
| File Size | Under 4GB (Instagram), under 287MB (TikTok ideal) |

**Vertical Video Setup:**
- Project Settings → Timeline Resolution: 1080×1920
- Or: Deliver page → Custom Resolution: 1080×1920

### Client Delivery (ProRes)

| Parameter | Value |
|-----------|-------|
| Format | QuickTime |
| Codec | Apple ProRes 422 HQ (master) or ProRes 4444 (with alpha) |
| Resolution | Match project |
| Frame Rate | Match project |
| Audio | Linear PCM, 48 kHz, 24-bit |
| Data Levels | Auto |

**ProRes Variants:**
| Variant | Bitrate (1080p24) | Use Case |
|---------|-------------------|----------|
| ProRes 422 Proxy | ~15 Mbps | Offline editing |
| ProRes 422 LT | ~30 Mbps | Internal review |
| ProRes 422 | ~50 Mbps | Standard delivery |
| ProRes 422 HQ | ~75 Mbps | Broadcast / archive master |
| ProRes 4444 | ~110 Mbps | VFX with alpha channel |
| ProRes 4444 XQ | ~165 Mbps | Maximum quality master |

### H.265 / HEVC

- **Requires DaVinci Resolve Studio** (paid) for encoding
- 40-50% smaller files than H.264 at same quality
- Best for: archival, high-quality client delivery, streaming platforms that support it
- Settings: Same as H.264 but reduce bitrate by 30-40%

### DNxHR (Avid Ecosystem)

| Parameter | Value |
|-----------|-------|
| Format | MXF or QuickTime |
| Codec | DNxHR HQ or DNxHR HQX |
| Use Case | Broadcast delivery, Avid round-trip |

### Batch Rendering

1. Set your export settings on the Deliver page
2. Click "Add to Render Queue" (NOT "Render" directly)
3. Change settings, add another job if needed
4. Click "Render All" to batch process

**Individual Clips Mode:** Set render mode to "Individual Clips" to export each timeline clip as a separate file (useful for social media content batches).

---

## 11. Workflow Tips

### Proxy Editing

**When to Use:** When your system struggles with 4K/6K/8K footage, BRAW, or RED files.

**Setup:**
1. Media Pool → select clips → right-click → "Generate Proxy Media"
2. Choose resolution: Quarter (1/4) or Half (1/2)
3. Choose codec: ProRes 422 Proxy (fast) or H.264 (smaller)
4. Playback → Proxy Mode → "Prefer Proxies"

**Optimized Media (Alternative):**
1. Media Pool → select clips → right-click → "Generate Optimized Media"
2. Project Settings → Master Settings → Optimized Media Resolution: choose
3. Resolve uses optimized media during editing, full-res for delivery
4. DNxHR SQ or ProRes 422 recommended

**Key Difference:**
- **Proxy:** Separate files, can be moved between systems
- **Optimized:** Stored in Resolve's cache, faster to generate

### Bin Organization

**Professional Bin Structure:**
```
📁 Master Project
├── 📁 01_Footage
│   ├── 📁 A-Cam
│   ├── 📁 B-Cam
│   ├── 📁 Drone
│   └── 📁 Phone
├── 📁 02_Audio
│   ├── 📁 Dialogue
│   ├── 📁 Music
│   └── 📁 SFX
├── 📁 03_Graphics
│   ├── 📁 Titles
│   ├── 📁 Lower Thirds
│   └── 📁 Logos
├── 📁 04_Stills
├── 📁 05_VFX
├── 📁 06_Exports
└── 📁 07_Selects
```

### Smart Bins

**Setup:** Media Pool → right-click → "Smart Bins"

**Useful Smart Bins:**
| Smart Bin | Rule |
|-----------|------|
| 4K Footage | Resolution is 3840×2160 |
| Slow Motion | Frame Rate > 60 |
| Long Takes | Duration > 60 seconds |
| Today's Import | Date Created is Today |
| A-Camera | Camera # contains "A7" |

### Markers & Marker Colors

**Marker Color Convention:**
| Color | Meaning |
|-------|---------|
| Blue | General note |
| Green | Good take / approved |
| Red | Problem / fix needed |
| Yellow | Review needed |
| Purple | VFX shot |
| Cyan | Audio issue |
| Pink | B-roll needed |

**Using Markers:**
- **M** — Add marker at playhead
- **Shift + M** — Open marker dialog (add notes, change color, set duration)
- Markers can be added to clips (source) or timeline (position-based)
- DaVinci Resolve Index panel shows all markers in a searchable list

### Power Grades

**Saving:**
1. Color Page → Gallery panel → right-click viewer → "Grab Still"
2. Right-click the still → "Apply Grade"
3. To save as Power Grade (available across all projects): drag still to "Power Grades" album in Gallery

**Organizing:**
- Create albums: "Interview Look," "Outdoor," "Night," "Client A"
- Export Power Grades: right-click → "Export" (.drx file)

### Project Backup

- **Live Save:** File → Project Settings → uncheck "Disable Live Save" (saves constantly)
- **Project Archive:** File → Export Project Archive → includes media, LUTs, stills
- **Database Backup:** Project Manager → right-click database → "Back Up"
- **Auto-save:** Every 5-10 minutes by default

---

## 12. Scripting & Automation

*See the separate `davinci_scripting_api.md` file for the complete API reference.*

### What Can Be Automated

| Task | API Support |
|------|-------------|
| Create projects | ✅ Full |
| Import media | ✅ Full |
| Create timelines | ✅ Full |
| Append clips to timeline | ✅ Full |
| Set render settings | ✅ Full |
| Start/stop rendering | ✅ Full |
| Add markers | ✅ Full |
| Set/get metadata | ✅ Full |
| Apply LUTs | ✅ Full |
| Apply CDL grades | ✅ Full |
| Copy grades between clips | ✅ Full |
| Switch pages | ✅ Full |
| Modify clip properties | ✅ Partial |
| Fusion compositions | ✅ Via Fusion scripting |
| Fairlight audio | ✅ Limited |
| Color grading (detailed) | ✅ Via DRX files |
| Export stills | ✅ Full |

### Quick Start Example

```python
#!/usr/bin/env python3
import DaVinciResolveScript as dvr_script

# Connect to running Resolve instance
resolve = dvr_script.scriptapp("Resolve")
pm = resolve.GetProjectManager()

# Create a new project
project = pm.CreateProject("My_Automated_Project")

# Import media
ms = resolve.GetMediaStorage()
mp = project.GetMediaPool()
clips = ms.AddItemListToMediaPool(["/path/to/footage/clip1.mov", "/path/to/footage/clip2.mov"])

# Create timeline from clips
timeline = mp.CreateTimelineFromClips("Main Edit", clips)

# Set render settings and render
project.SetRenderSettings({"TargetDir": "/path/to/output", "CustomName": "Final_v1"})
project.SetCurrentRenderFormatAndCodec("mp4", "H264_NVIDIA")
project.AddRenderJob()
project.StartRendering()
```

---

## 13. Pro Tips: Amateur vs Professional

### What Separates Amateur Edits from Professional Ones

**1. Pacing & Rhythm**
- Amateurs: Clips are too long. Cuts are random.
- Pros: Every cut has a reason. Pacing matches the energy of the content and music.
- **Rule:** If a clip isn't adding new information after 3-5 seconds, cut.

**2. Audio Quality**
- Amateurs: Camera-mounted mic, inconsistent levels, no music ducking, audible room echo.
- Pros: Clean dialogue, consistent levels (-14 LUFS for YouTube), music ducked under speech, proper EQ.
- **Rule:** Bad audio is worse than bad video. Audiences forgive visual imperfections but not audio ones.

**3. Color Consistency**
- Amateurs: Each clip looks different. Over-saturated or flat.
- Pros: Every clip in a scene matches. Skin tones are natural. There's a deliberate color palette.
- **Rule:** Grade your hero shot first, then match everything to it.

**4. Invisible Editing**
- Amateurs: Flashy transitions, excessive effects, cuts that draw attention.
- Pros: Straight cuts, motivated transitions, effects that serve the story.
- **Rule:** If the audience notices your editing, you've failed (unless it's intentional style).

**5. Sound Design**
- Amateurs: Only dialogue and music.
- Pros: Room tone, ambient sound, foley, subtle sound effects that sell the scene.
- **Rule:** Add room tone under every dialogue scene. Add subtle ambient sound to every outdoor scene.

**6. B-Roll Coverage**
- Amateurs: Talking head only. Or random B-roll that doesn't connect to dialogue.
- Pros: B-roll that illustrates what's being said. Cutaways that add context. Detail shots.
- **Rule:** For every 10 seconds of dialogue, have at least 3-5 seconds of relevant B-roll.

**7. Text & Graphics**
- Amateurs: Default fonts, poor positioning, no animation.
- Pros: Branded fonts, clean lower thirds, subtle animations, proper safe margins.
- **Rule:** Use 2-3 fonts max. Text should have breathing room (padding). Animate in/out.

**8. Export Quality**
- Amateurs: Wrong resolution, visible compression artifacts, wrong frame rate.
- Pros: Match platform requirements, upload masters to archive, proper color space tags.

**9. Timeline Hygiene**
- Amateurs: Single video track, audio on random tracks, no markers, no bins.
- Pros: V1 = A-cam, V2 = B-roll, V3 = Graphics. A1/A2 = Dialogue. A3/A4 = Music. A5+ = SFX. Named tracks. Color-coded clips.

**10. Delivery of Multiple Formats**
- Amateurs: One export, hope it works everywhere.
- Pros: Separate exports for YouTube (16:9), Instagram (9:16, 1:1), Twitter (16:9), and a ProRes master for archive.

---

## 14. Trending Styles 2025-2026

### Social Media (Reels, TikTok, Shorts)

**Fast-Paced Micro-Cuts:**
- 1-3 second clips maximum
- Beat-synced cutting (every cut on a beat)
- Jump cuts with zoom punches between cuts
- Text overlays timed to speech

**Cinematic B-Roll with Text:**
- Slow-motion B-roll (shot at 60-120fps)
- Large bold text (centered, animated)
- Film-emulated color grade (grain, faded blacks)
- Clean transitions (cuts or whip pans only)

**"Documentary Style" Talking Head:**
- Two-camera look (one wide, one tight — even from single cam with digital zoom)
- Subtitles burned in (with highlighted active word)
- Minimal graphics, clean typography
- Color grade: warm, slightly desaturated

### Music Videos

**Vintage Film Revival:**
- Heavy film grain (35mm simulation)
- Faded blacks (lifted shadows)
- Halation on bright objects
- Anamorphic lens flares
- 4:3 aspect ratio with rounded corners

**Hyper-Stylized Color:**
- Extreme tinting (all-red, all-blue scenes)
- High contrast, deep blacks
- Cross-processing looks (shifted hues)
- Split-toning with complementary colors

**Speed Ramp Everything:**
- Constant speed changes synced to music
- Normal speed on lyrics → 400% speed on instrumentals → 25% slow-mo on drops
- Optical Flow for smooth slow-motion

### Brand Content / Commercial

**Clean & Minimal:**
- Neutral color grade, slightly warm
- Crisp text animations (Fusion)
- Smooth transitions (dissolves at 12 frames)
- Consistent typography matching brand guidelines

**Aerial + Ground Combo:**
- Drone establishing shot → ground-level follow
- Speed ramp from drone normal speed to hyperlapse
- Color match between aerial and ground footage

**Product Hero Shots:**
- Speed ramp reveal (fast approach → smooth stop)
- Shallow depth of field (real or simulated)
- Clean white/dark background
- Subtle glow on product highlights

### Documentary / Vlog 2025-2026

**Run-and-Gun Aesthetic:**
- Intentional camera shake (but stabilized enough to be watchable)
- Natural color grade — avoid heavy stylization
- Ambient sound prominent in mix
- Jump cuts as standard

**Hybrid Interview:**
- Main interview framing with overlaid text quotes
- Split-screen moments (interviewer + interviewee)
- Archive footage intercut with modern footage
- Desaturated archive + vivid modern creates visual contrast

---

## Video Tutorial Sources Referenced

This knowledge base was compiled from studying and synthesizing techniques from the following sources:

### YouTube Educators
1. **Casey Faris** — Beginner-friendly DaVinci Resolve tutorials, complete workflows
2. **JayAreTV** — Color grading deep dives, Fusion tutorials, advanced techniques
3. **MrAlexTech** — Quick tips, efficiency workflows, shortcuts mastery
4. **Alex Jordan** — Cinematic color grading, camera-to-post workflows
5. **Patrick Stirling** — Advanced Fusion VFX, particle effects, motion design
6. **Primal Video** — Complete beginner tutorials, export optimization
7. **Kevin Stratvert / CameraTim** — Fusion motion graphics, lower thirds
8. **Carl Tomich** — Step-by-step beginner workflows
9. **Socratica FX** — Scripting API, console commands, automation
10. **Gedaly Guberek (DVResolve.com)** — Certified Master Trainer content

### Websites & Documentation
11. **Blackmagic Design Official** — Training materials, user manual, scripting API
12. **CROMO Studio (cromostudio.it)** — Professional node tree workflows, CST vs LUT analysis
13. **Miracamp** — Color grading workflow, AI tools, Power Grades
14. **Storyblocks** — Color grading tutorials, Fusion compositing guide
15. **CreatedTech** — Step-by-step cinematic grade tutorials
16. **FilmmakingElements** — Fusion motion graphics with vector shapes
17. **DaVinci Resolve Wiki (wiki.dvresolve.com)** — Scripting API documentation
18. **Unofficial API Docs (deric.github.io)** — Formatted scripting reference
19. **ResolveDevDoc (readthedocs.io)** — Community API documentation
20. **VFXStudy.com** — Fusion and VFX tutorials

### Community & Forums
21. **r/davinciresolve** — Workflow tips, troubleshooting, feature discussions
22. **Blackmagic Design Forum** — Official user community, bug reports, feature requests
23. **Liftgammagain.com** — Professional colorist community

---

*Last updated: March 2026*
*Written for DaVinci Resolve 19/20 (free and Studio versions)*
*For the professional videographer who knows how to shoot — this is your post-production weapon.*
