from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_SRC = REPO_ROOT / "app" / "backend" / "src"
sys.path.append(str(BACKEND_SRC))

from oci_arch_studio_backend.services.embeddings import LocalHashingEmbedder  # noqa: E402


class HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            cleaned = " ".join(data.split())
            if cleaned:
                self.parts.append(cleaned)

    def text(self) -> str:
        return normalize_text(" ".join(self.parts))


def normalize_text(text: str) -> str:
    for marker in ("Copyright ©", "About Oracle Contact Us"):
        if marker in text:
            text = text.split(marker, 1)[0]
    text = re.sub(r"\s+", " ", text)
    text = text.replace("JavaScript must be enabled to correctly display this content", "")
    return text.strip()


def ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except ImportError:
        return None

    return ssl.create_default_context(cafile=certifi.where())


def fetch_text(url: str, timeout: int) -> str:
    request = Request(
        url,
        headers={"User-Agent": "OCI-Architecture-Studio-Ingestion/0.1"},
    )
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        html = response.read().decode("utf-8", errors="ignore")

    parser = HtmlTextExtractor()
    parser.feed(html)
    return parser.text()


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    words = text.split()
    chunks: list[str] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        if end == len(words):
            break
        start = end - chunk_overlap

    return chunks


def load_registry(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return payload["sources"]


def build_index(args: argparse.Namespace) -> dict[str, object]:
    embedder = LocalHashingEmbedder(dimensions=args.dimensions)
    sources = load_registry(args.registry)
    chunks: list[dict[str, object]] = []

    for source in sources:
        fallback_text = source.get("fallback_text", "")
        text = fallback_text
        fetch_status = "fallback"

        if not args.no_fetch:
            try:
                fetched = fetch_text(source["url"], timeout=args.timeout)
                if len(fetched.split()) >= args.min_fetched_words:
                    text = f"{fallback_text} {fetched[: args.max_source_chars]}"
                    fetch_status = "fetched"
            except (TimeoutError, URLError, OSError):
                fetch_status = "fallback"

        for index, chunk in enumerate(
            chunk_text(text, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap),
            start=1,
        ):
            chunks.append(
                {
                    "id": f"{source['id']}::{index}",
                    "source_id": source["id"],
                    "title": source["title"],
                    "url": source["url"],
                    "source_type": source["source_type"],
                    "text": chunk,
                    "embedding": embedder.embed(chunk),
                    "metadata": {
                        "chunk_index": index,
                        "fetch_status": fetch_status,
                    },
                }
            )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "embedding_model": embedder.model_name,
        "dimensions": args.dimensions,
        "source_count": len(sources),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local OCI RAG index.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=REPO_ROOT / "knowledge" / "source_registry.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-rag-index.json",
    )
    parser.add_argument("--dimensions", type=int, default=256)
    parser.add_argument("--chunk-size", type=int, default=180)
    parser.add_argument("--chunk-overlap", type=int, default=30)
    parser.add_argument("--max-source-chars", type=int, default=14000)
    parser.add_argument("--min-fetched-words", type=int, default=120)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--no-fetch", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    index = build_index(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(index, file, indent=2)
        file.write("\n")

    print(
        f"Wrote {index['chunk_count']} chunks from {index['source_count']} sources "
        f"to {args.output}"
    )


if __name__ == "__main__":
    main()
