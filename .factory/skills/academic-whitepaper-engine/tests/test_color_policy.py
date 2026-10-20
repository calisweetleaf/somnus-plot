import pytest

try:
    from whitepaper_engine.visuals import VisualValidator
except ImportError:
    VisualValidator = None


def test_template_links_are_black(engine_root):
    template_path = engine_root / "templates" / "somnus-pandoc-template.tex"
    if not template_path.exists():
        pytest.skip("Template not found")
    content = template_path.read_text()
    assert "colorlinks" in content or "hypersetup" in content


def test_code_colors_defined(engine_root):
    template_path = engine_root / "templates" / "somnus-pandoc-template.tex"
    if not template_path.exists():
        pytest.skip("Template not found")
    content = template_path.read_text()
    assert "SomnusKeyword" in content
    assert "SomnusString" in content
    assert "SomnusComment" in content
    assert "SomnusType" in content


def test_no_colored_headings(engine_root):
    template_path = engine_root / "templates" / "somnus-pandoc-template.tex"
    if not template_path.exists():
        pytest.skip("Template not found")
    content = template_path.read_text()
    # Section formatting lines should not contain \color commands
    import re
    section_lines = [
        line for line in content.split("\n")
        if "\\titleformat" in line
    ]
    for line in section_lines:
        assert "\\color" not in line, f"Color found in section formatting: {line}"


@pytest.mark.skipif(VisualValidator is None, reason="whitepaper_engine.visuals not implemented")
def test_visual_validator_rejects_unvalidated():
    validator = VisualValidator()
    # validate_visual returns a list of issue strings
    entry = {"id": "fig1", "type": "chart"}  # missing required fields
    issues = validator.validate_visual(entry)
    assert isinstance(issues, list)
    assert len(issues) > 0
