import os
import json
from PIL import Image, ImageDraw

# 경로 설정
SLIDE_DIR = "slides/png"
HIGHLIGHT_DIR = "highlights"
OUT_DIR = "slides/highlighted"

os.makedirs(OUT_DIR, exist_ok=True)

# 하이라이트 색상 설정
HIGHLIGHT_COLOR = (255, 230, 150, 80) # 연한 노랑 + 투명도 (RGBA)
BORDER_COLOR = (255, 180, 60, 200) # 테두리
BORDER_WIDTH = 4

# 하이라이트 적용 함수
def apply_highlight(slide_path, highlight_json_path, out_path):
    # 이미지 열기 (RGBA로)
    img = Image.open(slide_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # 하이라이트 정보 로드
    with open(highlight_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for h in data["highlights"]:
        x1, y1, x2, y2 = h["box"]

        # 반투명 박스
        draw.rectangle(
            [x1, y1, x2, y2],
            fill=HIGHLIGHT_COLOR
        )

        # 테두리
        draw.rectangle(
            [x1, y1, x2, y2],
            outline=BORDER_COLOR,
            width=BORDER_WIDTH
        )

        # 원본 + 오버레이 합성
        result = Image.alpha_composite(img, overlay)

        # 저장 (PNG)
        result.save(out_path)


def main():
    slides = sorted(f for f in os.listdir(SLIDE_DIR) if f.endswith(".png"))

    for slide in slides:
        slide_path = os.path.join(SLIDE_DIR, slide)
        highlight_path = os.path.join(
            HIGHLIGHT_DIR,
            slide.replace(".png", ".json")
        )

        # 하이라이트 파일이 없으면 건너뜀
        if not os.path.exists(highlight_path):
            print(f"[SKIP] {slide} (highlight 없음)")
            continue

        out_path = os.path.join(OUT_DIR, slide)
        apply_highlight(slide_path, highlight_path, out_path)

        print(f"[OK] {out_path}")

if __name__ == "__main__":
    main()