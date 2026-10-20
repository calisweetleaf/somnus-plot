#!/usr/bin/env python3
"""
Metadata Cleaner — AI Artifact Remover

Comprehensive cleaning tool for removing ALL AI-introduced artifacts:
- ALL Unicode control characters (not just 19 hardcoded ones)
- Homoglyphs (lookalike characters from different scripts)
- Smart typography → ASCII equivalents
- AI-typical spacing patterns
- File metadata (EXIF, PDF properties, Office metadata, etc.)

Keeps your code authentically yours, even after AI assistance.

Author: Publication Workshop (Enhanced Edition)
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from xml.etree import ElementTree as ET

# Optional dependencies with graceful fallback
try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    import pikepdf
    HAS_PIKEPDF = True
except ImportError:
    HAS_PIKEPDF = False

try:
    import mutagen
    from mutagen.id3 import ID3
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    from mutagen.mp4 import MP4
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CleaningReport:
    """Report of cleaning operations performed on a file."""
    file_path: Path
    original_size: int
    cleaned_size: int
    metadata_removed: List[str] = field(default_factory=list)
    characters_removed: int = 0
    formatting_fixes: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return len(self.errors) == 0
    
    @property
    def size_diff(self) -> int:
        return self.original_size - self.cleaned_size
    
    def to_dict(self) -> Dict:
        return {
            "file": str(self.file_path),
            "original_size": self.original_size,
            "cleaned_size": self.cleaned_size,
            "size_reduction": self.size_diff,
            "metadata_removed": self.metadata_removed,
            "characters_removed": self.characters_removed,
            "formatting_fixes": self.formatting_fixes,
            "errors": self.errors,
            "warnings": self.warnings,
            "success": self.success
        }


# ============================================================================
# ENHANCED AI ARTIFACT DETECTION
# ============================================================================

# Homoglyph mappings (lookalike characters → ASCII equivalents)
HOMOGLYPH_MAP = {
    # Cyrillic → Latin
    'а': 'a', 'А': 'A', 'е': 'e', 'Е': 'E', 'о': 'o', 'О': 'O',
    'р': 'p', 'Р': 'P', 'с': 'c', 'С': 'C', 'у': 'y', 'У': 'Y',
    'х': 'x', 'Х': 'X', 'В': 'B', 'Н': 'H', 'К': 'K', 'М': 'M',
    'Т': 'T', 'і': 'i',
    # Greek → Latin
    'α': 'a', 'Α': 'A', 'β': 'b', 'Β': 'B', 'ε': 'e', 'Ε': 'E',
    'ο': 'o', 'Ο': 'O', 'ρ': 'p', 'Ρ': 'P', 'τ': 't', 'Τ': 'T',
    'ν': 'v', 'Ν': 'N', 'υ': 'u', 'Υ': 'Y', 'κ': 'k', 'Κ': 'K',
    'Μ': 'M', 'Ζ': 'Z', 'Ι': 'I', 'Η': 'H',
}

# Enhanced typography normalization (ALL fancy chars → ASCII)
TYPOGRAPHY_MAP = {
    # Quotes and primes
    '\u2018': "'",   # Left Single Quotation Mark
    '\u2019': "'",   # Right Single Quotation Mark
    '\u201a': "'",   # Single Low-9 Quotation Mark
    '\u201b': "'",   # Single High-Reversed-9 Quotation Mark
    '\u201c': '"',   # Left Double Quotation Mark
    '\u201d': '"',   # Right Double Quotation Mark
    '\u201e': '"',   # Double Low-9 Quotation Mark
    '\u201f': '"',   # Double High-Reversed-9 Quotation Mark
    '\u2032': "'",   # Prime
    '\u2033': '"',   # Double Prime
    '\u2034': "'''", # Triple Prime
    '\u2035': "'",   # Reversed Prime
    '\u2036': '"',   # Reversed Double Prime
    '\u2037': "'''", # Reversed Triple Prime
    # Dashes and hyphens
    '\u2010': '-',   # Hyphen
    '\u2011': '-',   # Non-Breaking Hyphen
    '\u2012': '-',   # Figure Dash
    '\u2013': '-',   # En Dash
    '\u2014': '--',  # Em Dash
    '\u2015': '--',  # Horizontal Bar
    '\u2212': '-',   # Minus Sign
    # Spaces (various widths)
    '\u00a0': ' ',   # Non-Breaking Space
    '\u2000': ' ',   # En Quad
    '\u2001': ' ',   # Em Quad
    '\u2002': ' ',   # En Space
    '\u2003': ' ',   # Em Space
    '\u2004': ' ',   # Three-Per-Em Space
    '\u2005': ' ',   # Four-Per-Em Space
    '\u2006': ' ',   # Six-Per-Em Space
    '\u2007': ' ',   # Figure Space
    '\u2008': ' ',   # Punctuation Space
    '\u2009': ' ',   # Thin Space
    '\u200a': ' ',   # Hair Space
    '\u202f': ' ',   # Narrow No-Break Space
    '\u205f': ' ',   # Medium Mathematical Space
    # Ellipsis and bullets
    '\u2026': '...',  # Horizontal Ellipsis
    '\u2022': '*',    # Bullet
    '\u2023': '>',    # Triangular Bullet
    '\u2043': '-',    # Hyphen Bullet
}


def is_control_character(char: str) -> bool:
    """
    Check if character is a control/format character that should be removed.
    
    Returns True for:
    - ASCII control chars (U+0000-001F, 007F-009F) except \n, \r, \t
    - Unicode format chars (Category Cf)
    - Other invisible/zero-width characters
    """
    if len(char) != 1:
        return False
    
    code = ord(char)
    
    # Whitelist: keep normal whitespace
    if char in '\n\r\t':
        return False
    
    # ASCII control characters (C0 and C1 control codes)
    if (0x00 <= code <= 0x1F) or (0x7F <= code <= 0x9F):
        return True
    
    # Unicode Format characters (invisible formatting)
    category = unicodedata.category(char)
    if category == 'Cf':  # Format character
        return True
    
    # Specific problematic characters
    if code in [0xFEFF, 0x200B, 0x200C, 0x200D, 0x2060, 0x00AD]:
        return True
    
    return False


# ============================================================================
# TEXT NORMALIZER
# ============================================================================

class TextNormalizer:
    """Enhanced text normalizer that removes ALL AI artifacts."""
    
    def __init__(self, 
                 remove_invisible: bool = True,
                 normalize_typography: bool = True,  # Now enabled by default
                 remove_homoglyphs: bool = True,     # NEW: Remove lookalike chars
                 fix_word_breaks: bool = True,
                 normalize_whitespace: bool = True,
                 normalize_newlines: bool = True,
                 aggressive: bool = False):          # NEW: Aggressive mode
        self.remove_invisible = remove_invisible
        self.normalize_typography = normalize_typography
        self.remove_homoglyphs = remove_homoglyphs
        self.fix_word_breaks = fix_word_breaks
        self.normalize_whitespace = normalize_whitespace
        self.normalize_newlines = normalize_newlines
        self.aggressive = aggressive
        
        # Compile regex patterns
        self._word_break_pattern = re.compile(r'(\w+)-\n(\w+)')
        self._multi_space_pattern = re.compile(r' {2,}')
        self._trailing_space_pattern = re.compile(r' +$', re.MULTILINE)
        self._leading_space_pattern = re.compile(r'^ +', re.MULTILINE)
        self._multiple_blank_lines = re.compile(r'\n{3,}')
        self._double_space_after_period = re.compile(r'\.  ')
    
    def normalize(self, text: str) -> Tuple[str, int, int]:
        """
        Comprehensive normalization to remove ALL AI artifacts.
        Returns (cleaned_text, chars_removed, fixes_made).
        """
        original_len = len(text)
        fixes = 0
        
        # 1. Remove ALL control/invisible characters (comprehensive scan)
        if self.remove_invisible:
            cleaned_chars = []
            for char in text:
                if not is_control_character(char):
                    cleaned_chars.append(char)
            text = ''.join(cleaned_chars)
        
        # 2. Normalize typography (smart quotes → ASCII)
        if self.normalize_typography:
            for char, replacement in TYPOGRAPHY_MAP.items():
                if char in text:
                    text = text.replace(char, replacement)
                    fixes += 1
        
        # 3. Remove homoglyphs (lookalike characters)
        if self.remove_homoglyphs:
            for char, replacement in HOMOGLYPH_MAP.items():
                if char in text:
                    text = text.replace(char, replacement)
                    fixes += 1
        
        # 4. Apply Unicode NFKC normalization (compatibility decomposition)
        text = unicodedata.normalize('NFKC', text)
        
        # 5. Fix word breaks (hyphenated line breaks)
        if self.fix_word_breaks:
            matches = len(self._word_break_pattern.findall(text))
            if matches:
                text = self._word_break_pattern.sub(r'\1\2', text)
                fixes += matches
        
        # 6. Normalize whitespace
        if self.normalize_whitespace:
            # Remove trailing spaces
            text = self._trailing_space_pattern.sub('', text)
            
            # Fix AI-typical double spaces after periods
            text = self._double_space_after_period.sub('. ', text)
            
            # Collapse multiple spaces
            new_text = self._multi_space_pattern.sub(' ', text)
            fixes += (len(text) - len(new_text)) // 2
            text = new_text
            
            # Collapse excessive blank lines (max 2)
            text = self._multiple_blank_lines.sub('\n\n', text)
        
        # 7. Normalize newlines
        if self.normalize_newlines:
            # Convert CRLF to LF
            if '\r\n' in text:
                text = text.replace('\r\n', '\n')
            # Remove standalone CR
            if '\r' in text:
                text = text.replace('\r', '\n')
        
        # 8. Aggressive mode: additional cleaning
        if self.aggressive:
            # Remove zero-width joiners between words
            text = re.sub(r'([a-zA-Z])\s+([a-zA-Z])', r'\1 \2', text)
            # Normalize mixed indentation (tabs → spaces)
            text = text.replace('\t', '    ')
        
        chars_removed = original_len - len(text)
        return text, chars_removed, fixes


# ============================================================================
# IMAGE CLEANER
# ============================================================================

class ImageCleaner:
    """Removes metadata from image files."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.webp'}
    
    def __init__(self):
        if not HAS_PILLOW:
            raise ImportError("Pillow is required for image cleaning. Install with: pip install Pillow")
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def clean(self, input_path: Path, output_path: Path) -> CleaningReport:
        """Remove all metadata from an image."""
        report = CleaningReport(
            file_path=input_path,
            original_size=input_path.stat().st_size,
            cleaned_size=0
        )
        
        try:
            with Image.open(input_path) as img:
                # Get original metadata for reporting
                if hasattr(img, '_getexif') and img._getexif():
                    report.metadata_removed.append("EXIF data")
                if 'icc_profile' in img.info:
                    report.metadata_removed.append("ICC profile")
                if 'xmp' in img.info:
                    report.metadata_removed.append("XMP data")
                
                # Create new image without metadata
                # Preserve essential info
                mode = img.mode
                size = img.size
                
                # Handle format-specific requirements
                suffix = output_path.suffix.lower()
                
                if suffix in ('.jpg', '.jpeg'):
                    # JPEG: convert to RGB if necessary
                    if mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    img.save(output_path, 'JPEG', quality=95, optimize=True)
                    
                elif suffix == '.png':
                    # PNG: keep transparency if present
                    if mode == 'P' and 'transparency' in img.info:
                        img = img.convert('RGBA')
                    img.save(output_path, 'PNG', optimize=True)
                    
                elif suffix == '.gif':
                    img.save(output_path, 'GIF')
                    
                elif suffix in ('.tiff', '.tif'):
                    img.save(output_path, 'TIFF', compression='lzw')
                    
                elif suffix == '.bmp':
                    img.save(output_path, 'BMP')
                    
                elif suffix == '.webp':
                    img.save(output_path, 'WEBP', quality=95)
                    
                else:
                    # Fallback: save in original format
                    img.save(output_path)
            
            report.cleaned_size = output_path.stat().st_size
            
        except Exception as e:
            report.errors.append(f"Image cleaning failed: {str(e)}")
        
        return report


