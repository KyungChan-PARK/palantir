import os
import shutil
from sentence_transformers import SentenceTransformer
import nltk
# import spacy # Spacy 모델이 필요하고 식별된 경우 주석 해제

# 이 스크립트가 있는 디렉토리를 기준으로 오프라인 자산의 기본 디렉토리 정의
OFFLINE_PREPARATION_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODELS_RESOURCES_DIR = os.path.join(OFFLINE_PREPARATION_DIR, "ml_models_and_resources")

os.makedirs(ML_MODELS_RESOURCES_DIR, exist_ok=True)

print(f"--- ML 자산 다운로드 시작: {ML_MODELS_RESOURCES_DIR} ---")

# Hugging Face가 이 디렉토리를 캐싱에 사용하도록 환경 변수 설정
os.environ['HF_HOME'] = ML_MODELS_RESOURCES_DIR
os.environ['TRANSFORMERS_CACHE'] = ML_MODELS_RESOURCES_DIR
# sentence-transformers와 같은 일부 라이브러리는 자체 cache_folder 매개변수를 가질 수 있음

# 1. Sentence Transformers 모델
embedding_model_name = "sentence-transformers/all-mpnet-base-v2"
print(f"Sentence Transformer 모델 다운로드/캐싱 중: {embedding_model_name}...")
try:
    # cache_folder는 정의된 구조 내에 저장하려고 시도합니다.
    model = SentenceTransformer(embedding_model_name, cache_folder=ML_MODELS_RESOURCES_DIR)
    print(f"{embedding_model_name} 처리 완료. {ML_MODELS_RESOURCES_DIR} 내에 있는지 확인하십시오.")
except Exception as e:
    print(f"Sentence Transformer 모델 {embedding_model_name} 다운로드 중 오류: {e}")

# 2. NLTK 데이터
nltk_data_path = os.path.join(ML_MODELS_RESOURCES_DIR, "nltk_data")
os.makedirs(nltk_data_path, exist_ok=True)
print(f"NLTK 리소스 다운로드 중: {nltk_data_path}...")
try:
    nltk.download('punkt', download_dir=nltk_data_path)
    nltk.download('averaged_perceptron_tagger', download_dir=nltk_data_path)
    print("NLTK 리소스 다운로드 완료.")
except Exception as e:
    print(f"NLTK 리소스 다운로드 중 오류: {e}")

# 3. Spacy 모델 (예시 - 특정 모델이 식별되면 주석 해제 및 수정)
# spacy_model_name = "en_core_web_sm" # 실제 모델로 교체 (예: en_core_web_lg)
# print(f"Spacy 모델 다운로드 중: {spacy_model_name}...")
# try:
#   spacy_models_download_path = os.path.join(ML_MODELS_RESOURCES_DIR, "spacy_models_download")
#   os.makedirs(spacy_models_download_path, exist_ok=True)
#   import spacy.cli
#   spacy.cli.download(spacy_model_name, False, False, "--target", spacy_models_download_path)
#   print(f"Spacy 모델 {spacy_model_name}이(가) {spacy_models_download_path}에 다운로드되었습니다.")
#   print(f"오프라인 환경에서 이 경로의 모델을 사용하도록 Spacy를 설정하거나, 모델을 적절한 위치로 옮기십시오.")
# except Exception as e:
#   print(f"Spacy 모델 {spacy_model_name} 자동 다운로드 실패: {e}")
#   print(f"온라인 환경에서 수동으로 다운로드하십시오 (예: python -m spacy download {spacy_model_name}).")
#   print(f"그런 다음 모델 디렉토리(예: .../site-packages/{spacy_model_name})를 {ML_MODELS_RESOURCES_DIR}/spacy_models/ 내로 복사하십시오.")

print("\n--- ML 자산 다운로드 스크립트 완료 ---")
print(f"모든 다운로드된 자산은 다음 하위 디렉토리에 있어야 합니다: {ML_MODELS_RESOURCES_DIR}")
print(f"샌드박스 환경으로 './offline_preparation/' 내의 '{os.path.basename(ML_MODELS_RESOURCES_DIR)}' 디렉토리 전체를 전송해야 합니다.")
print("다음으로, 애플리케이션이 이러한 로컬 경로/캐시를 사용하도록 구성하십시오.") 