@echo off
rem ============================================================================
rem  Cronicas de Cinzas - build completo no Windows
rem  Gera: dist\CronicasDeCinzas.exe (janela), dist\CronicasDeCinzas-CMD.exe (terminal)
rem        e, se o Inno Setup 6 estiver instalado, instalador\CronicasDeCinzas-Instalador-1.0.0.exe
rem  Uso:  build.bat           (testa, compila e gera o instalador)
rem        build.bat semtestes (pula os testes)
rem ============================================================================
setlocal EnableExtensions
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERRO] Python nao encontrado no PATH. Instale o Python 3.10+ de python.org ^(marque "Add to PATH" e mantenha o tcl/tk^).
  exit /b 1
)

if not exist .venv (
  echo [setup] Criando ambiente virtual .venv ...
  python -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat || exit /b 1
python -m pip install --quiet --upgrade pip pyinstaller || exit /b 1

python -c "import tkinter" 2>nul
if errorlevel 1 (
  echo [ERRO] tkinter ausente neste Python. Reinstale o Python incluindo "tcl/tk and IDLE".
  exit /b 1
)

if /i "%~1"=="semtestes" goto compilar
echo [1/4] Executando testes ...
python -m unittest discover -s tests || (echo [ERRO] Testes falharam. & exit /b 1)

:compilar
set "ICONE="
if exist assets\icone.ico set "ICONE=--icon assets\icone.ico"

echo [2/4] Gerando CronicasDeCinzas.exe ^(interface grafica, sem console^) ...
pyinstaller --noconfirm --clean --onefile --windowed --name CronicasDeCinzas ^
  --paths . --distpath dist --workpath build\gui --specpath build %ICONE% main_gui.py || exit /b 1

echo [3/4] Gerando CronicasDeCinzas-CMD.exe ^(terminal^) ...
pyinstaller --noconfirm --clean --onefile --console --name CronicasDeCinzas-CMD ^
  --paths . --distpath dist --workpath build\cmd --specpath build %ICONE% main_cmd.py || exit /b 1

echo [4/4] Gerando o instalador ...
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC (
  echo [AVISO] Inno Setup 6 nao encontrado. Instale com:  winget install JRSoftware.InnoSetup
  echo         Os executaveis ja estao prontos em dist\ . Depois rode:  ISCC installer.iss
  exit /b 0
)
"%ISCC%" installer.iss || exit /b 1

echo.
echo Pronto:
echo   dist\CronicasDeCinzas.exe
echo   dist\CronicasDeCinzas-CMD.exe
echo   instalador\CronicasDeCinzas-Instalador-1.0.0.exe
exit /b 0
