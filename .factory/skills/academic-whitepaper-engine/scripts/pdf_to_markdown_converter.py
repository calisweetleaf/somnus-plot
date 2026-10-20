#!/usr/bin/env python3
"""
PDF OCR to Structured Markdown Converter
Features:
- Batch processing of multiple PDFs
- OCR text extraction with semantic structure detection
- Clean Markdown formatting (headings, lists, tables, code blocks)
- Metadata hashing (SHA256, timestamps, location tags)
- Organized output to designated folders
- Zip file creation with all outputs
- Support for various document types (technical docs, reports, articles)
"""

import os
import sys
import re
import json
import yaml
import hashlib
import zipfile
import logging
import argparse
import subprocess
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from enum import Enum

# OCR and PDF libraries — graceful dependency check (NO dynamic pip install)
_MISSING_DEPS = []
try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    _MISSING_DEPS.append("pillow")

try:
    import pytesseract
except ImportError:
    _MISSING_DEPS.append("pytesseract")

try:
    from pdf2image import convert_from_path
except ImportError:
    _MISSING_DEPS.append("pdf2image")

try:
    import PyPDF2
except ImportError:
    _MISSING_DEPS.append("pypdf2")

try:
    import fitz  # PyMuPDF - for better text extraction
except ImportError:
    _MISSING_DEPS.append("pymupdf")

try:
    import cv2
except ImportError:
    _MISSING_DEPS.append("opencv-python")

try:
    import numpy as np
except ImportError:
    _MISSING_DEPS.append("numpy")

try:
    from sklearn.cluster import DBSCAN
except ImportError:
    _MISSING_DEPS.append("scikit-learn")

