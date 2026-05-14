import hashlib
import math
import re


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{1,}", re.IGNORECASE)


class LocalHashingEmbedder:
    """Small deterministic embedder for the first local RAG slice.

    This is not intended to be a production semantic model. It gives the
    ingestion and retrieval flow a real vector boundary without requiring an
    external embeddings API during the foundation phase.
    """

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    @property
    def model_name(self) -> str:
        return f"local-hashing-v1-{self.dimensions}"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = TOKEN_PATTERN.findall(text.lower())

        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        return normalize(vector)


def normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    return sum(left_value * right_value for left_value, right_value in zip(left, right))
