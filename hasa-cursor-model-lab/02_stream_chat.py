"""응답이 생성되는 대로 화면에 출력하는 스트리밍 채팅 실습."""

from hasa_client import get_client, model, readable_error


def main() -> None:
    question = input("질문을 입력하세요: ").strip()
    if not question:
        raise SystemExit("질문이 비어 있습니다.")

    try:
        client = get_client()
        stream = client.chat.completions.create(
            model=model("TEXT_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": "한국어로 간결하고 정확하게 답하는 AI 비서입니다.",
                },
                {"role": "user", "content": question},
            ],
            temperature=0.2,
            max_tokens=1024,
            stream=True,
        )

        print("\n[AI 답변]")
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
        print()
    except Exception as error:
        print("\n호출 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

