"""
ai_editor.py — Claude API integration for Tubee
Takes scene list + beat timestamps + user prompt and asks Claude to make
intelligent editing decisions: which scenes to use, what order, what timing.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TODO: Set your Anthropic API key here, or set the ANTHROPIC_API_KEY env var.
# Get your key at: https://console.anthropic.com/
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Model routing — use cheaper models to save money
# claude-haiku-4-5 is ~10x cheaper than Sonnet and great for structured editing decisions
# Switch to "claude-sonnet-4-6" only for complex creative prompts
CLAUDE_MODEL = os.environ.get("TUBEE_MODEL", "claude-haiku-4-5-20251001")


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

USER'S EDIT REQUEST:
"{user_prompt}"

RAW FOOTAGE SCENES (total: {total_raw_duration:.2f}s):
{scene_summary}

MUSIC ANALYSIS:
{beat_summary}
{duration_note}

INSTRUCTIONS:
1. Analyze the scenes and music (if provided).
2. Select which scenes to include — you can skip boring/redundant ones.
3. Decide the ORDER of scenes (can be different from original).
4. For each selected scene, decide the CLIP IN/OUT points (you can use just a portion of each scene).
5. Align cut points to beat timestamps when music is provided.
6. Keep the overall pace and energy appropriate to the user's request.
7. Total output should be engaging — usually 30 seconds to 3 minutes depending on content.

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
    if not ANTHROPIC_API_KEY:
        logger.warning("No Anthropic API key found — using rule-based fallback editor")
        return _rule_based_editor(scenes, beat_data, user_prompt, target_duration)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = build_edit_prompt(scenes, beat_data, user_prompt, target_duration)

        logger.info(f"Sending edit request to Claude ({CLAUDE_MODEL})...")
        logger.debug(f"Prompt length: {len(prompt)} chars")

        response = client.messages.create(
            model=CLAUDE_MODEL,
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
