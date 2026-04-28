@echo off
chcp 65001 > nul
echo [api-test-dwp] 启动 mitmdump，监听端口 12138
echo [api-test-dwp] Ctrl+C 停止
mitmdump -s "%~dp0capture_addon.py" --listen-port 12138
