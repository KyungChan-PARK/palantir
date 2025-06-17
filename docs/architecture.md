# Architecture Overview

이 문서는 Palantir 멀티에이전트 시스템의 오케스트레이션 구조를 간략히 설명합니다.

## 에이전트 계층

- **Planner**: 사용자 요구를 분석해 세부 태스크 목록을 생성합니다.
- **Developer**: Planner가 정의한 태스크를 코드로 구현합니다.
- **Reviewer**: 생성된 코드를 테스트하고 품질을 검토합니다.
- **SelfImprover**: 테스트 실패나 리뷰 피드백을 기반으로 코드 개선을 시도합니다.

## Orchestrator 동작 흐름

1. Planner가 입력을 받아 태스크 목록을 만듭니다.
2. 각 태스크는 Developer → Reviewer 순서로 처리됩니다.
3. Reviewer 단계에서 실패가 발생하면 SelfImprover가 최대 세 번까지 수정합니다.
4. 세 번 연속 실패 시 Planner가 해당 태스크를 다시 세분화하여 계획을 갱신합니다.
5. 모든 태스크가 완료되면 결과와 히스토리를 반환합니다.

오케스트레이터는 `serial`, `parallel`, `adaptive` 세 가지 실행 모드를 지원하며,
병렬 모드에서는 독립적인 태스크를 동시에 처리합니다.

## MCP 통합

모든 에이전트는 File, Git, LLM, Test, Web MCP를 통해 도구 접근을 통일된 인터페이스로 사용합니다.
오케스트레이터는 ContextManager를 이용해 에이전트별 컨텍스트를 병합하고 갱신합니다.
