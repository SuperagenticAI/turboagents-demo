# TurboAgents Demo

A small standalone demo repo for trying TurboAgents outside the main source tree.

## What this repo shows

- standalone TurboAgents with LanceDB
- standalone TurboAgents with SurrealDB
- optional SuperOptiX framework integrations using DSPy, Pydantic AI, and OpenAI Agents SDK

## Why the demo scripts are committed

The standalone demo code is checked into this repo on purpose.

That is better than generating it on demand because:

- users can read the exact code before they run anything
- the demo stays stable across recordings and launch posts
- the repo works as a public reference implementation, not just a generator
- the runner script can stay focused on execution and summary output

## Prerequisites

Before running this demo, make sure these local services are up:

- Ollama is running
- Docker is running
- a SurrealDB container is available on port `8000`
- the Ollama model `qwen3.5:9b` is already pulled if you want the SuperOptiX integrations

Useful checks:

```bash
ollama list
curl http://127.0.0.1:11434/api/tags
docker ps
```

## Quick start

```bash
git clone https://github.com/SuperagenticAI/turboagents-demo.git
cd turboagents-demo
uv sync
uv run python scripts/run_demo.py
```

That runs the standalone LanceDB and SurrealDB demos and writes a summary to `results/summary.md`.

## Optional SuperOptiX integrations

For the full integration path, install the extra and run:

```bash
uv sync --extra superoptix
uv run python scripts/run_demo.py --with-superoptix
```

This will bootstrap a local SuperOptiX workspace inside this repo, pull the packaged demo agents, compile them, and run:

- DSPy
- Pydantic AI
- OpenAI Agents SDK

## Links

- TurboAgents docs: https://superagenticai.github.io/turboagents/
- TurboAgents repo: https://github.com/SuperagenticAI/turboagents
- TurboAgents website: https://super-agentic.ai/turboagents
- SuperOptiX integration page: https://superoptix.ai/turboagents
- SuperOptiX repo: https://github.com/SuperagenticAI/superoptix
