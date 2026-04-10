# Tubee AI Video Editing App — Research Log

---

## 2026-04-07 (Monday)

### 1. NEW AI MODELS

**Google Gemma 4 (Released Apr 2)** — Open-source (Apache 2.0) model family in 4 sizes: E2B, E4B, 26B MoE, 31B Dense. Natively processes video and images. #3 open model on Arena AI leaderboard. Runs on laptop GPUs and workstations.
- **Should Tubee add this?** YES — the 26B MoE model is a game-changer for local inference on M4 Mac Mini. Vision + video understanding built in means Tubee could offer scene analysis, OCR on video frames, and content understanding without API costs.
- **How hard?** Medium — available on Hugging Face, compatible with llama.cpp/Ollama ecosystem. 1-2 weeks to integrate.
- **Cost?** FREE (Apache 2.0, runs locally)

**Google Veo 3.1 Lite (Launched Mar 31)** — New budget tier for video generation API: $0.05/sec at 720p, $0.08/sec at 1080p. Text-to-video and image-to-video. 4/6/8-sec clips.
- **Should Tubee add this?** YES — cheapest production-grade video gen API available. Could power B-roll generation, transition fills, and AI scene creation features in Tubee.
- **How hard?** Easy — standard REST API via Gemini API. 3-5 days to integrate.
- **Cost?** ~$0.40-0.64 per 8-sec 1080p clip

**Google Gemini API: Flex & Priority Tiers (Apr 1)** — New inference tiers for cost vs latency optimization.
- **Should Tubee add this?** Worth monitoring. Flex tier could cut costs for batch/non-realtime processing.

### 2. VIDEO GENERATION API UPDATES

**Veo 3.1 Fast Price Cut (TODAY, Apr 7)** — Google committed to reducing Veo 3.1 Fast pricing today. This is expected to trigger competitive responses from Runway, Kling, and Luma on their API pricing.
- **Should Tubee add this?** YES — watch for the new pricing. If Veo 3.1 Fast drops below $0.15/sec at 1080p, it becomes viable for real-time preview generation in Tubee.
- **Action:** Monitor Google AI Studio pricing page today.

**Sora Shutdown Timeline** — Sora app dies April 26. API stays live until September 24, 2026. OpenAI redirecting compute to "world simulation for robotics."
- **Should Tubee use Sora?** NO — dead platform. Don't build on it. Migrate any Sora experiments to Veo or Kling.

**Google Vids + Veo 3.1 Free Tier** — Any Google account gets 10 free Veo 3.1 video generations/month (8-sec, 720p). AI Pro/Ultra subs get up to 1,000 clips + Lyria 3 music gen + AI avatars.
- **Competitive threat?** MODERATE — Google Vids targets casual creators, not pro editors. But the free tier sets user expectations that AI video gen should be cheap/free.

### 3. NEW AI VIDEO EDITING COMPETITORS

**Eluvio EVIE (Launched today, Apr 7)** — Frame-accurate AI editing platform debuting at NAB 2026. Multimodal content search, automatic highlights, short-form generation, vertical video from 16:9 sources, live AI motion analysis, and orchestration APIs supporting natural language prompts and agentic interfaces. 15+ built-in AI models including OpenCLIP, ImageBind, MediaPipe.
- **Should Tubee worry?** LOW for now — EVIE targets enterprise media (sports, studios, archives), not indie creators/freelancers. BUT their "natural language prompt → edit" and "agentic interface" approach is exactly what Tubee should be building.
- **Steal this idea:** Their vertical-from-landscape auto-reframe and natural language editing API are features Tubee needs.
- **How hard?** The individual features (auto-reframe, highlights) are medium. The orchestration layer is the hard part.

**Meta AI Ad Creative Tools ($10B run-rate)** — Meta's Advantage+ AI creative suite now used by 65% of advertisers. Features: catalog-to-video conversion, AI image-to-video (10% higher CTR), UGC-style AI avatar ads, multilingual voiceover.
- **Should Tubee add this?** Not directly, but this proves the market. Tubee could target the "help freelancers make Meta ad videos" niche as a positioning angle.

### 4. PRICE DROPS & FREE TIERS

