#!/usr/bin/env python3
"""自己完結HTML技術文書の構文と検査可能な構造を監査する。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Sequence


VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
HEADING_PATTERN = re.compile(r"h([1-6])")
DOCUMENT_NAME_PATTERN = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*\.html$")
RECORD_ID_PATTERN = re.compile(r"^(?:REQ|DEC|CON|ASM|PRO|REC|OPN)-\d{3,}$")
SPACE_PATTERN = re.compile(r"\s+")


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Finding:
    severity: Severity
    code: str
    message: str
    line: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "line": self.line,
        }


@dataclass
class Element:
    tag: str
    attrs: dict[str, str]
    line: int
    column: int
    parent: Element | None = None
    children: list[Element] = field(default_factory=list)
    data: list[str] = field(default_factory=list)

    def descendants(self, tag: str | None = None) -> Iterable[Element]:
        for child in self.children:
            if tag is None or child.tag == tag:
                yield child
            yield from child.descendants(tag)

    def text_content(self) -> str:
        parts = list(self.data)
        for child in self.children:
            parts.append(child.text_content())
        return SPACE_PATTERN.sub(" ", " ".join(parts)).strip()

    def has_class(self, class_name: str) -> bool:
        return class_name in self.attrs.get("class", "").split()


class DocumentParser(HTMLParser):
    """明示的に閉じた生成HTMLを対象とする小さな構文木パーサー。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {}, 1, 0)
        self.stack: list[Element] = [self.root]
        self.doctype_found = False
        self.findings: list[Finding] = []

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {name.lower(): value or "" for name, value in attrs}

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype_found = True

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line, column = self.getpos()
        tag = tag.lower()
        element = Element(tag, self._attrs(attrs), line, column, self.stack[-1])
        self.stack[-1].children.append(element)
        if tag not in VOID_ELEMENTS:
            self.stack.append(element)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        line, column = self.getpos()
        tag = tag.lower()
        self.stack[-1].children.append(
            Element(tag, self._attrs(attrs), line, column, self.stack[-1])
        )

    def handle_endtag(self, tag: str) -> None:
        line, _ = self.getpos()
        tag = tag.lower()
        if len(self.stack) == 1:
            self.findings.append(Finding(Severity.ERROR, "HTML002", f"対応する開始タグのない </{tag}> があります。", line))
            return
        if self.stack[-1].tag == tag:
            self.stack.pop()
            return
        open_tags = [element.tag for element in self.stack[1:]]
        if tag not in open_tags:
            self.findings.append(Finding(Severity.ERROR, "HTML002", f"対応する開始タグのない </{tag}> があります。", line))
            return
        self.findings.append(
            Finding(
                Severity.ERROR,
                "HTML003",
                f"<{self.stack[-1].tag}> を閉じる前に </{tag}> が現れています。",
                line,
            )
        )
        while len(self.stack) > 1 and self.stack[-1].tag != tag:
            self.stack.pop()
        if len(self.stack) > 1:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].data.append(data)

    def close(self) -> None:
        super().close()
        for element in self.stack[1:]:
            self.findings.append(
                Finding(Severity.ERROR, "HTML004", f"<{element.tag}> が閉じられていません。", element.line)
            )
        self.stack = [self.root]


@dataclass
class AuditReport:
    path: Path
    findings: list[Finding]

    @property
    def error_count(self) -> int:
        return sum(item.severity is Severity.ERROR for item in self.findings)

    @property
    def warning_count(self) -> int:
        return sum(item.severity is Severity.WARNING for item in self.findings)

    def as_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "errors": self.error_count,
            "warnings": self.warning_count,
            "findings": [item.as_dict() for item in self.findings],
        }


