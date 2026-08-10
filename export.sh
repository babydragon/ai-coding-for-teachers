#!/usr/bin/env bash
# =============================================================================
# export.sh —— 把本项目的 Markdown 文档导出成 PDF（或单文件 HTML）
#
# 零依赖设计：只需要系统里已有的两样东西，无需安装任何第三方库：
#   1. Python 3（自带 markdown→HTML 转换器 tools/md2html.py，纯标准库实现）
#   2. 一个浏览器（Chrome / Edge / Chromium 任意一个，用于把 HTML 打印成 PDF）
#
# 支持的浏览器（按顺序自动探测）：
#   google-chrome-stable / google-chrome / chromium / chromium-browser /
#   microsoft-edge / msedge / edge
# 老师电脑上的 Chrome 或 Edge 都可以直接使用，无需额外安装。
#
# 用法：
#   ./export.sh                # 导出完整 PDF（README + 五个部分 + 附录）
#   ./export.sh --html         # 只生成单文件 HTML（可放 GitHub Pages / Cloudflare Pages）
#   ./export.sh --file 路径    # 只导出某一个 md 文件
#   ./export.sh --out 名字     # 自定义输出文件名（不带扩展名）
#
# 输出位置：dist/ 目录（自动创建）
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------- 路径与常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
CONVERTER="$SCRIPT_DIR/tools/md2html.py"
DIST_DIR="$SCRIPT_DIR/dist"
TMP_DIR="$SCRIPT_DIR/.export-tmp"

# 文档顺序：README 封面 + 六个部分（每部分内部按文件名排序）+ 附录
CHAPTERS=(
  "README.md"
  "docs/01-ai-coding-basics/01-名词解释.md"
  "docs/01-ai-coding-basics/02-agent编码原理.md"
  "docs/02-tool-guide/01-安装与模型配置.md"
  "docs/02-tool-guide/02-界面与常用操作.md"
  "docs/03-example/01-竖式乘法小游戏.md"
  "docs/04-agents-md/01-什么是AGENTS.md.md"
  "docs/04-agents-md/02-学生工具通用要求与模板.md"
  "docs/04-agents-md/03-安装与更新.md"
  "docs/05-templates/01-模板库.md"
  "docs/06-进阶使用/01-把需求说清楚.md"
  "docs/06-进阶使用/02-日常文本工作.md"
  "docs/06-进阶使用/03-让AI干更重的活.md"
  "docs/06-进阶使用/04-让AI连接更多.md"
  "docs/06-进阶使用/05-让AI掌握技能.md"
  "docs/06-进阶使用/06-进阶问答.md"
  "docs/附录-术语速查与FAQ.md"
)

MODE="pdf"          # pdf | html
OUT_NAME="面向教师的AI编码指南"
SINGLE_FILE=""

# ---------------------------------------------------------------- 小工具函数
log()  { printf '\033[1;34m[export]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[export]\033[0m 错误：%s\n' "$*" >&2; }

# ---------------------------------------------------------------- 探测浏览器
find_browser() {
  local candidates=(
    google-chrome-stable google-chrome chromium chromium-browser
    microsoft-edge msedge edge chrome
  )
  for c in "${candidates[@]}"; do
    if command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  # macOS 常见路径兜底
  if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    return 0
  fi
  if [ -x "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" ]; then
    echo "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    return 0
  fi
  return 1
}

# ---------------------------------------------------------------- HTML → PDF
html_to_pdf() {
  local html_file="$1" pdf_file="$2"
  local browser
  browser="$(find_browser)" || {
    err "没有找到可用的浏览器（Chrome/Edge/Chromium）。"
    err "请安装任意一个浏览器后重试，或先用 ./export.sh --html 生成 HTML 版本。"
    exit 1
  }
  log "使用浏览器：$browser"

  # Chrome/Edge 系通用参数；--no-sandbox 避免个别 Linux 环境下权限问题
  "$browser" --headless=new --disable-gpu --no-sandbox \
    --no-pdf-header-footer \
    --print-to-pdf="$pdf_file" \
    "file://$html_file" >/dev/null 2>&1 || true

  if [ ! -s "$pdf_file" ]; then
    err "PDF 生成失败（浏览器输出为空），请检查浏览器是否能正常打开网页。"
    exit 1
  fi
  log "PDF 已生成：$pdf_file"
}

# ---------------------------------------------------------------- 主流程
main() {
  # 解析参数
  while [ $# -gt 0 ]; do
    case "$1" in
      --html)  MODE="html"; shift ;;
      --file)  SINGLE_FILE="$2"; shift 2 ;;
      --out)   OUT_NAME="$2"; shift 2 ;;
      -h|--help)
        sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//'
        exit 0 ;;
      *)
        err "未知参数：$1（用 --help 查看用法）"
        exit 1 ;;
    esac
  done

  mkdir -p "$DIST_DIR" "$TMP_DIR"
  trap 'rm -rf "$TMP_DIR"' EXIT

  # 单文件模式：只导出指定 md
  if [ -n "$SINGLE_FILE" ]; then
    [ -f "$SINGLE_FILE" ] || { err "找不到文件：$SINGLE_FILE"; exit 1; }
    local out_html="$TMP_DIR/single.html"
    python3 "$CONVERTER" "$SINGLE_FILE" "$out_html" --title "$(basename "$SINGLE_FILE" .md)" --inline-images
    if [ "$MODE" = "html" ]; then
      cp "$out_html" "$DIST_DIR/$OUT_NAME.html"
      log "HTML 已生成：$DIST_DIR/$OUT_NAME.html"
    else
      html_to_pdf "$out_html" "$DIST_DIR/$OUT_NAME.pdf"
    fi
    exit 0
  fi

  # 完整模式：合并全部章节为一个 HTML（封面 + 每章分页）
  log "开始转换全部章节（共 ${#CHAPTERS[@]} 个文件）…"
  local merged_html="$TMP_DIR/merged.html"
  local md_files=()
  for ch in "${CHAPTERS[@]}"; do
    local md_path="$PROJECT_ROOT/$ch"
    [ -f "$md_path" ] || { err "找不到文件：$md_path"; exit 1; }
    md_files+=("$md_path")
  done

  python3 "$CONVERTER" "${md_files[@]}" "$merged_html" \
    --title "面向教师的 AI Coding 入门指南" --cover --inline-images

  # 合并 HTML 始终同步到 dist（网页版随时可用）
  cp "$merged_html" "$DIST_DIR/$OUT_NAME.html"

  if [ "$MODE" = "html" ]; then
    log "HTML 已生成：$DIST_DIR/$OUT_NAME.html"
    log "可直接用浏览器打开，或上传到 GitHub Pages / Cloudflare Pages 发布。"
  else
    html_to_pdf "$merged_html" "$DIST_DIR/$OUT_NAME.pdf"
    log "导出完成 🎉 输出目录：$DIST_DIR/"
  fi
}

main "$@"
