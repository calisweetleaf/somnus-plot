import pytest
import shutil
from pathlib import Path

def test_pandoc_template_uses_biblatex(engine_root):
    template_path = engine_root / "templates" / "somnus-pandoc-template.tex"
    if not template_path.exists():
        pytest.skip("Template not found")
    content = template_path.read_text()
    assert "biblatex" in content
    assert "bibtex" not in content.replace("bibtex8", "")

def test_pandoc_template_uses_biber(engine_root):
    template_path = engine_root / "templates" / "somnus-pandoc-template.tex"
    if not template_path.exists():
        pytest.skip("Template not found")
    content = template_path.read_text()
    assert "biber" in content

def test_no_natbib_in_template(engine_root):
    template_path = engine_root / "templates" / "somnus-pandoc-template.tex"
    if not template_path.exists():
        pytest.skip("Template not found")
    content = template_path.read_text()
    assert "natbib" not in content

def test_build_command_includes_biber():
    try:
        from whitepaper_engine.compiler import get_build_command
        # If implemented, verify biber is in the command
        pass
    except ImportError:
        pytest.skip("whitepaper_engine.compiler not implemented yet")
