"""Cursor에서 실행해 보는 가장 작은 HASA 웹 채팅 앱."""

from __future__ import annotations

import streamlit as st

from hasa_client import get_client, model, readable_error


st.set_page_config(page_title="HASA Cursor Lab", page_icon="⚡")
st.title("⚡ HASA 로컬 채팅 실습")
st.caption("API 키는 .env에서만 읽습니다. 화면이나 코드에 실제 키를 쓰지 마세요.")


@st.cache_resource
def client():
    return get_client()


try:
    default_model = model("TEXT_MODEL")
except Exception as error:
    st.error(readable_error(error))
    st.stop()

selected_model = st.sidebar.text_input("모델 ID", value=default_model)
st.sidebar.caption("먼저 00_env_check.py로 내 키에 허용된 모델을 확인하세요.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("질문을 입력하세요")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = client().chat.completions.create(
                model=selected_model,
                messages=[
                    {
                        "role": "system",
                        "content": "한국어 업무 보조 AI입니다. 근거 없는 사실은 만들지 마세요.",
                    },
                    *st.session_state.messages,
                ],
                temperature=0.2,
                max_tokens=1000,
            )
            answer = response.choices[0].message.content or ""
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as error:
            st.error(readable_error(error))
