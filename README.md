# Skills Record — 技能记录库

> 本文件由 `scripts/generate-skills-readme.py` 自动生成，请勿手工编辑。
> 最后更新：2026-06-23 05:53 UTC

收录 Cursor / Claude Agent Skill 与相关工具。技能可来自 **仓库子目录**（含 `SKILL.md`）或 **GitHub Issues**（标签 `skill-record`）。

## 技能目录

| 名称 | 分类 | 简介 | 来源 | 详情 |
|------|------|------|------|------|
| CNKI Research Toolkit | Cursor Skill | 面向 Cursor / Claude Agent 的 中国知网（CNKI）文献研究 Skill。将原先分散的 10 个子 Skill 合并为单一工作流，通过 Chrome DevTools MCP 在真实浏览器中完成检索、解析、下载、导出与期刊分析。 | 本地 `cnki/` | [README](cnki/README.md) |

## 各 Skill 简介

### CNKI Research Toolkit

- **Slug**：`cnki`
- **分类**：Cursor Skill
- **来源**：本地 `cnki/`

面向 Cursor / Claude Agent 的 中国知网（CNKI）文献研究 Skill。将原先分散的 10 个子 Skill 合并为单一工作流，通过 Chrome DevTools MCP 在真实浏览器中完成检索、解析、下载、导出与期刊分析。

详细文档见 [cnki/README.md](cnki/README.md)。

---

## 如何新增 Skill

### 方式一：上传到仓库

1. 在仓库根目录创建 `{slug}/` 文件夹
2. 放入 `SKILL.md`（必需）与 `README.md`（推荐，人类可读说明）
3. 提交代码；`post-commit` 钩子或 CI 会自动更新本文件

### 方式二：GitHub Issue

1. 在本仓库创建 Issue，标题格式：`[skill] 显示名称`
2. 添加标签 `skill-record`
3. 正文建议使用 YAML frontmatter（`title`、`summary`、`category`、`repo_url`、`tags` 等）
4. Issue 创建/编辑后，GitHub Actions 会触发索引更新

## 维护脚本

```bash
python3 scripts/generate-skills-readme.py          # 生成 README.md
python3 scripts/generate-skills-readme.py --check    # 检查是否过期
bash scripts/install-hooks.sh                      # 安装 Git 钩子
```
