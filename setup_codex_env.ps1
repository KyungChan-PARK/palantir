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
$VENV = ".venv"
$PKG_DIR = "offline_preparation\python_packages\unified"

function Log($msg) {
    $msg | Tee-Object -FilePath $LogFile -Append
}

try {
    Log "[1] 가상환경 생성 중..."
    if (-Not (Test-Path $VENV)) {
        python -m venv $VENV
    }
    & "$VENV\Scripts\activate"
    Log "[2] pip 오프라인 설치 (메인) ..."
    if ((Test-Path $PKG_DIR) -and ((Get-ChildItem $PKG_DIR).Count -gt 0)) {
        Write-Host "▶ 오프라인 패키지 설치"
        pip install --no-index --find-links="$PKG_DIR" `
            -r requirements.txt `
            -r pipeline_ui\requirements.txt
    } else {
        Write-Host "⚠  오프라인 저장소 비어 있음 → PyPI fallback"
        pip install -r requirements.txt `
                    -r pipeline_ui\requirements.txt
    }
    Log "[3] Codex 설정 파일 생성..."
    $codexConf = '{"model": "codex-o3-latest", "workdir": "C:\\palantir"}'
    Set-Content -Path "$ProjectRoot\.codex-config.json" -Value $codexConf -Encoding UTF8
    Log "[4] 설치 검증 (pytest) ..."
    $env:PYTHONPATH = "$PWD"
    pytest -q | Tee-Object -FilePath offline_preparation\install_test.log
    Log "[✔] Offline env ready"
    Write-Host "[✔] Offline env ready"
} catch {
    $_ | Tee-Object -FilePath install_errors.log -Append
    Log "[!] 오류 발생: $_"
    Write-Host "[!] 오류 발생: $_"
    Exit 1
}
