@echo off

cd /d "%~dp0"

echo Adding changes...
git add .

echo Committing...
git commit -m "update %date% %time%"

echo Pushing to GitHub...
git push

echo Done.
