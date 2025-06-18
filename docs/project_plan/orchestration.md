이제 Claude-Sonnet-3.5 모델이 Cursor 등에서 독립 파일로 실행할 수 있도록 전문 형태의 작업지시서를 총 6개 마크다운 파일로 분리해 작성하겠습니다. 각 지시서는 예시가 아닌 완성된 명령 형식으로 구성되며, 외부 참고가 필요한 경우 명확한 GitHub, Reddit, 블로그 링크를 명시합니다.

또한 현재 GitHub 리포지토리의 의존성 문제 및 설치 오류 가능성을 검토한 후, 가장 먼저 실행해야 할 '환경 구성 및 의존성 설치 검증' 작업지시서를 별도 작성하여 Claude가 정확히 시작할 수 있도록 안내하겠습니다. 이 과정이 완료되면 전체 작업지시서와 구조를 정리하여 전달드리겠습니다.


## 03\_orchestration.md

# 3. 오케스트레이션 클래스 구현 및 멀티에이전트 병렬 실행

**목적 및 개요:** 기존에는 하나의 AI 에이전트가 주어진 작업을 **순차적으로 단독 수행**했다면, 이제 여러 에이전트가 **병렬 협업**할 수 있는 오케스트레이션 프레임워크를 구현합니다. 중앙에 **Orchestrator** 클래스(또는 모듈)를 두어 작업들을 조정하며, 각 에이전트는 역할을 분담하여 동시에 일을 처리합니다. 예를 들어 **Planner**, **Executor**, **Validator**, **Documenter**와 같은 전문 에이전트를 두고, Orchestrator가 이들을 지휘하여 **병렬 처리**와 **교차 검증**을 가능하게 합니다. 이를 통해 작업 처리 속도를 높이고 품질을 향상시키는 것이 목표입니다. (실제 개발 사례로, Reddit 커뮤니티의 한 프로젝트에서는 4개의 Claude 에이전트를 병렬 활용해 **4배 이상의 개발 속도 향상**을 보고하기도 했습니다.)

**전체 실행 절차:**

1. **Orchestrator 클래스 생성:** 오케스트레이션의 핵심은 **중앙 관리자로서의 Orchestrator**입니다. Orchestrator는 내부에 작업 \*\*대기열(queue)\*\*과 에이전트 \*\*풀(pool)\*\*을 관리하며, 각 작업을 어떤 에이전트에게 보낼지 결정합니다.

   * Python 표준 라이브러리의 `threading.Thread`를 활용해 각 에이전트를 스레드로 실행하거나, `concurrent.futures.ThreadPoolExecutor`를 사용할 수 있습니다. Orchestrator는 각 에이전트의 상태(진행 중, 완료, 실패 등)를 추적하고 결과를 수집합니다.
   * Orchestrator 클래스를 새로 만들거나, 프로젝트에 이미 유사한 스케줄러/큐 관리 로직이 있다면 이를 확장합니다. (예: APScheduler 기반 주기 실행이 있었다면, 거기에 에이전트 병렬 실행 기능을 덧붙이는 식)

2. **에이전트 역할 분담 설계:** 협업 효율을 높이기 위해 **에이전트별 전문 역할**을 정의합니다. 최소한 다음과 같은 역할을 고려합니다:

   * **Planner:** 작업 계획 수립 담당. (예: 문제를 sub-task로 나누거나 수행 순서 결정)
   * **Executor:** 실제 코드 작성 또는 작업 수행 담당. (예: Planner의 계획에 따라 코드를 구현하거나 명령 실행)
   * **Validator:** 결과 검증 담당. (예: 생성된 코드의 테스트 수행, 결과 품질 평가)
   * **Documenter:** 문서화 담당. (예: 변경 사항을 문서에 반영하거나 요약 리포트 작성)
     Orchestrator는 첫 작업을 Planner에게 보내고, Planner 결과를 받아 Executor에게 전달, Executor 작업 완료 후 Validator에게 검증을 요청... 이런 식의 파이프라인을 구축합니다. 필요에 따라 일부 단계는 병렬 진행도 가능합니다 (예: Executor가 코드 작성 중에 Documenter가 옆에서 관련 문서 초안을 작성).

