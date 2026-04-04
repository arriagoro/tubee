"""
ai_editor.py — Claude API integration for Tubee
Takes scene list + beat timestamps + user prompt and asks Claude to make
intelligent editing decisions: which scenes to use, what order, what timing.
"""

import os
import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TODO: Set your Anthropic API key here, or set the ANTHROPIC_API_KEY env var.
# Get your key at: https://console.anthropic.com/
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", "")

# Model routing
# Primary: Kimi K2 Turbo (fast, smart, vision-capable, cheaper)
# Fallback: Claude Haiku (if Kimi fails)
# Premium: Claude Opus (for complex prompts)
KIMI_MODEL = "kimi-k2-turbo-preview"
CLAUDE_MODEL_FAST = os.environ.get("TUBEE_MODEL_FAST", "claude-haiku-4-5-20251001")
CLAUDE_MODEL_PREMIUM = os.environ.get("TUBEE_MODEL_PREMIUM", "claude-sonnet-4-6")

# Complexity keywords that trigger premium model routing
_COMPLEX_KEYWORDS = {
    "narrative", "story", "cinematic", "emotional", "dramatic",
    "documentary", "creative", "artistic", "mood", "atmosphere",
    "professional", "premium", "high quality", "best quality",
}


def smart_route_model(user_prompt: str, scene_count: int) -> str:
    """
    Route to Haiku (fast/cheap) or Opus (premium) based on prompt complexity.
    
    Uses Opus 4.6 when:
      - Prompt contains creative/complex keywords
      - Many scenes (>15) requiring nuanced selection
      - Prompt is long (>200 chars), suggesting detailed creative direction
    """
    prompt_lower = user_prompt.lower()
    
    # Check for complexity signals
    has_complex_keywords = any(kw in prompt_lower for kw in _COMPLEX_KEYWORDS)
    many_scenes = scene_count > 15
    detailed_prompt = len(user_prompt) > 200
    
    if has_complex_keywords or (many_scenes and detailed_prompt):
        logger.info(f"Smart routing → Opus 4.6 (complex edit detected)")
        return CLAUDE_MODEL_PREMIUM
    
    logger.info(f"Smart routing → Haiku (standard edit)")
    return CLAUDE_MODEL_FAST


def build_vision_edit_prompt(
    scenes: List[Dict[str, Any]],
    beat_data: Optional[Dict[str, Any]],
    user_prompt: str,
    target_duration: Optional[float] = None,
    frame_map: Optional[Dict[str, List[str]]] = None,
) -> str:
    """
    Build an edit prompt that includes visual context from extracted frames.
    Same structure as build_edit_prompt but prepends frame descriptions so
    Kimi knows WHAT it's looking at.

    Args:
        scenes: Scene list from scene_detect.
        beat_data: Beat data (or None).
        user_prompt: User's edit request.
        target_duration: Desired output duration.
        frame_map: Dict mapping video_path → [frame_path, ...] from extract_key_frames.

    Returns:
        Full prompt string with visual context header + edit instructions.
    """
    base_prompt = build_edit_prompt(scenes, beat_data, user_prompt, target_duration)

    if not frame_map:
        return base_prompt

    # Build a visual context header describing which frames come from where
    vision_header_lines = [
        "VISUAL ANALYSIS — FRAME REFERENCE",
        "=" * 50,
        "I'm sending you actual frames extracted from the raw footage.",
        "Use what you SEE in these frames to make smarter edit decisions.",
        "",
        "For each clip, I extracted frames at the start (10%), middle (50%), and end (90%).",
        "Look at the frames and identify:",
        "  • Which clips have the best energy, action, or emotion",
        "  • What the best visual moments are",
        "  • How to structure the narrative based on what you see",
        "  • Shot composition quality (framing, lighting, focus)",
        "  • Visual variety — avoid back-to-back clips that look the same",
        "",
        "Frame index:",
    ]

    frame_index = 1
    for video_path, frame_paths in frame_map.items():
        clip_name = Path(video_path).name
        for fp in frame_paths:
            fname = Path(fp).stem
            vision_header_lines.append(f"  Frame {frame_index}: from '{clip_name}' — {fname}")
            frame_index += 1

    vision_header_lines.append("")
    vision_header_lines.append(
        "Based on what you SEE in these frames AND the scene timing data below, "
        "make the best possible edit decisions. Prioritize visually striking moments."
    )
    vision_header_lines.append("=" * 50)
    vision_header_lines.append("")

    vision_header = "\n".join(vision_header_lines)
    return vision_header + "\n" + base_prompt


