import weaviate.embedded
import time
import requests
import os

WEAVIATE_PATH = os.path.join(os.getcwd(), "weaviate_data")

client = weaviate.embedded.WeaviateEmbedded(persistence_data_path=WEAVIATE_PATH)

# 헬스체크 대기
for _ in range(30):
    try:
        r = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=1)
        if r.status_code == 200:
            print("[OK] Weaviate ready")
            break
    except Exception:
        pass
    time.sleep(1)
else:
    print("[FAIL] Weaviate not ready after 30s")
    exit(1) 