3. **공유 메모리 및 통신 구현:** 여러 에이전트가 협업하려면 상태나 데이터를 공유할 방법이 필요합니다. \*\*공유 메모리(블랙보드 모델)\*\*를 Orchestrator 내에 두고, 에이전트들이 작업 중간중간 그 메모리를 통해 통신하게 할 수 있습니다.

   * 구현 방법: Orchestrator 클래스 안에 스레드-세이프한 자료구조 (예: `threading.Lock`으로 보호되는 딕셔너리 `shared_state`)를 만들고, 모든 에이전트가 해당 공유 상태를 참조/갱신합니다.
   * 예를 들어, Planner 에이전트가 계획을 수립하면 `shared_state["plan"]` 키에 계획 내용을 쓰고 완료합니다. Builder(Executor) 에이전트는 지속적으로 `shared_state["plan"]`을 폴링하여 계획이 채워지면 자기 작업을 시작하는 식입니다.
   * 에이전트 간 직접 통신이 필요할 경우 간단히 Orchestrator의 메소드를 호출해 다른 에이전트에게 데이터를 전달하거나, Python `queue.Queue`를 사용한 메시지 큐를 둘 수도 있습니다. 다만 구현 복잡도가 올라가므로 우선은 공유 상태 + 락으로 직관적으로 구성합니다.

4. **병렬 처리 및 동기화:** 에이전트들 간 **의존성이 없는 작업은 병렬로** 실행되도록 Orchestrator를 설계합니다. 예를 들어, Planner가 계획을 마치면 그 결과를 가지고 Executor, Validator, Documenter가 **동시에 시작**할 수도 있습니다 (Validator는 엄밀히는 실행 결과가 필요하지만, 코드 스타일 검사 같은 것은 미리 할 수도 있겠죠).

   * Python의 `ThreadPoolExecutor` 또는 여러 `threading.Thread` 인스턴스를 Orchestrator에서 관리하여, `agent.start()`로 실행하고 `join()`으로 완료 대기를 합니다. 이때 Planner처럼 반드시 선행이 필요한 쓰레드는 먼저 `join(timeout=..)`으로 어느 정도 기다린 후 나머지 쓰레드를 기다리는 식으로 조율합니다.
   * **락(Lock) 활용:** 공유 자원을 접근할 때는 반드시 락으로 보호하여 레이스 컨디션을 막습니다. 각 에이전트 작업 자체는 자기 고유 영역을 다루도록 설계하여, 락 충돌을 최소화합니다. (예: 서로 다른 키의 shared\_state를 업데이트할 때는 크게 문제가 없지만, 같은 데이터에 접근한다면 락 필수)
   * **에러 전파:** 한 에이전트에서 예외가 발생하면 Orchestrator는 그것을 캐치해서 로그를 남기고, 다른 에이전트들에게 취소 신호를 보낼지 여부도 결정해야 합니다. 간단히 구현할 경우, 쓰레드 내 예외는 잡지 않으면 메인 쓰레드를 죽이지 않으므로(`threading.Thread`에서는), Orchestrator가 각 에이전트 종료 후 상태를 점검하여 실패한 에이전트 존재 시 전체 작업 실패로 처리하는 방식으로 할 수 있습니다.

5. **시스템 통합:** 구현한 Orchestrator를 프로젝트 흐름에 녹입니다. 기존에는 단일 에이전트가 하던 일을 이제 Orchestrator를 통해 수행하도록 변경합니다. 예를 들어 사용자가 특정 기능을 요청하면, 이전에는 한 함수가 다 했겠지만 이제 Orchestrator 객체를 생성해 `orchestrator.run_all()`을 호출함으로써 여러 에이전트가 협업하도록 만듭니다.

   * Orchestrator의 출력으로 여러 에이전트의 결과 묶음(예: `{'plan': ..., 'code': ..., 'test_result': ...}`)을 얻을 수 있다면, 이를 취합하여 사용자 응답을 생성하거나 최종 산출물을 결정합니다.
   * 점진적 통합: 처음부터 모든 부분에 오케스트레이션을 적용하기 어렵다면, 특정 기능(예: 코드 생성 및 테스트 부분)에만 시범적으로 Orchestrator를 적용해보고, 안정성이 확인되면 범위를 넓혀갑니다.

### 📄 예시: Orchestrator 클래스와 다중 에이전트 병렬 실행

아래 코드는 간단한 Orchestrator와 에이전트 예시를 보여줍니다. `Agent` 클래스는 각 에이전트를 **별도 스레드로 동작**시키기 위한 래퍼이며, Orchestrator는 여러 에이전트를 생성하여 병렬로 실행합니다. 여기서는 **Planner → Builder → Tester → Documenter** 에이전트가 협력하는 시나리오를 스레드로 시뮬레이션했습니다.

