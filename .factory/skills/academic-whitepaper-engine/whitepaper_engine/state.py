import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class StateTracker:
    STATES = {
        0: {"name": "Reconnaissance", "deps": [], "artifacts": ['whitepaper/state/reconnaissance.json']},
        1: {"name": "Authority Map", "deps": [0], "artifacts": ['whitepaper/state/authority-map.yaml']},
        2: {"name": "Thesis Contract", "deps": [1], "artifacts": ['whitepaper/state/thesis-contract.md']},
        3: {"name": "Claim Ledger", "deps": [2], "artifacts": ['whitepaper/state/claim-ledger.yaml']},
        4: {"name": "Visual Ledger", "deps": [2], "artifacts": ['whitepaper/state/visual-ledger.yaml']},
        5: {"name": "Section Graph", "deps": [3, 4], "artifacts": ['whitepaper/state/section-graph.yaml']},
        6: {"name": "Markdown Composition", "deps": [5], "artifacts": ['src/sections/']},
        7: {"name": "Editorial Passes", "deps": [6], "artifacts": []},
        8: {"name": "TeX Transcreation", "deps": [7], "artifacts": ['output/whitepaper.tex']},
        9: {"name": "Build & Render Validation", "deps": [8], "artifacts": ['output/whitepaper.pdf']},
        10: {"name": "Anti-Genericity Review", "deps": [9], "artifacts": ['whitepaper/state/validation-report.json']},
        11: {"name": "Release Bundle", "deps": [10], "artifacts": ['output/whitepaper.pdf', 'whitepaper/state/build-manifest.json']}
    }

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / 'whitepaper' / 'state'
        self.session_file = self.state_dir / 'session.json'
        self.tasklist_file = self.state_dir / 'tasklist.json'

    def init(self) -> None:
        """Creates state directory structure, generates default session.json and tasklist.json."""
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        session = {
            "current_state": 0,
            "completed_states": []
        }
        self._save_session(session)

        tasklist = {
            str(k): {"status": "pending", "name": v["name"]}
            for k, v in self.STATES.items()
        }
        self._save_tasklist(tasklist)
        print(f"Initialized state tracker in {self.state_dir}", file=sys.stdout)

    def status(self) -> dict:
        """Returns current session state."""
        try:
            session = self._load_session()
            tasklist = self._load_tasklist()
            return {
                "session": session,
                "tasklist": tasklist,
                "active_state": session.get("current_state", 0)
            }
        except FileNotFoundError:
            return {"error": "Not initialized. Run init first."}

    def advance(self, state_id: Optional[int] = None) -> bool:
        """Marks current state complete and advances to next or specified state."""
        session = self._load_session()
        current = session.get("current_state", 0)
        completed = set(session.get("completed_states", []))
        
        target_state = state_id if state_id is not None else current + 1
        
        if target_state not in self.STATES:
            print(f"Error: Invalid target state {target_state}", file=sys.stderr)
            return False

        # Mark current as complete
        completed.add(current)
        
        # Check dependencies for target_state
        deps = self.STATES[target_state]["deps"]
        missing_deps = [dep for dep in deps if dep not in completed]
        if missing_deps:
            print(f"Error: Cannot advance to {target_state}. Missing dependencies: {missing_deps}", file=sys.stderr)
            return False

        session["current_state"] = target_state
        session["completed_states"] = sorted(list(completed))
        self._save_session(session)

        tasklist = self._load_tasklist()
        tasklist[str(current)]["status"] = "completed"
        tasklist[str(target_state)]["status"] = "active"
        self._save_tasklist(tasklist)
        
        print(f"Advanced to State {target_state}: {self.STATES[target_state]['name']}", file=sys.stdout)
        return True

    def verify(self) -> dict:
        """Checks all completed states have their required artifacts."""
        session = self._load_session()
        completed = session.get("completed_states", [])
        
        report = {"verified": True, "issues": []}
        for state_id in completed:
            artifacts = self.STATES[state_id]["artifacts"]
            for artifact in artifacts:
                artifact_path = self.project_root / artifact
                if not artifact_path.exists():
                    report["verified"] = False
                    report["issues"].append(f"State {state_id} missing artifact: {artifact}")
        
        return report

    def get_current_state(self) -> int:
        """Returns current active state number."""
        return self._load_session().get("current_state", 0)

    def is_state_complete(self, state_id: int) -> bool:
        """Check if a specific state is done."""
        return state_id in self._load_session().get("completed_states", [])

    def _load_session(self) -> dict:
        if not self.session_file.exists():
            raise FileNotFoundError("session.json not found")
        with open(self.session_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_session(self, data: dict) -> None:
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _load_tasklist(self) -> dict:
        if not self.tasklist_file.exists():
            raise FileNotFoundError("tasklist.json not found")
        with open(self.tasklist_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_tasklist(self, data: dict) -> None:
        with open(self.tasklist_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)


def cli_main():
    parser = argparse.ArgumentParser(description="Whitepaper State Machine Tracker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--project-root", default=".", help="Project root directory")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--project-root", default=".", help="Project root directory")
    status_parser.add_argument("--json", action="store_true", help="Output as JSON")

    advance_parser = subparsers.add_parser("advance")
    advance_parser.add_argument("--project-root", default=".", help="Project root directory")
    advance_parser.add_argument("--state", type=int, help="Optional state number to advance to")

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--project-root", default=".", help="Project root directory")

    args = parser.parse_args()
    tracker = StateTracker(Path(args.project_root).resolve())

    try:
        if args.command == "init":
            tracker.init()
            sys.exit(0)
            
        elif args.command == "status":
            stat = tracker.status()
            if "error" in stat:
                print(stat["error"], file=sys.stderr)
                sys.exit(1)
            if args.json:
                print(json.dumps(stat, indent=2))
            else:
                print(f"Active State: {stat['active_state']}")
                print(f"Completed States: {stat['session']['completed_states']}")
            sys.exit(0)
            
        elif args.command == "advance":
            success = tracker.advance(args.state)
            sys.exit(0 if success else 1)
            
        elif args.command == "verify":
            report = tracker.verify()
            if report["verified"]:
                print("All verified.", file=sys.stdout)
                sys.exit(0)
            else:
                print("Verification failed:", file=sys.stderr)
                for issue in report["issues"]:
                    print(f" - {issue}", file=sys.stderr)
                sys.exit(1)
                
    except Exception as e:
        print(f"Unhandled error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    cli_main()
