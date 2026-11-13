import tempfile
import unittest
from pathlib import Path
from starter.src.models import DocumentPage
from starter.src.ingestion import normalize_text
from starter.src.chunking import fixed_size, by_paragraph
from starter.src.evaluation import evaluate_query
from starter.src.store import QdrantStore

class PipelineTests(unittest.TestCase):
    def test_normalization_preserves_structure_and_is_idempotent(self):
        text = "  A\t B\r\n\r\n\r\n C  "
        cleaned = normalize_text(text)
        self.assertEqual(cleaned, "A B\n\nC")
        self.assertEqual(normalize_text(cleaned), cleaned)

    def test_chunk_offsets_coverage_and_deterministic_ids(self):
        page = DocumentPage("doc", "file.pdf", 9, "Alpha sentence. Beta sentence. " * 40,
                            {"content_group": "sample"})
        for chunks in (fixed_size(page, 80, 10), by_paragraph(page, 80)):
            covered = set()
            for c in chunks:
                start, end = c.metadata["start_char"], c.metadata["end_char"]
                self.assertEqual(c.text, page.text[start:end])
                self.assertLessEqual(len(c.text), 80)
                self.assertEqual(c.page, 9)
                self.assertEqual(c.metadata["content_group"], "sample")
                covered.update(range(start, end))
            self.assertTrue(all(i in covered for i, ch in enumerate(page.text) if not ch.isspace()))
        self.assertEqual([c.chunk_id for c in fixed_size(page,80,10)],
                         [c.chunk_id for c in fixed_size(page,80,10)])

    def test_oversized_unit_is_not_lost(self):
        page = DocumentPage("doc", "x", 1, "x" * 301)
        chunks = by_paragraph(page, 80)
        self.assertEqual("".join(c.text for c in chunks), page.text)

    def test_evidence_requires_correct_page_and_full_quote(self):
        q = {"gold_source_id": "doc", "gold_page": 2, "evidence_quote": "full evidence"}
        wrong_page = {"document_id": "doc", "page": 1, "text": "full evidence"}
        partial = {"document_id": "doc", "page": 2, "text": "full"}
        correct = {"document_id": "doc", "page": 2, "text": "full\nevidence"}
        result = evaluate_query(q, [wrong_page, partial, correct])
        self.assertFalse(result["hit1"])
        self.assertTrue(result["hit3"])
        self.assertEqual(result["evidence_matches"], [False, False, True])

    def test_invalid_overlap(self):
        page = DocumentPage("doc", "x", 1, "abc")
        with self.assertRaises(ValueError):
            fixed_size(page, 3, 3)

    def test_store_reload_filter_persistence_and_removed_chunks(self):
        # Tiny explicit fixture vectors exercise storage only, never used as embeddings.
        with tempfile.TemporaryDirectory() as tmp:
            store = QdrantStore(Path(tmp), 2)
            p1 = DocumentPage("doc", "x", 1, "alpha", {"content_group": "one"})
            p2 = DocumentPage("doc", "x", 2, "beta", {"content_group": "two"})
            chunks = [fixed_size(p, 20, 0)[0] for p in (p1, p2)]
            store.replace("A", chunks, [[1.0,0.0],[0.0,1.0]])
            store.upsert("A", chunks, [[1.0,0.0],[0.0,1.0]])
            self.assertEqual(store.count("A"), 2)
            hits = store.search("A",[1.0,0.0],filters={"content_group":"two"})
            self.assertEqual([h["page"] for h in hits], [2])
            store.replace("A", chunks[:1], [[1.0,0.0]])
            self.assertEqual(store.count("A"), 1)
            store.close()
            store = QdrantStore(Path(tmp), 2)
            self.assertEqual(store.count("A"), 1)
            self.assertEqual(store.search("A",[1.0,0.0])[0]["page"], 1)
            store.close()

if __name__ == "__main__":
    unittest.main()
