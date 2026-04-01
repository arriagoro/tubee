# Tubee Daily Improvements

## 2026-04-01 (Tuesday)

### Research Summary

**AI Video Editing Landscape (April 2026)**
- Fast-inference models (LTX-2.3-Fast, Hailuo 2.3 Fast) now generate clips in seconds — iteration speed is the new competitive edge
- Google Veo 3.1 and Runway Gen-4.5 produce footage indistinguishable from professional cinematography
- 52% of TikTok/Reels content now involves AI elements; 87% of creative pros use AI video tools weekly
- Auto-clipping, smart captions, and silence removal are fully commoditized — differentiation requires style intelligence
- Quality threshold has crossed: temporal consistency, lighting, and physics are now near-perfect in leading tools

**Anthropic/Claude Updates (April 2026)**
- Claude Opus 4.6 (released Feb 5, 2026) remains the strongest model — 1M token context, 76% long context retrieval (up from 18.5%)
- Claude Code got major March updates: voice mode, /loop for recurring tasks, Opus 4.6 as default
- Claude Haiku 3 being deprecated April 19 — Tubee already uses Haiku 4.5 ✅
- Opus 4.6 beats GPT-5.2 and Gemini 3 Pro on most benchmarks — ideal for complex creative edit decisions

**Trending Edit Styles (Reels/TikTok, April 2026)**
1. **UGC-Style Authenticity** — Slightly imperfect, handheld feel with jump cuts. 161% higher conversion rates for brands
2. **Micro-Cinematic** — 15-30s clips with cinematic grading, shallow DoF feel. 3x engagement vs standard edits
3. **Anime/Ghibli Aesthetics** — 155M+ TikTok videos with anime filters. Bold, saturated colors that forgive AI imperfections
4. **Fast Jump Cuts** — Sub-2-second retention window, remove all dead air
5. **Kinetic Typography** — Animated text synced to beats — the #1 differentiator in viral Reels
6. **Pattern Interrupts** — Visual surprises every 5-7 seconds (flash, zoom, reverse) to reset viewer attention

---

### Today's Improvements (5 Actionable Items)

#### 1. 🐛 FIX: Aspect Ratio Variable Scoping Bug (CRITICAL)
**Priority:** CRITICAL | **Effort:** Low | **Status:** ✅ IMPLEMENTED
**What:** `output_width` and `output_height` were defined inside `process_job()` but referenced inside `_extract_segments()` as free variables — this would cause a `NameError` at runtime when processing any job.
**Fix:** Added `output_width` and `output_height` as explicit parameters to `_extract_segments()` and passed them from `process_job()`.
**Files changed:** `backend/processor.py`

#### 2. 📱 Add Multi-Format Export (Aspect Ratio Selector)
**Priority:** HIGH | **Effort:** Medium | **Status:** ✅ IMPLEMENTED
**What:** Added aspect ratio selection to both API and frontend. Users can now choose between 9:16 (Reels/TikTok), 1:1 (IG square), 4:5 (IG portrait), and 16:9 (YouTube) directly from the editor UI.
**Why:** Creators post the same content across platforms. One-click format switching saves significant time and is a feature every competitor offers.
**Files changed:** `backend/main.py` (EditRequest model + style mapping), `frontend/src/app/editor/page.tsx` (format picker UI)

#### 3. 🎨 Wire Style Presets Through API
**Priority:** HIGH | **Effort:** Low | **Status:** ✅ IMPLEMENTED
**What:** The frontend had style pills (Cinematic, Music Video, Retro, etc.) but the style selection was never sent to the backend. Now the frontend sends the style in the `/edit` request, and `main.py` maps frontend style names to backend presets (e.g., "Music Video" → "cole_bennett", "Retro" → "vintage").
**Why:** Users were selecting styles but getting no effect — this was a broken feature.
**Files changed:** `backend/main.py`

#### 4. 🎬 Add Vintage 2026 Style Preset
**Priority:** MEDIUM | **Effort:** Low | **Status:** ✅ IMPLEMENTED
**What:** Added a new "vintage_2026" style preset that combines the existing vintage grade with heavier grain (25), stronger vignette (0.5), subtle chromatic aberration (RGB split offset 2), and 4:3 letterboxing for the full retro look trending on Reels.
**Why:** Vintage/retro is the #2 trending aesthetic. The existing "vintage" preset was too subtle — this one matches the actual viral look.
**Files changed:** `backend/effects.py`, `backend/processor.py`

#### 5. 🧠 Update AI Prompt with Q2 2026 Trends
**Priority:** MEDIUM | **Effort:** Low | **Status:** ✅ IMPLEMENTED
**What:** Updated the trending styles section in Claude's editing prompt to include April 2026 trends: UGC-style authenticity, micro-cinematic, anime/Ghibli color influence, and pattern interrupts every 5-7 seconds.
**Why:** The prompt drives Claude's editing decisions. Keeping it current with what's actually trending means Tubee's auto-edits match what performs on social media right now.
**Files changed:** `backend/ai_editor.py`

---

### Implementation Summary
All 5 items implemented directly in code. Changes are backward-compatible — no API breaking changes.

