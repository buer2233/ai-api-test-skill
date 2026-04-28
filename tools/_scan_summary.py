# -*- coding: utf-8 -*-
"""对 page_api_index.json 做汇总统计（一次性脚本）。"""

import json
import os
from collections import Counter, defaultdict

IDX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page_api_index.json")

with open(IDX, "r", encoding="utf-8") as f:
    idx = json.load(f)

methods = idx["methods"]
stats = idx["_stats"]

print("=== 全量扫描统计 ===")
print("scanned_files :", stats["scanned_files"])
print("total_methods :", stats["total_methods"])
print("unique_paths  :", stats["unique_paths"])
print("generated_at  :", idx["generated_at"])
print()

# 按顶级模块统计
mod_counter = Counter()
mod_files = defaultdict(set)
mod_classes = defaultdict(set)
for m in methods:
    f = m["file"].replace("\\", "/")
    parts = f.split("/")
    try:
        i = parts.index("page_api")
        mod = parts[i + 1] if i + 1 < len(parts) else "<root>"
    except ValueError:
        mod = "<unknown>"
    mod_counter[mod] += 1
    mod_files[mod].add(f)
    mod_classes[mod].add(m["class"])

print("=== 按 page_api/<module> 顶级模块统计 ===")
print(f'{"模块":<45} {"方法":>8} {"文件":>6} {"类":>5}')
print("-" * 70)
for mod, cnt in sorted(mod_counter.items(), key=lambda x: -x[1]):
    print(f"{mod:<45} {cnt:>8} {len(mod_files[mod]):>6} {len(mod_classes[mod]):>5}")

# URL 前两段分布
prefix_counter = Counter()
for m in methods:
    p = m["pure_path"]
    segs = p.strip("/").split("/")
    seg2 = "/" + "/".join(segs[:2])
    prefix_counter[seg2] += 1

print()
print("=== URL 前两段路径 TOP 30 ===")
print(f'{"前缀":<50} {"数量":>6}')
print("-" * 60)
for pfx, cnt in prefix_counter.most_common(30):
    print(f"{pfx:<50} {cnt:>6}")

# 类数统计
cls_counter = Counter(m["class"] for m in methods)
print()
print(f"=== 方法最多的 API 类 TOP 20（共 {len(cls_counter)} 个类）===")
print(f'{"类名":<55} {"方法数":>6}')
print("-" * 65)
for c, n in cls_counter.most_common(20):
    print(f"{c:<55} {n:>6}")

# 文件数统计
file_counter = Counter(m["file"] for m in methods)
print()
print(f"=== 方法最多的文件 TOP 15（共 {len(file_counter)} 个 py 文件）===")
print(f'{"文件":<80} {"方法数":>6}')
print("-" * 90)
for fn, n in file_counter.most_common(15):
    print(f"{fn:<80} {n:>6}")
