"""API 문서 자동화 모듈."""

import json
from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from palantir.core.config import settings


def custom_openapi() -> Dict[str, Any]:
    """OpenAPI 스키마 생성."""
    if not hasattr(custom_openapi, "openapi_schema"):
        custom_openapi.openapi_schema = get_openapi(
            title=settings.API_TITLE,
            version=settings.API_VERSION,
            description=settings.API_DESCRIPTION,
            routes=app.routes,
            servers=[{"url": "/"}],
            components={
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                }
            },
            security=[{"bearerAuth": []}],
            tags=[
                {
                    "name": "users",
                    "description": "사용자 관리 API",
                },
                {
                    "name": "auth",
                    "description": "인증 관련 API",
                },
                {
                    "name": "admin",
                    "description": "관리자 전용 API",
                },
            ],
        )
    return custom_openapi.openapi_schema

def setup_docs(app: FastAPI) -> None:
    """API 문서 설정."""
    # OpenAPI 스키마 설정
    app.openapi = custom_openapi
    
    # 정적 파일 마운트
    static_path = Path(__file__).parent.parent / "static"
    static_path.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    
    # Swagger UI 엔드포인트
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=f"{settings.API_PREFIX}/openapi.json",
            title=f"{settings.API_TITLE} - Swagger UI",
            oauth2_redirect_url=f"{settings.API_PREFIX}/docs/oauth2-redirect",
            swagger_js_url="/static/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger-ui.css",
        )
    
    # ReDoc 엔드포인트
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=f"{settings.API_PREFIX}/openapi.json",
            title=f"{settings.API_TITLE} - ReDoc",
            redoc_js_url="/static/redoc.standalone.js",
        )
    
    # OpenAPI JSON 엔드포인트
    @app.get(f"{settings.API_PREFIX}/openapi.json", include_in_schema=False)
    async def get_openapi_json():
        return JSONResponse(app.openapi())
    
    # OpenAPI YAML 엔드포인트
    @app.get(f"{settings.API_PREFIX}/openapi.yaml", include_in_schema=False)
    async def get_openapi_yaml():
        return JSONResponse(
            yaml.dump(app.openapi()),
            media_type="application/yaml"
        )

def generate_api_docs(output_dir: str = "docs") -> None:
    """API 문서 생성."""
    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # OpenAPI 스키마 가져오기
    schema = custom_openapi()
    
    # JSON 형식으로 저장
    with open(output_path / "openapi.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    
    # YAML 형식으로 저장
    with open(output_path / "openapi.yaml", "w", encoding="utf-8") as f:
        yaml.dump(schema, f, allow_unicode=True, sort_keys=False) 