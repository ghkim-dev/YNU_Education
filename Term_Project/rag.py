"""Minimal, inspectable RAG pipeline for the BioLens classroom project."""

from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, BinaryIO

from pypdf import PdfReader

from hasa_client import HasaAPIError, HasaClient


@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str
    vector: list[float] | None = None


def read_file(uploaded_file: BinaryIO, filename: str) -> str:
    """Read a Streamlit upload as plain text without sending the file itself."""

    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    raw = uploaded_file.read()
    suffix = PurePosixPath(filename).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(raw))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if suffix == ".csv":
        decoded = raw.decode("utf-8-sig", errors="replace")
        rows = csv.reader(io.StringIO(decoded))
        return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
    return raw.decode("utf-8-sig", errors="replace")


def split_text(text: str, *, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    if overlap >= chunk_size:
        overlap = chunk_size // 5

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        if end < len(cleaned):
            boundary = cleaned.rfind(". ", start, end)
            if boundary > start + int(chunk_size * 0.6):
                end = boundary + 1
        chunks.append(cleaned[start:end].strip())
        if end >= len(cleaned):
            break
        start = max(start + 1, end - overlap)
    return chunks


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class RAGIndex:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.last_note = ""

    @classmethod
    def from_uploads(
        cls,
        uploads: list[Any],
        client: HasaClient,
        *,
        chunk_size: int = 1000,
    ) -> "RAGIndex":
        chunks: list[Chunk] = []
        for upload in uploads:
            text = read_file(upload, upload.name)
            for number, piece in enumerate(split_text(text, chunk_size=chunk_size), start=1):
                chunks.append(Chunk(chunk_id=f"{upload.name}-{number}", source=upload.name, text=piece))

        if not chunks:
            raise ValueError("업로드한 파일에서 읽을 수 있는 텍스트가 없습니다.")

        vectors = client.embed([chunk.text for chunk in chunks])
        for chunk, vector in zip(chunks, vectors):
            chunk.vector = vector
        return cls(chunks)

    def search(
        self,
        query: str,
        client: HasaClient,
        *,
        top_k: int = 5,
        use_rerank: bool = True,
    ) -> list[dict[str, Any]]:
        query_vector = client.embed([query])[0]
        scored = [
            {
                "chunk": chunk,
                "score": cosine_similarity(query_vector, chunk.vector or []),
            }
            for chunk in self.chunks
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        candidates = scored[: max(top_k * 3, 8)]

        if use_rerank and len(candidates) > 1:
            texts = [item["chunk"].text for item in candidates]
            try:
                reranked = client.rerank(query, texts)
            except HasaAPIError as exc:
                # A development key may allow embeddings but not the optional
                # reranker. Keep the MVP usable and make the limitation visible.
                self.last_note = f"리랭커를 사용할 수 없어 임베딩 검색 결과를 사용했습니다: {exc}"
                reranked = []
            if reranked:
                candidates = [
                    {"chunk": candidates[index]["chunk"], "score": score}
                    for index, score in reranked
                    if 0 <= index < len(candidates)
                ]

        return candidates[:top_k]

    @staticmethod
    def context_text(results: list[dict[str, Any]], max_chars: int = 12000) -> str:
        blocks: list[str] = []
        used = 0
        for number, item in enumerate(results, start=1):
            chunk: Chunk = item["chunk"]
            block = f"[S{number}] 출처: {chunk.source}\n{chunk.text}"
            if used + len(block) > max_chars:
                break
            blocks.append(block)
            used += len(block)
        return "\n\n".join(blocks)
