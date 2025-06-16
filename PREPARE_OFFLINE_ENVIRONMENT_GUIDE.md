# 오프라인 환경 준비 및 애플리케이션 구성 가이드

이 가이드는 AI 에이전트가 생성한 오프라인 자산을 사용하여 네트워크가 차단된 샌드박스 환경에서 프로젝트를 설정하는 방법을 안내합니다.

## 1단계: 오프라인 자산 전송

AI 에이전트가 생성한 `./offline_preparation/` 디렉토리의 내용을 오프라인 샌드박스 환경의 프로젝트 루트로 전송하십시오. 전송 후 오프라인 환경의 프로젝트 구조는 다음과 같아야 합니다:

```
<project_root>/
├── offline_preparation/
│   ├── python_packages/
│   │   ├── main_app_packages/
│   │   └── pipeline_ui_packages/
│   ├── docker_images/
│   │   ├── grafana_loki_2.8.0.tar
│   │   └── grafana_promtail_2.8.0.tar
│   ├── ml_models_and_resources/
│   │   ├── nltk_data/
│   │   └── ... (기타 모델 파일 및 캐시)
│   ├── INSTALL_PYTHON_PACKAGES_OFFLINE.md
│   ├── LOAD_DOCKER_IMAGES_OFFLINE.md
│   └── download_ml_assets.py  (이 스크립트는 온라인 환경에서 이미 실행되었어야 함)
├── palantir/
├── pipeline_ui/
├── ... (기타 프로젝트 파일)
└── PREPARE_OFFLINE_ENVIRONMENT_GUIDE.md (현재 파일)
```

**참고:** `./offline_preparation/download_ml_assets.py` 스크립트는 이 단계 이전에 **온라인 환경에서 실행**되어 `ml_models_and_resources` 디렉토리를 채웠어야 합니다.

## 2단계: Python 의존성 설치 (오프라인)

`./offline_preparation/INSTALL_PYTHON_PACKAGES_OFFLINE.md` 파일의 지침에 따라 오프라인 환경에 Python 패키지를 설치하십시오.

## 3단계: Docker 이미지 로드 (오프라인)

`./offline_preparation/LOAD_DOCKER_IMAGES_OFFLINE.md` 파일의 지침에 따라 오프라인 환경에 Docker 이미지를 로드하십시오.

## 4단계: 머신러닝 모델 및 리소스 사용 설정 (오프라인)

오프라인 환경에서 애플리케이션이 로컬에 저장된 ML 모델과 리소스를 사용하도록 다음 환경 변수를 설정하십시오. 터미널에서 직접 설정하거나, 애플리케이션 실행 스크립트에 추가하거나, `.env` 파일을 통해 설정할 수 있습니다.

```bash
# 프로젝트 루트 디렉토리의 실제 경로로 /path/to/your/project/를 교체하십시오.
# Hugging Face 모델 (sentence-transformers, transformers 등에서 사용)
export HF_HOME="/path/to/your/project/offline_preparation/ml_models_and_resources"
export TRANSFORMERS_CACHE="/path/to/your/project/offline_preparation/ml_models_and_resources"

# NLTK 데이터
export NLTK_DATA="/path/to/your/project/offline_preparation/ml_models_and_resources/nltk_data"

# Spacy 모델 (ml_models_and_resources/spacy_models/ 와 같이 특정 하위 폴더에 다운로드한 경우)
# export SPACY_MODELS_DIR="/path/to/your/project/offline_preparation/ml_models_and_resources/spacy_models"
# 애플리케이션 코드에서 spacy.load(os.environ.get("SPACY_MODELS_DIR") + "/en_core_web_sm_version") 와 같이 사용
```

**코드/구성 수정 확인 (필요한 경우):**

* **임베딩 모델 (`palantir/core/config.py`):**
    위에서 `HF_HOME`/`TRANSFORMERS_CACHE`를 설정하면 `sentence-transformers`가 캐시된 모델을 자동으로 찾아야 합니다.
    만약 `download_ml_assets.py` 스크립트에서 `model.save()`를 사용하여 특정 경로(예: `ml_models_and_resources/my_specific_st_model_v2`)에 모델을 저장했다면, `palantir/core/config.py`의 `DEFAULT_EMBEDDING_MODEL`을 이 로컬 경로로 업데이트해야 할 수 있습니다:
    `DEFAULT_EMBEDDING_MODEL = "/path/to/your/project/offline_preparation/ml_models_and_resources/my_specific_st_model_v2"`
    그러나 캐시 환경 변수에 의존하는 것이 일반적으로 더 선호됩니다.

* **NLTK:** `NLTK_DATA` 환경 변수 설정으로 충분해야 합니다.

* **Spacy:** Spacy 모델을 사용하고 특정 경로에 다운로드한 경우, 코드가 해당 경로에서 모델을 로드하는지 확인하십시오 (예: `nlp = spacy.load("/path/to/your/project/offline_preparation/ml_models_and_resources/spacy_models/en_core_web_sm/en_core_web_sm-3.X.X")`).

