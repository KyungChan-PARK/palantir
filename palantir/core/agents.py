from .agent_base import BaseAgent
from palantir.services.mcp.llm_mcp import LLMMCP
from palantir.services.mcp.file_mcp import FileMCP
from palantir.services.mcp.git_mcp import GitMCP
from palantir.services.mcp.test_mcp import TestMCP
from palantir.models.state import OrchestratorState, TaskState
import json
import ast
import shutil
import os

class PlannerAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.llm = LLMMCP()

    def process(self, user_input: str, state: dict = None):
        fail_reason = state['fail_reason'] if state and 'fail_reason' in state else None
        fail_history = state['history'] if state and 'history' in state else None
        alerts = state['alerts'] if state and 'alerts' in state else None
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
    def __init__(self, name: str):
        super().__init__(name)
        self.llm = LLMMCP()
        self.file = FileMCP()
        self.git = GitMCP()

    def process(self, tasks, state: dict = None):
        results = []
        prev_feedback = state['prev_feedback'] if state and 'prev_feedback' in state else None
        fail_history = state['history'] if state and 'history' in state else None
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
            prompt += "\n코드만 출력하세요."
            code = self.llm.generate(prompt)
            filename = f"task_{tasks.index(task)+1}.py"
            self.file.write_file(filename, code)
            self.git.commit(f"{task} 코드 생성: {filename}")
            results.append({"task": task, "file": filename, "code": code})
        return results

class ReviewerAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.test = TestMCP()
        self.llm = LLMMCP()

    def process(self, dev_results, state: dict = None):
        review_results = []
        prev_improvements = state['prev_improvements'] if state and 'prev_improvements' in state else None
        fail_history = state['history'] if state and 'history' in state else None
        alerts = state['alerts'] if state and 'alerts' in state else None
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
            feedback = self.llm.generate(review_prompt)
            review_results.append({"task": item["task"], "file": item["file"], "test_result": test_result, "feedback": feedback})
        return review_results

class SelfImprovementAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.llm = LLMMCP()
        self.file = FileMCP()
        self.git = GitMCP()
        self.test = TestMCP()

    def process(self, review_results, state: dict = None):
        improvement_suggestions = []
        fail_count = state['fail_count'] if state and 'fail_count' in state else 0
        history = state['history'] if state and 'history' in state else None
        alerts = state['alerts'] if state and 'alerts' in state else None
        policy_triggered = state['policy_triggered'] if state and 'policy_triggered' in state else False
        rollbacked = False
        rollback_reason = None
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
            analyze_prompt += "\n요구: 위 Pydantic 모델 구조(JSON)로만 답변"
            suggestion_json = self.llm.generate(analyze_prompt)
            try:
                suggestion = json.loads(suggestion_json)
            except Exception:
                suggestion = {"cause": "파싱 실패", "target_file": item["file"], "suggestion": suggestion_json, "refactor_needed": False}
            improvement_suggestions.append({"file": item["file"], "suggestion": suggestion})
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
                    history.append(f"[SelfImprover] 문법 오류로 롤백: {rollback_reason}")
                continue
            self.file.write_file(file_path, improved_code)
            self.git.commit(f"자가개선: {file_path}")
            test_result = self.test.run_tests()
            if '실패' in str(test_result):
                # 테스트 실패 시 롤백
                shutil.copyfile(backup_path, file_path)
                rollbacked = True
                rollback_reason = f"TestFailed: {test_result}"
                if history:
                    history.append(f"[SelfImprover] 테스트 실패로 롤백: {rollback_reason}")
                continue
            # 롤백이 없을 때만 백업 삭제
            if os.path.exists(backup_path) and not rollbacked:
                os.remove(backup_path)
        # 개선 이력/정책 위반 이력 등 상태 객체에 누적 기록(상위에서 state 갱신 필요)
        if rollbacked and state and 'history' in state:
            state['history'].append(f"[SelfImprover] 롤백 발생: {rollback_reason}")
        return {"improvements": improvement_suggestions, "rollbacked": rollbacked, "rollback_reason": rollback_reason, "test_result": test_result} 