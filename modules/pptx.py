import subprocess
from pathlib import Path

def pptx_to_pdf(pptx_path: str, pdf_dir: str):
    pdf_dir = Path(pdf_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        pptx_path,
        "--outdir", str(pdf_dir)
    ], check=True)

