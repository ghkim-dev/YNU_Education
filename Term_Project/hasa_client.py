"""Small client wrapper for the HASA OpenAI-compatible gateway.

The rest of the application only depends on this module. This keeps the
provider-specific Base URL, authentication, and error messages in one place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable

import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class HasaAPIError(RuntimeError):
    """An actionable error returned by the HASA gateway."""


@dataclass(frozen=True)
class HasaConfig:
    base_url: str
    api_key: str
    chat_model: str
    embedding_model: str
    rerank_model: str
    use_rerank: bool
    top_k: int
    max_context_chars: int
    timeout_seconds: int

    @classmethod
    def from_env(cls) -> "HasaConfig":
        base_url = os.getenv("HASA_BASE_URL", "").strip().rstrip("/")
        api_key = os.getenv("HASA_API_KEY", "").strip()
        if not base_url:
            raise HasaAPIError("HASA_BASE_URL이 비어 있습니다. .env 파일을 확인하세요.")
        if not api_key or api_key == "sk-dev-replace-me":
            raise HasaAPIError("HASA_API_KEY가 설정되지 않았습니다. .env 파일에 개발키를 입력하세요.")

        def int_env(name: str, default: int) -> int:
            try:
                return int(os.getenv(name, str(default)))
            except ValueError:
                return default

        return cls(
            base_url=base_url,
            api_key=api_key,
            chat_model=os.getenv("CHAT_MODEL", "phi-4").strip(),
            embedding_model=os.getenv("EMBEDDING_MODEL", "bge-m3").strip(),
            rerank_model=os.getenv("RERANK_MODEL", "bge-reranker-v2-m3").strip(),
            use_rerank=os.getenv("USE_RERANK", "true").lower() in {"1", "true", "yes", "y"},
            top_k=max(1, int_env("TOP_K", 5)),
            max_context_chars=max(2000, int_env("MAX_CONTEXT_CHARS", 12000)),
            timeout_seconds=max(10, int_env("HASA_TIMEOUT_SECONDS", 90)),
        )


class HasaClient:
    def __init__(self, config: HasaConfig | None = None) -> None:
        self.config = config or HasaConfig.from_env()
        self._openai = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout_seconds,
            max_retries=1,
        )

    @property
    def api_origin(self) -> str:
        """Return the gateway origin used by non-OpenAI-compatible endpoints."""

        return self.config.base_url.removesuffix("/v1").rstrip("/")

    def _raise_http_error(self, response: requests.Response) -> None:
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text[:500]

        detail = body
        if isinstance(body, dict):
            detail = body.get("detail") or body.get("message") or body.get("error") or body

        hints = {
            401: "API Key가 없거나 유효하지 않습니다.",
            403: "현재 API Key에 해당 모델 사용 권한이 없습니다. .env의 모델을 phi-4 또는 포털에서 허용된 모델로 바꿔 보세요.",
            404: "모델 ID 또는 엔드포인트를 확인하세요.",
            429: "요청 한도를 초과했습니다. 잠시 후 다시 시도하세요.",
            503: "GPU 백엔드가 준비 중이거나 일시적으로 응답하지 않습니다.",
        }
        hint = hints.get(response.status_code, "API 요청이 실패했습니다.")
        raise HasaAPIError(f"{hint}\nHTTP {response.status_code}: {detail}")

    def list_models(self) -> list[str]:
        """List model IDs visible to the current gateway."""

        response = requests.get(
            f"{self.config.base_url}/models",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
            timeout=self.config.timeout_seconds,
        )
        if not response.ok:
            self._raise_http_error(response)
        payload = response.json()
        return [item.get("id", "") for item in payload.get("data", []) if item.get("id")]

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 900,
    ) -> str:
        response = self._openai.chat.completions.create(
            model=model or self.config.chat_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    def embed(self, texts: Iterable[str], *, model: str | None = None) -> list[list[float]]:
        values = list(texts)
        if not values:
            return []
        response = self._openai.embeddings.create(
            model=model or self.config.embedding_model,
            input=values,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

    def rerank(
        self,
        query: str,
        documents: list[str],
        *,
        model: str | None = None,
    ) -> list[tuple[int, float]]:
        """Return (document_index, score) pairs in descending relevance order.

        HASA documents describe this endpoint as Jina-compatible. The parser
        accepts both ``results`` and ``data`` response envelopes to make the
        classroom starter more tolerant of minor gateway version differences.
        """

        if not documents:
            return []
        response = requests.post(
            f"{self.api_origin}/rerank",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model or self.config.rerank_model,
                "query": query,
                "documents": documents,
            },
            timeout=self.config.timeout_seconds,
        )
        if not response.ok:
            self._raise_http_error(response)

        payload = response.json()
        rows = payload.get("results", payload.get("data", payload)) if isinstance(payload, dict) else payload
        result: list[tuple[int, float]] = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            index = row.get("index", row.get("document_index"))
            score = row.get("relevance_score", row.get("score", row.get("relevance")))
            if index is None or score is None:
                continue
            result.append((int(index), float(score)))
        return sorted(result, key=lambda pair: pair[1], reverse=True)
