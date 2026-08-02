from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from audit_document import DocumentAuditor


VALID_DOCUMENT = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="監査用の正常文書。">
  <title>正常文書</title>
  <style>:root { --ink: #123456; } body { color: var(--ink); }</style>
</head>
<body>
  <main id="main">
    <h1>正常文書</h1>
    <section id="requirements">
      <h2>要求</h2>
      <article class="record" id="REQ-001">
        <h3>直接参照</h3>
        <p>種別: 要求</p>
        <p>状態: 承認済み</p>
        <p>規範強度: 必須</p>
        <p class="record__statement">文書は通常参照だけで理解できなければならない。</p>
      </article>
      <figure>
        <svg viewBox="0 0 10 10" role="img"><title>関係図</title><desc>一つの要素を示す。</desc><circle cx="5" cy="5" r="4"></circle></svg>
        <figcaption>REQ-001の関係を示す。</figcaption>
      </figure>
      <table><caption>要求一覧</caption><thead><tr><th scope="col">ID</th><th scope="col">状態</th></tr></thead><tbody><tr><th scope="row">REQ-001</th><td>承認済み</td></tr></tbody></table>
    </section>
  </main>
</body>
</html>
"""


class DocumentAuditorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)
        self.auditor = DocumentAuditor()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.directory / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_document_has_no_errors(self) -> None:
        report = self.auditor.audit(self.write("REQUIREMENTS.html", VALID_DOCUMENT))
        self.assertEqual(0, report.error_count, [item.message for item in report.findings])

    def test_invalid_name_is_rejected(self) -> None:
        report = self.auditor.audit(self.write("requirements.html", VALID_DOCUMENT))
        self.assertIn("NAME001", {item.code for item in report.findings})

    def test_duplicate_id_and_missing_fragment_are_rejected(self) -> None:
        invalid = VALID_DOCUMENT.replace(
            "<h1>正常文書</h1>",
            '<h1 id="duplicate">正常文書</h1><p id="duplicate"><a href="#missing">参照</a></p>',
        )
        report = self.auditor.audit(self.write("REQUIREMENTS.html", invalid))
        codes = {item.code for item in report.findings}
        self.assertIn("LINK001", codes)
        self.assertIn("LINK002", codes)

    def test_external_stylesheet_is_rejected(self) -> None:
        invalid = VALID_DOCUMENT.replace(
            "<style>:root { --ink: #123456; } body { color: var(--ink); }</style>",
            '<link rel="stylesheet" href="document.css">',
        )
        report = self.auditor.audit(self.write("REQUIREMENTS.html", invalid))
        self.assertIn("SELF001", {item.code for item in report.findings})

    def test_canonical_statement_inside_details_is_rejected(self) -> None:
        invalid = VALID_DOCUMENT.replace(
            '<p class="record__statement">文書は通常参照だけで理解できなければならない。</p>',
            '<details><summary>詳細</summary><p class="record__statement">文書は通常参照だけで理解できなければならない。</p></details>',
        )
        report = self.auditor.audit(self.write("REQUIREMENTS.html", invalid))
        self.assertIn("REC006", {item.code for item in report.findings})


if __name__ == "__main__":
    unittest.main()
