# -*- coding: utf-8 -*-
"""
生成 00_全目录.md。
数字和清单都从实际文件算，不手写——手写的数字必错。
"""
import os
import re

# 根目录由脚本自身位置推算：scripts/ 的上一级
# 这样放到任何机器、任何路径下都能直接跑，不用改配置
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "00_全目录.md")

# 顺序 = 读者该走的顺序
SECTIONS = [
    ("入口", "根目录", [
        "SKILL.md", "README.md", "使用说明.md", "00_全目录.md",
        "CHANGELOG.md", "LICENSE",
    ]),
    ("第一层 · 方法（怎么想）", "method", None),
    ("第二层 · 能力（怎么办）", "capabilities", None),
    ("知识层说明", "knowledge", None),
    ("第三层 · 制度（规定是什么）", "knowledge/制度", None),
    ("第四层 · 认知（凭什么这么说）", "knowledge/认知", None),
    ("依据 · 思想（拿什么立场看）", "knowledge/思想", None),
    ("引擎 · 原子库（可调用知识库）", "knowledge/原子库", None),
    ("第五层 · 表达（怎么说）", "express", None),
    ("侧镜 · 判断（换个处境还成立吗）", "judgement", None),
    ("补充 · 竞赛事实库", "knowledge/竞赛", None),
    ("补充 · 赚钱与防骗", "knowledge/赚钱", None),
    ("契约 · 模块之间怎么接力", "shared", None),
    ("脚本", "scripts", None),
]


# 根文件的用途没法从正文抽，固定写
ROOT_DESC = {
    "SKILL.md": "调度台：接住问题 → 判断材料 → 路由到某一层 → 执行 → 输出契约 → 两道自检",
    "README.md": "对外门面：这是什么、能干什么、怎么装、为什么值得用",
    "使用说明.md": "**第一次用先看这份**：三步上手 + 八类问题 + 七个常见场景怎么串",
    "00_全目录.md": "就是这一页：全部文件索引，数字由脚本算",
    "CHANGELOG.md": "版本变更记录",
    "LICENSE": "许可条款",
    "scripts/gen_catalog.py": "生成这一页，别手改数字",
}


# 制度层正文第一行是收录日期，抽不出用途，固定写
DESC_OVERRIDE = {
    "00_制度总览.md": "八个制度节点 × 四条主线的学期时间轴：一眼看他站在哪个窗口、关没关",
    "01_学籍与专业.md": "转专业、大类分流、辅修双学位、休学复学——**最早关闭的那批窗口**",
    "02_绩点与考核.md": "四种 GPA 算法、挂科与重修、三条路各自的绩点门槛",
    "03_保研.md": "推免四个硬门槛、2026 新规（优营失效、预推免前置）、加分收紧",
    "04_考研.md": "报名与考试时间轴、学硕专硕、调剂、二战成本",
    "05_出国.md": "GPA 换算、语言成绩、申请材料、**GPA 不可逆**",
    "06_就业.md": "秋招春招时间轴、应届生身份、三方协议、报到证已取消、档案与户口",
    "07_科研与竞赛.md": "大创、本科生发论文、专利、竞赛目录与加分规则",
    "08_奖助与费用.md": "奖学金、助学金、助学贷款、困难认定（**不认定就摸不到四年几万块**）",
    "00_竞赛总览.md": "Ⅰ/Ⅱ/Ⅲ 类分档规则、全赛事速查、全年时间轴、三选一建议",
    "01_一类赛事.md": "中国国际大学生创新大赛、挑战杯大挑、挑战杯小挑（含 2026 硬规则）",
    "02_二类赛事.md": "ICPC、电赛、集创赛、三创赛、iCAN、蓝桥杯",
    "03_其他榜单赛事.md": "竞赛目录内其余 30+ 项简表",
    "00_防骗与红线.md": "兼职副业的骗局清单与法律红线",
    "存档契约.md": "什么该存、存哪、四种状态（进行中／已结论／悬置／废弃）",
    "术语表.md": "同一个词在库里的唯一含义，避免各层各说一套",
    "组合契约.md": "多个模块同时要用时怎么排顺序：从最终交付倒推，缺的往前补",
}

