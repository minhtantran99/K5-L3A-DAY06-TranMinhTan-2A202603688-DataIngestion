"""Read and normalize source data. TODO: implement functions."""
from pathlib import Path
from .models import DocumentPage
import re
import unicodedata
import logging

from pypdf import PdfReader



def load_pdf(
    path: Path,
    document_id: str,
    source: str,
) -> list[DocumentPage]:
    reader = PdfReader(path)
    pages = []

    for page_number, pdf_page in enumerate(reader.pages, start=1):
        try:
            raw_text = pdf_page.extract_text() or ""
        except Exception:
            logger.exception(
                "Không trích xuất được: file=%s page=%s",
                path,
                page_number,
            )
            raise

        clean_text = normalize_text(raw_text)

        if not clean_text:
            logger.warning(
                "Trang không có text: file=%s page=%s",
                path,
                page_number,
            )

        page = DocumentPage(
            document_id=document_id,
            source=source,
            page=page_number,
            text=clean_text,
            metadata={
                "raw_char_count": len(raw_text),
                "char_count": len(clean_text),
            },
        )

        pages.append(page)

    return pages


def normalize_text(text: str) -> str:
    # Đưa các cách biểu diễn dấu Unicode về dạng thống nhất.
    text = unicodedata.normalize("NFC", text)

    # Thống nhất ký tự xuống dòng.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = []

    for line in text.split("\n"):
        # Gộp khoảng trắng ngang, giữ ranh giới dòng.
        line = re.sub(r"[^\S\n]+", " ", line).strip()
        lines.append(line)

    text = "\n".join(lines)

    # Tối đa một dòng trống giữa các phần nội dung.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


logger = logging.getLogger(__name__)