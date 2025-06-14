import pytest
from palantir.core.agents import PlannerAgent, DeveloperAgent, ReviewerAgent, SelfImprovementAgent
from palantir.core.orchestrator import Orchestrator

class DummyLLM:
    def generate(self, prompt, **kwargs):
        if "태스크 리스트" in prompt:
            return "['파일 생성', '코드 작성', '테스트 실행']"
        if "코드만 출력" in prompt:
            return "print('hello world')"
        if "코드 리뷰어" in prompt:
            return "문제 없음"
        if "자가개선" in prompt:
            return "주석 추가"
        return ""

@pytest.fixture
def patch_llm(monkeypatch):
    monkeypatch.setattr("palantir.core.agents.LLMMCP", lambda *a, **kw: DummyLLM())
    monkeypatch.setattr("palantir.services.mcp.llm_mcp.LLMMCP", lambda *a, **kw: DummyLLM())


def test_planner_agent(patch_llm):
    agent = PlannerAgent("Planner")
    tasks = agent.process("간단한 파이썬 프로그램 작성")
    assert isinstance(tasks, list)
    assert "파일 생성" in tasks[0]

def test_developer_agent(tmp_path, patch_llm):
    from palantir.services.mcp.file_mcp import FileMCP
    from palantir.services.mcp.git_mcp import GitMCP
    # MCP 임시 디렉토리로 교체
    agent = DeveloperAgent("Developer")
    agent.file = FileMCP(str(tmp_path))
    agent.git = GitMCP(str(tmp_path))
    tasks = ["파일 생성", "코드 작성"]
    results = agent.process(tasks)
    assert len(results) == 2
    for r in results:
        assert tmp_path.joinpath(r["file"]).exists()

def test_reviewer_agent(patch_llm):
    agent = ReviewerAgent("Reviewer")
    agent.test = lambda: "테스트 통과"
    dev_results = [{"task": "코드 작성", "file": "a.py", "code": "print('hi')"}]
    reviews = agent.process(dev_results)
    assert reviews[0]["feedback"] == "문제 없음"

def test_self_improvement_agent(tmp_path, patch_llm):
    from palantir.services.mcp.file_mcp import FileMCP
    from palantir.services.mcp.git_mcp import GitMCP
    from palantir.services.mcp.test_mcp import TestMCP
    agent = SelfImprovementAgent("SelfImprover")
    agent.file = FileMCP(str(tmp_path))
    agent.git = GitMCP(str(tmp_path))
    agent.test = lambda: "테스트 통과"
    review_results = [{"file": "a.py", "code": "print('hi')", "feedback": "문제 없음"}]
    agent.file.write_file("a.py", "print('hi')")
    result = agent.process(review_results)
    assert "improvements" in result
    assert "test_result" in result

def test_orchestrator(monkeypatch, tmp_path):
    # 전체 오케스트레이션 루프 테스트(모킹)
    monkeypatch.setattr("palantir.core.agents.LLMMCP", lambda *a, **kw: DummyLLM())
    monkeypatch.setattr("palantir.services.mcp.llm_mcp.LLMMCP", lambda *a, **kw: DummyLLM())
    from palantir.core.orchestrator import Orchestrator
    orch = Orchestrator()
    orch.developer.file.base_dir = str(tmp_path)
    orch.developer.git.repo_dir = str(tmp_path)
    orch.self_improver.file.base_dir = str(tmp_path)
    orch.self_improver.git.repo_dir = str(tmp_path)
    result = orch.run("간단한 파이썬 프로그램 작성")
    assert "improvements" in result 