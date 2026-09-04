@echo off
rem ============================================================
rem  Oil Roxwood - commit + push en un clic
rem  Usage : double-clic, ou  push.bat mon message de commit
rem  L'adresse du site est deduite du depot : rien a modifier ici.
rem
rem  Depuis septembre 2026, le depot a plusieurs auteurs : toi, le bot
rem  Discord (table des coffres, recrues, reponses aux ordres) et le robot
rem  GitHub Actions (logs, sauvegardes). Le bot ecrit environ toutes les
rem  minutes. Il arrive donc qu'il pousse un commit pile pendant le tien :
rem  GitHub refuse alors de deplacer la branche, avec un message du genre
rem  "cannot lock ref 'refs/heads/main': is at ... but expected ...".
rem
rem  Ce n'est pas une erreur a corriger, c'est une collision a rejouer.
rem  D'ou la boucle ci-dessous : pull + push, jusqu'a trois fois.
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

set ESSAI=0

:BOUCLE
set /a ESSAI+=1
echo.
echo === Essai %ESSAI%/3 - recuperation des commits des robots ===
git pull --rebase origin main
if errorlevel 1 goto CONFLIT

echo.
echo === Push vers GitHub ===
git push origin main
if not errorlevel 1 goto OK

if %ESSAI% GEQ 3 goto ECHEC
echo.
echo   Un robot a pousse pendant l'envoi. On rejoue dans 3 secondes...
timeout /t 3 /nobreak >nul
goto BOUCLE

:CONFLIT
echo.
echo   ATTENTION : le pull a echoue - conflit probable.
echo   Regle le conflit, puis relance push.bat.
pause
exit /b 1

:ECHEC
echo.
echo   Le push a echoue apres 3 essais.
echo   Si le message parle de "cannot lock ref", relance simplement push.bat.
echo   Sinon, verifie ton acces au depot.
pause
exit /b 1

:OK
for /f "delims=" %%u in ('git remote get-url origin 2^>nul') do set REMOTE=%%u
echo.
echo === Termine ! Le site se met a jour dans ~1 minute ===
if defined REMOTE echo     Depot : %REMOTE%
echo     Site  : voir Settings ^> Pages du depot
echo.
pause
