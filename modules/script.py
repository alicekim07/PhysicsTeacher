import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# 프롬프트
SYSTEM_PROMPT = """
    너는 대학교 물리학 교수다.
    칠판 앞에서 학생들에게 말로 설명하듯 강의한다.

    이 텍스트는 사람이 읽는 문서가 아니라,
    TTS로 음성 변환되어 강의 영상에서 재생된다.

    학생 수준:
    - 물리학 전공자이므로 개념적 사고는 가능하다
    - 그러나 수학 기호와 수식에 의존한 설명은 이해하지 못한다

    매우 중요:
    이 강의에서는 수학 기호를 전혀 사용하지 않는다.
    수식, 기호, 약어가 하나라도 등장하면 실패다.

    절대 사용 금지:
    - 모든 수학 기호와 약어
    - 알파벳으로 된 물리량 이름
    - C, V, P, f 같은 문자 단독 사용
    - 등호, 분수, 미분, 합 기호
    - 괄호 안에 기호 설명

    반드시 말로 풀어 설명할 것:
    - “일정한 부피에서 열을 얼마나 잘 저장하는지 나타내는 성질”
    - “압력을 일정하게 유지하면서 열을 넣어줄 때의 성질”
    - “움직임의 자유로운 방향의 개수”
    처럼 완전한 문장으로 설명하라.

    강의 스타일 규칙:
    - 정의부터 말하지 말고, 먼저 상황과 직관을 설명하라
    - 교재 문장처럼 딱딱하게 말하지 말라
    - 설명 중 최소 한 번은 교수 스스로의 판단이나 선택(왜 이 방식으로 설명하는지, 왜 이 개념이 중요한지)을 드러내라
    - 학생들이 흔히 헷갈리는 지점을 교수가 미리 짚어 주는 문장을 포함하라
    - 정리된 발표문이 아니라, 생각을 정리해 가며 설명하는 흐름을 유지하라
    - 한 슬라이드를 설명하는 분량을 넘기지 말 것
    - 슬라이드에 없는 내용을 추측하거나 확장하지 말 것

    출력 전 마지막으로 스스로 검사해라:
    - 수학 기호가 있는가?
    - 알파벳 기호로 된 물리량 표현이 있는가?
    하나라도 있으면 다시 고쳐서 출력해라.

    강의 영상용 슬라이드 스크립트이므로
    '다음 시간에는', '다음 강의에서는' 같은
    시간을 넘기는 표현은 절대 사용하지 말 것.

    강의 중간 슬라이드에서는
    문장의 시작에 '자,', '자 이제', '자 그럼' 같은
    구어체 접속사를 절대 사용하지 말 것.
"""

USER_PROMPT = """
    아래 제공된 정보와 지침을 바탕으로,
    교수가 실제 수업 시간에 말하는 것처럼
    강의 영상용 음성 스크립트를 작성하라.

    중요:
    - 기호나 수식을 사용하지 말 것
    - 모든 개념은 말로 풀어 설명할 것
    - 학생이 왜 이 개념을 배워야 하는지
    자연스럽게 느낄 수 있도록 설명할 것
"""

OCR_SYSTEM = """
    너는 대학교 강의 슬라이드에서 텍스트를 추출하는 도구다.
    너의 목표는 '보이는 글자'를 최대한 정확히 옮기는 것이다.

    규칙:
    - 절대 내용을 해석하거나 설명하지 말고, 보이는 텍스트만 추출해라.
    - 제목, 소제목, 본문, 불릿, 캡션을 구분해라.
    - 수식/기호가 있으면 그대로 문자열로 포함하되, 따로 equations 배열에도 넣어라.
    - 잘 안 보이는 경우 confidence를 낮게 주고, uncertain_tokens에 후보를 기록해라.
    - 출력은 반드시 JSON만.
"""

OCR_USER = """
    이 이미지에서 보이는 텍스트를 추출해 JSON으로 반환해라.
"""

SEMANTIC_SYSTEM_PROMPT = """
    너는 대학교 물리 강의 슬라이드를 해석하는 조교다.

    입력은 OCR로 추출된 슬라이드 텍스트와 수식 목록이다.

    너의 역할은:
    - 이 슬라이드에서 교수자가 전달하려는 핵심 개념을 추출하는 것
    - 교수의 말이나 설명 문장을 작성하지 않고, 교수자가 머리속에서 사용하는 개념적 구조만 정리하는 것

    엄격한 금지 규칙 :
    - 수학 기호, 기호 이름, 알파벳 물리량을 절대 사용하지 말 것
    - 계산 절차, 단계 나열, 공식 소개를 포함하지 말 것
    - "설명한다", "보여준다", "논의한다", "단계별로", "과정"과 같은 설명형 동사를 사용하지 말 것
    - 교과서 요약처럼 보이는 서술을 하지 말 것
    
    출력 내용 지침:
    - 핵심 개념 하나를 중심 개념으로 제시할 것
    - 그 개념을 이해하기 위해 필요한 개념적 관계들을 여러 개의 **개념 포인트**로 나누어 정리할 것
    - 각 개념 포인트는 '무엇과 무엇이 어떤 관계에 있는가'를 드러내는 개념 수준의 진술이어야 한다.
    - 말하듯 설명하지 말고, 개념 지도처럼 정리할 것

    출력 형식 규칙 (매우 중요):
    - 출력은 반드시 **순수 JSON 객체 하나만** 반환해라
    - 출력의 첫 글자는 { 이고 마지막 글자는 } 여야 한다
    - JSON 앞뒤에 어떠한 설명, 인사, 문장도 붙이지 마라
    - 코드블록(''')을 사용하지 마라
"""

