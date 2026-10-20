#!/usr/bin/env python3
"""Render Markdown through GitHub's own GFM renderer and stage desktop, narrow, and grayscale views.

GitHub's `POST /markdown` endpoint returns the sanitized HTML that GitHub would show, so
this script reports which raw HTML features (inline SVG, `style=` attributes, and similar)
the target renderer dropped. It then writes three review pages per document and, when a
Chrome or Chromium binary is available, screenshots each one.

The wrapper stylesheet only approximates GitHub's typography; the HTML structure is
GitHub's. Mermaid fences are rendered client-side on github.com and appear here as code.
Set GITHUB_TOKEN to raise the anonymous rate limit (60 requests per hour).
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from scripts.check_docs import collect_markdown, visible_lines  # noqa: E402


API_URL = "https://api.github.com/markdown"
TRACKED_TAGS = ("svg", "style", "div", "span", "details", "summary", "picture", "img", "iframe", "script")
STYLE_ATTRIBUTE = re.compile(r"\sstyle\s*=", re.IGNORECASE)
CODE_SPAN = re.compile(r"(`+)(?!`).+?(?<!`)\1")
VIEWS = {
    "desktop": {"width": 1012, "filter": "none"},
    "narrow": {"width": 390, "filter": "none"},
    "grayscale": {"width": 1012, "filter": "grayscale(1)"},
}
BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")
STYLESHEET = """
body { margin: 0; background: #fff; color: #1f2328; }
main { box-sizing: border-box; max-width: %(width)spx; margin: 0 auto; padding: 32px 16px;
  font: 16px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
  overflow-wrap: break-word; }
html { filter: %(filter)s; }
h1, h2 { border-bottom: 1px solid #d1d9e0; padding-bottom: .3em; }
h1, h2, h3, h4, h5, h6 { margin: 24px 0 16px; font-weight: 600; line-height: 1.25; }
a { color: #0969da; }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 85%%; }
code { background: #eff1f3; padding: .2em .4em; border-radius: 6px; }
pre { background: #f6f8fa; padding: 16px; overflow: auto; border-radius: 6px; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; display: block; max-width: 100%%; overflow: auto; }
th, td { border: 1px solid #d1d9e0; padding: 6px 13px; }
blockquote { margin: 0; padding: 0 1em; color: #59636e; border-left: .25em solid #d1d9e0; }
img { max-width: 100%%; }
"""


def render_github(markdown: str, *, context: str | None, token: str | None, timeout: float = 30) -> str:
    """Return GitHub's sanitized HTML for one Markdown document."""
    payload: dict[str, str] = {"text": markdown, "mode": "gfm"}
    if context:
        payload["context"] = context
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(API_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def feature_counts(markup: str) -> dict[str, int]:
    """Count raw HTML features that GitHub may sanitize."""
    counts = {tag: len(re.findall(rf"<\s*{tag}\b", markup, re.IGNORECASE)) for tag in TRACKED_TAGS}
    counts["style="] = len(STYLE_ATTRIBUTE.findall(markup))
    return counts


def dropped_features(markdown: str, rendered: str) -> dict[str, tuple[int, int]]:
    """Return features present in visible source that the renderer removed or reduced."""
    prose = "\n".join(CODE_SPAN.sub("", line) for _, line in visible_lines(markdown))
    source = feature_counts(prose)
    output = feature_counts(rendered)
    return {name: (count, output[name]) for name, count in source.items() if output[name] < count}


def wrap_page(body: str, *, title: str, base: Path, view: str) -> str:
    """Wrap rendered HTML in a review page for one view."""
    style = STYLESHEET % VIEWS[view]
    return (
        "<!doctype html>\n<html><head><meta charset=\"utf-8\">\n"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<base href=\"{html.escape(base.resolve().as_uri())}/\">\n"
        f"<title>{html.escape(title)} ({view})</title>\n<style>{style}</style>\n"
        f"</head><body><main class=\"markdown-body\">\n{body}\n</main></body></html>\n"
    )


def find_browser(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    return next((found for name in BROWSERS if (found := shutil.which(name))), None)


def screenshot(browser: str, page: Path, image: Path, *, width: int, height: int) -> bool:
    command = [
        browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
        "--allow-file-access-from-files", f"--window-size={width},{height}",
        f"--screenshot={image}", page.resolve().as_uri(),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    # Sandboxed browsers (Flatpak, Snap) may exit 0 without access to the page or output path.
    return result.returncode == 0 and image.is_file()


def output_stem(path: Path, root: Path) -> str:
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        relative = Path(path.name)
    return "__".join(relative.with_suffix("").parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", help="Markdown files or directories, relative to --root when not absolute")
    parser.add_argument("--root", default=".", help="repository root for relative input paths")
    parser.add_argument("--output", default="render-check", help="directory for rendered pages and screenshots")
    parser.add_argument("--context", help="owner/repo used by GitHub to resolve issue and user references")
    parser.add_argument("--no-screenshots", action="store_true", help="write HTML views only")
    parser.add_argument("--browser", help="Chrome or Chromium binary for screenshots (auto-detected when omitted)")
    parser.add_argument("--height", type=int, default=2400, help="screenshot viewport height in pixels")
    parser.add_argument("--fail-on-dropped", action="store_true", help="exit 1 when GitHub drops any raw HTML feature")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output).resolve()
    files, findings = collect_markdown(args.paths, root)
    for finding in findings:
        print(finding.render(root), file=sys.stderr)
    if findings:
        return 2
    output.mkdir(parents=True, exist_ok=True)
    browser = None if args.no_screenshots else find_browser(args.browser)
    if not args.no_screenshots and browser is None:
        print("render-check: no Chrome/Chromium found; writing HTML views only", file=sys.stderr)

    token = os.environ.get("GITHUB_TOKEN")
    any_dropped = False
    for path in files:
        markdown = path.read_text(encoding="utf-8")
        try:
            rendered = render_github(markdown, context=args.context, token=token)
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"render-check: GitHub render failed for {path}: {error}", file=sys.stderr)
            return 3
        stem = output_stem(path, root)
        (output / f"{stem}.github.html").write_text(rendered, encoding="utf-8")
        print(f"{path.relative_to(root) if path.is_relative_to(root) else path}")
        dropped = dropped_features(markdown, rendered)
        any_dropped = any_dropped or bool(dropped)
        if dropped:
            summary = ", ".join(f"{name} {before}->{after}" for name, (before, after) in dropped.items())
            print(f"  dropped by GitHub: {summary}")
        else:
            print("  dropped by GitHub: none")
        for view, settings in VIEWS.items():
            page = output / f"{stem}.{view}.html"
            page.write_text(wrap_page(rendered, title=path.name, base=path.parent, view=view), encoding="utf-8")
            line = f"  {view}: {page}"
            if browser:
                image = page.with_suffix(".png")
                if screenshot(browser, page, image, width=settings["width"] + 32, height=args.height):
                    line += f" -> {image}"
                else:
                    line += " (screenshot failed; Flatpak/Snap browsers can only use folders such as ~/Downloads, so retry with --output there)"
            print(line)
    return 1 if args.fail_on_dropped and any_dropped else 0


if __name__ == "__main__":
    sys.exit(main())
