# Tubee Next Actions — 2026-04-10

## Priority 1 — Gemma 4 local eval
Goal: test local Apple Silicon multimodal footage understanding on the Mac Mini for scene tagging, OCR, clip search, and edit suggestions.

Immediate tasks:
- Check whether Ollama or another local runner is already installed
- Identify best Gemma 4 variants for M4 Mac Mini
- Define a tiny benchmark using real Tubee footage tasks:
  - scene description
  - text/OCR from frame
  - best clip candidate suggestion
  - simple edit recommendation
- Record quality, latency, and zero-API-cost viability

## Priority 2 — Product response to CapCut Video Studio
Goal: narrow Tubee positioning toward AI-first first-cut generation.

Immediate tasks:
- Define one sharp product promise:
  - "Turn one source clip into 3 polished short-form edits"
- Audit current Tubee flow against that promise
- Identify which UI/features add friction vs support that promise

## Priority 3 — Replicate R&D benchmark
Goal: use Replicate as fast model-testing layer before deeper vendor integration.

Immediate tasks:
- Make shortlist of candidate models to benchmark
- Compare quality, speed, and cost
- Decide which models deserve native integration vs experiments only
