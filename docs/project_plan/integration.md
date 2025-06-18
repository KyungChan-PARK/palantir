이제 Claude-Sonnet-3.5 모델이 Cursor 등에서 독립 파일로 실행할 수 있도록 전문 형태의 작업지시서를 총 6개 마크다운 파일로 분리해 작성하겠습니다. 각 지시서는 예시가 아닌 완성된 명령 형식으로 구성되며, 외부 참고가 필요한 경우 명확한 GitHub, Reddit, 블로그 링크를 명시합니다.

또한 현재 GitHub 리포지토리의 의존성 문제 및 설치 오류 가능성을 검토한 후, 가장 먼저 실행해야 할 '환경 구성 및 의존성 설치 검증' 작업지시서를 별도 작성하여 Claude가 정확히 시작할 수 있도록 안내하겠습니다. 이 과정이 완료되면 전체 작업지시서와 구조를 정리하여 전달드리겠습니다.


## 02\_aip\_integration.md

# 2. AIP 시스템 연동 및 벡터 검색 통합

**목적 및 개요:** Palantir 프로젝트에 외부 AI 서비스 연동 기반을 확인하고, 미비한 부분을 보강합니다. 구체적으로, **OpenAI 및 Anthropic 등의 LLM API 연동**이 제대로 구현되어 있는지 점검하고 없을 경우 구현하며, **벡터 데이터베이스(Pinecone 등)** 설정이 있는 경우 실제 **유사도 검색을 통한 컨텍스트 주입 기능**을 추가합니다. 이는 Palantir AIP 철학의 핵심인 *기업 데이터와 LLM의 결합*을 구현하는 작업으로서, 에이전트가 외부 LLM의 능력을 활용함과 동시에 **도메인 지식이 반영된 응답**을 할 수 있게 합니다.

**전체 실행 절차:**

1. **API 키 사용처 확인 및 LLM 호출 구현:** 먼저 `.env` 등 설정파일에 정의된 `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` 등이 **코드 내에서 실제로 사용되고 있는지** 검색합니다.

   * 프로젝트 전체를 대상으로 `"OPENAI_API_KEY"` 문자열을 검색하거나, OpenAI/Anthropic 라이브러리(`openai`, `anthropic` 등) 호출 부분을 찾습니다.
   * **미구현 시 조치:** 만약 API 키가 설정만 되어 있고 코드 어디에서도 해당 API를 호출하지 않는다면, **예시 구현**으로 OpenAI ChatCompletion API를 호출하는 함수를 작성합니다. 이를 위해 OpenAI의 Python SDK(`openai` 라이브러리)를 사용하여, 주어진 프롬프트를 모델(`gpt-3.5-turbo` 등)에 보내고 결과를 받아오는 유틸리티 함수를 프로젝트에 추가합니다. (Anthropic Claude API의 경우 `anthropic` 패키지를 사용하거나, HTTP 요청을 직접 구성할 수도 있습니다. Claude 통신도 비슷한 형태로 구현하되 openAI와 다른 엔드포인트/파라미터를 참고합니다.)
   * 구현한 함수는 프로젝트의 서비스 흐름에 통합합니다. 예컨대 사용자의 질문을 처리하는 부분이 있다면, 해당 질문을 위 새 함수를 통해 LLM에 전달하고 응답을 받아 답변 생성에 활용하도록 코드를 삽입합니다.
   * **이미 구현된 경우 점검:** 반대로, 이미 LLM 호출 로직이 있다면, **예외 처리**와 **타임아웃 설정**이 포함돼 있는지 확인합니다. 네트워크 통신이므로 타임아웃 없이 무기한 대기하지 않게 `timeout` 파라미터를 지정하고, `try/except`로 OpenAI API 에러(`openai.error.OpenAIError` 등)를 잡아 적절히 재시도하거나 오류 응답을 주도록 합니다.

2. **벡터 DB 연동 점검 및 컨텍스트 주입 기능 추가:** `.env`에 Pinecone 등 벡터 DB 설정 (`PINECONE_API_KEY`, `PINECONE_ENV`, `PINECONE_INDEX` 등)이 존재한다면, 코드 내에서 **벡터 임베딩 저장/검색 기능**이 구현되어 있는지 확인합니다.

   * **미구현 시 추가:** 만약 벡터 DB를 전혀 사용하고 있지 않다면, 다음과 같은 절차로 기능을 추가합니다:
     a. OpenAI Embedding API 등을 사용해 문서나 지식 베이스 문장을 **임베딩 벡터화**하고 Pinecone에 upsert하여 인덱스를 구축하는 초기 스크립트를 작성합니다. (프로젝트의 도메인 데이터가 있다면 그것을 임베딩하여 사전 색인)
     b. 사용자의 질의가 들어오면, 해당 질의를 임베딩하고 Pinecone에서 **유사도 검색**을 수행해 관련도가 높은 상위 문서를 찾습니다.
     c. 찾아낸 문서들을 LLM 프롬프트 맥락에 포함시켜, **도메인 컨텍스트가 반영된 답변**을 생성하도록 합니다.
     d. 이 흐름을 구현하기 위한 함수를 작성하고, 기존 Q\&A 흐름에 통합합니다. (예: `answer_query_with_context(question: str)` 함수를 구현하여, 내부에서 a, b, c 과정을 수행하고 OpenAI ChatCompletion으로 최종 답변 생성)
   * **이미 일부 연동된 경우:** 만약 Pinecone를 초기화하는 코드만 있고 실제 쿼리에는 쓰지 않는 경우, 위의 검색 및 사용 부분(c 단계)을 추가해 줍니다. 또는 임시로 **FAISS**와 같은 로컬 벡터 검색으로 대체할 수도 있습니다. (Pinecone 서비스를 사용하기 어려운 개발 환경이라면, `faiss` 라이브러리를 활용해 메모리 내 벡터 인덱스를 구축하는 것도 한 방법입니다.)

