"""Loads the recycling knowledge base markdown docs from disk into chunks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from waste_classifier import config


@dataclass
class Chunk:
    doc_id: str
    heading: str
    text: str


def _split_into_chunks(doc_id: str, markdown_text: str) -> list[Chunk]:
    """Split a markdown doc into chunks along '## ' headings."""
    chunks: list[Chunk] = []
    current_heading = doc_id
    current_lines: list[str] = []

    for line in markdown_text.splitlines():
        if line.startswith("## "):
            if current_lines:
                text = "\n".join(current_lines).strip()
                chunks.append(Chunk(doc_id=doc_id, heading=current_heading, text=text))
            current_heading = line.removeprefix("## ").strip()
            current_lines = []
        elif line.startswith("# "):
            current_heading = line.removeprefix("# ").strip()
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append(
            Chunk(doc_id=doc_id, heading=current_heading, text="\n".join(current_lines).strip())
        )

    return [c for c in chunks if c.text]


def load_knowledge_base(directory: Path = config.KNOWLEDGE_BASE_DIR) -> list[Chunk]:
    """Load every markdown file in the knowledge base directory into chunks."""
    chunks: list[Chunk] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks.extend(_split_into_chunks(path.stem, text))
    return chunks