if _MISSING_DEPS:
    print(
        "✗ Missing required dependencies for PDF-to-Markdown conversion:\n"
        f"  {', '.join(_MISSING_DEPS)}\n\n"
        "Install them with:\n"
        f"  pip install {' '.join(_MISSING_DEPS)}\n\n"
        "Or install the full OCR extras:\n"
        "  pip install whitepaper-engine[ocr]",
        file=sys.stderr,
    )
    sys.exit(2)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_markdown_converter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of documents for structure detection"""
    TECHNICAL = "technical"
    REPORT = "report"
    ARTICLE = "article"
    PAPER = "paper"
    BOOK = "book"
    UNKNOWN = "unknown"


@dataclass
class DocumentMetadata:
    """Structured metadata for documents"""
    filename: str
    original_path: str
    file_size: int
    sha256_hash: str
    md5_hash: str
    processing_timestamp: str
    location_tag: str
    pages: int
    document_type: str
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None
    language: str = "en"
    estimated_word_count: int = 0
    estimated_paragraphs: int = 0
    estimated_sections: int = 0
    ocr_confidence_avg: float = 0.0


@dataclass
class OCRPage:
    """OCR result for a single page"""
    page_number: int
    text: str
    structured_text: List[Dict]
    confidence: float
    image_dimensions: Tuple[int, int]
    processing_time: float
    detected_elements: List[str]


class MarkdownFormatter:
    """Formats OCR text into clean, structured Markdown"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'heading_levels': {'h1': '#', 'h2': '##', 'h3': '###', 'h4': '####', 'h5': '#####'},
            'detect_tables': True,
            'detect_lists': True,
            'detect_code': True,
            'detect_quotes': True,
            'clean_whitespace': True,
            'preserve_line_breaks': False,
            'max_line_length': 80,
            'table_format': 'github',  # github, simple, grid
            'language_detection': True
        }
        
        # Regex patterns for structure detection
        self.heading_patterns = [
            (r'^(?:[IVXLCDM]+\.\s+)?[A-Z][A-Z\s]{10,}$', 'h1'),
            (r'^(?:[0-9]+\.\s+)?[A-Z][A-Za-z\s]{5,}$', 'h2'),
            (r'^(?:[0-9]+\.[0-9]+\s+)?[A-Z][A-Za-z\s]{3,}$', 'h3'),
            (r'^(?:[a-z]\)\s+)?[A-Z][a-z]+(?:\s+[A-Za-z]+){1,3}$', 'h4'),
        ]
        
        self.list_patterns = [
            (r'^\s*[-*•]\s+', 'bullet'),
            (r'^\s*\d+\.\s+', 'numbered'),
            (r'^\s*\([a-zA-Z0-9]\)\s+', 'alpha'),
        ]
        
        self.code_block_patterns = [
            (r'^\s*(?:def|class|import|from|if|for|while|return|print)\s+', 'python'),
            (r'^\s*(?:function|var|let|const|if|for|while|return|console\.)\s+', 'javascript'),
            (r'^\s*(?:<\?php|echo|function|class|if|for|foreach)\s+', 'php'),
            (r'^\s*(?:public|private|class|interface|void|int|String)\s+', 'java'),
            (r'^\s*(?:#include|int main|printf|scanf)\s+', 'c'),
        ]
    
    def clean_text(self, text: str) -> str:
        """Clean OCR text artifacts"""
        # Remove excessive whitespace
        if self.config['clean_whitespace']:
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            # Collapse spaces/tabs but preserve newlines for structure detection
            text = re.sub(r'[ \t]+', ' ', text)
            # Normalize excessive blank lines
            text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Fix common OCR errors
        replacements = [
            (r'(\w)\s*-\s*(\w)', r'\1-\2'),  # Fix hyphenated words
            (r'\s*,\s*', ', '),  # Fix commas
            (r'\s*\.\s*', '. '),  # Fix periods
            (r'\s*:\s*', ': '),  # Fix colons
            (r'\s*;\s*', '; '),  # Fix semicolons
            (r'\s*\!\s*', '! '),  # Fix exclamation
            (r'\s*\?\s*', '? '),  # Fix question marks
            (r'``', '"'),  # Fix quotes
            (r"''", '"'),  # Fix quotes
            (r'`', "'"),  # Fix apostrophes
            (r'\s+\)', ')'),  # Fix parentheses
            (r'\(\s+', '('),  # Fix parentheses
            (r'\s+\]', ']'),  # Fix brackets
            (r'\[\s+', '['),  # Fix brackets
        ]
        
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        
        return text.strip()
    
    def detect_structure(self, lines: List[str]) -> List[Dict]:
        """Detect document structure from text lines"""
        structured = []
        
        for i, line in enumerate(lines):
            line = line.rstrip()
            if not line:
                continue
            
            element = {
                'text': line,
                'type': 'paragraph',
                'level': None,
                'language': None,
                'is_continuation': False
            }
            
            # Check for headings
            for pattern, heading_type in self.heading_patterns:
                if re.match(pattern, line.strip()):
                    element['type'] = 'heading'
                    element['level'] = heading_type
                    break
            
            # Check for lists
            if element['type'] == 'paragraph':
                for pattern, list_type in self.list_patterns:
                    if re.match(pattern, line):
                        element['type'] = 'list_item'
                        element['list_type'] = list_type
                        element['indent'] = len(line) - len(line.lstrip())
                        break
            
            # Check for code blocks
            if element['type'] == 'paragraph' and self.config['detect_code']:
                for pattern, language in self.code_block_patterns:
                    if re.match(pattern, line):
                        element['type'] = 'code'
                        element['language'] = language
                        break
            
            # Check for quotes
            if element['type'] == 'paragraph' and line.strip().startswith('>'):
                element['type'] = 'quote'
            
            # Check for table rows
            if element['type'] == 'paragraph' and self.config['detect_tables']:
                # Simple table detection: multiple columns separated by 2+ spaces or tabs
                if re.search(r'\s{2,}|\t', line) and len(line.split()) > 2:
                    element['type'] = 'table_row'
                    element['columns'] = [col.strip() for col in re.split(r'\s{2,}|\t', line)]
            
            structured.append(element)
        
        return structured
    
    def format_to_markdown(self, structured_text: List[Dict], metadata: DocumentMetadata) -> str:
        """Convert structured text to Markdown"""
        markdown_lines = []
        
        # Add document header
        markdown_lines.append(f"# {metadata.title or metadata.filename.replace('.pdf', '')}")
        markdown_lines.append("")
        
        # Add metadata block
        markdown_lines.append("## Document Metadata")
        markdown_lines.append("")
        markdown_lines.append("| Property | Value |")
        markdown_lines.append("|----------|-------|")
        markdown_lines.append(f"| Filename | {metadata.filename} |")
        markdown_lines.append(f"| Author | {metadata.author or 'Unknown'} |")
        markdown_lines.append(f"| Pages | {metadata.pages} |")
        markdown_lines.append(f"| Created | {metadata.created or 'Unknown'} |")
        markdown_lines.append(f"| Modified | {metadata.modified or 'Unknown'} |")
        markdown_lines.append(f"| SHA256 | `{metadata.sha256_hash}` |")
        markdown_lines.append(f"| Processing Timestamp | {metadata.processing_timestamp} |")
        markdown_lines.append(f"| Document Type | {metadata.document_type} |")
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")
        
        # Process structured text
        in_code_block = False
        current_language = None
        in_table = False
        table_rows = []
        list_stack = []
        
        for element in structured_text:
            text = element['text']
            
            # Handle code blocks
            if element['type'] == 'code':
                if not in_code_block:
                    language = element.get('language', '')
                    markdown_lines.append(f"```{language}")
                    in_code_block = True
                    current_language = language
                markdown_lines.append(text)
            elif in_code_block:
                markdown_lines.append("```")
                markdown_lines.append("")
                in_code_block = False
                current_language = None
            
            # Handle headings
            elif element['type'] == 'heading':
                level = element['level']
                if level == 'h1':
                    markdown_lines.append(f"# {text}")
                elif level == 'h2':
                    markdown_lines.append(f"## {text}")
                elif level == 'h3':
                    markdown_lines.append(f"### {text}")
                elif level == 'h4':
                    markdown_lines.append(f"#### {text}")
                else:
                    markdown_lines.append(f"##### {text}")
                markdown_lines.append("")
            
            # Handle list items
            elif element['type'] == 'list_item':
                list_type = element.get('list_type', 'bullet')
                indent = element.get('indent', 0)
                
                # Manage list hierarchy
                while list_stack and list_stack[-1][0] >= indent:
                    list_stack.pop()
                
                prefix = "  " * (len(list_stack))
                if list_type == 'numbered':
                    list_num = 1
                    for _, lt, ln in reversed(list_stack):
                        if lt == 'numbered':
                            list_num = ln + 1
                            break
                    markdown_lines.append(f"{prefix}{list_num}. {text.lstrip()}")
                    list_stack.append((indent, 'numbered', list_num))
                else:
                    markdown_lines.append(f"{prefix}* {text.lstrip()}")
                    list_stack.append((indent, 'bullet', 0))
            
            # Handle table rows
            elif element['type'] == 'table_row':
                columns = element.get('columns', [])
                if not in_table:
                    # Start table
                    markdown_lines.append("| " + " | ".join(columns) + " |")
                    markdown_lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
                    in_table = True
                    table_rows = [columns]
                else:
                    if len(columns) == len(table_rows[0]):
                        markdown_lines.append("| " + " | ".join(columns) + " |")
                        table_rows.append(columns)
                    else:
                        # End table if column count doesn't match
                        markdown_lines.append("")
                        in_table = False
            
            # Handle quotes
            elif element['type'] == 'quote':
                markdown_lines.append(f"> {text.lstrip('> ')}")
                markdown_lines.append("")
            
            # Handle regular paragraphs
            elif element['type'] == 'paragraph':
                if in_table:
                    markdown_lines.append("")
                    in_table = False
                    list_stack.clear()
                
                # Wrap long lines if configured
                if self.config['max_line_length'] and len(text) > self.config['max_line_length']:
                    words = text.split()
                    lines = []
                    current_line = []
                    current_length = 0
                    
                    for word in words:
                        if current_length + len(word) + 1 > self.config['max_line_length']:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            current_length = len(word)
                        else:
                            current_line.append(word)
                            current_length += len(word) + 1
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    for line in lines:
                        markdown_lines.append(line)
                    markdown_lines.append("")
                else:
                    markdown_lines.append(text)
                    if not self.config['preserve_line_breaks']:
                        markdown_lines.append("")
        
        # Close any open code block
        if in_code_block:
            markdown_lines.append("```")
        
        # Add document footer
        markdown_lines.append("")
        markdown_lines.append("---")
        markdown_lines.append("")
        markdown_lines.append(f"*Document processed by PDF OCR to Markdown Converter on {metadata.processing_timestamp}*")
        markdown_lines.append(f"*OCR Confidence: {metadata.ocr_confidence_avg:.1f}%*")
        
        return '\n'.join(markdown_lines)
    
    def format_table_github(self, rows: List[List[str]]) -> str:
        """Format table in GitHub-style Markdown"""
        if not rows or len(rows) < 2:
            return ""
        
        markdown = []
        markdown.append("| " + " | ".join(rows[0]) + " |")
        markdown.append("| " + " | ".join(["---"] * len(rows[0])) + " |")
        
        for row in rows[1:]:
            markdown.append("| " + " | ".join(row) + " |")
        
        return '\n'.join(markdown)


