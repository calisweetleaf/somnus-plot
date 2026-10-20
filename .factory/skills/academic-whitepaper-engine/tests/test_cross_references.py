import pytest
from md2tex import CrossReferenceLinker


def test_labeled_theorem_gets_label():
    linker = CrossReferenceLinker()
    label = linker._create_label("theorem", "Pythagorean Theorem")
    assert "theorem" in label
    assert "pythagorean-theorem" in label


def test_unnamed_theorems_no_collision():
    linker = CrossReferenceLinker()
    label1 = linker._create_label("theorem", "")
    label2 = linker._create_label("theorem", "")
    assert label1 != label2
    assert label1.startswith("theorem:")
    assert label2.startswith("theorem:")


def test_duplicate_titles_get_suffix():
    linker = CrossReferenceLinker()
    label1 = linker._create_label("theorem", "Main Result")
    label2 = linker._create_label("theorem", "Main Result")
    assert "main-result" in label1
    assert "main-result" in label2
    assert label1 != label2


def test_different_env_types_independent():
    linker = CrossReferenceLinker()
    label1 = linker._create_label("theorem", "Fundamental")
    label2 = linker._create_label("definition", "Fundamental")
    assert label1.startswith("theorem:")
    assert label2.startswith("definition:")
    assert label1 != label2
