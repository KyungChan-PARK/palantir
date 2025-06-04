#!/usr/bin/env python
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import aiohttp
from rich.console import Console
from rich.table import Table

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

console = Console()

async def test_user_creation(session: aiohttp.ClientSession) -> float:
    """사용자 생성 성능 테스트"""
    start_time = time.time()
    for i in range(100):
        async with session.post(
            "http://localhost:8000/api/v1/users/",
            json={
                "email": f"test{i}@example.com",
                "password": "testpassword123",
                "username": f"testuser{i}"
            }
        ) as response:
            assert response.status == 201
    return time.time() - start_time

async def test_user_retrieval(session: aiohttp.ClientSession) -> float:
    """사용자 조회 성능 테스트"""
    start_time = time.time()
    for i in range(1000):
        async with session.get(f"http://localhost:8000/api/v1/users/{i % 100 + 1}") as response:
            assert response.status == 200
    return time.time() - start_time

async def test_concurrent_users(session: aiohttp.ClientSession) -> float:
    """동시 사용자 처리 성능 테스트"""
    start_time = time.time()
    tasks = []
    for i in range(50):
        tasks.append(
            session.get(f"http://localhost:8000/api/v1/users/{i % 100 + 1}")
        )
    responses = await asyncio.gather(*tasks)
    for response in responses:
        assert response.status == 200
    return time.time() - start_time

async def test_authentication(session: aiohttp.ClientSession) -> float:
    """인증 성능 테스트"""
    start_time = time.time()
    for i in range(1000):
        async with session.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "username": f"testuser{i % 100}",
                "password": "testpassword123"
            }
        ) as response:
            assert response.status == 200
    return time.time() - start_time

async def test_db_connection_pool(session: aiohttp.ClientSession) -> float:
    """데이터베이스 연결 풀 성능 테스트"""
    start_time = time.time()
    tasks = []
    for i in range(100):
        tasks.append(
            session.get(f"http://localhost:8000/api/v1/users/{i % 100 + 1}")
        )
    responses = await asyncio.gather(*tasks)
    for response in responses:
        assert response.status == 200
    return time.time() - start_time

async def run_performance_tests() -> Dict[str, float]:
    """모든 성능 테스트 실행"""
    async with aiohttp.ClientSession() as session:
        results = {
            "사용자 생성 (100명)": await test_user_creation(session),
            "사용자 조회 (1000회)": await test_user_retrieval(session),
            "동시 사용자 처리 (50명)": await test_concurrent_users(session),
            "인증 처리 (1000회)": await test_authentication(session),
            "DB 연결 풀 (100개)": await test_db_connection_pool(session)
        }
    return results

def save_results(results: Dict[str, float]) -> str:
    """테스트 결과를 JSON 파일로 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"performance_results/performance_test_{timestamp}.json"
    os.makedirs("performance_results", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return filename

def display_results(results: Dict[str, float]):
    """테스트 결과를 테이블 형식으로 표시"""
    table = Table(title="성능 테스트 결과")
    table.add_column("테스트 항목", style="cyan")
    table.add_column("소요 시간 (초)", style="green")
    
    for test_name, duration in results.items():
        table.add_row(test_name, f"{duration:.2f}")
    
    console.print(table)

async def main():
    """메인 실행 함수"""
    try:
        console.print("[bold green]성능 테스트를 시작합니다...[/bold green]")
        results = await run_performance_tests()
        
        filename = save_results(results)
        console.print(f"\n[bold blue]테스트 결과가 저장되었습니다: {filename}[/bold blue]")
        
        display_results(results)
        
    except Exception as e:
        console.print(f"[bold red]테스트 실행 중 오류가 발생했습니다: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 