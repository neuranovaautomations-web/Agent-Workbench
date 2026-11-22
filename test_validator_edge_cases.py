"""Regression tests for skill metadata limits and malformed frontmatter."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_skills import parse_skill_file, validate_skill_file  # noqa: E402


class SkillMetadataBoundaryTests(unittest.TestCase):
    def write_skill(self, directory: str, name: str, description: str) -> Path:
        path = Path(directory) / "SKILL.md"
        body = "Operational workflow. " * 12
        path.write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n{body}",
            encoding="utf-8",
        )
        return path

    def test_accepts_name_and_description_at_documented_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_skill(temp, "a" * 64, "d" * 1024)
            errors = validate_skill_file(path)
        self.assertFalse(any("exceeds 64 characters" in error for error in errors))
        self.assertFalse(any("exceeds 1024 characters" in error for error in errors))

    def test_rejects_name_longer_than_64_characters(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_skill(temp, "a" * 65, "A valid description.")
            errors = validate_skill_file(path)
        self.assertTrue(any("name exceeds 64 characters" in error for error in errors))

    def test_rejects_description_longer_than_1024_characters(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_skill(temp, "sample-skill", "d" * 1025)
            errors = validate_skill_file(path)
        self.assertTrue(any("description exceeds 1024 characters" in error for error in errors))

    def test_rejects_name_that_is_not_a_lowercase_hyphenated_slug(self):
        with tempfile.TemporaryDirectory() as temp:
            path = self.write_skill(temp, "Invalid_Name", "A valid description.")
            errors = validate_skill_file(path)
        self.assertTrue(any("lowercase hyphenated slug" in error for error in errors))

    def test_reports_missing_closing_frontmatter_delimiter(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            path.write_text(
                "---\nname: sample-skill\ndescription: A valid description.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "closing"):
                parse_skill_file(path)

    def test_reports_frontmatter_line_without_key_value_separator(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            path.write_text(
                "---\nname: sample-skill\nthis is malformed\ndescription: Valid.\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "expected key: value"):
                parse_skill_file(path)

    def test_reports_empty_frontmatter_value(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "SKILL.md"
            path.write_text(
                "---\nname: sample-skill\ndescription:\n---\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "key and value are required"):
                parse_skill_file(path)


if __name__ == "__main__":
    unittest.main()
