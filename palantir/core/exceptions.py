"""오케스트레이션 시스템 예외 정의"""

class OrchestratorError(Exception):
    """오케스트레이터 기본 예외"""
    pass


class TaskExecutionError(OrchestratorError):
    """태스크 실행 중 발생한 예외"""
    pass


class AgentError(OrchestratorError):
    """에이전트 관련 예외"""
    pass


class MCPError(OrchestratorError):
    """MCP 계층 관련 예외"""
    pass


class MemoryError(OrchestratorError):
    """공유 메모리 관련 예외"""
    pass


class TimeoutError(OrchestratorError):
    """작업 시간 초과 예외"""
    pass


class SelfImprovementError(OrchestratorError):
    """자기개선 시스템 관련 예외"""
    pass


class PerformanceAnalysisError(SelfImprovementError):
    """성능 분석 중 발생한 예외"""
    pass


class ImprovementGenerationError(SelfImprovementError):
    """개선 제안 생성 중 발생한 예외"""
    pass


class ImprovementApplicationError(SelfImprovementError):
    """개선 사항 적용 중 발생한 예외"""
    pass 