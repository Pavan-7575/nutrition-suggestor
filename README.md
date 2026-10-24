# NutriVision AI — Evidence-Aware Nutrition Coach

A clinical, multimodal nutrition web application built on **Python Flask**, **Hybrid RAG (BGE-M3 + Okapi BM25)**, and local vision intelligence using **Ollama** (`minicpm-v` / `llava`).

It accepts a dietary question alongside an optional meal photo or Nutrition Facts label, retrieves authoritative clinical benchmarks, and synthesizes evidence-grounded dietary observations.

The assistant is deliberately conservative: food photos cannot establish exact portion weights, hidden oils, calories, allergens, or medical suitability. Every assessment cites its authoritative sources (USDA, FDA, WHO) and attaches a clinical limitation notice.

---

## Key Features

- **Multimodal Visual Understanding**: Reads meal photos and Nutrition Facts labels using locally hosted vision LLMs (default: `minicpm-v` or `llava`) via Ollama.
- **Hybrid RAG Retrieval**: Combines dense semantic vector search via **BGE-M3** with lexical keyword matching via **Okapi BM25**, fused through **Reciprocal Rank Fusion (RRF)**.
- **Clinical Evidence Grounding**: Answers are grounded directly against verified excerpts from:
  - **USDA FoodData Central**
  - **Dietary Guidelines for Americans**
  - **FDA Nutrition Facts Label Guidance**
  - **World Health Organization (WHO) Healthy Diet Guidelines**
- **Modern Restyled Web UI**: Dark-mode interface with live preview, real-time status feedback, and evidence cards.
- **RESTful API**: Standardized JSON endpoint (`POST /api/analyze`) for programmatic access.
- **100% Local & Private**: Runs completely on your machine with Ollama. Zero external API keys, zero token fees, zero cloud image leakage.
- **CI Automated Quality**: Continuous integration via GitHub Actions enforcing strict linting (`ruff`) and automated unit tests.

---

## Architecture

```text
User Input (Image + Dietary Question)
       │
       ├──► Hybrid RAG Search (nutrition_coach/services/rag.py)
       │      ├─► BM25 Lexical Keyword Matching
       │      ├─► BGE-M3 Semantic Vector Embeddings (via Ollama)
       │      └─► Reciprocal Rank Fusion (RRF) ──► Top Cited Passages
       │
       └──► Local Vision Generator (nutrition_coach/services/ollama_generator.py)
              └─► Ollama API (minicpm-v / llava) + Grounded System Prompt
                     │
                     ▼
       Structured Assessment + Evidence Citations + Safety Disclaimer
```

---

## Prerequisites

1. **Python 3.11+**
2. **Ollama installed**: [Download Ollama](https://ollama.com/download)
   - Pull the vision model:
     ```powershell
     ollama run minicpm-v
     ```
   - Pull the embedding model for Hybrid RAG:
     ```powershell
     ollama pull bge-m3
     ```

---

## Installation & Running

1. **Clone the repository**:
   ```powershell
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd "nutrition suggestor"
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   python -m pip install -r requirements-dev.txt
   ```

4. **Launch the Flask application**:
   ```powershell
   python app.py
   ```

Open your browser at **`http://localhost:5000`**.

---

## REST API Specification

### `POST /api/analyze`
Accepts `multipart/form-data`:

| Field | Type | Description |
| :--- | :--- | :--- |
| `question` | String *(required)* | Dietary query (up to 2,000 characters). |
| `image` | File *(optional)* | JPEG, PNG, or WebP image (up to 8 MB). |

#### Example Request:
```bash
curl -F "question=How balanced is this meal?" -F "image=@meal.jpg" http://localhost:5000/api/analyze
```

#### Example Response:
```json
{
  "question": "How balanced is this meal?",
  "assessment": "The meal contains salmon and vegetables. While protein and fiber are present, exact portion sizes and calorie totals cannot be determined from an image alone...",
  "mode": "model-assisted",
  "image_received": true,
  "evidence": [
    {
      "id": "dietary-guidelines",
      "title": "Dietary Guidelines for Americans: dietary patterns",
      "url": "https://www.dietaryguidelines.gov/",
      "excerpt": "Healthy dietary patterns emphasize vegetables, fruits, whole grains...",
      "score": 0.033
    }
  ],
  "limitations": [
    "Nutrition information and any image-based observations are approximate. An image cannot reliably establish portions, ingredients, or medical suitability. For medical or precise dietary guidance, consult a qualified clinician or dietitian."
  ]
}
```

---

## Testing & Quality Checks

Run linting checks and test suites locally:

```powershell
# Run Ruff linter (enforced by GitHub Actions CI)
python -m ruff check .

# Run unit tests
python -m unittest discover -s tests -v
```

---

## Project Structure

```text
├── app.py                          # Flask application entry point
├── nutrition_coach/
│   ├── config.py                   # Environment settings & application configuration
│   ├── routes.py                   # Web and JSON API routes
│   ├── data/
│   │   └── knowledge_base.json     # Curated USDA, FDA, and WHO reference documents
│   └── services/
│       ├── analysis.py             # Orchestration between RAG and vision generation
│       ├── image_processing.py      # Image validation and base64 encoding
│       ├── ollama_generator.py      # Ollama API client (minicpm-v / llava)
│       └── rag.py                  # Hybrid RAG engine (Okapi BM25 + BGE-M3 + RRF)
├── templates/                      # Flask HTML5 template
├── static/                         # Polished CSS styles and client-side JavaScript
├── tests/                          # Automated unit tests
├── requirements.txt                # Runtime dependencies
└── requirements-dev.txt            # Development & CI dependencies (ruff)
```

---

## Medical & Clinical Disclaimer

NutriVision AI provides educational nutrition information grounded in public health standards. It does not provide medical diagnoses, treatment plans, or clinical prescriptions. Visual observations are approximate estimates and should not replace advice from a registered dietitian or healthcare provider.
