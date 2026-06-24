#!/usr/bin/env python3
"""
扫描仓库内各 skill 目录（含 SKILL.md）与 GitHub Issues（label: skill-record），
生成项目根目录 README.md 总索引。

用法:
  python3 scripts/generate-skills-readme.py
  python3 scripts/generate-skills-readme.py --check   # 仅检查是否需要更新，非 0 退出
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
OUTPUT = REPO_ROOT / "README.md"
ISSUE_LABEL = "skill-record"
ISSUE_TITLE_PREFIXES = ("[skill]", "[repo]", "[idea]")
INDEX_ISSUE_TITLE = "[skill-index]"


@dataclass
class SkillEntry:
    slug: str
    name: str
    description: str
    source: str  # local | issue
    detail_path: str
    tags: list[str] = field(default_factory=list)
    category: str = ""
    status: str = ""
    stars: str = ""
    repo_url: str = ""
    recorded_at: str = ""
    updated_at: str = ""
    seq: int = 0
    issue_number: int | None = None
    detail_sections: dict[str, str] = field(default_factory=dict)


# category → README 分区
BUCKET_SKILL = "skill"
BUCKET_REPO = "repo"
BUCKET_IDEA = "idea"

# 详情区展示的章节（不含安装、更新日志等）
DETAIL_SECTION_MAP: dict[str, list[str]] = {
    "简介": ["简介", "想法"],
    "使用方法": ["用法", "使用方式", "使用方法", "快速开始", "可能的下一步"],
    "使用效果": ["备注", "使用效果", "效果", "功能概览", "功能亮点", "适用场景", "触发场景", "关联"],
}

SKIP_SECTION_RE = re.compile(
    r"安装|更新日志|^链接$|目录结构|DOM|选择器|模块详解|维护脚本|如何新增|架构图",
    re.IGNORECASE,
)

TABLE_SUMMARY_MAX = 48


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        data[key.strip()] = value
    return data


def slug_from_dir(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-")


def extract_summary(readme_path: Path, description: str, max_len: int = 200) -> str:
    if readme_path.is_file():
        text = readme_path.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("|") or line.startswith("-"):
                continue
            if line.startswith("```"):
                break
            summary = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
            return summary[:max_len] + ("…" if len(summary) > max_len else "")
    desc = description.replace("\\n", " ").strip()
    return desc[:max_len] + ("…" if len(desc) > max_len else "")


def parse_record_frontmatter(body: str) -> dict[str, str]:
    """解析 Issue 正文或 records 风格 YAML frontmatter。"""
    # Issue 展示格式：摘要表 + ```yaml 代码块
    fence = re.search(r"```yaml\s*\n(.*?)\n```", body, re.DOTALL)
    if fence:
        return _parse_yaml_block(fence.group(1))
    match = re.match(r"^---\s*\n(.*?)\n---", body, re.DOTALL)
    if not match:
        return {}
    return _parse_yaml_block(match.group(1))


def _parse_yaml_block(block: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip().strip('"').strip("'")
        if value.startswith("[") and value.endswith("]"):
            continue
        data[key.strip()] = value
    return data


def scan_local_skills() -> dict[str, SkillEntry]:
    skills: dict[str, SkillEntry] = {}
    if not SKILLS_DIR.is_dir():
        return skills

    for child in sorted(SKILLS_DIR.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue

        slug = slug_from_dir(child.name)
        meta = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        readme = child / "README.md"
        name = meta.get("name", child.name)
        description = meta.get("description", "")
        rel = f"skills/{child.name}"

        summary = extract_summary(readme, description)
        detail_src = readme if readme.is_file() else skill_md
        skills[slug] = SkillEntry(
            slug=slug,
            name=name,
            description=summary,
            source="local",
            detail_path=f"{rel}/README.md" if readme.is_file() else f"{rel}/SKILL.md",
            category=meta.get("category", "cursor-skill"),
            tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            detail_sections=extract_detail_sections(
                detail_src.read_text(encoding="utf-8"), summary
            ),
        )
    return skills


def gh_available() -> bool:
    try:
        subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            check=True,
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def issue_title_display(title: str) -> str | None:
    if title.startswith(INDEX_ISSUE_TITLE):
        return None
    for prefix in ISSUE_TITLE_PREFIXES:
        if title.startswith(prefix):
            return title[len(prefix) :].strip()
    return None


def fetch_issue_skills() -> dict[str, SkillEntry]:
    if not gh_available():
        return {}

    try:
        raw = subprocess.check_output(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                _github_repo(),
                "--label",
                ISSUE_LABEL,
                "--state",
                "all",
                "--limit",
                "200",
                "--json",
                "number,title,body,state",
            ],
            text=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return {}

    skills: dict[str, SkillEntry] = {}
    for item in json.loads(raw):
        title = item.get("title", "")
        display = issue_title_display(title)
        if display is None:
            continue
        if item.get("state") != "OPEN":
            continue

        body = item.get("body") or ""
        meta = parse_record_frontmatter(body)
        slug = meta.get("slug") or slug_from_dir(display)
        number = item["number"]

        summary = meta.get("summary") or extract_summary(Path(), meta.get("description", ""))
        category = meta.get("category", "")
        if not category:
            if title.startswith("[repo]"):
                category = "github-repo"
            elif title.startswith("[idea]"):
                category = "idea"
        seq_raw = meta.get("seq", "")
        try:
            seq = int(seq_raw) if seq_raw else 0
        except ValueError:
            seq = 0
        skills[slug] = SkillEntry(
            slug=slug,
            name=meta.get("title", display),
            description=summary,
            source="issue",
            detail_path=f"https://github.com/{_github_repo()}/issues/{number}",
            category=category,
            status=meta.get("status", ""),
            stars=meta.get("stars", ""),
            repo_url=meta.get("repo_url", ""),
            recorded_at=meta.get("recorded_at", ""),
            updated_at=meta.get("updated_at", ""),
            seq=seq,
            issue_number=number,
            tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            detail_sections=extract_detail_sections(body, summary),
        )
    return skills


def _github_repo() -> str:
    try:
        url = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "config", "--get", "remote.origin.url"],
            text=True,
            timeout=5,
        ).strip()
        # git@github.com:owner/repo.git 或 https://github.com/owner/repo.git
        m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", url)
        if m:
            return m.group(1).removesuffix(".git")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return "whisper-xiang/skills-record"


def merge_skills(local: dict[str, SkillEntry], issues: dict[str, SkillEntry]) -> list[SkillEntry]:
    merged = dict(issues)
    for slug, entry in local.items():
        merged[slug] = entry
    return list(merged.values())


def entry_bucket(entry: SkillEntry) -> str:
    cat = entry.category
    if cat == "github-repo":
        return BUCKET_REPO
    if cat == "idea":
        return BUCKET_IDEA
    return BUCKET_SKILL


def sort_entries(entries: list[SkillEntry]) -> list[SkillEntry]:
    return sorted(
        entries,
        key=lambda e: (
            e.seq if e.seq else 0,
            e.recorded_at or "0000-00-00",
            e.name.lower(),
        ),
        reverse=True,
    )


def split_by_bucket(entries: list[SkillEntry]) -> dict[str, list[SkillEntry]]:
    buckets: dict[str, list[SkillEntry]] = {
        BUCKET_SKILL: [],
        BUCKET_REPO: [],
        BUCKET_IDEA: [],
    }
    for entry in entries:
        buckets[entry_bucket(entry)].append(entry)
    for key in buckets:
        buckets[key] = sort_entries(buckets[key])
    return buckets


def format_stars(raw: str) -> str:
    if not raw:
        return "—"
    try:
        n = int(raw)
    except ValueError:
        return raw
    if n >= 1000:
        s = f"{n / 1000:.1f}k"
        return s.replace(".0k", "k")
    return str(n)


def status_label(status: str) -> str:
    mapping = {
        "bookmarked": "收藏",
        "installed": "已安装",
        "tried": "已试用",
        "deprecated": "已过时",
        "spark": "灵感",
        "exploring": "探索中",
        "parked": "搁置",
        "done": "已落实",
        "dropped": "已放弃",
    }
    return mapping.get(status, status or "—")


def category_label(cat: str) -> str:
    mapping = {
        "cursor-skill": "Cursor Skill",
        "claude-skill": "Claude Skill",
        "mcp": "MCP",
        "agent-tool": "Agent 工具",
        "github-repo": "GitHub 项目",
        "idea": "想法",
        "other": "其他",
    }
    return mapping.get(cat, cat or "—")


def clean_record_body(text: str) -> str:
    """去掉 frontmatter、摘要表、YAML 代码块与一级标题，保留正文章节。"""
    text = text.strip()
    text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)
    text = re.sub(r"^```yaml\s*\n.*?\n```\s*\n", "", text, count=1, flags=re.DOTALL)
    lines = text.splitlines()
    idx = 0
    while idx < len(lines) and lines[idx].strip().startswith("|"):
        idx += 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    text = "\n".join(lines[idx:])
    text = re.sub(r"^# [^\n]+\n+", "", text.strip(), count=1)
    return text.strip()


def split_markdown_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """返回 (前言, [(## 标题, 正文), ...])。"""
    parts = re.split(r"^## +(.+)$", text, flags=re.MULTILINE)
    if len(parts) == 1:
        return parts[0].strip(), []
    preamble = parts[0].strip()
    sections: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections.append((title, body))
    return preamble, sections


def should_skip_section(title: str) -> bool:
    return bool(SKIP_SECTION_RE.search(title))


def map_section_key(title: str) -> str | None:
    for key, aliases in DETAIL_SECTION_MAP.items():
        if any(alias in title for alias in aliases):
            return key
    return None


def first_paragraph(text: str) -> str:
    buf: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if buf:
                break
            continue
        if s.startswith("#") or s.startswith("|") or s.startswith("```") or s.startswith("---"):
            break
        buf.append(s)
    return " ".join(buf)


def clean_section_body(body: str) -> str:
    """去掉章节正文中独立的 --- 分隔线。"""
    lines = [ln for ln in body.splitlines() if ln.strip() != "---"]
    return "\n".join(lines).strip()


def extract_detail_sections(text: str, fallback_summary: str = "") -> dict[str, str]:
    cleaned = clean_record_body(text)
    preamble, sections = split_markdown_sections(cleaned)
    result: dict[str, str] = {}

    for title, body in sections:
        if should_skip_section(title):
            continue
        key = map_section_key(title)
        body = clean_section_body(body)
        if not key or not body:
            continue
        if key in result:
            result[key] = f"{result[key]}\n\n{body}"
        else:
            result[key] = body

    if "简介" not in result:
        intro = first_paragraph(preamble) or fallback_summary
        if intro:
            result["简介"] = intro

    return result


def truncate_cell(text: str, max_len: int = TABLE_SUMMARY_MAX) -> str:
    one_line = re.sub(r"\s+", " ", text.replace("|", "\\|")).strip()
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 1] + "…"


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_table_html(entries: list[SkillEntry], *, show_stars: bool = True) -> str:
    """HTML 表格：序号、加入/更新时间、名称等。"""
    if show_stars:
        colgroup = (
            '<col width="5%"><col width="9%"><col width="9%">'
            '<col width="16%"><col width="7%"><col width="10%">'
            '<col width="8%"><col width="36%">'
        )
        header = (
            "<th>#</th><th>加入</th><th>更新</th><th>名称</th>"
            "<th>Stars</th><th>分类</th><th>状态</th><th>简介</th>"
        )
        colspan = 8
    else:
        colgroup = (
            '<col width="5%"><col width="10%"><col width="10%">'
            '<col width="18%"><col width="12%"><col width="10%">'
            '<col width="35%">'
        )
        header = (
            "<th>#</th><th>加入</th><th>更新</th><th>名称</th>"
            "<th>分类</th><th>状态</th><th>简介</th>"
        )
        colspan = 7

    rows: list[str] = [
        "<table>",
        "<colgroup>",
        colgroup,
        "</colgroup>",
        "<thead>",
        f"<tr>{header}</tr>",
        "</thead>",
        "<tbody>",
    ]
    if not entries:
        rows.append(f'<tr><td colspan="{colspan}"><em>暂无记录</em></td></tr>')
    else:
        for s in entries:
            seq_cell = escape_html(str(s.seq)) if s.seq else "—"
            joined = escape_html(s.recorded_at or "—")
            updated = escape_html(s.updated_at or "—")
            name = escape_html(s.name)
            summary = escape_html(truncate_cell(s.description, max_len=40))
            cells = [
                f"<td>{seq_cell}</td>",
                f"<td>{joined}</td>",
                f"<td>{updated}</td>",
                f'<td><a href="#{s.slug}">{name}</a></td>',
            ]
            if show_stars:
                cells.append(f"<td>{escape_html(format_stars(s.stars))}</td>")
            cells.extend(
                [
                    f"<td>{escape_html(category_label(s.category))}</td>",
                    f"<td>{escape_html(status_label(s.status))}</td>",
                    f"<td>{summary}</td>",
                ]
            )
            rows.append("<tr>" + "".join(cells) + "</tr>")
    rows.extend(["</tbody>", "</table>"])
    return "\n".join(rows)


def render_entry_details(entries: list[SkillEntry], section_title: str) -> list[str]:
    if not entries:
        return []
    lines = [section_title, ""]
    for i, s in enumerate(entries):
        lines.append(f'<a id="{s.slug}"></a>')
        lines.append("")
        lines.append(f"### {s.name}")
        lines.append("")

        meta: list[str] = []
        if s.seq:
            meta.append(f"**#{s.seq}**")
        meta.append(f"**分类** {category_label(s.category)}")
        if s.recorded_at:
            meta.append(f"**加入** {s.recorded_at}")
        if s.updated_at and s.updated_at != s.recorded_at:
            meta.append(f"**更新** {s.updated_at}")
        if s.stars and entry_bucket(s) != BUCKET_IDEA:
            meta.append(f"**Stars** {format_stars(s.stars)}")
        if s.status:
            meta.append(f"**状态** {status_label(s.status)}")
        if s.tags:
            meta.append(f"**标签** {', '.join(s.tags)}")
        if s.repo_url:
            meta.append(f"**仓库** [{s.repo_url}]({s.repo_url})")
        if s.source == "local":
            meta.append(f"**文档** [{s.detail_path}]({s.detail_path})")
        else:
            meta.append(f"**Issue** [#{s.issue_number}]({s.detail_path})")
        lines.append(" · ".join(meta))
        lines.append("")

        for key in DETAIL_SECTION_MAP:
            content = s.detail_sections.get(key, "").strip()
            if content:
                lines.extend([f"#### {key}", "", content, ""])

        if i < len(entries) - 1:
            lines.extend(["---", ""])
    return lines


def render_skill_details(skills: list[SkillEntry]) -> list[str]:
    return render_entry_details(skills, "## Skill 详情")


def render_readme(entries: list[SkillEntry], issue_count: int) -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M ")
    buckets = split_by_bucket(entries)
    skill_n = len(buckets[BUCKET_SKILL])
    repo_n = len(buckets[BUCKET_REPO])
    idea_n = len(buckets[BUCKET_IDEA])
    total = skill_n + repo_n + idea_n

    lines = [
        "# Skills Record — 目录库",
        "",
        f"> 最后更新：{now}",
        "",
        (
            "收录 **Agent Skill**、**GitHub 开源项目** 与 **偶然想法**。"
            "条目来自仓库内 `skills/` 目录，或 GitHub Issues（标签 `skill-record`）。"
        ),
        "",
        f"共 **{total}** 条：Skill {skill_n} · GitHub 项目 {repo_n} · 想法 {idea_n}",
        "",
        "## Agent Skill",
        "",
        render_table_html(buckets[BUCKET_SKILL], show_stars=True),
        "",
        "## GitHub 项目",
        "",
        render_table_html(buckets[BUCKET_REPO], show_stars=True),
        "",
        "## 想法",
        "",
        render_table_html(buckets[BUCKET_IDEA], show_stars=False),
        "",
    ]

    detail_parts = [
        render_entry_details(buckets[BUCKET_SKILL], "## Skill 详情"),
        render_entry_details(buckets[BUCKET_REPO], "## GitHub 项目详情"),
        render_entry_details(buckets[BUCKET_IDEA], "## 想法详情"),
    ]
    if any(detail_parts):
        lines.extend([p for part in detail_parts for p in (part + [""])])

    if issue_count == 0 and not gh_available():
        lines.extend(
            [
                "> 提示：未检测到 `gh` 登录，仅扫描了本地 `skills/` 目录。"
                "安装并登录 GitHub CLI 后可合并 Issues 中的记录。",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 skills-record 总索引 README.md")
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查 README 是否已是最新（用于 CI）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help=f"输出路径（默认 {OUTPUT.relative_to(REPO_ROOT)}）",
    )
    args = parser.parse_args()

    local = scan_local_skills()
    issues = fetch_issue_skills()
    entries = merge_skills(local, issues)
    content = render_readme(entries, len(issues))

    if args.check:
        if args.output.is_file() and args.output.read_text(encoding="utf-8") == content:
            print("README.md is up to date.")
            return 0
        print("README.md is out of date.", file=sys.stderr)
        return 1

    args.output.write_text(content, encoding="utf-8")
    print(
        f"Wrote {args.output.relative_to(REPO_ROOT)} "
        f"({len(entries)} entries: {len(split_by_bucket(entries)[BUCKET_SKILL])} skills, "
        f"{len(split_by_bucket(entries)[BUCKET_REPO])} repos, "
        f"{len(split_by_bucket(entries)[BUCKET_IDEA])} ideas)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
