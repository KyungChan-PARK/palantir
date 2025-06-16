import re
from typing import List, Tuple
from .config import settings


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """
    비밀번호 유효성 검사
    Returns:
        Tuple[bool, List[str]]: (유효성 여부, 오류 메시지 리스트)
    """
    errors = []

    if len(password) < settings.MIN_PASSWORD_LENGTH:
        errors.append(
            f"비밀번호는 최소 {settings.MIN_PASSWORD_LENGTH}자 이상이어야 합니다."
        )

    if settings.REQUIRE_SPECIAL_CHAR and not re.search(
        r"[!@#$%^&*(),.?\":{}|<>]", password
    ):
        errors.append("비밀번호는 최소 1개의 특수문자를 포함해야 합니다.")

    if settings.REQUIRE_NUMBER and not re.search(r"\d", password):
        errors.append("비밀번호는 최소 1개의 숫자를 포함해야 합니다.")

    if settings.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        errors.append("비밀번호는 최소 1개의 대문자를 포함해야 합니다.")

    if settings.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        errors.append("비밀번호는 최소 1개의 소문자를 포함해야 합니다.")

    return len(errors) == 0, errors


def validate_email(email: str) -> Tuple[bool, List[str]]:
    """
    이메일 유효성 검사
    """
    errors = []
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_regex, email):
        errors.append("유효하지 않은 이메일 형식입니다.")

    return len(errors) == 0, errors