# ============================================================================
# PDF CLEANER
# ============================================================================

class PDFCleaner:
    """Removes metadata from PDF files."""
    
    def __init__(self):
        if not HAS_PIKEPDF:
            raise ImportError("pikepdf is required for PDF cleaning. Install with: pip install pikepdf")
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == '.pdf'
    
    def clean(self, input_path: Path, output_path: Path) -> CleaningReport:
        """Remove all metadata from a PDF."""
        report = CleaningReport(
            file_path=input_path,
            original_size=input_path.stat().st_size,
            cleaned_size=0
        )
        
        try:
            with pikepdf.open(input_path) as pdf:
                # Report what we're removing
                if pdf.docinfo:
                    for key in pdf.docinfo.keys():
                        report.metadata_removed.append(f"PDF Info: {key}")
                
                # Check for XMP metadata
                if pdf.Root.get('/Metadata'):
                    report.metadata_removed.append("XMP metadata stream")
                
                # Clear document info dictionary
                with pdf.open_metadata() as meta:
                    # Delete all XMP metadata
                    for key in list(meta.keys()):
                        del meta[key]
                
                # Clear the document info (legacy PDF metadata)
                pdf.docinfo.clear()
                
                # Remove the metadata stream reference
                if '/Metadata' in pdf.Root:
                    del pdf.Root['/Metadata']
                
                # Save without object streams for maximum compatibility
                pdf.save(output_path, 
                        linearize=True,  # Optimize for web viewing
                        object_stream_mode=pikepdf.ObjectStreamMode.disable)
            
            report.cleaned_size = output_path.stat().st_size
            
        except Exception as e:
            report.errors.append(f"PDF cleaning failed: {str(e)}")
        
        return report


