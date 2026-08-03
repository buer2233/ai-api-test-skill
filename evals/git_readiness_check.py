#!/usr/bin/env python3
"""Read-only Git readiness checks for the api-test-E10 skill."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    path: str
    message: str


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def status_paths(repo_root: Path) -> list[tuple[str, str]]:
    raw = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repo_root,
        check=False,
        capture_output=True,
    ).stdout
    entries: list[tuple[str, str]] = []
    for item in raw.split(b"\0"):
        if len(item) < 4:
            continue
        decoded = item.decode("utf-8", errors="replace")
        entries.append((decoded[:2], decoded[3:]))
    return entries


def parse_skill_name(skill_md: Path) -> str | None:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^name:\s*(\S+)\s*$", text, re.MULTILINE)
    return match.group(1).strip("\"'") if match else None


def collect_findings(repo_root: Path, skill_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    entries = status_paths(repo_root)
    changed_paths = {path for _, path in entries}

    skill_name = parse_skill_name(skill_root / "SKILL.md")
    if skill_name and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
        findings.append(
            Finding(
                "BLOCKER",
                "skill-name",
                str(skill_root / "SKILL.md"),
                f"frontmatter name {skill_name!r} is not hyphen-case",
            )
        )

    tracked_accounts = run_git(repo_root, "ls-files", "*account.txt").splitlines()
    for path in tracked_accounts:
        findings.append(
            Finding(
                "BLOCKER",
                "tracked-credentials",
                path,
                "tracked account data file may contain live credentials; rotate and externalize before commit",
            )
        )

    for path in sorted(changed_paths):
        normalized = path.replace("\\", "/")
        if normalized.startswith("api_test_dwp_temp/") or normalized == "nul":
            findings.append(
                Finding(
                    "BLOCKER",
                    "runtime-artifact",
                    path,
                    "runtime artifact is part of the Git change set",
                )
            )
        if normalized.endswith(".sqlite3"):
            try:
                size = (repo_root / path).stat().st_size
            except OSError:
                size = 0
            if size >= 10 * 1024 * 1024:
                findings.append(
                    Finding(
                        "WARN",
                        "large-binary",
                        path,
                        f"large SQLite binary ({size / 1024 / 1024:.1f} MiB) has no human-readable diff",
                    )
                )
        if normalized.endswith("/JenkinsReport/report.html"):
            findings.append(
                Finding(
                    "WARN",
                    "report-artifact",
                    path,
                    "generated report changed; keep separate from skill/eval source changes",
                )
            )

    cached = run_git(repo_root, "diff", "--cached", "--name-status")
    for line in cached.splitlines():
        if line.startswith("D\t") and "report.html" in line:
            findings.append(
                Finding(
                    "WARN",
                    "staged-report-delete",
                    line[2:],
                    "staged deletion appears to be a generated report",
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--skill-root", type=Path, default=None)
    args = parser.parse_args()

    skill_root = (args.skill_root or Path(__file__).resolve().parents[1]).resolve()
    repo_root = (args.repo_root or skill_root.parents[2]).resolve()
    findings = collect_findings(repo_root, skill_root)
    if not findings:
        print("git readiness: PASS")
        return 0
    for finding in findings:
        print(f"[{finding.severity}] {finding.code}: {finding.path} - {finding.message}")
    blockers = sum(finding.severity == "BLOCKER" for finding in findings)
    warnings = len(findings) - blockers
    print(f"git readiness: {blockers} blocker(s), {warnings} warning(s)")
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
