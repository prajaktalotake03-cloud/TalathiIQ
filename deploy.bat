@echo off
echo ===================================================
echo TalathiIQ - Pushing local updates to GitHub...
echo ===================================================
echo.

echo Configuring Git buffer size for large files...
git config http.postBuffer 1572864000

git add .
git commit -m "Deploy latest updates, working AI Mentor, and extracted PDF notes"
git push origin main

echo.
echo ===================================================
echo Changes pushed successfully!
echo.
echo Next steps:
echo 1. Go to Render.com or PythonAnywhere.com
echo 2. Trigger a deploy / reload.
echo ===================================================
pause
