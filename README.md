# Nutrition Coach

A small Flask-based multimodal nutrition assistant. It accepts a nutrition question and an optional food or Nutrition Facts-label image, retrieves relevant local evidence, and can send the grounded prompt plus image to IBM watsonx.ai's Llama 4 Maverick vision model.

It is deliberately conservative: food photos do not establish exact portions, ingredients, calories, allergies, or medical suitability. Every response includes source links and a limitation notice.

## Features

- Responsive browser interface with question input, image selection, preview, loading and error states.
- Validated JPEG, PNG and WebP uploads (8 MB by default); files are processed in memory and never persisted.
- Local, deterministic retrieval over a cited knowledge base in `nutrition_coach/data/knowledge_base.json`.
- Evidence-grounded watsonx vision prompt when `WATSONX_*` settings are present.
- Useful evidence-only fallback when no credential, package, or provider response is available—never a fake vision result.
- Structured JSON API response with assessment, evidence, response mode, and limitations.

## Architecture

```text
Browser -> Flask /api/analyze -> input validation -> local retrieval
                                             |             |
                                             |             +-> citations/excerpts
                                             +-> watsonx Llama 4 Vision (optional)
                                                           |
                                                     structured browser response
```

The retriever uses a transparent TF-IDF-style lexical scorer to avoid an additional database service for this small starter corpus. The service boundary in `nutrition_coach/services/rag.py` is the replacement point for embeddings and a vector store when a larger approved corpus becomes available.

## Requirements

- Python 3.11+
- A watsonx.ai API key and project ID only for live model-assisted analysis

## Install and run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`. Configure the `WATSONX_*` variables in `.env` before launching for live Llama 4 Maverick calls. Without them, the app still demonstrates validation, retrieval, citations, and its explicit evidence-only fallback.

On macOS/Linux, activate the environment with `source .venv/bin/activate`.

## API

`POST /api/analyze` is `multipart/form-data`:

- `question` — required, up to 2,000 characters
- `image` — optional JPEG, PNG, or WebP image

Example:

```bash
curl -F "question=How do I compare serving sizes on this label?" -F "image=@label.png" http://127.0.0.1:5000/api/analyze
```

The response has `assessment`, `mode`, `evidence`, `limitations`, and `image_received`. `mode: evidence-only` indicates the model was not used; it is not an image analysis result.

## Knowledge and RAG workflow

The bundled corpus contains brief, attributed guidance from USDA FoodData Central, the Dietary Guidelines for Americans, FDA Nutrition Facts label guidance, and WHO. It is intentionally not a food-composition database. To add approved knowledge, append an object with `id`, `title`, `text`, and `source_url` to `nutrition_coach/data/knowledge_base.json`; citations are generated only from these entries.

For production, review and version the corpus, add an embedding/vector backend behind `LocalKnowledgeBase`, and evaluate retrieval quality before relying on the app for user-facing advice.

## Testing and quality checks

```powershell
ruff check .
python -m unittest discover -s tests -v
```

The tests cover retrieval, image validation, API validation, the web route, and the credential-free retrieval fallback. They do not invoke watsonx.ai or validate real model output.

## Project layout

```text
app.py                         Application entry point
nutrition_coach/routes.py      Web and JSON API routes
nutrition_coach/services/      Image validation, retrieval, generation, orchestration
nutrition_coach/data/          Curated, cited knowledge source excerpts
templates/ and static/         Browser experience
tests/                         Unit and route tests
```

## Safety and limitations

- This is nutrition information, not medical diagnosis or treatment.
- Image observations and portions must be treated as estimates.
- A model response can be incomplete or wrong; inspect the linked evidence.
- Do not upload sensitive health information or images you do not have permission to use.
- The local corpus is small, so many questions should result in a limited or no-grounded-answer response.

## GitHub readiness

`.env` is ignored, `.env.example` documents every setting, tests do not require secrets, and GitHub Actions runs linting and tests. No license was added because none was selected by the project owner.
