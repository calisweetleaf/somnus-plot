# System Requirements — Academic Whitepaper Engine v4

This document lists all **external system binaries** required by the engine. These are NOT Python packages — they must be installed via your system package manager, TeX distribution, or dedicated installer.

---

## Required Binaries

| Binary | Purpose | Minimum Version | Install Command (Debian/Ubuntu) |
|--------|---------|-----------------|--------------------------------|
| `lualatex` | Canonical TeX engine (Unicode-native) | TeX Live 2023+ | `sudo apt install texlive-luatex` |
| `biber` | Bibliography backend for biblatex | 2.17+ | `sudo apt install biber` |
| `latexmk` | Automated TeX build driver | 4.79+ | `sudo apt install latexmk` |
| `pandoc` | Markdown → TeX AST conversion | 3.1+ | `sudo apt install pandoc` |

## Optional Binaries

| Binary | Purpose | Install Command (Debian/Ubuntu) |
|--------|---------|--------------------------------|
| `graphviz` / `dot` | Dependency graph and structural tree rendering | `sudo apt install graphviz` |
| `pdftotext` | PDF text extraction for render validation | `sudo apt install poppler-utils` |
| `tesseract` | OCR engine for scanned PDF ingestion | `sudo apt install tesseract-ocr` |
| `ffmpeg` | Video metadata stripping (cleaner.py) | `sudo apt install ffmpeg` |
| `mkvpropedit` | MKV metadata editing (cleaner.py) | `sudo apt install mkvtoolnix` |

## Required TeX Packages

The following LaTeX packages must be available in your TeX distribution. All are included in a standard TeX Live full installation:

- `fontspec` — OpenType/TrueType font loading (LuaLaTeX)
- `unicode-math` — Unicode mathematics support
- `microtype` — Microtypographic enhancements
- `geometry` — Page layout
- `setspace` — Line spacing control
- `graphicx` — Image inclusion
- `tikz` — Diagram creation
- `pgfplots` — Data visualization
- `listings` — Code listings
- `xcolor` — Color support
- `booktabs` — Professional tables
- `longtable` — Multi-page tables
- `amsmath`, `amssymb`, `amsthm` — AMS mathematics
- `mathtools` — Enhanced math tools
- `algorithm`, `algpseudocode` — Algorithm typesetting
- `biblatex` — Modern bibliography management
- `hyperref` — PDF hyperlinks and metadata
- `fancyhdr` — Header/footer customization
- `titlesec` — Section title formatting
- `caption` — Caption customization
- `float` — Float placement control
- `mdframed` — Framed environments

## TeX Live Quick Install

For a complete TeX Live installation with all required packages:

```bash
# Full install (recommended, ~5GB)
sudo apt install texlive-full

# Minimal install (requires manual package additions)
sudo apt install texlive-luatex texlive-latex-extra texlive-fonts-extra \
    texlive-bibtex-extra texlive-science biber latexmk
```

## Verification

After installing, run the engine self-check:

```bash
python scripts/check_engine.py
```

This will verify all required binaries and report any missing dependencies.

---

*Last updated: 2026-08-06 (v4 System Requirements)*
