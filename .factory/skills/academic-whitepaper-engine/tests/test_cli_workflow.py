import pytest
import shutil

try:
    from whitepaper_engine.state import StateTracker
except ImportError:
    StateTracker = None


@pytest.mark.skipif(StateTracker is None, reason="whitepaper_engine.state not implemented")
def test_state_init_creates_directory(tmp_project):
    tracker = StateTracker(tmp_project)
    tracker.init()

    state_dir = tmp_project / "whitepaper" / "state"
    assert state_dir.exists()
    assert (state_dir / "session.json").exists()
    assert (state_dir / "tasklist.json").exists()


@pytest.mark.skipif(StateTracker is None, reason="whitepaper_engine.state not implemented")
def test_state_status_returns_dict(tmp_project):
    tracker = StateTracker(tmp_project)
    tracker.init()
    status = tracker.status()
    assert isinstance(status, dict)
    # The status dict has 'session', 'tasklist', and 'active_state' keys
    assert "active_state" in status
    assert status["active_state"] == 0


@pytest.mark.skipif(StateTracker is None, reason="whitepaper_engine.state not implemented")
def test_state_advance_increments(tmp_project):
    tracker = StateTracker(tmp_project)
    tracker.init()
    initial_state = tracker.status()["active_state"]
    tracker.advance()
    new_state = tracker.status()["active_state"]
    assert new_state > initial_state


@pytest.mark.skipif(StateTracker is None, reason="whitepaper_engine.state not implemented")
def test_state_advance_respects_dependencies(tmp_project):
    tracker = StateTracker(tmp_project)
    tracker.init()
    # Trying to jump to state 5 should fail — deps 0-4 not complete
    result = tracker.advance(state_id=5)
    assert result is False


@pytest.mark.skipif(StateTracker is None, reason="whitepaper_engine.state not implemented")
def test_state_verify_checks_artifacts(tmp_project):
    tracker = StateTracker(tmp_project)
    tracker.init()
    report = tracker.verify()
    assert isinstance(report, dict)
