from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    # Cat SAU dau cau (lookbehind) de khong nuot mat dau cham.
    _BOUNDARY = re.compile(r"(?<=[.!?])[ \n]+")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [s.strip() for s in self._BOUNDARY.split(text) if s.strip()]
        if not sentences:
            return []

        size = self.max_sentences_per_chunk
        return [" ".join(sentences[i : i + size]) for i in range(0, len(sentences), size)]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        text = current_text
        if not text:
            return []
        # Base case 1: da vua kich thuoc, khong can cat them.
        if len(text) <= self.chunk_size:
            return [text]
        # Base case 2: het separator (hoac separator rong) -> cat cung theo do dai.
        if not remaining_separators or remaining_separators[0] == "":
            return self._hard_split(text)

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        parts = [p for p in text.split(separator) if p]
        # Base case 3: separator khong xuat hien -> ha xuong separator nho hon.
        if len(parts) <= 1:
            return self._split(text, rest)

        # Di xuong: manh nao con dai hon chunk_size thi cat tiep bang separator nho hon.
        pieces: list[str] = []
        for part in parts:
            if len(part) <= self.chunk_size:
                pieces.append(part)
            else:
                pieces.extend(self._split(part, rest))

        return self._merge(pieces, separator)

    def _hard_split(self, text: str) -> list[str]:
        size = max(1, self.chunk_size)
        return [text[i : i + size] for i in range(0, len(text), size)]

    def _merge(self, pieces: list[str], separator: str) -> list[str]:
        """Gom cac manh nho lien ke lai cho toi sat chunk_size."""
        merged: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue
            if buffer:
                merged.append(buffer)
            buffer = piece
        if buffer:
            merged.append(buffer)
        return merged


class HeadingChunker:
    """Split ATX Markdown sections, repeating their heading on every subchunk.

    chunk_size includes the heading. Raise ValueError if a heading leaves no
    room for its content. Text before the first heading uses recursive splitting.
    """

    _HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+|$)")
    _FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")

    def __init__(self, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        chunks: list[str] = []
        heading = ""
        lines: list[str] = []
        fence = ""
        for line in text.splitlines():
            marker = self._FENCE.match(line)
            if marker:
                run, suffix = marker.groups()
                if not fence:
                    fence = run
                elif run[0] == fence[0] and len(run) >= len(fence) and not suffix.strip():
                    fence = ""
            elif not fence and self._HEADING.match(line):
                chunks.extend(self._split_section(heading, lines))
                heading, lines = line.strip(), []
                continue
            lines.append(line)
        chunks.extend(self._split_section(heading, lines))
        return chunks

    def _split_section(self, heading: str, lines: list[str]) -> list[str]:
        body = "\n".join(lines).strip()
        prefix = heading + "\n\n" if heading and body else heading
        if len(prefix) > self.chunk_size or (body and len(prefix) == self.chunk_size):
            raise ValueError("chunk_size is too small for the section heading")
        if not body:
            return [heading] if heading else []
        parts = RecursiveChunker(chunk_size=self.chunk_size - len(prefix)).chunk(body)
        return [prefix + part for part in parts]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if not norm_a or not norm_b:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=max(1, chunk_size // 10)),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            total = sum(len(c) for c in chunks)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (total / len(chunks)) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
