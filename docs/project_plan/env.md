이제 Claude-Sonnet-3.5 모델이 Cursor 등에서 독립 파일로 실행할 수 있도록 전문 형태의 작업지시서를 총 6개 마크다운 파일로 분리해 작성하겠습니다. 각 지시서는 예시가 아닌 완성된 명령 형식으로 구성되며, 외부 참고가 필요한 경우 명확한 GitHub, Reddit, 블로그 링크를 명시합니다.

또한 현재 GitHub 리포지토리의 의존성 문제 및 설치 오류 가능성을 검토한 후, 가장 먼저 실행해야 할 '환경 구성 및 의존성 설치 검증' 작업지시서를 별도 작성하여 Claude가 정확히 시작할 수 있도록 안내하겠습니다. 이 과정이 완료되면 전체 작업지시서와 구조를 정리하여 전달드리겠습니다.


## 00\_initialize\_env.md

# 0. 개발 환경 초기화 및 설정

**목적 및 개요:** 이 단계에서는 Palantir 프로젝트를 실행하기 위한 **개발 환경을 구축**하고 **필요한 의존성**을 정확히 설치합니다. Claude-Sonnet-3.5 기반 AI 에이전트가 코드 실행이나 문서 편집 등을 수행하기 전에, 환경 설정과 라이브러리 설치, API 키 설정 등이 제대로 되어야 오류 없이 진행될 수 있습니다. 또한 `.env` 파일 등의 **환경변수 설정**을 점검하여, **OpenAI/Anthropic API 키** 등 **외부 서비스 연동 정보가 누락되지 않았는지** 확인합니다. 이 준비 단계를 통해 이후 작업들이 원활히 이루어지도록 합니다.

**전체 실행 절차:**

1. **리포지토리 클론 및 Python 버전 확인:** 프로젝트 저장소(`KyungChan-PARK/palantir`)를 로컬에 클론합니다. Python 3.10 이상 (CI 테스트 기준 Python 3.13) 버전이 설치되어 있는지 확인합니다.

   ```bash
   # GitHub 저장소 클론 (SSH 또는 HTTPS)
   git clone git@github.com:KyungChan-PARK/palantir.git
   cd palantir
   python --version  # Python 3.10+ 확인
   ```

   * 만약 Python 최신 버전 사용 시 호환성 문제(예: 특정 라이브러리 설치 오류)가 있다면, Python 3.10\~3.11 버전을 권장합니다. Python 버전이 올바르게 설치되어 있다면 다음 단계로 진행합니다.

2. **가상환경 생성 및 활성화:** 프로젝트 전용의 virtualenv(또는 Conda 환경)를 만듭니다. 이를 통해 의존성 격리를 유지하고 시스템 Python에 영향을 주지 않습니다.

   ```bash
   python -m venv .venv  # 가상환경 생성
   source .venv/bin/activate  # 가상환경 활성화 (Windows의 경우 .venv\Scripts\activate)
   python -m pip install --upgrade pip setuptools  # 최신 pip/세트업툴로 업그레이드
   ```

   * **Windows:** 위 명령에서 가상환경 활성화는 `.\.venv\Scripts\activate` 형식으로 실행하십시오.
   * **오류 대비:** 가상환경 활성화 후 `python` 명령이 올바른 버전을 가리키는지 (`which python` 또는 `where python`으로) 확인합니다. Pip 업그레이드 시 권한 문제나 버전 충돌이 있으면 관리자 권한으로 실행하거나 `--user` 옵션을 사용합니다.

