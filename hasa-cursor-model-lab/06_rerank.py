"""HASA 전용 /rerank 엔드포인트로 문서를 다시 정렬하는 실습."""

from __future__ import annotations

import json

import requests

from hasa_client import api_root, model, readable_error, setting


def main() -> None:
    query = "API 키를 안전하게 보관하는 방법"
    documents = [
        "개발키와 운영키는 용도를 분리하고 서버 환경변수 또는 비밀관리 도구에 보관합니다.",
        "GPU 사용량은 대시보드에서 확인할 수 있습니다.",
        "회의록은 참석자 확인 후 공유 폴더에 등록합니다.",
    ]
    payload = {
        "model": model("RERANK_MODEL"),
        "query": query,
        "documents": documents,
    }

    try:
        response = requests.post(
            f"{api_root()}/rerank",
            headers={
                "Authorization": f"Bearer {setting('HASA_API_KEY')}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        print("질의:", query)
        print("\n[원본 응답]")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        print("\n응답의 index 또는 score를 보고 문서가 어떤 순서로 재정렬됐는지 확인하세요.")
    except Exception as error:
        print("리랭커 호출 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

