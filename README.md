# Palantir AI Platform

자세한 개발자 안내서는 **[DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md)** 를 참고하세요.

- 시스템 아키텍처 다이어그램은 `docker-compose.yml`을 기반으로 자동 생성됩니다.
- 최신 다이어그램을 생성하려면: `poetry run python scripts/generate_architecture_diagram.py`

### User Interface
본 프로젝트의 메인 UI는 Reflex 프레임워크를 기반으로 하며, `apps/reflex_ui` 디렉토리에서 관리됩니다. 모든 핵심 기능(데이터 탐색, 파이프라인 빌드, 모니터링)은 Reflex UI를 통해 제공됩니다. 초기 프로토타입으로 개발되었던 Streamlit UI는 `archive/streamlit_ui`에 보관되어 있습니다.
