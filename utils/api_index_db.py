# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""page_api 覆盖索引的 SQLite 读写工具。"""

import json
import os
import sqlite3
from typing import Dict, Iterable, List, Optional


DB_FILENAME = "page_api_index.sqlite3"


def get_default_db_path(tools_dir: str) -> str:
    """返回 tools 目录下默认 SQLite 索引路径。"""
    return os.path.join(tools_dir, DB_FILENAME)


def connect(db_path: str) -> sqlite3.Connection:
    """创建连接并使用 Row，便于按字段名读取。"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    """确保索引表结构存在。"""
    _drop_legacy_api_methods_table(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS api_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_url TEXT NOT NULL,
            api_name TEXT NOT NULL,
            api_desc TEXT DEFAULT '',
            Author TEXT DEFAULT '',
            "Create Date" TEXT DEFAULT '',
            "Update Date" TEXT DEFAULT '',
            method TEXT DEFAULT '',
            file TEXT DEFAULT '',
            class_name TEXT DEFAULT '',
            bases_json TEXT DEFAULT '[]',
            line INTEGER DEFAULT 0,
            mtime INTEGER DEFAULT 0,
            url_literal TEXT DEFAULT '',
            UNIQUE(api_url, api_name, file, line)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_methods_url ON api_methods(api_url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_methods_method_url ON api_methods(method, api_url)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_api_methods_file ON api_methods(file)")
    conn.commit()


def _drop_legacy_api_methods_table(conn: sqlite3.Connection) -> None:
    """旧版调试库若字段名不符合当前约定，直接重建生成型索引表。"""
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='api_methods'"
    ).fetchone()
    if not row:
        return
    columns = {item[1] for item in conn.execute("PRAGMA table_info(api_methods)").fetchall()}
    required = {"api_url", "api_name", "api_desc", "Author", "Create Date", "Update Date", "method"}
    if not required.issubset(columns):
        conn.execute("DROP TABLE api_methods")


def replace_index(db_path: str, records: Iterable[dict], metadata: Optional[Dict[str, str]] = None) -> None:
    """用 records 原子替换当前索引。"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with connect(db_path) as conn:
        ensure_schema(conn)
        conn.execute("DELETE FROM api_methods")
        conn.execute("DELETE FROM metadata")
        if metadata:
            conn.executemany(
                "INSERT INTO metadata(key, value) VALUES(?, ?)",
                [(str(k), str(v)) for k, v in metadata.items()],
            )
        conn.executemany(
            """
            INSERT INTO api_methods(
                api_url, api_name, api_desc, Author, "Create Date", "Update Date",
                method, file, class_name, bases_json, line, mtime, url_literal
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.get("api_url") or item.get("pure_path") or "",
                    item.get("api_name") or item.get("method") or "",
                    item.get("api_desc") or "",
                    item.get("author") or "",
                    item.get("create_date") or "",
                    item.get("update_date") or "",
                    (item.get("http_method") or item.get("request_method") or "").upper(),
                    item.get("file") or "",
                    item.get("class") or item.get("class_name") or "",
                    json.dumps(item.get("bases") or [], ensure_ascii=False),
                    int(item.get("line") or 0),
                    int(item.get("mtime") or 0),
                    item.get("url_literal") or item.get("api_url") or item.get("pure_path") or "",
                )
                for item in records
            ],
        )
        conn.commit()


def load_methods(db_path: str) -> List[dict]:
    """读取所有已覆盖接口记录；数据库不存在时返回空列表。"""
    if not os.path.isfile(db_path):
        return []
    with connect(db_path) as conn:
        ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT api_url, api_name, api_desc, Author, "Create Date", "Update Date",
                   method, file, class_name, bases_json, line, mtime, url_literal
            FROM api_methods
            ORDER BY file, line, api_name, api_url
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def load_metadata(db_path: str) -> Dict[str, str]:
    """读取索引元信息。"""
    if not os.path.isfile(db_path):
        return {}
    with connect(db_path) as conn:
        ensure_schema(conn)
        rows = conn.execute("SELECT key, value FROM metadata").fetchall()
    return {row["key"]: row["value"] for row in rows}


def _row_to_dict(row: sqlite3.Row) -> dict:
    try:
        bases = json.loads(row["bases_json"] or "[]")
    except json.JSONDecodeError:
        bases = []
    return {
        "api_url": row["api_url"],
        "pure_path": row["api_url"],
        "api_name": row["api_name"],
        "api_desc": row["api_desc"],
        "author": row["Author"],
        "Author": row["Author"],
        "create_date": row["Create Date"],
        "Create Date": row["Create Date"],
        "update_date": row["Update Date"],
        "Update Date": row["Update Date"],
        "http_method": row["method"],
        "method": row["method"],
        "file": row["file"],
        "class": row["class_name"],
        "class_name": row["class_name"],
        "bases": bases,
        "line": row["line"],
        "mtime": row["mtime"],
        "url_literal": row["url_literal"],
    }
