# 오프라인 Docker 이미지 로딩 가이드

네트워크가 차단된 환경에서 Docker 이미지를 로드하려면 다음 단계를 따르십시오.

1.  오프라인 환경에 Docker가 설치되어 있는지 확인하십시오.
2.  전체 `offline_preparation/docker_images` 디렉토리를 오프라인 환경으로 전송하십시오.
3.  오프라인 환경의 프로젝트 루트 디렉토리 (또는 `docker_images` 폴더를 위치시킨 곳)에서 터미널을 여십시오.

4.  이미지 로드:
    ```bash
    docker load -i ./offline_preparation/docker_images/grafana_loki_2.8.0.tar
    docker load -i ./offline_preparation/docker_images/grafana_promtail_2.8.0.tar
    # 추가로 저장한 이미지가 있다면 여기에 추가
    ```

5.  이미지가 로드되면, YAML 파일의 `image:` 태그가 로드된 이미지와 일치한다고 가정할 때, 네트워크 연결 없이 `docker-compose -f docker-compose.loki.yaml up -d` (또는 유사한 명령어)를 실행할 수 있어야 합니다. 