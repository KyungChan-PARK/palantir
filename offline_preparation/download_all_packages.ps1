# requirements.txt, pipeline_ui/requirements.txt의 모든 패키지 오프라인 저장
$venv = ".tmp"
python -m venv $venv
& "$venv\Scripts\activate"
python -m pip install --upgrade pip
pip download -r requirements.txt `
             -r pipeline_ui\requirements.txt `
             -d offline_preparation\python_packages\unified
deactivate
Remove-Item -Recurse -Force $venv
Write-Host "✅ 오프라인 패키지 다운로드 완료" 