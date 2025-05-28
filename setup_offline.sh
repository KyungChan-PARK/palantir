#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install --no-index --find-links=deps -r requirements.txt --extra-index-url file://$PWD/deps
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest -q 