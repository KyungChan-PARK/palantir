# 모든 하위 폴더에 __init__.py 생성
Get-ChildItem -Recurse -Directory | ForEach-Object {
    $init = Join-Path $_.FullName "__init__.py"
    if (-not (Test-Path $init)) { New-Item $init -ItemType File }
} 