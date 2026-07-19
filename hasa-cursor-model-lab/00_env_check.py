"""내 API 키로 접근 가능한 모델을 확인하는 첫 번째 실습."""

from hasa_client import get_client, readable_error


def main() -> None:
    try:
        client = get_client()
        models = client.models.list()
        model_ids = sorted(item.id for item in models.data)

        print(f"연결 성공: 현재 키로 조회된 모델 {len(model_ids)}개")
        print("-" * 60)
        for model_id in model_ids:
            print(model_id)
        print("-" * 60)
        print("위 목록을 보고 .env의 TEXT_MODEL 등 모델명을 현재 권한에 맞게 바꾸세요.")
    except Exception as error:
        print("연결 확인 실패")
        print(readable_error(error))


if __name__ == "__main__":
    main()

