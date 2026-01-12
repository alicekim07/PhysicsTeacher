import os
import json
import subprocess

def build_drawbox_filters(highlight_json):
    filters = []

    with open(highlight_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    for h in data["highlights"]:
        x1, y1, x2, y2 = h["box"]
        start = h["start"]
        w = x2 - x1
        hgt = y2 - y1

        filters.append(
            f"drawbox="
            f"x={x1}:y={y1}:w={w}:h={hgt}:"
            f"color=yellow@0.35:t=fill:"
            f"enable='gte(t,{start})'"
        )

    return ",".join(filters)


def make_video(slide, audio, srt, highlight_json, out):
    print(">>> make_video CALLED")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    srt_abs = os.path.abspath(srt)
    fonts_abs = os.path.abspath("fonts")

    srt_escaped = srt_abs.replace(":", "\\:").replace(" ", "\\ ")
    fonts_escaped = fonts_abs.replace(":", "\\:").replace(" ", "\\ ")

    subtitle_filter = f"subtitles=filename={srt_escaped}:fontsdir={fonts_escaped}"
    if highlight_json:
        highlight_filter = build_drawbox_filters(highlight_json)

    # 🔥 핵심: subtitles + drawbox를 하나의 -vf로 합침
    vf = subtitle_filter
    if highlight_json:
        vf = f"{subtitle_filter},{highlight_filter}"

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", slide,
        "-i", audio,
        "-vf", vf,
        "-c:v", "h264_videotoolbox",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        out
    ]

    print("FFMPEG CMD:")
    print(" ".join(cmd))

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    make_video(
        slide="slides/png/slide_01.png",          # ✅ 원본 슬라이드
        audio="audio/slide_01.mp3",
        srt="subs/slide_01.srt",
        highlight_json="highlights/slide_01.json",
        out="video/slide_01_final.mp4"
    )