| Service | Old Price | New Price | Notes |
|---------|-----------|-----------|-------|
| Veo 3.1 Lite (720p) | N/A (new) | $0.05/sec | Cheapest quality video gen API |
| Veo 3.1 Lite (1080p) | N/A (new) | $0.08/sec | Half the cost of Veo 3.1 Fast |
| Veo 3.1 Fast | TBD | Price cut TODAY | Watch for announcement |
| Google Vids (free tier) | N/A | 10 clips/mo free | Consumer-grade but sets expectations |

### 5. TRENDING TECHNIQUES

- **AI Avatar Ads** — Meta's UGC-style AI avatar videos with voiceovers are outperforming traditional ads by 10%+ CTR. Creators on TikTok/Reels are using similar AI avatar tools for "faceless" content.
- **Vertical Auto-Reframe** — Eluvio's 16:9→9:16 AI reframe is a hot feature. CapCut already has it; Tubee should too.
- **Natural Language Editing** — "Edit my video to remove awkward pauses" style prompting is becoming the expected UX.

### 6. OPEN SOURCE MODELS FOR LOCAL M4 MAC MINI

**Gemma 4 26B MoE (A4B)** — Only 4B active parameters during inference despite 26B total. Apache 2.0. Processes video/images natively. Should run well on M4 Mac Mini's unified memory.
- **Priority:** HIGH — This is Tubee's best bet for free, local video understanding.

**Gemma 4 E4B** — Tiny 4B effective model for on-device. Good for quick classification tasks.
- **Priority:** MEDIUM — Could handle lightweight tasks like shot detection, scene classification.

### TOP 3 ACTIONABLE FINDINGS

1. **🏆 Gemma 4 26B MoE → FREE local video understanding for Tubee** — Apache 2.0, runs on M4 Mac Mini, native video/image processing. Integrate this for scene analysis, content tagging, and intelligent edit suggestions WITHOUT API costs.

2. **💰 Veo 3.1 Lite API → Cheapest AI video generation ($0.05/sec)** — Add B-roll generation and AI scene creation to Tubee at half the cost of any competitor API. Price dropping further TODAY.

3. **🎯 Natural Language Editing UX (Eluvio EVIE pattern)** — The "prompt to edit" paradigm is going mainstream at NAB 2026. Tubee should make this the core UX: "remove awkward pauses," "add transition here," "make this vertical." First mover advantage for indie creators.

---

## 2026-04-09 (Thursday)

### 1. NEW AI MODELS (Last 7 Days)

**Microsoft MAI-Transcribe-1 / MAI-Voice-1 / MAI-Image-2 (announced Apr 2, available now in Foundry)** — Microsoft released new media models for transcription, voice generation, and image generation. Pricing published by Microsoft: MAI-Transcribe-1 at **$0.36/hour**, MAI-Voice-1 at **$22 per 1M characters**, MAI-Image-2 at **$5 per 1M text-input tokens + $33 per 1M image-output tokens**.
- **Should Tubee add this?** **YES, selectively.** MAI-Transcribe-1 is the most relevant for Tubee because transcription is a core editing primitive. Voice is useful later for voiceover generation. MAI-Image-2 matters more for thumbnail/storyboard tooling than core editing.
- **Why?** Cheap transcription and voice APIs can improve captions, rough cuts, searchable transcripts, and multilingual workflows.
- **How hard?** **Easy to medium.** Foundry integration plus eval against Whisper/Gemini/Assembly/OpenAI.
- **Cost?** **Low.** Especially attractive for transcript-heavy workflows.

### 2. VIDEO GENERATION API UPDATES

**No major verified Runway/Kling/Luma/Sora/Veo API launch was clearly documented in the sources I could verify this morning.**
- **Should Tubee add anything here?** **Not yet.** Keep existing watchlist, but do not ship against rumor-level changes.
- **Why?** The market is noisy, and Tubee should build on stable, documented APIs only.
- **How hard?** N/A
- **Cost?** N/A

**MAI-Image-2 commercial rollout is expanding** — Microsoft says MAI-Image-2 is rolling out on Copilot/Bing Image Creator and becoming broadly available in Foundry.
- **Should Tubee add this?** **Maybe, but later.** This is more useful for thumbnails, key art, shot boards, and promo asset generation than timeline editing.
- **Why?** Nice monetizable add-on, not core editor moat.
- **How hard?** **Easy.** Straight API integration.
- **Cost?** **Low to moderate.** Depends on image volume.

### 3. NEW VIDEO EDITING AI TOOLS / COMPETITORS

