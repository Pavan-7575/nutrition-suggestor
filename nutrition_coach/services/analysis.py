from __future__ import annotations

from dataclasses import dataclass

from .image_processing import ProcessedImage
from .ollama_generator import OllamaVisionGenerator
from .rag import LocalKnowledgeBase, RetrievedDocument

DISCLAIMER = (
    "Nutrition information and any image-based observations are approximate. An image cannot "
    "reliably establish portions, ingredients, or medical suitability. For medical or precise "
    "dietary guidance, consult a qualified clinician or dietitian."
)


@dataclass
class NutritionAnalysisService:
    knowledge_base: LocalKnowledgeBase
    generator: OllamaVisionGenerator

    def analyze(self, question: str, image: ProcessedImage | None) -> dict:
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
            "An image is attached. Identify only what is reasonably visible, and label every food or portion "
            "conclusion as an estimate. Do not infer exact serving size."
            if has_image
            else "No image is attached; do not claim to have seen a meal or label."
        )
        return f"""You are a cautious nutrition information assistant. Answer the user's question with plain text headings and bullets. Use only the evidence below for factual nutrition guidance; cite each factual statement as [source-id]. If the evidence does not support an answer, say so. Do not diagnose, prescribe treatment, or invent calories, ingredients, portion sizes, citations, or results.
{image_rule}

Question: {question}

Retrieved evidence:
{context or "No relevant evidence was retrieved."}
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
