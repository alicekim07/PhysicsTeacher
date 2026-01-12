import os
from make_video_with_highlight_and_subs import make_video

SLIDE_DIR = "slides/png"
AUDIO_DIR = "audio"
SUB_DIR = "subs"
HIGHLIGHT_DIR = "highlights"
OUT_DIR = "video/clips"

os.makedirs(OUT_DIR, exist_ok=True)

slides = sorted(f for f in os.listdir(SLIDE_DIR) if f.endswith(".png"))

for slide in slides:
    name = slide.replace(".png", "")

    highlight_path = os.path.join("highlights", f"{name}.json")

    if not os.path.exists(highlight_path):
        highlight_path = None

    make_video(
        slide=os.path.join(SLIDE_DIR, slide),
        audio=os.path.join(AUDIO_DIR, f"{name}.mp3"),
        srt=os.path.join(SUB_DIR, f"{name}.srt"),
        highlight_json=highlight_path,
        out=os.path.join(OUT_DIR, f"{name}.mp4")
    )
