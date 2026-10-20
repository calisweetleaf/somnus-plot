#!/usr/bin/env python3
"""
PDF OCR Scanner with Batch Processing and Metadata Management
Features:
- Batch processing of multiple PDFs
- Sequential processing to avoid conflicts
- OCR text extraction
- Metadata hashing (SHA256, timestamps, location tags)
- Organized output to designated folders
- Zip file creation
- Progress tracking and logging
"""

import os
import sys
import time
import json
import hashlib
import zipfile
import logging
import argparse
import threading
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# OCR and PDF libraries — graceful dependency check (NO dynamic pip install)
_MISSING_DEPS = []
try:
    from PIL import Image
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
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    _MISSING_DEPS.append("reportlab")

if _MISSING_DEPS:
    print(
        "✗ Missing required dependencies for PDF OCR scanning:\n"
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
        logging.FileHandler('pdf_ocr_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PDFOCRScanner:
    """Main PDF OCR Scanner class with batch processing capabilities"""
    
    def __init__(self, 
                 input_paths: List[str],
                 output_dir: str = "processed_pdfs",
                 temp_dir: str = "temp",
                 poppler_path: Optional[str] = None,
                 tesseract_path: Optional[str] = None,
                 max_workers: int = 2,
                 dpi: int = 300):
        """
        Initialize the PDF OCR Scanner
        
        Args:
            input_paths: List of PDF file paths or directory paths
            output_dir: Directory to save processed PDFs
            temp_dir: Directory for temporary files
            poppler_path: Path to poppler binaries (for pdf2image)
            tesseract_path: Path to tesseract executable
            max_workers: Maximum number of concurrent workers
            dpi: DPI for image conversion
        """
        self.input_paths = input_paths
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.poppler_path = poppler_path
        self.tesseract_path = tesseract_path
        self.max_workers = max_workers
        self.dpi = dpi
        
        # Setup directories
        self.setup_directories()
        
        # Configure Tesseract if path is provided
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
        # Processing queue
        self.processing_queue = Queue()
        self.processed_files = []
        self.metadata_store = []
        
        # Performance tracking
        self.start_time = None
        self.end_time = None
        
    def setup_directories(self):
        """Create necessary directories"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "ocr_pdfs").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        
    def collect_pdf_files(self) -> List[Path]:
        """
        Collect all PDF files from input paths
        
        Returns:
            List of Path objects for PDF files
        """
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
                    
        # Sort files for consistent processing order
        pdf_files.sort()
        
        logger.info(f"Total PDF files collected: {len(pdf_files)}")
        return pdf_files
    
    def compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA256 hash of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest()
    
    def extract_pdf_metadata(self, file_path: Path) -> Dict:
        """
        Extract metadata from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            "filename": file_path.name,
            "original_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "sha256_hash": self.compute_file_hash(file_path),
            "processing_timestamp": datetime.now().isoformat(),
            "location_tag": str(file_path.parent),
            "pages": 0,
            "author": None,
            "title": None,
            "subject": None,
            "created": None,
            "modified": None
        }
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                # Extract PDF info
                if pdf_reader.metadata:
                    pdf_info = pdf_reader.metadata
                    metadata.update({
                        "author": pdf_info.get('/Author'),
                        "title": pdf_info.get('/Title'),
                        "subject": pdf_info.get('/Subject'),
                        "created": pdf_info.get('/CreationDate'),
                        "modified": pdf_info.get('/ModDate')
                    })
                    
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            
        return metadata
    
    def perform_ocr_on_pdf(self, pdf_path: Path, output_path: Path) -> Dict:
        """
        Perform OCR on a PDF file and save as searchable PDF
        
        Args:
            pdf_path: Path to input PDF
            output_path: Path to save OCRed PDF
            
        Returns:
            Dictionary with OCR statistics
        """
        ocr_stats = {
            "original_file": str(pdf_path),
            "output_file": str(output_path),
            "total_pages": 0,
            "processed_pages": 0,
            "ocr_text_length": 0,
            "processing_time": 0,
            "ocr_errors": []
        }
        
        start_time = time.time()
        
        try:
            # Convert PDF to images
            logger.info(f"Converting PDF to images: {pdf_path}")
            images = convert_from_path(
                str(pdf_path),
                dpi=self.dpi,
                poppler_path=self.poppler_path
            )
            
            ocr_stats["total_pages"] = len(images)
            
            # Create searchable PDF
            temp_pdf_paths = []
            all_text = []
            
            for i, image in enumerate(images):
                try:
                    # Perform OCR
                    text = pytesseract.image_to_pdf_or_hocr(
                        image, 
                        extension='pdf',
                        config='--psm 3 --oem 3'
                    )
                    
                    # Save temporary PDF for this page
                    temp_pdf_path = self.temp_dir / f"page_{i}_{pdf_path.stem}.pdf"
                    with open(temp_pdf_path, 'wb') as f:
                        f.write(text)
                    
                    temp_pdf_paths.append(temp_pdf_path)
                    ocr_stats["processed_pages"] += 1
                    
                    # Also extract text for statistics
                    extracted_text = pytesseract.image_to_string(image)
                    all_text.append(extracted_text)
                    
                    logger.debug(f"Processed page {i+1}/{len(images)}")
                    
                except Exception as e:
                    error_msg = f"Error processing page {i+1}: {e}"
                    logger.error(error_msg)
                    ocr_stats["ocr_errors"].append(error_msg)
            
            # Merge all temporary PDFs into one
            if temp_pdf_paths:
                self.merge_pdfs(temp_pdf_paths, output_path)
                
                # Update OCR statistics
                ocr_stats["ocr_text_length"] = sum(len(text) for text in all_text)
                
                # Clean up temporary files
                for temp_file in temp_pdf_paths:
                    try:
                        temp_file.unlink()
                    except:
                        pass
                        
        except Exception as e:
            error_msg = f"Error during OCR processing: {e}"
            logger.error(error_msg)
            ocr_stats["ocr_errors"].append(error_msg)
            
        finally:
            ocr_stats["processing_time"] = time.time() - start_time
            
        return ocr_stats
    
    def merge_pdfs(self, pdf_paths: List[Path], output_path: Path):
        """
        Merge multiple PDFs into one
        
        Args:
            pdf_paths: List of PDF file paths to merge
            output_path: Output PDF path
        """
        pdf_writer = PyPDF2.PdfWriter()
        
        for pdf_path in pdf_paths:
            pdf_reader = PyPDF2.PdfReader(str(pdf_path))
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
                
        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)
    
    def process_single_pdf(self, pdf_path: Path) -> Dict:
        """
        Process a single PDF file with OCR and metadata extraction
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing: {pdf_path}")
        
        # Extract metadata
        metadata = self.extract_pdf_metadata(pdf_path)
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"ocr_{pdf_path.stem}_{timestamp}.pdf"
        output_path = self.output_dir / "ocr_pdfs" / output_filename
        
        # Perform OCR
        ocr_stats = self.perform_ocr_on_pdf(pdf_path, output_path)
        
        # Compute hash of OCRed PDF
        if output_path.exists():
            metadata["ocr_sha256_hash"] = self.compute_file_hash(output_path)
            metadata["ocr_file_path"] = str(output_path)
            metadata["ocr_file_size"] = output_path.stat().st_size
            
        # Combine metadata and OCR stats
        result = {
            "metadata": metadata,
            "ocr_stats": ocr_stats,
            "status": "success" if ocr_stats["processed_pages"] > 0 else "failed",
            "processing_completed": datetime.now().isoformat()
        }
        
        # Save individual metadata
        metadata_file = self.output_dir / "metadata" / f"{pdf_path.stem}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
            
        logger.info(f"Completed: {pdf_path} - Status: {result['status']}")
        
        return result
    
    def process_all_pdfs(self):
        """
        Process all collected PDF files with batch processing
        """
        self.start_time = datetime.now()
        logger.info(f"Starting batch processing at {self.start_time}")
        
        # Collect PDF files
        pdf_files = self.collect_pdf_files()
        
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return
            
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process files with thread pool (controlled concurrency)
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_pdf = {
                executor.submit(self.process_single_pdf, pdf_file): pdf_file 
                for pdf_file in pdf_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_pdf):
                pdf_file = future_to_pdf[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.processed_files.append(pdf_file)
                    
                except Exception as e:
                    logger.error(f"Error processing {pdf_file}: {e}")
                    results.append({
                        "filename": str(pdf_file),
                        "status": "failed",
                        "error": str(e)
                    })
        
        # Save batch metadata
        self.save_batch_metadata(results)
        
        # Create zip archive
        self.create_zip_archive()
        
        self.end_time = datetime.now()
        self.generate_summary_report(results)
        
        # Clean up temporary directory
        self.cleanup_temp_directory()
        
    def save_batch_metadata(self, results: List[Dict]):
        """
        Save batch processing metadata
        
        Args:
            results: List of processing results
        """
        batch_metadata = {
            "batch_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "processing_start": self.start_time.isoformat(),
            "processing_end": datetime.now().isoformat(),
            "total_files": len(results),
            "successful_files": len([r for r in results if r.get('status') == 'success']),
            "failed_files": len([r for r in results if r.get('status') == 'failed']),
            "files": results
        }
        
        metadata_file = self.output_dir / "batch_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(batch_metadata, f, indent=2, default=str)
            
        self.metadata_store = batch_metadata
        
        logger.info(f"Batch metadata saved to: {metadata_file}")
    
    def create_zip_archive(self):
        """
        Create a zip archive of all processed files and metadata
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = self.output_dir / f"pdf_ocr_archive_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add OCRed PDFs
            ocr_pdf_dir = self.output_dir / "ocr_pdfs"
            for pdf_file in ocr_pdf_dir.glob("*.pdf"):
                zipf.write(pdf_file, arcname=f"ocr_pdfs/{pdf_file.name}")
                
            # Add metadata files
            metadata_dir = self.output_dir / "metadata"
            for metadata_file in metadata_dir.glob("*.json"):
                zipf.write(metadata_file, arcname=f"metadata/{metadata_file.name}")
                
            # Add batch metadata
            batch_metadata = self.output_dir / "batch_metadata.json"
            if batch_metadata.exists():
                zipf.write(batch_metadata, arcname="batch_metadata.json")
                
            # Add log file
            log_file = Path("pdf_ocr_scanner.log")
            if log_file.exists():
                zipf.write(log_file, arcname="processing_log.log")
        
        logger.info(f"Zip archive created: {zip_filename}")
        
        # Verify zip file
        zip_size = zip_filename.stat().st_size
        logger.info(f"Zip file size: {zip_size / (1024*1024):.2f} MB")
    
    def generate_summary_report(self, results: List[Dict]):
        """
        Generate a summary report of the processing
        
        Args:
            results: List of processing results
        """
        total_files = len(results)
        successful = len([r for r in results if r.get('status') == 'success'])
        failed = total_files - successful
        
        total_processing_time = (self.end_time - self.start_time).total_seconds()
        
        summary = f"""
        =========================================
        PDF OCR PROCESSING SUMMARY
        =========================================
        Start Time:      {self.start_time}
        End Time:        {self.end_time}
        Total Duration:  {total_processing_time:.2f} seconds
        
        Total Files:     {total_files}
        Successful:      {successful}
        Failed:          {failed}
        
        Output Directory: {self.output_dir}
        =========================================
        
        Files Processed:
        """
        
        for result in results:
            filename = result.get('metadata', {}).get('filename', 'Unknown')
            status = result.get('status', 'unknown')
            summary += f"\n  - {filename}: {status}"
            
        summary_file = self.output_dir / "processing_summary.txt"
        with open(summary_file, 'w') as f:
            f.write(summary)
            
        print(summary)
        logger.info("Summary report generated")
    
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
    """Main function to run the PDF OCR Scanner"""
    parser = argparse.ArgumentParser(
        description="PDF OCR Scanner with Batch Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single PDF
  python pdf_ocr_scanner.py input.pdf
  
  # Process multiple PDFs
  python pdf_ocr_scanner.py file1.pdf file2.pdf file3.pdf
  
  # Process all PDFs in a directory
  python pdf_ocr_scanner.py /path/to/pdf/directory/
  
  # Specify custom output directory
  python pdf_ocr_scanner.py input.pdf --output ./my_output
  
  # Set number of concurrent workers
  python pdf_ocr_scanner.py input.pdf --workers 4
  
  # Specify Tesseract path
  python pdf_ocr_scanner.py input.pdf --tesseract /usr/bin/tesseract
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
        default="processed_pdfs",
        help="Output directory (default: processed_pdfs)"
    )
    
    parser.add_argument(
        "--temp",
        "-t",
        default="temp",
        help="Temporary directory (default: temp)"
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
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create scanner instance
    scanner = PDFOCRScanner(
        input_paths=args.inputs,
        output_dir=args.output,
        temp_dir=args.temp,
        poppler_path=args.poppler,
        tesseract_path=args.tesseract,
        max_workers=args.workers,
        dpi=args.dpi
    )
    
    try:
        # Start processing
        scanner.process_all_pdfs()
        
        logger.info("Processing completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    # Check for required system components
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
        
    # Run main function
    sys.exit(main())