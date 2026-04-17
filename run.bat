@echo off
cd C:\Users\tote5\viral-collector
echo 수집 시작...
python collector.py daily
echo.
echo GitHub push 중...
git add .
git commit -m "daily update %date:~0,4%-%date:~5,2%-%date:~8,2%"
git push
if errorlevel 1 (
    echo push 실패, 강제 push 시도...
    git push --force
)
echo.
echo 완료!
pause