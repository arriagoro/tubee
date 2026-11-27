#!/usr/bin/env python3
"""Render the Arias Organization Miami reel (1080x1920, 30fps) with ffmpeg."""
import subprocess, sys, os

S = "/tmp/claude-0/-home-user-tubee/36541372-250d-5ea2-9319-57103dd4c74e/scratchpad"
F = f"{S}/fonts"
OUT = sys.argv[1] if len(sys.argv) > 1 else f"{S}/reel_v1.mp4"

REAL = f"{S}/proxy/oct22_C0001_13tNUo.mp4"
G = lambda i: f"{S}/gen/broll_{i}.mp4"

# (source, source_in, timeline_start, timeline_end, is_real_footage)
CUTS = [
    (G(5), 0.0, 0.00, 3.07, False),   # neon Miami skyline
    (G(1), 0.0, 3.07, 5.06, False),   # supercar on Ocean Drive (approaching)
    (REAL, 1.0, 5.06, 7.06, True),    # Design District walk
    (G(3), 0.5, 7.06, 9.06, False),   # hand on the wheel
    (G(1), 2.9, 9.06, 11.05, False),  # supercar pulls up close
    (G(2), 0.3, 11.05, 13.05, False), # crew laughing
    (REAL, 5.0, 13.05, 15.07, True),  # Design District walk, part 2
    (G(4), 0.5, 15.07, 19.06, False), # rooftop team high-fives
]
END_START, END_LEN = 19.06, 6.0
TOTAL = END_START + END_LEN

# (text, start, end, size, y_center, style)
TEXT = [
    ("MIAMI, FLORIDA.", 0.30, 3.00, 150, 820, "pink"),
    ("NEW CITY.", 3.07, 6.95, 175, 760, "pink"),
    ("BIG ENERGY.", 4.06, 6.95, 175, 960, "cyan"),
    ("UNLIMITED", 7.06, 10.95, 170, 760, "pink"),
    ("OPPORTUNITY.", 7.55, 10.95, 150, 950, "cyan"),
    ("BUILT", 11.05, 14.95, 230, 740, "pink"),
    ("DIFFERENT.", 11.55, 14.95, 190, 960, "cyan"),
    ("ONE TEAM.", 15.07, 18.95, 175, 760, "pink"),
    ("ONE MISSION.", 16.56, 18.95, 165, 960, "cyan"),
]

GRADE_REAL = ("eq=contrast=1.28:saturation=1.55:gamma=0.95,"
              "colorbalance=rs=0.06:bs=-0.04:rh=0.05:bh=-0.03,curves=preset=increase_contrast")
GRADE_AI = "eq=contrast=1.06:saturation=1.12"

inputs, chains, labels = [], [], []
for k, (src, sin, a, b, real) in enumerate(CUTS):
    dur = b - a
    inputs += ["-ss", f"{sin}", "-t", f"{dur + 0.2}", "-i", src]
    grade = GRADE_REAL if real else GRADE_AI
    # slow punch-in: scale grows ~6% over the shot, centre-cropped back to 1080x1920
    pre = "crop=iw:ih*0.80:0:ih*0.20," if src == G(4) else ""  # drop ceiling strip on rooftop shot
    chains.append(
        f"[{k}:v]{pre}fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{grade},"
        f"scale=w='trunc(1080*(1+0.06*t/{dur:.2f})/2)*2':h=-2:eval=frame,crop=1080:1920,"
        f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[c{k}]")
    labels.append(f"[c{k}]")

# end card (sunset + lockup) held out to END_LEN
ek = len(CUTS)
inputs += ["-i", f"{S}/gen/endcard.mp4"]
chains.append(f"[{ek}:v]fps=30,tpad=stop_mode=clone:stop_duration=1.2,trim=duration={END_LEN},"
              f"setpts=PTS-STARTPTS,setsar=1,format=yuv420p[cend]")

chains.append("".join(labels) + f"concat=n={len(CUTS)}:v=1:a=0[body]")

# white flash on each cut for punch
flashes = "+".join(f"between(t,{a:.2f},{a + 0.07:.2f})" for _, _, a, _, _ in CUTS[1:])
draw = [f"[body]drawbox=x=0:y=0:w=iw:h=ih:color=white@0.55:t=fill:enable='{flashes}'"]

for txt, a, b, size, yc, style in TEXT:
    border, shadow = ("0xFF2BD6", "0x00F0FF") if style == "pink" else ("0x00C8FF", "0xFF2BD6")
    fs = (f"if(lt(t-{a},0.12),{size}*(0.5+5.5*max(0,t-{a})),"
          f"{size}*(1.16-0.16*min(1,(t-{a}-0.12)/0.12)))")
    t = txt.replace(",", "\\,").replace(":", "\\:")
    draw.append(
        f"drawtext=fontfile={F}/Anton.ttf:text='{t}':fontsize='{fs}':fontcolor=white:"
        f"borderw=8:bordercolor={border}:shadowx=10:shadowy=10:shadowcolor={shadow}:"
        f"x=(w-tw)/2:y={yc}-th/2:enable='between(t,{a},{b})'")
chains.append(",".join(draw) + "[bodyt]")
chains.append("[bodyt][cend]concat=n=2:v=1:a=0,fade=out:st=" + f"{TOTAL - 0.5:.2f}:d=0.5[v]")

mi = ek + 1
inputs += ["-i", f"{S}/gen/music.mp3"]
chains.append(f"[{mi}:a]atrim=0:{TOTAL:.2f},afade=t=out:st={TOTAL - 1.6:.2f}:d=1.6,"
              f"loudnorm=I=-14:TP=-1.0:LRA=11[a]")

cmd = (["ffmpeg", "-v", "error", "-y"] + inputs +
       ["-filter_complex", ";\n".join(chains), "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{TOTAL:.2f}", OUT])
subprocess.run(cmd, check=True)
print("wrote", OUT)