SKIP_PREFIX = ("收录日期", "依据", "本份", "⚠️", "对应认知层")


# 同名文件（README 有好几个）必须按路径区分
REL_DESC = {
    "knowledge/README.md": "知识层总说明：客观规定、认知依据、观点层各管什么、怎么分工",
    "method/README.md": "方法层说明：十四个动作怎么选、怎么串",
    "knowledge/思想/00_思想原子导航.md": "观点层学习入口：两种用法、两档措辞、五条调用纪律",
    "knowledge/思想/01_思想原子卡.md": "本人认可的观点原文，按思想纲领／参考认知分档；统一生成，勿手改",
    "knowledge/思想/02_问题-原子对照表.md": "卡点信号 → 取哪条观点 → 拆什么 → 落回哪个模块",
    "method/14_思想校准.md": "不缺步骤、缺立场时取一条观点换角度，用完落回能力模块",
    "knowledge/原子库/SKILL.md": "原子库检索引擎入口：触发条件、状态门禁、输出契约",
    "knowledge/原子库/README.md": "引擎目录说明：真源关系、数据字段、更新方式",
    "express/README.md": "表达层说明：六个动作按产出物分，先定要交什么再选",
    "judgement/00_索引与用法.md": "判断层怎么用：260 条按主题分组，每条带边界，只能当参考视角",
    "knowledge/认知/00_主题总表.md": "11 个认知主题的总表：每个主题几条、厚度如何",
}


def one_liner(path):
    """从文件里抽一句话用途。"""
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    base = os.path.basename(path)
    if rel in ROOT_DESC:
        return ROOT_DESC[rel]
    if rel in REL_DESC:
        return REL_DESC[rel]
    if base in DESC_OVERRIDE:
        return DESC_OVERRIDE[base]
    try:
        t = open(path, encoding="utf-8").read()
    except Exception:
        return ""

    # 判断层：条数动态取，主题从文件名取
    if rel.startswith("judgement/"):
        m = re.search(r"本份\s*(\d+)\s*条", t)
        topic = re.sub(r"^\d+_", "", base[:-3])
        return ("%s 条判断 · 换个处境看「%s」" % (m.group(1), topic)) if m \
            else ("换个处境看「%s」" % topic)
    lines = t.split("\n")

    # frontmatter 里的「交出:」
    if lines and lines[0].strip() == "---":
        for ln in lines[1:40]:
            if ln.strip() == "---":
                break
            if ln.startswith("交出:"):
                v = ln.split(":", 1)[1].strip()
                v = re.sub(r"[*`]", "", v)
                return v.split("（")[0].strip()[:80]

    # > 用途：xxx  /  > **用途**：xxx
    for ln in lines[:20]:
        s = ln.strip()
        m = re.match(r"^>\s*(?:\*\*)?用途(?:\*\*)?[:：]\s*(.+)$", s)
        if m:
            return re.sub(r"[*`]", "", m.group(1)).strip()[:80]
        m = re.match(r"^>\s*(?:\*\*)?这一(块|页)讲什么(?:\*\*)?[:：]\s*(.+)$", s)
        if m:
            return re.sub(r"[*`]", "", m.group(2)).strip()[:80]

    # 第一段正文（跳过元信息行）
    for ln in lines[1:20]:
        s = ln.strip()
        if not s.startswith(">"):
            continue
        body = re.sub(r"[*`>]", "", s).strip()
        if len(body) < 8:
            continue
        if body.startswith(SKIP_PREFIX):
            continue
        return body[:80]
    return ""


