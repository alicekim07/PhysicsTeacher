from dotenv import load_dotenv 
load_dotenv()
from config import PPTX_DIR, PDF_DIR, METADATA_DIR, get_output_dirs
from modules.pptx import pptx_to_pdf, extract_notes_from_pptx
from modules.image import pdf_to_images
from modules.script import slides_to_scripts
from modules.context import prepare_professor_style
from modules.tts import scripts_to_audio
from modules.subtitle import audio_to_subs
from modules.video import make_video, concat_videos
from modules.metadata import load_slide_metadata

def ensure_pdf_from_pptx():
    for pptx in PPTX_DIR.glob("*.pptx"):
        pdf_name = pptx.stem
        pdf_path = PDF_DIR / f"{pdf_name}.pdf"

        # output dirs 확보
        dirs = get_output_dirs(pdf_name)
        notes_dir = dirs["notes"]
        notes_path = notes_dir / "raw_notes.txt"

        # 1. PPTX -> notes
        if not notes_path.exists():
            notes_text = extract_notes_from_pptx(str(pptx))
            with open(notes_path, "w", encoding="utf-8") as f:
                f.write(notes_text)

        # 2. PPTX -> PDF
        if not pdf_path.exists():
            pptx_to_pdf(
                pptx_path=str(pptx),
                pdf_dir=str(PDF_DIR)
            )

def process_pdf(pdf_path, professor_style):
    pdf_name = pdf_path.stem # 확장자 제거한 파일명
    dirs = get_output_dirs(pdf_name)

    # 1. Load slide metadata
    metadata_path = METADATA_DIR / f"{pdf_name}.yaml"
    if not metadata_path.exists():
        raise FileNotFoundError(f"No metadata file for lecture: {pdf_name}")
    
    slide_metadata_map = load_slide_metadata(metadata_path)

    # 1. PDF -> Slides
    pdf_to_images(
        pdf_path=str(pdf_path),
        out_dir=str(dirs["slides"])
    )
    
    # 2. Slides -> Scripts
    slides_to_scripts(
        slides_dir=str(dirs["slides"]),
        scripts_dir=str(dirs["scripts"]),
        professor_style=professor_style,
        slide_metadata_map=slide_metadata_map
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
        method="api",
        scripts_dir=str(dirs["scripts"])
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
        pdf_name = pdf.stem # 확장자 제거한 파일명
        dirs = get_output_dirs(pdf_name)

        professor_style = prepare_professor_style(
            dirs["notes"] / "raw_notes.txt"
        )

        process_pdf(pdf, professor_style)


if __name__ == "__main__":
    main()