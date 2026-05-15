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
sys.path.append(str(Path(__file__).resolve().parent))

from release_intelligence import normalize_release_item  # noqa: E402


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
    text = re.sub(r"JavaScript must be enabled to correctly display this content", " ", text)
    text = re.sub(r"Copyright\s+©.*?$", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\s+", " ", text)
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
        headers={"User-Agent": "OCI-Architecture-Studio-Release-Ingestion/0.1"},
    )
    with urlopen(request, timeout=timeout, context=ssl_context()) as response:
        html = response.read().decode("utf-8", errors="ignore")
    parser = HtmlTextExtractor()
    parser.feed(html)
    return parser.text()


def load_registry(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)["sources"]


def service_domain(service: str, text: str) -> str:
    haystack = f"{service} {text}".lower()
    if any(token in haystack for token in ("vault", "secret", "security", "iam", "cloud guard")):
        return "security"
    if any(token in haystack for token in ("object storage", "block volume", "file storage", "backup")):
        return "storage"
    if any(token in haystack for token in ("load balancer", "dns", "vcn", "network")):
        return "networking"
    if any(token in haystack for token in ("database", "mysql", "autonomous")):
        return "database"
    if any(token in haystack for token in ("cost", "budget", "billing", "price")):
        return "cost"
    if any(token in haystack for token in ("disaster", "replication", "failover", "availability")):
        return "resilience"
    return "general"


def impact_tags(text: str) -> list[str]:
    normalized = text.lower()
    tags: list[str] = []
    keyword_map = {
        "security": ("security", "secret", "vault", "key", "iam", "policy"),
        "architecture": ("load balancer", "network", "storage", "database", "compute", "availability"),
        "migration": ("migration", "compatibility", "s3", "api", "import", "export"),
        "cost": ("cost", "budget", "billing", "limit", "capacity"),
        "dr": ("disaster", "replication", "backup", "failover", "recovery"),
        "observability": ("logging", "monitoring", "metrics", "alarm", "audit"),
    }
    for tag, keywords in keyword_map.items():
        if any(keyword in normalized for keyword in keywords):
            tags.append(tag)
    return tags or ["general"]


def service_change_tags(text: str) -> list[str]:
    normalized = text.lower()
    tags: list[str] = []
    keyword_map = {
        "api-compatibility": ("api", "compatibility", "s3", "endpoint", "url"),
        "naming": ("renamed", "now", "name", "secret management"),
        "limits": ("limit", "quota", "capacity"),
        "availability": ("available", "availability", "region"),
        "security": ("security", "secret", "vault", "key", "iam", "policy"),
        "migration": ("migration", "import", "export", "compatibility"),
        "pricing-capacity": ("cost", "budget", "billing", "capacity"),
        "deprecation": ("deprecated", "retired", "removed", "end of support"),
        "observability": ("logging", "monitoring", "metrics", "alarm", "audit"),
    }
    for tag, keywords in keyword_map.items():
        if any(keyword in normalized for keyword in keywords):
            tags.append(tag)
    return tags or ["general"]


def parse_release_date(text: str) -> str | None:
    match = re.search(
        r"Release Date:\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})",
        text,
    )
    return match.group(1) if match else None


def parse_services(text: str) -> list[str]:
    match = re.search(r"Services?:\s*([^.]+)", text)
    if not match:
        return []
    return [service.strip() for service in re.split(r",| and ", match.group(1)) if service.strip()]


def split_release_items(text: str, max_items: int) -> list[str]:
    release_blocks = re.findall(
        r"([A-Z][^.]{8,180}\.\s+Services?:\s*[^.]+\.\s+Release Date:\s*"
        r"[A-Z][a-z]+\s+\d{1,2},\s+\d{4}\.[\s\S]*?)"
        r"(?=\s+[A-Z][^.]{8,180}\.\s+Services?:|$)",
        text,
    )
    if release_blocks:
        items = [normalize_text(candidate) for candidate in release_blocks if len(candidate.split()) >= 10]
        return items[:max_items]

    candidates = re.split(
        r"(?=\b[A-Z][A-Za-z0-9/()&+.-]+(?:\s+[A-Z][A-Za-z0-9/()&+.-]+){0,8}\s+"
        r"(?:is|are|now|supports|adds|updated|improved|available)\b)",
        text,
    )
    items = [normalize_text(candidate) for candidate in candidates if len(candidate.split()) >= 10]
    return items[:max_items]


def classify_release_item(item: str, source: dict[str, str], index: int, ingested_at: str) -> dict[str, object]:
    title = item.split(". ", 1)[0][:140]
    services = parse_services(item)
    primary_service = services[0] if services else "Oracle Cloud Infrastructure"
    tags = impact_tags(item)
    release = {
        "id": f"{source['id']}::{index}",
        "source_id": source["id"],
        "title": title,
        "source_url": source["url"],
        "source_type": source["source_type"],
        "release_date": parse_release_date(item),
        "service": primary_service,
        "services": services,
        "service_domain": service_domain(primary_service, item),
        "service_change_tags": service_change_tags(item),
        "impact_tags": tags,
        "impact_level": "review" if any(tag in tags for tag in ("security", "dr", "migration", "architecture")) else "informational",
        "architecture_affecting": any(tag in tags for tag in ("architecture", "migration", "dr", "security", "cost")),
        "knowledge_scope": "current",
        "valid_from": parse_release_date(item),
        "valid_to": None,
        "trust_level": source.get("trust_level", "official"),
        "ingested_timestamp": ingested_at,
        "summary": item[:800],
    }
    return normalize_release_item(release)


def build_release_snapshot(args: argparse.Namespace) -> dict[str, object]:
    ingested_at = datetime.now(UTC).isoformat()
    releases: list[dict[str, object]] = []
    sources = load_registry(args.registry)

    for source in sources:
        text = source.get("fallback_text", "")
        fetch_status = "fallback"
        if not args.no_fetch:
            try:
                fetched = fetch_text(source["url"], timeout=args.timeout)
                if len(fetched.split()) >= args.min_fetched_words:
                    text = fetched[: args.max_source_chars]
                    fetch_status = "fetched"
            except (TimeoutError, URLError, OSError):
                fetch_status = "fallback"

        for index, item in enumerate(split_release_items(text, args.max_items_per_source), start=1):
            release = classify_release_item(item, source, index, ingested_at)
            release["fetch_status"] = fetch_status
            releases.append(release)

    return {
        "generated_at": ingested_at,
        "snapshot_scope": "current",
        "source_count": len(sources),
        "release_count": len(releases),
        "releases": releases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local OCI release snapshot.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=REPO_ROOT / "knowledge" / "release_source_registry.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "knowledge" / "snapshots" / "oci-release-snapshot.json",
    )
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--min-fetched-words", type=int, default=100)
    parser.add_argument("--max-source-chars", type=int, default=30000)
    parser.add_argument("--max-items-per-source", type=int, default=12)
    parser.add_argument("--no-fetch", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = build_release_snapshot(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as file:
        json.dump(snapshot, file, indent=2)
        file.write("\n")
    print(
        f"Wrote {snapshot['release_count']} release item(s) from "
        f"{snapshot['source_count']} source(s) to {args.output}"
    )


if __name__ == "__main__":
    main()
