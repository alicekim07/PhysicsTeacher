import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

PROF_STYLE_SYSTEM_PROMPT = """
    너는 대학교 교수이 강의 스타일을 분석하는 조교다.

    입력은 교수의 강의 메모이며, 이 메모는 강의 내용을 정리한 문서가 아니다.

    너의 역할은:
    - 교수의 말투, 설명 방식, 강의 태도를 분석하는 것
    - 교수의 설명 철학과 반복되는 패턴을 추출하는 것

    엄격한 규칙:
    - 물리 개념을 요약하거나 해석하지 말 것
    - 강의 내용을 정리하지 말 것
    - 슬라이드별 설명을 만들지 말 것
    - 오직 '설명 스타일'과 '설명 습관'만 추출할 것

    출력 규칙:
    - 출력은 반드시 **순수 JSON 객체 하나만** 반환해라
    - 출력의 첫 글자는 { 이고 마지막 글자는 } 여야 한다
    - JSON 앞뒤에 어떠한 설명, 인사, 문장도 붙이지 마라
    - 코드블록(''')을 사용하지 마라
"""

PROF_STYLE_USER_PROMPT = """
    다음은 교수의 강의 메모다.

    이 메모를 바탕으로 교수의 강의 스타일을 JSON으로 분석하라.
"""

def analyze_professor_notes(notes_text: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": PROF_STYLE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": PROF_STYLE_USER_PROMPT + "\n\n" + notes_text
            }
        ]
    )

    text = resp.choices[0].message.content.strip()

    # print(repr(text))
    return json.loads(text)

def prepare_professor_style(notes_path) -> dict:
    style_path = notes_path.parent / "professor_style.json"

    if style_path.exists():
        return json.loads(
            style_path.read_text(encoding="utf-8")
        )
    
    notes_text = notes_path.read_text(encoding="utf-8")
    professor_style = analyze_professor_notes(notes_text)

    style_path.write_text(
        json.dumps(professor_style, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return professor_style