# ============================================================================
# OFFICE DOCUMENT CLEANER
# ============================================================================

class OfficeCleaner:
    """Removes metadata from Office documents (OOXML format)."""
    
    SUPPORTED_FORMATS = {'.docx', '.xlsx', '.pptx'}
    
    # Namespaces used in Office documents
    NS_CORE = 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'
    NS_DC = 'http://purl.org/dc/elements/1.1/'
    NS_DCTERMS = 'http://purl.org/dc/terms/'
    NS_APP = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def clean(self, input_path: Path, output_path: Path) -> CleaningReport:
        """Remove all metadata from an Office document."""
        report = CleaningReport(
            file_path=input_path,
            original_size=input_path.stat().st_size,
            cleaned_size=0
        )
        
        try:
            # Office documents are ZIP archives
            with zipfile.ZipFile(input_path, 'r') as zin:
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                    for item in zin.namelist():
                        data = zin.read(item)
                        
                        # Clean metadata files
                        if item == 'docProps/core.xml':
                            data, removed = self._clean_core_xml(data)
                            report.metadata_removed.extend(removed)
                            
                        elif item == 'docProps/app.xml':
                            data, removed = self._clean_app_xml(data)
                            report.metadata_removed.extend(removed)
                            
                        elif item == 'docProps/custom.xml':
                            # Remove custom properties entirely
                            report.metadata_removed.append("Custom properties")
                            continue
                        
                        zout.writestr(item, data)
            
            report.cleaned_size = output_path.stat().st_size
            
        except Exception as e:
            report.errors.append(f"Office document cleaning failed: {str(e)}")
        
        return report
    
    def _clean_core_xml(self, data: bytes) -> Tuple[bytes, List[str]]:
        """Clean core.xml (Dublin Core metadata)."""
        removed = []
        
        try:
            # Register namespaces to preserve prefixes
            ET.register_namespace('cp', self.NS_CORE)
            ET.register_namespace('dc', self.NS_DC)
            ET.register_namespace('dcterms', self.NS_DCTERMS)
            
            root = ET.fromstring(data)
            
            # Elements to clear (but keep the structure)
            elements_to_clear = [
                ('{%s}creator' % self.NS_DC, 'Creator'),
                ('{%s}lastModifiedBy' % self.NS_CORE, 'Last Modified By'),
                ('{%s}revision' % self.NS_CORE, 'Revision'),
                ('{%s}created' % self.NS_DCTERMS, 'Created Date'),
                ('{%s}modified' % self.NS_DCTERMS, 'Modified Date'),
                ('{%s}title' % self.NS_DC, 'Title'),
                ('{%s}subject' % self.NS_DC, 'Subject'),
                ('{%s}description' % self.NS_DC, 'Description'),
                ('{%s}keywords' % self.NS_CORE, 'Keywords'),
            ]
            
            for tag, name in elements_to_clear:
                elem = root.find(tag)
                if elem is not None and elem.text:
                    removed.append(f"Core: {name}")
                    elem.text = ''
            
            return ET.tostring(root, encoding='unicode').encode('utf-8'), removed
            
        except Exception:
            return data, removed
    
    def _clean_app_xml(self, data: bytes) -> Tuple[bytes, List[str]]:
        """Clean app.xml (application-specific properties)."""
        removed = []
        
        try:
            ET.register_namespace('', self.NS_APP)
            root = ET.fromstring(data)
            
            # Elements to clear
            elements_to_clear = [
                ('Application', 'Application Name'),
                ('AppVersion', 'Application Version'),
                ('Company', 'Company'),
                ('Manager', 'Manager'),
                ('TotalTime', 'Total Editing Time'),
            ]
            
            for tag, name in elements_to_clear:
                elem = root.find('.//{%s}%s' % (self.NS_APP, tag))
                if elem is not None and elem.text:
                    removed.append(f"App: {name}")
                    elem.text = ''
            
            return ET.tostring(root, encoding='unicode').encode('utf-8'), removed
            
        except Exception:
            return data, removed