```python
# orchestrator.py - Example Orchestrator and multi-agent parallel execution

import threading, time

# 공유 메모리 구조 (에이전트 간 상태를 공유)
shared_state = {"plan": None, "code": None, "test_result": None, "docs": None}
shared_lock = threading.Lock()

class Agent(threading.Thread):
    def __init__(self, name, task_func):
        super().__init__(name=name)
        self.task_func = task_func  # 에이전트가 수행할 작업 (함수)
        self.daemon = True         # 메인 스레드 종료 시 함께 종료되도록 설정

    def run(self):
        """스레드 시작 시 실행되는 메서드: 공유 상태를 이용해 작업 수행."""
        print(f"[{self.name}] Started")
        result = self.task_func()
        # 공유 상태에 결과 저장 (스레드 세이프하게)
        with shared_lock:
            shared_state[self.name] = result
        print(f"[{self.name}] Completed")

# 에이전트 작업 함수들 정의
def planner_task():
    # 계획 수립 (간단히 문자열로 가정)
    time.sleep(0.1)  # 작업 소요 시간 시뮬레이션
    plan = "Step1: Build feature X\nStep2: Write tests"
    return plan

def builder_task():
    # Planner의 계획이 나올 때까지 대기
    while True:
        with shared_lock:
            plan = shared_state.get("plan")
        if plan:
            break
        time.sleep(0.05)
    # 계획에 따라 코드 구현 (여기선 문자열로 시뮬레이션)
    time.sleep(0.2)
    code = f"Code for features based on plan: {plan}"
    return code

def tester_task():
    # 코드가 완성될 때까지 대기
    while True:
        with shared_lock:
            code = shared_state.get("code")
        if code:
            break
        time.sleep(0.05)
    # 코드에 대한 테스트 실행 (문자열 결과 시뮬레이션)
    time.sleep(0.1)
    test_result = "All tests passed"
    return test_result

def documenter_task():
    # 코드 완성까지 대기 (Documenter는 코드 완료 후 실행 가능하다고 가정)
    while True:
        with shared_lock:
            code = shared_state.get("code")
        if code:
            break
        time.sleep(0.05)
    # 문서 작성 (코드 내용을 요약하는 시뮬레이션)
    time.sleep(0.1)
    docs = f"Documentation for: {code[:30]}..."
    return docs

class Orchestrator:
    def __init__(self):
        # 역할별 에이전트 초기화
        self.agents = {
            "plan": Agent("plan", planner_task),
            "code": Agent("code", builder_task),
            "test_result": Agent("test_result", tester_task),
            "docs": Agent("docs", documenter_task)
        }

    def run_all(self):
        # 모든 에이전트 (스레드) 시작
        for agent in self.agents.values():
            agent.start()
        # Planner 완료를 잠시 대기 (다른 에이전트는 Planner 계획을 기다리므로)
        self.agents["plan"].join(timeout=1.0)
        # 모든 에이전트 완료 대기
        for agent in self.agents.values():
            agent.join(timeout=2.0)
        return dict(shared_state)  # 최종 상태 반환 (딕셔너리 복사본)

# Orchestrator 실행 예시
if __name__ == "__main__":
    orchestrator = Orchestrator()
    final_state = orchestrator.run_all()
    print("Final shared state:", final_state)
    # 예상 출력 (실행 시 마다 약간 순서 다를 수 있음):
    # [plan] Started
    # [plan] Completed
    # [code] Started
    # [test_result] Started
    # [docs] Started
    # [code] Completed
    # [test_result] Completed
    # [docs] Completed
    # Final shared state: {'plan': 'Step1: Build feature X\nStep2: Write tests',
    #                      'code': 'Code for features based on plan: Step1: Build feature X\nStep2: Write tests',
    #                      'test_result': 'All tests passed',
    #                      'docs': 'Documentation for: Code for features based ...'}
}
```

위 예시에서는 `Agent`를 `threading.Thread`의 서브클래스로 정의하여 각 에이전트를 **독립 스레드**로 실행했습니다. 공유 딕셔너리 `shared_state`가 **블랙보드**처럼 사용되어, 에이전트들은 필요한 데이터가 나타날 때까지 (`while` 루프로) 대기했다가 작업을 수행합니다. `shared_lock`으로 **공유 자원 접근에 대한 동기화**를 처리하여 스레드 안전성을 확보했습니다. Orchestrator의 `run_all()` 메서드는 모든 에이전트를 시작하고 `join()`으로 완료를 기다려, **최종 결과 상태**를 딕셔너리로 반환합니다.

