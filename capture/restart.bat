@echo off
chcp 65001 > nul
echo [api-test-dwp] 重启 mitmdump，监听端口 12138
call "%~dp0stop.bat"
echo [api-test-dwp] 等待 1 秒后重新启动
ping 127.0.0.1 -n 2 > nul
mitmdump -s "%~dp0capture_addon.py" --listen-port 12138
