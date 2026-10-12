#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h}"
if [[ -x "$PROJECT_DIR/.venv/bin/python" ]]; then
  LUMI_PYTHON="$PROJECT_DIR/.venv/bin/python"
else
  LUMI_PYTHON="$(command -v python3)"
fi
"$LUMI_PYTHON" "$PROJECT_DIR/lumi.py" install
echo '\n安装完成。请打开 Mini & Pets，刷新 My pets，然后选择「露米 Lumi · 项目版」。'
if [[ -t 0 ]]; then read '?按回车键关闭…'; fi
