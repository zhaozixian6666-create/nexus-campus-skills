# -*- coding: utf-8 -*-
"""
Nexus 原子库检索引擎。

只读 data/atoms.jsonl 与 data/corpus.jsonl，不联网、不写文件。
状态门禁写在代码里（不靠提示词）：不是 ✅ 已认可的原子，一律不返回观点。

用法：
  python scripts/query.py --topic 人生感悟
  python scripts/query.py --scene 人际 --limit 3
  python scripts/query.py --keyword 选择 --json
  python scripts/query.py --id ATOM-038
  python scripts/query.py --scope corpus --book 底层逻辑
  python scripts/query.py --stats
"""
from pathlib import Path
import argparse
import json
import sys

DATA = Path(__file__).resolve().parent.parent / "data"


def load(name):
    p = DATA / name
    if not p.is_file():
        raise SystemExit("缺数据文件：%s（跑 build-atoms-engine.py 重建）" % p)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def clean_source(s):
    return (s or "").removeprefix("提炼自：").strip() or "未登记"


def short_source(s):
    """示例措辞里只留作者 + 书名，不带日期和原卡号。"""
    return clean_source(s).split("（")[0].strip()


def attribution(row, corpus=False):
    if corpus:
        return "引用须标作者 + 书名；📎 语料只作对照物，不说成本人判断"
    s = row.get("source", "")
    if s.startswith("子贤口述"):
        return "可以说「我一直这么说」"
    if s.startswith("提炼自"):
        return "必须标作者 + 书名：「这是从 %s 里提炼、我认可的一条」" % short_source(s)
    if row.get("status", "").startswith("📎 参考"):
        return "参考判断，出处待核：只能说「这是整理过的参考判断，原出处我没核到」，不当作本人认可，不说成本人原话"
    return "来源未登记，不外露"


def match(row, args, corpus=False):
    if args.id and row.get("id" if not corpus else "code") != args.id:
        return False
    if args.keyword and args.keyword not in (
            (row.get("view") or "") + (row.get("title") or "") + (row.get("judgement") or "")):
        return False
    if not corpus:
        if args.topic and args.topic not in row.get("topic", ""):
            return False
        if args.layer and args.layer not in row.get("layer", ""):
            return False
        if args.scene and args.scene not in row.get("scene", ""):
            return False
        if args.source == "oral" and not row.get("source", "").startswith("子贤口述"):
            return False
        if args.source == "published" and not row.get("source", "").startswith("提炼自"):
            return False
    else:
        if args.book and args.book not in (row.get("source", "") + row.get("book", "")):
            return False
        if args.topic:
            return False  # 语料没有主题维度，带主题查询时不混进来
    return True


def brief(row, corpus=False):
    if corpus:
        return {
            "code": row["code"], "title": row["title"],
            "judgement": row["judgement"],
            "source": row["source"], "status": row["status"],
            "atom": row.get("atom", ""),
            "对外说": attribution(row, corpus=True),
        }
    return {
        "id": row["id"], "topic": row["topic"], "layer": row["layer"],
        "scene": row["scene"], "type": row["type"],
        "view": row["view"], "source": clean_source(row["source"]),
        "status": row["status"], "tags": row["tags"],
        "对外说": attribution(row),
    }


def stats(atoms, corpus):
    def count(rows, pred):
        return sum(1 for r in rows if pred(r))
    return {
        "原子库": {
            "总计": len(atoms),
            "✅ 已认可": count(atoms, lambda r: r["status"].startswith("✅")),
            "📎 参考（来源待考）": count(atoms, lambda r: r["status"].startswith("📎 参考")),
            "⏳ 待确认": count(atoms, lambda r: r["status"].startswith("⏳")),
        },
        "九本书语料": {
            "总计": len(corpus),
            "✅ 已认可": count(corpus, lambda r: r["status"].startswith("✅")),
            "📎 语料": count(corpus, lambda r: r["status"].startswith("📎")),
        },
        "门禁": "可返回三档：✅ 已认可按归属措辞；📎 参考固定说「整理过的参考判断，出处待核」；九本书语料标作者书名。⏳ 待确认只给数量，不给观点。任何一档都不冒充本人原话。",
    }


def main():
    ap = argparse.ArgumentParser(description="Nexus 原子库检索")
    ap.add_argument("--topic", help="主题（仅原子）")
    ap.add_argument("--layer", help="层次，如 L1 / L5")
    ap.add_argument("--scene", help="大学场景，如 成长 / 人际 / 就业")
    ap.add_argument("--keyword", help="在观点/标题/判断里搜词")
    ap.add_argument("--id", help="精确编号，ATOM-038 或 SCY-26")
    ap.add_argument("--book", help="书名关键词（仅语料）")
    ap.add_argument("--source", choices=["oral", "published"], help="来源类型（仅原子）")
    ap.add_argument("--scope", choices=["atoms", "corpus", "all"], default="atoms")
    ap.add_argument("--status", choices=["approved", "all"], default="approved",
                    help="approved=给可用观点（✅ 已认可 + 📎 参考）；all=再带上 ⏳ 的元信息，仍不给观点")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--stats", action="store_true", help="只看库存统计，不返回任何观点")
    args = ap.parse_args()

    atoms, corpus = load("atoms.jsonl"), load("corpus.jsonl")

    if args.stats:
        print(json.dumps(stats(atoms, corpus), ensure_ascii=False, indent=2))
        return 0

    out, gated = [], 0
    if args.scope in ("atoms", "all"):
        for r in atoms:
            if not match(r, args):
                continue
            available = bool(r["view"]) and (
                r["status"].startswith("✅") or r["status"].startswith("📎 参考"))
            if not available:
                gated += 1
                if args.status == "all":
                    out.append({"id": r["id"], "topic": r["topic"],
                                "status": r["status"] or "未登记",
                                "门禁": "未认可，观点不外露"})
                continue
            out.append(brief(r))
    if args.scope in ("corpus", "all"):
        for r in corpus:
            if not match(r, args, corpus=True):
                continue
            out.append(brief(r, corpus=True))

    if args.limit > 0:
        out = out[:args.limit]

    if args.json:
        print(json.dumps({"结果": out, "被门禁拦下": gated,
                          "提示": "一次最多用 1-2 条，观点不能替代结论"},
                         ensure_ascii=False, indent=2))
        return 0

    if not out:
        print("没查到可返回的观点。" + ("（有 %d 条被状态门禁拦下）" % gated if gated else ""))
        print("可试：--stats 看库存，或换 --topic / --scene / --keyword。")
        return 0

    for r in out:
        if "id" in r:
            print("【%s】%s" % (r["id"], r.get("view") or "（观点不外露）"))
            print("  主题 %s ｜ 层次 %s ｜ 场景 %s" % (r["topic"], r["layer"], r["scene"]))
            print("  来源 %s ｜ 状态 %s" % (r["source"], r["status"] or "未登记"))
            print("  对外：%s" % r["对外说"])
        else:
            print("【%s】%s" % (r["code"], r["title"]))
            if r["judgement"]:
                print("  %s" % r["judgement"])
            print("  来源 %s ｜ 状态 %s%s" % (
                r["source"], r["status"],
                " ｜ 转正 " + r["atom"] if r["atom"] else ""))
            print("  对外：%s" % r["对外说"])
        print()
    if gated:
        print("（另有 %d 条 ⏳ 待确认，按门禁没返回观点）" % gated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
