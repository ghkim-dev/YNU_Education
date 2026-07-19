"""텍스트 모델에 한 번 질문하고 답을 받는 가장 작은 채팅 실습."""

from __future__ import annotations

import argparse

from hasa_client import get_client, model, readable_error


SYSTEM_PROMPT = """당신은 한국어 업무 보조 AI입니다.
답변은 사실과 추정을 구분하고, 요청한 형식을 우선합니다.
모르는 내용은 지어내지 말고 확인이 필요하다고 말하세요."""


def main() -> None:
    parser = argparse.ArgumentParser(description="HASA 텍스트 채팅 실습")
    parser.add_argument("question", nargs="?", help="질문. 생략하면 실행 중에 입력합니다.")
    parser.add_argument("--model", default=None, help="이번 실행에서만 쓸 모델 ID")
    parser.add_argument("--temperature", type=float, default=0.2)
    args = parser.parse_args()

    question = args.question or input("질문을 입력하세요: ").strip()
    if not question:
        raise SystemExit("질문이 비어 있습니다.")

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=args.model or model("TEXT_MODEL"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=args.temperature,
            max_tokens=1024,
        )
        print("\n[AI 답변]")
        print(response.choices[0].message.content)
    except Exception as error:
        print("\n호출 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

