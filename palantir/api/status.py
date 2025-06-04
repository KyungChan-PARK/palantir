"""상태 확인 API 라우터.

서버 상태 확인용 엔드포인트 제공.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def get_status() -> dict:
    """서버 상태 확인 엔드포인트.

    Returns:
        dict: 상태 정보
    """
    return {"status": "ok"}
