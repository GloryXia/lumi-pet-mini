#!/bin/zsh
set -e

SCRIPT_DIR="${0:A:h}"
TARGET_ROOT="${CODEX_HOME:-$HOME/.codex}/pets"
TARGET_DIR="$TARGET_ROOT/lumi"

if [[ -e "$TARGET_DIR/pet.json" || -e "$TARGET_DIR/spritesheet.webp" ]]; then
  echo "露米已经存在于 $TARGET_DIR。请先在 ChatGPT 的设置 > Pets 中检查。"
  read '?按回车键关闭…'
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp "$SCRIPT_DIR/pet.json" "$TARGET_DIR/pet.json"
cp "$SCRIPT_DIR/spritesheet.webp" "$TARGET_DIR/spritesheet.webp"

echo "露米已安装到 $TARGET_DIR。"
echo "请在 ChatGPT 桌面 App 中打开 Settings > Pets，点击 Refresh，然后选择「露米 Lumi」。"
read '?按回车键关闭…'
