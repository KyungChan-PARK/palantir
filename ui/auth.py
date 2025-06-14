import streamlit as st
import requests
from typing import Optional, Dict, Any
import jwt

class AuthManager:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        if "user_token" not in st.session_state:
            st.session_state.user_token = None
        if "user_info" not in st.session_state:
            st.session_state.user_info = None

    def login(self, email: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{self.api_url}/auth/jwt/login",
                data={"username": email, "password": password}
            )
            if response.status_code == 200:
                token = response.json()["access_token"]
                st.session_state.user_token = token
                self._update_user_info(token)
                return True
            return False
        except Exception as e:
            st.error(f"로그인 실패: {str(e)}")
            return False

    def register(self, email: str, username: str, password: str) -> bool:
        try:
            response = requests.post(
                f"{self.api_url}/auth/register",
                json={
                    "email": email,
                    "username": username,
                    "password": password
                }
            )
            if response.status_code == 201:
                st.success("회원가입이 완료되었습니다. 로그인해주세요.")
                return True
            return False
        except Exception as e:
            st.error(f"회원가입 실패: {str(e)}")
            return False

    def logout(self):
        st.session_state.user_token = None
        st.session_state.user_info = None

    def is_authenticated(self) -> bool:
        return st.session_state.user_token is not None

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        return st.session_state.user_info

    def _update_user_info(self, token: str):
        try:
            # JWT 토큰에서 사용자 정보 추출
            payload = jwt.decode(token, options={"verify_signature": False})
            st.session_state.user_info = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "is_superuser": payload.get("is_superuser", False)
            }
        except Exception as e:
            st.error(f"사용자 정보 업데이트 실패: {str(e)}")

def render_auth_ui():
    """인증 UI 컴포넌트"""
    auth = AuthManager()
    
    if not auth.is_authenticated():
        tab1, tab2 = st.tabs(["로그인", "회원가입"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("이메일")
                password = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인"):
                    if auth.login(email, password):
                        st.success("로그인 성공!")
                        st.rerun()
        
        with tab2:
            with st.form("register_form"):
                reg_email = st.text_input("이메일", key="reg_email")
                reg_username = st.text_input("사용자명")
                reg_password = st.text_input("비밀번호", type="password", key="reg_pass")
                reg_password2 = st.text_input("비밀번호 확인", type="password")
                if st.form_submit_button("회원가입"):
                    if reg_password != reg_password2:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        if auth.register(reg_email, reg_username, reg_password):
                            st.success("회원가입이 완료되었습니다. 로그인해주세요.")
    else:
        user_info = auth.get_user_info()
        st.write(f"👤 {user_info['email']}")
        if st.button("로그아웃"):
            auth.logout()
            st.rerun()

    return auth.is_authenticated() 