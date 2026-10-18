# Reproduce

## Analysis (no model needed)

Use Python 3.12 and uv from the repository root.

```bash
make setup     # install from the committed lockfile
make test      # lint, format, strict typing, tests, integrity checks
make analyze   # regenerate traces, case counts, pilot results and report inputs
make report    # build paper/report.pdf (needs pdflatex)
uv run python scripts/verify_seal.py   # recompute the seal record checksums
```

`make analyze` rescores the committed generations in `results/b10-pilot/raw/runs.jsonl` against `data/b10_pilot/gold.jsonl`, using the cached statement similarities in `results/b10-pilot/raw/cosine_cache.json`, so it needs neither the models nor the embedding model.

## Regenerating model outputs

This needs the two GGUF files pinned in `configs/b10_pilot.json` (file names and SHA-256 checksums are listed there) in a local folder, and `llama-cpp-python` 0.3.16.

```bash
uv run python scripts/b10_pilot_collect.py --models-dir /path/to/models \
  --output runs.jsonl --manifest manifest.json --n-gpu-layers -1   # -1 = all layers on GPU; 0 = CPU
```

Use `--only-model` to run one model. Outputs depend on the backend: CPU and GPU runs of the same seed can sample different tokens (see `backend_check` in `results/derived/b10_pilot_summary.json`). The pilot's own runs used a 2-thread CPU container for Qwen and an Apple M1 Max GPU for Mistral.

## Safety

No paid API is used. Never commit `.env` or keys; CI runs gitleaks over the full history.
