# BioLens · HASA 의생명 문서 도우미

의생명공학과 학생이 **HASA Open AI Service Hub** API로 만드는 근거 기반 학습 웹 앱입니다.
공개 문서를 업로드하면 `bge-m3`로 관련 구절을 찾고, 선택적으로 `bge-reranker-v2-m3`로 재정렬한 뒤, 채팅 모델이 `[S1]`, `[S2]` 근거를 붙여 설명합니다.

친구에게 추천할 때 한 줄로 말하면:

> “공개 논문을 올리면, HASA API가 관련 문단을 찾아 출처와 함께 설명해 주는 개인 웹 앱을 만든다.”

## 왜 이 프로젝트인가

| 장점 | 설명 |
|---|---|
| 웹 앱 형태 | Streamlit으로 브라우저에서 바로 시연 |
| API 실습 | 채팅·임베딩·리랭크를 한 흐름으로 경험 |
| 개인화 쉬움 | 주제·문서·역할만 바꿔도 각자 프로젝트 |
| 안전 장치 | 진단·치료 단정 금지, 근거 없는 내용은 모른다고 답함 |

## 화면에서 하는 일

1. 주제 선택 (논문 / 프로토콜 / 바이오센서 / 재생의학)
2. 공개 문서 업로드 또는 **샘플 문서**로 즉시 시작
3. 질문 → 검색 → (리랭크) → 근거 포함 답변
4. `top_k`·리랭커 on/off로 검색 품질 비교

```text
문서 업로드 → 청킹 → bge-m3 임베딩 → 유사도 검색
→ bge-reranker 재정렬 → phi-4 답변 + [S] 인용
```

## 1. API 키 준비

HASA 포털 [회원가입](https://open.hasa.re.kr/auth/signup) 후:

1. [활용 프로젝트](https://open.hasa.re.kr/account/projects) 등록
2. 개발키 신청
3. [개발키 관리](https://open.hasa.re.kr/account/dev-keys)에서 키 확인

개발키는 코드·README·채팅창에 붙이지 말고 `.env`에만 넣습니다.

| 기능 | 엔드포인트 | 용도 |
|---|---|---|
| 모델 목록 | `GET /v1/models` | 연결 확인 |
| 채팅 | `POST /v1/chat/completions` | 최종 답변 |
| 임베딩 | `POST /v1/embeddings` | 문서·질문 벡터화 |
| 리랭크 | `POST /rerank` | 검색 결과 재정렬 |

Base URL은 [API 문서](https://open.hasa.re.kr/docs)를 우선합니다. 현재 공개 설정 예: `http://210.123.135.174:8080/v1`

## 2. 실행 (Windows PowerShell)

```powershell
cd Final_Class
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

`.env` 최소 설정:

```dotenv
HASA_BASE_URL=http://210.123.135.174:8080/v1
HASA_API_KEY=발급받은_개발키
CHAT_MODEL=phi-4
EMBEDDING_MODEL=bge-m3
RERANK_MODEL=bge-reranker-v2-m3
USE_RERANK=true
```

```powershell
python healthcheck.py
streamlit run app.py
```

브라우저가 열리면 **샘플 문서**를 눌러 PCR 교육용 요약으로 바로 질문해 볼 수 있습니다.

## 3. 모델 선택

- 기본 채팅: `phi-4`
- 한국어 품질 비교: `exaone-4.0-32b` (키 허용 시)
- 검색: `bge-m3` / 재정렬: `bge-reranker-v2-m3`
- `403`이면 모델 ID 오류보다 **키 권한** 문제일 가능성이 큽니다 → `phi-4`로 재시도

## 4. 친구별 주제 예시

공통 앱은 그대로 두고 **역할·문서·질문만** 바꿉니다.

- **논문 이해** (가장 추천): 질환·바이오마커·유전자 공개 초록
- **실험 프로토콜**: PCR·ELISA·세포배양 공개 SOP
- **바이오센서**: 원리·성능지표·한계 비교
- **재생의학**: 스캐폴드·세포·조직공학 자료 (치료효과 단정 금지)
- **CSV 해설 / 이미지 설명**: 시간 남는 확장 과제

## 5. 발표 최소 성공 조건

1. 주제·자료 선정 이유를 30초 안에 설명
2. 문서 색인이 실제로 생성됨
3. 답변에 `[S]` 출처가 표시됨
4. 문서에 없는 질문에서 불확실성을 표현
5. API Key를 `.env`로만 관리

## 6. 파일 구조

```text
Final_Class/
├─ app.py                 # Streamlit 웹 UI
├─ hasa_client.py         # HASA 인증·채팅·임베딩·리랭크
├─ rag.py                 # 읽기·청킹·검색·근거 구성
├─ prompts.py             # 근거 기반 답변 규칙
├─ healthcheck.py         # API 연결 테스트
├─ .env.example
├─ requirements.txt
├─ data/
│  ├─ sample_pcr_protocol.md
│  └─ README.md
└─ docs/
   ├─ architecture.md
   └─ cursor-claude-prompts.md
```

## 7. 제한사항

교육용 프로토타입입니다. 환자 식별정보·진료기록·유전체 원자료는 올리지 마세요.
답변을 진단·치료·약물 결정에 쓰지 말고, 원문과 교수·전문가 검토를 전제로 하세요.

| 코드 | 확인할 것 |
|---|---|
| 401 | `.env` 키·Base URL |
| 403 | 허용 모델인지 (`phi-4` 재시도) |
| 404 | [모델 카탈로그](https://open.hasa.re.kr/models)에서 ID 복사 |
| 429 | 잠시 후 요청 수 줄이기 |
| 503 | [플랫폼 상태](https://open.hasa.re.kr/platform) 확인 |
