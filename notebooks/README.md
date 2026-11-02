# notebooks

Agent experiments: model comparisons, threshold sweeps, prompt variants.
**Experiments live here; `api/src/saklolo/agents/` stays inference-only.**

| Notebook | Question it answers |
|---|---|
| `01-model-comparison.ipynb` | Which Bedrock model should the fast path use? |
| `02-dedupe-threshold-sweep.ipynb` | Which similarity threshold merges duplicates without merging neighbors? |
| `03-prompt-variants.ipynb` | Does a prompt change improve triage without losing Critical recall? |

`lab.py` holds the shared helpers. `prompts/` holds prompt variants under test.

## Setup
```bash
cd api && uv sync --group notebooks
```
In VS Code, open a notebook and pick the kernel `api/.venv`. The notebooks read
`.env` at the repo root like the API does.

## Rules
- **Dev or calibration split only.** `lab.run()` refuses the eval split; eval is
  for final reporting through `make eval`.
- **Every paid call is cached** in `eval/cache/` (gitignored). Re-running a
  notebook after changing only a threshold or a plot costs nothing. Delete the
  cache to force fresh calls.
- **Mind the bill.** Nova models are billed as Bedrock (usually covered by AWS
  credits). Claude on Bedrock is billed through AWS Marketplace and may not be.
- **Numbers stay provisional** until the dev split has human labels; `lab`
  prints a warning when it falls back to generator intent.
- **Clear outputs before committing** so diffs stay readable and no long
  message dumps land in git.

## Promoting a result
An experiment changes nothing on its own. To adopt a winner:
1. Copy the setting into `.env.example` / `config.py`, or the prompt into
   `api/src/saklolo/agents/prompts/`.
2. Run `make eval` (ask first: it costs money) and paste the before/after table
   in the PR (`run-evals` skill).
3. Record anything architectural as an ADR (`write-adr` skill).
