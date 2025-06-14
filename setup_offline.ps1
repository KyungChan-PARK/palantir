set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot

python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install --no-index --find-links=deps -r requirements.txt
$env:PYTHONPATH = "$PSScriptRoot"
pytest -q
Pop-Location 