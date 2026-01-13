"""Flask server for Second Brain API."""

import os
import sys
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

sys.path.insert(0, str(Path(__file__).parent))

from config import HOST, PORT, VAULT_PATH
from services import (
    VaultService,
    ClassifierService,
    TranscriberService,
    QueryService,
    DigestService,
)

app = Flask(__name__, static_folder="../frontend")
CORS(app)

vault_service = VaultService()
classifier_service = ClassifierService(vault_service)
transcriber_service = TranscriberService()
query_service = QueryService(vault_service)
digest_service = DigestService(vault_service)


@app.route("/")
def index():
    """Serve the frontend."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/capture", methods=["POST"])
def capture():
    """Classify text and write to vault."""
    data = request.get_json()

    if not data or "text" not in data:
        return jsonify({"success": False, "error": "Missing 'text' field"}), 400

    text = data["text"].strip()

    if not text:
        return jsonify({"success": False, "error": "Empty text"}), 400

    try:
        result = classifier_service.process_capture(text)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    """Transcribe audio file to text."""
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided"}), 400

    audio_file = request.files["audio"]

    if audio_file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    try:
        audio_bytes = audio_file.read()
        filename = audio_file.filename or "audio.webm"

        result = transcriber_service.transcribe(audio_bytes, filename)

        if not result["success"]:
            return jsonify(result), 400

        if request.form.get("classify", "true").lower() == "true":
            classification = classifier_service.process_capture(result["text"])
            result["classification"] = classification

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/query", methods=["POST"])
def query():
    """Answer natural language questions about the vault."""
    data = request.get_json()

    if not data or "question" not in data:
        return jsonify({"success": False, "error": "Missing 'question' field"}), 400

    question = data["question"].strip()

    if not question:
        return jsonify({"success": False, "error": "Empty question"}), 400

    try:
        search_terms = data.get("search_terms")
        if search_terms:
            result = query_service.search_and_query(question, search_terms)
        else:
            result = query_service.query(question)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/fix", methods=["POST"])
def fix():
    """Reclassify a misclassified item."""
    data = request.get_json()

    required_fields = ["source_id", "category", "name"]
    for field in required_fields:
        if not data or field not in data:
            return jsonify({"success": False, "error": f"Missing '{field}' field"}), 400

    try:
        result = classifier_service.reclassify(
            source_id=data["source_id"],
            new_category=data["category"],
            new_name=data["name"],
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/edit", methods=["POST"])
def edit():
    """Edit an entry's name or category without re-running AI classification."""
    data = request.get_json()

    if not data or "source_id" not in data:
        return jsonify({"success": False, "error": "Missing 'source_id' field"}), 400

    try:
        result = vault_service.edit_entry(
            source_id=data["source_id"],
            new_name=data.get("name"),
            new_category=data.get("category"),
            metadata_updates=data.get("metadata"),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/delete", methods=["POST"])
def delete():
    """Delete an entry from the vault."""
    data = request.get_json()

    if not data or "source_id" not in data:
        return jsonify({"success": False, "error": "Missing 'source_id' field"}), 400

    try:
        result = vault_service.delete_entry(source_id=data["source_id"])
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/digest/daily", methods=["GET"])
def daily_digest():
    """Generate daily digest."""
    try:
        result = digest_service.generate_daily_digest()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/digest/weekly", methods=["GET"])
def weekly_digest():
    """Generate weekly digest."""
    try:
        result = digest_service.generate_weekly_digest()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/vault/stats", methods=["GET"])
def vault_stats():
    """Get vault statistics."""
    try:
        contents = vault_service.read_vault_contents()
        stats = {
            "people": len(contents.get("People", [])),
            "projects": len(contents.get("Projects", [])),
            "ideas": len(contents.get("Ideas", [])),
            "admin": len(contents.get("Admin", [])),
            "total": sum(len(v) for v in contents.values()),
        }
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/vault/recent", methods=["GET"])
def recent_entries():
    """Get recent vault entries."""
    try:
        days = request.args.get("days", 7, type=int)
        entries = {
            "People": vault_service.get_recent_entries("People", days),
            "Projects": vault_service.get_recent_entries("Projects", days),
            "Ideas": vault_service.get_recent_entries("Ideas", days),
            "Admin": vault_service.get_recent_entries("Admin", days),
        }
        return jsonify({"success": True, "entries": entries, "days": days})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "success": True,
        "status": "healthy",
        "vault_path": str(VAULT_PATH),
    })


if __name__ == "__main__":
    print(f"Starting Second Brain server on http://{HOST}:{PORT}")
    print(f"Vault path: {VAULT_PATH}")
    app.run(host=HOST, port=PORT, debug=True)
