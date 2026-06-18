import pdfplumber
import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF using pdfplumber, preserving formatting.

    Args:
        pdf_bytes: PDF file as bytes

    Returns:
        Extracted text as string with preserved line breaks, or fallback message for scanned PDFs
    """
    try:
        text_parts = []

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        # Check if any text was extracted
        if not text_parts:
            logger.warning("No text extracted from PDF - likely a scanned document")
            return "Scanned PDF — manual review required"

        # Join pages with double newline to separate them
        full_text = "\n\n".join(text_parts)

        # Clean up excessive blank lines (more than 2 consecutive newlines)
        import re
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)

        return full_text.strip()

    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise Exception(f"Failed to extract text from PDF: {e}")
