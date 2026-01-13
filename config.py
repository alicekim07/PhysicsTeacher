from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

DATA_DIR = PROJECT_ROOT / "data"

PPTX_DIR = DATA_DIR / "pptx"    # 원본 입력
PDF_DIR = DATA_DIR / "pdf"      # 중간 입력
OUTPUT_DIR = DATA_DIR / "outputs"

def get_output_dirs(pdf_name: str):
    base = OUTPUT_DIR / pdf_name

    dirs = {
        "base": base,
        "slides": base / "slides",
        "scripts": base / "scripts",
        "audio": base / "audio",
        "subs": base / "subs",
        "highlights": base / "highlights",
        "video": base / "video",
        "notes": base / "notes",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    return dirs