def stat(path):
    # 按行迭代，别用 read().count("\n") + 1：文件末尾有换行时会整体多算 1 行
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _build(self_lines):
    out = []
    global total_files, total_lines, md_files, md_lines
    total_files = 0
    total_lines = 0
    md_files = 0
    md_lines = 0

    out.append("# 全目录")
    out.append("")
    out.append("> 这套库有多少东西、每个文件干什么。一页看完，不用翻别处。")
    out.append("> **这份文件由 `scripts/gen_catalog.py` 生成**，数字是算出来的。改了文件重跑一次，别手改数字。")
    out.append("")
    out.append("**怎么读**：想知道某件事该找谁，从下面的标题找；只想快速开始，看 `使用说明.md`。")
    out.append("")
    out.append("---")
    out.append("")

    for title, rel, explicit in SECTIONS:
        out.append("## " + title)
        out.append("")
        if explicit:
            files = [os.path.join(ROOT, f) for f in explicit]
            files = [f for f in files if os.path.isfile(f)]
        else:
            d = os.path.join(ROOT, rel)
            if not os.path.isdir(d):
                out.append("（这一层还没有内容）")
                out.append("")
                continue
            ext = ".py" if rel == "scripts" else ".md"
            files = sorted(
                os.path.join(d, f) for f in os.listdir(d)
                if f.endswith(ext) and f != "_索引.md"
            )

        # 排除自身：否则每次重跑，自己的行数一变，合计也跟着变
        files = [f for f in files if os.path.abspath(f) != os.path.abspath(OUT)]

        out.append("| 文件 | 行数 | 干什么 |")
        out.append("|---|---|---|")
        sec_lines = 0
        for p in files:
            n = stat(p)
            shown = os.path.relpath(p, ROOT).replace("\\", "/")
            out.append("| `%s` | %d | %s |" % (shown, n, one_liner(p)))
            sec_lines += n
            total_files += 1
            total_lines += n
            if p.lower().endswith(".md"):
                md_files += 1
                md_lines += n
        out.append("")
        out.append("**小计：%d 个文件 / %d 行**" % (len(files), sec_lines))
        out.append("")

    out.append("---")
    out.append("")
    out.append("## 合计")
    out.append("")
    out.append("| 项 | 数 |")
    out.append("|---|---|")
    out.append("| 正文 md | **%d** 份 / **%d** 行 |" % (md_files, md_lines))
    out.append("| 本页自身 | 1 份 / %d 行 |" % self_lines)
    out.append("| 脚本与许可 | %d 个 / %d 行 |" % (total_files - md_files, total_lines - md_lines))
    out.append("| **合计** | **%d** 个文件 / **%d** 行 |" % (total_files + 1, total_lines + self_lines))
    out.append("")

    return out


def build(self_lines):
    """生成全目录的正文行。self_lines 是上一轮算出的「本页自身行数」。"""
    global total_files, total_lines, md_files, md_lines
    total_files = total_lines = md_files = md_lines = 0
    return _build(self_lines)


def main():
    # 本页要统计自己，就存在「写多少行 → 自己的行数变 → 合计也跟着变」的循环。
    # 解法：迭代到不动点，通常两轮就稳定。
    self_lines = 0
    for _ in range(4):
        out = build(self_lines)
        text = "\n".join(out).rstrip("\n")
        # 必须和 stat() 的口径一致：数实际内容行，不是数列表元素
        real = text.count("\n") + 1
        if real == self_lines:
            break
        self_lines = real

    # newline="\n" 必须写死：Windows 下默认会把 \n 写成 \r\n，
    # 一转 CRLF 就跟镜像的逐字节校验打架，每次都要重来一遍。
    open(OUT, "w", encoding="utf-8", newline="\n").write(text)
    print("已生成 00_全目录.md：%d 个文件 / %d 行（含本页自身 %d 行）"
          % (total_files + 1, total_lines + self_lines, self_lines))


if __name__ == "__main__":
    main()
