# TurboAgents Demo

A small standalone demo repo for trying TurboAgents outside the main source tree.

## What this repo shows

- standalone TurboAgents with LanceDB
- standalone TurboAgents with SurrealDB
- optional SuperOptiX framework integrations using an existing local validation workspace

## Why the demo scripts are committed

The standalone demo code is checked into this repo on purpose.

That is better than generating it on demand because:

- users can read the exact code before they run anything
- the demo stays stable across recordings and launch posts
- the repo works as a public reference implementation, not just a generator
- the runner script can stay focused on execution and summary output

## Quick start

```bash
git clone https://github.com/SuperagenticAI/turboagents-demo.git
cd turboagents-demo
uv sync
uv run python scripts/run_demo.py
```

That runs the standalone LanceDB and SurrealDB demos and writes a summary to `results/summary.md`.

## Optional SuperOptiX integrations

If you already have a local SuperOptiX source checkout and validation workspace, run:

```bash
export SUPEROPTIX_ROOT=/path/to/superoptix
export TURBOAGENTS_ROOT=/path/to/turboagents
export SUPEROPTIX_VALIDATION_ROOT=/path/to/superoptix-validation
uv run python scripts/run_demo.py --with-superoptix
```

This will also run:

- DSPy
- Pydantic AI
- OpenAI Agents SDK

Required environment variables for `--with-superoptix`:

- `SUPEROPTIX_ROOT`
- `TURBOAGENTS_ROOT`
- `SUPEROPTIX_VALIDATION_ROOT`

## Links

- TurboAgents docs: https://superagenticai.github.io/turboagents/
- TurboAgents repo: https://github.com/SuperagenticAI/turboagents
- TurboAgents website: https://super-agentic.ai/turboagents
- SuperOptiX integration page: https://superoptix.ai/turboagents
- SuperOptiX repo: https://github.com/SuperagenticAI/superoptix
