import unittest
from unittest.mock import patch

from utils.live_news import _dedupe, _normalize
from utils.verification import verify_claim


class LiveEngineeringTests(unittest.TestCase):
    def test_normalize_and_reliability(self):
        item = _normalize({
            "title": "Kheda administration issues update",
            "url": "https://kheda.nic.in/update",
            "description": "Official notice",
            "source": "Kheda District",
            "publishedAt": "2026-10-03T10:00:00Z",
        }, "NewsAPI")
        self.assertEqual(item["domain"], "kheda.nic.in")
        self.assertEqual(item["source_reliability"], "official")

    def test_dedupe(self):
        items = [
            {"title": "Same story", "url": "https://a.example/1"},
            {"title": "Same story", "url": "https://b.example/2"},
            {"title": "Different story", "url": "https://c.example/3"},
        ]
        self.assertEqual(len(_dedupe(items, 10)), 2)

    @patch("utils.live_news.search_live_claim", return_value=[])
    @patch("utils.verification._search_gdelt", return_value=[])
    @patch("utils.verification._google_factcheck_search", return_value=[])
    def test_no_evidence_uses_binary_ml_fallback(self, *_):
        result = verify_claim("Nadiad has a new local event", {"prediction": "fake", "confidence": 96}, city="Nadiad")
        self.assertIn(result["verdict"], {"real", "fake"})
        self.assertEqual(result["decision_basis"], "ml_fallback")
        self.assertFalse(result["evidence_confirmed"])


if __name__ == "__main__":
    unittest.main()
