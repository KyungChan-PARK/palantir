import os
import re
import subprocess
import sys
import traceback
from datetime import datetime
from palantir.utils.wsl import assert_wsl
from loguru import logger

PHASES = [
    ("ruff", "ruff --fix ."),
    ("black", "black --check --line-length 88 ."),
    ("bandit", "bandit -r app -f json -o logs/bandit.json"),
    ("safety", "safety check --json > logs/safety.json"),
    ("radon", "radon cc -n C app > logs/radon.txt"),
    ("mutmut", "mutmut run --paths-to-mutate app"),
    ("pytest", "pytest -n auto --maxfail=2 --cov=app --cov-report=xml"),
    ("pytest-benchmark", "pytest --benchmark-only --benchmark-autosave"),
]

ENV = "Py 3.13 • WSL Ubuntu"
PROM_METRICS = "logs/self_improve_metrics.prom"

# WSL 체크
assert_wsl()


def run(cmd):
    try:
        subprocess.check_call(cmd, shell=True)
        return True, None
    except subprocess.CalledProcessError as e:
        return False, str(e)


def parse_radon_grade():
    try:
        with open("logs/radon.txt") as f:
            txt = f.read()
        grades = re.findall(r"\b([A-F])\b", txt)
        grade_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}
        worst = max([grade_map[g] for g in grades]) if grades else 6
        return worst
    except Exception:
        return 6


def parse_mutmut_alive_pct():
    try:
        out = subprocess.check_output("mutmut results", shell=True, encoding="utf-8")
        m = re.search(r"(\d+)%.*survived", out)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 100


def write_prometheus_metrics(radon_grade, mutmut_alive):
    with open(PROM_METRICS, "w") as f:
        f.write(f"radon_complexity_grade {radon_grade}\n")
        f.write(f"mutation_coverage_alive_pct {mutmut_alive}\n")


def write_error_report(phase, trace, extra=None):
    today = datetime.now().strftime("%Y%m%d")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"error_report_{today}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("##ERROR_REPORT##\n")
        f.write(f"phase: {phase}\n")
        f.write(f"traceback: {trace}\n")
        f.write(
            f"agent_diagnosis: {phase} 단계에서 자동화 실패. 로그, 커버리지, 스타일, 보안, 복잡도, mutation, benchmark 상태를 점검하세요.\n"
        )
        if extra:
            f.write(f"extra: {extra}\n")
        f.write(f"env: {ENV}\n")
        f.write("##END_ERROR_REPORT##\n")
    logger.info(f"[SELF-IMPROVE][ERROR] {phase} FAIL. See {path}")


def run_improvement_cycle():
    """
    평가-개선 루프를 실행합니다.
    1. scripts/run_promptfoo_eval.py를 실행하여 평가를 수행하고, 결과를 JSON 파일로 저장합니다.
    2. 평가 결과에서 실패(pass: false) 케이스를 추출합니다.
    3. 실패 케이스가 있으면 logs/improvement_candidates.log에 상세 기록을 남깁니다.
    4. (확장성) 실패 케이스별로 개선 방안 제안 및 파인튜닝 데이터셋에 추가하는 로직의 TODO를 남깁니다.
    """
    import json
    import subprocess
    from datetime import datetime
    import os

    eval_result_path = "logs/promptfoo_eval_result.json"
    os.makedirs("logs", exist_ok=True)
    # 1. 평가 스크립트 실행
    subprocess.run([
        sys.executable, "scripts/run_promptfoo_eval.py", "--output", eval_result_path
    ], check=True)

    # 2. 평가 결과 로드
    with open(eval_result_path, encoding="utf-8") as f:
        results = json.load(f)

    failed_cases = [case for case in results if not case.get("pass", True)]

    # 3. 실패 케이스 로깅
    if failed_cases:
        log_path = "logs/improvement_candidates.log"
        with open(log_path, "a", encoding="utf-8") as log:
            for case in failed_cases:
                ts = datetime.now().isoformat()
                prompt = case.get("prompt", "")
                expected = case.get("expected_output", "")
                actual = case.get("actual_output", "")
                log.write(f"[{ts}] FAILED - Prompt: {prompt}, Expected: {expected}, Got: {actual}\n")
                # TODO: Implement a function to suggest a new prompt based on the failure case.
                # TODO: Append the failed case to a 'data/finetuning_dataset.jsonl' file for future training.


def main():
    # 기존 품질 점검 루프
    today = datetime.now().strftime("%Y%m%d")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"self_improve_{today}.md")
    failed = False
    with open(log_path, "w", encoding="utf-8") as log:
        for phase, cmd in PHASES:
            try:
                ok, err = run(cmd)
                if ok:
                    log.write(f"✅ {phase} PASS\n")
                else:
                    log.write(f"❌ {phase} FAIL: {err}\n")
                    write_error_report(phase, err)
                    failed = True
                    break
            except Exception:
                trace = traceback.format_exc()
                log.write(f"❌ {phase} EXCEPTION: {trace}\n")
                write_error_report(phase, trace)
                failed = True
                break
        # 지표 파싱 및 기준 미달 체크
        radon_grade = parse_radon_grade()
        mutmut_alive = parse_mutmut_alive_pct()
        write_prometheus_metrics(radon_grade, mutmut_alive)
        log.write(f"radon_complexity_grade: {radon_grade}\n")
        log.write(f"mutation_coverage_alive_pct: {mutmut_alive}\n")
        if radon_grade > 3 or mutmut_alive > 30:
            msg = f"복잡도 등급 C 초과(radon={radon_grade}) 또는 mutation 생존율 30% 초과({mutmut_alive}%)"
            write_error_report("self-improve-metric", "", extra=msg)
            failed = True
    # 평가-개선 루프 실행
    try:
        run_improvement_cycle()
    except Exception as e:
        logger.error(f"[SELF-IMPROVE][EVAL] 평가-개선 루프 실패: {e}")
        failed = True
    if failed:
        sys.exit(1)
    else:
        logger.info("[SELF-IMPROVE] ALL PASS")


if __name__ == "__main__":
    main()
