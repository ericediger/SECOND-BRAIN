"""Obsidian vault read/write operations."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter

from config import VAULT_PATH, VAULT_CATEGORIES


class VaultService:
    """Handles all Obsidian vault file operations."""

    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = Path(vault_path) if vault_path else VAULT_PATH
        self._ensure_vault_structure()

    def _ensure_vault_structure(self) -> None:
        """Create vault directories if they don't exist."""
        for category in VAULT_CATEGORIES:
            (self.vault_path / category).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Sanitize a string for use as a filename."""
        sanitized = re.sub(r"[^a-zA-Z0-9\s\-_]", "", name)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        return sanitized[:100] if sanitized else "untitled"

    @staticmethod
    def generate_source_id() -> str:
        """Generate a unique source ID based on current timestamp."""
        return datetime.now().strftime("%Y-%m-%d_%H%M%S")

    def get_file_path(self, category: str, filename: str) -> Path:
        """Get full path for a file in a category."""
        return self.vault_path / category / f"{filename}.md"

    def write_file(
        self,
        category: str,
        filename: str,
        metadata: dict,
        content: str = "",
    ) -> Path:
        """Write a markdown file with YAML frontmatter."""
        file_path = self.get_file_path(category, filename)

        metadata["last_touched"] = datetime.now().strftime("%Y-%m-%d")

        post = frontmatter.Post(content, **metadata)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        return file_path

    def read_file(self, file_path: Path) -> Optional[frontmatter.Post]:
        """Read a markdown file and return parsed frontmatter."""
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return frontmatter.load(f)

    def update_file(
        self,
        file_path: Path,
        metadata_updates: Optional[dict] = None,
        content: Optional[str] = None,
    ) -> bool:
        """Update an existing file's metadata and/or content."""
        post = self.read_file(file_path)
        if not post:
            return False

        if metadata_updates:
            for key, value in metadata_updates.items():
                post[key] = value

        post["last_touched"] = datetime.now().strftime("%Y-%m-%d")

        if content is not None:
            post.content = content

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        return True

    def read_vault_contents(self, categories: Optional[list] = None) -> dict:
        """Read all files from specified categories (or all)."""
        if categories is None:
            categories = ["People", "Projects", "Ideas", "Admin"]

        contents = {}

        for category in categories:
            category_path = self.vault_path / category
            if not category_path.exists():
                continue

            contents[category] = []

            for file_path in category_path.glob("*.md"):
                post = self.read_file(file_path)
                if post:
                    contents[category].append({
                        "filename": file_path.stem,
                        "metadata": dict(post.metadata),
                        "content": post.content,
                    })

        return contents

    def write_inbox_log(
        self,
        source_id: str,
        original_text: str,
        filed_to: str,
        destination_name: str,
        destination_file: str,
        confidence: float,
        status: str = "filed",
    ) -> Path:
        """Write an entry to the InboxLog for audit trail."""
        metadata = {
            "type": "inbox_log",
            "original_text": original_text,
            "filed_to": filed_to,
            "destination_name": destination_name,
            "destination_file": destination_file,
            "confidence": confidence,
            "status": status,
            "created": datetime.now().isoformat(),
        }

        return self.write_file("InboxLog", source_id, metadata)

    def get_recent_entries(self, category: str, days: int = 7) -> list:
        """Get entries from a category modified within the last N days."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        entries = []
        category_path = self.vault_path / category

        if not category_path.exists():
            return entries

        for file_path in category_path.glob("*.md"):
            post = self.read_file(file_path)
            if post and post.get("last_touched", "") >= cutoff_str:
                entries.append({
                    "filename": file_path.stem,
                    "metadata": dict(post.metadata),
                    "content": post.content,
                })

        return entries

    def search_vault(self, query: str) -> list:
        """Simple text search across vault files."""
        results = []
        query_lower = query.lower()

        for category in ["People", "Projects", "Ideas", "Admin"]:
            category_path = self.vault_path / category
            if not category_path.exists():
                continue

            for file_path in category_path.glob("*.md"):
                post = self.read_file(file_path)
                if not post:
                    continue

                searchable = (
                    post.content.lower()
                    + " "
                    + str(post.metadata).lower()
                )

                if query_lower in searchable:
                    results.append({
                        "category": category,
                        "filename": file_path.stem,
                        "metadata": dict(post.metadata),
                        "content": post.content,
                    })

        return results

    def find_by_source_id(self, source_id: str) -> Optional[dict]:
        """Find an entry by its source_id across all categories."""
        for category in ["People", "Projects", "Ideas", "Admin"]:
            category_path = self.vault_path / category
            if not category_path.exists():
                continue

            for file_path in category_path.glob("*.md"):
                post = self.read_file(file_path)
                if post and post.get("source_id") == source_id:
                    return {
                        "category": category,
                        "filename": file_path.stem,
                        "file_path": file_path,
                        "metadata": dict(post.metadata),
                        "content": post.content,
                    }

        return None

    def edit_entry(
        self,
        source_id: str,
        new_name: Optional[str] = None,
        new_category: Optional[str] = None,
        metadata_updates: Optional[dict] = None,
    ) -> dict:
        """Edit an existing entry's name, category, or metadata."""
        entry = self.find_by_source_id(source_id)
        if not entry:
            return {"success": False, "error": "Entry not found"}

        old_path = entry["file_path"]
        old_category = entry["category"]
        old_filename = entry["filename"]
        post = self.read_file(old_path)

        if metadata_updates:
            for key, value in metadata_updates.items():
                post[key] = value

        if new_name:
            post["name"] = new_name

        post["last_touched"] = datetime.now().strftime("%Y-%m-%d")

        category_map = {
            "people": "People",
            "project": "Projects",
            "idea": "Ideas",
            "admin": "Admin",
        }
        target_category = category_map.get(new_category, old_category) if new_category else old_category
        target_filename = self.sanitize_filename(new_name) if new_name else old_filename

        if target_category != old_category or target_filename != old_filename:
            new_path = self.get_file_path(target_category, target_filename)
            with open(new_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
            old_path.unlink()
            final_path = new_path
        else:
            with open(old_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
            final_path = old_path

        return {
            "success": True,
            "source_id": source_id,
            "name": post.get("name", target_filename),
            "category": target_category,
            "file_path": str(final_path),
        }

    def delete_entry(self, source_id: str) -> dict:
        """Delete an entry by its source_id."""
        entry = self.find_by_source_id(source_id)
        if not entry:
            return {"success": False, "error": "Entry not found"}

        file_path = entry["file_path"]
        name = entry["metadata"].get("name", entry["filename"])
        category = entry["category"]

        file_path.unlink()

        return {
            "success": True,
            "source_id": source_id,
            "name": name,
            "category": category,
            "message": "Entry deleted",
        }
