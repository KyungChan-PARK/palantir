#!/usr/bin/env bash
set -euo pipefail
ORIGINAL_DIR=$(pwd)
cd "$(dirname "$0")"

# Python 버전 체크
if ! command -v python3.13 &> /dev/null; then
    echo "Python 3.13이 필요합니다"
    exit 1
fi

python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install --no-index --find-links=deps -r requirements.txt --extra-index-url file://$PWD/deps
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest -q

cd "$ORIGINAL_DIR" 