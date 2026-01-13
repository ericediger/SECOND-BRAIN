"""AI classification service using Claude."""

import json
import re
from pathlib import Path
from typing import Optional

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PROMPTS_PATH, CONFIDENCE_THRESHOLD
from .vault import VaultService


class ClassifierService:
    """Classifies text input and routes to appropriate vault category."""

    CATEGORY_MAP = {
        "people": "People",
        "project": "Projects",
        "idea": "Ideas",
        "admin": "Admin",
        "needs_review": "InboxLog",
    }

    def __init__(self, vault_service: Optional[VaultService] = None):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.vault = vault_service or VaultService()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load classification prompt from file."""
        prompt_path = PROMPTS_PATH / "classification.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _parse_response(self, response_text: str) -> dict:
        """Parse AI response, handling markdown code blocks."""
        text = response_text.strip()

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_match:
            text = json_match.group(1).strip()

        return json.loads(text)

    def classify(self, text: str) -> dict:
        """Classify text and return structured result."""
        message = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": self.prompt_template.replace("{{INPUT}}", text),
                }
            ],
        )

        response_text = message.content[0].text
        result = self._parse_response(response_text)

        return result

    def process_capture(self, text: str) -> dict:
        """Full classification flow: classify, write to vault, create log."""
        source_id = self.vault.generate_source_id()
        classification = self.classify(text)

        category_key = classification.get("type", "needs_review")
        confidence = classification.get("confidence", 0.0)

        if confidence < CONFIDENCE_THRESHOLD:
            category_key = "needs_review"

        category = self.CATEGORY_MAP.get(category_key, "InboxLog")
        name = classification.get("name", "Untitled")
        filename = self.vault.sanitize_filename(name)

        metadata = {
            "type": category_key,
            "source_id": source_id,
            "confidence": confidence,
            **{k: v for k, v in classification.items() if k not in ["type", "confidence"]},
        }

        content = classification.get("body", "")

        if category_key != "needs_review":
            file_path = self.vault.write_file(category, filename, metadata, content)
            destination_file = str(file_path.relative_to(self.vault.vault_path))
            status = "filed"
        else:
            destination_file = "needs_review"
            status = "needs_review"
            self.vault.write_file(
                "InboxLog",
                f"review_{source_id}",
                {
                    "type": "needs_review",
                    "original_text": text,
                    "suggested_type": classification.get("type"),
                    "suggested_name": name,
                    "confidence": confidence,
                    "source_id": source_id,
                },
                text,
            )

        self.vault.write_inbox_log(
            source_id=source_id,
            original_text=text,
            filed_to=category_key,
            destination_name=name,
            destination_file=destination_file,
            confidence=confidence,
            status=status,
        )

        return {
            "success": True,
            "source_id": source_id,
            "category": category,
            "name": name,
            "confidence": confidence,
            "needs_review": category_key == "needs_review",
            "classification": classification,
        }

    def reclassify(self, source_id: str, new_category: str, new_name: str) -> dict:
        """Reclassify a needs_review item to the correct category."""
        review_path = self.vault.get_file_path("InboxLog", f"review_{source_id}")
        post = self.vault.read_file(review_path)

        if not post:
            return {"success": False, "error": "Review item not found"}

        original_text = post.get("original_text", post.content)

        classification = self.classify(original_text)

        classification["type"] = new_category
        classification["name"] = new_name

        category = self.CATEGORY_MAP.get(new_category, "InboxLog")
        filename = self.vault.sanitize_filename(new_name)

        metadata = {
            "type": new_category,
            "source_id": source_id,
            "confidence": 1.0,
            **{k: v for k, v in classification.items() if k not in ["type", "confidence"]},
        }

        content = classification.get("body", original_text)
        file_path = self.vault.write_file(category, filename, metadata, content)

        self.vault.update_file(
            review_path,
            metadata_updates={
                "status": "fixed",
                "fixed_to": new_category,
                "fixed_name": new_name,
            },
        )

        log_path = self.vault.get_file_path("InboxLog", source_id)
        if log_path.exists():
            self.vault.update_file(
                log_path,
                metadata_updates={
                    "status": "fixed",
                    "filed_to": new_category,
                    "destination_name": new_name,
                    "destination_file": str(file_path.relative_to(self.vault.vault_path)),
                },
            )

        return {
            "success": True,
            "source_id": source_id,
            "category": category,
            "name": new_name,
            "file_path": str(file_path),
        }
