# Tubee AI Video Editing App — Research Log

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

