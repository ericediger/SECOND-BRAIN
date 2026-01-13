"""Digest generation service for daily and weekly summaries."""

from datetime import datetime
from typing import Optional

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PROMPTS_PATH
from .vault import VaultService


class DigestService:
    """Generates daily and weekly digest summaries."""

    def __init__(self, vault_service: Optional[VaultService] = None):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.vault = vault_service or VaultService()

    def _load_prompt(self, prompt_name: str) -> str:
        """Load a digest prompt from file."""
        prompt_path = PROMPTS_PATH / f"{prompt_name}.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _format_entries(self, entries: dict) -> str:
        """Format entries for digest context."""
        formatted_parts = []

        for category, items in entries.items():
            if not items:
                continue

            formatted_parts.append(f"\n## {category}\n")

            for item in items:
                metadata = item["metadata"]
                formatted_parts.append(f"### {item['filename']}")

                for key, value in metadata.items():
                    if key not in ["type", "source_id"]:
                        formatted_parts.append(f"- {key}: {value}")

                if item["content"].strip():
                    formatted_parts.append(f"\n{item['content'][:500]}")

                formatted_parts.append("")

        return "\n".join(formatted_parts)

    def generate_daily_digest(self) -> dict:
        """Generate a daily digest of recent activity."""
        entries = {
            "People": self.vault.get_recent_entries("People", days=1),
            "Projects": self.vault.get_recent_entries("Projects", days=1),
            "Ideas": self.vault.get_recent_entries("Ideas", days=1),
            "Admin": self.vault.get_recent_entries("Admin", days=1),
        }

        context = self._format_entries(entries)

        if not context.strip():
            return {
                "success": True,
                "digest": "No new entries in the last 24 hours.",
                "date": datetime.now().strftime("%Y-%m-%d"),
            }

        prompt_template = self._load_prompt("daily_digest")
        prompt = (
            prompt_template
            .replace("{{CONTEXT}}", context)
            .replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
        )

        message = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        digest_text = message.content[0].text

        digest_filename = f"daily_{datetime.now().strftime('%Y-%m-%d')}"
        self.vault.write_file(
            "_digests",
            digest_filename,
            {
                "type": "digest",
                "digest_type": "daily",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "entries_count": sum(len(v) for v in entries.values()),
            },
            digest_text,
        )

        return {
            "success": True,
            "digest": digest_text,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "entries_count": sum(len(v) for v in entries.values()),
        }

    def generate_weekly_digest(self) -> dict:
        """Generate a weekly digest of activity."""
        entries = {
            "People": self.vault.get_recent_entries("People", days=7),
            "Projects": self.vault.get_recent_entries("Projects", days=7),
            "Ideas": self.vault.get_recent_entries("Ideas", days=7),
            "Admin": self.vault.get_recent_entries("Admin", days=7),
        }

        context = self._format_entries(entries)

        if not context.strip():
            return {
                "success": True,
                "digest": "No entries in the last 7 days.",
                "week_ending": datetime.now().strftime("%Y-%m-%d"),
            }

        prompt_template = self._load_prompt("weekly_digest")
        prompt = (
            prompt_template
            .replace("{{CONTEXT}}", context)
            .replace("{{WEEK_ENDING}}", datetime.now().strftime("%Y-%m-%d"))
        )

        message = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        digest_text = message.content[0].text

        digest_filename = f"weekly_{datetime.now().strftime('%Y-%m-%d')}"
        self.vault.write_file(
            "_digests",
            digest_filename,
            {
                "type": "digest",
                "digest_type": "weekly",
                "week_ending": datetime.now().strftime("%Y-%m-%d"),
                "entries_count": sum(len(v) for v in entries.values()),
            },
            digest_text,
        )

        return {
            "success": True,
            "digest": digest_text,
            "week_ending": datetime.now().strftime("%Y-%m-%d"),
            "entries_count": sum(len(v) for v in entries.values()),
        }