SEMANTIC_USER_PROMPT = """
    다음은 한 장의 대학교 물리학 강의 슬라이드에서 OCR로 추출된 정보다.

    이 슬라이드에서 교수가 학생에게 전달하려는 핵심 개념과 그 개념을 구성하는 개념적 관계를 JSON으로 정리해라.
"""

ALIGN_SYSTEM_PROMPT = """
    너는 강의 스크립트를 작성하는 역할이 아니다.

    너의 역할은:
    - 슬라이드의 핵심 개념(WHAT)과
    - 교수의 강의 스타일(HOW)을 참고하여
    - 스크립트 생성기가 따라야 할 '설명 지침'을 만드는 것이다.

    중요 규칙:
    - 실제 강의 문장이나 설명 문단을 절대 작성하지 마라
    - 교재처럼 서술하지 마라
    - 새로운 물리 개념을 추가하지 마라
    - 슬라이드에 없는 내용을 확장하지 마라

    출력 형식 규칙 (매우 중요):
    - 출력은 반드시 **순수 JSON 객체 하나만** 반환해라
    - 출력의 첫 글자는 { 이고 마지막 글자는 } 여야 한다
    - JSON 앞뒤에 어떠한 설명, 인사, 문장도 붙이지 마라
    - 코드블록(''')을 사용하지 마라
    - JSON 구조는 반드시 아래 형식을 따를 것

    {
        "instruction": "이 슬라이드를 설명할 때의 전체 방향 한 문장",
        "emphasis":  ["반드시 강조해야 할 개념 포인트들"],
        "avoid": ["설명에서 피해야 할 방식이나 표현들"]
    }
"""

ALIGN_USER_PROMPT = """
    다음은 한 장의 강의 슬라이드에 대한 정보다.

    - slide_semantics: 이 슬라이드에서 무엇을 설명해야 하는지 정리된 정보
    - professor_style: 교수의 강의 스타일 요약

    이 정보를 바탕으로, 스크립트 생성기가 따라야 할 설명 지침을 만들어라.
"""

