#!/usr/bin/env bash
# 取消本地 Git hooks；README 索引由 GitHub Actions 统一更新。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

chmod +x scripts/generate-skills-readme.py

current="$(git config --local --get core.hooksPath 2>/dev/null || true)"
if [[ "$current" == ".githooks" ]]; then
  git config --local --unset core.hooksPath
  echo "已移除本地 hooks：core.hooksPath（原为 .githooks）"
else
  echo "未配置 core.hooksPath=.githooks，无需移除"
fi

cat <<'EOF'

README.md 由 CI 自动维护：
  • push 变更 skills/、生成脚本或 workflow → Actions 更新 README
  • Issue（标签 skill-record）新建/编辑 → Actions 更新 README

工作流：commit → push → 等待 CI（约 1–2 分钟）→ git pull

本地仅预览索引（不提交）：
  python3 scripts/generate-skills-readme.py
EOF
