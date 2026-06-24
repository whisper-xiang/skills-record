#!/usr/bin/env python3
"""
扫描仓库内各 skill 目录（含 SKILL.md）与 GitHub Issues（label: skill-record），
生成项目根目录 README.md 总索引。

用法:
  python3 scripts/generate-skills-readme.py
  python3 scripts/generate-skills-readme.py --check
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

BUCKET_SKILL = "skill"
BUCKET_REPO = "repo"
BUCKET_IDEA = "idea"

SECTION_ZH = {
    BUCKET_SKILL: "一、Agent Skill",
    BUCKET_REPO: "二、GitHub 项目",
    BUCKET_IDEA: "三、想法",
}

SECTION_NUM = {BUCKET_SKILL: 1, BUCKET_REPO: 2, BUCKET_IDEA: 3}

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


@dataclass
class SkillEntry:
    slug: str
    name: str
    description: str
    source: str
    detail_path: str
    tags: list[str] = field(default_factory=list)
    category: str = ""
    status: str = ""
    stars: str = ""
    repo_url: str = ""
    recorded_at: str = ""
    issue_number: int | None = None
    detail_sections: dict[str, str] = field(default_factory=dict)


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
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True, timeout=10)
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
                "gh", "issue", "list", "--repo", _github_repo(),
                "--label", ISSUE_LABEL, "--state", "all", "--limit", "200",
                "--json", "number,title,body,state",
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
        if display is None or item.get("state") != "OPEN":
            continue
        body = item.get("body") or ""
        meta = parse_record_frontmatter(body)
        slug = meta.get("slug") or slug_from_dir(display)
        number = item["number"]
        category = meta.get("category", "")
        if not category:
            if title.startswith("[repo]"):
                category = "github-repo"
            elif title.startswith("[idea]"):
                category = "idea"
        summary = meta.get("summary") or extract_summary(Path(), meta.get("description", ""))
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
            issue_number=number,
            tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            detail_sections=extract_detail_sections(body, summary),
        )
    return skills


def _github_repo() -> str:
    try:
        url = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "config", "--get", "remote.origin.url"],
            text=True, timeout=5,
        ).strip()
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
    if entry.category == "github-repo":
        return BUCKET_REPO
    if entry.category == "idea":
        return BUCKET_IDEA
    return BUCKET_SKILL


def sort_entries(entries: list[SkillEntry]) -> list[SkillEntry]:
    return sorted(
        entries,
        key=lambda e: (e.recorded_at or "0000-00-00", e.name.lower()),
        reverse=True,
    )


def split_by_bucket(entries: list[SkillEntry]) -> dict[str, list[SkillEntry]]:
    buckets: dict[str, list[SkillEntry]] = {
        BUCKET_SKILL: [], BUCKET_REPO: [], BUCKET_IDEA: [],
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


def skill_status_label(status: str) -> str:
    return {"bookmarked": "收藏", "installed": "已安装"}.get(status, "收藏")


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
        result[key] = f"{result[key]}\n\n{body}" if key in result else body
    if "简介" not in result:
        intro = first_paragraph(preamble) or fallback_summary
        if intro:
            result["简介"] = intro
    return result


def truncate_cell(text: str, max_len: int = TABLE_SUMMARY_MAX) -> str:
    one_line = re.sub(r"\s+", " ", text.replace("|", "\\|")).strip()
    return one_line if len(one_line) <= max_len else one_line[: max_len - 1] + "…"


def md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def render_md_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_暂无记录_"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_escape(c) for c in row) + " |")
    return "\n".join(lines)


def render_index_table(entries: list[SkillEntry], bucket: str) -> str:
    rows: list[list[str]] = []
    for i, e in enumerate(entries, start=1):
        anchor = f"[{e.name}](#{e.slug})"
        joined = e.recorded_at or "—"
        summary = truncate_cell(e.description, 40)
        if bucket == BUCKET_SKILL:
            rows.append([
                str(i),
                anchor,
                category_label(e.category),
                format_stars(e.stars),
                summary,
                skill_status_label(e.status),
                joined,
            ])
        elif bucket == BUCKET_REPO:
            rows.append([str(i), anchor, format_stars(e.stars), summary, joined])
        else:
            rows.append([str(i), anchor, summary, joined])
    if bucket == BUCKET_SKILL:
        headers = ["序号", "名称", "分类", "Stars", "简介", "状态", "加入"]
    elif bucket == BUCKET_REPO:
        headers = ["序号", "名称", "Stars", "简介", "加入"]
    else:
        headers = ["序号", "名称", "简介", "加入"]
    return render_md_table(headers, rows)


def render_meta_table(entry: SkillEntry, bucket: str) -> str:
    rows: list[list[str]] = []
    rows.append(["分类", category_label(entry.category)])
    rows.append(["加入", entry.recorded_at or "—"])
    if bucket != BUCKET_IDEA:
        rows.append(["Stars", format_stars(entry.stars)])
    if bucket == BUCKET_SKILL:
        rows.append(["状态", skill_status_label(entry.status)])
    if entry.tags:
        rows.append(["标签", ", ".join(entry.tags)])
    if entry.repo_url:
        rows.append(["仓库", f"[{entry.repo_url}]({entry.repo_url})"])
    if entry.source == "local":
        rows.append(["文档", f"[{entry.detail_path}]({entry.detail_path})"])
    elif entry.issue_number:
        rows.append(["备份", f"[Issue #{entry.issue_number}]({entry.detail_path})"])
    return render_md_table(["字段", "内容"], rows)


def render_bucket_section(bucket: str, entries: list[SkillEntry]) -> list[str]:
    sec = SECTION_NUM[bucket]
    title = SECTION_ZH[bucket]
    lines = [f"## {title}", ""]
    lines.extend(["### 目录", "", render_index_table(entries, bucket), ""])
    if not entries:
        return lines
    lines.append("### 详情")
    lines.append("")
    for i, entry in enumerate(entries, start=1):
        lines.append(f'<a id="{entry.slug}"></a>')
        lines.append("")
        lines.append(f"#### {sec}.{i} {entry.name}")
        lines.append("")
        lines.append(render_meta_table(entry, bucket))
        lines.append("")
        for key in DETAIL_SECTION_MAP:
            content = entry.detail_sections.get(key, "").strip()
            if content:
                lines.extend([f"##### {key}", "", content, ""])
        if i < len(entries):
            lines.append("---")
            lines.append("")
    return lines


def render_readme(entries: list[SkillEntry], issue_count: int) -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M ")
    buckets = split_by_bucket(entries)
    total = sum(len(v) for v in buckets.values())
    lines = [
        "# Skills Record — 目录库",
        "",
        f"> 最后更新：{now}",
        "",
        "收录 **Agent Skill**、**GitHub 开源项目** 与 **偶然想法**。",
        "序号仅为各模块内顺序编号，非 Issue 编号。Skill 状态仅 **收藏 / 已安装**。",
        "",
        f"共 **{total}** 条：Skill {len(buckets[BUCKET_SKILL])} · "
        f"GitHub 项目 {len(buckets[BUCKET_REPO])} · 想法 {len(buckets[BUCKET_IDEA])}",
        "",
    ]
    for bucket in (BUCKET_SKILL, BUCKET_REPO, BUCKET_IDEA):
        lines.extend(render_bucket_section(bucket, buckets[bucket]))
        lines.append("")
    if issue_count == 0 and not gh_available():
        lines.append(
            "> 提示：未检测到 `gh` 登录，仅扫描了本地 `skills/` 目录。"
            "安装并登录 GitHub CLI 后可合并 Issues 中的记录。"
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 skills-record 总索引 README.md")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
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
    b = split_by_bucket(entries)
    print(
        f"Wrote {args.output.relative_to(REPO_ROOT)} "
        f"({len(entries)} entries: {len(b[BUCKET_SKILL])} skills, "
        f"{len(b[BUCKET_REPO])} repos, {len(b[BUCKET_IDEA])} ideas)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
