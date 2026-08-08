#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
md2html.py —— 零依赖的 Markdown → HTML 转换器（Python 标准库实现）

专为本项目文档设计，覆盖本项目用到的 GFM 语法子集：
  标题、段落、无序/有序列表、引用块、代码块（围栏式）、
  表格、分割线、行内代码、加粗、斜体、链接、行内 HTML。

用法:
  python3 md2html.py 输入.md 输出.html [--section 章节名] [--toc]

特点:
  * 不依赖任何第三方库，可在任意有 Python 3 的机器上运行
  * 相对链接（指向 .md / templates / examples 的文件链接）转为纯文本，
    因为合并成 PDF 后这些链接没有意义
  * http(s) 链接保留可点击
  * --section 会把整篇包进 <section class="chapter">，方便打印时每章分页
"""

import base64
import html
import mimetypes
import os
import re
import sys

# ---------------------------------------------------------------- 行内解析

INLINE_RE = re.compile(
    r'(`[^`]+`|'      # 行内代码
    r'\*\*[^*]+\*\*|' # 加粗
    r'_[^_]+_|'       # 斜体（下划线式）
    r'!\[[^\]]*\]\([^)]*\)|'  # 图片（本项目无，占位）
    r'\[[^\]]*\]\([^)]*\))'   # 链接
)


def _inline(text: str) -> str:
    """把一个普通文本行里的行内标记转成 HTML。"""

    def repl(m: re.Match) -> str:
        token = m.group(0)
        if token.startswith('`'):
            return f'<code>{html.escape(token[1:-1])}</code>'
        if token.startswith('**'):
            return f'<strong>{_inline(token[2:-2])}</strong>'
        if token.startswith('_'):
            return f'<em>{_inline(token[1:-1])}</em>'
        if token.startswith('!['):
            # 图片 ![alt](src)
            inner = token[2:token.index(']')]
            src = token[token.index('](') + 2:-1]
            return f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(inner, quote=True)}">'
        # 链接 [text](url)
        inner = token[1:token.index(']')]
        url = token[token.index('](') + 2:-1]
        if url.startswith('http://') or url.startswith('https://'):
            return f'<a href="{html.escape(url, quote=True)}">{_inline(inner)}</a>'
        # 相对链接 / 锚点链接：PDF 中无意义，只保留文字
        return _inline(inner)

    return INLINE_RE.sub(repl, html.escape(text))


# ---------------------------------------------------------------- 块级解析

def _parse_table(lines: list, i: int):
    """解析以 lines[i] 开头的表格，返回 (html, 下一个未消费行号)。"""
    header = [c.strip() for c in lines[i].strip().strip('|').split('|')]
    j = i + 1
    while j < len(lines) and re.match(r'^\s*\|?[\s:|-]+\|?\s*$', lines[j]) and '-' in lines[j]:
        j += 1  # 跳过对齐行
    rows = []
    while j < len(lines) and lines[j].strip().startswith('|'):
        cells = [c.strip() for c in lines[j].strip().strip('|').split('|')]
        rows.append(cells)
        j += 1
    out = ['<table>', '<thead><tr>']
    for c in header:
        out.append(f'<th>{_inline(c)}</th>')
    out.append('</tr></thead><tbody>')
    for r in rows:
        out.append('<tr>')
        for c in r:
            out.append(f'<td>{_inline(c)}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return ''.join(out), j


def _parse_list(lines: list, i: int):
    """解析从 lines[i] 开始的列表（无序 -/* 或有序 1.），返回 (html, 下一个行号)。"""
    out = []
    ordered = re.match(r'^\s*\d+\.\s+', lines[i]) is not None
    tag = 'ol' if ordered else 'ul'
    out.append(f'<{tag}>')
    j = i
    while j < len(lines):
        line = lines[j]
        m = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$', line)
        if not m:
            break
        content = m.group(3)
        # 处理嵌套引用/代码块外的简单续行（无缩进续行本项目未使用，忽略）
        out.append('<li>')
        out.append(_inline(content))
        out.append('</li>')
        j += 1
    out.append(f'</{tag}>')
    return ''.join(out), j


def _parse_quote(lines: list, i: int):
    """解析连续引用块（> ...），返回 (html, 下一个行号)。"""
    parts = []
    j = i
    while j < len(lines) and lines[j].startswith('>'):
        parts.append(lines[j][1:].lstrip())
        j += 1
    # 引用内的块级内容（代码块/列表）罕见，本项目引用均为段落，简化处理
    body = '<br>\n'.join(_inline(p) for p in parts if p)
    return f'<blockquote>{body}</blockquote>', j


def markdown_to_html(md_text: str) -> str:
    """主入口：Markdown 文本 → HTML 正文。"""
    lines = md_text.split('\n')
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip('\r')
        stripped = line.strip()

        # 空行
        if not stripped:
            i += 1
            continue

        # 代码块（围栏式）
        if stripped.startswith('```'):
            j = i + 1
            buf = []
            while j < n and not lines[j].strip().startswith('```'):
                buf.append(lines[j])
                j += 1
            j += 1  # 跳过结束围栏
            lang = stripped[3:].strip()
            cls = f' class="language-{html.escape(lang)}"' if lang else ''
            out.append(f'<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>')
            i = j
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            level = len(m.group(1))
            out.append(f'<h{level}>{_inline(m.group(2))}</h{level}>')
            i += 1
            continue

        # 分割线
        if re.match(r'^\s*(---|\*\*\*|___)\s*$', line):
            out.append('<hr>')
            i += 1
            continue

        # 表格
        if stripped.startswith('|'):
            html_tbl, j = _parse_table(lines, i)
            out.append(html_tbl)
            i = j
            continue

        # 引用块
        if line.startswith('>'):
            html_q, j = _parse_quote(lines, i)
            out.append(html_q)
            i = j
            continue

        # 列表
        if re.match(r'^\s*([-*]|\d+\.)\s+', line):
            html_l, j = _parse_list(lines, i)
            out.append(html_l)
            i = j
            continue

        # 普通段落：收集连续非空、非特殊行
        buf = [line]
        j = i + 1
        while j < n:
            s = lines[j].rstrip('\r').strip()
            if not s or s.startswith('```') or s.startswith('|') or s.startswith('>') \
                    or re.match(r'^\s*([-*]|\d+\.)\s+', lines[j]) \
                    or re.match(r'^#{1,6}\s+', lines[j]) \
                    or re.match(r'^\s*(---|\*\*\*|___)\s*$', lines[j]):
                break
            buf.append(lines[j].rstrip('\r'))
            j += 1
        out.append(f'<p>{_inline(" ".join(x.strip() for x in buf))}</p>')
        i = j

    return '\n'.join(out)


# ---------------------------------------------------------------- 页面组装

COVER_HTML = """<div class="cover">
<h1>面向教师的 AI Coding 入门指南</h1>
<div class="subtitle">从零开始，用 Reasonix 让 AI 帮你做学生工具</div>
<div class="meta">名词解释 · 工具手册 · 动手示例 · AGENTS.md 制定 · 模板库</div>
</div>"""

CSS = """
:root {
  --primary: #1a6fb0;
  --primary-light: #e8f1f8;
  --accent: #e8842c;
  --text: #222;
  --text-light: #555;
  --border: #d0d0d0;
  --code-bg: #f6f8fa;
  --quote-bg: #fdf6ec;
  --quote-border: #e8842c;
}
* { box-sizing: border-box; }
body {
  font-family: "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei",
               "PingFang SC", "WenQuanYi Micro Hei", "AR PL UMing CN", sans-serif;
  color: var(--text);
  font-size: 10.5pt;
  line-height: 1.75;
  margin: 0;
  padding: 0;
}
h1, h2, h3, h4, h5, h6 { color: var(--primary); line-height: 1.4; margin: 1.2em 0 0.5em; }
h1 { font-size: 20pt; border-bottom: 2px solid var(--primary-light); padding-bottom: 0.25em; }
h2 { font-size: 16pt; border-bottom: 1px solid var(--primary-light); padding-bottom: 0.2em; }
h3 { font-size: 13.5pt; }
h4 { font-size: 12pt; }
p { margin: 0.5em 0; }
strong { color: #c0392b; }
a { color: var(--primary); text-decoration: none; }
code {
  font-family: "JetBrains Mono", "Consolas", "Courier New", monospace;
  background: var(--code-bg);
  border: 1px solid #e3e3e3;
  border-radius: 3px;
  padding: 0.1em 0.35em;
  font-size: 0.92em;
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.7em 1em;
  overflow-x: auto;
  line-height: 1.5;
}
pre code { background: none; border: none; padding: 0; font-size: 9pt; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 9.5pt; }
th, td { border: 1px solid var(--border); padding: 0.4em 0.6em; text-align: left; vertical-align: top; }
th { background: var(--primary-light); color: var(--primary); font-weight: 600; }
tr:nth-child(even) td { background: #fafafa; }
blockquote {
  background: var(--quote-bg);
  border-left: 4px solid var(--quote-border);
  margin: 0.8em 0;
  padding: 0.5em 1em;
  color: #6b4a1f;
}
blockquote code { background: #fdf0da; border-color: #ecd9b8; }
hr { border: none; border-top: 2px solid var(--primary-light); margin: 1.5em 0; }
ul, ol { margin: 0.5em 0; padding-left: 1.8em; }
li { margin: 0.25em 0; }
.cover { text-align: center; padding-top: 25vh; }
.cover h1 { font-size: 30pt; border: none; color: var(--primary); }
.cover .subtitle { font-size: 14pt; color: var(--text-light); margin-top: 1em; }
.cover .meta { font-size: 10pt; color: var(--text-light); margin-top: 3em; }
.toc { font-size: 10pt; }
.toc ol { list-style: none; padding-left: 0; }
.toc li { margin: 0.35em 0; }
.chapter { page-break-before: always; }
img {
  max-width: 100%;
  height: auto;
  border: 1px solid var(--border);
  border-radius: 4px;
  margin: 0.6em 0;
}
.figure {
  text-align: center;
  margin: 1em 0;
}
.figure .caption {
  font-size: 9pt;
  color: var(--text-light);
  margin-top: 0.3em;
}
"""


def build_page(body: str, title: str, subtitle: str = "", toc: str = "") -> str:
    """组装完整 HTML 页面。"""
    cover = ''
    if subtitle:
        cover = (
            '<div class="cover">'
            f'<h1>{html.escape(title)}</h1>'
            f'<div class="subtitle">{html.escape(subtitle)}</div>'
            f'<div class="meta">{html.escape("面向教师的 AI Coding 入门指南")}</div>'
            '</div>'
        )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
{cover}
{toc}
{body}
</body>
</html>
"""


def inline_images(body: str, base_dir: str) -> str:
    """把 <img src="相对路径"> 的图片 base64 内联，保证单文件 HTML / PDF 可用。"""

    def repl(m: re.Match) -> str:
        src = m.group(1)
        alt = m.group(2)
        if src.startswith(('http://', 'https://', 'data:', 'file:')):
            return m.group(0)
        path = os.path.normpath(os.path.join(base_dir, src))
        if not os.path.isfile(path):
            print(f'⚠️  找不到图片：{src}（已保留原样，导出后可能不显示）', file=sys.stderr)
            return m.group(0)
        mime, _ = mimetypes.guess_type(path)
        mime = mime or 'image/png'
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return f'<img src="data:{mime};base64,{b64}" alt="{alt}">'

    return re.sub(r'<img src="([^"]+)" alt="([^"]*)">', repl, body)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='零依赖 Markdown → HTML 转换器')
    parser.add_argument('input', nargs='+', help='输入 .md 文件（多个时合并为一个 HTML）')
    parser.add_argument('output', help='输出 .html 文件')
    parser.add_argument('--section', help='章节名：包进 <section class="chapter">（打印时分页）')
    parser.add_argument('--title', help='页面标题（默认取输入文件名）')
    parser.add_argument('--cover', action='store_true',
                        help='在文档最前面插入封面页（用于合并导出完整指南）')
    parser.add_argument('--inline-images', action='store_true',
                        help='把相对路径图片 base64 内联进 HTML（单文件导出/PDF 必备）')
    args = parser.parse_args()

    bodies = []
    for md_path in args.input:
        with open(md_path, encoding='utf-8') as f:
            md_text = f.read()
        body = markdown_to_html(md_text)
        if args.inline_images:
            body = inline_images(body, os.path.dirname(os.path.abspath(md_path)))
        if len(args.input) > 1:
            body = f'<section class="chapter">\n{body}\n</section>'
        bodies.append(body)

    combined = '\n'.join(bodies)
    if args.cover:
        combined = COVER_HTML + '\n' + combined

    title = args.title or (args.input[0] if len(args.input) == 1 else '合并文档')
    page = build_page(combined, title)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'✔ 已生成 {args.output}')


if __name__ == '__main__':
    main()
