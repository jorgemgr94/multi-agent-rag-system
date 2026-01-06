"""Document loading from the knowledge base."""

import re
from pathlib import Path
from typing import Any

from app.logging_config import get_logger
from app.schemas.document import (
    CompanySize,
    DealOutcome,
    DocType,
    Document,
    DocumentMetadata,
)

logger = get_logger(__name__)


class DocumentLoader:
    """Loads documents from the knowledge base directory."""

    def __init__(self, knowledge_base_path: Path):
        self.base_path = knowledge_base_path

    def load_all(self) -> list[Document]:
        """Load all markdown documents from knowledge base."""
        documents = []

        if not self.base_path.exists():
            logger.warning(f"Knowledge base not found: {self.base_path}")
            return documents

        for md_file in self.base_path.rglob("*.md"):
            try:
                doc = self.load_file(md_file)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Failed to load {md_file}: {e}")

        logger.info(f"Loaded {len(documents)} documents from {self.base_path}")
        return documents

    def load_file(self, file_path: Path) -> Document | None:
        """Load a single markdown file."""
        content = file_path.read_text(encoding="utf-8")
        if not content.strip():
            return None

        # Extract metadata from file path and content
        metadata = self._extract_metadata(file_path, content)

        return Document(content=content, metadata=metadata)

    def _extract_metadata(self, file_path: Path, content: str) -> DocumentMetadata:
        """Extract metadata from file path and frontmatter."""
        relative_path = file_path.relative_to(self.base_path)
        parts = relative_path.parts

        # Determine doc_type from directory
        doc_type = self._infer_doc_type(parts[0] if parts else "")

        # Generate doc_id from filename
        doc_id = file_path.stem

        # Extract metadata from frontmatter or content
        extracted = self._parse_frontmatter(content)

        return DocumentMetadata(
            doc_id=doc_id,
            doc_type=doc_type,
            industry=extracted.get("industry"),
            company_size=self._parse_company_size(extracted.get("company_size")),
            deal_value=extracted.get("deal_value"),
            outcome=self._parse_outcome(extracted.get("outcome")),
            date=None,  # Could parse from content if needed
            tags=extracted.get("tags", []),
            source_file=str(relative_path),
        )

    def _infer_doc_type(self, directory: str) -> DocType:
        """Infer document type from directory name."""
        mapping = {
            "deals": DocType.DEAL,
            "proposals": DocType.PROPOSAL,
            "competitors": DocType.COMPETITOR,
            "products": DocType.PRODUCT,
            "case_studies": DocType.CASE_STUDY,
            "industries": DocType.INDUSTRY,
        }
        return mapping.get(directory, DocType.PRODUCT)

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        """Parse YAML-like frontmatter from markdown."""
        # Simple key-value extraction from content
        metadata: dict[str, Any] = {}

        # Look for patterns like "**Industry:** Healthcare"
        patterns = {
            "industry": r"\*\*Industry:\*\*\s*(\w+)",
            "company_size": r"\*\*Size:\*\*\s*([\w-]+)",
            "deal_value": r"\*\*Deal Value:\*\*\s*\$?([\d,]+)",
            "outcome": r"\*\*Outcome:\*\*\s*(\w+)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if key == "deal_value":
                    value = int(value.replace(",", ""))
                metadata[key] = value

        # Extract tags from content
        tags_match = re.search(r"\*\*Tags:\*\*\s*(.+)", content)
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split(",")]
            metadata["tags"] = tags

        return metadata

    def _parse_company_size(self, value: str | None) -> CompanySize | None:
        if not value:
            return None
        value_lower = value.lower().replace(" ", "-")
        for size in CompanySize:
            if size.value == value_lower:
                return size
        return None

    def _parse_outcome(self, value: str | None) -> DealOutcome | None:
        if not value:
            return None
        value_lower = value.lower()
        for outcome in DealOutcome:
            if outcome.value == value_lower:
                return outcome
        return None
