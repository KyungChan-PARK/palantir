# 오프라인 Python 패키지 설치 가이드

네트워크가 차단된 환경에서 Python 의존성을 설치하려면 다음 단계를 따르십시오.

1.  오프라인 환경에 Python과 pip가 설치되어 있는지 확인하십시오.
2.  전체 `offline_preparation/python_packages` 디렉토리를 오프라인 환경으로 전송하십시오.
3.  오프라인 환경의 프로젝트 루트 디렉토리에서 터미널을 여십시오.

4.  메인 애플리케이션 의존성 설치:
    ```bash
    pip install --no-index --find-links=./offline_preparation/python_packages/main_app_packages -r requirements.txt
    ```

5.  pipeline_ui 애플리케이션 의존성 설치:
    ```bash
    pip install --no-index --find-links=./offline_preparation/python_packages/pipeline_ui_packages -r pipeline_ui/requirements.txt
    ``` 