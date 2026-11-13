"""Deterministic page-bounded chunks with character offsets."""
import hashlib
import re
from .models import Chunk, DocumentPage

def make_chunk(page, start, end, method):
    while start < end and page.text[start].isspace():
        start += 1
    while end > start and page.text[end - 1].isspace():
        end -= 1
    text = page.text[start:end]
    identity = f"{page.document_id}:{page.page}:{method}:{start}:{end}:{text}"
    return Chunk(hashlib.sha256(identity.encode()).hexdigest(), page.document_id,
                 page.source, page.page, text,
                 {**page.metadata, "start_char": start, "end_char": end, "method": method})

def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError("Require size > overlap >= 0")
    chunks, start = [], 0
    while start < len(page.text):
        end = min(start + size, len(page.text))
        chunk = make_chunk(page, start, end, f"fixed:{size}:{overlap}")
        if chunk.text:
            chunks.append(chunk)
        if end == len(page.text):
            break
        start += size - overlap
    return chunks

def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Pack paragraphs/sentences, preserving original text and offsets."""
    if max_size <= 0:
        raise ValueError("max_size must be positive")
    boundaries = [0]
    boundaries += [m.end() for m in re.finditer(r"\n\s*\n|(?<=[.!?;])\s+", page.text)]
    boundaries.append(len(page.text))
    units = []
    for start, end in zip(boundaries, boundaries[1:]):
        while end - start > max_size:
            cut = page.text.rfind(" ", start + max_size // 2, start + max_size + 1)
            if cut <= start:
                cut = start + max_size
            units.append((start, cut))
            start = cut
        if start < end:
            units.append((start, end))
    spans = []
    for start, end in units:
        if spans and end - spans[-1][0] <= max_size:
            spans[-1] = (spans[-1][0], end)
        else:
            spans.append((start, end))
    return [c for start, end in spans
            if (c := make_chunk(page, start, end, f"paragraph:{max_size}")).text]
