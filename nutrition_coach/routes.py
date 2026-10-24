from __future__ import annotations

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.exceptions import RequestEntityTooLarge

from .services.analysis import NutritionAnalysisService
from .services.image_processing import ImageValidationError, validate_and_encode_image
from .services.rag import LocalKnowledgeBase
from .services.ollama_generator import OllamaVisionGenerator

web = Blueprint("web", __name__)


@web.get("/")
def index():
    return render_template("index.html")


@web.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@web.route("/api/analyze", methods=["OPTIONS"])
def analyze_options():
    return "", 204


@web.post("/api/analyze")
def analyze():
    question = (request.form.get("question") or "").strip()
    if not question:
        return _error_response("Enter a nutrition question or description.", 400)
    if len(question) > 2_000:
        return _error_response("Keep the question under 2,000 characters.", 400)
    uploaded = request.files.get("image")
    image = None
    if uploaded and uploaded.filename:
        try:
            image = validate_and_encode_image(
                uploaded.read(),
                uploaded.mimetype,
                current_app.config["MAX_UPLOAD_BYTES"],
            )
        except ImageValidationError as error:
            return _error_response(str(error), 400)
    service = NutritionAnalysisService(
        LocalKnowledgeBase(host=current_app.config.get("OLLAMA_HOST", "http://localhost:11434")),
        OllamaVisionGenerator(current_app.config),
    )
    return jsonify(service.analyze(question, image))


@web.errorhandler(RequestEntityTooLarge)
def upload_too_large(_error):
    return _error_response("The upload exceeds the configured size limit.", 413)


def _error_response(message: str, status: int):
    return jsonify({"error": {"message": message}}), status
