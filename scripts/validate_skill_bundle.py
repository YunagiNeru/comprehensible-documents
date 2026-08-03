#!/usr/bin/env python3
"""Skillディレクトリに実行時の必須ファイルが揃っているか検証する。"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


REQUIRED_FILES = (
    Path("SKILL.md"),
    Path("agents/openai.yaml"),
    Path("assets/document-system/DOCUMENT-TEMPLATE.html"),
    Path("assets/document-system/document.css"),
    Path("assets/document-system/tokens.css"),
    Path("references/document-genre-matrix.html"),
    Path("references/evidence-map.html"),
    Path("references/hallmark-document-profile.html"),
    Path("references/human-ai-document-model.html"),
    Path("references/naming-policy.html"),
    Path("references/quality-gates.html"),
    Path("references/reference.css"),
    Path("references/single-document-model.html"),
    Path("scripts/audit_document.py"),
)


@dataclass(frozen=True)
class BundleFinding:
    code: str
    message: str


@dataclass(frozen=True)
class BundleReport:
    root: Path
    findings: tuple[BundleFinding, ...]

    @property
    def error_count(self) -> int:
        return len(self.findings)


class SkillBundleValidator:
    """Skillの実行に必要な同梱ファイルを検証する。"""

    def validate(self, root: Path) -> BundleReport:
        resolved_root = root.resolve()
        if not resolved_root.is_dir():
            finding = BundleFinding(
                "BUNDLE001",
                f"Skillディレクトリが存在しません: {resolved_root}",
            )
            return BundleReport(resolved_root, (finding,))

        findings = tuple(
            BundleFinding(
                "BUNDLE002",
                f"必須ファイルが存在しません: {relative_path.as_posix()}",
            )
            for relative_path in REQUIRED_FILES
            if not (resolved_root / relative_path).is_file()
        )
        return BundleReport(resolved_root, findings)


class BundleReportPrinter:
    @staticmethod
    def print_text(report: BundleReport) -> None:
        print(f"BUNDLE {report.root}")
        for finding in report.findings:
            print(f"ERROR [{finding.code}]: {finding.message}")
        print(f"ERROR {report.error_count}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Skillディレクトリの実行時依存を検証します。",
    )
    parser.add_argument("skill_root", type=Path, help="検証するSkillディレクトリ")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    report = SkillBundleValidator().validate(args.skill_root)
    BundleReportPrinter.print_text(report)
    return 1 if report.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
