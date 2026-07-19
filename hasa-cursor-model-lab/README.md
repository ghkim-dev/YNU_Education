# HASA × Cursor 로컬 실습 프로젝트

이 프로젝트는 HASA의 OpenAI 호환 API를 Cursor에서 직접 실행해 보도록 만든 실습 묶음입니다.

## 빠른 시작

    # Windows PowerShell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Copy-Item .env.example .env

.env에 발급받은 API 키를 넣은 뒤 아래 순서로 실행합니다.

    python 00_env_check.py
    python 01_chat.py "생성형 AI API를 처음 쓰는 학생에게 3문장으로 설명해줘."
    python 02_stream_chat.py

## 실습 파일 순서

| 파일 | 실습 주제 |
|---|---|
| 00_env_check.py | 내 키로 접근 가능한 모델 확인 |
| 01_chat.py | 단일 채팅 API 호출 |
| 02_stream_chat.py | 스트리밍 응답 |
| 03_compare_models.py | 같은 질문을 여러 모델로 비교 |
| 04_vision.py | 이미지 설명·문서 읽기 |
| 05_embeddings.py | 텍스트 임베딩과 의미 유사도 |
| 06_rerank.py | 질의-문서 재정렬 |
| 07_rag.py | 로컬 파일 기반 간단 RAG |
| 08_transcribe.py | Whisper 음성 전사 |
| 09_web_app.py | 브라우저에서 쓰는 간단한 채팅 앱 |

HASA_Cursor_실습교안.md를 먼저 읽고, 위 순서대로 실행하세요.

