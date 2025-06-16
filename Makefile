.PHONY: test performance-test performance-report performance-analyze performance-report-html clean docs migrate

# 환경 변수
export PYTHONPATH := $(shell pwd)
export DATABASE_URL := postgresql://postgres:postgres@localhost:5432/palantir_test
export REDIS_URL := redis://localhost:6379/0
export SECRET_KEY := test_secret_key

# 기본 테스트 실행
test:
	pytest tests/unit tests/integration -v

# 성능 테스트 실행
performance-test:
	python scripts/run_performance_tests.py

# 성능 테스트 결과 분석
performance-analyze:
	python scripts/analyze_performance.py

# 성능 테스트 HTML 보고서 생성
performance-report-html:
	python scripts/generate_performance_report.py

# API 문서 생성
docs:
	python scripts/generate_api_docs.py

# 데이터베이스 마이그레이션
migrate:
	python scripts/migrate_database.py

# 테스트 결과 정리
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name "htmlcov" -exec rm -r {} +
	find . -type d -name "dist" -exec rm -r {} +
	find . -type d -name "build" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +

# 최근 성능 테스트 결과 표시
performance-report:
	@echo "최근 성능 테스트 결과:"
	@ls -t performance_results/*.json | head -n 1 | xargs cat 