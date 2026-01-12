from pdf2image import convert_from_path
import os

def pdf_to_images(pdf_path: str, out_dir: str, dpi: int = 300):
    pages  = convert_from_path(pdf_path, dpi=dpi)
    for i, page in enumerate(pages):
        page.save(f"{out_dir}/slide_{i+1:02d}.png", "PNG")

    print(f"[image] Saved {len(pages)} images to {out_dir}")

if __name__ == "__main__":
    # 테스트용 (실제 파이프라인은 run_all.py)
    pdf_to_images(
        pdf_path="data/pdf/example.pdf",
        out_dir = "data/outputs/examples/slides"
    )