# Helper 함수
def encode_image_to_data_url(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def _debug_print_json(obj, max_len=5000):
    import json
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    print(s[:max_len] + ("..." if len(s) > max_len else ""))

def summarize_for_context(script_text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                다음 강의 발화를 다음 슬라이드에서 이어서 설명하기 위해,
                이미 설명한 핵심만 두세 문장으로 요약하라.

                규칙:
                - 수학 기호, 알파벳 물리량, 약어 사용 금지
                - 말하기용 접속사 제거 ('자', '이제', '먼저' 등)
                - 내용 정보만 중립적으로 요약할 것
                - 두세 문장 이내로 요약할 것
                """

            },
            {
                "role": "user",
                "content": script_text
            }
        ],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

# 1. OCR 추출
def extract_text_from_image(slide_path: str, model: str = "gpt-4o", temperature: float = 0.0) -> dict:
    """
    Slide image -> structured OCR-like text extraction
    Returns dict with fields:
    - title: str
    - headings: list[str]
    - bullets: list[str]
    - body: str
    - captions: list[str]
    - equations: list[str]
    - confidence: float (0~1)
    - uncertain_tokens: list[str]
    """
    image_data_url = encode_image_to_data_url(slide_path)

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": OCR_SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": OCR_USER},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ]}
        ],
    )

    text = resp.choices[0].message.content.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 모델이 JSON 밖 텍스트를 섞으면, 최소 복구 시도
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(text[start:end+1])
        else:
            raise ValueError("OCR output is not valid JSON")
        
    return data

# 2. Semantic Extractor Agent 추가
def extract_slide_semantics(ocr: dict) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": SEMANTIC_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    SEMANTIC_USER_PROMPT
                    + "\n\n[OCR RESULT]\n"
                    + json.dumps(ocr, ensure_ascii=False, indent=2)
                )
            }
        ]
    )

    text = resp.choices[0].message.content.strip()
    return json.loads(text)

# 3. Context Alignment Agent
def align_contexts(slide_semantics: dict, professor_style: dict) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": ALIGN_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    ALIGN_USER_PROMPT
                    + "\n\n"
                    + json.dumps(
                        {
                            "slide_semantics": slide_semantics,
                            "professor_style": professor_style
                        },
                        ensure_ascii=False,
                        indent=2
                    )
                )
            }
        ]
    )

    text = resp.choices[0].message.content.strip()
    return json.loads(text)

# 4. Script Generator
def generate_script(
    slide_semantics: dict,
    alignment: dict,
    previous_context: str,
    slide_index: int,
    total_slides: int
):
    """
    Generate lecture script from:
    - slide_semantics: 무엇을 설명할지
    - alignment: 어떻게 설명할지
    - previous_context: 앞 슬라이드 요약
    """

    # 1. Alignment 규칙 블록
    alignment_block = f"""
    [설명 지침]
    - 전체 설명 방향
    {alignment.get("instruction", "")}

    - 반드시 강조할 개념
    {chr(10).join("- " + e for e in alignment.get("emphasis", []))}

    - 반드시 피할 설명 방식:
    {chr(10).join("- " + a for a in alignment.get("avoid", []))}

    위 지침을 반드시 따를 것.
    """

    # 2. 강의 흐름 지침
    if slide_index == 0:
        flow_block = """
            이제 막 강의를 시작하는 첫 슬라이드다.
            
            자연스럽게 상황이나 문제의 맥락부터 꺼내라.
            오늘 다룰 개념이 왜 필요한지 직관적으로 느끼게 하라.

            마지막 문장은
            해답을 주기보다는
            생각해볼 관점 하나를 던지는 정도로 끝내라
    
        """

    elif slide_index < total_slides - 1:
        flow_block = """
            지금은 강의의 중간이다.

            도입 멘트 없이
            이전 설명에서 자연스럽게 이어서
            개념 설명을 계속하라.

            이 슬라이드는 강의 흐름의 일부이므로
            정의, 요약, 평가, 예고로 끝내지 말 것.

            설명이 이어지다가
            개념이 충분히 전달된 시점에서
            자연스럽게 멈춰라.
        """

    else:
        flow_block = """
            지금은 강의의 마지막 슬라이드다.

            강의를 끝낸다는 표현이나 시간 흐름을 언급하는 말은 사용하지 말 것.

            지금까지 설명한 개념이 전체 흐름에서 어떤 위치를 차지하는지만 짚어라.

            새로운 동기 부여나 예고 없이, 의미가 남는 한두 문장으로 조용히 설명을 마무리하라.
        """


    # 3. 이전 슬라이드 연결
    previous_block = ""
    if previous_context:
        previous_block = f"""
            [앞 슬라이드에서 이미 설명한 내용 요약]
            {previous_context}
        """

    # 4. 슬라이드 의미 정보
    semantic_block = f"""
        [이번 슬라이드 핵심 개념 요약]
        {json.dumps(slide_semantics, ensure_ascii=False, indent=2)}
    """

    # 5. 메시지 구성
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "assistant",
            "content": (
                alignment_block
                + "\n"
                + flow_block
                + "\n"
                + previous_block
            )
        },
        {
            "role": "user",
            "content": (
                USER_PROMPT
                + "\n\n"
                + semantic_block
            )
        }
    ]

    # 6. LLM 호출
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.4
    )

    return response.choices[0].message.content.strip()

# 5. Pipeline
def slides_to_scripts(slides_dir: str, scripts_dir: str, professor_style: dict):
    slides = sorted(f for f in os.listdir(slides_dir) if f.endswith(".png"))
    total_slides = len(slides)

    previous_context = ""

    for idx, slide in enumerate(slides):
        slide_path = os.path.join(slides_dir, slide)

        # 1) OCR
        ocr = extract_text_from_image(slide_path)

        # 2) Semantics
        sem = extract_slide_semantics(ocr)

        # 3) Alignment (sem + professor_style)
        alignment = align_contexts(sem, professor_style)

        # 4) Script
        script_text = generate_script(
            slide_semantics=sem,
            alignment=alignment,
            previous_context=previous_context,
            slide_index=idx,
            total_slides=total_slides
        )

        # 5) Save script
        script_name = slide.replace(".png", ".txt")
        script_path = os.path.join(scripts_dir, script_name)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_text)

        previous_context = summarize_for_context(script_text)
        print(f"[script] {script_name} 생성 완료")

if __name__ == "__main__":
    test_slide_path = "../slide_09.png"

    professor_style = {"tone": "casual and enthusiastic", "explanation_style": "informal", "engagement": "uses humor and enthusiasm to engage students", "repetition": "repeats phrases to emphasize enjoyment", "language": "uses simple and relatable language"}

    print("\n=== [OCR] ===")
    ocr = extract_text_from_image(test_slide_path)
    _debug_print_json(ocr, max_len=2000)

    print("\n=== [SEMANTIC] ===")
    sem = extract_slide_semantics(ocr)
    _debug_print_json(sem, max_len=2000)

    print("\n=== [ALIGNMENT] ===")
    alignment = align_contexts(sem, professor_style)
    _debug_print_json(alignment, max_len=2000)

    print("\n=== [SCRIPT] ===")
    script = generate_script(
        slide_semantics=sem,
        alignment=alignment,
        previous_context="", # 첫 슬라이드라고 가정
        slide_index=0,
        total_slides=10
    )
    print(script)