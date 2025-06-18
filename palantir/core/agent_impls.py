"""
에이전트 모듈
"""

import ast
import json
import os
import shutil
from typing import Any, Dict, List

from src.agents.base_agent import AgentConfig, BaseAgent
from palantir.services.mcp.llm_mcp import LLMMCP
from palantir.services.mcp.file_mcp import FileMCP
from palantir.services.mcp.git_mcp import GitMCP
from palantir.services.mcp.test_mcp import TestMCP


class PlannerAgent(BaseAgent):
    """계획 수립 에이전트"""

    def __init__(self, name: str):
        super().__init__(name)
        self.llm = LLMMCP()

    def process(self, user_input: str, state: dict = None) -> List[str]:
        """사용자 입력을 태스크 리스트로 분해"""
        fail_reason = state.get("fail_reason") if state else None
        fail_history = state.get("history") if state else None
        alerts = state.get("alerts") if state else None
        external_knowledge = state.get("external_knowledge") if state else None

        prompt = f"""
        [역할] 당신은 Constitutional AI 기반 프로젝트 매니저(Planner)입니다.
        [목표] 사용자의 요구를 안전하고 신뢰성 있게 단계별 태스크 리스트로 분해하세요.
        [행동지침]
        - 각 태스크는 한 문장으로 명확하게 작성
        - 각 태스크는 테스트/검증 단계를 반드시 포함
        - 실패/반복/정책 이력이 있으면 반드시 반영해 재계획
        - 예시: ['데이터 파일 로드', '전처리', '분석 코드 작성', '결과 리포트 생성']
        사용자 요구: {user_input}
        """

        if fail_reason:
            prompt += f"\n[실패/에러/이유] {fail_reason}"
        if fail_history:
            prompt += f"\n[실패 이력] {fail_history}"
        if alerts:
            prompt += f"\n[정책/알림 이력] {alerts}"
        if external_knowledge:
            prompt += f"\n[외부지식/온톨로지] {external_knowledge}"

        prompt += "\n태스크 리스트:"
        response = self.llm.generate(prompt)

        # 간단 파싱(리스트 형태 추출)
        try:
            tasks = ast.literal_eval(response.strip())
            if isinstance(tasks, list):
                return [str(t).strip() for t in tasks if str(t).strip()]
        except Exception:
            pass

        # 리스트 형태가 아니면 줄바꿈 기준으로 분해
        lines = [line.strip("- •") for line in response.strip().splitlines()]
        tasks = [line for line in lines if line]
        return tasks


class DeveloperAgent(BaseAgent):
    """개발 에이전트"""

    def __init__(self, name: str):
        super().__init__(name)
        self.llm = LLMMCP()
        self.file = FileMCP()
        self.git = GitMCP()

    def process(self, tasks: List[str], state: dict = None) -> List[Dict[str, str]]:
        """태스크 리스트를 코드로 구현"""
        results = []
        prev_feedback = state.get("prev_feedback") if state else None
        fail_history = state.get("history") if state else None
        external_knowledge = state.get("external_knowledge") if state else None

        for task in tasks:
            prompt = f"""
            [역할] 당신은 Constitutional AI 기반 시니어 소프트웨어 엔지니어(Developer)입니다.
            [목표] 아래 태스크를 위한 파이썬 코드를 생성하고, 테스트/검증이 용이하도록 작성하세요.
            [행동지침]
            - 코드 품질, 보안, 테스트 용이성, 정책 준수에 유의
            - 이전 리뷰/개선 피드백, 실패 이력, 정책 위반 이력이 있으면 반드시 반영
            태스크: {task}
            """

            if prev_feedback:
                prompt += f"\n[이전 리뷰/개선 피드백] {prev_feedback}\n피드백을 반영해 코드를 개선하세요."
            if fail_history:
                prompt += f"\n[실패 이력] {fail_history}"
            if external_knowledge:
                prompt += f"\n[외부지식/온톨로지] {external_knowledge}"

            prompt += "\n코드만 출력하세요."
            code = self.llm.generate(prompt)
            filename = f"task_{tasks.index(task)+1}.py"
            self.file.write_file(filename, code)
            self.git.commit(f"{task} 코드 생성: {filename}")
            results.append({"task": task, "file": filename, "code": code})

        return results


class ReviewerAgent(BaseAgent):
    """리뷰 에이전트"""

    def __init__(self, name: str):
        super().__init__(name)
        self.test = TestMCP()
        self.llm = LLMMCP()

    def process(
        self, dev_results: List[Dict[str, str]], state: dict = None
    ) -> List[Dict[str, str]]:
        """개발 결과를 리뷰"""
        review_results = []
        prev_improvements = state.get("prev_improvements") if state else None
        fail_history = state.get("history") if state else None
        alerts = state.get("alerts") if state else None
        external_knowledge = state.get("external_knowledge") if state else None

        for item in dev_results:
            test_result = self.test.run_tests()
            review_prompt = f"""
            [역할] 당신은 Constitutional AI 기반 코드 리뷰어(Reviewer)입니다.
            [목표] 아래 코드를 검토하고, 테스트 결과/이전 개선 이력/실패 사유/정책 위반 이력을 바탕으로 개선점/문제점/칭찬할 점을 한글로 3줄 이내로 요약하세요.
            [행동지침]
            - 테스트 결과, 정책 위반, 실패 이력, 개선 이력을 반드시 반영
            코드:
            {item['code']}
            [테스트 결과] {test_result}
            """

            if prev_improvements:
                review_prompt += f"\n[이전 개선 이력] {prev_improvements}"
            if fail_history:
                review_prompt += f"\n[실패 이력] {fail_history}"
            if alerts:
                review_prompt += f"\n[정책/알림 이력] {alerts}"
            if external_knowledge:
                review_prompt += f"\n[외부지식/온톨로지] {external_knowledge}"

            feedback = self.llm.generate(review_prompt)
            review_results.append(
                {
                    "task": item["task"],
                    "file": item["file"],
                    "test_result": test_result,
                    "feedback": feedback,
                }
            )

        return review_results


