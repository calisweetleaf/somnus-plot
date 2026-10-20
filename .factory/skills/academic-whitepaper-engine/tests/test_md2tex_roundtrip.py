import pytest
from md2tex import MathNormalizer, AdmonitionProcessor, CitationProcessor


@pytest.fixture
def sample_input(tmp_path):
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)
    md_file = fixtures_dir / "sample_input.md"
    content = """# Heading

```math
E = mc^2
```

Inline math $x = y$ is here.

Prose paragraph with = sign but not math.

> [!THEOREM] Test Theorem
> Content.

Citation here: [[Author 2024: Some Paper]]
"""
    md_file.write_text(content)
    return md_file


def test_math_fence_converted():
    normalizer = MathNormalizer()
    input_text = "```math\nE = mc^2\n```"
    output = normalizer.normalize(input_text)
    assert "$$" in output
    assert "```math" not in output


def test_prose_not_wrapped_in_math():
    normalizer = MathNormalizer()
    input_text = "Prose paragraph with = sign."
    output = normalizer.normalize(input_text)
    assert "$$" not in output
    assert "\\[" not in output


def test_admonition_converted():
    processor = AdmonitionProcessor()
    input_text = "> [!THEOREM] Test Theorem\n> Content."
    output = processor.process(input_text)
    assert "\\begin{theorem}" in output


def test_citation_converted():
    processor = CitationProcessor()
    input_text = "See [[Author 2024: Some Paper]] for details."
    output = processor.process(input_text)
    assert "\\cite" in output
