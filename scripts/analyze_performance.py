#!/usr/bin/env python

import json
import os
from datetime import datetime
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()

def load_test_results() -> List[Tuple[datetime, Dict[str, float]]]:
    """모든 성능 테스트 결과를 로드합니다."""
    results_dir = "performance_results"
    results = []
    
    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            timestamp = datetime.strptime(
                filename.replace("performance_test_", "").replace(".json", ""),
                "%Y%m%d_%H%M%S"
            )
            
            with open(os.path.join(results_dir, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
            
            results.append((timestamp, data))
    
    return sorted(results, key=lambda x: x[0])

def calculate_statistics(results: List[Tuple[datetime, Dict[str, float]]]) -> Dict[str, Dict[str, float]]:
    """각 테스트 항목별 통계를 계산합니다."""
    stats = {}
    
    for _, data in results:
        for test_name, duration in data.items():
            if test_name not in stats:
                stats[test_name] = []
            stats[test_name].append(duration)
    
    return {
        test_name: {
            "mean": np.mean(durations),
            "min": np.min(durations),
            "max": np.max(durations),
            "std": np.std(durations)
        }
        for test_name, durations in stats.items()
    }

def display_statistics(stats: Dict[str, Dict[str, float]]):
    """통계 결과를 테이블 형식으로 표시합니다."""
    table = Table(title="성능 테스트 통계")
    
    table.add_column("테스트 항목", style="cyan")
    table.add_column("평균 (초)", justify="right", style="green")
    table.add_column("최소 (초)", justify="right", style="blue")
    table.add_column("최대 (초)", justify="right", style="red")
    table.add_column("표준편차", justify="right", style="yellow")
    
    for test_name, test_stats in stats.items():
        table.add_row(
            test_name,
            f"{test_stats['mean']:.2f}",
            f"{test_stats['min']:.2f}",
            f"{test_stats['max']:.2f}",
            f"{test_stats['std']:.2f}"
        )
    
    console.print(table)

def plot_trends(results: List[Tuple[datetime, Dict[str, float]]]):
    """성능 추세를 그래프로 표시합니다."""
    plt.figure(figsize=(12, 6))
    
    timestamps = [ts for ts, _ in results]
    test_names = set()
    for _, data in results:
        test_names.update(data.keys())
    
    for test_name in test_names:
        durations = []
        for _, data in results:
            durations.append(data.get(test_name, 0))
        
        plt.plot(timestamps, durations, marker='o', label=test_name)
    
    plt.title("성능 테스트 추세")
    plt.xlabel("테스트 실행 시간")
    plt.ylabel("소요 시간 (초)")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    
    # 그래프 저장
    plots_dir = "performance_results/plots"
    os.makedirs(plots_dir, exist_ok=True)
    plt.savefig(os.path.join(plots_dir, "performance_trends.png"), bbox_inches='tight')
    plt.close()

def analyze_performance():
    """성능 테스트 결과를 분석합니다."""
    try:
        # 결과 로드
        results = load_test_results()
        if not results:
            console.print("[bold red]분석할 성능 테스트 결과가 없습니다.[/bold red]")
            return
        
        # 통계 계산
        stats = calculate_statistics(results)
        
        # 결과 표시
        console.print("\n[bold]성능 테스트 분석 결과[/bold]")
        display_statistics(stats)
        
        # 추세 그래프 생성
        plot_trends(results)
        console.print("\n[green]성능 추세 그래프가 생성되었습니다: performance_results/plots/performance_trends.png[/green]")
        
    except Exception as e:
        console.print(f"[bold red]분석 중 오류가 발생했습니다: {str(e)}[/bold red]")

if __name__ == "__main__":
    analyze_performance() 