class SelfImprovementAgent(BaseAgent):
    """자가 개선 에이전트"""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.test_mcp = TestMCP()
        self.performance_threshold = 0.8

    def _initialize(self) -> None:
        """에이전트 초기화"""
        self.llm = LLMMCP()
        self.file = FileMCP()
        self.git = GitMCP()

    def process(
        self, review_results: List[Dict[str, str]], state: dict = None
    ) -> Dict[str, Any]:
        """리뷰 결과를 바탕으로 코드 개선"""
        # 상태 초기화
        fail_count = state.get("fail_count", 0) if state else 0
        history = state.get("history", []) if state else []
        alerts = state.get("alerts", []) if state else []
        
        try:
            # 1. 성능 분석
            metrics = self._analyze_performance(review_results)
            
            # 2. 개선이 필요한지 확인
            if self._is_performance_satisfactory(metrics):
                return {
                    "status": "success",
                    "message": "현재 성능이 목표치를 충족",
                    "metrics": metrics
                }
            
            # 3. 개선 제안 생성
            suggestions = self._generate_improvements(metrics)
            if not suggestions:
                return {
                    "status": "success",
                    "message": "개선이 필요한 사항이 없음",
                    "metrics": metrics
                }
            
            # 4. 개선 사항 적용
            results = []
            for suggestion in suggestions:
                try:
                    # 4.1. 변경 사항 백업
                    if "file" in suggestion:
                        self.file.backup(suggestion["file"])
                    
                    # 4.2. 개선 사항 적용
                    if "code_change" in suggestion:
                        self.file.write(suggestion["file"], suggestion["code_change"])
                    
                    # 4.3. 테스트 실행
                    test_result = self.test_mcp.run_tests()
                    
                    if all(result["success"] for result in test_result):
                        # 4.4. 성공한 경우 커밋
                        self.git.commit(f"improvement: {suggestion['description']}")
                        results.append({
                            "suggestion": suggestion,
                            "status": "success",
                            "test_result": test_result
                        })
                    else:
                        # 4.5. 실패한 경우 롤백
                        if "file" in suggestion:
                            self.file.restore_backup(suggestion["file"])
                        results.append({
                            "suggestion": suggestion,
                            "status": "failed",
                            "test_result": test_result
                        })
                        fail_count += 1
                        alerts.append(f"테스트 실패: {suggestion['description']}")
                
                except Exception as e:
                    results.append({
                        "suggestion": suggestion,
                        "status": "error",
                        "error": str(e)
                    })
                    fail_count += 1
                    alerts.append(f"개선 적용 실패: {str(e)}")
            
            # 5. 결과 반환
            return {
                "status": "completed",
                "results": results,
                "metrics": metrics,
                "fail_count": fail_count,
                "alerts": alerts
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "fail_count": fail_count,
                "alerts": alerts
            }

    def _analyze_performance(self, review_results: List[Dict[str, str]]) -> Dict[str, float]:
        """성능 지표 분석"""
        total = len(review_results)
        if total == 0:
            return {
                "accuracy": 0.0,
                "response_time": 0.0,
                "error_rate": 0.0
            }
        
        success = sum(1 for r in review_results if r.get("status") == "success")
        errors = sum(1 for r in review_results if r.get("status") == "error")
        response_times = [float(r.get("response_time", 0)) for r in review_results if "response_time" in r]
        
        return {
            "accuracy": success / total if total > 0 else 0.0,
            "response_time": sum(response_times) / len(response_times) if response_times else 0.0,
            "error_rate": errors / total if total > 0 else 0.0
        }

    def _is_performance_satisfactory(self, metrics: Dict[str, float]) -> bool:
        """성능이 만족스러운지 확인"""
        return all([
            metrics.get("accuracy", 0) >= self.performance_threshold,
            metrics.get("response_time", float("inf")) <= 1.0,
            metrics.get("error_rate", 1.0) <= 0.1
        ])

    def _generate_improvements(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """성능 개선 제안 생성"""
        suggestions = []
        
        if metrics.get("accuracy", 0) < self.performance_threshold:
            suggestions.append({
                "type": "accuracy",
                "description": "정확도 개선",
                "priority": 1
            })
        
        if metrics.get("response_time", float("inf")) > 1.0:
            suggestions.append({
                "type": "performance",
                "description": "응답 시간 개선",
                "priority": 2
            })
        
        if metrics.get("error_rate", 1.0) > 0.1:
            suggestions.append({
                "type": "reliability",
                "description": "에러 처리 개선",
                "priority": 3
            })
        
        return sorted(suggestions, key=lambda x: x["priority"])
