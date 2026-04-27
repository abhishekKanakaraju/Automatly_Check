@echo off

cd /d "%~dp0"

echo Killing existing Python process...
taskkill /F /IM python.exe 2>nul

echo Pulling latest from GitHub...
git pull origin main --rebase

echo Adding changes...
git add .

echo Committing...
git commit -m "update %date% %time%"

echo Pushing to GitHub...
git push origin main

echo.
echo Done! All changes pushed to GitHub.
pause