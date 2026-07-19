"""HASA OpenAI 호환 API에 공통으로 연결하는 작은 도우미 모듈."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# 어느 스크립트에서 실행해도 프로젝트 루트의 .env를 읽도록 고정한다.
PROJECT_DIR = Path(__file__).resolve().parent
load_dotenv(PROJECT_DIR / ".env")


def setting(name: str, default: str | None = None) -> str:
    """환경변수 값을 읽고, 필수값이 비어 있으면 이해하기 쉬운 오류를 낸다."""
    value = os.getenv(name, default)
    if value is None or not value.strip():
        raise RuntimeError(
            f"{name} 값이 비어 있습니다. .env.example을 복사해 .env를 만들고 값을 입력하세요."
        )
    return value.strip()


def get_client() -> OpenAI:
    """OpenAI SDK를 HASA Base URL로 연결한다."""
    return OpenAI(
        base_url=setting("HASA_BASE_URL").rstrip("/"),
        api_key=setting("HASA_API_KEY"),
    )


def api_root() -> str:
    """OpenAI 호환 /v1 바깥에 있는 HASA 전용 엔드포인트용 주소를 만든다."""
    base_url = setting("HASA_BASE_URL").rstrip("/")
    return base_url[:-3] if base_url.endswith("/v1") else base_url


def model(name: str) -> str:
    """TEXT_MODEL처럼 .env에 둔 모델 이름을 읽는다."""
    return setting(name)


def readable_error(error: Exception) -> str:
    """초보자가 바로 다음 조치를 알 수 있게 자주 나는 오류를 풀어 쓴다."""
    text = str(error)
    if "401" in text:
        return "401 인증 오류: HASA_API_KEY가 비어 있거나 잘못되었습니다."
    if "403" in text:
        return "403 권한 오류: 현재 키에 이 모델 사용 권한이 없을 수 있습니다."
    if "404" in text:
        return "404 모델/주소 오류: 모델 ID와 HASA_BASE_URL을 다시 확인하세요."
    if "429" in text:
        return "429 한도 초과: 잠시 기다렸다가 다시 실행하세요."
    if "503" in text:
        return "503 백엔드 준비 중: GPU 모델이 준비될 때까지 잠시 후 다시 시도하세요."
    return text

