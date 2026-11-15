# -*- coding: utf-8 -*-
"""
职业原子脚手架 —— 新建原子文件并自动登记索引。

用法（Windows，使用托管 Python）：
  python new_atom.py --name "核电运行工程师" --track "成长·高教组" --source "用户投喂"
  python new_atom.py --name "XXX" --track "通用" --source "待采集" --kind 通用
  python new_atom.py --name "XXX" --track "就业·职教组" --source "JD实录" --alias "别名1,别名2"

参数：
  --name    职业名称（必填）
  --track   适用赛道组别（必填，多个用逗号分隔）
  --source  来源（必填）：用户投喂 / JD实录 / 从业者访谈 / 待采集
  --alias   俗称或别名，逗号分隔（可选）
  --industry 所属行业（可选）
  --kind    原子种类：career（默认） / general
"""
import argparse
import datetime
import os
import re
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATOMS_DIR = os.path.join(SKILL_ROOT, "atoms")
INDEX_PATH = os.path.join(ATOMS_DIR, "索引.md")
TEMPLATE_PATH = os.path.join(ATOMS_DIR, "_原子模板.md")

KIND_DIR = {"career": "职业原子", "general": "通用原子"}
# 来源 -> 成熟度映射。来源不明的一律降级为「骨架」。
MATURITY_BY_SOURCE = {
    "用户投喂": "待校验",
    "JD实录": "待校验",
    "从业者访谈": "待校验",
    "待采集": "骨架",
}

# 文件名不允许出现的字符
INVALID_CHARS = r'[\\/:*?"<>|]'


def sanitize(name):
    cleaned = re.sub(INVALID_CHARS, "_", name).strip()
    return cleaned or "未命名原子"


def next_id(kind):
    """扫描现有原子文件，返回下一个可用 ID。"""
    folder = os.path.join(ATOMS_DIR, KIND_DIR[kind])
    prefix = "C" if kind == "career" else "G"
    max_num = 0
    if os.path.isdir(folder):
        for fn in os.listdir(folder):
            m = re.match(rf"^{prefix}-(\d{{3}})[-_]", fn)
            if m:
                max_num = max(max_num, int(m.group(1)))
    # 同时读索引表，避免已登记未落文件的 ID 冲突
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as f:
            for m in re.finditer(rf"\| {prefix}-(\d{{3}}) \|", f.read()):
                max_num = max(max_num, int(m.group(1)))
    return f"{prefix}-{max_num + 1:03d}"


def build_header(args, atom_id, maturity, today):
    lines = [
        "---",
        f"原子ID: {atom_id}",
        f"职业名称: {args.name}",
        f"俗称/别名: {args.alias or '（待补）'}",
        f"所属行业: {args.industry or '（待补）'}",
        f"典型雇主类型: （待补）",
        f"适用赛道组别: {args.track}",
        f"成熟度: {maturity}",
        f"来源: {args.source}",
        f"最后更新: {today}",
        "已用次数: 0",
        "---",
    ]
    return "\n".join(lines)


def render_template(args, atom_id, maturity, today):
    if not os.path.exists(TEMPLATE_PATH):
        raise SystemExit(f"[X] 找不到模板文件：{TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        body = f.read()

    new_header = build_header(args, atom_id, maturity, today)
    pattern = re.compile(r"```\n---\n原子ID:.*?\n```", re.DOTALL)
    if not pattern.search(body):
        raise SystemExit("[X] 模板格式已变更：未匹配到头部 YAML 代码块，请检查 _原子模板.md")
    body = pattern.sub("```\n" + new_header + "\n```", body, count=1)

    # 正文标题改为具体职业名
    body = body.replace("# 职业原子 · 著录模板", f"# {atom_id} · {args.name}", 1)
    return body


def append_index(atom_id, args, maturity, today):
    if not os.path.exists(INDEX_PATH):
        raise SystemExit(f"[X] 找不到索引文件：{INDEX_PATH}")
    with open(INDEX_PATH, encoding="utf-8") as f:
        content = f.read()

    row = f"| {atom_id} | {args.name} | {args.track} | {maturity} | {args.source} | 0 | {today} |"
    anchor = "| — | — | — | — | — | — | — |\n"
    if anchor not in content:
        raise SystemExit("[X] 索引表占位行已变更，请检查 atoms/索引.md 的「原子登记表」")
    content = content.replace(anchor, row + "\n" + anchor, 1)

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="新建职业原子并登记索引")
    parser.add_argument("--name", required=True, help="职业名称")
    parser.add_argument("--track", required=True, help="适用赛道组别，多个用逗号分隔")
    parser.add_argument("--source", required=True, help="来源：用户投喂/JD实录/从业者访谈/待采集")
    parser.add_argument("--alias", default="", help="俗称或别名，逗号分隔")
    parser.add_argument("--industry", default="", help="所属行业")
    parser.add_argument("--kind", default="career", choices=["career", "general"], help="原子种类")
    args = parser.parse_args()

    maturity = MATURITY_BY_SOURCE.get(args.source, "骨架")
    atom_id = next_id(args.kind)
    today = datetime.date.today().isoformat()

    safe_name = sanitize(args.name)
    folder = os.path.join(ATOMS_DIR, KIND_DIR[args.kind])
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{atom_id}-{safe_name}.md")

    if os.path.exists(file_path):
        raise SystemExit(f"[X] 目标文件已存在：{file_path}")

    content = render_template(args, atom_id, maturity, today)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    append_index(atom_id, args, maturity, today)

    print(f"[OK] 已创建原子：{file_path}")
    print(f"[OK] 索引已登记：{atom_id} | {args.name} | {maturity}")
    if maturity == "骨架":
        print("[!] 该原子为「骨架」级，仅可作提问线索，不得用于评级。补齐第 5 节（能力→证据对照表）后请更新成熟度。")


if __name__ == "__main__":
    main()
