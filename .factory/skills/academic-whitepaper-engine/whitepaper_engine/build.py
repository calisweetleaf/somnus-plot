import argparse
import sys
import subprocess
import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any


class BuildOrchestrator:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()

    def check_dependencies(self) -> dict:
        status = {}
        for tool in ['lualatex', 'biber', 'latexmk', 'pandoc']:
            status[tool] = shutil.which(tool) is not None
        return status

    def build(self, tex_path: Path, output_dir: Path = None) -> dict:
        deps = self.check_dependencies()
        if not deps['lualatex']:
            return {"status": "error", "error": "lualatex not found"}
            
        out_dir_str = str(output_dir) if output_dir else str(tex_path.parent)
        
        if deps['latexmk']:
            cmd = ['latexmk', '-lualatex', '-interaction=nonstopmode', f'-output-directory={out_dir_str}', str(tex_path)]
        else:
            # Fallback
            cmd = ['lualatex', '-interaction=nonstopmode', f'-output-directory={out_dir_str}', str(tex_path)]
            
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=self.project_root)
            
            pdf_path = Path(out_dir_str) / tex_path.with_suffix('.pdf').name
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "warnings": [], # placeholder for actual log parsing
                "errors": [result.stderr] if result.returncode != 0 else [],
                "output_path": str(pdf_path)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def validate_output(self, pdf_path: Path) -> dict:
        if not pdf_path.exists():
            return {"valid": False, "error": f"{pdf_path} does not exist"}
            
        if pdf_path.stat().st_size == 0:
            return {"valid": False, "error": f"{pdf_path} is empty"}
            
        return {"valid": True}

    def generate_manifest(self, source_files: List[Path], output_files: List[Path]) -> dict:
        manifest = {"sources": {}, "outputs": {}}
        
        for f in source_files:
            if f.exists() and f.is_file():
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                manifest["sources"][str(f)] = h
                
        for f in output_files:
            if f.exists() and f.is_file():
                h = hashlib.sha256(f.read_bytes()).hexdigest()
                manifest["outputs"][str(f)] = h
                
        return manifest


def cli_main():
    parser = argparse.ArgumentParser(description="LuaLaTeX + Biber Build Orchestrator")
    parser.add_argument("tex_file", type=str, help="Path to TeX file to build")
    parser.add_argument("--output-dir", type=str, help="Output directory")
    args = parser.parse_args()

    tex_path = Path(args.tex_file)
    out_dir = Path(args.output_dir) if args.output_dir else tex_path.parent
    
    orchestrator = BuildOrchestrator(Path.cwd())
    
    deps = orchestrator.check_dependencies()
    missing = [tool for tool, present in deps.items() if not present and tool in ('lualatex', 'latexmk')]
    if missing:
        print(f"Missing required dependencies: {missing}", file=sys.stderr)
        sys.exit(2)
        
    print(f"Building {tex_path}...", file=sys.stdout)
    res = orchestrator.build(tex_path, out_dir)
    
    if res['status'] == 'error':
        print(f"Build failed: {res.get('error')}", file=sys.stderr)
        sys.exit(1)
        
    if res['status'] == 'failed':
        print("Build command failed.", file=sys.stderr)
        for err in res['errors']:
            print(err, file=sys.stderr)
        sys.exit(1)
        
    pdf_path = Path(res['output_path'])
    val = orchestrator.validate_output(pdf_path)
    
    if not val['valid']:
        print(f"Output validation failed: {val.get('error')}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Successfully built: {pdf_path}", file=sys.stdout)
    sys.exit(0)

if __name__ == '__main__':
    cli_main()
