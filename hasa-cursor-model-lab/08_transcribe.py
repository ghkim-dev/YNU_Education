"""Whisper large-v3를 이용한 로컬 음성 파일 전사 실습."""

from __future__ import annotations

import argparse
from pathlib import Path

from hasa_client import get_client, model, readable_error


def main() -> None:
    parser = argparse.ArgumentParser(description="HASA Whisper 음성 전사 실습")
    parser.add_argument("--audio", required=True, help="wav 또는 mp3 파일 경로")
    parser.add_argument("--language", default="ko", help="언어 코드. 한국어는 ko")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.is_file():
        raise SystemExit(f"음성 파일을 찾을 수 없습니다: {audio_path}")

    try:
        client = get_client()
        with audio_path.open("rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model("STT_MODEL"),
                file=audio_file,
                language=args.language,
            )
        print(getattr(transcript, "text", transcript))
    except Exception as error:
        print("음성 전사 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

