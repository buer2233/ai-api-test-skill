@echo off
chcp 65001 > nul
echo [api-test-dwp] 查找并停止占用 12138 的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :12138 ^| findstr LISTENING') do (
    echo [api-test-dwp] 停止 PID=%%a
    taskkill /PID %%a /F
)
echo [api-test-dwp] 完成
