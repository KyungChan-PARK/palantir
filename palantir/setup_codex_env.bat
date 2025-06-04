@echo off
setlocal
set LOGFILE=build_offline_env.log
set PROJECT_ROOT=%cd%
set VENV_PATH=%PROJECT_ROOT%\.venv
set PYEXE=C:\Python313\python.exe
set MAIN_REQ=%PROJECT_ROOT%\requirements.txt
set UI_REQ=%PROJECT_ROOT%\pipeline_ui\requirements.txt
set PKG_ROOT=%PROJECT_ROOT%\offline_preparation\python_packages
set MAIN_PKG=%PKG_ROOT%\main_app_packages
set UI_PKG=%PKG_ROOT%\pipeline_ui_packages
set VENV=.venv
set PKG_DIR=offline_preparation\python_packages\unified

call :log [1] 가상환경 생성 중...
if not exist %VENV% (
    python -m venv %VENV%
)
call %VENV%\Scripts\activate.bat
if exist %PKG_DIR% (
    dir /b %PKG_DIR%\*.whl >nul 2>nul
    if %errorlevel%==0 (
        echo ▶ 오프라인 패키지 설치
        pip install --no-index --find-links=%PKG_DIR% ^
            -r requirements.txt ^
            -r pipeline_ui\requirements.txt
    ) else (
        echo ⚠ 오프라인 저장소 비어 있음 → PyPI fallback
        pip install -r requirements.txt ^
                    -r pipeline_ui\requirements.txt
    )
)

set PATH=%VENV_PATH%\Scripts;%PATH%

call :log [2] pip 오프라인 설치 (메인) ...
%VENV_PATH%\Scripts\pip.exe install --no-index --find-links=%MAIN_PKG% -r %MAIN_REQ% >> %LOGFILE% 2>&1
if errorlevel 1 goto error

call :log [3] pip 오프라인 설치 (UI) ...
%VENV_PATH%\Scripts\pip.exe install --no-index --find-links=%UI_PKG% -r %UI_REQ% >> %LOGFILE% 2>&1
if errorlevel 1 goto error

call :log [4] Codex 설정 파일 생성...
(echo {"model": "codex-o3-latest", "workdir": "C:\\palantir"}) > %PROJECT_ROOT%\.codex-config.json

call :log [5] 설치 검증 (pytest) ...
set PYTHONPATH=%PROJECT_ROOT% && %VENV_PATH%\Scripts\python.exe -m pytest -q > %PROJECT_ROOT%\activate_tests.log

echo [✔] Offline env ready
exit /b 0

:error
echo [!] 오류 발생. 자세한 내용은 build_offline_env.log 또는 install_errors.log 참조
exit /b 1

:log
echo %* >> %LOGFILE%
exit /b 0 