실행 결과를 보면 Planner 완료 후 Builder, Tester, Documenter가 **거의 동시에 진행**되어 일부 작업이 병렬화됨을 알 수 있습니다. 이처럼 Orchestrator를 통해 작업들을 병렬로 지휘하면 전체 개발 사이클이 **가속화**되고, Validator(예시에선 tester) 에이전트가 실시간으로 품질 검증을 수행하므로 **품질 체크가 내재화**됩니다. 실제 사례에서도 이러한 멀티에이전트 협업으로 “한 명의 AI가 모든 것을 하는 것보다 훨씬 효율적”이라는 평가를 받았고, 4인의 에이전트 팀으로 **4배 빠른 개발**을 달성한 예시가 보고되었습니다.

또한, Orchestrator 패턴은 저수준의 스레드 구현 외에도 **LangChain**이나 **Microsoft Autogen** 같은 고급 프레임워크를 활용해 구현할 수도 있습니다. 예를 들어 LangChain에서는 여러 툴과 LLM 체인을 구성하여 한 에이전트가 내부적으로 다른 도구/모델을 호출하도록 만들 수 있고, AutoGen 프레임워크를 사용하면 **여러 LLM 에이전트들이 메시지를 교환하며 공동 작업**하도록 설정할 수 있습니다. Microsoft에서 공개한 **AutoGen**은 다중 에이전트 협업을 손쉽게 구축하기 위한 오픈소스 프레임워크로, 에이전트들이 대화하듯 협력하며 작업을 수행하게 해줍니다. AutoGen의 예로, 하나의 *코더* 에이전트와 *리뷰어* 에이전트를 만들어 코더가 코드 작성 제안을 하면 리뷰어가 검토/수정하는 **이중 에이전트 패턴**을 구현할 수 있습니다. 이렇듯 프로젝트 규모가 커지면 이러한 프레임워크 도입을 검토하여, 보다 견고하고 검증된 오케스트레이션을 사용할 것을 권장합니다.

**오류 발생 시 대처:**

* **스레드 간 Race Condition:** 만약 에이전트들이 공유 데이터에 엉뚱한 값을 덮어쓰거나, `None` 참조 같은 문제가 발생하면 공유자원 락 사용이 올바른지 확인합니다. 위 예시에서는 각 에이전트가 고유 키에만 기록하지만, 혹여 동일 키를 여러 에이전트가 갱신해야 한다면 락 구역을 세밀하게 조정해야 합니다.
* **데드락/무한루프:** 에이전트가 무한 대기(loop) 상태에서 깨어나지 못하는 경우 (예: 공유 상태가 영원히 채워지지 않는 논리 오류), Orchestrator의 `join(timeout=...)`으로도 종료가 안 될 수 있습니다. 이런 때는 Orchestrator에 타임아웃 후 **에이전트 강제 종료**나 **타임아웃 이벤트 발생 시 예외 발생** 처리를 추가합니다. 예컨대 특정 시간이 지나도 `shared_state["plan"]`이 안 차면 Orchestrator가 `"plan" 에이전트 실패`로 간주하고 다른 에이전트를 깨우는 등의 로직을 넣어야 할 수 있습니다.
* **스레드 에러 수집:** Python `threading.Thread`는 내부 예외를 메인에 전파하지 않으므로, 각 에이전트 함수(task\_func) 내부를 `try/except`로 감싸고 예외 발생 시 공유 상태에 에러 플래그를 저장하거나 Orchestrator에 알리도록 구현합니다. 예시에서는 생략했지만, 실제 적용 시 안정성을 위해 필요한 부분입니다. 그런 후 Orchestrator는 `run_all()` 결과를 모을 때 에러 플래그가 있으면 전체 프로세스를 실패 처리하거나 재시도를 시도할 수 있습니다.
* **자원 정리:** 멀티스레드 실행 중에 KeyboardInterrupt(CTRL+C) 등을 누르면 프로그램이 종료되는데, 데몬 스레드 사용 (`daemon=True`) 덕분에 함께 종료됩니다. 하지만 파일 핸들이나 네트워크 소켓 등을 에이전트가 열어놓았다면, 종료 전에 적절히 닫히도록 신경써야 합니다. 필요한 경우 Orchestrator에 `stop_all()` 메서드를 구현하고 각 에이전트에 종료 신호를 보내 안전하게 끝내도록 개선할 수 있습니다.

오케스트레이션 시스템이 구축되면, 팔란티어 에이전트는 **자율협력형 AI 팀**으로서 작동하게 됩니다. 이제 단일 에이전트의 한계를 넘어서 복잡한 작업도 분담하여 처리할 수 있으며, 특히 Validator 등을 통해 **실시간 피드백**을 주고받으므로 더 안정적인 결과를 기대할 수 있습니다. 다음 단계에서는 이러한 시스템에 **자기 개선(Reflection) 루프**를 도입하여, 시간이 지날수록 에이전트의 성능이 향상되는 메커니즘을 구현합니다.

---
