#!/usr/bin/env bash
# 将 .githooks 注册为当前仓库的 Git hooks 目录
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

chmod +x .githooks/post-commit
chmod +x scripts/generate-skills-readme.py

git config core.hooksPath .githooks

echo "Git hooks installed: core.hooksPath=.githooks"
echo "  post-commit → 更新 README.md 技能索引"