3. **프로젝트 의존성 설치:** 프로젝트 디렉토리에 **`requirements.txt`** 또는 **`pyproject.toml`**/`poetry.lock`이 있는지 확인합니다.

   * `requirements.txt`가 있다면 다음을 실행합니다.

     ```bash
     pip install -r requirements.txt
     ```
   * Poetry를 사용하는 경우(`pyproject.toml` 존재)라면 다음을 실행합니다.

     ```bash
     pip install poetry  # Poetry 미설치 시
     poetry install
     ```

   설치가 완료되면 `pip check` 명령으로 **의존성 충돌 여부**를 확인합니다.

   ```bash
   pip check  # 설치된 패키지 간 충돌 여부 검사
   ```

   * **의존성 버전 일관성:** 만약 프로젝트에 `requirements.txt`와 `pyproject.toml`가 모두 존재한다면, 두 곳의 라이브러리 목록과 버전이 서로 어긋나지 않는지 검토합니다. (예: requirements에만 있고 pyproject에는 없는 패키지가 없는지 등) 필요시 하나의 기준으로 통일하고 재설치를 수행합니다.
   * **pip 관련 오류 대응:** `pip install` 중 특정 패키지에서 버전 호환 문제나 빌드 에러가 발생하면, 에러 메시지에 따라 패키지 버전을 조정하거나 `pip install --upgrade <패키지명>`으로 새 버전을 시도합니다. 또한 pip 자체가 오래되어 발생하는 오류는 `python -m pip install --upgrade pip`로 최신화하여 해결합니다.

4. **환경변수 설정 (.env 파일 구성):** 프로젝트 루트에 **`.env`** 파일을 준비하고 필요한 키들을 설정합니다. 레포지토리에 `.env.example` 또는 `env.template` 파일이 있다면 그것을 복사해 사용할 수 있습니다.
   주요 환경변수 항목 (예시):

   ```dotenv
   OPENAI_API_KEY=<YOUR_OPENAI_API_KEY>         # OpenAI API 키
   ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_API_KEY>   # Anthropic Claude API 키
   PINECONE_API_KEY=<YOUR_PINECONE_API_KEY>     # Pinecone 벡터 DB API 키
   PINECONE_ENV=<YOUR_PINECONE_ENVIRONMENT>     # Pinecone 환경(e.g., "us-west4-gcp")
   PINECONE_INDEX=palantir-index                # Pinecone에서 사용할 인덱스 이름
   AIGC_ADMIN_SERVER_HTTP_PORT=:8080            # (예시) 서비스 포트 설정 (기본 8080)
   AIGC_ADMIN_SERVER_ADMIN_USER=admin           # 초기 관리자 계정명 (최초 DB 초기화 시만 사용)
   AIGC_ADMIN_SERVER_ADMIN_PASS=admin           # 초기 관리자 비밀번호 (동일, 이후 변경 시에는 DB 직접 수정)
   ```

   * **API 키 설정:** OpenAI, Anthropic 등 외부 API 키는 실제 값으로 채워넣습니다. 이 값들이 올바르게 설정되지 않으면 이후 LLM 호출 단계에서 인증 오류가 발생하므로 주의합니다.
   * **벡터 DB 설정:** Pinecone을 사용할 경우 API 키 외에 환경(`PINECONE_ENV`)과 인덱스 이름(`PINECONE_INDEX`)도 프로젝트에 맞게 설정합니다. 만약 Pinecone 서비스를 사용하지 않거나 대안을 쓸 계획이라면, 관련 변수를 비워두고 코드에서 해당 기능을 비활성화하거나 FAISS 등의 로컬 대안을 활용합니다.
   * **포트 및 기타 설정:** 기본 API 서비스 포트는 8080으로 설정되어 있습니다. 다른 프로세스와 충돌 시 `AIGC_ADMIN_SERVER_HTTP_PORT` 값을 변경할 수 있습니다 (예: `:8081`). **주의:** 일부 환경변수의 경우 (예: `AIGC_ADMIN_SERVER_ADMIN_USER/PASS`) **초기 1회에만 적용**됩니다. 해당 값으로 애플리케이션 첫 실행 시 관리자 계정을 생성한 후에는 `.env`를 바꿔도 기존 계정에 영향이 없으니, 필요한 경우 애플리케이션 내에서 계정을 변경하거나 DB를 수정해야 합니다.
   * **DB 구성:** 기본 설정상 별도의 DB 설정을 하지 않으면 SQLite를 사용하도록 되어 있을 가능성이 높습니다. 예컨대 `AIGC_DB_DRIVER` 등의 값이 지정되지 않으면 프로젝트는 `./storage/database/aigc.db` 경로에 SQLite 파일을 생성해 사용할 수 있습니다. **MySQL 등 다른 DB를 사용하려면**, `.env`에 제공된 `AIGC_MYSQL_HOST`, `AIGC_MYSQL_USER` 등 정보를 채우고 해당 DB 인스턴스가 실행 중이어야 합니다. DB 설정을 변경한 경우, `.env`의 `AIGC_DB_DRIVER` 또는 관련 변수를 정확히 지정해야 하며, 필요한 초기 테이블을 생성하는 마이그레이션 절차가 README나 설치 문서에 있는지 확인합니다.

