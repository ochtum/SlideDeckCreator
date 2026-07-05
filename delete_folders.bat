@echo off
setlocal

set "BASE_DIR=%~dp0"
set "PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"

if not exist "%PS_EXE%" (
    echo [ERROR] PowerShell was not found.
    pause
    exit /b 1
)

"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -Command ^
  "$base = [System.IO.Path]::GetFullPath('%BASE_DIR%');" ^
  "$names = @('output', 'input', '.lt-slide-work');" ^
  "foreach ($name in $names) {" ^
  "  $target = [System.IO.Path]::GetFullPath((Join-Path -Path $base -ChildPath $name));" ^
  "  if (-not $target.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) { throw ('Refusing path outside base: ' + $target); }" ^
  "  if (Test-Path -LiteralPath $target -PathType Container) {" ^
  "    Remove-Item -LiteralPath $target -Recurse -Force;" ^
  "    if (Test-Path -LiteralPath $target) { throw ('Failed to delete: ' + $name); }" ^
  "    Write-Host ('Deleted: ' + $name);" ^
  "  } else {" ^
  "    Write-Host ('Not found: ' + $name);" ^
  "  }" ^
  "}"

if errorlevel 1 (
    echo Failed.
) else (
    echo Completed.
)
pause
exit /b %errorlevel%
