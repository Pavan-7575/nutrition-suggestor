from __future__ import annotations

import re
from dataclasses import dataclass

from .image_processing import ProcessedImage
from .ollama_generator import OllamaVisionGenerator
from .rag import LocalKnowledgeBase, RetrievedDocument

DISCLAIMER = (
    "Nutrition information and any image-based observations are approximate. An image cannot "
    "reliably establish portions, ingredients, or medical suitability. For medical or precise "
    "dietary guidance, consult a qualified clinician or dietitian."
)

GREETING_PATTERN = re.compile(
    r"^(hi|hello|hey|hlo|helo|hy|hola|greetings|good\s*(morning|afternoon|evening)|howdy|sup|yo|who\s*are\s*you|what\s*can\s*you\s*do|help)[\s!.,?]*$",
    re.IGNORECASE,
)


@dataclass
class NutritionAnalysisService:
    knowledge_base: LocalKnowledgeBase
    generator: OllamaVisionGenerator

    def analyze(self, question: str, image: ProcessedImage | None) -> dict:
        # Deterministic Guardrail: Catch pure greetings without querying heavy RAG or models
        if image is None and GREETING_PATTERN.match(question.strip()):
            return {
                "question": question,
                "assessment": (
                    "Hello! I am NutriVision AI, your evidence-aware nutrition assistant.\n\n"
                    "You can upload or take a photo of a meal or Nutrition Facts label, or ask me "
                    "any question about dietary balance, macronutrients, and healthy eating guidelines."
                ),
                "mode": "conversational",
                "image_received": False,
                "evidence": [],
                "limitations": [],
            }

        evidence = self.knowledge_base.search(question)
        generation = self.generator.generate(
            self._prompt(question, evidence, image is not None), image
        )
        if generation.text:
            assessment, mode = generation.text.strip(), "model-assisted"
        else:
            assessment, mode = (
                self._fallback(
                    evidence, image is not None, generation.unavailable_reason
                ),
                "evidence-only",
            )
        return {
            "question": question,
            "assessment": assessment,
            "mode": mode,
            "image_received": image is not None,
            "evidence": [
                item.citation() | {"excerpt": item.text, "score": item.score}
                for item in evidence
            ],
            "limitations": [DISCLAIMER],
        }

    @staticmethod
    def _prompt(
        question: str, evidence: list[RetrievedDocument], has_image: bool
    ) -> str:
        context = "\n\n".join(
            f"[{item.id}] {item.title}\n{item.text}" for item in evidence
        )
        image_rule = (
            "An image is attached. Identify what is reasonably visible, describe the food items, and label portions as estimates."
            if has_image
            else "No image is attached."
        )
        return f"""You are NutriVision AI, a knowledgeable, friendly, and evidence-aware nutrition assistant.

Guidelines:
- If the user provides a casual greeting, conversational opening (e.g., "hi", "hello", "who are you?"), or asks a general question, respond warmly, politely, and introduce how you can help them analyze meals or nutrition labels. Do NOT dump nutrition facts unless asked.
- When answering specific dietary, food, or nutrition questions, synthesize clear guidance. Cite evidence using [source-id] where applicable.
- Do not invent exact medical advice or calorie counts.
{image_rule}

User Query: {question}

Reference Evidence (use when relevant to the question):
{context or "No relevant evidence retrieved."}
"""

    @staticmethod
    def _fallback(
        evidence: list[RetrievedDocument], has_image: bool, reason: str | None
    ) -> str:
        availability = f" ({reason})" if reason else ""
        intro = (
            "The configured vision model is unavailable"
            if has_image
            else "The configured model is unavailable"
        )
        if not evidence:
            return f"{intro}{availability}. I could not retrieve relevant material from the local knowledge base, so I cannot provide a grounded nutrition conclusion."
        passages = "\n".join(f"- {item.text} [{item.id}]" for item in evidence)
        image_note = (
            " An image was received, but it has not been interpreted because no configured vision model completed."
            if has_image
            else ""
        )
        return f"{intro}{availability}. Here are the retrieved references relevant to your question:{image_note}\n{passages}"
