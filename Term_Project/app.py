"""BioLens — HASA 기반 의생명 문서 학습 웹 앱."""

from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from hasa_client import HasaAPIError, HasaClient
from prompts import build_messages
from rag import RAGIndex


load_dotenv()

ROOT = Path(__file__).resolve().parent
SAMPLE_DOC = ROOT / "data" / "sample_pcr_protocol.md"

TOPIC_PRESETS: dict[str, dict[str, object]] = {
    "논문 이해 도우미": {
        "role": "특정 질환·바이오마커·유전자 주제의 공개 논문을 근거로 연구 질문을 설명하는 학습 도우미",
        "examples": [
            "이 자료의 연구 목적과 핵심 가설은 무엇인가요?",
            "실험에서 사용한 주요 지표와 그 의미는 무엇인가요?",
            "저자들이 밝힌 한계와 후속 연구 과제는 무엇인가요?",
        ],
    },
    "실험 프로토콜 도우미": {
        "role": "세포배양·PCR·ELISA 등 공개 실험 프로토콜의 목적, 단계, 주의점을 설명하는 학습 도우미",
        "examples": [
            "이 실험의 목적과 필요한 시약은 무엇인가요?",
            "단계별로 어떤 일이 일어나며 주의할 점은 무엇인가요?",
            "결과가 기대와 다를 때 먼저 점검할 항목은 무엇인가요?",
        ],
    },
    "바이오센서 문헌 도우미": {
        "role": "바이오센서의 원리, 측정 대상, 성능지표, 한계를 비교·설명하는 학습 도우미",
        "examples": [
            "이 센서가 측정하는 대상과 동작 원리는 무엇인가요?",
            "감도·특이도·검출한계 등 성능지표를 정리해 주세요.",
            "실제 적용 시 고려해야 할 한계는 무엇인가요?",
        ],
    },
    "재생의학 자료 도우미": {
        "role": "스캐폴드·세포·조직공학 자료를 비교하되 치료효과를 단정하지 않는 학습 도우미",
        "examples": [
            "사용한 세포·스캐폴드 재료의 특징은 무엇인가요?",
            "평가에 쓰인 지표와 관찰 결과는 어떻게 정리되나요?",
            "자료에서 치료효과를 단정하기 어려운 이유는 무엇인가요?",
        ],
    },
}

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
  font-family: "IBM Plex Sans KR", "IBM Plex Sans", sans-serif;
}

