import os
import time

import requests
import weaviate.embedded

from palantir.core.config import settings

WEAVIATE_PATH = os.path.join(os.getcwd(), "weaviate_data")

client = weaviate.embedded.WeaviateEmbedded(persistence_data_path=WEAVIATE_PATH)

if getattr(settings, "OFFLINE_MODE", False):
    print("[오프라인 모드] WCS 연결을 건너뜁니다. 로컬 Weaviate 인스턴스를 사용합니다.")
    weaviate_url = settings.WEAVIATE_URL
else:
    # 기존 WCS_URL, WCS_API_KEY 사용 로직
    weaviate_url = getattr(settings, "WEAVIATE_URL", "http://localhost:8080")

# 헬스체크 대기
for _ in range(30):
    try:
        r = requests.get(weaviate_url + "/v1/.well-known/ready", timeout=1)
        if r.status_code == 200:
            print("[OK] Weaviate ready")
            break
    except Exception:
        pass
    time.sleep(1)
else:
    print("[FAIL] Weaviate not ready after 30s")
    exit(1)