class PDFToMarkdownConverter:
    """Main PDF to Markdown converter with OCR and batch processing"""
    
    def __init__(self,
                 input_paths: List[str],
                 output_dir: str = "markdown_output",
                 temp_dir: str = "temp_md",
                 poppler_path: Optional[str] = None,
                 tesseract_path: Optional[str] = None,
                 max_workers: int = 2,
                 dpi: int = 300,
                 config_file: Optional[str] = None):
        """
        Initialize the PDF to Markdown converter
        
        Args:
            input_paths: List of PDF file paths or directory paths
            output_dir: Directory to save processed Markdown files
            temp_dir: Directory for temporary files
            poppler_path: Path to poppler binaries
            tesseract_path: Path to tesseract executable
            max_workers: Maximum number of concurrent workers
            dpi: DPI for image conversion
            config_file: Path to configuration file
        """
        self.input_paths = input_paths
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.poppler_path = poppler_path
        self.tesseract_path = tesseract_path
        self.max_workers = max_workers
        self.dpi = dpi
        
        # Load configuration
        self.config = self.load_config(config_file)
        
        # Setup directories
        self.setup_directories()
        
        # Configure Tesseract
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Initialize formatter
        self.formatter = MarkdownFormatter(self.config.get('formatting', {}))
        
        # Processing state
        self.processed_files = []
        self.metadata_store = []
        self.start_time = None
        self.end_time = None
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'total_pages': 0,
            'total_words': 0,
            'total_characters': 0,
            'processing_time': 0
        }
    
    def load_config(self, config_file: Optional[str]) -> Dict:
        """Load configuration from YAML file"""
        default_config = {
            'ocr': {
                'dpi': 300,
                'language': 'eng',
                'engine_mode': 3,
                'page_segmentation_mode': 3,
                'preprocess': True,
                'preprocessing_steps': ['deskew', 'denoise', 'threshold']
            },
            'formatting': {
                'heading_levels': {'h1': '#', 'h2': '##', 'h3': '###', 'h4': '####'},
                'detect_tables': True,
                'detect_lists': True,
                'detect_code': True,
                'detect_quotes': True,
                'clean_whitespace': True,
                'preserve_line_breaks': False,
                'max_line_length': 80,
                'table_format': 'github'
            },
            'output': {
                'include_metadata': True,
                'include_toc': True,
                'toc_depth': 3,
                'split_by_heading': False,
                'max_file_size_mb': 10
            },
            'processing': {
                'max_concurrent': 2,
                'timeout_per_page': 30,
                'retry_failed': True,
                'max_retries': 2
            }
        }
        
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = yaml.safe_load(f)
                    # Merge configurations
                    self.merge_dicts(default_config, user_config)
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}. Using defaults.")
        
        return default_config
    
    def merge_dicts(self, base: Dict, update: Dict) -> Dict:
        """Recursively merge dictionaries"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self.merge_dicts(base[key], value)
            else:
                base[key] = value
        return base
    
    def setup_directories(self):
        """Create necessary directories"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        (self.output_dir / "assets").mkdir(exist_ok=True)
        (self.output_dir / "backups").mkdir(exist_ok=True)
    
    def collect_pdf_files(self) -> List[Path]:
        """Collect all PDF files from input paths"""
        pdf_files = []
        
        for input_path in self.input_paths:
            path = Path(input_path)
            
            if path.is_file() and path.suffix.lower() == '.pdf':
                pdf_files.append(path)
                logger.info(f"Added file: {path}")
            
            elif path.is_dir():
                for pdf_file in path.rglob("*.pdf"):
                    pdf_files.append(pdf_file)
                    logger.info(f"Added file from directory: {pdf_file}")
        
        # Sort files for consistent processing
        pdf_files.sort()
        
        logger.info(f"Total PDF files collected: {len(pdf_files)}")
        return pdf_files
    
    def compute_file_hashes(self, file_path: Path) -> Dict[str, str]:
        """Compute multiple hashes for a file"""
        hashes = {
            'sha256': hashlib.sha256(),
            'md5': hashlib.md5(),
            'sha1': hashlib.sha1()
        }
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                for hash_func in hashes.values():
                    hash_func.update(byte_block)
        
        return {name: func.hexdigest() for name, func in hashes.items()}
    
    def extract_pdf_metadata(self, file_path: Path) -> DocumentMetadata:
        """Extract metadata from PDF file"""
        # Compute file hashes
        hashes = self.compute_file_hashes(file_path)
        
        # Initialize metadata
        metadata = DocumentMetadata(
            filename=file_path.name,
            original_path=str(file_path),
            file_size=file_path.stat().st_size,
            sha256_hash=hashes['sha256'],
            md5_hash=hashes['md5'],
            processing_timestamp=datetime.now().isoformat(),
            location_tag=str(file_path.parent),
            pages=0,
            document_type=DocumentType.UNKNOWN.value,
            language="en"
        )
        
        try:
            # Try PyPDF2 first
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata.pages = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    pdf_info = pdf_reader.metadata
                    metadata.title = pdf_info.get('/Title')
                    metadata.author = pdf_info.get('/Author')
                    metadata.subject = pdf_info.get('/Subject')
                    metadata.created = pdf_info.get('/CreationDate')
                    metadata.modified = pdf_info.get('/ModDate')
            
            # Try PyMuPDF for additional metadata
            try:
                with fitz.open(file_path) as doc:
                    metadata_dict = doc.metadata
                    if metadata_dict:
                        metadata.title = metadata_dict.get('title') or metadata.title
                        metadata.author = metadata_dict.get('author') or metadata.author
                        metadata.subject = metadata_dict.get('subject') or metadata.subject
                        metadata.created = metadata_dict.get('creationDate') or metadata.created
                        metadata.modified = metadata_dict.get('modDate') or metadata.modified
            except:
                pass
            
            # Detect document type based on filename and content
            metadata.document_type = self.detect_document_type(file_path, metadata)
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
        
        return metadata
    
    def detect_document_type(self, file_path: Path, metadata: DocumentMetadata) -> str:
        """Detect type of document based on various heuristics"""
        filename = file_path.name.lower()
        
        # Check filename patterns
        if any(term in filename for term in ['thesis', 'dissertation', 'paper', 'research']):
            return DocumentType.PAPER.value
        elif any(term in filename for term in ['report', 'analysis', 'findings']):
            return DocumentType.REPORT.value
        elif any(term in filename for term in ['article', 'blog', 'post']):
            return DocumentType.ARTICLE.value
        elif any(term in filename for term in ['manual', 'guide', 'documentation', 'api']):
            return DocumentType.TECHNICAL.value
        elif any(term in filename for term in ['book', 'chapter', 'volume']):
            return DocumentType.BOOK.value
        
        # Check metadata
        if metadata.subject:
            subject_lower = metadata.subject.lower()
            if any(term in subject_lower for term in ['technical', 'manual', 'guide']):
                return DocumentType.TECHNICAL.value
            elif any(term in subject_lower for term in ['report', 'analysis']):
                return DocumentType.REPORT.value
        
        return DocumentType.UNKNOWN.value
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        if not self.config['ocr'].get('preprocess', True):
            return image
        
        steps = self.config['ocr'].get('preprocessing_steps', [])
        
        # Convert PIL to OpenCV
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        for step in steps:
            if step == 'grayscale':
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            elif step == 'denoise':
                img_cv = cv2.fastNlMeansDenoising(img_cv)
            elif step == 'threshold':
                if len(img_cv.shape) == 3:
                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                _, img_cv = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            elif step == 'deskew':
                # Simple deskewing
                coords = np.column_stack(np.where(img_cv > 0))
                angle = cv2.minAreaRect(coords)[-1]
                if angle < -45:
                    angle = 90 + angle
                if angle != 0:
                    (h, w) = img_cv.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    img_cv = cv2.warpAffine(img_cv, M, (w, h), flags=cv2.INTER_CUBIC, 
                                           borderMode=cv2.BORDER_REPLICATE)
            elif step == 'sharpen':
                kernel = np.array([[-1, -1, -1],
                                   [-1, 9, -1],
                                   [-1, -1, -1]])
                img_cv = cv2.filter2D(img_cv, -1, kernel)
        
        # Convert back to PIL
        if len(img_cv.shape) == 2:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2RGB)
        else:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        
        return Image.fromarray(img_cv)
    
    def ocr_page_to_markdown(self, image: Image.Image, page_num: int) -> OCRPage:
        """Perform OCR on a single page and structure the text"""
        start_time = time.time()
        
        # Preprocess image
        processed_image = self.preprocess_image(image)
        
        # OCR configuration
        ocr_config = self.config['ocr']
        custom_config = f'--oem {ocr_config.get("engine_mode", 3)} --psm {ocr_config.get("page_segmentation_mode", 3)}'
        
        try:
            # Get OCR data with confidence
            ocr_data = pytesseract.image_to_data(
                processed_image,
                lang=ocr_config.get('language', 'eng'),
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [float(conf) for conf in ocr_data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Reconstruct text by lines
            text_lines = []
            current_line = []
            current_line_num = -1
            
            for i in range(len(ocr_data['text'])):
                if ocr_data['text'][i].strip():
                    line_num = ocr_data['line_num'][i]
                    
                    if line_num != current_line_num:
                        if current_line:
                            text_lines.append(' '.join(current_line))
                            current_line = []
                        current_line_num = line_num
                    
                    current_line.append(ocr_data['text'][i])
            
            if current_line:
                text_lines.append(' '.join(current_line))
            
            full_text = '\n'.join(text_lines)
            
            # Clean and structure text
            cleaned_text = self.formatter.clean_text(full_text)
            lines = cleaned_text.split('\n')
            structured_text = self.formatter.detect_structure(lines)
            
            # Detect elements
            detected_elements = set()
            for element in structured_text:
                detected_elements.add(element['type'])
            
            return OCRPage(
                page_number=page_num,
                text=cleaned_text,
                structured_text=structured_text,
                confidence=avg_confidence,
                image_dimensions=image.size,
                processing_time=time.time() - start_time,
                detected_elements=list(detected_elements)
            )
            
        except Exception as e:
            logger.error(f"Error during OCR on page {page_num}: {e}")
            # Fallback to simple OCR
            fallback_text = pytesseract.image_to_string(
                processed_image,
                lang=ocr_config.get('language', 'eng')
            )
            
            return OCRPage(
                page_number=page_num,
                text=fallback_text,
                structured_text=[{'text': fallback_text, 'type': 'paragraph'}],
                confidence=0.0,
                image_dimensions=image.size,
                processing_time=time.time() - start_time,
                detected_elements=['paragraph']
            )
    
    def process_single_pdf(self, pdf_path: Path) -> Dict:
        """Process a single PDF file to Markdown"""
        logger.info(f"Processing: {pdf_path}")
        
        # Extract metadata
        metadata = self.extract_pdf_metadata(pdf_path)
        
        # Convert PDF to images
        try:
            images = convert_from_path(
                str(pdf_path),
                dpi=self.config['ocr'].get('dpi', self.dpi),
                poppler_path=self.poppler_path
            )
            metadata.pages = len(images)
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return {
                'filename': str(pdf_path),
                'status': 'failed',
                'error': str(e),
                'metadata': asdict(metadata)
            }
        
        # OCR each page
        ocr_pages = []
        total_confidence = 0
        total_words = 0
        total_chars = 0
        
        for i, image in enumerate(images):
            try:
                ocr_page = self.ocr_page_to_markdown(image, i + 1)
                ocr_pages.append(ocr_page)
                total_confidence += ocr_page.confidence
                
                # Update statistics
                words = len(ocr_page.text.split())
                chars = len(ocr_page.text)
                total_words += words
                total_chars += chars
                
                logger.debug(f"Processed page {i+1}/{len(images)} - "
                           f"Confidence: {ocr_page.confidence:.1f}%")
                
            except Exception as e:
                logger.error(f"Error processing page {i+1}: {e}")
                # Add empty page as placeholder
                ocr_pages.append(OCRPage(
                    page_number=i + 1,
                    text=f"[Error processing page {i+1}: {e}]",
                    structured_text=[],
                    confidence=0.0,
                    image_dimensions=image.size,
                    processing_time=0,
                    detected_elements=[]
                ))
        
        # Update metadata with OCR statistics
        metadata.ocr_confidence_avg = total_confidence / len(ocr_pages) if ocr_pages else 0
        metadata.estimated_word_count = total_words
        metadata.estimated_paragraphs = len([p for p in ocr_pages if p.structured_text])
        metadata.estimated_sections = len([elem for p in ocr_pages 
                                          for elem in p.structured_text 
                                          if elem.get('type') == 'heading'])
        
        # Combine all pages
        all_structured_text = []
        for page in ocr_pages:
            all_structured_text.extend(page.structured_text)
        
        # Generate Markdown
        markdown_content = self.formatter.format_to_markdown(all_structured_text, metadata)
        
        # Save Markdown file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^\w\-_\. ]', '_', pdf_path.stem)
        output_filename = f"{safe_name}_{timestamp}.md"
        output_path = self.output_dir / "markdown" / output_filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # Compute hash of generated Markdown
            md_hashes = self.compute_file_hashes(output_path)
            
            # Update result
            result = {
                'status': 'success',
                'metadata': asdict(metadata),
                'ocr_stats': {
                    'total_pages': len(ocr_pages),
                    'processed_pages': len([p for p in ocr_pages if p.confidence > 0]),
                    'average_confidence': metadata.ocr_confidence_avg,
                    'total_words': total_words,
                    'total_characters': total_chars,
                    'detected_elements': list(set([elem for p in ocr_pages 
                                                  for elem in p.detected_elements]))
                },
                'output_files': {
                    'markdown': str(output_path),
                    'markdown_sha256': md_hashes['sha256'],
                    'markdown_size': output_path.stat().st_size
                },
                'processing_details': {
                    'start_time': datetime.now().isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_time': sum(p.processing_time for p in ocr_pages)
                }
            }
            
            # Save individual metadata
            metadata_file = self.output_dir / "metadata" / f"{pdf_path.stem}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            logger.info(f"Successfully processed: {pdf_path} -> {output_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to save Markdown for {pdf_path}: {e}")
            return {
                'filename': str(pdf_path),
                'status': 'failed',
                'error': str(e),
                'metadata': asdict(metadata)
            }
    
    def process_all_pdfs(self):
        """Process all collected PDF files with batch processing"""
        import time
        self.start_time = datetime.now()
        logger.info(f"Starting batch processing at {self.start_time}")
        
        # Collect PDF files
        pdf_files = self.collect_pdf_files()
        
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return
        
        self.stats['total_files'] = len(pdf_files)
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process files with thread pool
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf_file): pdf_file 
                for pdf_file in pdf_files
            }
            
            for future in as_completed(future_to_pdf):
                pdf_file = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.processed_files.append(pdf_file)
                    
                    if result.get('status') == 'success':
                        self.stats['successful'] += 1
                        self.stats['total_pages'] += result['ocr_stats']['total_pages']
                        self.stats['total_words'] += result['ocr_stats']['total_words']
                        self.stats['total_characters'] += result['ocr_stats']['total_characters']
                    else:
                        self.stats['failed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {pdf_file}: {e}")
                    results.append({
                        'filename': str(pdf_file),
                        'status': 'failed',
                        'error': str(e)
                    })
                    self.stats['failed'] += 1
        
        # Save batch metadata
        self.save_batch_metadata(results)
        
        # Create zip archive
        self.create_zip_archive()
        
        # Generate reports
        self.generate_reports(results)
        
        self.end_time = datetime.now()
        self.stats['processing_time'] = (self.end_time - self.start_time).total_seconds()
        
        # Print summary
        self.print_summary()
        
        # Clean up
        self.cleanup_temp_directory()
    
    def save_batch_metadata(self, results: List[Dict]):
        """Save batch processing metadata"""
        batch_metadata = {
            "batch_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "processing_start": self.start_time.isoformat(),
            "processing_end": datetime.now().isoformat(),
            "config": self.config,
            "statistics": self.stats,
            "files": results,
            "summary": {
                "total_files": len(results),
                "successful": len([r for r in results if r.get('status') == 'success']),
                "failed": len([r for r in results if r.get('status') == 'failed']),
                "total_pages": self.stats['total_pages'],
                "total_words": self.stats['total_words'],
                "total_characters": self.stats['total_characters']
            }
        }
        
        metadata_file = self.output_dir / "batch_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(batch_metadata, f, indent=2, default=str)
        
        # Also save as YAML for readability
        yaml_file = self.output_dir / "batch_metadata.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(batch_metadata, f, default_flow_style=False)
        
        self.metadata_store = batch_metadata
        logger.info(f"Batch metadata saved to: {metadata_file}")
    
    def create_zip_archive(self):
        """Create a zip archive of all output files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = self.output_dir / f"markdown_archive_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add Markdown files
            markdown_dir = self.output_dir / "markdown"
            for md_file in markdown_dir.glob("*.md"):
                zipf.write(md_file, arcname=f"markdown/{md_file.name}")
            
            # Add metadata files
            metadata_dir = self.output_dir / "metadata"
            for meta_file in metadata_dir.glob("*.json"):
                zipf.write(meta_file, arcname=f"metadata/{meta_file.name}")
            
            # Add YAML metadata
            yaml_file = self.output_dir / "batch_metadata.yaml"
            if yaml_file.exists():
                zipf.write(yaml_file, arcname="batch_metadata.yaml")
            
            # Add log file
            log_file = Path("pdf_markdown_converter.log")
            if log_file.exists():
                zipf.write(log_file, arcname="processing_log.log")
            
            # Add config summary
            config_summary = {
                'converter_version': '1.0',
                'processing_date': datetime.now().isoformat(),
                'output_structure': {
                    'markdown': 'Converted Markdown files',
                    'metadata': 'JSON metadata for each file',
                    'logs': 'Processing logs',
                    'assets': 'Extracted images and assets'
                }
            }
            
            config_str = yaml.dump(config_summary, default_flow_style=False)
            zipf.writestr("README.md", f"# PDF to Markdown Archive\n\n{config_str}")
        
        zip_size = zip_filename.stat().st_size
        logger.info(f"Zip archive created: {zip_filename} ({zip_size / (1024*1024):.2f} MB)")
    
    def generate_reports(self, results: List[Dict]):
        """Generate various reports"""
        # Generate summary report
        self.generate_summary_report(results)
        
        # Generate statistics report
        self.generate_statistics_report(results)
        
        # Generate error report if any failures
        failed = [r for r in results if r.get('status') == 'failed']
        if failed:
            self.generate_error_report(failed)
    
    def generate_summary_report(self, results: List[Dict]):
        """Generate a human-readable summary report"""
        successful = len([r for r in results if r.get('status') == 'success'])
        failed = len([r for r in results if r.get('status') == 'failed'])
        
        report = f"""
        PDF to Markdown Conversion Summary
        ============================================
        
        Processing Date:     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Total Duration:      {self.stats['processing_time']:.2f} seconds
        
        Files Processed:     {self.stats['total_files']}
        ────────────────────────────────────────────
        Successful:          {successful}
        Failed:              {failed}
        
        Content Statistics:
        ────────────────────────────────────────────
        Total Pages:         {self.stats['total_pages']}
        Total Words:         {self.stats['total_words']:,}
        Total Characters:    {self.stats['total_characters']:,}
        
        Output Location:     {self.output_dir}
        
        Files Processed:
        ────────────────────────────────────────────
        """
        
        for result in results:
            status = "✓" if result.get('status') == 'success' else "✗"
            filename = result.get('metadata', {}).get('filename', 'Unknown')
            pages = result.get('ocr_stats', {}).get('total_pages', 0)
            confidence = result.get('ocr_stats', {}).get('average_confidence', 0)
            
            report += f"\n  {status} {filename}"
            if result.get('status') == 'success':
                report += f" ({pages} pages, {confidence:.1f}% confidence)"
            else:
                report += f" - ERROR: {result.get('error', 'Unknown error')}"
        
        report += "\n\n============================================\n"
        
        # Write to file
        summary_file = self.output_dir / "conversion_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(report)
        
        # Also create a Markdown version
        md_summary = f"""# PDF to Markdown Conversion Summary

## Overview
- **Processing Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Total Duration**: {self.stats['processing_time']:.2f} seconds
- **Total Files**: {self.stats['total_files']}
- **Successful**: {successful}
- **Failed**: {failed}

## Statistics
| Metric | Value |
|--------|-------|
| Total Pages | {self.stats['total_pages']} |
| Total Words | {self.stats['total_words']:,} |
| Total Characters | {self.stats['total_characters']:,} |

## Processed Files
"""
        
        for result in results:
            status = "✅" if result.get('status') == 'success' else "❌"
            filename = result.get('metadata', {}).get('filename', 'Unknown')
            pages = result.get('ocr_stats', {}).get('total_pages', 0)
            
            md_summary += f"- {status} **{filename}**"
            if result.get('status') == 'success':
                confidence = result.get('ocr_stats', {}).get('average_confidence', 0)
                md_summary += f" - {pages} pages ({confidence:.1f}% confidence)"
            else:
                md_summary += f" - Failed: {result.get('error', 'Unknown error')}"
            md_summary += "\n"
        
        md_summary_file = self.output_dir / "conversion_summary.md"
        with open(md_summary_file, 'w') as f:
            f.write(md_summary)
    
    def generate_statistics_report(self, results: List[Dict]):
        """Generate detailed statistics report"""
        successful_results = [r for r in results if r.get('status') == 'success']
        
        if not successful_results:
            return
        
        stats = {
            'confidence_scores': [],
            'page_counts': [],
            'word_counts': [],
            'file_sizes': [],
            'processing_times': [],
            'document_types': {},
            'detected_elements': {}
        }
        
        for result in successful_results:
            ocr_stats = result.get('ocr_stats', {})
            metadata = result.get('metadata', {})
            
            stats['confidence_scores'].append(ocr_stats.get('average_confidence', 0))
            stats['page_counts'].append(ocr_stats.get('total_pages', 0))
            stats['word_counts'].append(ocr_stats.get('total_words', 0))
            stats['file_sizes'].append(metadata.get('file_size', 0))
            
            doc_type = metadata.get('document_type', 'unknown')
            stats['document_types'][doc_type] = stats['document_types'].get(doc_type, 0) + 1
            
            elements = ocr_stats.get('detected_elements', [])
            for elem in elements:
                stats['detected_elements'][elem] = stats['detected_elements'].get(elem, 0) + 1
        
        # Calculate statistics
        def calculate_stats(values):
            if not values:
                return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}
            values = [v for v in values if v is not None]
            if not values:
                return {'min': 0, 'max': 0, 'avg': 0, 'median': 0}
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            return {
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / n,
                'median': sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
            }
        
        stats_report = {
            'overall': {
                'total_files_processed': len(results),
                'successful_conversions': len(successful_results),
                'success_rate': len(successful_results) / len(results) * 100 if results else 0
            },
            'ocr_confidence': calculate_stats(stats['confidence_scores']),
            'pages': calculate_stats(stats['page_counts']),
            'words': calculate_stats(stats['word_counts']),
            'file_sizes_mb': calculate_stats([s / (1024*1024) for s in stats['file_sizes']]),
            'document_type_distribution': stats['document_types'],
            'element_distribution': stats['detected_elements']
        }
        
        # Save statistics report
        stats_file = self.output_dir / "detailed_statistics.json"
        with open(stats_file, 'w') as f:
            json.dump(stats_report, f, indent=2)
        
        # Create human-readable version
        human_stats = f"""# Detailed Conversion Statistics

## Overall
- **Total Files Processed**: {stats_report['overall']['total_files_processed']}
- **Successful Conversions**: {stats_report['overall']['successful_conversions']}
- **Success Rate**: {stats_report['overall']['success_rate']:.1f}%

## OCR Confidence
- **Average**: {stats_report['ocr_confidence']['avg']:.1f}%
- **Minimum**: {stats_report['ocr_confidence']['min']:.1f}%
- **Maximum**: {stats_report['ocr_confidence']['max']:.1f}%
- **Median**: {stats_report['ocr_confidence']['median']:.1f}%

## Document Size
- **Average Pages**: {stats_report['pages']['avg']:.1f}
- **Average Words**: {stats_report['words']['avg']:,.0f}
- **Average File Size**: {stats_report['file_sizes_mb']['avg']:.2f} MB

## Document Types
"""
        
        for doc_type, count in stats_report['document_type_distribution'].items():
            percentage = count / len(successful_results) * 100
            human_stats += f"- **{doc_type.title()}**: {count} ({percentage:.1f}%)\n"
        
        human_stats += "\n## Detected Elements\n"
        for element, count in stats_report['element_distribution'].items():
            human_stats += f"- **{element}**: {count}\n"
        
        human_stats_file = self.output_dir / "detailed_statistics.md"
        with open(human_stats_file, 'w') as f:
            f.write(human_stats)
    
    def generate_error_report(self, failed_results: List[Dict]):
        """Generate error report for failed conversions"""
        error_report = f"""# Error Report

## Summary
- **Total Failed Files**: {len(failed_results)}
- **Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Failed Files
"""
        
        for result in failed_results:
            error_report += f"\n### {result.get('filename', 'Unknown')}\n"
            error_report += f"- **Error**: {result.get('error', 'Unknown error')}\n"
            
            metadata = result.get('metadata', {})
            if metadata:
                error_report += f"- **File Size**: {metadata.get('file_size', 0) / 1024:.1f} KB\n"
                error_report += f"- **Location**: {metadata.get('location_tag', 'Unknown')}\n"
            
            error_report += "\n"
        
        error_file = self.output_dir / "error_report.md"
        with open(error_file, 'w') as f:
            f.write(error_report)
    
    def print_summary(self):
        """Print processing summary to console"""
        duration = self.stats['processing_time']
        successful = self.stats['successful']
        total = self.stats['total_files']
        
        summary = f"""
        ╔══════════════════════════════════════════╗
        ║   PDF to Markdown Conversion Complete!   ║
        ╚══════════════════════════════════════════╝
        
        📊 Statistics:
        ────────────────────────────────────────────
          Total Files:      {total}
          Successful:       {successful}
          Failed:           {self.stats['failed']}
          Success Rate:     {successful/total*100 if total > 0 else 0:.1f}%
        
        📄 Content Processed:
        ────────────────────────────────────────────
          Total Pages:      {self.stats['total_pages']}
          Total Words:      {self.stats['total_words']:,}
          Total Chars:      {self.stats['total_characters']:,}
        
        ⏱️  Performance:
        ────────────────────────────────────────────
          Total Time:       {duration:.2f} seconds
          Avg Time/File:    {duration/total if total > 0 else 0:.2f} seconds
          Pages/Second:     {self.stats['total_pages']/duration if duration > 0 else 0:.2f}
        
        📁 Output Location:
        ────────────────────────────────────────────
          {self.output_dir}
        
        📦 Archive Created:
        ────────────────────────────────────────────
          markdown_archive_*.zip
        """
        
        print(summary)
        logger.info("Processing complete. Summary printed above.")
    
    def cleanup_temp_directory(self):
        """Clean up temporary files"""
        try:
            for file in self.temp_dir.glob("*"):
                try:
                    file.unlink()
                except:
                    pass
            
            # Remove temp directory if empty
            if not any(self.temp_dir.iterdir()):
                self.temp_dir.rmdir()
                
        except Exception as e:
            logger.warning(f"Could not clean up temp directory: {e}")


def main():
    """Main function to run the PDF to Markdown converter"""
    parser = argparse.ArgumentParser(
        description="PDF OCR to Structured Markdown Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single PDF to Markdown
  python pdf_to_markdown.py document.pdf
  
  # Convert multiple PDFs
  python pdf_to_markdown.py doc1.pdf doc2.pdf doc3.pdf
  
  # Convert all PDFs in a directory
  python pdf_to_markdown.py /path/to/pdfs/
  
  # Custom output directory
  python pdf_to_markdown.py input.pdf --output ./my_markdown
  
  # Specify configuration file
  python pdf_to_markdown.py input.pdf --config config.yaml
  
  # Set number of concurrent workers
  python pdf_to_markdown.py input.pdf --workers 4
  
  # Specify Tesseract path
  python pdf_to_markdown.py input.pdf --tesseract /usr/bin/tesseract
        """
    )
    
    parser.add_argument(
        "inputs",
        nargs="+",
        help="PDF files or directories to process"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        default="markdown_output",
        help="Output directory (default: markdown_output)"
    )
    
    parser.add_argument(
        "--temp",
        "-t",
        default="temp_md",
        help="Temporary directory (default: temp_md)"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=2,
        help="Number of concurrent workers (default: 2)"
    )
    
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for image conversion (default: 300)"
    )
    
    parser.add_argument(
        "--tesseract",
        help="Path to tesseract executable (if not in PATH)"
    )
    
    parser.add_argument(
        "--poppler",
        help="Path to poppler binaries (if not in PATH)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (saves intermediate images)"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check for Tesseract
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        print("""
        Error: Tesseract OCR is not installed or not in PATH.
        
        Installation instructions:
        
        Ubuntu/Debian:
          sudo apt-get install tesseract-ocr
        
        macOS:
          brew install tesseract
        
        Windows:
          Download from: https://github.com/UB-Mannheim/tesseract/wiki
          
        Or specify the path with --tesseract option.
        """)
        sys.exit(1)
    
    # Create converter instance
    converter = PDFToMarkdownConverter(
        input_paths=args.inputs,
        output_dir=args.output,
        temp_dir=args.temp,
        poppler_path=args.poppler,
        tesseract_path=args.tesseract,
        max_workers=args.workers,
        dpi=args.dpi,
        config_file=args.config
    )
    
    try:
        # Start processing
        converter.process_all_pdfs()
        
        logger.info("Conversion completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Conversion interrupted by user")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())