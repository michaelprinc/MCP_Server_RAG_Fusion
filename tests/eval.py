"""Evaluation utilities for measuring retrieval quality.

The script is intentionally lightweight so it can run both inside
containers and local Windows PowerShell sessions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

try:
    from server.retriever import Retriever
except ImportError:
    Retriever = None  # type: ignore


def load_dataset(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def recall_at_k(relevant: Sequence[str], retrieved: Sequence[str], k: int) -> float:
    if not relevant:
        return 0.0
    head = set(retrieved[:k])
    relevant_set = set(relevant)
    return len(head & relevant_set) / len(relevant_set)


def mean_reciprocal_rank(relevant: Sequence[str], retrieved: Sequence[str]) -> float:
    relevant_set = set(relevant)
    for index, chunk_id in enumerate(retrieved, start=1):
        if chunk_id in relevant_set:
            return 1.0 / index
    return 0.0


def ndcg_at_k(relevant: Sequence[str], retrieved: Sequence[Tuple[str, float]], k: int) -> float:
    if not relevant:
        return 0.0
    gains = []
    for rank, (chunk_id, score) in enumerate(retrieved[:k], start=1):
        gain = 1.0 if chunk_id in relevant else 0.0
        gains.append(gain / np.log2(rank + 1))
    ideal_gains = []
    for rank in range(1, min(k, len(relevant)) + 1):
        ideal_gains.append(1.0 / np.log2(rank + 1))
    dcg = sum(gains)
    idcg = sum(ideal_gains) or 1.0
    return dcg / idcg


def evaluate(
    dataset: Iterable[Dict],
    retriever: "Retriever",
    k: int = 10,
) -> Dict[str, float]:
    recalls: List[float] = []
    mrrs: List[float] = []
    ndcgs: List[float] = []

    for record in dataset:
        query = record["query"]
        expected_chunks = record.get("expected_chunks") or record.get("expected_sections", [])
        results = retriever.retrieve(query=query, intent=record.get("type", "factual"), top_k=k)
        chunk_ids = [chunk.chunk_id for chunk in results]
        scored = [(chunk.chunk_id, chunk.score) for chunk in results]

        recalls.append(recall_at_k(expected_chunks, chunk_ids, k))
        mrrs.append(mean_reciprocal_rank(expected_chunks, chunk_ids))
        ndcgs.append(ndcg_at_k(expected_chunks, scored, k))

    return {
        "recall@k": mean(recalls) if recalls else 0.0,
        "mrr": mean(mrrs) if mrrs else 0.0,
        "ndcg@k": mean(ndcgs) if ndcgs else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval performance.")
    parser.add_argument("--dataset", type=Path, default=Path("tests/eval_dataset.jsonl"))
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    if Retriever is None:
        raise SystemExit("Retriever class not available. Ensure server package is on PYTHONPATH.")

    dataset = load_dataset(args.dataset)
    retriever = Retriever.from_config()  # type: ignore[call-arg]
    metrics = evaluate(dataset, retriever, k=args.k)

    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")


if __name__ == "__main__":
    main()