5. **Docker/Compose 설정 (선택 사항):** 이 프로젝트에는 **Docker 지원**이 포함되어 있습니다. 로컬 환경 대신 Docker 컨테이너로 실행하려면, 먼저 Docker Desktop 등을 설치/실행하고 아래 명령을 사용합니다.

   ```bash
   docker-compose up --build -d
   ```

   이 명령은 관련 이미지들을 빌드하고 백그라운드에서 컨테이너를 실행합니다. Compose는 프로젝트 루트의 `.env` 파일을 자동으로 참조하므로, 앞서 설정한 API 키와 설정이 컨테이너 내에 적용됩니다.

   * **Compose 구성 검토:** `docker-compose.yml` 파일을 열어 **포트 매핑**, **환경변수 적용 여부**, **의존 서비스 (예: DB)** 등을 확인합니다. 예를 들어 FastAPI 웹서비스 컨테이너의 `ports` 섹션이 `"8080:8080"`으로 호스트에 노출되는지, `.env`의 키들이 `environment` 섹션이나 `env_file`로 참조되고 있는지 점검하십시오. 필요에 따라 docker-compose.yml에 환경변수 참조를 추가하거나, Dockerfile에 미설치된 OS 패키지(Tesseract 등)가 있다면 이미지를 수정해 설치하도록 합니다.
   * **Docker 이미지 빌드 오류:** Docker build 과정에서 실패한다면 에러 로그를 확인합니다. 예를 들어 특정 Python 패키지 빌드에 system 라이브러리가 필요하면 Dockerfile에 해당 라이브러리 설치를 추가해야 할 수 있습니다. BuildKit을 비활성화하고 (`DOCKER_BUILDKIT=0`) 빌드하면 상세 로그를 볼 수 있습니다.

6. **테스트 서버 실행 및 확인:** Docker를 사용하지 않는 경우, 가상환경이 활성화된 상태에서 **FastAPI 서버**를 직접 실행합니다. 일반적으로 프로젝트에는 실행 스크립트(`run.py` 등)나 진입점 모듈이 있으며, 없을 경우 아래와 같이 uvicorn으로 직접 기동 가능합니다.

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

   위 명령에서 `app.main:app` 부분은 FastAPI 앱 객체(`app`)가 정의된 모듈 경로입니다. 실제 프로젝트 구조에 따라 `main:app` 또는 `palantir.main:app` 등으로 변경해야 할 수 있습니다. **프로젝트 README**나 `uvicorn` 관련 스크립트를 확인하여 올바른 모듈 경로를 사용합니다.

   * 서버가 정상적으로 기동되면 터미널에 "**Uvicorn running on [http://0.0.0.0:8080](http://0.0.0.0:8080)**" 등의 출력이 나타납니다. 웹 브라우저 또는 API 클라이언트로 `http://localhost:8080/docs` (FastAPI Swagger UI)나 `http://localhost:8080/health` (건강 체크 엔드포인트가 있는 경우) 등에 접속해 응답을 확인합니다.
   * **초기 데이터 로드/마이그레이션:** 서버 실행 시 데이터베이스나 기타 초기 리소스 세팅이 필요하다면, 프로젝트 문서를 참고하여 해당 절차를 수행합니다. 예를 들어 DB 마이그레이션 도구(Alembic 등)를 사용하는 경우 `alembic upgrade head` 명령을, 또는 `make init_db`와 같은 커맨드를 실행해야 할 수 있습니다. 이러한 절차 없이도 기본 동작에 문제가 없다면 곧바로 API 호출 테스트를 진행해 봅니다.

