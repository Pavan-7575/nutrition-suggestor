from __future__ import annotations

import base64
import os
from io import BytesIO
from PIL import Image

import gradio as gr
from dotenv import load_dotenv

from nutrition_coach.services.analysis import NutritionAnalysisService
from nutrition_coach.services.image_processing import ProcessedImage
from nutrition_coach.services.ollama_generator import OllamaVisionGenerator
from nutrition_coach.services.rag import LocalKnowledgeBase

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "minicpm-v")

# Initialize services
kb = LocalKnowledgeBase(host=OLLAMA_HOST)
generator = OllamaVisionGenerator({"OLLAMA_HOST": OLLAMA_HOST, "OLLAMA_MODEL": OLLAMA_MODEL})
analysis_service = NutritionAnalysisService(kb, generator)


def analyze_meal(image: Image.Image | None, question: str):
    if not question.strip():
        question = "What foods are in this image, and how balanced is this meal?"

    processed_image = None
    if image is not None:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        b64_str = base64.b64encode(img_bytes).decode("ascii")
        processed_image = ProcessedImage(b64_str, "image/jpeg")

    # Run RAG + Vision Analysis
    result = analysis_service.analyze(question, processed_image)

    assessment = result.get("assessment", "No assessment generated.")
    mode = result.get("mode", "")

    # Format Evidence Cards
    evidence_items = result.get("evidence", [])
    evidence_html = ""
    if evidence_items:
        evidence_html = '<div class="evidence-section"><div class="section-badge">📚 CLINICAL GROUNDING (RAG)</div>'
        for item in evidence_items:
            evidence_html += f"""
            <div class="evidence-card">
                <a class="evidence-link" href="{item['url']}" target="_blank">🔗 {item['title']}</a>
                <p class="evidence-excerpt">{item['excerpt']}</p>
            </div>
            """
        evidence_html += "</div>"

    # Limitations
    limitations = result.get("limitations", [])
    notice_html = ""
    if limitations:
        notice_html = f"""
        <div class="notice-card">
            <strong>⚠️ Clinical Notice:</strong> {limitations[0]}
        </div>
        """

    # Model badge
    badge_html = f"""
    <div class="badge-bar">
        <span class="badge badge-accent">● {OLLAMA_MODEL.upper()}</span>
        <span class="badge badge-subtle">{mode.upper()}</span>
        <span class="badge badge-subtle">HYBRID RAG (BGE-M3 + BM25)</span>
    </div>
    """

    content_html = f"""
    {badge_html}
    <div class="assessment-card">
        <h3>🥗 Nutrition Assessment</h3>
        <div class="assessment-body">{assessment.replace(chr(10), '<br>')}</div>
    </div>
    {evidence_html}
    {notice_html}
    """

    return content_html


