import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    data = {
        "email": "test@example.com",
        "password": "Test1234!"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print("회원가입 응답:", response.status_code)
    if response.status_code == 201:
        print("회원가입 성공:", response.json())
    else:
        print("회원가입 실패:", response.text)

def test_login():
    data = {
        "username": "test@example.com",
        "password": "Test1234!"
    }
    response = requests.post(f"{BASE_URL}/auth/login", data=data)
    print("로그인 응답:", response.status_code)
    if response.status_code == 200:
        print("로그인 성공:", response.json())
        return response.json().get("access_token")
    else:
        print("로그인 실패:", response.text)
        return None

def test_protected_route(token):
    if not token:
        print("토큰이 없어 보호된 경로 테스트를 건너뜁니다.")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/protected", headers=headers)
    print("보호된 경로 응답:", response.status_code)
    if response.status_code == 200:
        print("보호된 경로 접근 성공:", response.json())
    else:
        print("보호된 경로 접근 실패:", response.text)

if __name__ == "__main__":
    print("=== 인증 시스템 테스트 시작 ===")
    test_register()
    token = test_login()
    test_protected_route(token)
    print("=== 인증 시스템 테스트 완료 ===") 