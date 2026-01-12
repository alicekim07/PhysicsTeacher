import os
import subprocess

VIDEO_DIR = "./video/clips"
OUT = "video/finals/lecture_full.mp4"

clips = sorted(
    f for f in os.listdir(VIDEO_DIR) if f.startswith("slide_")
)


with open("concat_list.txt", "w") as f:
    for clip in clips:
        f.write(f"file '{os.path.join(VIDEO_DIR, clip)}'\n")

subprocess.run([
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0",
    "-i", "concat_list.txt",
    "-c", "copy",
    OUT
], check=True)

print("[OK] lecture_full.mp4 생성 완료")