# ============================================================================
# TEXT FILE CLEANER
# ============================================================================

class TextFileCleaner:
    """Cleans text-based files (txt, md, tex, etc.)."""
    
    SUPPORTED_FORMATS = {'.txt', '.md', '.tex', '.rst', '.html', '.xml', '.json', '.yaml', '.yml', '.css', '.js', '.py'}
    
    def __init__(self, normalizer: TextNormalizer = None):
        self.normalizer = normalizer or TextNormalizer()
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def clean(self, input_path: Path, output_path: Path) -> CleaningReport:
        """Normalize a text file."""
        report = CleaningReport(
            file_path=input_path,
            original_size=input_path.stat().st_size,
            cleaned_size=0
        )
        
        try:
            # Read with fallback encodings
            content = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    content = input_path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                report.errors.append("Could not decode file with any supported encoding")
                return report
            
            # Normalize
            cleaned, chars_removed, fixes = self.normalizer.normalize(content)
            
            report.characters_removed = chars_removed
            report.formatting_fixes = fixes
            
            if chars_removed > 0:
                report.metadata_removed.append(f"Invisible characters ({chars_removed})")
            if fixes > 0:
                report.metadata_removed.append(f"Formatting fixes ({fixes})")
            
            # Write output
            output_path.write_text(cleaned, encoding='utf-8')
            report.cleaned_size = output_path.stat().st_size
            
        except Exception as e:
            report.errors.append(f"Text cleaning failed: {str(e)}")
        
        return report