.stApp {
  background:
    radial-gradient(1200px 600px at 10% -10%, #dceee8 0%, transparent 55%),
    radial-gradient(900px 500px at 100% 0%, #e8f0f7 0%, transparent 50%),
    linear-gradient(180deg, #f7faf9 0%, #eef3f1 100%);
}

.hero {
  padding: 1.4rem 1.6rem 1.2rem;
  border-radius: 18px;
  background: linear-gradient(135deg, #0f3d3e 0%, #1a5c5e 48%, #2f6f7a 100%);
  color: #f4fbfa;
  margin-bottom: 1.1rem;
  box-shadow: 0 18px 40px rgba(15, 61, 62, 0.18);
}

.hero h1 {
  margin: 0;
  font-size: 2rem;
  letter-spacing: -0.02em;
  font-weight: 700;
}

.hero p {
  margin: 0.45rem 0 0;
  opacity: 0.92;
  line-height: 1.55;
  max-width: 46rem;
}

.pipeline {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.55rem;
  margin: 0.9rem 0 1.2rem;
}

.step {
  background: rgba(255,255,255,0.78);
  border: 1px solid #d7e4e1;
  border-radius: 12px;
  padding: 0.7rem 0.75rem;
  min-height: 4.4rem;
}

.step .label {
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #5f7774;
  margin-bottom: 0.25rem;
}

.step .title {
  font-weight: 600;
  color: #143a3b;
  font-size: 0.95rem;
}

.step.done {
  border-color: #7eb8ae;
  background: #eef8f5;
}

.step.active {
  border-color: #1a5c5e;
  box-shadow: inset 0 0 0 1px #1a5c5e;
}

.soft-card {
  background: rgba(255,255,255,0.82);
  border: 1px solid #d7e4e1;
  border-radius: 14px;
  padding: 0.95rem 1rem;
  margin-bottom: 0.85rem;
}

.soft-card h3 {
  margin: 0 0 0.35rem;
  font-size: 1.02rem;
  color: #143a3b;
}

.soft-card p, .soft-card li {
  color: #33504e;
  font-size: 0.92rem;
  line-height: 1.5;
}

.chip {
  display: inline-block;
  background: #e7f2ef;
  color: #1a5c5e;
  border-radius: 999px;
  padding: 0.18rem 0.65rem;
  font-size: 0.78rem;
  margin: 0.15rem 0.25rem 0.15rem 0;
}

@media (max-width: 900px) {
  .pipeline { grid-template-columns: 1fr 1fr; }
  .hero h1 { font-size: 1.55rem; }
}
</style>
"""


def init_state() -> None:
    st.session_state.setdefault("index", None)
    st.session_state.setdefault("indexed_names", [])
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("topic", "실험 프로토콜 도우미")
    st.session_state.setdefault("project_role", TOPIC_PRESETS["실험 프로토콜 도우미"]["role"])
    st.session_state.setdefault("pending_question", None)


def make_client() -> HasaClient | None:
    try:
        return HasaClient()
    except HasaAPIError as exc:
        st.sidebar.error(str(exc))
        return None


def render_sources(results: list[dict]) -> None:
    if not results:
        return
    with st.expander("답변에 사용된 문서 근거", expanded=False):
        for number, item in enumerate(results, start=1):
            chunk = item["chunk"]
            score = item.get("score", 0.0)
            st.markdown(f"**[S{number}] {chunk.source}** · 관련도 `{score:.3f}`")
            st.caption(chunk.text)


def pipeline_html(*, has_key: bool, has_index: bool, asked: bool) -> str:
    stages = [
        ("설정", "API 연결", has_key),
        ("자료", "문서 업로드", has_index or asked),
        ("색인", "임베딩", has_index),
        ("검색", "리랭크", asked and has_index),
        ("답변", "근거 인용", asked),
    ]
    cards = []
    for label, title, done in stages:
        klass = "step done" if done else "step"
        if not done and (
            (label == "설정" and not has_key)
            or (label == "자료" and has_key and not has_index)
            or (label == "색인" and has_key and not has_index)
        ):
            klass = "step active"
        cards.append(
            f'<div class="{klass}"><div class="label">{label}</div>'
            f'<div class="title">{title}</div></div>'
        )
    return f'<div class="pipeline">{"".join(cards)}</div>'


def load_sample_index(client: HasaClient) -> None:
    if not SAMPLE_DOC.exists():
        raise FileNotFoundError("샘플 문서를 찾을 수 없습니다: data/sample_pcr_protocol.md")

    class _Upload:
        def __init__(self, path: Path) -> None:
            self.name = path.name
            self._path = path

        def seek(self, *_args, **_kwargs) -> None:
            return None

        def read(self) -> bytes:
            return self._path.read_bytes()

    st.session_state.index = RAGIndex.from_uploads([_Upload(SAMPLE_DOC)], client)
    st.session_state.indexed_names = [SAMPLE_DOC.name]
    st.session_state.messages = []


def main() -> None:
    init_state()
    st.set_page_config(
        page_title="BioLens · HASA 의생명 문서 도우미",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="hero">
          <h1>BioLens</h1>
          <p>
            HASA Open AI Service Hub의 임베딩·리랭커·채팅 API로 만드는
            근거 기반 의생명공학 학습 웹 앱입니다.
            공개 문서를 올리고, 출처가 표시되는 답변을 받아 보세요.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    client = make_client()
    has_key = client is not None
    has_index = st.session_state.index is not None
    asked = bool(st.session_state.messages)

    st.markdown(
        pipeline_html(has_key=has_key, has_index=has_index, asked=asked),
        unsafe_allow_html=True,
    )

    if client is None:
        st.markdown(
            """
            <div class="soft-card">
              <h3>시작 전 준비</h3>
              <p>1. HASA 포털에서 개발키를 발급합니다.</p>
              <p>2. <code>.env.example</code>을 복사해 <code>.env</code>를 만들고 키를 입력합니다.</p>
              <p>3. <code>python healthcheck.py</code>로 연결을 확인한 뒤 이 페이지를 새로고침합니다.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    with st.sidebar:
        st.header("실습 설정")
        topic = st.selectbox(
            "프로젝트 주제",
            options=list(TOPIC_PRESETS.keys()),
            index=list(TOPIC_PRESETS.keys()).index(st.session_state.topic)
            if st.session_state.topic in TOPIC_PRESETS
            else 1,
        )
        if topic != st.session_state.topic:
            st.session_state.topic = topic
            st.session_state.project_role = str(TOPIC_PRESETS[topic]["role"])

        project_role = st.text_area(
            "AI의 역할",
            value=str(st.session_state.project_role),
            height=90,
            help="친구마다 관심 분야에 맞게 바꿔 보세요.",
        )
        st.session_state.project_role = project_role

        st.divider()
        st.subheader("모델")
        st.caption(f"채팅 `{client.config.chat_model}`")
        st.caption(f"임베딩 `{client.config.embedding_model}`")
        st.caption(
            f"리랭커 `{client.config.rerank_model}`"
            if client.config.use_rerank
            else "리랭커 사용 안 함 (.env)"
        )

        top_k = st.slider("검색 문서 수 (top_k)", min_value=2, max_value=10, value=client.config.top_k)
        use_rerank = st.toggle("리랭커 사용", value=client.config.use_rerank)

        if st.button("API 연결 확인", use_container_width=True):
            try:
                models = client.list_models()
                st.success(f"연결 성공 · 모델 {len(models)}개")
                st.caption(", ".join(models[:10]) + (" …" if len(models) > 10 else ""))
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

        st.divider()
        st.subheader("1. 참고 문서")
        uploads = st.file_uploader(
            "공개 PDF · TXT · MD · CSV",
            type=["pdf", "txt", "md", "csv"],
            accept_multiple_files=True,
            help="환자정보·진료기록은 업로드하지 마세요.",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            build_clicked = st.button("색인 만들기", use_container_width=True, type="primary")
        with col_b:
            sample_clicked = st.button("샘플 문서", use_container_width=True)

        if sample_clicked:
            try:
                with st.spinner("샘플 PCR 프로토콜 색인 중..."):
                    load_sample_index(client)
                st.success("샘플 문서를 색인했습니다.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

        if uploads and build_clicked:
            try:
                with st.spinner("문서 분할 → 임베딩 생성 중..."):
                    st.session_state.index = RAGIndex.from_uploads(uploads, client)
                    st.session_state.indexed_names = [upload.name for upload in uploads]
                    st.session_state.messages = []
                st.success(f"{len(st.session_state.index.chunks)}개 청크를 색인했습니다.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(str(exc))

        if st.session_state.index is not None:
            st.info("색인: " + ", ".join(st.session_state.indexed_names))
            st.caption(f"청크 {len(st.session_state.index.chunks)}개")
            if st.button("색인 초기화", use_container_width=True):
                st.session_state.index = None
                st.session_state.indexed_names = []
                st.session_state.messages = []
                st.rerun()

        st.divider()
        st.caption("교육용 프로토타입 · 진단·치료·개인 의학적 판단에 사용하지 마세요.")

    left, right = st.columns([1.15, 1.85], gap="large")

    with left:
        st.markdown(
            f"""
            <div class="soft-card">
              <h3>오늘 실습에서 할 일</h3>
              <p><span class="chip">{st.session_state.topic}</span></p>
              <ol>
                <li>왼쪽에서 주제와 AI 역할을 정합니다.</li>
                <li>공개 문서를 업로드하거나 <b>샘플 문서</b>로 바로 시작합니다.</li>
                <li>질문을 던지고 답변의 <b>[S1]</b> 근거를 원문과 대조합니다.</li>
                <li>문서에 없는 질문·의료 판단 유도 질문도 한 번씩 시험합니다.</li>
              </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        examples = TOPIC_PRESETS[st.session_state.topic]["examples"]
        st.markdown("**예시 질문**")
        for example in examples:
            if st.button(example, key=f"ex-{example}", use_container_width=True):
                st.session_state.pending_question = example

        with st.expander("발표용 최소 성공 조건"):
            st.markdown(
                """
                1. 주제와 자료 선정 이유를 30초 안에 설명  
                2. 문서 업로드 후 색인이 생성됨  
                3. 답변에 문서 출처 `[S]`가 표시됨  
                4. 문서에 없는 질문에서 불확실성을 표현함  
                5. API Key를 `.env`로만 관리함  
                """
            )

        with st.expander("비교해 볼 실험"):
            st.markdown(
                """
                - `top_k`를 3과 8로 바꿔 근거가 어떻게 달라지는지 확인  
                - 리랭커 on/off 후 선택되는 문단 비교  
                - `.env`의 `CHAT_MODEL`만 바꿔 답변 톤 비교  
                """
            )

    with right:
        st.subheader("2. 질문하기")
        if not st.session_state.index:
            st.warning("왼쪽에서 문서를 색인하거나 **샘플 문서** 버튼으로 바로 시작해 주세요.")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("sources"):
                    render_sources(message["sources"])

        typed = st.chat_input("예: 이 자료에서 실험의 목적과 주요 한계는 무엇인가요?")
        question = st.session_state.pop("pending_question", None) or typed
        if not question:
            return

        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        results: list[dict] = []
        context = ""
        try:
            if st.session_state.index:
                with st.spinner("관련 문서 검색 중..."):
                    results = st.session_state.index.search(
                        question,
                        client,
                        top_k=top_k,
                        use_rerank=use_rerank,
                    )
                    context = st.session_state.index.context_text(
                        results,
                        max_chars=client.config.max_context_chars,
                    )
                    if st.session_state.index.last_note:
                        st.info(st.session_state.index.last_note)

            messages = build_messages(question, context, project_role)
            with st.chat_message("assistant"):
                with st.spinner("답변 생성 중..."):
                    answer = client.chat(messages)
                st.markdown(answer)
                render_sources(results)
                if results:
                    st.caption(
                        f"사용한 근거 {len(results)}개 · top_k={top_k} · "
                        f"리랭커={'ON' if use_rerank else 'OFF'}"
                    )
            st.session_state.messages.append(
                {"role": "assistant", "content": answer, "sources": results}
            )
        except Exception as exc:  # noqa: BLE001
            error_message = str(exc)
            with st.chat_message("assistant"):
                st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})


if __name__ == "__main__":
    main()
