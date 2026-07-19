"""bge-m3로 텍스트를 벡터화하고 의미 유사도를 계산하는 실습."""

from __future__ import annotations

import math

from hasa_client import get_client, model, readable_error


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_size = math.sqrt(sum(a * a for a in left))
    right_size = math.sqrt(sum(b * b for b in right))
    return dot / (left_size * right_size) if left_size and right_size else 0.0


def main() -> None:
    query = "GPU 자원 신청 절차를 알고 싶습니다."
    documents = [
        "초거대AI클라우드팜 GPU 자원은 활용 목적과 필요 모델을 적어 신청합니다.",
        "회의실 예약은 사내 포털에서 날짜와 시간을 선택해 진행합니다.",
        "API 키는 개발용과 운영용을 분리하여 환경변수로 관리합니다.",
    ]
    inputs = [query, *documents]

    try:
        client = get_client()
        response = client.embeddings.create(
            model=model("EMBEDDING_MODEL"),
            input=inputs,
        )
        vectors = [item.embedding for item in response.data]

        print(f"벡터 차원: {len(vectors[0])}")
        print(f"질의: {query}\n")
        scores = [
            (cosine_similarity(vectors[0], vector), document)
            for vector, document in zip(vectors[1:], documents)
        ]
        for score, document in sorted(scores, reverse=True):
            print(f"{score:.4f} | {document}")
    except Exception as error:
        print("임베딩 호출 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

