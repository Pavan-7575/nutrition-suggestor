import unittest
from io import BytesIO

from PIL import Image

from nutrition_coach import create_app


class RouteTests(unittest.TestCase):
    def setUp(self):
        app = create_app(
            {
                "TESTING": True,
                "WATSONX_URL": None,
                "WATSONX_API_KEY": None,
                "WATSONX_PROJECT_ID": None,
            }
        )
        self.client = app.test_client()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"NutriVision AI", response.data)

    def test_analysis_returns_retrieved_evidence_without_provider(self):
        response = self.client.post(
            "/api/analyze", data={"question": "How can I read a nutrition facts label?"}
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["mode"], "evidence-only")
        self.assertTrue(payload["evidence"])

    def test_analysis_requires_question(self):
        response = self.client.post("/api/analyze", data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("question", response.get_json()["error"]["message"])

    def test_analysis_accepts_a_valid_image(self):
        image_data = BytesIO()
        Image.new("RGB", (2, 2), "green").save(image_data, format="PNG")
        response = self.client.post(
            "/api/analyze",
            data={
                "question": "How should I assess this meal?",
                "image": (BytesIO(image_data.getvalue()), "meal.png", "image/png"),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["image_received"])