3. **통합 모듈화:** OpenAI 호출과 벡터 검색 기능을 구현했다면, 이를 **모듈화하여 관리**합니다. 예를 들어 `ai_integration.py` 모듈을 신설해 OpenAI API 호출 함수와 벡터DB 검색 함수를 넣고, 다른 부분에서는 이 모듈을 임포트하여 사용하도록 구조화합니다. 이렇게 하면 나중에 모델 제공자를 바꾸거나 (예: OpenAI -> Azure OpenAI) 벡터DB를 교체할 때 이 모듈만 수정하면 되어 유지보수가 수월합니다. 또한 API 키 로딩(`openai.api_key = ...`)도 이 초기화 부분에서 한 번만 설정하면 전체에서 공통으로 참조됩니다.

4. **API 응답 활용 로직 개선:** LLM에서 얻은 응답을 프로젝트 요구에 맞게 가공/검증합니다. 예를 들어 Palantir Foundry의 맥락에서는 **보안 및 필터링**이 중요한데, OpenAI 응답에 조직 정책에 어긋나는 내용이 없는지 검사하는 루틴을 추가하거나, 응답을 요약/정리하여 필요한 부분만 사용자에게 전달하는 후처리 코드를 넣습니다. 필요시 **모델 다중 활용** (예: OpenAI와 Anthropic 양쪽에 질의하고 결과를 비교한다거나, 하나의 응답을 다른 모델로 검증)을 고려할 수도 있습니다. 이러한 부분은 선택 사항이지만, Palantir AIP의 지향점(여러 모델을 상황에 맞게 조합 활용)에 부합하는 방향입니다.

### 📄 예시: OpenAI LLM 호출 및 Pinecone 벡터 검색 통합

다음 예시는 **OpenAI ChatCompletion API**를 호출하는 함수와 **Pinecone** 벡터DB를 사용한 임베딩 검색 함수를 구현한 코드입니다. 실제 프로젝트 환경에 맞게 API 키와 인덱스 등을 설정하여 사용할 수 있습니다. (Anthropic Claude API를 사용하는 경우, `anthropic` 라이브러리를 통해 비슷하게 호출하고 응답을 처리하는 함수를 작성하면 됩니다.)

```python
# ai_integration.py - OpenAI API call with error handling and Pinecone vector search

import os, openai, pinecone
from typing import List

# API 키 초기화 (환경변수에서 가져옴)
openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))

# Pinecone Index 객체 준비 (없는 경우 새로 생성)
index_name = "palantir-index"
if index_name not in pinecone.list_indexes():
    pinecone.create_index(index_name, dimension=1536)  # 예: text-embedding-ada-002 모델은 1536차원
index = pinecone.Index(index_name)

def get_embedding(text: str) -> List[float]:
    """주어진 텍스트에 대한 임베딩 벡터 생성 (OpenAI Embedding API 사용)"""
    try:
        # 임베딩 생성 (모델은 필요에 따라 변경 가능)
        result = openai.Embedding.create(model="text-embedding-ada-002", input=[text])
        embedding: List[float] = result["data"][0]["embedding"]
        return embedding
    except Exception as e:
        # 임베딩 생성 실패 시 예외 처리
        print(f"Embedding error: {e}")
        return []  # 오류 시 빈 리스트 반환

def query_similar_docs(query: str, top_k: int = 3) -> List[str]:
    """질의를 임베딩하여 Pinecone에서 top-k 유사한 문서를 검색"""
    emb = get_embedding(query)
    if not emb:
        return []
    try:
        # 벡터 유사도 검색 수행
        res = index.query(vector=emb, top_k=top_k, include_metadata=True)
        # 검색된 문서들의 텍스트 추출 (metadata에 'text' 필드가 담겨있다고 가정)
        similar_texts = [match['metadata']['text'] for match in res['matches']]
        return similar_texts
    except Exception as e:
        print(f"Vector search error: {e}")
        return []

def answer_query_with_context(query: str) -> str:
    """유사도 검색으로 문맥을 찾아 LLM에게 질의하여 답변 생성"""
    context_docs = query_similar_docs(query)
    # 시스템 메시지: 팔란티어 프로젝트 컨텍스트 (필요시 확장)
    system_prompt = (
        "You are an AI assistant for Palantir project. "
        "Answer the user's question using the context provided, if relevant."
    )
    # 사용자 메시지에 컨텍스트 문서 추가
    user_message = query
    if context_docs:
        context_text = "\n".join(context_docs)
        user_message = f"{query}\n\n[참고 문서]\n{context_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            timeout=10  # 응답 제한 시간 10초 설정
        )
        answer = response.choices[0].message["content"]
        return answer
    except openai.error.Timeout:
        return "Error: LLM response timed out."
    except openai.error.OpenAIError as oe:
        return f"Error: LLM API call failed ({oe})"
    except Exception as e:
        return f"Error: {e}"

# 단위 테스트 (예시): 문맥이 없을 때와 있을 때 함수 동작 확인
if __name__ == "__main__":
    test_q = "What is the purpose of the Palantir AIP Ontology SDK?"
    print("Answer without context:", answer_query_with_context("Hello?")[:30], "...")
    print("Answer with context:", answer_query_with_context(test_q)[:30], "...")
    # Expected: 첫 번째 출력은 일반적인 답변, 두 번째는 Palantir AIP Ontology 관련 문서 내용을 반영한 답변의 앞부분.
```

