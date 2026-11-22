@echo off
rem Executa o jogo em modo terminal a partir do codigo-fonte (sem compilar).
cd /d "%~dp0"
python main.py --cmd %*