7. **환경 설정 검증 (테스트 실행 등):** 환경 구성이 제대로 되었는지 확인하기 위해 **테스트**를 실행해 봅니다. 이 프로젝트는 테스트 커버리지 92% 이상으로 관리되고 있으므로, 테스트를 돌려보아 대부분 통과하면 설정이 정상임을 확인할 수 있습니다.

   ```bash
   pytest   # 또는 'make test' 등 프로젝트에서 제공하는 테스트 실행 커맨드
   ```

   모든 테스트가 통과하거나, 적어도 환경설정과 무관한 일부 테스트만 실패한다면 일단 준비 완료입니다. 테스트 실패 시 실패한 테스트의 오류 메시지를 분석해 **환경 변수 누락**, **의존성 버전 문제**, **외부 API 키 문제** 등이 아닌지 확인합니다. 예를 들어 OpenAI API 호출 테스트가 실패하면 API 키 설정을 다시 확인해야 하고, DB 관련 테스트 실패는 DB 마이그레이션이나 초기 데이터 누락을 의심해볼 수 있습니다.

**외부 참고 자료 및 추가 고려사항:**

* **포트 충돌 문제:** `Address already in use` 오류로 서버 실행이 안 될 경우, 8080 포트를 사용하는 다른 프로세스를 종료하거나, 위에서 설명한 대로 `.env` 또는 uvicorn `--port` 인자를 통해 다른 포트로 변경하십시오. 포트 변경 후에는 API 요청 시 해당 포트를 사용해야 합니다.
* **Tesseract OCR 설정:** 프로젝트에서 Tesseract OCR을 사용한다면, 로컬 환경에 Tesseract가 설치되어 있어야 합니다. Ubuntu 계열에서는 `sudo apt-get install -y tesseract-ocr`, Mac에서는 `brew install tesseract` 명령으로 설치합니다. 설치 후 `pytesseract.pytesseract.tesseract_cmd` 경로나 PATH 설정이 필요할 수 있으니, 첫 OCR 기능 사용 시 오류가 나타나면 해당 오류 메시지에 따라 경로를 잡아줍니다. Docker 사용 시에는 Docker 이미지에 이미 Tesseract가 포함되어 있거나, Dockerfile에 설치 커맨드를 추가해야 합니다.
* **의존성 충돌 및 버전:** 만약 설치 후 애플리케이션 실행 시 ImportError나 VersionMismatch 오류가 발생하면, 해당 모듈의 버전이 잘못 설치된 것일 수 있습니다. `pip freeze`로 설치된 버전 목록을 점검하고, 필요에 따라 특정 버전을 재설치하거나 제거(`pip uninstall`) 후 다른 버전을 설치합니다. 특히 `torch`, `tensorflow` 등의 대형 라이브러리는 시스템에 따라 설치가 달라질 수 있으니 주의합니다.
* **Makefile/스크립트 활용:** 프로젝트에 `Makefile`이나 `setup.sh` 등이 있다면, 문서를 열어 어떤 초기화 작업을 자동화하는지 확인합니다. 예를 들어 `make setup`이나 `bash setup.sh`가 가상환경 생성부터 의존성 설치, .env 템플릿 생성까지 해주는지 살펴보고, 그런 명령이 있다면 수동 단계를 대신하여 활용할 수 있습니다. 다만, 이러한 스크립트가 모든 케이스를 다루지 못할 수 있으므로 (예: OS 별 처리 누락), 오류 발생 시 스크립트 내용을 참고하여 수동으로 보완하십시오.

이상의 환경 설정 단계를 완료함으로써 **개발 및 실행 환경**이 준비되었습니다. 이제 Claude-Sonnet-3.5 에이전트가 이 환경에서 코드 수정, 서버 실행 등의 작업을 수행할 수 있습니다. 다음 단계로 넘어가 프로젝트 **문서 정리 및 동기화 작업**을 진행합니다.

---








