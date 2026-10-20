import sys
import os
import pytest
from pathlib import Path

# Add engine root and scripts to sys.path
engine_root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_root_path))
sys.path.insert(0, str(engine_root_path / "scripts"))

@pytest.fixture
def engine_root():
    return engine_root_path

@pytest.fixture
def tmp_project(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    state_dir = project_dir / "whitepaper" / "state"
    state_dir.mkdir(parents=True)
    return project_dir

@pytest.fixture
def sample_markdown(tmp_path):
    md_file = tmp_path / "sample.md"
    md_file.write_text("Sample markdown content with $E = mc^2$, code `print(1)`, and citation [[Smith 2023]].")
    return md_file

@pytest.fixture
def sample_claim_ledger(tmp_path):
    ledger = tmp_path / "claim-ledger.yaml"
    ledger.write_text("claims:\n  - id: claim1\n    text: sample claim\n")
    return ledger

@pytest.fixture
def sample_visual_ledger(tmp_path):
    ledger = tmp_path / "visual-ledger.yaml"
    ledger.write_text("visuals:\n  - id: fig1\n    type: chart\n    grayscale_fallback: true\n")
    return ledger