이 코드에서 `answer_query_with_context` 함수는 **벡터DB에서 관련 문서를 검색하여 프롬프트에 포함**하고, OpenAI의 ChatCompletion API로 최종 답변을 생성합니다. 예외 상황(타임아웃, API 오류 등)에 대비해 `try/except`로 처리하고 있습니다. Pinecone를 사용했지만, 로컬 환경에서는 **FAISS** 등으로 대체 구현할 수도 있습니다. 이러한 통합을 통해 팔란티어 에이전트가 사용자 질의에 프로젝트 **도메인 지식이 반영된 정확한 응답**을 제공할 수 있으며, Palantir AIP의 *데이터-LLM 밀결합* 철학을 실현하게 됩니다.

**오류 발생 시 대처:**

* **API 키 관련 오류:** OpenAI나 Anthropic 호출 시 `"Invalid API key"` 혹은 `"AuthenticationError"`가 발생하면, `.env`에 키가 정확히 설정되었는지, 코드에서 `openai.api_key` 등을 올바르게 셋업했는지 재확인합니다. Anthropic의 경우 환경변수 이름이나 불러오는 방법이 다를 수 있으므로 공식 문서를 참고해 구현합니다.
* **네트워크 타임아웃:** `Timeout` 에러 발생 시, `timeout` 값을 증가시키거나, 재시도 로직을 추가할 수 있습니다. 예를 들어 10초 내 응답이 없으면 한 번 더 시도하도록 `try` 블록을 이중으로 쓰거나, 백오프 전략을 적용합니다. 단, 너무 오랜 대기는 피해야 하므로 상한선을 정합니다.
* **Pinecone 관련 오류:** `pinecone.init` 단계에서 실패한다면 API 키나 환경 설정을 점검합니다. `pinecone.create_index`에서 권한 오류 또는 이미 존재하는 인덱스 관련 예외가 발생할 수 있으니, 인덱스 존재 여부를 체크한 후 생성하도록 코드에 반영했습니다. 벡터 검색(`index.query`)에서 잘못된 차원 오류가 발생하면, **임베딩 모델의 벡터 차원**과 **인덱스 생성 차원**이 일치하는지 확인해야 합니다 (예: text-embedding-ada-002는 1536차원이므로, 다른 모델을 쓰면 해당 차원으로 수정 필요). 이러한 설정값들은 `.env`나 상수로 관리하면 혼동을 줄일 수 있습니다.
* **요금/Rate-limit 관리:** OpenAI API는 속도 제한이 있으므로, 대량의 요청을 보낼 경우 `RateLimitError`가 날 수 있습니다. 이런 경우 **지수 백오프 재시도**, 또는 일정 횟수 이상 초과 시 대기 후 진행하는 로직을 추가합니다. 또한 Anthropic API도 토큰 사용량에 따라 지연이 있을 수 있으므로, 한 요청에 너무 많은 컨텍스트를 보내지 않도록 `user_message` 구성 시 문맥 문서 개수(`top_k`)나 길이를 적절히 제한합니다.

위 개선 작업을 통해 **AIP 시스템 연동**이 강화되었다면, 이제 프로젝트의 AI 에이전트가 외부 LLM의 능력을 활용하면서도 자체 데이터 지식을 응용할 수 있게 됩니다. 다음 단계에서는 **오케스트레이션 시스템**을 구현하여 멀티에이전트 협업 구조를 구축합니다.

---
