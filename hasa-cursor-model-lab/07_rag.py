"""벡터 검색과 채팅 모델을 결합한 최소 RAG 실습."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from hasa_client import PROJECT_DIR, get_client, model, readable_error


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_size = math.sqrt(sum(a * a for a in left))
    right_size = math.sqrt(sum(b * b for b in right))
    return dot / (left_size * right_size) if left_size and right_size else 0.0


def load_chunks() -> list[str]:
    source = PROJECT_DIR / "data" / "knowledge.txt"
    return [chunk.strip() for chunk in source.read_text(encoding="utf-8").split("\n\n") if chunk.strip()]


def retrieve(client, question: str, chunks: list[str], top_k: int = 3) -> list[tuple[int, str, float]]:
    response = client.embeddings.create(
        model=model("EMBEDDING_MODEL"),
        input=[question, *chunks],
    )
    vectors = [item.embedding for item in response.data]
    scored = [
        (index + 1, chunk, cosine_similarity(vectors[0], vector))
        for index, (chunk, vector) in enumerate(zip(chunks, vectors[1:]))
    ]
    return sorted(scored, key=lambda item: item[2], reverse=True)[:top_k]


def answer_with_context(client, question: str, selected: list[tuple[int, str, float]]) -> str:
    context = "\n\n".join(f"[근거 문서 {index}]\n{chunk}" for index, chunk, _ in selected)
    response = client.chat.completions.create(
        model=model("TEXT_MODEL"),
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 내부 문서 기반 질의응답 도우미입니다. "
                    "아래 근거 문서 밖의 사실은 만들지 마세요. "
                    "답변의 문장 끝에 사용한 근거 번호를 [근거 문서 n] 형식으로 붙이세요."
                ),
            },
            {
                "role": "user",
                "content": f"질문: {question}\n\n근거 문서:\n{context}",
            },
        ],
        temperature=0.1,
        max_tokens=900,
    )
    return response.choices[0].message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(description="최소 RAG 실습")
    parser.add_argument("question", nargs="?", default="API 키는 어디에 보관해야 하나요?")
    args = parser.parse_args()

    try:
        client = get_client()
        chunks = load_chunks()
        selected = retrieve(client, args.question, chunks)

        print("[검색된 근거]")
        for index, chunk, score in selected:
            print(f"문서 {index} | 유사도 {score:.4f}")
            print(chunk.replace("\n", " "))
            print()

        print("[RAG 답변]")
        print(answer_with_context(client, args.question, selected))
    except Exception as error:
        print("RAG 실행 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

