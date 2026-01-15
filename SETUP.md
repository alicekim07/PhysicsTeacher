# SETUP

PHYSICSTEACHER 프로젝트 실행을 위한 환경 설정 가이드입니다.

---

## 1. Python 환경

- Python 3.9 이상을 권장합니다.
- 가상 환경 사용을 권장합니다.

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

## 2. 필수 라이브러리 설치

필요한 외부 라이브러리는 아래 파일에 정리되어 있습니다.
``` bash
pip install -r requirements.txt
```

## 3. 환경 변수 설정 (.env)

프로젝트 루트 디렉토리에 .env 파일을 생성합니다.
``` text
OPENAI_API_KEY=your_openai_api_key_here
```
.env 파일은 GitHub에 커밋하지 마세요.

## 4. 입력 파일 준비

변환할 강의 PPTX 파일을 아래 디렉토리에 넣습니다.
``` text
data/pptx/
``` 
## 5. 실행

환경 설정이 완료되면, 프로젝트 루트에서 다음 명령을 실행합니다.
``` bash
python run_all.py
```

실행 결과는 아래 디렉토리에 생성됩니다.
``` text
data/outputs/{lecture_name}/
``` 

## 6. 참고 사항

- 본 프로젝트는 외부 API(OpenAI)를 사용하므로 네트워크 연결이 필요합니다.
- API 사용량에 따라 비용이 발생할 수 있습니다.