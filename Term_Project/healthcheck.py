"""Run a small API connectivity test before starting Streamlit."""

from hasa_client import HasaAPIError, HasaClient


def main() -> None:
    try:
        client = HasaClient()
        models = client.list_models()
        print(f"[OK] gateway connected: {len(models)} models visible")
        print(f"[OK] chat model: {client.config.chat_model}")
        print(f"[OK] embedding model: {client.config.embedding_model}")
        answer = client.chat(
            [{"role": "user", "content": "한 문장으로, 세포란 무엇인지 설명해 주세요."}],
            max_tokens=120,
        )
        print(f"[OK] chat response: {answer}")
    except HasaAPIError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1) from exc
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] unexpected error: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
