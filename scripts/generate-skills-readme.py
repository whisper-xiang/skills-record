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
ISSUE_TITLE_PREFIX = "[skill]"
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
    issue_number: int | None = None


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
    match = re.match(r"^---\s*\n(.*?)\n---", body, re.DOTALL)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
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

        skills[slug] = SkillEntry(
            slug=slug,
            name=name,
            description=extract_summary(readme, description),
            source="local",
            detail_path=f"{rel}/README.md" if readme.is_file() else f"{rel}/SKILL.md",
            category=meta.get("category", "cursor-skill"),
            tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
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
        if not title.startswith(ISSUE_TITLE_PREFIX) or title.startswith(INDEX_ISSUE_TITLE):
            continue
        if item.get("state") != "OPEN":
            continue

        display = title[len(ISSUE_TITLE_PREFIX) :].strip()
        body = item.get("body") or ""
        meta = parse_record_frontmatter(body)
        slug = meta.get("slug") or slug_from_dir(display)
        number = item["number"]

        skills[slug] = SkillEntry(
            slug=slug,
            name=meta.get("title", display),
            description=meta.get("summary") or extract_summary(Path(), meta.get("description", "")),
            source="issue",
            detail_path=f"https://github.com/{_github_repo()}/issues/{number}",
            category=meta.get("category", ""),
            status=meta.get("status", ""),
            stars=meta.get("stars", ""),
            repo_url=meta.get("repo_url", ""),
            issue_number=number,
            tags=[t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
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
    return sorted(merged.values(), key=lambda s: s.name.lower())


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
    }
    return mapping.get(status, status or "—")


def category_label(cat: str) -> str:
    mapping = {
        "cursor-skill": "Cursor Skill",
        "claude-skill": "Claude Skill",
        "mcp": "MCP",
        "agent-tool": "Agent 工具",
        "other": "其他",
    }
    return mapping.get(cat, cat or "—")


def source_label(entry: SkillEntry) -> str:
    if entry.source == "local":
        return f"本地 `skills/{entry.slug}/`"
    return f"Issue #{entry.issue_number}"


def render_readme(skills: list[SkillEntry], issue_count: int) -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M ")
    lines = [
        "# Skills Record — 技能记录库",
        "",
        f"> 最后更新：{now}",
        "",
        "收录 Cursor / Claude Agent Skill 与相关工具。技能可来自 **`skills/` 目录**（各子目录含 `SKILL.md`）或 **GitHub Issues**（标签 `skill-record`）。",
        "",
        "## 技能目录",
        "",
        "| 名称 | Stars | 分类 | 简介 | 状态 | 来源 | 详情 |",
        "|------|-------|------|------|------|------|------|",
    ]

    if not skills:
        lines.append("| _暂无记录_ | — | — | — | — | — | — |")
    else:
        for s in skills:
            if s.source == "local":
                link = f"[README]({s.detail_path})"
            else:
                link = f"[Issue #{s.issue_number}]({s.detail_path})"
            desc = s.description.replace("|", "\\|")
            lines.append(
                f"| {s.name} | {format_stars(s.stars)} | {category_label(s.category)} | {desc} | {status_label(s.status)} | {source_label(s)} | {link} |"
            )

    if issue_count == 0 and not gh_available():
        lines.extend(
            [
                "> 提示：未检测到 `gh` 登录，仅扫描了本地目录。安装并登录 GitHub CLI 后可合并 Issues 中的技能。",
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
    skills = merge_skills(local, issues)
    content = render_readme(skills, len(issues))

    if args.check:
        if args.output.is_file() and args.output.read_text(encoding="utf-8") == content:
            print("README.md is up to date.")
            return 0
        print("README.md is out of date.", file=sys.stderr)
        return 1

    args.output.write_text(content, encoding="utf-8")
    print(f"Wrote {args.output.relative_to(REPO_ROOT)} ({len(skills)} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