**Files modified:**
- `backend/processor.py` — Bug fix: aspect ratio variable scoping
- `backend/main.py` — API: style + aspect_ratio params, style name mapping
- `backend/effects.py` — New vintage_2026 preset
- `backend/ai_editor.py` — Updated trending styles prompt
- `frontend/src/app/editor/page.tsx` — Format picker UI, send style + aspect_ratio

### Next Priorities
- Add FCPXML export integration into the API (code exists in processor.py but isn't called from main.py)
- Implement server-side video preview/thumbnail generation for the frontend
- Add progress estimation based on file size + scene count (instead of fixed percentages)
- Prototype auto-captioning via Whisper → kinetic text pipeline
- Consider offering Opus 4.6 as a "Premium Edit" toggle in the UI

---

## 2026-03-29 (Sunday)

### Research Summary

**AI Video Editing Landscape (March 2026)**
- OpusClip and similar tools now auto-convert long-form to 12+ viral shorts in under 4 minutes — the bar for "auto-editing" speed is very high
- AI color grading presets and instant mood-switching are now standard features across competitors
- 4K output with temporal consistency (no flickering/artifacts) is the new baseline — 1080p is minimum table stakes
- B-roll matching, auto-captioning, and silence removal are considered commodity features

**Anthropic/Claude Updates (March 2026)**
- Claude Opus 4.6 launched this month — strongest model yet for complex multi-step tasks
- Tubee currently uses `claude-haiku-4-5` for edit decisions — this is smart for cost, but Opus 4.6 could unlock better creative decisions on premium edits
- Claude now supports interactive apps on mobile — potential for richer edit preview experiences via API

**Trending Edit Styles (Reels/TikTok, March 2026)**
1. **Fast Jump Cuts** — Remove all dead air, deliver value every second. Sub-2-second retention window
2. **Kinetic Typography** — Animated text synced to music beats (huge on Reels right now)
3. **Vintage Film Aesthetic** — Grain, warm tones, 4:3 crops, VHS/film emulation
4. **Seamless Motion Transitions** — Whip pans, zoom morphs, match cuts between scenes
5. **AI Smart Color Grading** — Generative presets that shift mood instantly

---

### Today's Improvements (5 Actionable Items)

#### 1. 🎯 Add "Trending Style" Presets to AI Prompt
**Priority:** HIGH | **Effort:** Low (prompt-only change)
**What:** Update `ai_editor.py` prompt to include awareness of current trending styles. When users say "make it viral" or "trending style," Claude should default to fast jump cuts with kinetic text and beat-synced transitions.
**Why:** The current prompt is generic. Adding style intelligence makes Tubee's output match what actually performs on Reels/TikTok right now.

#### 2. 🎬 Add Kinetic Typography Effect
**Priority:** HIGH | **Effort:** Medium (new FFmpeg filter chain)
**What:** Add a `kinetic_text` effect to `effects.py` that renders animated text overlays synced to beat timestamps — text that scales, slides, or bounces on each beat hit.
**Why:** This is THE trending edit style of Q1 2026. Every viral Reel has animated text. Tubee's current text overlay is static — making it kinetic would be a major differentiator.

#### 3. ⚡ Add Smart Model Routing (Haiku vs Opus)
**Priority:** MEDIUM | **Effort:** Low (logic change in ai_editor.py)
**What:** Route simple/short edits through Haiku (fast, cheap) but use Claude Opus 4.6 for complex prompts (multi-scene narratives, specific creative directions). Add a `smart_route_model()` function that checks prompt complexity.
**Why:** Opus 4.6 just dropped and excels at complex multi-step reasoning. Using it selectively for premium edits improves quality without blowing up API costs.

#### 4. 📱 Add Vertical-First Aspect Ratio Options
**Priority:** MEDIUM | **Effort:** Low (processor.py change)
**What:** Currently hardcoded to 1080x1920 (9:16). Add support for 1:1 (Instagram feed), 4:5 (Instagram post), and 16:9 (YouTube) with smart auto-crop that keeps subjects centered using FFmpeg's `crop` filter with scene-aware positioning.
**Why:** Creators post the same content across platforms. One-click format switching would save significant time.

#### 5. 🎨 Add Vintage Film Preset
**Priority:** MEDIUM | **Effort:** Medium (new effects.py preset)
**What:** Create a "Vintage 2026" style preset combining: warm color shift, subtle grain (using existing `apply_film_grain`), slight 4:3 letterboxing, occasional light leak flashes, and reduced saturation. Wire it as a new preset in the style system.
**Why:** Vintage/retro is the #2 trending aesthetic on Reels/TikTok right now. Tubee already has grain and color grading components — just needs a curated combo preset.

---

### Implementation Notes
- Items 1 and 3 are pure Python changes, no new dependencies
- Item 2 needs FFmpeg drawtext with expression-based animation (doable with existing FFmpeg)
- Item 5 can compose existing effects from `effects.py`
- All changes are backward-compatible — no breaking API changes

### Next Session
- Implement items 1 and 3 (prompt engineering + model routing) — these are quick wins
- Prototype kinetic typography FFmpeg filter chain
- Test vintage preset composition
