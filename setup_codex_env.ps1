# 오프라인 Codex 개발환경 자동 구축 스크립트 (PowerShell)
# 실행: PowerShell에서 관리자 권한으로 실행 권장

$ErrorActionPreference = 'Stop'
$LogFile = "build_offline_env.log"
$ProjectRoot = (Get-Location).Path
$VenvPath = "$ProjectRoot\.venv"
$PyExe = "C:\Python313\python.exe"
$MainReq = "$ProjectRoot\requirements.txt"
$UiReq = "$ProjectRoot\pipeline_ui\requirements.txt"
$PkgRoot = "$ProjectRoot\offline_preparation\python_packages"
$MainPkg = "$PkgRoot\main_app_packages"
$UiPkg = "$PkgRoot\pipeline_ui_packages"

function Log($msg) {
    $msg | Tee-Object -FilePath $LogFile -Append
}

try {
    Log "[1] 가상환경 생성 중..."
    & $PyExe -m venv $VenvPath | Tee-Object -FilePath $LogFile -Append
    $env:VIRTUAL_ENV = $VenvPath
    $env:PATH = "$VenvPath\Scripts;" + $env:PATH
    Log "[2] pip 오프라인 설치 (메인) ..."
    & "$VenvPath\Scripts\pip.exe" install --no-index --find-links=$MainPkg -r $MainReq 2>&1 | Tee-Object -FilePath $LogFile -Append
    Log "[3] pip 오프라인 설치 (UI) ..."
    & "$VenvPath\Scripts\pip.exe" install --no-index --find-links=$UiPkg -r $UiReq 2>&1 | Tee-Object -FilePath $LogFile -Append
    Log "[4] Codex 설정 파일 생성..."
    $codexConf = '{"model": "codex-o3-latest", "workdir": "C:\\palantir"}'
    Set-Content -Path "$ProjectRoot\.codex-config.json" -Value $codexConf -Encoding UTF8
    Log "[5] 설치 검증 (pytest) ..."
    & "$VenvPath\Scripts\Activate.ps1"
    Start-Process -NoNewWindow -Wait -FilePath "$VenvPath\Scripts\python.exe" -ArgumentList "-m", "pytest", "-q" -WorkingDirectory $ProjectRoot -RedirectStandardOutput "$ProjectRoot\activate_tests.log" -Environment @{"PYTHONPATH" = "$ProjectRoot"}
    Log "[✔] Offline env ready"
    Write-Host "[✔] Offline env ready"
} catch {
    $_ | Tee-Object -FilePath install_errors.log -Append
    Log "[!] 오류 발생: $_"
    Write-Host "[!] 오류 발생: $_"
    Exit 1
}
