#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""重新生成 00_全目录.md 的规模统计。

用法：python scripts/gen_catalog.py
数字全部实算，不手写。新增赛事文件后跑一次即可。
"""

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTFILE = ROOT / "00_全目录.md"
SKIP_DIRS = {".git", "__pycache__", ".obsidian"}
SKIP_FILES = {"00_全目录.md"}

GROUPS = [
    ("调度台与说明", ROOT, ["SKILL.md", "README.md", "LICENSE", "使用说明.md"]),
    ("competitions/ · 按赛事", ROOT / "competitions", None),
    ("shared/ · 赛事无关", ROOT / "shared", None),
    ("语料/ · 对照物", ROOT / "语料", "summary"),
]


def desc_of(path: Path) -> str:
    """取 frontmatter 的『接手』字段；没有就用第一个标题。"""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^接手:\s*(.+)$", text, re.M)
    if m:
        return m.group(1).strip()
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if m:
        return re.sub(r"^\d+\s*·\s*", "", m.group(1).strip())
    return "—"


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def main():
    rows = []  # (group, relpath, desc, lines, 份数)
    total_files = 0
    total_lines = 0

    for group, base, fixed in GROUPS:
        if fixed == "summary":
            # 语料按一级目录汇总，不逐份列（一百多份）
            loose_desc = {"🗂 语料导航.md": "七个目录各什么时候取，三条取料规矩"}
            for p in sorted(x for x in base.iterdir()
                            if x.is_file() and x.suffix in {".md", ".txt"}):
                n = line_count(p)
                rows.append((group, p.relative_to(ROOT).as_posix(),
                             loose_desc.get(p.name, "—"), n, 1))
                total_files += 1
                total_lines += n
            for d in sorted(x for x in base.iterdir() if x.is_dir()):
                fs = sorted(p for p in d.rglob("*")
                            if p.is_file() and p.suffix in {".md", ".txt"})
                if not fs:
                    continue
                n = sum(line_count(p) for p in fs)
                rows.append((group, d.relative_to(ROOT).as_posix() + "/",
                             f"{len(fs)} 份", n, len(fs)))
                total_files += len(fs)
                total_lines += n
            continue

        if fixed:
            paths = [base / n for n in fixed if (base / n).exists()]
        elif group.startswith("competitions/"):
            # 赛事已拆成模块目录，递归统计每个模块内的四块
            paths = sorted(
                p for p in base.rglob("*")
                if p.is_file() and p.suffix in {".md", ".txt"}
                and p.name not in SKIP_FILES
                and not any(d in SKIP_DIRS for d in p.parts)
            )
        else:
            paths = sorted(
                f for f in base.iterdir()
                if f.is_file() and f.suffix in {".md", ".txt"} and f.name not in SKIP_FILES
            )
        for p in paths:
            rel = p.relative_to(ROOT).as_posix()
            n = line_count(p)
            rows.append((group, rel, desc_of(p), n, 1))
            total_files += 1
            total_lines += n

    # 脚本自身计入脚本与许可一类
    scripts = sorted(
        f.name for f in (ROOT / "scripts").iterdir()
        if f.is_file() and f.suffix == ".py"
    )
    for name in scripts:
        p = ROOT / "scripts" / name
        n = line_count(p)
        rows.append(("scripts/ · 脚本", p.relative_to(ROOT).as_posix(), "重新生成全目录", n, 1))
        total_files += 1
        total_lines += n

    out = []
    out.append("# 全目录 · 竞赛线")
    out.append("")
    out.append("> 由 `scripts/gen_catalog.py` 实算生成，数字不手写。新增文件后跑一次脚本。")
    out.append("")
    out.append("---")
    out.append("")

    for group, _, _ in GROUPS + [("scripts/ · 脚本", None, None)]:
        subset = [r for r in rows if r[0] == group]
        if not subset:
            continue
        out.append("## " + group)
        out.append("")
        out.append("| 文件 | 管什么 | 行数 |")
        out.append("|---|---|---:|")
        for _, rel, desc, n, _c in subset:
            out.append(f"| `{rel}` | {desc} | {n:,} |")
        out.append("")
        cnt = sum(r[4] for r in subset)
        out.append(f"**小计：{cnt} 份 / {sum(r[3] for r in subset):,} 行**")
        out.append("")

    out.append("---")
    out.append("")
    out.append("## 合计")
    out.append("")
    out.append("| 项 | 数 |")
    out.append("|---|---|")
    out.append(f"| 文件（不含本页） | **{total_files}** 个 |")
    out.append(f"| 正文行数 | **{total_lines:,}** 行 |")
    out.append(f"| 本页自身 | 1 份 |")
    out.append("")

    OUTFILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已生成 00_全目录.md：{total_files} 个文件 / {total_lines} 行（不含本页）")


if __name__ == "__main__":
    main()
