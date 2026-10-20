import argparse
import sys
import re
import math
from pathlib import Path
from typing import Dict, List, Any


class StyleReviewer:
    AI_FINGERPRINT_PHRASES = [
        'Furthermore,', 'Moreover,', 'Delving deeper', 'It is worth noting', 'In conclusion,',
        'This approach', 'Notably,', 'Importantly,', 'In this context,', 'It should be noted',
        'This highlights', 'This underscores', 'This demonstrates', 'plays a crucial role',
        'It is important to note', 'a testament to', 'the intricacies of', 'a comprehensive',
        'a nuanced', 'a holistic', 'delve into', 'tapestry', 'multifaceted', 'leverage',
        'groundbreaking', 'cutting-edge', 'game-changing', 'paradigm shift', 'synergy',
        'This is not merely', 'at the heart of', 'at its core'
    ]

    def _calc_stats(self, lengths: List[int]) -> Dict[str, Any]:
        if not lengths:
            return {"mean": 0.0, "std": 0.0, "min": 0, "max": 0, "uniformity_score": 0.0, "flag_uniformity": False}
        
        n = len(lengths)
        mean = sum(lengths) / n
        variance = sum((x - mean) ** 2 for x in lengths) / n
        std = math.sqrt(variance)
        
        return {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": min(lengths),
            "max": max(lengths),
            "uniformity_score": round(std, 2),
            "flag_uniformity": std < 5.0 and n > 5
        }

    def scan_text(self, text: str) -> dict:
        lines = text.split('\n')
        
        ai_phrases_found = []
        for i, line in enumerate(lines):
            for phrase in self.AI_FINGERPRINT_PHRASES:
                if phrase.lower() in line.lower():
                    ai_phrases_found.append((phrase, i + 1, line.strip()))
                    
        # Basic parsing
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        headings = [line for line in lines if line.strip().startswith('#')]
        
        sentence_lengths = [len(s.split()) for s in sentences]
        paragraph_lengths = [len(p.split()) for p in paragraphs if not p.strip().startswith('#')]
        
        sent_stats = self._calc_stats(sentence_lengths)
        para_stats = self._calc_stats(paragraph_lengths)
        
        heading_count = len(headings)
        para_count = len(paragraph_lengths)
        frag_score = heading_count / para_count if para_count > 0 else 0
        
        overall_risk_score = min(1.0, (len(ai_phrases_found) * 0.1) + (0.2 if sent_stats['flag_uniformity'] else 0.0))
        
        return {
            "ai_phrases_found": ai_phrases_found,
            "sentence_length_stats": sent_stats,
            "paragraph_length_stats": para_stats,
            "generic_transition_count": len(ai_phrases_found), # rough proxy
            "heading_fragmentation_score": round(frag_score, 2),
            "flag_fragmentation": frag_score > 0.3,
            "repeated_patterns": [], # placeholder for more advanced AST NLP
            "overall_risk_score": round(overall_risk_score, 2)
        }

    def scan_file(self, path: Path) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return self.scan_text(f.read())

    def generate_report(self, results: dict) -> str:
        lines = ["=== Style & Anti-Genericity Review Report ==="]
        lines.append(f"Overall Risk Score: {results['overall_risk_score']}/1.0")
        
        if results['ai_phrases_found']:
            lines.append("\n[!] AI Fingerprint Phrases Found:")
            for phrase, ln, ctx in results['ai_phrases_found']:
                lines.append(f"  Line {ln} | '{phrase}' | Context: {ctx[:50]}...")
                
        lines.append("\n--- Metrics ---")
        lines.append(f"Sentence Length: Mean={results['sentence_length_stats']['mean']}, Std={results['sentence_length_stats']['std']}")
        if results['sentence_length_stats']['flag_uniformity']:
            lines.append("  -> [WARNING] Sentences are too uniform in length (Std < 5).")
            
        lines.append(f"Paragraph Length: Mean={results['paragraph_length_stats']['mean']}, Std={results['paragraph_length_stats']['std']}")
        lines.append(f"Heading Fragmentation Score: {results['heading_fragmentation_score']}")
        if results['flag_fragmentation']:
            lines.append("  -> [WARNING] Text is overly fragmented (ratio > 0.3 headings per paragraph).")
            
        return "\n".join(lines)


def cli_main():
    parser = argparse.ArgumentParser(description="Anti-Genericity & AI Voice Scanner")
    parser.add_argument("file", type=str, help="File to scan")
    args = parser.parse_args()

    reviewer = StyleReviewer()
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: {file_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    results = reviewer.scan_file(file_path)
    report = reviewer.generate_report(results)
    
    print(report, file=sys.stdout)
    
    # Exit with 1 if risk score > 0.5
    sys.exit(1 if results['overall_risk_score'] > 0.5 else 0)

if __name__ == '__main__':
    cli_main()
