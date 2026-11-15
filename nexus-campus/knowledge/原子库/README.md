# 原子库引擎 · 目录说明

> **这是整套大学版的可调用知识库引擎**，不是一堆静态文档。
> 入口 `SKILL.md` 管触发与输出，细则 `references/调用契约.md`，检索走 `scripts/query.py`，数据在 `data/`。

---

## 目录

```
knowledge/原子库/
├── SKILL.md                   引擎入口：触发条件、接手契约、输出契约、红线
├── README.md                  本页
├── references/调用契约.md      状态门禁、三条调用路径、归属措辞、什么算答完
├── scripts/query.py           检索脚本：主题/层次/场景/关键词/编号/书名/库存
└── data/
    ├── atoms.jsonl            50 条思想原子（18 条已认可带原文 / 30 条参考判断 / 2 条待确认不出观点）
    ├── corpus.jsonl           216 条九本书语料，每条带作者 + 书名 + 状态
    └── 00_索引.md             四张检索表（主题／层次／大学场景／来源）+ 状态口径
```

`data/` 与 `data/00_索引.md` 由 `tools/build-atoms-engine.py` 生成，**统一生成、勿手改**。

## 真源关系

```
独立的思想原子库（唯一真源，人改那里）
   │  build-atoms-engine.py
   ├──→ 本目录 data/（脱敏、随包分发、可检索）
   └──→ 本机完整镜像（含主题正文、九本书全文、治理文档，不随包分发）
```

**两个入口，一份真源。**

> ⚠️ **构建脚本未随包发布。** `tools/` 下的 `build-atoms-engine.py`、`build-thought-layer.py`、`check-thought-layer.py`、`sync-all.py` 为作者本机的生成与校验工具，开源包只分发**生成物**（`data/` 三文件、`knowledge/思想/` 卡片）。要重建数据层，请按 `data/` 的字段结构自行实现等价生成流程；检索不受影响，`scripts/query.py` 已随包提供。 主题正文、九本书全文、收录治理文档只在本机留存；对外包里只有脱敏数据与引擎本体。

## 跟其他两处的关系

| 去哪 | 干什么 |
|---|---|
| `knowledge/思想/` | 18 条精选观点卡 + 卡点对照表，**按学生原话的信号快速取一条** |
| **本引擎** | **全量检索、查出处、查库存**，支持主题/层次/场景/关键词 |
| 按编号回取原卡 | 216 条带来源的外部语料另存一份只读索引，引用时按编号回取 |

三处数据同源，不互相复制正文：思想层与本引擎都是生成物，改内容改原子库。

## 数据字段（`atoms.jsonl`）

| 字段 | 说明 |
|---|---|
| `id` / `date` / `topic` / `layer` / `type` | 编号、日期、主题、层次、类型 |
| `view` | 观点原文。**仅 ✅ 已认可的有值**，其余为空 |
| `gated` | 非空表示「未认可，观点不外露」 |
| `status` / `source` | 认可状态、来源（口述 / 出版物，含作者书名原卡号） |
| `themes` / `track` / `scene` | 认知主题编号、板块、映射的大学场景 |
| `tags` / `skills` | 清洗后的语义标签、归属 Skill |

`corpus.jsonl` 每条含 `code` / `title` / `judgement` / `author` / `book` / `source` / `status` / `atom`（转正后对应的原子编号）。

## 更新

原子库补了字段、点头转正、或加了新书后，在库根跑：

```
python tools/sync-all.py
```

它会自动调 `build-atoms-engine.py`，再同步三条线并跑八道闸。单独只想重建数据层，跑 `python tools/build-atoms-engine.py`。

**⏳ 待确认不点头不会自动转正。**
