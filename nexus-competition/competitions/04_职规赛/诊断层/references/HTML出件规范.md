# HTML 出件规范（v0.4 · P1 落盘）

> 用途：把报告正文 + 图片做成一个 HTML，再转成 Word。**通道已在本机实测跑通**（2026-11-14）。

## 转换命令

```
python3 <workbuddy-docx>/skills/html-to-doc/scripts/convert_doc.py \
  --html <版式产物.html> --output <交付.docx> [--require-page-furniture]
```

脚本路径：`~/.workbuddy/plugins/cache/workbuddy-builtin/workbuddy-docx/5.11.3-*/skills/html-to-doc/scripts/convert_doc.py`。
stdout 末行 JSON：`success / docx_path / preflight / verify / error`；失败如实报错，**不降级、不换别的实现**。

## HTML 硬规则（转 docx 会静默走样的部分）

| 规则 | 说明 |
|---|---|
| 单文件 | 封面、目录、正文全在一个 HTML，`<style>` 集中一份 |
| 样式分层 | 元素级视觉写 inline style；`@page` 页眉/页脚/页码写 `<style>` |
| CSS 变量 | 一律 `var(--*)`，`:root` 统一声明；禁裸值 |
| 禁 flex / grid | 会静默降级；结构化对齐一律用 `<table>`（含 `thead`/`tbody`） |
| 禁 CSS 分页 | `break-after` / `page-break-*` 被忽略 |
| 标题 | 正文用 `h1`~`h3`；封面大标题禁用 h1~h6，用 `p`/`div` + 大字号 |
| 封面 | 有封面时正文首个 `<section>` 带 `data-page-restart="1"` |
| 图片 | `<img>` **必须包在 `<p>` 里**才居中；`src` 用**绝对路径或 base64**，相对路径与 `file://` 会丢图 |

## 出件校验

- 转换开启 `--require-page-furniture` 时看 `preflight.passed` / `verify.passed` / `content.missing_count`。
- 拆包复核 `word/media/` 是否有图、`w:tbl` 与 `w:sectPr` 数量、关键文字是否保留。
- 官方硬约束：报告 PDF ≤10MB、文字 ≤2000 字、图表 ≤5 张；展示 PPT ≤50MB。**PDF 由用户自行转换。**

## 红线

生成图只能是概念/装饰/图表可视化；**不得冒充证书、成绩单、实习证明、访谈照片、作品截图等证据类图片**。证据类只能用学生本人提供的原件。