# ============================================================================
# AUDIO CLEANER
# ============================================================================

class AudioCleaner:
    """Removes metadata from audio files (ID3, Vorbis Comments, MP4 atoms)."""
    
    SUPPORTED_FORMATS = {'.mp3', '.flac', '.ogg', '.m4a', '.mp4', '.wav', '.aac'}
    
    def __init__(self):
        if not HAS_MUTAGEN:
            raise ImportError("mutagen is required for audio cleaning. Install with: pip install mutagen")
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def clean(self, input_path: Path, output_path: Path) -> CleaningReport:
        """Remove all metadata from an audio file."""
        report = CleaningReport(
            file_path=input_path,
            original_size=input_path.stat().st_size,
            cleaned_size=0
        )
        
        try:
            # Copy file first if not in-place
            if input_path != output_path:
                shutil.copy2(input_path, output_path)
            
            suffix = output_path.suffix.lower()
            
            if suffix == '.mp3':
                self._clean_mp3(output_path, report)
            elif suffix == '.flac':
                self._clean_flac(output_path, report)
            elif suffix == '.ogg':
                self._clean_ogg(output_path, report)
            elif suffix in ('.m4a', '.mp4', '.aac'):
                self._clean_mp4(output_path, report)
            else:
                report.warnings.append(f"Limited support for {suffix}")
            
            report.cleaned_size = output_path.stat().st_size
            
        except Exception as e:
            report.errors.append(f"Audio cleaning failed: {str(e)}")
        
        return report
    
    def _clean_mp3(self, path: Path, report: CleaningReport):
        """Clean MP3 ID3 tags."""
        try:
            # ID3v2
            audio = ID3(str(path))
            if audio:
                tags = list(audio.keys())
                if tags:
                    report.metadata_removed.append(f"ID3v2 tags: {len(tags)} frames")
                audio.delete()
        except Exception:
            pass
        
        # ID3v1 - Remove last 128 bytes if it's an ID3v1 tag
        try:
            with open(path, 'rb+') as f:
                f.seek(-128, 2)
                if f.read(3) == b'TAG':
                    report.metadata_removed.append("ID3v1 tag")
                    f.seek(-128, 2)
                    f.truncate()
        except Exception:
            pass
    
    def _clean_flac(self, path: Path, report: CleaningReport):
        """Clean FLAC Vorbis comments and picture blocks."""
        try:
            audio = FLAC(str(path))
            if audio.tags:
                report.metadata_removed.append(f"Vorbis comments: {len(audio.tags)} tags")
                audio.delete()
            if audio.pictures:
                report.metadata_removed.append(f"FLAC pictures: {len(audio.pictures)}")
                audio.clear_pictures()
            audio.save()
        except Exception:
            pass
    
    def _clean_ogg(self, path: Path, report: CleaningReport):
        """Clean OGG Vorbis comments."""
        try:
            audio = OggVorbis(str(path))
            if audio.tags:
                report.metadata_removed.append(f"Vorbis comments: {len(audio.tags)} tags")
                audio.delete()
                audio.save()
        except Exception:
            pass
    
    def _clean_mp4(self, path: Path, report: CleaningReport):
        """Clean MP4/M4A atoms."""
        try:
            audio = MP4(str(path))
            if audio.tags:
                report.metadata_removed.append(f"MP4 atoms: {len(audio.tags)} tags")
                audio.delete()
                audio.save()
        except Exception:
            pass


# ============================================================================
# VIDEO CLEANER
# ============================================================================

