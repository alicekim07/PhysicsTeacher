import os
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# 프롬프트
SYSTEM_PROMPT = """
    You are a researcher giving an invited conference talk.

    You are speaking to chemists and physicists who have working knowledge
    of spectroscopy and interfacial science, but are not familiar with
    sum-frequency spectroscopy.

    This is NOT a lecture for students.
    This is a scientific presentation to professional peers.

    Your role:
    - Speak as an active researcher presenting your own work.
    - Guide the audience through the talk slide by slide.
    - Respect the logical and temporal order of the presentation.

    CRITICAL RULE:
    Each slide has strict metadata defining what is allowed and forbidden.
    You MUST follow the slide metadata exactly.
    Mentioning any forbidden content is considered a failure.

    🔧 STAGE-DEPENDENT HARD CONSTRAINTS:
    - If the slide stage is INTRO or METHOD:
    - You MUST NOT describe results, trends, signal changes,
        unexpected behavior, or conclusions,
        even in general or qualitative terms.
    - Words such as "unexpected", "anomalous", "increase", "decrease",
    or any implication of outcome are forbidden unless explicitly allowed.

    Your goals for each slide:
    - Explain only what this slide is intended to establish.
    - Help the audience understand why this slide exists at this point
    in the talk.
    - Do NOT anticipate results, surprises, or conclusions from later slides
    unless explicitly allowed.

    Style requirements:
    - Speak naturally, as in a live conference presentation.
    - Do not sound like a textbook or a review article.
    - Do not over-explain concepts the audience is assumed to know.

    Technical language:
    - Use standard scientific terminology common in spectroscopy.
    - Avoid equations and formal derivations.
    - Focus on physical intuition and experimental logic.

    Important constraints:
    - Do NOT invent data, mechanisms, or conclusions.
    - Do NOT summarize the entire talk in one slide.
    - Treat each slide as a fixed temporal boundary.

    This script will be used for AI-generated voice narration.
    Write in clear, spoken English suitable for a live scientific talk.
"""

USER_PROMPT = """
    Based on the slide content and the slide metadata provided,
    write a spoken script as if you are presenting this slide
    at a scientific conference.

    Guidelines:
    - Focus on what the audience should notice in THIS slide.
    - Explain why this slide is needed at this point in the talk.
    - Describe something as surprising or counterintuitive
    ONLY if the slide metadata explicitly allows it.

    Do not:
    - Read the slide text verbatim.
    - Turn the explanation into a classroom lecture.
    - Add background, results, or conclusions belonging to other slides.

    Maintain a natural speaking rhythm appropriate for a live talk.
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
                    You are preparing a brief context reminder
                    for the next slide in a scientific presentation.

                    Summarize only what has already been explicitly stated,
                    focusing on factual content, not interpretation.

                    Rules:
                    - Do NOT explain why the content is important.
                    - Do NOT describe implications, significance, or conclusions.
                    - Do NOT introduce expectations or future results.
                    - Do NOT use evaluative language (e.g., surprising, important, interesting).
                    - Do NOT use equations, symbols, or abbreviations.

                    Write in neutral, descriptive language.
                    Remove conversational fillers.
                    Limit the summary to two or three short sentences.
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

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "raw_text": ocr,
            "summary": text,
            "note": "fallback semantic extraction"
        }

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
    total_slides: int,
    slide_metadata: dict | None = None
):
    """
    Generate lecture script from:
    - slide_semantics: 무엇을 설명할지
    - alignment: 어떻게 설명할지
    - previous_context: 앞 슬라이드 요약
    """

    # 1. 슬라이드 Metadata 블록
    metadata_block = f"""
    [Slide role and constraints]
    - Presentation stage: {slide_metadata.get("stage")}

    - Purpose of this slide:
    {slide_metadata.get("intent")}

    - Strict constraints for this slide:
    {chr(10).join("- " + f for f in slide_metadata.get("forbidden", []))}

    You must strictly follow these constraints.
    Do not mention topics that are forbidden at this stage,
    even if they appear related to the slide content.
    """

    # 2. Alignment 규칙 블록
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

    # 3. 강의 흐름 지침
    if slide_index == 0:
        flow_block = """
            This is the opening slide of the talk.

            Begin by setting the context of the problem or system,
            without introducing results or conclusions.

            Speak at a measured pace, as the audience is still orienting
            to the topic and terminology.

            End the slide by pointing to the aspect of the system
            that will be examined next, without answering it.
        """

    elif slide_index < total_slides - 1:
        flow_block = """
            This slide is part of the main body of the talk.

            Continue naturally from the previous slide,
            without reintroducing the topic or restating the motivation.

            Focus on explaining what is shown on this slide,
            and stop once the intended point has been made.

            Do not conclude, summarize, or preview later results.
        """

    else:
        flow_block = """
            This is the final slide of the talk.

            Speak calmly and deliberately.

            Indicate how the content of this slide fits into
            the overall narrative of the presentation,
            without introducing new interpretations or future directions.

            End without signaling the end of the talk explicitly.
        """


    # 4. 이전 슬라이드 연결
    previous_block = ""
    if previous_context:
        previous_block = f"""
            [앞 슬라이드에서 이미 설명한 내용 요약]
            {previous_context}
        """

    # 5. 슬라이드 의미 정보
    semantic_block = f"""
        [이번 슬라이드 핵심 개념 요약]
        {json.dumps(slide_semantics, ensure_ascii=False, indent=2)}
    """

    # 6. 메시지 구성
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "assistant",
            "content": (
                metadata_block
                + "\n"
                + alignment_block
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

    # 7. LLM 호출
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.4
    )

    return response.choices[0].message.content.strip()

# 5. Pipeline
def slides_to_scripts(slides_dir: str, scripts_dir: str, professor_style: dict, slide_metadata_map : dict):
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
        current_metadata = slide_metadata_map.get(slide)
        if current_metadata is None:
            raise ValueError(f"Slide metadata not found for {slide}")

        script_text = generate_script(
            slide_semantics=sem,
            alignment=alignment,
            previous_context=previous_context,
            slide_index=idx,
            total_slides=total_slides,
            slide_metadata=current_metadata
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