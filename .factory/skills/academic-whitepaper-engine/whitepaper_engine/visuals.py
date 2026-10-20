import argparse
import sys
import re
from pathlib import Path
from typing import Dict, List, Any
import yaml


class VisualValidator:
    COLOR_POLICY = {
        'body_text': 'monochrome_only',
        'headings': 'monochrome_only',
        'hyperlinks': 'monochrome_only',
        'equations': 'monochrome_only',
        'code_boxes': 'color_allowed',
        'diagrams': 'color_semantic_only',
        'plots': 'color_semantic_only'
    }
    
    VISUAL_PURPOSES = [
        'topology', 'process', 'comparison', 'measurement', 
        'state_transition', 'mathematical_intuition', 
        'implementation_map', 'chronology', 'failure_analysis'
    ]

    def validate_visual(self, visual: dict) -> List[str]:
        issues = []
        purpose = visual.get('purpose')
        visual_type = visual.get('type')
        
        if purpose not in self.VISUAL_PURPOSES:
            issues.append(f"Invalid visual purpose '{purpose}'. Allowed: {self.VISUAL_PURPOSES}")
            
        if visual_type in self.COLOR_POLICY:
            policy = self.COLOR_POLICY[visual_type]
            color_used = visual.get('color_used', False)
            if policy == 'monochrome_only' and color_used:
                issues.append(f"Visual type '{visual_type}' must be monochrome, but color is used.")
                
        return issues

    def validate_ledger(self, ledger_path: Path) -> dict:
        try:
            with open(ledger_path, 'r', encoding='utf-8') as f:
                ledger = yaml.safe_load(f)
        except Exception as e:
            return {"error": f"Failed to load ledger: {e}"}

        if not isinstance(ledger, list):
            return {"error": "Visual ledger must be a list of visuals"}

        all_issues = {}
        for i, visual in enumerate(ledger):
            v_id = visual.get('id', f"visual_{i}")
            issues = self.validate_visual(visual)
            if issues:
                all_issues[v_id] = issues

        return {
            "valid": len(all_issues) == 0,
            "issues": all_issues
        }

    def check_color_in_tex(self, tex_path: Path) -> List[str]:
        issues = []
        if not tex_path.exists():
            issues.append(f"TeX file not found: {tex_path}")
            return issues
            
        with open(tex_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Very basic scanner: flags \textcolor or \color if not inside allowed environments
        in_allowed_env = False
        allowed_envs = ['lstlisting', 'tikzpicture', 'pgfplots']
        
        for i, line in enumerate(lines):
            for env in allowed_envs:
                if f"\\begin{{{env}}}" in line:
                    in_allowed_env = True
                if f"\\end{{{env}}}" in line:
                    in_allowed_env = False
                    
            if not in_allowed_env:
                if r"\textcolor" in line or r"\color{" in line:
                    issues.append(f"Line {i+1}: Found color command outside allowed environments: {line.strip()}")
                    
        return issues


def cli_main():
    parser = argparse.ArgumentParser(description="Visual Constitution Validator")
    parser.add_argument("file", type=str, help="Path to visual ledger YAML or TeX file")
    args = parser.parse_args()

    validator = VisualValidator()
    target_path = Path(args.file)
    
    if not target_path.exists():
        print(f"Error: {target_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    has_errors = False
    
    if target_path.suffix == '.yaml':
        result = validator.validate_ledger(target_path)
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)
        if not result["valid"]:
            print("Visual ledger has issues:", file=sys.stderr)
            for vid, issues in result["issues"].items():
                print(f"\nVisual {vid}:", file=sys.stderr)
                for issue in issues:
                    print(f" - {issue}", file=sys.stderr)
            has_errors = True
        else:
            print("Visual ledger is valid.", file=sys.stdout)
            
    elif target_path.suffix == '.tex':
        issues = validator.check_color_in_tex(target_path)
        if issues:
            print("TeX file has color policy issues:", file=sys.stderr)
            for issue in issues:
                print(f" - {issue}", file=sys.stderr)
            has_errors = True
        else:
            print("TeX file color policy is valid.", file=sys.stdout)
            
    else:
        print("Error: Unsupported file type. Must be .yaml or .tex", file=sys.stderr)
        sys.exit(1)

    sys.exit(1 if has_errors else 0)


if __name__ == '__main__':
    cli_main()
