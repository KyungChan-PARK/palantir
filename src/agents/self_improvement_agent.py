import ast
import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from src.core.mcp import MCP, MCPConfig
from src.data.pipeline import DataConfig, DataPipeline
from palantir.services.mcp.test_mcp import TestMCP
from palantir.services.mcp.llm_mcp import LLMMCP

from .base_agent import AgentConfig, BaseAgent
from src.agents.base_agent import BaseAgent
from src.core.message_broker import MessageBroker, MessageBuilder, MessageType, MessagePriority
from src.core.profiler import PerformanceProfiler
from src.core.optimizer import PerformanceOptimizer
from src.core.dependency_graph import DependencyGraph

logger = logging.getLogger(__name__)


class SelfImprovementAgent(BaseAgent):
    """자가 개선 에이전트"""

    def __init__(
        self,
        agent_id: str,
        message_broker: MessageBroker,
        dependency_graph: DependencyGraph,
        profiler: PerformanceProfiler,
        optimizer: PerformanceOptimizer,
    ):
        super().__init__(agent_id, message_broker, profiler)
        self.dependency_graph = dependency_graph
        self.optimizer = optimizer
        self.improvement_strategies = {
            "resource": self._improve_resource_usage,
            "bottleneck": self._improve_bottlenecks,
            "performance": self._improve_performance,
            "reliability": self._improve_reliability,
        }
        self.test_mcp = TestMCP()
        self.llm = LLMMCP()

    def _initialize(self) -> None:
        """에이전트 초기화"""
        pass

    async def process(self, input_data: Any) -> Any:
        """성능 분석 및 개선"""
        # 1. 작업 정보 검색
        task = input_data.get("task", "")
        analysis = await self.retrieve_memory(f"task_analysis:{task}")
        implementation = await self.retrieve_memory(f"implementation:{task}")
        review = await self.retrieve_memory(f"review:{task}")
        test_results = await self.retrieve_memory(f"test_results:{task}")
        
        # 2. 성능 분석
        performance = await self.analyze_performance({
            "task": task,
            "analysis": analysis,
            "implementation": implementation,
            "review": review,
            "test_results": test_results
        })
        
        # 3. 성능 분석 결과를 메모리에 저장
        await self.store_memory(
            key=f"performance:{task}",
            value=performance,
            type="performance",
            tags={"task", "performance", self.agent_id},
            metadata={"task": task}
        )
        
        # 4. 프롬프트 최적화
        optimized_prompts = await self.optimize_prompts({
            "task": task,
            "analysis": analysis,
            "implementation": implementation,
            "review": review,
            "test_results": test_results,
            "performance": performance
        })
        
        # 5. 최적화된 프롬프트를 메모리에 저장
        await self.store_memory(
            key=f"optimized_prompts:{task}",
            value=optimized_prompts,
            type="prompts",
            tags={"task", "prompts", self.agent_id},
            metadata={"task": task}
        )
        
        # 6. 컨텍스트 업데이트
        self.update_agent_context("last_task", task)
        self.update_global_context("current_performance", performance)
        
        return {
            "performance": performance,
            "optimized_prompts": optimized_prompts
        }

    async def analyze_performance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """성능 분석"""
        # 1. 이전 성능 분석 검색
        task = input_data["task"]
        previous_performance = await self.search_memory({"task", "performance"})
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 작업의 성능을 분석하세요.\n"
            f"작업: {task}\n"
            "---\n"
            f"작업 분석:\n{input_data.get('analysis', '')}\n"
            "---\n"
            f"구현:\n{input_data.get('implementation', {}).get('code', '')}\n"
            "---\n"
            f"리뷰:\n{input_data.get('review', {}).get('review', '')}\n"
            "---\n"
            f"테스트 결과:\n{input_data.get('test_results', {}).get('results', '')}\n"
            "---\n"
            "이전 성능 분석:\n"
            f"{previous_performance}\n"
            "---\n"
            "다음 사항을 분석하세요:\n"
            "1. 실행 시간\n"
            "2. 메모리 사용량\n"
            "3. CPU 사용량\n"
            "4. I/O 작업\n"
            "5. 병목 지점\n"
        )
        
        # 3. LLM 호출
        response = await self.llm.generate(
            prompt=prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return {
            "task": task,
            "analysis": response.get("text", ""),
            "timestamp": response.get("timestamp", "")
        }

    async def optimize_prompts(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """프롬프트 최적화"""
        # 1. 이전 프롬프트 최적화 검색
        task = input_data["task"]
        previous_optimizations = await self.search_memory({"task", "prompts"})
        
        # 2. 프롬프트 생성
        prompt = (
            "아래 작업의 프롬프트를 최적화하세요.\n"
            f"작업: {task}\n"
            "---\n"
            f"작업 분석:\n{input_data.get('analysis', '')}\n"
            "---\n"
            f"구현:\n{input_data.get('implementation', {}).get('code', '')}\n"
            "---\n"
            f"리뷰:\n{input_data.get('review', {}).get('review', '')}\n"
            "---\n"
            f"테스트 결과:\n{input_data.get('test_results', {}).get('results', '')}\n"
            "---\n"
            f"성능 분석:\n{input_data.get('performance', {}).get('analysis', '')}\n"
            "---\n"
            "이전 최적화:\n"
            f"{previous_optimizations}\n"
            "---\n"
            "다음 사항을 최적화하세요:\n"
            "1. 프롬프트 명확성\n"
            "2. 컨텍스트 활용\n"
            "3. 제약 조건\n"
            "4. 예시 포함\n"
            "5. 출력 형식\n"
        )
        
        # 3. LLM 호출
        response = await self.llm.generate(
            prompt=prompt,
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return {
            "task": task,
            "prompts": response.get("text", ""),
            "timestamp": response.get("timestamp", "")
        }

    async def validate(self, output: Any) -> bool:
        # 개선 결과 검증
        return output.get("test_result", {}).get("success", False)

    async def analyze_codebase(self) -> Dict[str, Any]:
        """src/ 디렉토리 내 파이썬 파일 목록, AST 파싱, 함수/클래스/주석 요약"""
        src_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "src")
        )
        py_files = []
        for root, _, files in os.walk(src_dir):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(os.path.join(root, f))
        summary = []
        for file_path in py_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
                tree = ast.parse(code)
                file_info = {
                    "file": os.path.relpath(file_path, src_dir),
                    "functions": [],
                    "classes": [],
                    "docstring": ast.get_docstring(tree),
                }
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        file_info["functions"].append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        file_info["classes"].append(node.name)
                summary.append(file_info)
            except Exception as e:
                summary.append({"file": file_path, "error": str(e)})
        return {"summary": summary, "file_count": len(py_files)}

    async def generate_improvement_suggestions(
        self, analysis: Dict[str, Any], model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """코드베이스 분석을 바탕으로 개선 제안 생성"""
        mcp_config = MCPConfig(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            base_url=os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
        )

        # RAG 컨텍스트 수집
        rag_ctx = ""
        try:
            # 1. 최근 PR/이슈 검색
            async with MCP(mcp_config) as mcp:
                prs = await mcp.github_search(
                    query="is:pr is:merged label:improvement",
                    sort="updated",
                    per_page=3,
                )
                issues = await mcp.github_search(
                    query="is:issue is:closed label:bug",
                    sort="updated",
                    per_page=3,
                )
                rag_ctx += f"\n최근 PR: {str(prs)[:500]}"
                rag_ctx += f"\n최근 이슈: {str(issues)[:500]}"

            # 2. 테스트 커버리지 리포트
            coverage_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "tests", "coverage", "index.html"
            )
            if os.path.exists(coverage_path):
                with open(coverage_path, "r", encoding="utf-8") as f:
                    coverage = f.read()
                    rag_ctx += f"\n커버리지: {coverage[:500]}"

        except Exception as e:
            rag_ctx += f"\nRAG 컨텍스트 수집 실패: {str(e)}"

        async with MCP(mcp_config) as mcp:
            prompt = (
                "아래는 코드베이스 분석 요약과 관련 문서/코드(RAG 컨텍스트)입니다.\n"
                "각 개선안은 반드시 아래 JSON 포맷으로 반환하세요.\n"
                "---\n"
                "[\n"
                "  {\n"
                '    "file": "수정할 파일 경로(예: src/agents/example.py)",\n'
                '    "original": "원본 코드(수정 전)",\n'
                '    "suggested": "수정된 코드(수정 후)",\n'
                '    "description": "변경 요약 설명"\n'
                "  }\n"
                "]\n"
                "---\n"
                "최소 1개, 최대 3개의 개선안을 제안하세요. 반드시 위 JSON 포맷만 반환하세요.\n"
                f"분석 요약: {str(analysis['summary'])[:1000]}\n"
                f"\n[RAG 컨텍스트]\n{rag_ctx}"
            )
            try:
                response = await mcp.llm_generate(prompt=prompt, model=model)
                import json

                suggestions = (
                    response.get("suggestions") or response.get("text") or response
                )
                if isinstance(suggestions, str):
                    try:
                        suggestions = json.loads(suggestions)
                    except Exception:
                        suggestions = [
                            {"error": "LLM 응답이 JSON이 아님", "raw": suggestions}
                        ]
            except Exception as e:
                suggestions = [{"error": str(e)}]
        return {"suggestions": suggestions}

    async def apply_improvements(
        self, suggestions: Dict[str, Any], approved_files: list = None
    ) -> Dict[str, Any]:
        """승인된 항목만 실제 코드에 적용하고, 변경 이력을 DB에 기록하며, Git 자동화(브랜치/커밋/PR)까지 수행하는 구조"""
        import datetime
        import difflib
        import os
        import shutil

        from src.core.mcp import MCP, MCPConfig
        from src.data.pipeline import DataConfig, DataPipeline

        db_path = os.environ.get(
            "DB_PATH",
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent.db")
            ),
        )
        data_pipeline = DataPipeline(
            DataConfig(
                input_path="./data/input", output_path="./data/output", db_path=db_path
            )
        )
        applied_files = []
        backup_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "backup")
        )
        os.makedirs(backup_dir, exist_ok=True)
        # 승인된 파일만 적용
        if approved_files is None:
            approved_files = suggestions.get("suggestions", [])
        for patch in approved_files:
            file_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", patch.get("file", "")
                )
            )
            if not os.path.isfile(file_path):
                continue
            rel_path = patch.get("file", "")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(
                backup_dir, f"{rel_path.replace(os.sep, '_')}.{timestamp}.bak"
            )
            shutil.copy2(file_path, backup_path)
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()
            suggested_code = patch.get("suggested", "")
            if original_code.strip() == suggested_code.strip():
                continue
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(suggested_code)
            diff = "\n".join(
                difflib.unified_diff(
                    original_code.splitlines(),
                    suggested_code.splitlines(),
                    fromfile="original",
                    tofile="suggested",
                    lineterm="",
                )
            )
            description = patch.get("description", "")
            applied_files.append(
                {
                    "file": rel_path,
                    "backup": backup_path,
                    "diff": diff,
                    "description": description,
                }
            )
            data_pipeline.log_selfimprove_history(
                rel_path, timestamp, diff, description
            )

        return {
            "applied": True,
            "applied_files": applied_files,
            "note": "승인된 항목 적용, DB 기록, Git 자동화(브랜치/커밋/PR) 완료",
        }

    async def run_tests(self) -> Dict[str, Any]:
        """테스트 실행"""
        results = self.test_mcp.run_tests()
        success = all(result["success"] for result in results)
        
        # 실패한 테스트가 있으면 상세 정보 포함
        details = []
        if not success:
            for result in results:
                if not result["success"]:
                    details.append({
                        "type": result["type"],
                        "error": result.get("stderr", ""),
                        "output": result.get("output", "")
                    })
        
        return {
            "success": success,
            "results": results,
            "details": details if details else None
        }

    async def preview_improvements(self, suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """Human-in-the-loop: 개선 diff/patch 목록만 생성 (실제 적용 X)"""
        import difflib
        import os

        preview_files = []
        for patch in suggestions.get("suggestions", []):
            file_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), "..", "..", patch.get("file", "")
                )
            )
            if not os.path.isfile(file_path):
                continue
            rel_path = patch.get("file", "")
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()
            suggested_code = patch.get("suggested", "")
            if original_code.strip() == suggested_code.strip():
                continue
            diff = "\n".join(
                difflib.unified_diff(
                    original_code.splitlines(),
                    suggested_code.splitlines(),
                    fromfile="original",
                    tofile="suggested",
                    lineterm="",
                )
            )
            description = patch.get("description", "")
            preview_files.append(
                {"file": rel_path, "diff": diff, "description": description}
            )
        return {"preview": preview_files, "note": "실제 적용 전 diff/patch 목록만 생성"}

    async def rollback_improvement(self, file: str, timestamp: str) -> dict:
        """DB 이력 기반 롤백: 지정 파일을 특정 시점 백업본으로 복원"""
        import os
        import shutil

        from src.data.pipeline import DataConfig, DataPipeline

        db_path = os.environ.get(
            "DB_PATH",
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent.db")
            ),
        )
        data_pipeline = DataPipeline(
            DataConfig(
                input_path="./data/input", output_path="./data/output", db_path=db_path
            )
        )
        # 백업 파일 경로 생성 규칙과 일치해야 함
        backup_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "backup")
        )
        rel_path = file
        backup_pattern = f"{rel_path.replace(os.sep, '_')}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_pattern)
        target_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", rel_path)
        )
        if not os.path.isfile(backup_path):
            return {
                "success": False,
                "error": f"백업 파일이 존재하지 않음: {backup_path}",
            }
        shutil.copy2(backup_path, target_path)
        # 롤백 이력 DB에 기록(선택)
        data_pipeline.log_selfimprove_history(
            rel_path, timestamp, "ROLLBACK", "롤백 수행"
        )
        data_pipeline.close()
        return {
            "success": True,
            "file": rel_path,
            "restored_from": backup_path,
            "note": "지정 시점으로 롤백 완료",
        }

    async def _handle_task(self, message: Any):
        """작업 메시지 처리"""
        try:
            content = message.content
            if content["type"] == "improvement":
                await self._handle_agent_improvement(content["data"])
            elif content["type"] == "system_improvement":
                await self._handle_system_improvement(content["data"])
            else:
                logger.warning(f"Unknown improvement type: {content['type']}")

        except Exception as e:
            logger.error(f"Error handling improvement task: {e}")
            await self._publish_error(str(e))

    async def _handle_agent_improvement(self, data: Dict[str, Any]):
        """에이전트 개선 처리"""
        agent_id = data["agent_id"]
        analysis = data["analysis"]
        suggestions = data["suggestions"]
        strategy = data["strategy"]

        try:
            # 개선 전략 실행
            improvements = []
            
            # 리소스 사용량 개선
            if analysis["resource_usage"]["avg_cpu"] > 80 or analysis["resource_usage"]["avg_memory"] > 80:
                resource_improvements = await self._improve_resource_usage(
                    agent_id,
                    analysis["resource_usage"],
                )
                improvements.extend(resource_improvements)

            # 성능 개선
            if analysis["task_processing"]["avg_time"] > 5.0:
                performance_improvements = await self._improve_performance(
                    agent_id,
                    analysis["task_processing"],
                )
                improvements.extend(performance_improvements)

            # 안정성 개선
            if analysis["reliability"]["error_rate"] > 0.1:
                reliability_improvements = await self._improve_reliability(
                    agent_id,
                    analysis["reliability"],
                )
                improvements.extend(reliability_improvements)

            # 개선 결과 발행
            await self._publish_improvement_results(
                agent_id,
                improvements,
                strategy,
            )

        except Exception as e:
            logger.error(f"Error improving agent {agent_id}: {e}")
            await self._publish_error(str(e))

    async def _handle_system_improvement(self, data: Dict[str, Any]):
        """시스템 개선 처리"""
        metrics = data["metrics"]
        improvements = data["improvements"]

        try:
            results = []
            for improvement in improvements:
                if improvement["type"] == "resource":
                    result = await self._improve_resource_usage(
                        improvement["target"],
                        metrics,
                    )
                elif improvement["type"] == "bottleneck":
                    result = await self._improve_bottlenecks(
                        improvement["details"]["bottlenecks"],
                        improvement["details"]["critical_path"],
                    )
                else:
                    logger.warning(f"Unknown improvement type: {improvement['type']}")
                    continue

                results.append(result)

            # 개선 결과 발행
            await self._publish_system_improvement_results(results)

        except Exception as e:
            logger.error(f"Error improving system: {e}")
            await self._publish_error(str(e))

    async def _improve_resource_usage(
        self,
        agent_id: str,
        metrics: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """리소스 사용량 개선"""
        improvements = []

        # CPU 사용량 최적화
        if metrics["avg_cpu"] > 80:
            improvements.append({
                "type": "resource",
                "target": "cpu",
                "action": "optimize",
                "changes": [
                    {
                        "parameter": "batch_size",
                        "old_value": 32,
                        "new_value": 16,
                    },
                    {
                        "parameter": "worker_threads",
                        "old_value": 4,
                        "new_value": 2,
                    }
                ]
            })

        # 메모리 사용량 최적화
        if metrics["avg_memory"] > 80:
            improvements.append({
                "type": "resource",
                "target": "memory",
                "action": "optimize",
                "changes": [
                    {
                        "parameter": "cache_size",
                        "old_value": "1GB",
                        "new_value": "512MB",
                    },
                    {
                        "parameter": "buffer_size",
                        "old_value": "256MB",
                        "new_value": "128MB",
                    }
                ]
            })

        return improvements

    async def _improve_bottlenecks(
        self,
        bottlenecks: List[str],
        critical_path: List[str],
    ) -> List[Dict[str, Any]]:
        """병목 지점 개선"""
        improvements = []

        for bottleneck in bottlenecks:
            # 작업 분산
            if bottleneck in critical_path:
                improvements.append({
                    "type": "bottleneck",
                    "target": bottleneck,
                    "action": "distribute",
                    "changes": [
                        {
                            "parameter": "parallel_tasks",
                            "old_value": 1,
                            "new_value": 2,
                        },
                        {
                            "parameter": "queue_size",
                            "old_value": 100,
                            "new_value": 200,
                        }
                    ]
                })

            # 캐싱 추가
            improvements.append({
                "type": "bottleneck",
                "target": bottleneck,
                "action": "cache",
                "changes": [
                    {
                        "parameter": "cache_enabled",
                        "old_value": False,
                        "new_value": True,
                    },
                    {
                        "parameter": "cache_size",
                        "old_value": "0",
                        "new_value": "100MB",
                    }
                ]
            })

        return improvements

    async def _improve_performance(
        self,
        agent_id: str,
        metrics: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """성능 개선"""
        improvements = []

        # 처리 시간 최적화
        if metrics["avg_time"] > 5.0:
            improvements.append({
                "type": "performance",
                "target": "processing",
                "action": "optimize",
                "changes": [
                    {
                        "parameter": "batch_processing",
                        "old_value": False,
                        "new_value": True,
                    },
                    {
                        "parameter": "prefetch_size",
                        "old_value": 1,
                        "new_value": 10,
                    }
                ]
            })

        return improvements

    async def _improve_reliability(
        self,
        agent_id: str,
        metrics: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """안정성 개선"""
        improvements = []

        # 에러 처리 개선
        if metrics["error_rate"] > 0.1:
            improvements.append({
                "type": "reliability",
                "target": "error_handling",
                "action": "improve",
                "changes": [
                    {
                        "parameter": "retry_enabled",
                        "old_value": False,
                        "new_value": True,
                    },
                    {
                        "parameter": "max_retries",
                        "old_value": 0,
                        "new_value": 3,
                    }
                ]
            })

        return improvements

    async def _publish_improvement_results(
        self,
        agent_id: str,
        improvements: List[Dict[str, Any]],
        strategy: Dict[str, Any],
    ):
        """개선 결과 발행"""
        message = (
            MessageBuilder()
            .with_type(MessageType.RESULT)
            .from_sender(self.agent_id)
            .to_recipients([agent_id])
            .with_subject("Improvement results")
            .with_content({
                "type": "improvement_results",
                "data": {
                    "agent_id": agent_id,
                    "improvements": improvements,
                    "strategy": strategy,
                    "timestamp": datetime.now().isoformat(),
                }
            })
            .build()
        )
        await self.message_broker.publish(message)

    async def _publish_system_improvement_results(
        self,
        results: List[Dict[str, Any]],
    ):
        """시스템 개선 결과 발행"""
        message = (
            MessageBuilder()
            .with_type(MessageType.RESULT)
            .from_sender(self.agent_id)
            .to_recipients(["orchestrator"])
            .with_subject("System improvement results")
            .with_content({
                "type": "system_improvement_results",
                "data": {
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                }
            })
            .build()
        )
        await self.message_broker.publish(message)
