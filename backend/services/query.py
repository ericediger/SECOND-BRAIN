"""Natural language query service using Claude."""

from typing import Optional

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, PROMPTS_PATH
from .vault import VaultService


class QueryService:
    """Handles natural language queries against the vault."""

    def __init__(self, vault_service: Optional[VaultService] = None):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.vault = vault_service or VaultService()
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        """Load query prompt from file."""
        prompt_path = PROMPTS_PATH / "query.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _format_vault_contents(self, contents: dict) -> str:
        """Format vault contents as context string for the AI."""
        formatted_parts = []

        for category, entries in contents.items():
            if not entries:
                continue

            formatted_parts.append(f"\n## {category}\n")

            for entry in entries:
                metadata = entry["metadata"]
                content = entry["content"]

                formatted_parts.append(f"### {entry['filename']}")
                formatted_parts.append("**Metadata:**")

                for key, value in metadata.items():
                    if key != "type":
                        formatted_parts.append(f"- {key}: {value}")

                if content.strip():
                    formatted_parts.append(f"\n**Notes:**\n{content}")

                formatted_parts.append("")

        return "\n".join(formatted_parts)

    def query(self, question: str) -> dict:
        """Answer a natural language question about the vault contents."""
        contents = self.vault.read_vault_contents()
        context = self._format_vault_contents(contents)

        prompt = (
            self.prompt_template
            .replace("{{CONTEXT}}", context)
            .replace("{{QUESTION}}", question)
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

        answer = message.content[0].text

        return {
            "success": True,
            "question": question,
            "answer": answer,
        }

    def search_and_query(self, question: str, search_terms: Optional[list] = None) -> dict:
        """Search for specific items and then answer questions about them."""
        if search_terms:
            results = []
            for term in search_terms:
                results.extend(self.vault.search_vault(term))

            if results:
                contents = {}
                for result in results:
                    category = result["category"]
                    if category not in contents:
                        contents[category] = []
                    contents[category].append({
                        "filename": result["filename"],
                        "metadata": result["metadata"],
                        "content": result["content"],
                    })

                context = self._format_vault_contents(contents)
            else:
                context = "(No matching entries found)"
        else:
            contents = self.vault.read_vault_contents()
            context = self._format_vault_contents(contents)

        prompt = (
            self.prompt_template
            .replace("{{CONTEXT}}", context)
            .replace("{{QUESTION}}", question)
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

        return {
            "success": True,
            "question": question,
            "answer": message.content[0].text,
            "search_terms": search_terms,
        }