**확인:** 환경 변수를 설정하고 필요한 코드 변경을 수행한 후, 오프라인 환경의 Python 인터프리터에서 모델 로더를 인스턴스화하여 네트워크 호출 없이 올바르게 로드되는지 확인합니다. 예:
`from sentence_transformers import SentenceTransformer`
`model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2") # 캐시에서 로드되어야 함`
`import nltk`
`nltk.word_tokenize("test sentence") # 로컬 'punkt'를 사용해야 함`

## 5단계: 오프라인 애플리케이션 운영을 위한 구성

외부 API 호출을 비활성화하거나 재라우팅해야 합니다.

1.  **`palantir/core/config.py` 수정:**
    다음 설정을 `Settings` 클래스 내에 추가하거나 기존 설정을 수정합니다.

    ```python
    # Settings 클래스 내에 추가:
    OFFLINE_MODE: bool = os.getenv("OFFLINE_MODE", "False").lower() == "true"
    LOCAL_MODELS_PATH: Optional[str] = os.getenv("LOCAL_MODELS_PATH", None) # HF_HOME/TRANSFORMERS_CACHE 대신 명시적 경로용
    ```

2.  **OpenAI API 사용 (`palantir/core/llm_manager.py`, `palantir/core/transpiler.py` 등):**
    `settings.OFFLINE_MODE`가 `True`일 때 OpenAI API 호출을 건너뛰거나 모의(mock) 응답을 반환하도록 관련 함수를 수정합니다.
    예시 (`palantir/core/llm_manager.py` 내):
    ```python
    # from ..core.config import settings # 이미 import 되어 있을 수 있음
    # ... 함수 내에서 ...
    # if settings.LLM_PROVIDER.lower() == "openai" and settings.OFFLINE_MODE:
    #     logger.warning("OpenAI API 호출이 오프라인 모드에서 건너뛰어졌습니다.")
    #     return "OpenAI 기능은 오프라인 모드에서 비활성화되었습니다." # 또는 적절한 모의 응답/예외 처리
    ```
    또는 사용자가 `.env` 파일에서 `LLM_PROVIDER`를 `openai`가 아닌 다른 값(예: `local_llm`)으로 설정하도록 안내하고, 해당 제공자에 대한 로컬 로직을 구현하거나 기능을 제한합니다.

3.  **Weaviate 구성 (`weaviate_boot.py`, `palantir/core/config.py`):**
    `settings.OFFLINE_MODE`가 `True`일 때 Weaviate Cloud Service (WCS) 대신 로컬 Weaviate 인스턴스를 사용하도록 합니다.
    `palantir/core/config.py`에서 `WEAVIATE_URL`이 로컬 인스턴스(예: `http://localhost:8080`)를 가리키도록 기본값을 설정하거나 `.env`에서 설정 가능하도록 합니다.
    `weaviate_boot.py`에서 WCS 관련 로직(`WCS_URL`, `WCS_API_KEY` 사용)이 `settings.OFFLINE_MODE`가 `True`일 때는 실행되지 않도록 수정합니다.

4.  **`.env` 파일 생성/업데이트 (오프라인 환경용):**
    오프라인 환경의 프로젝트 루트에 다음 내용으로 `.env` 파일을 생성하거나 업데이트하도록 사용자에게 안내합니다:

    ```env
    # 일반 오프라인 설정
    OFFLINE_MODE=True

    # LLM 구성 (OpenAI 호출을 피하기 위해)
    LLM_PROVIDER="local_mock" # 또는 'openai'가 아닌 다른 값. 로컬 LLM을 사용하는 경우 해당 설정.
    # OPENAI_API_KEY= # LLM_PROVIDER가 'openai'가 아니면 비워두거나 제거

    # Weaviate 구성 (로컬/도커화된 Weaviate를 가리키도록)
    WEAVIATE_URL="http://localhost:8080" # 로컬 Weaviate 엔드포인트
    # WCS_URL= # 비워두거나 제거
    # WCS_API_KEY= # 비워두거나 제거

    # 모델 캐시 경로 (쉘 환경 변수로 설정했다면 중복될 수 있지만, 앱이 읽는다면 명시성을 위해 사용 가능)
    # HF_HOME="./offline_preparation/ml_models_and_resources" # 프로젝트 루트 기준 상대 경로
    # TRANSFORMERS_CACHE="./offline_preparation/ml_models_and_resources"
    # NLTK_DATA="./offline_preparation/ml_models_and_resources/nltk_data"
    # LOCAL_MODELS_PATH="./offline_preparation/ml_models_and_resources" # 명시적 경로 설정 예시
    ```

## 6단계: 애플리케이션 실행 (오프라인)

위의 모든 설정이 완료되면, 오프라인 환경에서 애플리케이션을 시작합니다. 로그를 확인하여 네트워크 오류 없이 정상적으로 실행되는지, 모델이 로컬 경로에서 로드되는지 확인합니다. 