**No clearly verified major standalone AI video editor launch surfaced in the last 7 days from the sources I could confirm.**
- **Should Tubee react?** **Yes, by focusing on execution instead of chasing every noisy launch.**
- **Why?** This is a good sign. The market conversation is still centered on generation and media models, leaving room for Tubee to win on workflow and UX.
- **How hard?** N/A
- **Cost?** N/A

### 4. PRICE DROPS / FREE TIERS TO WATCH

**Microsoft MAI pricing is the clearest new low-cost signal this week**
- Transcription: **$0.36/hour**
- Voice generation: **$22 / 1M chars**
- Image generation: **$5 / 1M input tokens, $33 / 1M output tokens**
- **Should Tubee add this?** **YES for benchmarking immediately.**
- **Why?** Even if Tubee does not adopt MAI directly, these prices set a new bar for what “cheap enough to bundle” looks like.
- **How hard?** **Easy** to benchmark.
- **Cost?** **Low**.

**No major new free tier from core video generation leaders was verified this morning.**
- **Should Tubee change roadmap because of this?** **No.**
- **Why?** Focus on reliable margins, not waiting on competitors to get cheaper.
- **How hard?** N/A
- **Cost?** N/A

### 5. VIRAL EDITING TECHNIQUES TRENDING ON TIKTok / INSTAGRAM REELS

Based on CapCut’s 2026 trends page and Later’s weekly Reels roundup, the strongest currently visible patterns are:

**A. AI-synced templates / beat-matched edits**
- **Should Tubee add this?** **YES.**
- **Why?** This is the easiest “wow” feature for creators and short-form editors.
- **How hard?** **Medium.** Need beat detection + clip suggestion + one-tap template application.
- **Cost?** **Low to moderate** if done locally with standard audio analysis.

**B. Velocity edits (slow motion + speed ramps)**
- **Should Tubee add this?** **YES.**
- **Why?** Still one of the most reused attention hooks for reels and sports/lifestyle edits.
- **How hard?** **Easy.** Mostly product/UX work plus a few smart presets.
- **Cost?** **Low.**

**C. “Frozen in time” cutout overlay effect**
- **Should Tubee add this?** **YES, as a preset.**
- **Why?** Good viral-format feature that looks advanced but is template-friendly.
- **How hard?** **Medium.** Needs masking/cutout + motion sync.
- **Cost?** **Low to moderate.**

**D. Interactive / story-based short-form formats (“zoom in to get a sign”, choose-your-own-path style, day-in-my-life storytelling)**
- **Should Tubee add this?** **Maybe.**
- **Why?** Better as template packs than core engine work.
- **How hard?** **Easy.** Mostly packaging and UX.
- **Cost?** **Low.**

### 6. OPEN SOURCE MODELS THAT COULD RUN LOCALLY ON M4 MAC MINI FOR FREE

**Wan2.1 T2V-1.3B** — Hugging Face says it supports consumer-grade hardware; a Mac-focused repo reports it can run on a **32GB M4 Mac Mini** with MPS/offloading, generating short 480p clips locally.
- **Should Tubee add this?** **YES, for R&D. Not production yet.**
- **Why?** This is one of the clearest paths to free local video generation experiments on Apple Silicon.
- **How hard?** **Medium to hard.** You’ll need inference wrappers, job management, and patience because runtime is slow.
- **Cost?** **Free model cost**, but compute time is expensive in latency.

**Gemma 4 family remains worth tracking from the Apr 2 release window** — especially for local multimodal understanding on Mac hardware.
- **Should Tubee add this?** **YES.**
- **Why?** Better fit for scene understanding, transcript-aware editing, shot labeling, and prompt routing than raw video generation.
- **How hard?** **Medium.**
- **Cost?** **Free locally.**

### TOP 3 MOST ACTIONABLE FINDINGS

1. **Benchmark Microsoft MAI-Transcribe-1 immediately** — $0.36/hour is cheap enough that Tubee can likely bundle captions, transcript search, and rough-cut assistance without killing margins.

2. **Ship short-form preset features, not just “AI”** — beat-synced templates, speed ramps, and the “frozen in time” effect are concrete viral editing wins Tubee can productize fast.

3. **Prototype Wan2.1 locally on the M4 Mac Mini** — not for production yet, but as a free internal R&D path for Apple-Silicon-native video generation experiments.