# Custom Modern Styling (Deep charcoal, warm ember orange, sleek glass cards)
custom_css = """
/* Global Styles */
.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Header Banner */
.hero-header {
    background: linear-gradient(135deg, #181922 0%, #202230 100%);
    border: 1px solid rgba(255, 94, 30, 0.2);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    margin-bottom: 2rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.hero-tag {
    display: inline-block;
    background: rgba(255, 94, 30, 0.15);
    color: #ff5e1e;
    border: 1px solid rgba(255, 94, 30, 0.35);
    padding: 0.35rem 1rem;
    border-radius: 50px;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
}

.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0.5rem;
}

.hero-title span {
    background: linear-gradient(135deg, #ff7e40 0%, #ff5e1e 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: #9ca3af;
    font-size: 1.05rem;
    max-width: 650px;
    margin: 0 auto;
    line-height: 1.5;
}

/* Primary Action Button */
button.primary {
    background: linear-gradient(135deg, #ff5e1e 0%, #e04e14 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.85rem 1.75rem !important;
    box-shadow: 0 4px 16px rgba(255, 94, 30, 0.35) !important;
    transition: all 0.2s ease !important;
}

button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 22px rgba(255, 94, 30, 0.5) !important;
}

/* Result Cards */
.badge-bar {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}

.badge {
    padding: 0.3rem 0.75rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}

.badge-accent {
    background: #ff5e1e;
    color: #ffffff;
}

.badge-subtle {
    background: rgba(255, 255, 255, 0.08);
    color: #d1d5db;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.assessment-card {
    background: #171924;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
}

.assessment-card h3 {
    margin-top: 0;
    color: #ff7e40;
    font-size: 1.2rem;
    margin-bottom: 0.75rem;
}

.assessment-body {
    color: #e5e7eb;
    font-size: 1rem;
    line-height: 1.6;
}

.evidence-section {
    margin-top: 1.25rem;
}

.section-badge {
    font-size: 0.8rem;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 0.75rem;
    letter-spacing: 0.05em;
}

.evidence-card {
    background: rgba(56, 189, 248, 0.04);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.evidence-link {
    color: #38bdf8;
    font-weight: 600;
    text-decoration: none;
    font-size: 0.95rem;
}

.evidence-link:hover {
    text-decoration: underline;
}

.evidence-excerpt {
    color: #94a3b8;
    font-size: 0.85rem;
    margin: 0.35rem 0 0 0;
    line-height: 1.45;
}

.notice-card {
    background: rgba(251, 146, 60, 0.06);
    border-left: 4px solid #f97316;
    padding: 0.9rem 1.2rem;
    border-radius: 0 10px 10px 0;
    font-size: 0.85rem;
    color: #fdba74;
    margin-top: 1.25rem;
    line-height: 1.5;
}
"""

with gr.Blocks(title="NutriVision AI", css=custom_css, theme=gr.themes.Base()) as demo:
    # Header Banner
    gr.HTML(
        """
        <div class="hero-header">
            <span class="hero-tag">✨ EVIDENCE-GROUNDED MULTIMODAL AI</span>
            <h1 class="hero-title">NutriVision <span>AI Coach</span></h1>
            <p class="hero-subtitle">
                Inspect meal composition, portion balance, and clinical dietary standards with 
                Hybrid RAG (USDA, FDA, WHO) and on-device vision intelligence.
            </p>
        </div>
        """
    )

    with gr.Row():
        # Left Panel: User Inputs
        with gr.Column(scale=5):
            image_input = gr.Image(
                type="pil", 
                label="📸 Upload Meal / Nutrition Facts Photo",
                height=320,
            )
            question_input = gr.Textbox(
                lines=3,
                label="💬 Your Question / Goal",
                placeholder="e.g., Identify the foods on this plate and tell me if it qualifies as a balanced meal...",
                value="What foods are in this image, and how balanced is this meal?"
            )
            submit_btn = gr.Button("🔍 Analyze Meal & Ground Evidence", variant="primary", size="lg")

            gr.Examples(
                examples=[
                    ["What foods are in this image, and how balanced is this meal?"],
                    ["Estimate the portion size and key macronutrients."],
                    ["Does this meal satisfy the WHO daily fruit and vegetable recommendations?"],
                    ["What should I check on this Nutrition Facts label according to FDA standards?"],
                ],
                inputs=[question_input],
                label="💡 Quick Prompts"
            )

        # Right Panel: Analysis & Evidence
        with gr.Column(scale=6):
            output_html = gr.HTML(
                value="""
                <div class="assessment-card" style="text-align: center; padding: 3rem 1.5rem; color: #6b7280;">
                    <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">🥗 Ready for meal analysis</p>
                    <p style="font-size: 0.9rem;">Upload a meal photo or ask a nutrition question to see model findings and clinical RAG citations.</p>
                </div>
                """
            )

    submit_btn.click(
        fn=analyze_meal,
        inputs=[image_input, question_input],
        outputs=output_html,
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
