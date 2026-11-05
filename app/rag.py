from __future__ import annotations

import re
import json
import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .models import ManualChunk, RetrievalQuery


@dataclass(frozen=True)
class RetrievalResult:
    chunk: ManualChunk
    score: float


class ManualIndex:
    """Índice pequeño y reproducible; puede reemplazarse por pgvector."""

    def __init__(self, chunks: list[ManualChunk] | None = None) -> None:
        self.chunks = chunks or []

    def add(self, chunk: ManualChunk) -> None:
        self.chunks.append(chunk)

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "ManualIndex":
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(f"Corpus inexistente: {source}")
        chunks: list[ManualChunk] = []
        with source.open(encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                citation = item["id"]
                chunks.append(
                    ManualChunk(
                        equipment_tag="B-101" if citation.startswith("TX350-") else "general",
                        manufacturer="Trimax Industrial",
                        document=item["doc"],
                        section=citation,
                        citation=citation,
                        text=item["texto"],
                        vigente=item.get("vigente", True),
                    )
                )
        return cls(chunks)

    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        terms = self._tokens(query.question)
        candidates = [
            chunk
            for chunk in self.chunks
            if chunk.vigente
            and (query.equipment_tag is None or chunk.equipment_tag == query.equipment_tag)
        ]
        document_frequency: dict[str, int] = {}
        tokenized: list[tuple[ManualChunk, list[str]]] = []
        for chunk in candidates:
            tokens = self._tokens(
                f"{chunk.text} {chunk.section} {chunk.document}"
            )
            tokenized.append((chunk, tokens))
            for term in set(tokens):
                document_frequency[term] = document_frequency.get(term, 0) + 1
        ranked = []
        average_length = (
            sum(len(tokens) for _, tokens in tokenized) / len(tokenized)
            if tokenized else 1
        )
        total_documents = len(tokenized) or 1
        for chunk, tokens in tokenized:
            counts = {term: tokens.count(term) for term in set(tokens)}
            score = 0.0
            for term in terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                idf = math.log(
                    1 + (total_documents - document_frequency.get(term, 0) + 0.5)
                    / (document_frequency.get(term, 0) + 0.5)
                )
                denominator = frequency + 1.4 * (
                    1 - 0.75 + 0.75 * len(tokens) / average_length
                )
                score += idf * frequency * 2.4 / denominator
            if score:
                score += self._document_priority(chunk.document) * 0.01
                ranked.append(RetrievalResult(chunk, float(score)))
        return sorted(
            ranked, key=lambda item: (-item.score, item.chunk.citation)
        )[: query.k]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = unicodedata.normalize("NFD", text.casefold())
        normalized = "".join(
            char for char in normalized
            if unicodedata.category(char) != "Mn"
        )
        return re.findall(r"[a-z0-9]+", normalized)

    @staticmethod
    def _document_priority(document: str) -> int:
        if document.endswith("-D"):
            return 1
        if document.endswith("-C"):
            return -1
        return 0

    @staticmethod
    def evaluate(
        search: "ManualIndex", suite: list[dict[str, object]], k: int = 5
    ) -> dict[str, float]:
        hits = 0
        reciprocal = 0.0
        for item in suite:
            query = RetrievalQuery(
                question=str(item["question"]),
                equipment_tag=item.get("equipment_tag"),  # type: ignore[arg-type]
                k=k,
            )
            expected = str(item["expected_section"])
            results = search.search(query)
            positions = [
                index + 1
                for index, result in enumerate(results)
                if result.chunk.section == expected
            ]
            if positions:
                hits += 1
                reciprocal += 1 / positions[0]
        total = len(suite) or 1
        return {"hit_at_k": hits / total, "recall_at_k": hits / total}

    def evaluate_official(
        self, retrieval_json: str | Path, k_values: tuple[int, ...] = (1, 3, 5, 10)
    ) -> dict[str, object]:
        source = Path(retrieval_json)
        if not source.is_file():
            raise FileNotFoundError(f"Suite de retrieval inexistente: {source}")
        suite = json.loads(source.read_text(encoding="utf-8"))
        rows: list[dict[str, float | str]] = []
        for item in suite:
            results = self.search(
                RetrievalQuery(question=item["pregunta"], k=max(max(k_values), 20))
            )
            citations = [result.chunk.citation for result in results]
            relevant = set(item["relevantes"])
            distractors = set(item["distractores"])
            row: dict[str, float | str] = {"id": item["id"]}
            for k in k_values:
                top = citations[:k]
                row[f"hit@{k}"] = float(bool(relevant.intersection(top)))
                row[f"recall@{k}"] = len(relevant.intersection(top)) / len(relevant)
                row[f"distractor@{k}"] = float(
                    any(
                        citation in distractors
                        and not any(relevant_citation in top[:index] for relevant_citation in relevant)
                        for index, citation in enumerate(top)
                    )
                )
            rows.append(row)
        total = {
            metric: round(
                sum(float(row[metric]) for row in rows) / len(rows), 3
            )
            for metric in rows[0]
            if metric != "id"
        }
        return {"n": len(rows), "total": total, "preguntas": rows}


def build_context(results: list[RetrievalResult], max_chunks: int = 5) -> str:
    return "\n\n".join(
        f"[{result.chunk.citation}] {result.chunk.text}"
        for result in results[:max_chunks]
    )
