"""LocalFileResearcher — reads .md, .txt, .pdf files from the local filesystem."""
from __future__ import annotations

import re
import warnings
from pathlib import Path
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
EXCLUDED_DIRS = {".obsidian", ".git", "node_modules", ".trash"}


class LocalFileResearcher:
    """Reads local Markdown, TXT, and PDF files for LLM synthesis.

    Implements the Researcher Protocol (ingest / search / analyze / generate).
    No external services — all synthesis is left to the calling LLM.
    """

    def __init__(self) -> None:
        self._indexed_content: dict[str, str] = {}  # file_path → text content

    # ── Private helpers ────────────────────────────────────────────────────────

    def _scan_directory(self, directory: Path) -> list[Path]:
        """Recursively find supported files, skipping excluded directories."""
        results: list[Path] = []
        for item in directory.iterdir():
            if item.is_dir():
                if item.name in EXCLUDED_DIRS:
                    continue
                results.extend(self._scan_directory(item))
            elif item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS:
                results.append(item)
        return results

    def _strip_yaml_frontmatter(self, text: str) -> str:
        """Remove YAML frontmatter block (--- ... ---) from Markdown text."""
        pattern = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
        return pattern.sub("", text).lstrip()

    def _read_file(self, path: Path) -> str | None:
        """Read a file and return its text content, or None to skip."""
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            warnings.warn(
                f"Skipping {path}: exceeds 10 MB size limit.", stacklevel=3
            )
            return None

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            return self._read_pdf(path)

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            warnings.warn(
                f"Skipping {path}: non-UTF-8 encoding.", stacklevel=3
            )
            return None

        if suffix == ".md":
            text = self._strip_yaml_frontmatter(text)

        return text

    def _read_pdf(self, path: Path) -> str | None:
        """Extract text from a PDF file using pdfplumber (optional dependency)."""
        try:
            import pdfplumber
        except ImportError:
            warnings.warn(
                "pdfplumber is not installed. Install with: pip install khanote[pdf]",
                stacklevel=4,
            )
            return None

        try:
            with pdfplumber.open(path) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            text = "\n".join(pages).strip()
            if not text:
                warnings.warn(
                    f"Skipping {path}: no extractable text (image-only PDF?).",
                    stacklevel=4,
                )
                return None
            return text
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"Skipping {path}: PDF read error — {exc}", stacklevel=4)
            return None

    # ── Protocol methods ───────────────────────────────────────────────────────

    def ingest(self, sources: list[str]) -> dict:
        """Ingest files or directories into indexed_content.

        Sources can be file paths or directory paths. Directories are scanned
        recursively, excluding .obsidian/, .git/, node_modules/, .trash/.

        Returns:
            {"source_count": int, "indexed_ids": list[str]}
        """
        self._indexed_content.clear()

        paths_to_read: list[Path] = []
        for source in sources:
            p = Path(source)
            if p.is_dir():
                paths_to_read.extend(self._scan_directory(p))
            elif p.is_file():
                if p.suffix.lower() in SUPPORTED_EXTENSIONS:
                    paths_to_read.append(p)
                else:
                    warnings.warn(
                        f"Skipping {p}: unsupported file type '{p.suffix}'.",
                        stacklevel=2,
                    )
            # Non-existent paths are silently skipped (ingest is best-effort)

        for file_path in paths_to_read:
            text = self._read_file(file_path)
            if text is not None:
                self._indexed_content[str(file_path)] = text

        indexed_ids = list(self._indexed_content.keys())
        return {"source_count": len(indexed_ids), "indexed_ids": indexed_ids}

    def search(self, query: str) -> list[dict]:
        """Keyword search across indexed content.

        Returns results sorted by descending score.
        Each result: {"id": str, "title": str, "excerpt": str, "score": float}
        Score = fraction of query words found in document (0.0–1.0).
        """
        if not query.strip() or not self._indexed_content:
            return []

        query_words = list(re.findall(r"\w+", query.lower()))
        results: list[dict] = []

        for file_id, content in self._indexed_content.items():
            content_lower = content.lower()

            # Substring match: query word appears anywhere in content
            matched = [w for w in query_words if w in content_lower]
            if not matched:
                continue

            score = len(matched) / len(query_words)

            # Title: first non-empty line, stripped of Markdown heading markers
            first_line = next(
                (line.strip().lstrip("#").strip() for line in content.splitlines() if line.strip()),
                Path(file_id).stem,
            )

            # Excerpt: first 200 chars of content around first match
            first_match_word = matched[0]
            match_pos = content_lower.find(first_match_word)
            start = max(0, match_pos - 50)
            excerpt = content[start : start + 200].replace("\n", " ").strip()

            results.append(
                {
                    "id": file_id,
                    "title": first_line,
                    "excerpt": excerpt,
                    "score": round(score, 3),
                }
            )

        results.sort(key=lambda r: r["score"], reverse=True)
        return results

    def analyze(self, query: str | None = None) -> dict:
        """Return all indexed content structured for LLM synthesis.

        Returns:
            {"summary": str, "sections": dict[str, str], "raw": list[dict]}
        """
        if not self._indexed_content:
            return {"summary": "No content indexed.", "sections": {}, "raw": []}

        sections: dict[str, str] = {}
        raw: list[dict] = []
        for file_id, content in self._indexed_content.items():
            name = Path(file_id).stem
            sections[name] = content[:500]  # excerpt per file
            raw.append({"id": file_id, "content": content})

        file_count = len(self._indexed_content)
        summary = f"Indexed {file_count} file{'s' if file_count != 1 else ''}."
        if query:
            summary += f" Query context: {query}"

        return {"summary": summary, "sections": sections, "raw": raw}

    def generate(self, type: str, **kwargs) -> str:  # noqa: A002
        """Format indexed content as a Markdown summary for LLM consumption.

        Returns a Markdown string listing each indexed file with its content excerpt.
        """
        if not self._indexed_content:
            return "*(No local files indexed.)*"

        lines: list[str] = [f"# Local File Content ({len(self._indexed_content)} files)\n"]
        for file_id, content in self._indexed_content.items():
            name = Path(file_id).name
            lines.append(f"## {name}\n")
            lines.append(content[:1000])
            if len(content) > 1000:
                lines.append("\n*(truncated)*")
            lines.append("\n")

        return "\n".join(lines)
