import os
from openai import OpenAI

client = OpenAI()

# TTS 설정
MODEL = "gpt-4o-mini-tts"
VOICE = "nova"

# 텍스트 -> 음성
def text_to_speech(text, out_path):
    with client.audio.speech.with_streaming_response.create(
        model=MODEL,
        voice=VOICE,
        input=text
    ) as response:
        response.stream_to_file(out_path)


def scripts_to_audio(scripts_dir:str, audio_dir:str):
    scripts = sorted(
        f for f in os.listdir(scripts_dir) if f.endswith(".txt")
    )

    for script in scripts:
        script_path = os.path.join(scripts_dir, script)
        audio_path = os.path.join(
            audio_dir,
            script.replace(".txt", ".mp3")
        )

        with open(script_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        print(f"[tts] {script} -> {audio_path}")
        text_to_speech(text, audio_path)

    print("[tts] 모든 음성 생성 완료")