---

## 2026-04-04 (Saturday)

### 1. NEW AI MODELS (Last 7 Days)

#### Google Gemma 4 — Released Apr 2, 2026
- **What:** Google's most capable open models. 4 sizes: E2B, E4B, 26B MoE, 31B Dense. Apache 2.0 license.
- **Key for Tubee:** Native vision + video + image processing. The 26B MoE model activates only 4B params at a time — runs on laptops/workstations including M4 Mac Mini. The 31B model is #3 open model globally on Arena AI.
- **Should Tubee add this?** YES — the 26B-A4B MoE model can run locally on M4 Mac Mini for free (no API costs). Can do OCR, chart understanding, visual tasks, code generation. Perfect for local video analysis/tagging pipeline.
- **How hard:** Medium. Need to set up Ollama/llama.cpp with Gemma 4 GGUF. ~1 week integration.
- **Cost:** FREE (Apache 2.0, runs locally)

#### Microsoft MAI Models — Released Apr 2, 2026
- **MAI-Transcribe-1:** Speech-to-text in 25 languages, 2.5x faster than Azure Fast. $0.36/hr.
- **MAI-Voice-1:** Text-to-speech, generates 60s audio in 1 second, custom voice creation. $22/1M characters.
- **MAI-Image-2:** Image/video generation model. $5/1M text tokens input, $33/1M image tokens output.
- **Should Tubee add this?** YES for MAI-Transcribe-1 — cheap, fast transcription is core for auto-subtitles. MAI-Voice-1 useful for AI voiceover features.
- **How hard:** Easy — standard API integration via Microsoft Foundry. ~3 days.
- **Cost:** Very competitive pricing, undercuts Google and OpenAI.

#### GLM-5V-Turbo (Z.AI)
- **What:** Vision model for coding/agent workflows. Native multimodal understanding of images, video, text. Good at UI interpretation and chart/document understanding.
- **Should Tubee add?** Monitor only. Less proven ecosystem than Gemma/Google.

### 2. VIDEO GENERATION API UPDATES

#### Google Veo 3.1 Lite — Launched Mar 31, 2026
- **What:** New low-cost tier of Veo video generation API. <50% cost of Veo 3.1 Fast tier. 720p/1080p, 4-8 second clips, text-to-video + image-to-video.
- **Why it matters:** Designed for high-volume pipelines (thousands of clips/day). Fast tier getting ANOTHER price cut on Apr 7.
- **Should Tubee add?** YES — this is the best-priced video generation API on the market now. With Sora dead, Veo is the clear leader.
- **How hard:** Medium. Gemini API integration, ~1 week.
- **Cost:** Sub-$0.375/sec (less than half of the original $0.75/sec Fast pricing)

#### OpenAI Sora — SHUT DOWN (Mar 24, 2026)
- **What:** OpenAI killed Sora. Was burning ~$15M/day, only made $2.1M lifetime revenue. Disney ended partnership.
- **Impact on Tubee:** Do NOT integrate Sora. Dead product. Veo + Kling + Runway are the survivors.

#### Google Vids + Veo 3.1 + Lyria Integration — Apr 2026
- **What:** Google Vids (their editing product) now integrates Veo 3.1 for video generation + Lyria for AI music. Directable AI avatars. Free tier: 10 vids/month. Pro: 50. Ultra: 1,000.
- **Should Tubee add?** COMPETITOR ALERT. Google Vids is a direct competitor to Tubee. Key differentiator for Tubee: focus on real footage editing for freelance videographers (not AI-generated content). But watch their API access patterns.

### 3. VIDEO EDITING AI COMPETITORS

- **Cutback Video, Selects, Descript** continue to be top competitors
- **DaVinci Resolve 20** Neural Engine expanding AI editing capabilities
- **Adobe Premiere Pro** — Generative Extend features deepening
- **Seedance** — emerging competitor with AI-first approach
- Google Vids integrating Veo directly = biggest new competitive threat this week

### 4. PRICE DROPS / FREE TIERS

| Service | Change | Date |
|---------|--------|------|
| Veo 3.1 Lite | <50% of Fast tier | Mar 31 |
| Veo 3.1 Fast | Further price cut | Apr 7 (upcoming) |
| Gemini API | New Flex tier (cost-optimized) + Priority tier | Apr 1 |
| MAI-Transcribe-1 | $0.36/hr (undercuts competitors) | Apr 2 |
| Gemma 4 | Free, Apache 2.0, runs locally | Apr 2 |

