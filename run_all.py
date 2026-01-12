from config import PPTX_DIR, PDF_DIR, get_output_dirs
from dotenv import load_dotenv
from modules.pptx import pptx_to_pdf
from modules.image import pdf_to_images
from modules.script import slides_to_scripts

load_dotenv()

def ensure_pdf_from_pptx():
    for pptx in PPTX_DIR.glob("*.pptx"):
        pdf_path = PDF_DIR / (pptx.stem + ".pdf")

        if not pdf_path.exist():
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
        slide_dir=str(dirs["slides"]),
        scripts_dir=str(dirs["scripts"])
    )


def main():
    # 0단계
    ensure_pdf_from_pptx()

    # 1단계부터
    for pdf in PDF_DIR.glob("*.pdf"):
        process_pdf(pdf)


if __name__ == "__main__":
    main()