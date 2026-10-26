@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (set "PYTHON=py -3") else (set "PYTHON=python")
if not exist .venv\Scripts\python.exe (
  %PYTHON% -m venv .venv
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe -c "import fastapi, uvicorn, sqlalchemy, httpx, filelock" >nul 2>nul
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe scripts\start_demo.py
pause
exit /b 0
:error
echo Falha na preparacao. Instale Python 3.11 ou superior e confira a conexao para baixar dependencias.
pause
exit /b 1
