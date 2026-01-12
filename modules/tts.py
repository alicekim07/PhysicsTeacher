import os
from dotenv import load_dotenv
from openai import OpenAI

# 환경 설정
load_dotenv()
client = OpenAI()

SCRIPT_DIR = "scripts"
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

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

# 전체 스크립트 처리
def main():
    scripts = sorted(
        f for f in os.listdir(SCRIPT_DIR) if f.endswith(".txt")
    )

    for script in scripts:
        script_path = os.path.join(SCRIPT_DIR, script)
        audio_path = os.path.join(
            AUDIO_DIR,
            script.replace(".txt", ".mp3")
        )

        with open(script_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        print(f"[TTS] {script} -> {audio_path}")
        text_to_speech(text, audio_path)

    print("모든 음성 생성 완료")

if __name__ == "__main__":
    main()