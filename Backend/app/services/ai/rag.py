import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "knowledge"


def _chunk(text: str, size: int = 400, overlap: int = 60) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - overlap
    return chunks


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class KnowledgeBase:
    def __init__(self, docs_dir: Path = DOCS_DIR):
        self.chunks: list[tuple[str, str]] = []  # (source, chunk)
        if docs_dir.exists():
            for path in sorted(docs_dir.glob("**/*")):
                if path.suffix in (".md", ".txt"):
                    try:
                        for chunk in _chunk(path.read_text(encoding="utf-8", errors="ignore")):
                            self.chunks.append((path.name, chunk))
                    except OSError:
                        continue

    def retrieve(self, query: str, k: int = 3) -> list[str]:
        q = _tokens(query)
        if not q:
            return []
        scored = []
        for source, chunk in self.chunks:
            score = len(q & _tokens(chunk))
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]
