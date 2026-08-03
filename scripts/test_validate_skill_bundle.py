from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_skill_bundle import REQUIRED_FILES, SkillBundleValidator


class SkillBundleValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.validator = SkillBundleValidator()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_complete_bundle(self) -> None:
        for relative_path in REQUIRED_FILES:
            path = self.root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test", encoding="utf-8")

    def assert_missing_file_is_rejected(self, relative_path: Path) -> None:
        self.create_complete_bundle()
        (self.root / relative_path).unlink()

        report = self.validator.validate(self.root)

        self.assertEqual(1, report.error_count)
        self.assertIn(relative_path.as_posix(), report.findings[0].message)

    def test_complete_bundle_has_no_errors(self) -> None:
        self.create_complete_bundle()

        report = self.validator.validate(self.root)

        self.assertEqual(0, report.error_count)

    def test_skill_file_only_is_rejected(self) -> None:
        (self.root / "SKILL.md").write_text("test", encoding="utf-8")

        report = self.validator.validate(self.root)

        self.assertEqual(len(REQUIRED_FILES) - 1, report.error_count)

    def test_missing_reference_is_rejected(self) -> None:
        self.assert_missing_file_is_rejected(
            Path("references/quality-gates.html"),
        )

    def test_missing_template_is_rejected(self) -> None:
        self.assert_missing_file_is_rejected(
            Path("assets/document-system/DOCUMENT-TEMPLATE.html"),
        )

    def test_missing_auditor_is_rejected(self) -> None:
        self.assert_missing_file_is_rejected(Path("scripts/audit_document.py"))

    def test_missing_root_is_rejected(self) -> None:
        report = self.validator.validate(self.root / "missing")

        self.assertEqual(1, report.error_count)
        self.assertEqual("BUNDLE001", report.findings[0].code)


if __name__ == "__main__":
    unittest.main()
