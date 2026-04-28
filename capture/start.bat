@echo off
chcp 65001 > nul
cd /d %~dp0
echo [api-test-dwp] 启动 mitmdump，监听端口 12138
echo [api-test-dwp] JSONL 输出: %~dp0latest.jsonl
echo [api-test-dwp] 可扩展前缀: %~dp0allowed_prefixes.txt
echo [api-test-dwp] Ctrl+C 停止
mitmdump -s capture_addon.py --listen-port 12138
