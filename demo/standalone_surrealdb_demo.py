from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np

from turboagents.rag import TurboSurrealDB

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"


def style(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


async def main() -> None:
    demo_dir = Path(__file__).resolve().parent
    (demo_dir / "data").mkdir(parents=True, exist_ok=True)
    dim = 64

    index = TurboSurrealDB(
        url="ws://127.0.0.1:8000/rpc",
        namespace="superoptix",
        database="knowledge",
        dim=dim,
        bits=3.5,
        metric="COSINE",
        auth={"username": "root", "password": "secret"},
    )

    vectors = np.zeros((3, dim), dtype=np.float32)
    vectors[0, :4] = [0.00, 1.00, 0.00, 0.00]
    vectors[1, :4] = [0.08, 0.90, 0.02, 0.00]
    vectors[2, :4] = [0.92, 0.05, 0.03, 0.00]
    metadata = [
        {
            "title": "SurrealDB Retrieval",
            "summary": "TurboAgents can rerank SurrealDB candidates with the same compressed index path.",
            "token": "NEON-FOX-742",
        },
        {
            "title": "Grounded Answering",
            "summary": "SuperOptiX uses this seeded token for retrieval grounding checks.",
            "token": "GROUND-742",
        },
        {
            "title": "LanceDB Integration",
            "summary": "The local LanceDB demo shows the standalone vector-store path.",
            "token": "LANCE-TURBO-314",
        },
    ]

    await index.create_collection("turboagents_live_demo", dim=dim)
    await index.add(vectors, metadata=metadata)

    query = np.zeros(dim, dtype=np.float32)
    query[:4] = [0.0, 1.0, 0.0, 0.0]
    results = await index.search(query, k=2, rerank_top=3)

    print(style("TurboAgents standalone SurrealDB demo", BOLD, CYAN))
    print(style("TurboQuant-style path: 3.5-bit compressed index with reranked SurrealDB candidates", YELLOW))
    for i, result in enumerate(results, start=1):
        meta = result["metadata"]
        print(
            style(
                f"{i}. {meta['title']} | score={result['score']:.4f} | token={meta['token']}",
                GREEN,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
