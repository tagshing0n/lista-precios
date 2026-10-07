@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 exit /b 1
echo Preparando listaPrecios...
if exist ".venv\Scripts\python.exe" goto instalar
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if not errorlevel 1 goto crear_py
python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 goto falta_python
python -m venv .venv
goto verificar
:crear_py
py -3 -m venv .venv
:verificar
if errorlevel 1 goto error
:instalar
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
".venv\Scripts\python.exe" -c "import openpyxl, PIL; print('Dependencias verificadas.')"
if errorlevel 1 goto error
if not exist datos mkdir datos
if not exist outputs mkdir outputs
echo Instalacion terminada. Copia el TXT y el logo a datos.
echo Despues abre Generar_listas.cmd.
popd
pause
exit /b 0
:falta_python
echo Instala Python 3.11 o posterior desde https://www.python.org/downloads/windows/
echo Activa Add Python to PATH y vuelve a ejecutar este archivo.
goto error
:error
echo No se completo la instalacion. Revisa el mensaje anterior y tu conexion a Internet.
popd
pause
exit /b 1
