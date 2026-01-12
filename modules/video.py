import os
import subprocess
from pathlib import Path

def make_video(
    slide_path: str,
    audio_path: str,
    out_path: str,
    subs_path: str | None = None,
    fonts_dirs: str = "fonts"
):
    os.makedirs(os.path.dirname(out_path), exist_ok = True)

    vf = None

    if subs_path:
        srt_abs = os.path.abspath(subs_path)
        fonts_abs = os.path.abspath(fonts_dirs)

        srt_escaped = srt_abs.replace(":", "\\:").replace(" ", "\\ ")
        fonts_escaped = fonts_abs.replace(":", "\\:").replace(" ", "\\ ")

        vf = f"subtitles=filename={srt_escaped}:fontsdir={fonts_escaped}"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", slide_path,
            "-i", audio_path,
        ]

        if vf:
            cmd += ["-vf", vf]

        cmd += [
            "-c:v", "h264_videotoolbox",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            out_path
        ]

        subprocess.run(cmd, check=True)

def concat_videos(
    clips_dir: str,
    out_path: str,
    prefix: str = "slide_"
):
    clips_dir = Path(clips_dir)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    clips = sorted(
        p for p in clips_dir.iterdir()
        if p.name.startswith(prefix) and p.suffix == ".mp4"
    )

    if not clips:
        print("[WARN] 병합할 클립이 없습니다.")
        return
    
    concat_list = clips_dir / "concat_list.txt"

    with open(concat_list, "w", encoding="utf-8") as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(out_path)
        ],
        check=True
    )

    concat_list.unlink() # 임시 파일 제거
    print(f"[OK] {out_path} 생성 완료")