def build_edit_prompt(
    scenes: List[Dict[str, Any]],
    beat_data: Optional[Dict[str, Any]],
    user_prompt: str,
    target_duration: Optional[float] = None,
) -> str:
    """
    Build a structured prompt for Claude to make editing decisions.

    Args:
        scenes: List of scene dicts from scene_detect.py
        beat_data: Beat detection output from beat_sync.py (can be None)
        user_prompt: The user's description of what they want
        target_duration: Optional desired output duration in seconds

    Returns:
        Full prompt string to send to Claude.
    """
    total_raw_duration = sum(s["duration"] for s in scenes)

    # Compact scene format to save tokens — ~60% less than verbose format
    scene_summary = "\n".join([
        f"  S{s['scene_num']}: {s['start_time']:.1f}-{s['end_time']:.1f}s ({s['duration']:.1f}s)"
        for s in scenes
    ])

    beat_summary = "No music provided."
    if beat_data:
        beat_summary = (
            f"BPM: {beat_data['bpm']}\n"
            f"  Total music duration: {beat_data['total_duration']:.2f}s\n"
            f"  Beat timestamps (first 20): {beat_data['beats'][:20]}\n"
            f"  Downbeat timestamps (first 10): {beat_data['downbeats'][:10]}"
        )

    duration_note = ""
    if target_duration:
        duration_note = f"\nTarget output duration: {target_duration:.1f} seconds."
    elif beat_data:
        duration_note = f"\nTarget output duration: match music length ({beat_data['total_duration']:.1f}s)."

    prompt = f"""You are a professional video editor AI. Your job is to create an edit decision list (EDL) based on the raw footage scenes and the user's creative brief.

TRENDING STYLES (April 2026 — use these when the user asks for "viral", "trending", or "social media" edits):
- Fast Jump Cuts: Remove all dead air, cut every 1-3 seconds, keep energy high from frame 1
- Beat-Synced Cuts: Every major cut lands on a beat or downbeat — this is non-negotiable for music videos
- Kinetic Pacing: Start fast, breathe for 2-3 seconds mid-video, then accelerate to the end
- Hook First: The most visually striking scene goes in the first 1.5 seconds, not at the end
- Seamless Transitions: Prefer motion-matched cuts (whip pan → whip pan) over hard cuts when scenes have similar movement
- UGC-Style Authenticity: Slightly imperfect, handheld feel with jump cuts — 161% higher conversion for brands
- Micro-Cinematic: Short clips (15-30s) with cinematic color grading and shallow depth of field feel
- Anime/Stylized Color: Bold, saturated color grades inspired by the anime/Ghibli aesthetic trend
- Pattern Interrupts: Insert a 0.5-1s visual surprise (flash, zoom, reverse) every 5-7 seconds to reset attention

YOU ARE THE WORLD'S MOST AGGRESSIVE, INTELLIGENT VIDEO EDITOR. You edit like a combination of Cole Bennett, David Fincher, and the best TikTok editors in the world. Every edit you make is CINEMATIC, PUNCHY, and VIRAL. You never make boring edits. You never just trim one clip. You create STORIES from raw footage.

USER'S EDIT REQUEST:
"{user_prompt}"

RAW FOOTAGE SCENES (total: {total_raw_duration:.2f}s):
{scene_summary}

MUSIC ANALYSIS:
{beat_summary}
{duration_note}

CRITICAL RULES (follow these above everything else):
1. USE MULTIPLE CLIPS — you MUST use clips from DIFFERENT source scenes. Never just trim one long clip. A good edit uses 8-20+ cuts.
2. TRIM AGGRESSIVELY — take the BEST 1-3 seconds from each scene, not the full scene. Cut out boring parts.
3. REORDER creatively — don't just play clips in original order. Put the most exciting moment FIRST as a hook.
4. DURATION IS LAW — if the user says "20-30 seconds", total clip durations MUST add up to 20-30 seconds. COUNT YOUR CLIPS as you go.
5. SPREAD THE CLIPS — use clips from as many different source scenes as possible.
6. FAST PACING — unless user says otherwise, each clip should be 1-3 seconds max.
7. Align cut points to beat timestamps when music is provided.

INSTRUCTIONS:
1. Read the user's request carefully and identify: desired duration, style, mood.
2. Go through ALL available scenes and identify the BEST moments in each.
3. Select 8-20 clips from DIFFERENT scenes (not one long clip from one scene).
4. For each clip, set clip_start and clip_end to capture only the best 1-3 seconds of that scene.
5. Reorder clips for maximum impact — hook first, build energy, strong close.
6. Add up all clip durations — they MUST match the requested duration.
7. If no duration specified, aim for 20-30 seconds for social media content.

RESPOND WITH VALID JSON ONLY. No explanation, no markdown, just raw JSON in this exact format:
{{
  "edit_notes": "Brief explanation of your creative decisions",
  "estimated_output_duration": 90.5,
  "clips": [
    {{
      "clip_index": 0,
      "source_scene_num": 1,
      "clip_start": 0.0,
      "clip_end": 3.5,
      "duration": 3.5,
      "transition": "cut",
      "notes": "Opening shot — establishes the scene"
    }},
    ...
  ]
}}

TRANSITION OPTIONS: "cut", "dissolve", "fade_in", "fade_out"
clip_index must be sequential (0, 1, 2, ...).
clip_start and clip_end are timestamps within the SOURCE video file.
"""
    return prompt


