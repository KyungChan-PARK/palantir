import os
import ast
import asyncio
from .base_agent import BaseAgent, AgentConfig
from typing import Any, Dict, List
from src.core.mcp import MCP, MCPConfig
from src.data.pipeline import DataPipeline, DataConfig

class SelfImprovementAgent(BaseAgent):
    """자가 개선 루프 담당 에이전트"""
    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def process(self, input_data: Any) -> Any:
        # 자가 개선 전체 루프 실행 (스켈레톤)
        analysis = await self.analyze_codebase()
        suggestions = await self.generate_improvement_suggestions(analysis)
        applied = await self.apply_improvements(suggestions)
        test_result = await self.run_tests()
        return {
            "analysis": analysis,
            "suggestions": suggestions,
            "applied": applied,
            "test_result": test_result
        }

    async def validate(self, output: Any) -> bool:
        # 개선 결과 검증 (스켈레톤)
        return output.get("test_result", {}).get("success", False)

    async def analyze_codebase(self) -> Dict[str, Any]:
        """src/ 디렉토리 내 파이썬 파일 목록, AST 파싱, 함수/클래스/주석 요약"""
        src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
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
                    "docstring": ast.get_docstring(tree)
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

    async def generate_improvement_suggestions(self, analysis: Dict[str, Any], model: str = "gpt-4o") -> Dict[str, Any]:
        """MCP를 통한 LLM 프롬프트 호출 구조 (5개 모델만 허용, 예외 명확화)"""
        allowed_models = ["gpt-4o", "o3", "o3-pro", "o4-mini", "o4-mini-high"]
        if model not in allowed_models:
            raise ValueError(f"지원하지 않는 모델입니다. (허용 모델: {', '.join(allowed_models)})")
        import sys
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")))
        from embedding_pipeline import EmbeddingPipeline
        mcp_config = MCPConfig(
            api_key=os.environ.get("MCP_API_KEY", "your-api-key"),
            base_url=os.environ.get("MCP_BASE_URL", "http://localhost:8000")
        )
        rag_ctx = ""
        try:
            pipe = EmbeddingPipeline()
            query_text = str(analysis['summary'])[:200]
            rag_results = pipe.query(query_text, top_k=2)
            rag_ctx = "\n\n".join([f"[{r['file']}]:\n{r['content'][:500]}" for r in rag_results])
        except Exception as e:
            rag_ctx = f"(RAG 컨텍스트 오류: {str(e)})"
        async with MCP(mcp_config) as mcp:
            prompt = (
                "아래는 코드베이스 분석 요약과 관련 문서/코드(RAG 컨텍스트)입니다.\n"
                "각 개선안은 반드시 아래 JSON 포맷으로 반환하세요.\n"
                "---\n"
                "[\n"
                "  {\n"
                "    \"file\": \"수정할 파일 경로(예: src/agents/example.py)\",\n"
                "    \"original\": \"원본 코드(수정 전)\",\n"
                "    \"suggested\": \"수정된 코드(수정 후)\",\n"
                "    \"description\": \"변경 요약 설명\"\n"
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
                suggestions = response.get("suggestions") or response.get("text") or response
                if isinstance(suggestions, str):
                    try:
                        suggestions = json.loads(suggestions)
                    except Exception:
                        suggestions = [{"error": "LLM 응답이 JSON이 아님", "raw": suggestions}]
            except Exception as e:
                suggestions = [{"error": str(e)}]
        return {"suggestions": suggestions}

    async def apply_improvements(self, suggestions: Dict[str, Any], approved_files: list = None) -> Dict[str, Any]:
        """승인된 항목만 실제 코드에 적용하고, 변경 이력을 DB에 기록하며, Git 자동화(브랜치/커밋/PR)까지 수행하는 구조"""
        import shutil
        import datetime
        import difflib
        import os
        from src.data.pipeline import DataPipeline, DataConfig
        from src.core.mcp import MCP, MCPConfig
        db_path = os.environ.get("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent.db")))
        data_pipeline = DataPipeline(DataConfig(
            input_path="./data/input",
            output_path="./data/output",
            db_path=db_path
        ))
        applied_files = []
        backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backup"))
        os.makedirs(backup_dir, exist_ok=True)
        # 승인된 파일만 적용
        if approved_files is None:
            approved_files = suggestions.get("suggestions", [])
        for patch in approved_files:
            file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", patch.get("file", "")))
            if not os.path.isfile(file_path):
                continue
            rel_path = patch.get("file", "")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"{rel_path.replace(os.sep, '_')}.{timestamp}.bak")
            shutil.copy2(file_path, backup_path)
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()
            suggested_code = patch.get("suggested", "")
            if original_code.strip() == suggested_code.strip():
                continue
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(suggested_code)
            diff = '\n'.join(difflib.unified_diff(
                original_code.splitlines(),
                suggested_code.splitlines(),
                fromfile="original",
                tofile="suggested",
                lineterm=""
            ))
            description = patch.get("description", "")
            applied_files.append({"file": rel_path, "backup": backup_path, "diff": diff, "description": description})
            data_pipeline.log_selfimprove_history(rel_path, timestamp, diff, description)
        # Git 자동화 (옵션)
        try:
            mcp_config = MCPConfig(
                api_key=os.environ.get("MCP_API_KEY", "your-api-key"),
                base_url=os.environ.get("MCP_BASE_URL", "http://localhost:8000")
            )
            async with MCP(mcp_config) as mcp:
                repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                branch_name = f"ai_suggestion_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                # 브랜치 생성
                await mcp.git_op(op="checkout", repo_path=repo_path, args={"branch": branch_name, "create": True})
                # 변경 파일 add/commit
                await mcp.git_op(op="add", repo_path=repo_path, args={"files": [patch.get("file", "") for patch in approved_files]})
                commit_msg = f"AI 개선안 자동 커밋: {', '.join([patch.get('file', '') for patch in approved_files])}"
                await mcp.git_op(op="commit", repo_path=repo_path, args={"message": commit_msg})
                # 푸시
                await mcp.git_op(op="push", repo_path=repo_path, args={"branch": branch_name})
                # PR 생성(옵션)
                await mcp.git_op(op="pr", repo_path=repo_path, args={"branch": branch_name, "title": commit_msg})
        except Exception as e:
            applied_files.append({"git_error": str(e)})
        data_pipeline.close()
        return {"applied": True, "applied_files": applied_files, "note": "승인된 항목 적용, DB 기록, Git 자동화(브랜치/커밋/PR) 완료"}

    async def run_tests(self) -> Dict[str, Any]:
        """pytest를 서브프로세스로 실행하고 결과를 파싱"""
        import subprocess
        import sys
        import tempfile
        result = {"success": False, "details": ""}
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode="w+", encoding="utf-8", suffix=".txt") as tmp:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "--maxfail=3", "--disable-warnings", "--tb=short", "--color=no", "tests/"],
                    stdout=tmp,
                    stderr=subprocess.STDOUT,
                    cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
                    timeout=120
                )
                tmp.flush()
                tmp.seek(0)
                output = tmp.read()
            result["details"] = output[-2000:]  # 마지막 2000자만 요약 반환
            result["success"] = proc.returncode == 0
        except Exception as e:
            result["details"] = f"테스트 실행 오류: {str(e)}"
            result["success"] = False
        return result

    async def preview_improvements(self, suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """Human-in-the-loop: 개선 diff/patch 목록만 생성 (실제 적용 X)"""
        import difflib
        import os
        preview_files = []
        for patch in suggestions.get("suggestions", []):
            file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", patch.get("file", "")))
            if not os.path.isfile(file_path):
                continue
            rel_path = patch.get("file", "")
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()
            suggested_code = patch.get("suggested", "")
            if original_code.strip() == suggested_code.strip():
                continue
            diff = '\n'.join(difflib.unified_diff(
                original_code.splitlines(),
                suggested_code.splitlines(),
                fromfile="original",
                tofile="suggested",
                lineterm=""
            ))
            description = patch.get("description", "")
            preview_files.append({"file": rel_path, "diff": diff, "description": description})
        return {"preview": preview_files, "note": "실제 적용 전 diff/patch 목록만 생성"}

    async def rollback_improvement(self, file: str, timestamp: str) -> dict:
        """DB 이력 기반 롤백: 지정 파일을 특정 시점 백업본으로 복원"""
        import os
        import shutil
        from src.data.pipeline import DataPipeline, DataConfig
        db_path = os.environ.get("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "agent.db")))
        data_pipeline = DataPipeline(DataConfig(
            input_path="./data/input",
            output_path="./data/output",
            db_path=db_path
        ))
        # 백업 파일 경로 생성 규칙과 일치해야 함
        backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backup"))
        rel_path = file
        backup_pattern = f"{rel_path.replace(os.sep, '_')}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_pattern)
        target_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", rel_path))
        if not os.path.isfile(backup_path):
            return {"success": False, "error": f"백업 파일이 존재하지 않음: {backup_path}"}
        shutil.copy2(backup_path, target_path)
        # 롤백 이력 DB에 기록(선택)
        data_pipeline.log_selfimprove_history(rel_path, timestamp, "ROLLBACK", "롤백 수행")
        data_pipeline.close()
        return {"success": True, "file": rel_path, "restored_from": backup_path, "note": "지정 시점으로 롤백 완료"} 