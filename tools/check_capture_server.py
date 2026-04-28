# -*- coding: utf-8 -*-
"""检查 12138 端口抓包服务器状态。

用法：
    python check_capture_server.py
退出码：
    0  RUNNING           端口已被 mitmdump 类进程监听
    1  NOT_RUNNING       端口未被监听
    2  PORT_OCCUPIED     端口被占用但无法确定是否 mitmdump
"""

import socket
import subprocess
import sys

PORT = 12138
HOST = "127.0.0.1"


def _port_listening(host: str, port: int, timeout: float = 0.5) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def _pid_on_port(port: int):
    """Windows 下用 netstat 查 LISTENING PID。"""
    try:
        out = subprocess.check_output(
            ["netstat", "-ano"], shell=False, stderr=subprocess.DEVNULL
        ).decode("gbk", errors="ignore")
    except Exception:
        return None
    for line in out.splitlines():
        if f":{port} " in line and "LISTENING" in line:
            parts = line.split()
            if parts:
                return parts[-1]
    return None


def _pid_exe(pid: str):
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            shell=False, stderr=subprocess.DEVNULL
        ).decode("gbk", errors="ignore")
        # "image.exe","PID","...","..."
        if out.strip():
            return out.strip().split(",")[0].strip('"')
    except Exception:
        pass
    return None


def main() -> int:
    listening = _port_listening(HOST, PORT)
    if not listening:
        print("NOT_RUNNING")
        return 1

    pid = _pid_on_port(PORT)
    if pid is None:
        print("RUNNING")  # 能连通但查不到 PID，视为已运行
        return 0

    exe = _pid_exe(pid) or ""
    exe_lower = exe.lower()
    if "mitm" in exe_lower or "python" in exe_lower:
        print(f"RUNNING pid={pid} exe={exe}")
        return 0

    print(f"PORT_OCCUPIED pid={pid} exe={exe}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