class DocumentAuditor:
    """HTML文書の構文、意味構造、自己完結性を監査する。"""

    def audit(self, path: Path) -> AuditReport:
        findings: list[Finding] = []
        if not path.is_file():
            return AuditReport(path, [Finding(Severity.ERROR, "FILE001", "対象ファイルが存在しません。")])

        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return AuditReport(path, [Finding(Severity.ERROR, "FILE002", "UTF-8として読み込めません。")])

        if not DOCUMENT_NAME_PATTERN.fullmatch(path.name):
            findings.append(
                Finding(Severity.ERROR, "NAME001", "文書名はUPPER-KEBAB-CASE.htmlにしてください。")
            )

        parser = DocumentParser()
        try:
            parser.feed(source)
            parser.close()
        except Exception as exc:  # HTMLParser由来の予期しない構文障害を報告する。
            findings.append(Finding(Severity.ERROR, "HTML001", f"HTMLを解析できません: {exc}"))
            return AuditReport(path, findings)

        findings.extend(parser.findings)
        root = parser.root
        elements = list(root.descendants())

        if not parser.doctype_found:
            findings.append(Finding(Severity.ERROR, "DOC001", "<!DOCTYPE html> がありません。"))

        html_elements = [item for item in elements if item.tag == "html"]
        if len(html_elements) != 1:
            findings.append(Finding(Severity.ERROR, "DOC002", "html要素は一つ必要です。"))
        elif not html_elements[0].attrs.get("lang"):
            findings.append(Finding(Severity.ERROR, "DOC003", "html要素にlang属性が必要です。", html_elements[0].line))

        self._audit_metadata(elements, findings)
        self._audit_landmarks(elements, findings)
        self._audit_headings(elements, findings)
        self._audit_ids_and_links(elements, findings)
        self._audit_media(elements, findings)
        self._audit_tables(elements, findings)
        self._audit_self_containment(elements, source, findings)
        self._audit_records(elements, findings)

        findings.sort(key=lambda item: (0 if item.severity is Severity.ERROR else 1, item.line or 0, item.code))
        return AuditReport(path, findings)

    @staticmethod
    def _audit_metadata(elements: Sequence[Element], findings: list[Finding]) -> None:
        metas = [item for item in elements if item.tag == "meta"]
        if not any("charset" in item.attrs for item in metas):
            findings.append(Finding(Severity.ERROR, "META001", "meta charsetがありません。"))
        if not any(item.attrs.get("name", "").lower() == "viewport" for item in metas):
            findings.append(Finding(Severity.ERROR, "META002", "viewportメタ情報がありません。"))
        if not any(item.attrs.get("name", "").lower() == "description" and item.attrs.get("content", "").strip() for item in metas):
            findings.append(Finding(Severity.WARNING, "META003", "文書説明のmeta要素がありません。"))
        titles = [
            item for item in elements
            if item.tag == "title" and item.parent is not None and item.parent.tag == "head"
        ]
        if len(titles) != 1 or not titles[0].text_content():
            findings.append(Finding(Severity.ERROR, "META004", "空でないtitle要素が一つ必要です。"))

    @staticmethod
    def _audit_landmarks(elements: Sequence[Element], findings: list[Finding]) -> None:
        mains = [item for item in elements if item.tag == "main"]
        if len(mains) != 1:
            findings.append(Finding(Severity.ERROR, "SEM001", "main要素は一つ必要です。"))
        h1s = [item for item in elements if item.tag == "h1"]
        if len(h1s) != 1:
            findings.append(Finding(Severity.ERROR, "SEM002", "h1要素は一つ必要です。"))
        for section in [item for item in elements if item.tag == "section"]:
            has_heading = any(HEADING_PATTERN.fullmatch(child.tag) for child in section.descendants())
            if not has_heading and not section.attrs.get("aria-label") and not section.attrs.get("aria-labelledby"):
                findings.append(Finding(Severity.WARNING, "SEM003", "sectionに見出しまたはアクセシブルな名前がありません。", section.line))

    @staticmethod
    def _audit_headings(elements: Sequence[Element], findings: list[Finding]) -> None:
        previous_level: int | None = None
        for heading in [item for item in elements if HEADING_PATTERN.fullmatch(item.tag)]:
            level = int(heading.tag[1])
            if not heading.text_content():
                findings.append(Finding(Severity.ERROR, "HEAD001", f"{heading.tag}が空です。", heading.line))
            if previous_level is not None and level > previous_level + 1:
                findings.append(Finding(Severity.ERROR, "HEAD002", f"見出し階層がh{previous_level}からh{level}へ飛んでいます。", heading.line))
            previous_level = level

    @staticmethod
    def _audit_ids_and_links(elements: Sequence[Element], findings: list[Finding]) -> None:
        ids: dict[str, Element] = {}
        for element in elements:
            element_id = element.attrs.get("id")
            if not element_id:
                continue
            if element_id in ids:
                findings.append(Finding(Severity.ERROR, "LINK001", f"id '{element_id}' が重複しています。", element.line))
            else:
                ids[element_id] = element
        for anchor in [item for item in elements if item.tag == "a"]:
            href = anchor.attrs.get("href", "")
            if href.startswith("#") and len(href) > 1 and href[1:] not in ids:
                findings.append(Finding(Severity.ERROR, "LINK002", f"内部リンク先 '{href}' が存在しません。", anchor.line))

    @staticmethod
    def _audit_media(elements: Sequence[Element], findings: list[Finding]) -> None:
        for image in [item for item in elements if item.tag == "img"]:
            if "alt" not in image.attrs:
                findings.append(Finding(Severity.ERROR, "MEDIA001", "img要素にalt属性がありません。", image.line))
            src = image.attrs.get("src", "")
            if src.startswith(("http://", "https://", "//")):
                findings.append(Finding(Severity.ERROR, "MEDIA002", "外部画像へ依存しています。", image.line))
            if src.startswith("data:") and len(src) > 8192:
                findings.append(Finding(Severity.WARNING, "MEDIA003", "大きなData URIがAIの直接参照と差分確認を圧迫します。", image.line))
        for figure in [item for item in elements if item.tag == "figure"]:
            if not any(True for _ in figure.descendants("figcaption")):
                findings.append(Finding(Severity.ERROR, "MEDIA004", "figureにfigcaptionがありません。", figure.line))
        for svg in [item for item in elements if item.tag == "svg"]:
            if svg.attrs.get("aria-hidden") == "true":
                continue
            title_found = any(True for _ in svg.descendants("title"))
            description_found = any(True for _ in svg.descendants("desc"))
            if not title_found or not description_found:
                findings.append(Finding(Severity.ERROR, "MEDIA005", "意味を持つsvgにはtitleとdescが必要です。", svg.line))

    @staticmethod
    def _audit_tables(elements: Sequence[Element], findings: list[Finding]) -> None:
        for table in [item for item in elements if item.tag == "table"]:
            if not any(True for _ in table.descendants("caption")):
                findings.append(Finding(Severity.ERROR, "TABLE001", "tableにcaptionがありません。", table.line))
            headers = list(table.descendants("th"))
            if not headers:
                findings.append(Finding(Severity.ERROR, "TABLE002", "tableにth要素がありません。", table.line))
            for header in headers:
                if header.attrs.get("scope") not in {"col", "row", "colgroup", "rowgroup"}:
                    findings.append(Finding(Severity.WARNING, "TABLE003", "th要素にscope属性がありません。", header.line))

    @staticmethod
    def _audit_self_containment(elements: Sequence[Element], source: str, findings: list[Finding]) -> None:
        for link in [item for item in elements if item.tag == "link"]:
            if "stylesheet" in link.attrs.get("rel", "").lower().split():
                findings.append(Finding(Severity.ERROR, "SELF001", "外部CSSへ依存しています。成果物ではstyle要素へ取り込んでください。", link.line))
        for script in [item for item in elements if item.tag == "script"]:
            findings.append(Finding(Severity.ERROR, "SELF002", "文書成果物にscript要素を使用しないでください。", script.line))
        for style in [item for item in elements if item.tag == "style"]:
            style_text = style.text_content()
            if re.search(r"@import|url\s*\(\s*['\"]?(?:https?:)?//", style_text, re.IGNORECASE):
                findings.append(Finding(Severity.ERROR, "SELF003", "CSSが外部資源へ依存しています。", style.line))
            if len(style_text) > 50000:
                findings.append(Finding(Severity.WARNING, "CTX001", "インラインCSSが50,000文字を超えています。重複と不要規則を確認してください。", style.line))
        if len(source) > 500000:
            findings.append(Finding(Severity.WARNING, "CTX002", "HTMLが500,000文字を超えています。正本の重複と埋め込み資産を確認してください。"))

    @staticmethod
    def _audit_records(elements: Sequence[Element], findings: list[Finding]) -> None:
        records = [item for item in elements if item.has_class("record")]
        statements: dict[str, Element] = {}
        for record in records:
            record_id = record.attrs.get("id", "")
            if not RECORD_ID_PATTERN.fullmatch(record_id):
                findings.append(Finding(Severity.ERROR, "REC001", "規範レコードに有効な安定IDがありません。", record.line))
            text = record.text_content()
            for label in ("種別", "規範強度"):
                if label not in text:
                    findings.append(Finding(Severity.ERROR, "REC002", f"規範レコードに'{label}'がありません。", record.line))
            if not any(status in text for status in ("承認済み", "提案", "未確定", "実装済み", "検証済み", "廃止", "置換済み")):
                findings.append(Finding(Severity.ERROR, "REC003", "規範レコードに状態がありません。", record.line))
            statement_nodes = [item for item in record.descendants() if item.has_class("record__statement")]
            if len(statement_nodes) != 1 or not statement_nodes[0].text_content():
                findings.append(Finding(Severity.ERROR, "REC004", "規範レコードには空でない正本本文が一つ必要です。", record.line))
                continue
            statement = SPACE_PATTERN.sub(" ", statement_nodes[0].text_content()).strip().casefold()
            if statement in statements:
                findings.append(Finding(Severity.ERROR, "REC005", f"正本本文がレコード '{statements[statement].attrs.get('id', '')}' と重複しています。", statement_nodes[0].line))
            else:
                statements[statement] = record
            ancestor = statement_nodes[0].parent
            while ancestor is not None and ancestor is not record:
                if ancestor.tag == "details":
                    findings.append(Finding(Severity.ERROR, "REC006", "正本本文をdetails内へ隠さないでください。", statement_nodes[0].line))
                    break
                ancestor = ancestor.parent


class ReportPrinter:
    @staticmethod
    def print_text(reports: Sequence[AuditReport]) -> None:
        for report in reports:
            print(f"AUDIT {report.path}")
            for finding in report.findings:
                location = f" line {finding.line}" if finding.line is not None else ""
                print(f"{finding.severity.value} [{finding.code}]{location}: {finding.message}")
            print(f"ERROR {report.error_count} / WARNING {report.warning_count}")

    @staticmethod
    def print_json(reports: Sequence[AuditReport]) -> None:
        print(json.dumps([report.as_dict() for report in reports], ensure_ascii=False, indent=2))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="自己完結HTML技術文書を監査します。")
    parser.add_argument("paths", nargs="+", type=Path, help="監査するHTMLファイル")
    parser.add_argument("--json", action="store_true", help="結果をJSONで出力します。")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    auditor = DocumentAuditor()
    reports = [auditor.audit(path) for path in args.paths]
    if args.json:
        ReportPrinter.print_json(reports)
    else:
        ReportPrinter.print_text(reports)
    return 1 if any(report.error_count for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