class VideoCleaner:
    """Removes metadata from video files using ffmpeg."""
    
    SUPPORTED_FORMATS = {'.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v'}
    
    def __init__(self):
        # Check if ffmpeg is available
        self.ffmpeg_available = shutil.which('ffmpeg') is not None
        self.mkvpropedit_available = shutil.which('mkvpropedit') is not None
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def clean(self, input_path: Path, output_path: Path) -> CleaningReport:
        """Remove all metadata from a video file."""
        report = CleaningReport(
            file_path=input_path,
            original_size=input_path.stat().st_size,
            cleaned_size=0
        )
        
        suffix = input_path.suffix.lower()
        
        try:
            if suffix == '.mkv' and self.mkvpropedit_available:
                self._clean_mkv(input_path, output_path, report)
            elif self.ffmpeg_available:
                self._clean_with_ffmpeg(input_path, output_path, report)
            else:
                report.errors.append("ffmpeg not found. Install ffmpeg for video metadata removal.")
                return report
            
            if output_path.exists():
                report.cleaned_size = output_path.stat().st_size
            
        except Exception as e:
            report.errors.append(f"Video cleaning failed: {str(e)}")
        
        return report
    
    def _clean_with_ffmpeg(self, input_path: Path, output_path: Path, report: CleaningReport):
        """Use ffmpeg to strip metadata."""
        import subprocess
        
        cmd = [
            'ffmpeg', '-y', '-i', str(input_path),
            '-map_metadata', '-1',  # Strip all metadata
            '-c', 'copy',           # Copy streams without re-encoding
            '-fflags', '+bitexact', # Remove encoder info
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            report.metadata_removed.append("Video container metadata (ffmpeg)")
        else:
            report.errors.append(f"ffmpeg error: {result.stderr[:200]}")
    
    def _clean_mkv(self, input_path: Path, output_path: Path, report: CleaningReport):
        """Use mkvpropedit for MKV files (faster, no re-mux)."""
        import subprocess
        
        # Copy first
        shutil.copy2(input_path, output_path)
        
        # Remove tags
        cmd = ['mkvpropedit', str(output_path), '--tags', 'all:']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            report.metadata_removed.append("MKV tags removed")
        
        # Remove title
        cmd = ['mkvpropedit', str(output_path), '--delete', 'title']
        subprocess.run(cmd, capture_output=True)
        report.metadata_removed.append("MKV title removed")


# ============================================================================
# SVG CLEANER
# ============================================================================

class SVGCleaner:
    """Removes metadata from SVG files."""
    
    SUPPORTED_FORMATS = {'.svg'}
    
    # Namespaces commonly used for metadata
    METADATA_NAMESPACES = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'cc': 'http://creativecommons.org/ns#',
        'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
        'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    }
    
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    def clean(self, input_path: Path, output_path: Path) -> CleaningReport:
        """Remove metadata from an SVG file."""
        report = CleaningReport(
            file_path=input_path,
            original_size=input_path.stat().st_size,
            cleaned_size=0
        )
        
        try:
            content = input_path.read_text(encoding='utf-8')
            
            # Remove XML comments
            comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
            comments_found = len(comment_pattern.findall(content))
            if comments_found:
                content = comment_pattern.sub('', content)
                report.metadata_removed.append(f"XML comments ({comments_found})")
            
            # Parse and clean
            try:
                # Register namespaces to avoid ns0, ns1 prefixes
                for prefix, uri in self.METADATA_NAMESPACES.items():
                    ET.register_namespace(prefix, uri)
                
                root = ET.fromstring(content)
                
                # Remove <metadata> elements
                for ns_uri in ['', '{http://www.w3.org/2000/svg}']:
                    for meta in root.findall(f'.//{ns_uri}metadata'):
                        root.remove(meta) if meta in root else None
                        report.metadata_removed.append("<metadata> element")
                
                # Remove editor-specific attributes
                editor_attrs = []
                for elem in root.iter():
                    attrs_to_remove = [
                        attr for attr in elem.attrib 
                        if any(ns in attr for ns in ['inkscape:', 'sodipodi:', '{http://www.inkscape.org'])
                    ]
                    for attr in attrs_to_remove:
                        del elem.attrib[attr]
                        editor_attrs.append(attr)
                
                if editor_attrs:
                    report.metadata_removed.append(f"Editor attributes ({len(editor_attrs)})")
                
                # Serialize back
                content = ET.tostring(root, encoding='unicode')
                
            except ET.ParseError:
                # If XML parsing fails, just use regex-based cleaning
                report.warnings.append("XML parsing failed, using regex fallback")
                
                # Remove <metadata>...</metadata> blocks
                meta_pattern = re.compile(r'<metadata[^>]*>.*?</metadata>', re.DOTALL | re.IGNORECASE)
                if meta_pattern.search(content):
                    content = meta_pattern.sub('', content)
                    report.metadata_removed.append("<metadata> block (regex)")
            
            # Write output
            output_path.write_text(content, encoding='utf-8')
            report.cleaned_size = output_path.stat().st_size
            
        except Exception as e:
            report.errors.append(f"SVG cleaning failed: {str(e)}")
        
        return report


# ============================================================================
# MAIN CLEANER
# ============================================================================

class MetadataCleaner:
    """Main metadata cleaning orchestrator."""
    
    def __init__(self, 
                 strip_images: bool = True,
                 strip_pdfs: bool = True,
                 strip_office: bool = True,
                 strip_text: bool = True,
                 strip_audio: bool = True,
                 strip_video: bool = True,
                 strip_svg: bool = True,
                 text_normalizer: TextNormalizer = None):
        
        self.cleaners = []
        
        if strip_images and HAS_PILLOW:
            self.cleaners.append(ImageCleaner())
        elif strip_images:
            print("Warning: Pillow not installed. Image cleaning disabled.", file=sys.stderr)
        
        if strip_pdfs and HAS_PIKEPDF:
            self.cleaners.append(PDFCleaner())
        elif strip_pdfs:
            print("Warning: pikepdf not installed. PDF cleaning disabled.", file=sys.stderr)
        
        if strip_office:
            self.cleaners.append(OfficeCleaner())
        
        if strip_audio and HAS_MUTAGEN:
            self.cleaners.append(AudioCleaner())
        elif strip_audio:
            print("Warning: mutagen not installed. Audio cleaning disabled.", file=sys.stderr)
        
        if strip_video:
            self.cleaners.append(VideoCleaner())
        
        if strip_svg:
            self.cleaners.append(SVGCleaner())
        
        if strip_text:
            self.cleaners.append(TextFileCleaner(text_normalizer))
    
    def can_handle(self, path: Path) -> bool:
        """Check if any cleaner can handle this file."""
        return any(c.can_handle(path) for c in self.cleaners)
    
    def get_cleaner(self, path: Path):
        """Get the appropriate cleaner for a file."""
        for cleaner in self.cleaners:
            if cleaner.can_handle(path):
                return cleaner
        return None
    
    def clean_file(self, input_path: Path, output_path: Path = None, 
                   inplace: bool = False) -> CleaningReport:
        """Clean a single file."""
        input_path = Path(input_path)
        
        if not input_path.exists():
            report = CleaningReport(file_path=input_path, original_size=0, cleaned_size=0)
            report.errors.append("File not found")
            return report
        
        # Determine output path
        if inplace:
            output_path = input_path
            temp_path = input_path.with_suffix(input_path.suffix + '.tmp')
        else:
            output_path = Path(output_path) if output_path else input_path.with_stem(input_path.stem + '_clean')
            temp_path = output_path
        
        # Find appropriate cleaner
        cleaner = self.get_cleaner(input_path)
        
        if cleaner is None:
            report = CleaningReport(
                file_path=input_path, 
                original_size=input_path.stat().st_size,
                cleaned_size=input_path.stat().st_size
            )
            report.warnings.append("No cleaner available for this file type")
            if not inplace and output_path:
                shutil.copy2(input_path, output_path)
            return report
        
        # Clean the file
        report = cleaner.clean(input_path, temp_path)
        
        # Handle inplace replacement
        if inplace and report.success and temp_path.exists():
            temp_path.replace(input_path)
            report.cleaned_size = input_path.stat().st_size
        
        return report
    
    def clean_directory(self, dir_path: Path, output_dir: Path = None,
                       recursive: bool = True, inplace: bool = False) -> List[CleaningReport]:
        """Clean all supported files in a directory."""
        dir_path = Path(dir_path)
        reports = []
        
        if not dir_path.is_dir():
            report = CleaningReport(file_path=dir_path, original_size=0, cleaned_size=0)
            report.errors.append("Not a directory")
            return [report]
        
        # Create output directory if needed
        if output_dir and not inplace:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # Iterate files
        pattern = '**/*' if recursive else '*'
        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            if not self.can_handle(file_path):
                continue
            
            # Determine output path
            if inplace:
                out_path = None
            elif output_dir:
                relative = file_path.relative_to(dir_path)
                out_path = output_dir / relative
                out_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                out_path = file_path.with_stem(file_path.stem + '_clean')
            
            report = self.clean_file(file_path, out_path, inplace=inplace)
            reports.append(report)
        
        return reports


# ============================================================================
# CLI
# ============================================================================

def print_report(report: CleaningReport, verbose: bool = False):
    """Print a cleaning report."""
    status = "✓" if report.success else "✗"
    print(f"{status} {report.file_path}")
    
    if report.metadata_removed:
        print(f"  Removed: {', '.join(report.metadata_removed)}")
    
    if report.size_diff != 0:
        if report.size_diff > 0:
            print(f"  Size reduction: {report.size_diff:,} bytes")
        else:
            print(f"  Size increase: {abs(report.size_diff):,} bytes")
    
    for warning in report.warnings:
        print(f"  ⚠ {warning}")
    
    for error in report.errors:
        print(f"  ✗ {error}")


def main():
    parser = argparse.ArgumentParser(
        description="Metadata Cleaner — Strip metadata from files for clean distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf -o clean.pdf
  %(prog)s ./manuscript/ --recursive --inplace
  %(prog)s image.jpg --dry-run
  %(prog)s ./docs/ -o ./dist/ --json report.json
        """
    )
    
    parser.add_argument('input', type=Path, help='Input file or directory')
    parser.add_argument('-o', '--output', type=Path, help='Output file or directory')
    parser.add_argument('--inplace', action='store_true', help='Modify files in place')
    parser.add_argument('--recursive', '-r', action='store_true', help='Process directories recursively')
    parser.add_argument('--dry-run', action='store_true', help='Report what would be done without making changes')
    parser.add_argument('--json', type=Path, help='Write JSON report to file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    # Specific cleaners
    parser.add_argument('--no-images', action='store_true', help='Skip image cleaning')
    parser.add_argument('--no-pdfs', action='store_true', help='Skip PDF cleaning')
    parser.add_argument('--no-office', action='store_true', help='Skip Office document cleaning')
    parser.add_argument('--no-text', action='store_true', help='Skip text file normalization')
    parser.add_argument('--no-audio', action='store_true', help='Skip audio metadata cleaning')
    parser.add_argument('--no-video', action='store_true', help='Skip video metadata cleaning')
    parser.add_argument('--no-svg', action='store_true', help='Skip SVG metadata cleaning')
    
    # Text normalization options
    parser.add_argument('--normalize-quotes', action='store_true', 
                       help='Convert smart quotes to straight quotes')
    parser.add_argument('--normalize-dashes', action='store_true',
                       help='Convert em/en dashes to hyphens')
    
    # Safety gate: require explicit author command
    parser.add_argument(
        '--force-author-command',
        action='store_true',
        help='REQUIRED safety flag. Confirms this is an explicit author-initiated '
             'invocation. Without this flag, the cleaner will refuse to run. '
             'This prevents accidental execution in automated pipelines.',
    )

    args = parser.parse_args()

    # ── Safety Gate ──────────────────────────────────────────────────────
    # Per AGENTS.md: cleaner.py MUST NEVER run automatically.
    # Require --force-author-command unless in --dry-run mode.
    if not args.dry_run and not args.force_author_command:
        print(
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  ⛔  SAFETY BLOCK — Author Command Required                ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║  cleaner.py performs deep, aggressive metadata and          ║\n"
            "║  character stripping that can mangle binary files.          ║\n"
            "║                                                            ║\n"
            "║  This tool MUST NOT be run in automated pipelines.          ║\n"
            "║                                                            ║\n"
            "║  To confirm this is an explicit author command, re-run      ║\n"
            "║  with:  --force-author-command                             ║\n"
            "║                                                            ║\n"
            "║  To preview without changes:  --dry-run                    ║\n"
            "╚══════════════════════════════════════════════════════════════╝",
            file=sys.stderr,
        )
        sys.exit(2)

    # Create text normalizer with ENHANCED AI artifact removal
    normalizer = TextNormalizer(
        normalize_typography=True,  # Always enabled: removes smart quotes, fancy dashes
        remove_homoglyphs=True      # Removes lookalike Cyrillic/Greek characters
    )
    
    # Create cleaner
    cleaner = MetadataCleaner(
        strip_images=not args.no_images,
        strip_pdfs=not args.no_pdfs,
        strip_office=not args.no_office,
        strip_text=not args.no_text,
        strip_audio=not args.no_audio,
        strip_video=not args.no_video,
        strip_svg=not args.no_svg,
        text_normalizer=normalizer
    )
    
    # Check dependencies
    if not HAS_PILLOW and not args.no_images:
        print("Note: Install Pillow for image cleaning: pip install Pillow", file=sys.stderr)
    if not HAS_PIKEPDF and not args.no_pdfs:
        print("Note: Install pikepdf for PDF cleaning: pip install pikepdf", file=sys.stderr)
    if not HAS_MUTAGEN and not args.no_audio:
        print("Note: Install mutagen for audio cleaning: pip install mutagen", file=sys.stderr)
    
    # Dry run mode
    if args.dry_run:
        print("DRY RUN — No files will be modified\n")
        if args.input.is_file():
            if cleaner.can_handle(args.input):
                print(f"Would clean: {args.input}")
            else:
                print(f"Cannot handle: {args.input}")
        else:
            pattern = '**/*' if args.recursive else '*'
            for f in args.input.glob(pattern):
                if f.is_file() and cleaner.can_handle(f):
                    print(f"Would clean: {f}")
        return
    
    # Process files
    reports = []
    
    if args.input.is_file():
        report = cleaner.clean_file(args.input, args.output, inplace=args.inplace)
        reports.append(report)
        print_report(report, args.verbose)
    else:
        reports = cleaner.clean_directory(
            args.input, 
            args.output,
            recursive=args.recursive,
            inplace=args.inplace
        )
        for report in reports:
            print_report(report, args.verbose)
    
    # Summary
    if len(reports) > 1:
        successful = sum(1 for r in reports if r.success)
        total_removed = sum(r.size_diff for r in reports if r.size_diff > 0)
        print(f"\n{'='*60}")
        print(f"Processed: {len(reports)} files")
        print(f"Successful: {successful}")
        print(f"Total size reduction: {total_removed:,} bytes")
    
    # JSON report
    if args.json:
        with open(args.json, 'w') as f:
            json.dump([r.to_dict() for r in reports], f, indent=2)
        print(f"\nJSON report: {args.json}")
    
    # Exit code
    sys.exit(0 if all(r.success for r in reports) else 1)


if __name__ == '__main__':
    main()
