"""PDF document processing with hierarchical chunking."""

import fitz  # PyMuPDF
from typing import List, Dict, Any
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import config


@dataclass
class PDFPage:
    """Represents a single PDF page with metadata."""
    text: str
    page_number: int
    source_file: str
    has_tables: bool = False


class PDFProcessor:
    """Processes PDF documents with page-aware chunking."""
    
    def __init__(self):
        """Initialize the PDF processor with chunking strategy."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
        )
    
    def extract_pages(self, pdf_path: str) -> List[PDFPage]:
        """Extract text from PDF with page-level metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PDFPage objects
        """
        pages = []
        source_filename = pdf_path.split("/")[-1]
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text
                text = page.get_text("text")
                
                # Detect tables (basic heuristic: look for tab characters or grid patterns)
                has_tables = "\t" in text or self._detect_table_structure(text)
                
                # Clean text
                text = self._clean_text(text)
                
                if text.strip():  # Only add non-empty pages
                    pages.append(PDFPage(
                        text=text,
                        page_number=page_num + 1,  # 1-indexed for user display
                        source_file=source_filename,
                        has_tables=has_tables
                    ))
            
            doc.close()
            
        except Exception as e:
            raise ValueError(f"Error processing PDF {pdf_path}: {str(e)}")
        
        return pages
    
    def _detect_table_structure(self, text: str) -> bool:
        """Detect if text contains table-like structures.
        
        Args:
            text: Page text
            
        Returns:
            True if table structure detected
        """
        lines = text.split("\n")
        if len(lines) < 3:
            return False
        
        # Check for aligned columns (multiple spaces in consistent positions)
        aligned_count = 0
        for line in lines[:10]:  # Check first 10 lines
            if "  " in line:  # Multiple spaces
                aligned_count += 1
        
        return aligned_count > 3
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text.
        
        Args:
            text: Raw text from PDF
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace while preserving structure
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]  # Remove empty lines
        return "\n".join(lines)
    
    def create_chunks(self, pages: List[PDFPage]) -> List[Document]:
        """Create hierarchical chunks from pages.
        
        Strategy:
        - Each page is a parent context
        - Create semantic child chunks within each page
        - Preserve page boundaries for accurate citations
        
        Args:
            pages: List of extracted PDF pages
            
        Returns:
            List of LangChain Document objects with metadata
        """
        chunks = []
        chunk_id = 0
        
        for page in pages:
            # For short pages, keep as single chunk
            if len(page.text) <= config.MIN_CHUNK_SIZE:
                chunks.append(Document(
                    page_content=page.text,
                    metadata={
                        "source_file": page.source_file,
                        "page_number": page.page_number,
                        "chunk_id": chunk_id,
                        "has_tables": page.has_tables,
                        "chunk_type": "full_page"
                    }
                ))
                chunk_id += 1
                continue
            
            # For longer pages, create semantic chunks
            page_chunks = self.text_splitter.create_documents(
                texts=[page.text],
                metadatas=[{
                    "source_file": page.source_file,
                    "page_number": page.page_number,
                    "has_tables": page.has_tables,
                }]
            )
            
            # Add chunk IDs and type
            for chunk in page_chunks:
                chunk.metadata["chunk_id"] = chunk_id
                chunk.metadata["chunk_type"] = "semantic_chunk"
                chunks.append(chunk)
                chunk_id += 1
        
        return chunks
    
    def process_pdf(self, pdf_path: str) -> List[Document]:
        """Complete PDF processing pipeline.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of processed document chunks
        """
        pages = self.extract_pages(pdf_path)
        chunks = self.create_chunks(pages)
        return chunks