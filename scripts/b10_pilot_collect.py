"""Collect B10 pilot generations with a local llama.cpp runtime.

Standalone on purpose: it runs in a separate environment that has llama-cpp-python
installed, and it imports nothing from the trusttrace package. It writes one JSON
record per generation, compatible with trusttrace.experiment_analysis.ExtractionRun.
The run is resumable: finished run IDs in the output file are skipped.
"""

import argparse
import datetime
import hashlib
import json
import platform
import re
import time
from pathlib import Path

FIELDS = ("statement", "trustor", "trustee", "scope", "condition", "fit_criterion", "evidence_span")


def parse_output(raw: str) -> tuple[str, list[dict[str, str]], str | None]:
    """Apply the frozen parsing rule. Returns (status, predictions, error)."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    if start < 0:
        return "invalid-output", [], "no JSON object found"
    depth, in_str, esc, end = 0, False, False, -1
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end < 0:
        return "invalid-output", [], "unbalanced JSON object"
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        return "invalid-output", [], f"JSON decode error: {exc.msg}"
    if not isinstance(obj, dict) or set(obj) != {"requirements"}:
        return "invalid-output", [], "top-level object must contain only 'requirements'"
    reqs = obj["requirements"]
    if not isinstance(reqs, list):
        return "invalid-output", [], "'requirements' is not a list"
    preds: list[dict[str, str]] = []
    for item in reqs:
        if not isinstance(item, dict) or set(item) != set(FIELDS):
            return "invalid-output", [], "requirement has missing or extra fields"
        if not all(isinstance(item[k], str) and item[k].strip() for k in FIELDS):
            return "invalid-output", [], "requirement field empty or not a string"
        preds.append({k: item[k].strip() for k in FIELDS})
    return "valid", preds, None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, default=Path("configs/b10_pilot.json"))
    ap.add_argument("--digests", type=Path, default=Path("data/b10_pilot/source_digests.json"))
    ap.add_argument("--models-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--only-model", default=None)
    ap.add_argument(
        "--n-gpu-layers",
        type=int,
        default=0,
        help="0 = CPU (the cloud-container runs); -1 = offload all layers (Metal on the Mac rerun)",
    )
    args = ap.parse_args()

    from llama_cpp import Llama
    from llama_cpp import __version__ as llama_version

    cfg_bytes = args.config.read_bytes()
    cfg = json.loads(cfg_bytes)
    config_sha = hashlib.sha256(cfg_bytes).hexdigest()
    src_path = Path(cfg["sources"]["path"])
    if hashlib.sha256(src_path.read_bytes()).hexdigest() != cfg["sources"]["sha256"]:
        raise SystemExit("Source file checksum does not match the frozen config")
    sources = [json.loads(line) for line in src_path.read_text().splitlines() if line]
    digests = json.loads(args.digests.read_text())
    prompts = cfg["prompts"]
    dec = cfg["decoding"]
    done: set[str] = set()
    if args.output.exists():
        done = {json.loads(line)["run_id"] for line in args.output.read_text().splitlines() if line}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "config_sha256": config_sha,
        "llama_cpp_python": llama_version,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "started": datetime.datetime.now(datetime.UTC).isoformat(),
        "models": {},
    }
    for spec in cfg["models"]:
        if args.only_model and spec["id"] != args.only_model:
            continue
        path = args.models_dir / spec["artifact_file"]
        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest["models"][spec["id"]] = {  # type: ignore[index]
            "file": spec["artifact_file"],
            "sha256": file_sha,
            "n_gpu_layers": args.n_gpu_layers,
        }
        llm = Llama(
            model_path=str(path),
            n_ctx=cfg["runtime"]["n_ctx"],
            n_threads=cfg["runtime"]["n_threads"],
            n_gpu_layers=args.n_gpu_layers,
            verbose=False,
        )
        short = spec["family"]
        for seed in cfg["seeds"]:
            for src in sources:
                for arm in cfg["conditions"]:
                    run_id = f"{short}-{src['id']}-{arm}-{seed}"
                    if run_id in done:
                        continue
                    system = prompts["system_template"].format(
                        common=prompts["common"],
                        arm=prompts[arm],
                        output_contract=prompts["output_contract"],
                    )
                    user = prompts["user_template"].format(text=src["text"])
                    messages = [{"role": "user", "content": system + "\n\n" + user}]
                    record: dict[str, object] = {
                        "run_id": run_id,
                        "source_id": src["id"],
                        "source_sha256": digests[src["id"]],
                        "model": spec["id"],
                        "model_revision": spec["artifact_revision"],
                        "config_sha256": config_sha,
                        "seed": seed,
                        "condition": arm,
                        "provenance": "measured:local-model",
                    }
                    attempts = []
                    for attempt in (1, 2):
                        t0 = time.perf_counter()
                        try:
                            out = llm.create_chat_completion(
                                messages=messages,
                                temperature=dec["temperature"],
                                top_p=dec["top_p"],
                                max_tokens=dec["max_new_tokens"],
                                seed=seed,
                            )
                            raw = out["choices"][0]["message"]["content"] or ""
                            usage = out.get("usage", {})
                            finish = out["choices"][0].get("finish_reason")
                            latency = time.perf_counter() - t0
                            status, preds, err = parse_output(raw)
                            if finish == "length" and status == "valid":
                                status, preds, err = (
                                    "invalid-output",
                                    [],
                                    "truncated at max_new_tokens",
                                )
                            record.update(
                                status=status,
                                prediction=preds,
                                raw_response=raw,
                                error=err,
                                latency_s=round(latency, 3),
                                timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                            )
                            attempts.append(
                                {
                                    "attempt": attempt,
                                    "ok": True,
                                    "usage": usage,
                                    "finish_reason": finish,
                                }
                            )
                            break
                        except Exception as exc:  # runtime crash: retry once, keep both
                            attempts.append({"attempt": attempt, "ok": False, "error": repr(exc)})
                            record.update(
                                status="transport-failure",
                                prediction=[],
                                raw_response=None,
                                error=repr(exc),
                                latency_s=round(time.perf_counter() - t0, 3),
                                timestamp=datetime.datetime.now(datetime.UTC).isoformat(),
                            )
                    with args.output.open("a") as fh:
                        fh.write(json.dumps(record) + "\n")
                    with args.output.with_suffix(".attempts.jsonl").open("a") as fh:
                        fh.write(json.dumps({"run_id": run_id, "attempts": attempts}) + "\n")
                    print(run_id, record["status"], record["latency_s"], flush=True)
        del llm
    manifest["finished"] = datetime.datetime.now(datetime.UTC).isoformat()
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
