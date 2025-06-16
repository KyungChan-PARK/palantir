#!/usr/bin/env python

import json
import os
from datetime import datetime
from typing import Dict, Tuple

import jinja2
from rich.console import Console

console = Console()


def load_latest_results() -> Tuple[datetime, Dict[str, float]]:
    """최신 성능 테스트 결과를 로드합니다."""
    results_dir = "performance_results"
    json_files = [f for f in os.listdir(results_dir) if f.endswith(".json")]
    if not json_files:
        raise FileNotFoundError("성능 테스트 결과 파일이 없습니다.")

    latest_file = sorted(json_files)[-1]
    timestamp = datetime.strptime(
        latest_file.replace("performance_test_", "").replace(".json", ""),
        "%Y%m%d_%H%M%S",
    )

    with open(os.path.join(results_dir, latest_file), "r", encoding="utf-8") as f:
        data = json.load(f)

    return timestamp, data


def generate_html_report(timestamp: datetime, results: Dict[str, float]) -> str:
    """HTML 보고서를 생성합니다."""
    template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>성능 테스트 보고서</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .timestamp {
                color: #7f8c8d;
                text-align: center;
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f8f9fa;
                color: #2c3e50;
            }
            tr:hover {
                background-color: #f5f5f5;
            }
            .summary {
                background-color: #e8f4f8;
                padding: 20px;
                border-radius: 4px;
                margin-bottom: 30px;
            }
            .chart {
                margin-top: 30px;
                text-align: center;
            }
            .chart img {
                max-width: 100%;
                height: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>성능 테스트 보고서</h1>
            <div class="timestamp">
                테스트 실행 시간: {{ timestamp.strftime('%Y-%m-%d %H:%M:%S') }}
            </div>
            
            <div class="summary">
                <h2>테스트 요약</h2>
                <p>총 테스트 항목: {{ results|length }}개</p>
                <p>평균 응답 시간: {{ (results.values()|sum / results.values()|length)|round(2) }}초</p>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>테스트 항목</th>
                        <th>소요 시간 (초)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for test_name, duration in results.items() %}
                    <tr>
                        <td>{{ test_name }}</td>
                        <td>{{ "%.2f"|format(duration) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div class="chart">
                <h2>성능 추세</h2>
                <img src="plots/performance_trends.png" alt="성능 추세 그래프">
            </div>
        </div>
    </body>
    </html>
    """

    env = jinja2.Environment()
    template = env.from_string(template)
    return template.render(timestamp=timestamp, results=results)


def save_report(html_content: str, timestamp: datetime):
    """HTML 보고서를 파일로 저장합니다."""
    reports_dir = "performance_results/reports"
    os.makedirs(reports_dir, exist_ok=True)

    filename = f"performance_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(reports_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filepath


def generate_report():
    """성능 테스트 보고서를 생성합니다."""
    try:
        # 최신 결과 로드
        timestamp, results = load_latest_results()

        # HTML 보고서 생성
        html_content = generate_html_report(timestamp, results)

        # 보고서 저장
        filepath = save_report(html_content, timestamp)

        console.print(f"[green]성능 테스트 보고서가 생성되었습니다: {filepath}[/green]")

    except Exception as e:
        console.print(
            f"[bold red]보고서 생성 중 오류가 발생했습니다: {str(e)}[/bold red]"
        )


if __name__ == "__main__":
    generate_report()
