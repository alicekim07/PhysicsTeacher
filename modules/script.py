import os
import base64
from dotenv import load_dotenv
from openai import OpenAI

client = OpenAI()

# 프롬프트
SYSTEM_PROMPT = """
너는 대학교 물리학 교수다.
칠판 앞에서 학생들에게 말로 설명하듯 강의한다.

이 텍스트는 사람이 읽는 문서가 아니라,
TTS로 음성 변환되어 강의 영상에서 재생된다.

매우 중요:
이 강의는 수학 기호를 전혀 모르는 학생에게 설명하는 상황이다.
수식, 기호, 약어가 하나라도 등장하면 실패다.

절대 사용 금지:
- 모든 수학 기호와 약어
- 알파벳으로 된 물리량 이름
- C, V, P, f 같은 문자 단독 사용
- 등호, 분수, 미분, 합 기호
- 괄호 안에 기호 설명

반드시 이렇게 말할 것:
- “일정한 부피에서 열을 얼마나 잘 저장하는지 나타내는 양”
- “압력을 일정하게 유지하면서 열을 넣어줄 때의 성질”
- “움직임의 자유로운 방향의 개수”
처럼 **완전한 문장으로 풀어서 설명**

강의 스타일 규칙:
- 정의부터 말하지 말고, 먼저 상황과 직관을 설명할 것
- 교재 문장처럼 딱딱하게 말하지 말 것
- “여기서 중요한 건”, “다시 말하면” 같은 말하기 표현을 사용할 것
- 설명 분량은 슬라이드의 정보량에 맞게 조절하되, 일반적인 강의에서 한 슬라이드를 설명하는 분량을 크게 벗어나지 않도록 할 것
- 슬라이드에 없는 내용을 추측하거나 확장하지 말 것

출력 전 마지막으로 스스로 검사해라:
- 수학 기호가 있는가?
- 알파벳 기호로 된 물리량이 있는가?
하나라도 있으면 다시 고쳐서 출력해라.

강의 영상용 슬라이드 스크립트이므로
'다음 시간에는', '다음 강의에서는' 같은
시간을 넘기는 표현은 절대 사용하지 말 것.

강의 중간 슬라이드에서는
문장의 시작에 '자,', '자 이제', '자 그럼' 같은
구어체 접속사를 절대 사용하지 말 것.
"""

USER_PROMPT = """
이 슬라이드를 참고해서,
학생들이 처음 듣는다고 가정하고
교수가 수업 시간에 말로 설명하는
강의 영상용 음성 스크립트를 작성해라.

중요:
기호나 수식을 쓰지 말고,
모든 개념을 말로만 설명해라.
"""

def encode_image_to_data_url(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

# 슬라이드 -> 스크립트
def generate_script(slide_path, previous_context, slide_index, total_slides):
    image_data_url = encode_image_to_data_url(slide_path)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    assistant_content = ""

    if slide_index == 0:
        assistant_content += (
            "이제 막 강의를 시작하는 첫 슬라이드다. "
            "자연스럽게 강의 도입을 해도 된다. "
            "마지막 문장은 문제를 제기하거나 관점을 소개하는 형태로 마무리하라.\n"
        )

    elif slide_index < total_slides - 1:
        assistant_content += """
        지금은 강의 중간이다.
        도입 멘트를 가능하면 사용하지 않고 바로 개념설명으로 들어갈 것.
        도입 멘트를 사용한다면 이번 슬라이드에서는 무엇을 설명하겠다는 표현을 쓸 것. 
        마무리는 다음 중 하나로 끝내라:
        - 이 슬라이드에서 가져가야 할 핵심 요약
        - 다음 슬라이드로 자연스럽게 이어지는 관점 전환
        - 학생이 생각해 볼 수 있는 질문 하나

        '다음 시간에는' 같은 표현은 절대 사용하지 말 것.
        """

    else:
        assistant_content += """
        지금은 강의의 마지막 슬라이드다.
        강의 시작 멘트와 시간 예고 표현은 사용하지 말 것.

        마무리는 반드시 다음 형태 중 하나로 하라:
        - 전체 내용을 한 번에 정리
        - 이 개념이 왜 중요한지 의미를 강조
        - 학생이 가져가야 할 핵심 메시지 한 문장

        강의를 끝낸다는 느낌의 자연스러운 정리만 허용된다.
        """

    if previous_context:
        assistant_content += f"\n지금까지 강의에서 이미 설명한 핵심 요약:\n{previous_context}\n"

    messages.append({
        "role": "assistant",
        "content": assistant_content
    })

    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": USER_PROMPT},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ],
    })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.4
    )

    return response.choices[0].message.content.strip()


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

def slides_to_scripts(slides_dir: str, scripts_dir: str):
    slides = sorted(f for f in os.listdir(slides_dir) if f.endswith(".png"))
    total_slides = len(slides)

    previous_context = ""

    for idx, slide in enumerate(slides):
        slide_path = os.path.join(slides_dir, slide)

        script_text = generate_script(
            slide_path,
            previous_context,
            slide_index=idx,
            total_slides=total_slides
        )

        script_name = slide.replace(".png", ".txt")
        script_path = os.path.join(scripts_dir, script_name)

        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script_text)

        previous_context = summarize_for_context(script_text)
        print(f"[script] {script_name} 생성 완료")