### 5. TRENDING EDITING TECHNIQUES

- AI avatar-based video content (Google Vids pushing this)
- Automated ad creative generation at scale (Veo Lite's target use case)
- Photo-to-video transformations (Kling pushing hard on this)

### 6. OPEN SOURCE MODELS FOR LOCAL M4 MAC MINI

| Model | Size | Can Run on M4 Mac Mini? | Use Case |
|-------|------|------------------------|----------|
| Gemma 4 26B-A4B MoE | 26B total, 4B active | ✅ YES easily | Vision, video analysis, code gen |
| Gemma 4 31B Dense | 31B | ✅ YES (tight fit, needs quantization) | Best quality local reasoning |
| Gemma 4 E4B | ~4B | ✅ YES trivially | Fast lightweight tasks |
| Wan 2.5 (Alibaba) | Varies | ⚠️ Needs testing | Open-source video generation |

---

### TOP 3 ACTIONABLE FINDINGS

1. **🏆 Gemma 4 26B MoE — FREE local AI for video analysis** → Run on M4 Mac Mini with zero API costs. Can analyze footage, tag scenes, read text in frames, understand visual content. Immediate competitive advantage.

2. **💰 Veo 3.1 Lite — Cheapest video generation API available** → With Sora dead, Google is aggressively pricing video gen. Lite is <$0.375/sec. Perfect for Tubee's AI video generation features. Apr 7 price cuts make it even better.

3. **🎤 MAI-Transcribe-1 — Fast cheap transcription for auto-subtitles** → 2.5x faster than Azure, $0.36/hr, 25 languages. Perfect for Tubee's auto-caption/subtitle pipeline. Easy API integration.

---

## 2026-04-10 (Friday)

### 1. NEW AI MODELS (Last 7 Days)

**Gemma 4 family (Apr 2, Hugging Face/Google ecosystem)** — Multimodal open-weight family with image, video, and for smaller variants audio input support. Sizes include E2B, E4B, 31B dense, and 26B A4B MoE. Apache 2.0. MLX and llama.cpp ecosystem support make this unusually practical on Apple Silicon.
- **Should Tubee add this?** YES, especially Gemma 4 E4B and 26B A4B.
- **Why?** Tubee needs cheap local intelligence for scene understanding, clip labeling, OCR-on-frames, rough edit suggestions, and search over footage.
- **How hard?** Medium. 1-2 weeks to test quantized local inference and build a vision analysis service around it.
- **Cost?** FREE model weights. Hardware cost only.

**Waypoint-1.5 (Apr 9, Hugging Face blog listing)** — New diffusion/world-model style release positioned around higher-fidelity interactive worlds on everyday GPUs.
- **Should Tubee add this?** NOT now.
- **Why?** Interesting for future camera-motion/world-consistency research, but not a direct editing feature for Tubee yet.
- **How hard?** Hard.
- **Cost?** Model may be free/open, but engineering cost is high.

### 2. VIDEO GENERATION API / PLATFORM UPDATES

**Seedance 2.0 is now showing up in production surfaces** — Replicate now advertises access to Seedance 2.0, and CapCut’s new Video Studio is reportedly built on Dreamina Seedance 2.0.
- **Should Tubee add this?** YES, at least benchmark it.
- **Why?** If ByteDance/CapCut is betting on it for creator workflows, Tubee should test it for prompt-to-shot generation, ad variants, and style-consistent short clips.
- **How hard?** Easy to medium if accessed via Replicate or another hosted provider.
- **Cost?** Variable, usage-based. Benchmark before committing.

**Replicate video pricing snapshot** — Wan 2.1 i2v 480p listed at **$0.09/sec** and 720p at **$0.25/sec** of output video.
- **Should Tubee add this?** MAYBE as fallback infrastructure, not core brand feature.
- **Why?** Useful for rapid prototyping and model switching without direct infra work.
- **How hard?** Easy.
- **Cost?** Moderate. Good for experiments, maybe expensive at scale.

### 3. NEW AI VIDEO EDITING COMPETITORS / COMPETITOR MOVES

**CapCut Video Studio (reported Mar 25, rolling out)** — Timeline-free AI-first workspace that scripts, storyboards, generates scenes, keeps characters/styles consistent, then hands off to traditional editing tools.
- **Should Tubee copy this direction?** YES.
- **Why?** This is the clearest competitive signal this week. The market is moving from “timeline editor with AI tools” to “AI director with manual polish.” Tubee should build toward prompt-driven edit orchestration.
- **How hard?** Hard as a full product, but medium for a narrow v1 like “turn this talking-head into 3 short variants.”
- **Cost?** Product cost is meaningful, but this is strategic, not optional.

**Luma’s site now pushes “creative agents” across video, image, audio, and text** — less about one-shot generation, more about end-to-end creative workflow.
- **Should Tubee add this?** YES, conceptually.
- **Why?** Tubee should not just be an editor. It should become an editing agent that keeps project context and executes multi-step transformations.
- **How hard?** Hard.
- **Cost?** Medium to high engineering cost, but strong product upside.

### 4. PRICE DROPS / FREE TIERS / COST SIGNALS

**ElevenLabs free plan remains strong for prototype voice features** — Free tier includes TTS, STT, sound effects, voice design, music, image/video surfaces, and 10k credits/month.
- **Should Tubee use this?** YES for prototyping voiceovers, dub tests, and caption-adjacent features.
- **Why?** Great way to validate features before locking into paid speech infra.
- **How hard?** Easy.
- **Cost?** Free to start, then low-end paid tiers from $5/month.

**Replicate stays valuable as a pay-as-you-go model router** — Strong if Tubee wants optionality instead of hard-wiring one video provider too early.
- **Should Tubee use this?** YES, for R&D.
- **Why?** Lets Tubee compare Seedance, Wan, Flux-class image tools, and more without custom hosting.
- **How hard?** Easy.
- **Cost?** Pay-per-use. Good for tests, watch margin at production scale.

### 5. VIRAL EDITING TECHNIQUES TRENDING ON TIKTOK / REELS

**Template-led edits are still dominant** — CapCut is explicitly leaning into one-click trending edits, advanced transitions, and AI enhancement templates for TikTok/Reels.
- **Should Tubee add this?** YES.
- **Why?** Tubee needs reusable “outcome templates,” not just tools. Example: podcast clip, realtor reel, cinematic product cut, church recap, talking-head ad.
- **How hard?** Medium.
- **Cost?** Low to medium. Mostly product/design and automation logic.

**Timeline-free creation is emerging as the viral-friendly workflow** — Fast storyboard-to-export flows are becoming the new expectation for short-form content.
- **Should Tubee add this?** YES.
- **Why?** Speed wins in Reels/TikTok. Tubee should reduce decision fatigue and get users to publish faster.
- **How hard?** Medium for guided workflows, hard for fully autonomous creation.
- **Cost?** Medium engineering cost.

### 6. OPEN SOURCE / LOCAL MODELS FOR M4 MAC MINI

**Gemma 4 E4B**
- **Should Tubee add this?** YES.
- **Why?** Best near-term local option for lightweight multimodal tasks on M4 Mac Mini.
- **How hard?** Easy to medium.
- **Cost?** FREE.

**Gemma 4 26B A4B**
- **Should Tubee add this?** YES.
- **Why?** Best bigger local model for richer reasoning over footage while still being feasible on Apple Silicon with quantization.
- **How hard?** Medium.
- **Cost?** FREE.

**Wan-class open video models via hosted/open ecosystems**
- **Should Tubee add this?** TEST, don’t commit.
- **Why?** Useful for low-cost experiments and potential local/self-hosted future paths, but quality/latency/product fit still need proof.
- **How hard?** Medium.
- **Cost?** Free weights in some cases, but compute is the real cost.

### TOP 3 ACTIONABLE FINDINGS

1. **Gemma 4 is still the biggest win** — Tubee should start a local Apple Silicon eval immediately. It is the cleanest path to free multimodal footage understanding on the M4 Mac Mini.

2. **CapCut’s timeline-free Video Studio is the clearest product threat** — Tubee should build a narrow AI-director workflow now, not later. Best first wedge: “turn this source clip into 3 polished short-form edits.”

3. **Use Replicate as Tubee’s fast R&D layer** — benchmark Seedance 2.0, Wan, and related video/image models there before committing to any one provider. It keeps experimentation cheap and fast.

