"""
Unit tests for _parse_fixer_response() in agents/fixer.py.

This is a pure function with no LLM dependency — ideal for exhaustive
unit testing. Covers happy path, malformed input, and edge cases.
"""

import pytest

from agents.fixer import _parse_fixer_response


# ------------------------------
# Helpers
# ------------------------------

def _make_response(code: str, changelog: str) -> str:
    return f"<fixed_code>\n{code}\n</fixed_code>\n<changelog>\n{changelog}\n</changelog>"


CHANGELOG_JSON = '[{"issue_ref": "CRITICAL L12", "change_made": "Added zero-division guard"}]'

SAMPLE_CODE = """\
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""


# ------------------------------
# Happy path
# ------------------------------

class TestParseFixerResponseHappyPath:
    def test_parses_fixed_code(self):
        response = _make_response(SAMPLE_CODE, CHANGELOG_JSON)
        result = _parse_fixer_response(response)
        assert "def divide" in result.fixed_code
        assert "raise ValueError" in result.fixed_code

    def test_parses_changelog_entry(self):
        response = _make_response(SAMPLE_CODE, CHANGELOG_JSON)
        result = _parse_fixer_response(response)
        assert len(result.changelog) == 1
        assert result.changelog[0].issue_ref == "CRITICAL L12"
        assert "zero-division" in result.changelog[0].change_made.lower()

    def test_parses_multiple_changelog_entries(self):
        multi = (
            '['
            '{"issue_ref": "CRITICAL L5", "change_made": "Added input validation"},'
            '{"issue_ref": "WARNING L20", "change_made": "Escaped SQL parameter"}'
            ']'
        )
        response = _make_response(SAMPLE_CODE, multi)
        result = _parse_fixer_response(response)
        assert len(result.changelog) == 2
        assert result.changelog[1].issue_ref == "WARNING L20"

    def test_preserves_multiline_code(self):
        multiline = "import os\n\ndef safe():\n    return os.getenv('KEY', 'default')\n"
        response = _make_response(multiline, CHANGELOG_JSON)
        result = _parse_fixer_response(response)
        assert "import os" in result.fixed_code
        assert "os.getenv" in result.fixed_code

    def test_returns_fixer_output_type(self):
        from models import FixerOutput
        response = _make_response(SAMPLE_CODE, CHANGELOG_JSON)
        result = _parse_fixer_response(response)
        assert isinstance(result, FixerOutput)


# ------------------------------
# Missing or malformed tags
# ------------------------------

class TestParseFixerResponseEdgeCases:
    def test_missing_fixed_code_tags_falls_back_to_raw(self):
        # No XML tags — whole response becomes the fixed_code
        raw = "def foo(): pass"
        result = _parse_fixer_response(raw)
        assert result.fixed_code == raw

    def test_missing_changelog_tags_returns_empty_list(self):
        response = f"<fixed_code>\n{SAMPLE_CODE}\n</fixed_code>"
        result = _parse_fixer_response(response)
        assert result.changelog == []

    def test_malformed_changelog_json_returns_empty_list(self):
        bad_json = '[{"issue_ref": "L1", BROKEN}'
        response = _make_response(SAMPLE_CODE, bad_json)
        result = _parse_fixer_response(response)
        assert result.changelog == []

    def test_empty_changelog_array_is_valid(self):
        response = _make_response(SAMPLE_CODE, "[]")
        result = _parse_fixer_response(response)
        assert result.changelog == []

    def test_empty_fixed_code_tag(self):
        response = "<fixed_code>\n\n</fixed_code>\n<changelog>\n[]\n</changelog>"
        result = _parse_fixer_response(response)
        # Should not raise — fixed_code may be empty string
        assert isinstance(result.fixed_code, str)

    def test_code_containing_special_characters(self):
        special = 'query = f"SELECT * FROM users WHERE id = \'{user_id}\'"\n'
        response = _make_response(special, CHANGELOG_JSON)
        result = _parse_fixer_response(response)
        assert "SELECT" in result.fixed_code

    def test_code_with_nested_angle_brackets(self):
        """XML-like content inside the fixed code should not confuse the parser."""
        html_code = 'template = "<div class=\\"foo\\">hello</div>"\n'
        response = _make_response(html_code, CHANGELOG_JSON)
        result = _parse_fixer_response(response)
        assert "template" in result.fixed_code

    def test_leading_trailing_whitespace_stripped_from_code(self):
        padded = "\n\n\ndef foo(): pass\n\n\n"
        response = f"<fixed_code>{padded}</fixed_code>\n<changelog>\n[]\n</changelog>"
        result = _parse_fixer_response(response)
        # Regex strips exactly one leading/trailing newline — remaining content is valid
        assert "def foo" in result.fixed_code
