@echo off
rem ============================================================
rem  Oil Roxwood - commit + push en un clic
rem  Usage : double-clic, ou  push.bat mon message de commit
rem  L'adresse du site est deduite du depot : rien a modifier ici.
rem ============================================================
cd /d "%~dp0"

if not exist ".git" (
  echo.
  echo   Ce dossier n'est pas encore un depot Git.
  echo   Lance d'abord, dans ce dossier :
  echo.
  echo     git init -b main
  echo     git remote add origin https://github.com/poulpizar01/Oil-Roxwood.git
  echo.
  pause
  exit /b 1
)

set MSG=%*
if "%MSG%"=="" set MSG=MAJ Oil Roxwood %date% %time:~0,5%

echo.
echo === Etat du depot ===
git status --short

echo.
echo === Commit : "%MSG%" ===
git add -A
git commit -m "%MSG%"

echo.
echo === Recuperation des commits des robots (sauvegardes, logs Discord) ===
git pull --rebase origin main
if errorlevel 1 (
  echo.
  echo   ATTENTION : le pull a echoue - conflit probable.
  echo   Regle le conflit, puis relance push.bat.
  pause
  exit /b 1
)

echo.
echo === Push vers GitHub ===
git push -u origin main
if errorlevel 1 (
  echo.
  echo   Le push a echoue. Verifie ton acces au depot.
  pause
  exit /b 1
)

for /f "delims=" %%u in ('git remote get-url origin 2^>nul') do set REMOTE=%%u
echo.
echo === Termine ! Le site se met a jour dans ~1 minute ===
if defined REMOTE echo     Depot : %REMOTE%
echo     Site  : voir Settings ^> Pages du depot
echo.
pause
