import sys
import json
import unicodedata
from pathlib import Path
from typing import Dict, List, Any

class UnicodeClassifier:
    DOMAINS = {
        'prose_typography': 'prose_typography',
        'mathematical_symbol': 'mathematical_symbol',
        'semantic_operator': 'semantic_operator',
        'control_invisible': 'control_invisible',
        'disallowed': 'disallowed'
    }

    def __init__(self):
        self.semantic_registry: set = set()

    def load_registry(self, path: Path) -> None:
        """Load project symbol registry for semantic operator classification"""
        if not path.exists():
            return
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.semantic_registry = set(data.get('semantic_operators', []))

    def classify(self, char: str) -> str:
        if len(char) != 1:
            return self.DOMAINS['disallowed']
            
        if char in self.semantic_registry:
            return self.DOMAINS['semantic_operator']
            
        category = unicodedata.category(char)
        
        # Controls
        if category.startswith('C'):
            if char in ('\n', '\t', '\r'):
                return self.DOMAINS['prose_typography']
            return self.DOMAINS['control_invisible']
            
        # Math symbols
        if category == 'Sm' or ('GREEK' in unicodedata.name(char, '')):
            return self.DOMAINS['mathematical_symbol']
            
        # ASCII and basic prose
        if ord(char) < 128:
            return self.DOMAINS['prose_typography']
            
        # Common typographic
        if char in ('“', '”', '‘', '’', '—', '–', '…'):
            return self.DOMAINS['prose_typography']
            
        # Accented chars and basic letters
        if category.startswith('L') or category.startswith('M'):
            return self.DOMAINS['prose_typography']
            
        # Default disallowed for random emojis, homoglyphs, etc.
        return self.DOMAINS['disallowed']

    def classify_text(self, text: str) -> Dict[str, Any]:
        counts = {d: 0 for d in self.DOMAINS.values()}
        locations = {d: [] for d in self.DOMAINS.values()}
        
        for i, char in enumerate(text):
            domain = self.classify(char)
            counts[domain] += 1
            if domain in (self.DOMAINS['control_invisible'], self.DOMAINS['disallowed']):
                locations[domain].append((i, char))
                
        return {
            "counts": counts,
            "locations": locations
        }

    def validate_text(self, text: str) -> List[str]:
        issues = []
        classification = self.classify_text(text)
        
        for idx, char in classification['locations'][self.DOMAINS['control_invisible']]:
            issues.append(f"Control character found at index {idx}: U+{ord(char):04X}")
            
        for idx, char in classification['locations'][self.DOMAINS['disallowed']]:
            name = unicodedata.name(char, 'UNKNOWN')
            issues.append(f"Disallowed character found at index {idx}: '{char}' (U+{ord(char):04X} {name})")
            
        return issues

    def is_prose_safe(self, char: str) -> bool:
        return self.classify(char) == self.DOMAINS['prose_typography']

    def is_math_symbol(self, char: str) -> bool:
        return self.classify(char) == self.DOMAINS['mathematical_symbol']
