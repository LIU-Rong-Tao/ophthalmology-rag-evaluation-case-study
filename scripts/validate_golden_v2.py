#!/usr/bin/env python3
"""Validate MedRAG-Align Golden v2 JSON/JSONL records."""

import argparse
import json
from pathlib import Path

REQUIRED = {
    "id", "source_dataset", "split", "task_type", "question",
    "evidence_spans", "answer", "claims", "safety_expectation", "metadata"
}
VALID_SPLITS = {"train_seed", "eval_heldout", "dev_eval", "preference_seed"}

def load_records(path):
    path = Path(path)
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    yield f"{path}:{i}", json.loads(line)
    else:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, list):
            for i, item in enumerate(data, start=1):
                yield f"{path}:{i}", item
        elif isinstance(data, dict):
            for key in ("samples", "test_cases", "records", "data"):
                if isinstance(data.get(key), list):
                    for i, item in enumerate(data[key], start=1):
                        yield f"{path}:{key}:{i}", item
                    return
            yield str(path), data

def validate(loc, rec):
    errors = []
    missing = REQUIRED - set(rec)
    if missing:
        errors.append(f"{loc}: missing {sorted(missing)}")
        return errors

    if rec["split"] not in VALID_SPLITS:
        errors.append(f"{loc}: invalid split {rec['split']}")

    if rec["split"] == "train_seed" and not str(rec.get("answer", "")).strip():
        errors.append(f"{loc}: train_seed must have answer")

    meta = rec.get("metadata")
    if not isinstance(meta, dict) or not meta.get("conversion"):
        errors.append(f"{loc}: metadata.conversion required")

    spans = rec.get("evidence_spans")
    if not isinstance(spans, list) or not spans:
        errors.append(f"{loc}: evidence_spans must be non-empty")
        evidence_ids = set()
    else:
        evidence_ids = set()
        for i, span in enumerate(spans, start=1):
            eid = str(span.get("evidence_id", "")).strip()
            if not eid:
                errors.append(f"{loc}: evidence_spans[{i}] missing evidence_id")
            elif eid in evidence_ids:
                errors.append(f"{loc}: duplicate evidence_id {eid}")
            else:
                evidence_ids.add(eid)
            if not str(span.get("evidence_text", "")).strip():
                errors.append(f"{loc}: evidence_spans[{i}] missing evidence_text")

    claims = rec.get("claims")
    if not isinstance(claims, list):
        errors.append(f"{loc}: claims must be list")
    else:
        for i, claim in enumerate(claims, start=1):
            if not claim.get("claim_id"):
                errors.append(f"{loc}: claims[{i}] missing claim_id")
            if not claim.get("claim_text"):
                errors.append(f"{loc}: claims[{i}] missing claim_text")
            if not claim.get("support_type"):
                errors.append(f"{loc}: claims[{i}] missing support_type")
            refs = claim.get("supporting_evidence_ids")
            if not isinstance(refs, list):
                errors.append(f"{loc}: claims[{i}] supporting_evidence_ids must be list")
            else:
                bad = [r for r in refs if r not in evidence_ids]
                if bad:
                    errors.append(f"{loc}: claims[{i}] bad evidence refs {bad}")

    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    all_errors = []
    n = 0
    for p in args.paths:
        path = Path(p)
        files = sorted(path.rglob("*.json")) + sorted(path.rglob("*.jsonl")) if path.is_dir() else [path]
        for file in files:
            for loc, rec in load_records(file):
                n += 1
                if not isinstance(rec, dict):
                    all_errors.append(f"{loc}: record must be object")
                else:
                    all_errors.extend(validate(loc, rec))

    if all_errors:
        for e in all_errors:
            print("ERROR:", e)
        print(f"Validated {n} records with {len(all_errors)} errors")
        raise SystemExit(1)

    print(f"Validated {n} records. No errors.")

if __name__ == "__main__":
    main()
