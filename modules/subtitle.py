import os
import re
from moviepy import AudioFileClip
from openai import OpenAI

client = OpenAI()

def split_sentence(text):
    """
    문장 단위로 분리
    (마침표, 물음표, 느낌표 기준)
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def sec_to_srt_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def make_srt_from_script(script_path: str, audio_path: str, out_path: str):
    # 스크립트 로드
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()

    sentences = split_sentence(text)

    # 음성 길이
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration

    # 문장 길이 기반 가중치
    lengths = [len(s) for s in sentences]
    total_len = sum(lengths)

    current_time = 0.0

    with open(out_path, "w", encoding="utf-8") as f:
        for idx, (sentence, length) in enumerate(zip(sentences, lengths), start=1):
            duration = total_duration * (length / total_len)
            start = current_time
            end = current_time + duration
            current_time = end

            f.write(f"{idx}\n")
            f.write(f"{sec_to_srt_time(start)} --> {sec_to_srt_time(end)}\n")
            f.write(sentence+ "\n\n")

def make_srt_api(audio_path, out_path):
    with open(audio_path, "rb") as f:
        srt_text = client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            response_format="srt",
            language="ko"
        )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(srt_text)


def audio_to_subs(
    audio_dir: str,
    subs_dir: str,
    method: str = "api", # "api" or "heuristic"
    scripts_dir: str | None = None
):
    for fname in sorted(os.listdir(audio_dir)):
        if not fname.endswith(".mp3"):
            continue

        base = fname.replace(".mp3", "")
        audio_path = os.path.join(audio_dir, fname)
        out_path = os.path.join(subs_dir, base + ".srt")

        if method == "api":
            make_srt_api(audio_path, out_path)

        elif method == "heuristic":
            if scripts_dir is None:
                raise ValueError("heuristic 방식은 scripts_dir가 필요합니다")
            
            script_path = os.path.join(scripts_dir, base + ".txt")
            make_srt_from_script(script_path, audio_path, out_path)

        else:
            raise ValueError(f"Unknown method: {method}")
        
        print(f"[subs] {out_path} 생성 완료")




def main():
    for fname in os.listdir(AUDIO_DIR):
        if not fname.endswith(".mp3"):
            continue

        base = fname.replace(".mp3", "")
        audio_path = os.path.join(AUDIO_DIR, base + ".mp3")
        out_path = os.path.join(SUB_DIR, base + ".srt")

        make_srt_api(audio_path, out_path)
        print(f"[OK] {out_path} 생성")

if __name__ == "__main__":
    main()