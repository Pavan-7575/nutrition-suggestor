import unittest

from nutrition_coach.services.rag import LocalKnowledgeBase


class KnowledgeBaseTests(unittest.TestCase):
    def test_retrieves_label_guidance(self):
        results = LocalKnowledgeBase().search(
            "How do I read a Nutrition Facts serving size?"
        )
        self.assertTrue(results)
        self.assertEqual(results[0].id, "fda-label")

    def test_empty_query_returns_no_results(self):
        self.assertEqual(LocalKnowledgeBase().search("..."), [])
