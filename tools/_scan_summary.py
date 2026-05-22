# -*- coding: utf-8 -*-
# Author: dengwanpeng

"""对 page_api_index.sqlite3 做汇总统计（一次性脚本）。"""

import os
import sys
from collections import Counter, defaultdict

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(TOOLS_DIR)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from skill_utils.api_index_db import get_default_db_path, load_metadata, load_methods  # noqa: E402


IDX = get_default_db_path(TOOLS_DIR)
methods = load_methods(IDX)
metadata = load_metadata(IDX)

print("=== 全量扫描统计 ===")
print("scanned_files :", metadata.get("scanned_files", ""))
print("total_methods :", metadata.get("total_methods", len(methods)))
print("unique_paths  :", metadata.get("unique_paths", len({m["api_url"] for m in methods})))
print("generated_at  :", metadata.get("generated_at", ""))
print()

mod_counter = Counter()
mod_files = defaultdict(set)
mod_classes = defaultdict(set)
for item in methods:
    file_path = item["file"].replace("\\", "/")
    parts = file_path.split("/")
    try:
        index = parts.index("page_api")
        module = parts[index + 1] if index + 1 < len(parts) else "<root>"
    except ValueError:
        module = "<unknown>"
    mod_counter[module] += 1
    mod_files[module].add(file_path)
    mod_classes[module].add(item["class"])

print("=== 按 page_api/<module> 顶级模块统计 ===")
print(f'{"模块":<45} {"方法":>8} {"文件":>6} {"类":>5}')
print("-" * 70)
for module, count in sorted(mod_counter.items(), key=lambda x: -x[1]):
    print(f"{module:<45} {count:>8} {len(mod_files[module]):>6} {len(mod_classes[module]):>5}")

prefix_counter = Counter()
for item in methods:
    path = item["api_url"]
    segments = path.strip("/").split("/")
    prefix = "/" + "/".join(segments[:2])
    prefix_counter[prefix] += 1

print()
print("=== URL 前两段路径 TOP 30 ===")
print(f'{"前缀":<50} {"数量":>6}')
print("-" * 60)
for prefix, count in prefix_counter.most_common(30):
    print(f"{prefix:<50} {count:>6}")

class_counter = Counter(item["class"] for item in methods)
print()
print(f"=== 方法最多的 API 类 TOP 20（共 {len(class_counter)} 个类）===")
print(f'{"类名":<55} {"方法数":>6}')
print("-" * 65)
for class_name, count in class_counter.most_common(20):
    print(f"{class_name:<55} {count:>6}")

file_counter = Counter(item["file"] for item in methods)
print()
print(f"=== 方法最多的文件 TOP 15（共 {len(file_counter)} 个 py 文件）===")
print(f'{"文件":<80} {"方法数":>6}')
print("-" * 90)
for file_path, count in file_counter.most_common(15):
    print(f"{file_path:<80} {count:>6}")
