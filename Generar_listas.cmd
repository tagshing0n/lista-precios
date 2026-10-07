@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
if not exist ".venv\Scripts\python.exe" goto instalar
".venv\Scripts\python.exe" -u generar_listas.py
set "resultado=%errorlevel%"
popd
pause
exit /b %resultado%
:instalar
echo Primero ejecuta Instalar_dependencias.cmd.
popd
pause
exit /b 1
