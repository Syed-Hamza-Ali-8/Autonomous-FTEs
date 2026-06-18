from unittest.mock import MagicMock, patch

from services.pdf_service import extract_text_from_pdf


def test_extract_text_returns_string():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "John Doe\n5 years Python experience"

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [mock_page]
        result = extract_text_from_pdf(b"fake pdf bytes")

    assert isinstance(result, str)
    assert "John Doe" in result


def test_extract_text_joins_multiple_pages():
    page1 = MagicMock()
    page1.extract_text.return_value = "Page 1 content"
    page2 = MagicMock()
    page2.extract_text.return_value = "Page 2 content"

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [page1, page2]
        result = extract_text_from_pdf(b"fake pdf bytes")

    assert "Page 1 content" in result
    assert "Page 2 content" in result


def test_extract_text_handles_scanned_pdf():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [mock_page]
        result = extract_text_from_pdf(b"fake scanned pdf")

    assert "manual review required" in result.lower()


def test_extract_text_collapses_excess_newlines():
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "John Doe\n\n\n\nPython"

    with patch("services.pdf_service.pdfplumber.open") as mock_open:
        mock_open.return_value.__enter__.return_value.pages = [mock_page]
        result = extract_text_from_pdf(b"fake pdf bytes")

    assert "\n\n\n" not in result
    assert "John Doe" in result
