import argparse
import sys
from pathlib import Path
from typing import Dict, List, Any
import yaml


class ClaimValidator:
    CLAIM_CLASSES = [
        'implemented', 'observed', 'derived', 'interpretive', 
        'hypothesized', 'planned', 'comparative', 'historical'
    ]
    
    TEMPERATURE_MAP = {
        'implemented': ['cold', 'measured'],
        'observed': ['cold', 'measured'],
        'derived': ['measured'],
        'interpretive': ['measured', 'warm'],
        'hypothesized': ['warm'],
        'planned': ['measured'],
        'comparative': ['measured'],
        'historical': ['cold', 'measured']
    }

    def validate_claim(self, claim: dict) -> List[str]:
        issues = []
        claim_class = claim.get('class')
        text = claim.get('text', '')
        
        if claim_class not in self.CLAIM_CLASSES:
            issues.append(f"Invalid claim class '{claim_class}'. Must be one of {self.CLAIM_CLASSES}")
            return issues
            
        temp_issues = self.validate_temperature(text, claim_class)
        issues.extend(temp_issues)
        
        return issues

    def validate_temperature(self, claim_text: str, claim_class: str) -> List[str]:
        issues = []
        text_lower = claim_text.lower()
        
        # Detect present tense in 'planned' claims (heuristic)
        if claim_class == 'planned':
            present_tense_verbs = ['is', 'are', 'implements', 'does', 'provides']
            if any(verb in text_lower.split() for verb in present_tense_verbs):
                issues.append(f"Planned claim should not use present tense ('implemented' language): {claim_text}")

        # Detect certainty language for 'hypothesized' claims
        if claim_class == 'hypothesized':
            certainty_words = ['definitely', 'certainly', 'proven', 'will', 'must']
            if any(word in text_lower.split() for word in certainty_words):
                issues.append(f"Hypothesized claim uses inappropriate certainty language: {claim_text}")
                
        # Detect superlatives for non-observed/implemented
        if claim_class not in ['observed', 'implemented']:
            superlatives = ['best', 'fastest', 'greatest', 'most', 'perfect', 'ultimate']
            if any(word in text_lower.split() for word in superlatives):
                issues.append(f"Claim class '{claim_class}' uses superlative language: {claim_text}")

        return issues

    def validate_ledger(self, ledger_path: Path) -> dict:
        try:
            with open(ledger_path, 'r', encoding='utf-8') as f:
                ledger = yaml.safe_load(f)
        except Exception as e:
            return {"error": f"Failed to parse ledger: {e}"}

        if not isinstance(ledger, list):
            return {"error": "Ledger must be a list of claims"}

        all_issues = {}
        for i, claim in enumerate(ledger):
            claim_id = claim.get('id', f"claim_{i}")
            issues = self.validate_claim(claim)
            if issues:
                all_issues[claim_id] = issues

        return {
            "valid": len(all_issues) == 0,
            "issues": all_issues
        }


def cli_main():
    parser = argparse.ArgumentParser(description="Claim Epistemology Engine")
    parser.add_argument("ledger", type=str, help="Path to claim ledger YAML file")
    args = parser.parse_args()

    validator = ClaimValidator()
    ledger_path = Path(args.ledger)
    
    if not ledger_path.exists():
        print(f"Error: {ledger_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    result = validator.validate_ledger(ledger_path)
    
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)
        
    if result["valid"]:
        print("Claim ledger is valid.", file=sys.stdout)
        sys.exit(0)
    else:
        print("Claim ledger has issues:", file=sys.stderr)
        for cid, issues in result["issues"].items():
            print(f"\nClaim {cid}:", file=sys.stderr)
            for issue in issues:
                print(f" - {issue}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    cli_main()
