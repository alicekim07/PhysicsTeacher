from dotenv import load_dotenv 
load_dotenv()
from config import PPTX_DIR, PDF_DIR, get_output_dirs
from modules.pptx import pptx_to_pdf
from modules.image import pdf_to_images
from modules.script import slides_to_scripts
from modules.tts import scripts_to_audio
from modules.subtitle import audio_to_subs
from modules.video import make_video, concat_videos



def ensure_pdf_from_pptx():
    for pptx in PPTX_DIR.glob("*.pptx"):
        pdf_path = PDF_DIR / (pptx.stem + ".pdf")

        if not pdf_path.exists():
            pptx_to_pdf(
                pptx_path=str(pptx),
                pdf_dir=str(PDF_DIR)
            )

def process_pdf(pdf_path):
    pdf_name = pdf_path.stem # 확장자 제거한 파일명
    dirs = get_output_dirs(pdf_name)

    # 1. PDF -> Slides
    pdf_to_images(
        pdf_path=str(pdf_path),
        out_dir=str(dirs["slides"])
    )
    
    # 2. Slides -> Scripts
    slides_to_scripts(
        slides_dir=str(dirs["slides"]),
        scripts_dir=str(dirs["scripts"])
    )

    # 3. Scripts -> Audio
    scripts_to_audio(
        scripts_dir=str(dirs["scripts"]),
        audio_dir = str(dirs["audio"])
    )

    # 4. Audio -> Subs
    audio_to_subs(
        audio_dir=str(dirs["audio"]),
        subs_dir=str(dirs["subs"]),
        method="api"
    )

    # 5. Slids + Audio + Subs -> Video (슬라이드별)
    for slide in sorted(dirs["slides"].glob("*.png")):
        base = slide.stem
        audio = dirs["audio"] / f"{base}.mp3"
        subs = dirs["subs"] / f"{base}.srt"
        out = dirs["video"] / f"{base}.mp4"

        if not audio.exists():
            print(f"[SKIP] {base} (audio 없음)")
            continue

        make_video(
            slide_path=str(slide),
            audio_path=str(audio),
            subs_path=str(subs) if subs.exists() else None,
            out_path=str(out)
        )

    # 6. 슬라이드 클립 병합
    concat_videos(
        clips_dir=str(dirs["video"]),
        out_path=str(dirs["video"] / f"{pdf_name}_full.mp4")
    )

def main():
    # 0단계
    ensure_pdf_from_pptx()

    # 1단계부터
    for pdf in PDF_DIR.glob("*.pdf"):
        process_pdf(pdf)


if __name__ == "__main__":
    main()