def get_edit_decisions(
    scenes: List[Dict[str, Any]],
    beat_data: Optional[Dict[str, Any]],
    user_prompt: str,
    target_duration: Optional[float] = None,
    video_files: Optional[List[str]] = None,
    frame_analysis: bool = True,
) -> Dict[str, Any]:
    """
    Call Claude to get AI-driven editing decisions.

    Args:
        scenes: Scene list from scene_detect.py (merged across all video files).
        beat_data: Beat data from beat_sync.py (or None if no music).
        user_prompt: The user's edit request.
        target_duration: Optional desired output duration.
        video_files: List of source video file paths (for context).

    Returns:
        Dict with keys:
            - edit_notes (str): Claude's creative commentary
            - estimated_output_duration (float): Expected output duration
            - clips (List[Dict]): List of clip decisions

    Raises:
        ValueError: If API key is not set.
        RuntimeError: If Claude call fails or returns invalid JSON.
    """
    # Try Kimi K2 first (faster, cheaper, vision-capable)
    if KIMI_API_KEY:
        job_id_for_frames = None
        try:
            from openai import OpenAI as KimiClient
            from frame_extractor import extract_key_frames, frames_to_base64, cleanup_frames

            kimi = KimiClient(api_key=KIMI_API_KEY, base_url="https://api.moonshot.ai/v1")

            # --- Vision-enhanced path: extract frames and let Kimi SEE them ---
            frame_map = None
            all_frame_paths = []

            if video_files and frame_analysis:
                try:
                    import uuid as _uuid
                    job_id_for_frames = str(_uuid.uuid4())[:8]
                    frame_map = extract_key_frames(
                        video_files, max_frames_per_clip=3, job_id=job_id_for_frames,
                    )
                    # Flatten all frame paths for base64 encoding
                    for paths in frame_map.values():
                        all_frame_paths.extend(paths)
                    logger.info(f"Extracted {len(all_frame_paths)} frames for Kimi vision")
                except Exception as frame_err:
                    logger.warning(f"Frame extraction failed ({frame_err}), continuing without vision")
                    frame_map = None
                    all_frame_paths = []

            # Build prompt — vision-enhanced if we have frames, standard otherwise
            if frame_map and all_frame_paths:
                prompt = build_vision_edit_prompt(
                    scenes, beat_data, user_prompt, target_duration, frame_map,
                )
            else:
                prompt = build_edit_prompt(scenes, beat_data, user_prompt, target_duration)

            # Build message content — include frame images if available
            content = []
            if all_frame_paths:
                # Add frame images as base64 for Kimi to SEE
                frame_contents = frames_to_base64(all_frame_paths)
                content.extend(frame_contents)
                logger.info(f"Sending {len(frame_contents)} frame images to Kimi K2")

            content.append({"type": "text", "text": prompt})

            logger.info(f"Sending edit request to Kimi K2 ({KIMI_MODEL})...")
            kimi_response = kimi.chat.completions.create(
                model=KIMI_MODEL,
                messages=[{"role": "user", "content": content}],
                max_tokens=4096,
                temperature=0.3,
            )

            # Clean up frames
            if job_id_for_frames:
                cleanup_frames(job_id_for_frames)

            raw = kimi_response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                clips = result.get("clips", [])
                if clips:
                    vision_tag = " (with vision)" if all_frame_paths else ""
                    logger.info(
                        f"Kimi edit decisions{vision_tag}: {len(clips)} clips, "
                        f"~{result.get('estimated_output_duration', 0):.1f}s"
                    )
                    return result
        except Exception as e:
            logger.warning(f"Kimi failed ({e}), falling back to Claude")
            # Clean up frames on error too
            if job_id_for_frames:
                try:
                    from frame_extractor import cleanup_frames
                    cleanup_frames(job_id_for_frames)
                except Exception:
                    pass

    if not ANTHROPIC_API_KEY:
        logger.warning("No API key found — using rule-based fallback editor")
        return _rule_based_editor(scenes, beat_data, user_prompt, target_duration)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = build_edit_prompt(scenes, beat_data, user_prompt, target_duration)

        # Smart model routing based on prompt complexity and scene count
        selected_model = smart_route_model(user_prompt, len(scenes))

        logger.info(f"Sending edit request to Claude ({selected_model})...")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        response = client.messages.create(
            model=selected_model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        raw = response.content[0].text.strip()
        logger.debug(f"Claude raw response: {raw[:500]}...")

        # Parse JSON response
        try:
            decisions = json.loads(raw)
        except json.JSONDecodeError:
            # Try to extract JSON from response if it contains extra text
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                decisions = json.loads(match.group())
            else:
                raise RuntimeError(f"Claude returned non-JSON response: {raw[:200]}")

        # Validate structure
        if "clips" not in decisions:
            raise RuntimeError("Claude response missing 'clips' field")

        logger.info(
            f"Claude edit decisions: {len(decisions['clips'])} clips, "
            f"~{decisions.get('estimated_output_duration', '?')}s"
        )
        return decisions

    except ImportError:
        logger.warning("anthropic SDK not installed — using rule-based fallback")
        return _rule_based_editor(scenes, beat_data, user_prompt, target_duration)

    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        logger.warning("Falling back to rule-based editor")
        return _rule_based_editor(scenes, beat_data, user_prompt, target_duration)


def _rule_based_editor(
    scenes: List[Dict[str, Any]],
    beat_data: Optional[Dict[str, Any]],
    user_prompt: str,
    target_duration: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Rule-based fallback editor when Claude is unavailable.
    Uses simple heuristics: beat-aligned cuts, skips very short/long scenes.

    This is a real functional fallback — not just a stub.
    """
    logger.info("Using rule-based fallback editor")

    # Determine target duration
    if target_duration is None:
        if beat_data:
            target_duration = beat_data["total_duration"]
        else:
            target_duration = min(sum(s["duration"] for s in scenes), 120.0)

    # Determine cut points from beats or even spacing
    if beat_data and beat_data["beats"]:
        # Cut on downbeats
        cut_points = [t for t in beat_data["downbeats"] if t <= target_duration]
        if not cut_points:
            cut_points = beat_data["beats"][:int(target_duration / 2)]
    else:
        # Even 3-second cuts
        cut_points = [i * 3.0 for i in range(int(target_duration / 3) + 1)]

    # Filter scenes: skip very short scenes (<0.5s), prefer medium-length ones
    usable_scenes = [s for s in scenes if s["duration"] >= 0.5]
    if not usable_scenes:
        usable_scenes = scenes  # Use all if none pass filter

    # Build clips to fill the cut points
    clips = []
    scene_idx = 0
    total_so_far = 0.0

    for i in range(len(cut_points) - 1):
        if total_so_far >= target_duration:
            break

        clip_duration = cut_points[i + 1] - cut_points[i]
        if clip_duration <= 0:
            continue

        # Cycle through scenes
        scene = usable_scenes[scene_idx % len(usable_scenes)]
        scene_idx += 1

        # Clamp clip to scene bounds
        clip_start = scene["start_time"]
        clip_end = min(scene["start_time"] + clip_duration, scene["end_time"])

        # If scene is shorter than clip_duration, use the whole scene
        if clip_end <= clip_start:
            clip_end = scene["end_time"]

        actual_duration = clip_end - clip_start

        clips.append({
            "clip_index": len(clips),
            "source_scene_num": scene["scene_num"],
            "clip_start": round(clip_start, 4),
            "clip_end": round(clip_end, 4),
            "duration": round(actual_duration, 4),
            "transition": "cut",
            "notes": f"Rule-based: beat-aligned cut at {cut_points[i]:.2f}s",
        })

        total_so_far += actual_duration

    # If no clips were generated, use the first scene
    if not clips and scenes:
        s = scenes[0]
        clips = [{
            "clip_index": 0,
            "source_scene_num": s["scene_num"],
            "clip_start": s["start_time"],
            "clip_end": min(s["end_time"], s["start_time"] + 30.0),
            "duration": min(s["duration"], 30.0),
            "transition": "cut",
            "notes": "Fallback: single clip",
        }]

    return {
        "edit_notes": (
            f"Rule-based edit (no Claude API key). "
            f"Beat-aligned cuts, {len(clips)} clips, "
            f"targeting {target_duration:.1f}s. "
            f"User prompt: '{user_prompt}'"
        ),
        "estimated_output_duration": round(sum(c["duration"] for c in clips), 2),
        "clips": clips,
    }


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # Quick test with dummy data
    test_scenes = [
        {"scene_num": 1, "start_time": 0.0, "end_time": 5.0, "duration": 5.0,
         "start_frame": 0, "end_frame": 150},
        {"scene_num": 2, "start_time": 5.0, "end_time": 12.0, "duration": 7.0,
         "start_frame": 150, "end_frame": 360},
        {"scene_num": 3, "start_time": 12.0, "end_time": 20.0, "duration": 8.0,
         "start_frame": 360, "end_frame": 600},
    ]
    test_beats = {
        "bpm": 120.0,
        "beats": [0.5 * i for i in range(40)],
        "downbeats": [2.0 * i for i in range(10)],
        "total_duration": 20.0,
        "onset_times": [0.5 * i for i in range(40)],
    }
    test_prompt = "Make a fast-paced highlight reel with energy"

    result = get_edit_decisions(test_scenes, test_beats, test_prompt)
    print(json.dumps(result, indent=2))


# ---------------------------------------------------------------------------
# Kimi K2.5 Integration (Moonshot AI)
# OpenAI-compatible API — can see video frames AND make edit decisions
# ---------------------------------------------------------------------------

def get_edit_decisions_kimi(
    scenes: List[Dict[str, Any]],
    beat_data: Optional[Dict[str, Any]],
    user_prompt: str,
    target_duration: Optional[float] = None,
    video_files: Optional[List[str]] = None,
    frame_paths: Optional[List[str]] = None,  # actual video frames for visual analysis
) -> Dict[str, Any]:
    """
    Use Kimi K2.5 for edit decisions — it can ACTUALLY SEE video frames.
    Falls back to Claude if Kimi key not set.
    """
    import os, base64
    kimi_key = os.environ.get("KIMI_API_KEY")
    if not kimi_key:
        logger.info("KIMI_API_KEY not set, falling back to Claude")
        return get_edit_decisions(scenes, beat_data, user_prompt, target_duration, video_files)

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=kimi_key,
            base_url="https://api.moonshot.ai/v1"
        )

        # Build messages — include actual frame images if available
        messages = []
        content = []

        # Add frame images if provided (Kimi can SEE them)
        if frame_paths:
            content.append({"type": "text", "text": "Here are frames from the video footage I need you to edit:"})
            for frame_path in frame_paths[:20]:  # max 20 frames
                try:
                    with open(frame_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
                    })
                except Exception:
                    pass

        # Add the edit prompt
        edit_prompt = build_edit_prompt(scenes, beat_data, user_prompt, target_duration)
        content.append({"type": "text", "text": edit_prompt})
        messages.append({"role": "user", "content": content})

        response = client.chat.completions.create(
            model="kimi-k2-5",
            messages=messages,
            max_tokens=4096,
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()
        # Parse JSON response (same format as Claude)
        import json, re
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(raw)

    except Exception as e:
        logger.warning(f"Kimi edit failed: {e}, falling back to Claude")
        return get_edit_decisions(scenes, beat_data, user_prompt, target_duration, video_files)
