import pytest
from md2tex import UnicodeClassifier


def test_ascii_classified_correctly():
    assert UnicodeClassifier.classify('A') == 'ascii'
    assert UnicodeClassifier.classify('1') == 'ascii'
    assert UnicodeClassifier.classify(' ') == 'ascii'


def test_prose_typography_classified():
    assert UnicodeClassifier.classify('\u2019') == 'prose_typography'  # right single quote
    assert UnicodeClassifier.classify('\u2014') == 'prose_typography'  # em-dash
    assert UnicodeClassifier.classify('\u00E9') == 'prose_typography'  # é


def test_math_symbols_classified():
    assert UnicodeClassifier.classify('\u03B1') == 'mathematical_symbol'  # α
    assert UnicodeClassifier.classify('\u2211') == 'mathematical_symbol'  # ∑
    assert UnicodeClassifier.classify('\u222B') == 'mathematical_symbol'  # ∫


def test_control_chars_flagged():
    assert UnicodeClassifier.classify('\u200B') == 'control_invisible'
    assert UnicodeClassifier.classify('\uFEFF') == 'control_invisible'


def test_validate_text_finds_control_chars():
    issues = UnicodeClassifier.validate_text('Hello\u200BWorld')
    assert len(issues) > 0
    assert issues[0]['domain'] == 'control_invisible'


def test_validate_text_clean():
    issues = UnicodeClassifier.validate_text('Hello World! 123')
    assert len(issues) == 0
