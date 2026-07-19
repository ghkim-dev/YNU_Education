"""로컬 이미지 하나를 Qwen 계열 비전 모델에 전달하는 실습."""

from __future__ import annotations

import argparse
import base64
import mimetypes
from pathlib import Path

from hasa_client import get_client, model, readable_error


def image_as_data_url(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(image_path.name)
    mime_type = mime_type or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def main() -> None:
    parser = argparse.ArgumentParser(description="HASA 비전 모델 실습")
    parser.add_argument("--image", required=True, help="분석할 로컬 이미지 경로")
    parser.add_argument(
        "--question",
        default="이미지에서 확인되는 내용을 표로 정리하고, 확실하지 않은 내용은 추정이라고 표시해줘.",
    )
    parser.add_argument("--model", default=None, help="비전 모델 ID. 기본값은 .env의 VISION_MODEL")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.is_file():
        raise SystemExit(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=args.model or model("VISION_MODEL"),
            messages=[
                {
                    "role": "system",
                    "content": "이미지에서 실제로 보이는 것만 설명하세요. 추정은 반드시 추정이라고 표시하세요.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": args.question},
                        {"type": "image_url", "image_url": {"url": image_as_data_url(image_path)}},
                    ],
                },
            ],
            temperature=0.1,
            max_tokens=1200,
        )
        print(response.choices[0].message.content)
    except Exception as error:
        print("비전 호출 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

