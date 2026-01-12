import os
from moviepy import ImageClip, AudioFileClip

SLIDE_DIR = "slides/highlighted"
AUDIO_DIR = "audio"
VIDEO_DIR = "video"

os.makedirs(VIDEO_DIR, exist_ok=True)

def make_even(n):
    return n if n % 2 == 0 else n - 1

def make_video(slide_path, audio_path, out_path):
    audio = AudioFileClip(audio_path)
    duration = audio.duration

    clip = ImageClip(slide_path)

    w, h = clip.size
    w2, h2 = make_even(w), make_even(h)
    if (w, h) != (w2, h2):
        clip = clip.resizedWh((w2, h2))

    clip = (
        clip
        .with_duration(duration)
        .with_audio(audio)
    )

    # 영상 저장
    clip.write_videofile(
        out_path,
        fps=24, # 정지 화면 이므로 낮아도 OK
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        ffmpeg_params=[
            "-pix_fmt", "yuv420p"
        ]
    )

def main():
    slides = sorted(f for f in os.listdir(SLIDE_DIR) if f.endswith(".png"))

    for slide in slides:
        slide_path = os.path.join(SLIDE_DIR, slide)
        audio_path = os.path.join(
            AUDIO_DIR,
            slide.replace(".png", ".mp3")
        )

        if not os.path.exists(audio_path):
            print(f"[SKIP] {slide} (audio 없음)")
            continue

        out_path = os.path.join(
            VIDEO_DIR,
            slide.replace(".png", ".mp4")
        )

        print(f"[VIDEO] {slide} + audio → {out_path}")
        make_video(slide_path, audio_path, out_path)

if __name__ == "__main__":
    main()