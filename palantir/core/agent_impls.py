"""
에이전트 모듈
"""

import ast
import json
import os
import shutil
from typing import Any, Dict, List, Optional

from .base import BaseAgent
from .mcp import LLMMCP, FileMCP, GitMCP, TestMCP


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
                return tasks
        except Exception:
            pass
        return [response.strip()]


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

    def __init__(self, name: str):
        super().__init__(name)
        self.llm = LLMMCP()
        self.file = FileMCP()
        self.git = GitMCP()
        self.test = TestMCP()

    def process(
        self, review_results: List[Dict[str, str]], state: dict = None
    ) -> Dict[str, Any]:
        """리뷰 결과를 바탕으로 코드 개선"""
        improvement_suggestions = []
        fail_count = state.get("fail_count") if state else 0
        history = state.get("history") if state else None
        alerts = state.get("alerts") if state else None
        policy_triggered = state.get("policy_triggered") if state else False
        external_knowledge = state.get("external_knowledge") if state else None
        rollbacked = False
        rollback_reason = None
        test_result = None

        for item in review_results:
            analyze_prompt = f"""
            [역할] 당신은 Constitutional AI 기반 코드 자가개선 AI(SelfImprover)입니다.
            [목표] 아래 코드, 리뷰 피드백, 테스트 결과, 실패 이력, 반복 횟수, 정책/알림 이력, 정책 위반 여부를 종합적으로 반영해 개선안을 JSON으로 출력하세요.
            [행동지침]
            - 반드시 아래 Pydantic 모델 구조로 답변:
            {{
                "cause": "오류 원인 요약",
                "target_file": "문제 발생 파일명",
                "suggestion": "제안하는 수정 방향",
                "refactor_needed": false
            }}
            - 반복 실패/이력/피드백/테스트 결과/정책 위반 이력을 반드시 반영
            코드:
            {item['code']}
            피드백:
            {item['feedback']}
            테스트 결과:
            {item.get('test_result','')}
            """

            if fail_count:
                analyze_prompt += f"\n[실패 반복 횟수] {fail_count}회"
            if history:
                analyze_prompt += f"\n[실패/개선 이력] {history}"
            if alerts:
                analyze_prompt += f"\n[정책/알림 이력] {alerts}"
            if policy_triggered:
                analyze_prompt += f"\n[정책 위반] True"
            if external_knowledge:
                analyze_prompt += f"\n[외부지식/온톨로지] {external_knowledge}"

            analyze_prompt += "\n요구: 위 Pydantic 모델 구조(JSON)로만 답변"
            suggestion_json = self.llm.generate(analyze_prompt)

            try:
                suggestion = json.loads(suggestion_json)
            except Exception:
                suggestion = {
                    "cause": "파싱 실패",
                    "target_file": item["file"],
                    "suggestion": suggestion_json,
                    "refactor_needed": False,
                }

            improvement_suggestions.append(
                {"file": item["file"], "suggestion": suggestion}
            )

            # 개선 적용 전 백업
            file_path = item["file"]
            backup_path = file_path + ".bak"
            shutil.copyfile(file_path, backup_path)

            code = self.file.read_file(file_path)
            improved_code = f"# 개선안: {suggestion['suggestion']}\n" + code

            # 1차: 전체 코드 덮어쓰기(추후 diff patch/부분 수정 확장 가능)
            try:
                ast.parse(improved_code)
            except Exception as e:
                # 문법 오류 발생 시 롤백
                shutil.copyfile(backup_path, file_path)
                rollbacked = True
                rollback_reason = f"SyntaxError: {str(e)}"
                if history:
                    history.append(
                        f"[SelfImprover] 문법 오류로 롤백: {rollback_reason}"
                    )
                continue

            self.file.write_file(file_path, improved_code)
            self.git.commit(f"자가개선: {file_path}")

            test_result = self.test.run_tests()
            if "실패" in str(test_result):
                # 테스트 실패 시 롤백
                shutil.copyfile(backup_path, file_path)
                rollbacked = True
                rollback_reason = f"TestFailed: {test_result}"
                if history:
                    history.append(
                        f"[SelfImprover] 테스트 실패로 롤백: {rollback_reason}"
                    )

            # 롤백이 없을 때만 백업 삭제
            if os.path.exists(backup_path) and not rollbacked:
                os.remove(backup_path)

        # 개선 이력/정책 위반 이력 등 상태 객체에 누적 기록(상위에서 state 갱신 필요)
        if rollbacked and state and "history" in state:
            state["history"].append(f"[SelfImprover] 롤백 발생: {rollback_reason}")

        return {
            "improvements": improvement_suggestions,
            "rollbacked": rollbacked,
            "rollback_reason": rollback_reason,
            "test_result": test_result,
        }
