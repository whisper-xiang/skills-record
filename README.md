# Skills Record — 技能记录库

> 本文件由 `scripts/generate-skills-readme.py` 自动生成，请勿手工编辑。
> 最后更新：2026-06-23 14:10 北京时间

收录 Cursor / Claude Agent Skill 与相关工具。技能可来自 **`skills/` 目录**（各子目录含 `SKILL.md`）或 **GitHub Issues**（标签 `skill-record`）。

## 技能目录

| 名称 | 分类 | 简介 | 来源 | 详情 |
|------|------|------|------|------|
| Academic Research Skills (ARS) | Claude Skill | Claude Code 学术研究全流程技能套件，覆盖研究、写作、审稿与 10 阶段 pipeline。 | Issue #1 | [Issue #1](https://github.com/whisper-xiang/skills-record/issues/1) |
| CNKI Research Toolkit | Cursor Skill | 面向 Cursor / Claude Agent 的 中国知网（CNKI）文献研究 Skill。将原先分散的 10 个子 Skill 合并为单一工作流，通过 Chrome DevTools MCP 在真实浏览器中完成检索、解析、下载、导出与期刊分析。 | 本地 `skills/cnki/` | [README](skills/cnki/README.md) |
| nature-skills | 其他 | Nature/CNS 风格科研技能包，含润色、绘图、reader、PPT、审稿、引用等 11 个子技能。 | Issue #2 | [Issue #2](https://github.com/whisper-xiang/skills-record/issues/2) |

## 各 Skill 简介

### Academic Research Skills (ARS)

- **Slug**：`academic-research-skills`
- **分类**：Claude Skill
- **来源**：Issue #1
- **仓库**：[https://github.com/imbad0202/academic-research-skills](https://github.com/imbad0202/academic-research-skills)
- **标签**：学术, 论文, 文献综述, 同行评审, Claude Code

Claude Code 学术研究全流程技能套件，覆盖研究、写作、审稿与 10 阶段 pipeline。

详细内容见 [Issue #1](https://github.com/whisper-xiang/skills-record/issues/1)。

---

### CNKI Research Toolkit

- **Slug**：`cnki`
- **分类**：Cursor Skill
- **来源**：本地 `skills/cnki/`

面向 Cursor / Claude Agent 的 中国知网（CNKI）文献研究 Skill。将原先分散的 10 个子 Skill 合并为单一工作流，通过 Chrome DevTools MCP 在真实浏览器中完成检索、解析、下载、导出与期刊分析。

详细文档见 [skills/cnki/README.md](skills/cnki/README.md)。

---

### nature-skills

- **Slug**：`nature-skills`
- **分类**：其他
- **来源**：Issue #2
- **仓库**：[https://github.com/Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills)
- **标签**：Nature, 论文, 科研绘图, 学术写作, Codex, Cursor

Nature/CNS 风格科研技能包，含润色、绘图、reader、PPT、审稿、引用等 11 个子技能。

详细内容见 [Issue #2](https://github.com/whisper-xiang/skills-record/issues/2)。

---

## 如何新增 Skill

### 方式一：上传到仓库

1. 在 `skills/` 下创建 `{slug}/` 文件夹
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
