"""같은 질문을 여러 HASA 모델에 보내 결과와 사용감을 비교하는 실습."""

from __future__ import annotations

import argparse

from hasa_client import get_client, model, readable_error


def ask(client, model_id: str, question: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                "role": "system",
                "content": "한국어로 답하고, 핵심 근거와 결론을 구분해 간결하게 작성하세요.",
            },
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        max_tokens=700,
    )
    return response.choices[0].message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(description="HASA 모델 비교 실습")
    parser.add_argument(
        "question",
        nargs="?",
        default="우리 기관의 AI 교육 안내문을 작성할 때 확인해야 할 항목을 5개로 정리해줘.",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=[model("TEXT_MODEL"), "qwen2.5-coder-32b", "gpt-oss-20b"],
        help="비교할 모델 ID를 공백으로 구분해 입력합니다.",
    )
    args = parser.parse_args()

    client = get_client()
    print(f"질문: {args.question}")
    print("=" * 72)

    for model_id in args.models:
        print(f"MODEL: {model_id}")
        try:
            print(ask(client, model_id, args.question))
        except Exception as error:
            # 개발키에 허용되지 않은 모델도 있을 수 있으므로 전체 실습을 멈추지 않는다.
            print(f"[이 모델은 비교하지 못했습니다] {readable_error(error)}")
        print("-" * 72)


if __name__ == "__main__":
    main()

