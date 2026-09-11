# ScopeBot

A GitHub bot that bridges **[Black-Pope-77-48](https://github.com/Black-Pope-77-48)** with the live Bitcoin mempool at [mempool.space](https://mempool.space).

## What it does

- Every hour (and on manual run), GitHub Actions fetches recommended fees and mempool size from mempool.space.
- Writes `STATUS.json` + `STATUS.md` in this repo.
- Comments the snapshot on issue #1 (the live bot log).
- A Grok automation also posts when this GitHub account pushes to the [mempool fork](https://github.com/Black-Pope-77-48/mempool).

## Live files

| File | Purpose |
| --- | --- |
| [STATUS.json](./STATUS.json) | Machine-readable snapshot |
| [STATUS.md](./STATUS.md) | Human-readable snapshot |

## Manual run

Actions → **ScopeBot** → Run workflow.

Source API: `https://mempool.space/api/v1/fees/recommended`
