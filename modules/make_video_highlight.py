import os
import json
from moviepy import (
    ImageClip, AudioFileClip,
    CompositeVideoClip, ColorClip
)

SLIDE_DIR = "slides/png"
AUDIO_DIR = "audio"
HIGHLIGHT_DIR = "highlights"
VIDEO_DIR = "video"

os.makedirs(VIDEO_DIR, exist_ok=True)

def make_even(n):
    return n if n % 2 == 0 else n - 1

def highlight_clip(box, start, video_duration):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1

    return (
        ColorClip(size=(w, h), color=(255, 230, 150))
        .with_opacity(0.35)
        .with_position((x1, y1))
        .with_start(start)
        .with_duration(video_duration-start)
    )

def make_video(slide_path, audio_path, highlight_path, out_path):
    audio = AudioFileClip(audio_path)

    base = ImageClip(slide_path)
    w, h = base.size
    w, h = make_even(w), make_even(h)
    base = base.resized((w, h))

    base = base.with_duration(audio.duration).with_audio(audio)

    clips = [base]

    with open(highlight_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for hlt in data["highlights"]:
        clips.append(
            highlight_clip(
                hlt["box"],
                hlt["start"],
                audio.duration
            )
        )

    final = CompositeVideoClip(clips)

    final.write_videofile(
        out_path,
        fps=10,
        codec="libx264",
        audio_codec="aac",
        ffmpeg_params=["-pix_fmt", "yuv420p"]
    )

def main():
    slide = "slide_01.png"

    make_video(
        slide_path=os.path.join(SLIDE_DIR, slide),
        audio_path=os.path.join(AUDIO_DIR, "slide_01.mp3"),
        highlight_path=os.path.join(HIGHLIGHT_DIR, "slide_01.json"),
        out_path=os.path.join(VIDEO_DIR, "slide_01_highlight.mp4")
    )

if __name__ == "__main__":
    main()