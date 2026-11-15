# -*- coding: utf-8 -*-
"""
生涯发展报告出件脚本（成长赛道）

用法：
  python build_report.py 输入.md [-o 输出.docx] [--check-only]

功能：
  1. 校验官方硬约束：文字 ≤2000 字、图表 ≤5 张（PDF ≤10MB 由导出方确认）
  2. 校验推演标注：列出所有 〔推演〕 与 〔待填：XX〕，生成确认清单
  3. 生成 docx，按 G-006 排版规格：大标题一号 / 小标题小二 / 正文三号

依赖：python-docx
"""
import argparse
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt
    from docx.oxml.ns import qn
except ImportError:
    print("[!] 缺少 python-docx，请先安装：pip install python-docx")
    sys.exit(1)

# 官方硬约束（第四届附件1）
MAX_CHARS = 2000
MAX_FIGURES = 5

# G-006 排版规格（制作规范，非官方规定）
SIZE_H1 = Pt(26)   # 一号
SIZE_H2 = Pt(18)   # 小二
SIZE_BODY = Pt(16)  # 三号
FONT_H = "黑体"
FONT_BODY = "宋体"

RE_TUICE = re.compile(r"〔推演〕")
RE_TODO = re.compile(r"〔待填：([^〕]*)〕")
RE_IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def count_chars(text: str) -> int:
    """中文字数口径：去掉所有空白字符后的字符数（含标点）。"""
    return len(re.sub(r"\s", "", text))


def set_font(run, name: str, size):
    run.font.name = name
    run.font.size = size
    # 中文字体需设置 eastAsia，否则 Word 里显示成默认字体
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)


def parse_markdown(md_text: str):
    """极简 markdown 解析：只处理 #/##/正文/列表/图片，够用即可。"""
    blocks = []
    for line in md_text.splitlines():
        s = line.rstrip()
        if not s.strip():
            continue
        if RE_IMG.fullmatch(s.strip()):
            alt = re.search(r"!\[([^\]]*)\]", s.strip())
            src = re.search(r"\(([^)]*)\)", s.strip())
            blocks.append(("img", (alt.group(1) if alt else "", src.group(1) if src else "")))
        elif s.startswith("## "):
            blocks.append(("h2", s[3:].strip()))
        elif s.startswith("# "):
            blocks.append(("h1", s[2:].strip()))
        elif s.startswith(("- ", "* ")) or re.match(r"^\d+\.\s", s):
            blocks.append(("li", re.sub(r"^(\d+\.|[-*])\s*", "", s).strip()))
        else:
            blocks.append(("p", s.strip()))
    return blocks


def build_docx(blocks, out_path: Path):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = FONT_BODY
    style.font.size = SIZE_BODY
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT_BODY)

    # 去掉正文样式的默认段后间距，中文排版更紧凑
    style.paragraph_format.space_after = Pt(0)

    for kind, content in blocks:
        if kind == "h1":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(6)
            set_font(p.add_run(content), FONT_H, SIZE_H1)
        elif kind == "h2":
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            set_font(p.add_run(content), FONT_H, SIZE_H2)
        elif kind == "li":
            p = doc.add_paragraph(style="List Bullet")
            set_font(p.add_run(content), FONT_BODY, SIZE_BODY)
        elif kind == "img":
            alt, src = content
            p = doc.add_paragraph()
            set_font(p.add_run(f"〔图：{alt or src}〕"), FONT_BODY, SIZE_BODY)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.first_line_indent = SIZE_BODY * 2
            set_font(p.add_run(content), FONT_BODY, SIZE_BODY)

    doc.save(str(out_path))


def main():
    ap = argparse.ArgumentParser(description="生涯发展报告出件与合规校验")
    ap.add_argument("input", help="输入的 Markdown 文件")
    ap.add_argument("-o", "--output", help="输出的 docx 路径，默认与输入同目录同名")
    ap.add_argument("--check-only", action="store_true", help="只做校验，不生成 docx")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f"[!] 找不到文件：{src}")
        sys.exit(1)

    md = src.read_text(encoding="utf-8")
    blocks = parse_markdown(md)

    # 字数：只统计实际会进正文的文字块（标题+段落+列表），图片占位不计
    body_text = "".join(c for k, c in blocks if k in ("h1", "h2", "p", "li"))
    n_chars = count_chars(body_text)
    n_figs = sum(1 for k, _ in blocks if k == "img")

    tuice = RE_TUICE.findall(md)
    todos = RE_TODO.findall(md)

    print("=" * 52)
    print("生涯发展报告 · 合规校验")
    print("=" * 52)

    ok = True

    status = "OK " if n_chars <= MAX_CHARS else "超限"
    print(f"[{status}] 文字 {n_chars} / {MAX_CHARS} 字")
    if n_chars > MAX_CHARS:
        print(f"        需删减 {n_chars - MAX_CHARS} 字。优先砍第一章（行业前景/政策/市场最易注水）。")
        ok = False

    status = "OK " if n_figs <= MAX_FIGURES else "超限"
    print(f"[{status}] 图表 {n_figs} / {MAX_FIGURES} 张")
    if n_figs > MAX_FIGURES:
        ok = False

    print()
    if tuice:
        print(f"[!] 推演补全 {len(tuice)} 处 → 必须生成《推演与待填确认清单》")
    if todos:
        print(f"[!] 待填 {len(todos)} 处：")
        for t in todos:
            print(f"      - {t}")

    if tuice or todos:
        print()
        print("    按 G-007：学生逐条确认前，不得输出「可提交」结论，也不得转 PDF。")
        print("    学生对每处推演有三个选项：属实 / 修改 / 删掉，默认是「删掉」。")

    print()
    if args.check_only:
        print("--check-only：已跳过 docx 生成。")
        sys.exit(0 if ok else 2)

    out = Path(args.output) if args.output else src.with_suffix(".docx")
    build_docx(blocks, out)
    print(f"[OK] 已生成：{out}")
    print("     排版：大标题一号 / 小标题小二 / 正文三号（黑体标题 + 宋体正文）")
    print("     请自行在 Word/WPS 中另存为 PDF，并确认 PDF ≤10MB。")

    sys.exit(0 if (ok and not todos) else 2)


if __name__ == "__main__":
    main()
