#!/usr/bin/env python3
"""Convert PubMedQA samples into MedRAG-Align Golden v2 schema.

This creates training-ready SFT seed samples.
It does not create clinician-verified claim-level annotations.
Claim-to-evidence links are weakly supervised by PubMedQA context fields.
"""

import argparse
import json
from pathlib import Path

CONVERSION = "automatic_pubmedqa_adapter_v1"

def get_first(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return default

def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def norm(x):
    if x is None:
        return ""
    return " ".join(str(x).split())

def iter_samples(raw):
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                yield None, item
        return

    if not isinstance(raw, dict):
        raise ValueError("Input must be a JSON object or list")

    for key in ("data", "samples", "train", "dev", "test", "test_cases"):
        if key in raw:
            yield from iter_samples(raw[key])
            return

    for key, val in raw.items():
        if isinstance(val, dict):
            q = get_first(val, "QUESTION", "question", "Question")
            c = get_first(val, "CONTEXTS", "contexts", "context")
            if q is not None or c is not None:
                yield str(key), val

def build_record(sample_id, idx, sample, split, source_dataset):
    question = norm(get_first(sample, "QUESTION", "question", "Question"))
    answer = norm(get_first(sample, "LONG_ANSWER", "long_answer", "answer", "final_answer"))
    contexts = as_list(get_first(sample, "CONTEXTS", "contexts", "context"))
    labels = as_list(get_first(sample, "LABELS", "labels", default=[]))

    evidence_spans = []
    for i, ctx in enumerate(contexts, start=1):
        text = norm(ctx)
        if not text:
            continue
        section = norm(labels[i - 1]) if i - 1 < len(labels) else f"CONTEXT_{i}"
        evidence_spans.append({
            "evidence_id": f"e{i}",
            "source": source_dataset,
            "section": section,
            "evidence_text": text
        })

    if not question or not answer or not evidence_spans:
        return None

    sid = sample_id or f"{idx:06d}"
    evidence_ids = [e["evidence_id"] for e in evidence_spans]

    return {
        "id": f"pubmedqa_{sid}",
        "source_dataset": source_dataset,
        "split": split,
        "task_type": "evidence_grounded_qa",
        "domain": "biomedical",
        "question": question,
        "evidence_spans": evidence_spans,
        "answer": answer,
        "reference_answer": answer,
        "claims": [{
            "claim_id": "c1",
            "claim_text": answer,
            "supporting_evidence_ids": evidence_ids,
            "support_type": "weak_supervision"
        }],
        "safety_expectation": "answer",
        "metadata": {
            "final_decision": norm(get_first(sample, "final_decision", "FINAL_DECISION", "label", "LABEL")).lower(),
            "mesh_terms": as_list(get_first(sample, "MESHES", "meshes", "mesh_terms", default=[])),
            "year": get_first(sample, "YEAR", "year", default=None),
            "context_labels": labels,
            "conversion": CONVERSION,
            "weak_supervision_note": "PubMedQA contexts are weak evidence links, not clinician-verified claim-level annotations."
        }
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="eval/align/pubmedqa_sft_seed.sample.jsonl")
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--split", default="train_seed", choices=["train_seed", "dev_eval"])
    ap.add_argument("--source-dataset", default="PubMedQA")
    args = ap.parse_args()

    raw = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))

    records = []
    skipped = 0
    for idx, (sid, sample) in enumerate(iter_samples(raw), start=1):
        if len(records) >= args.limit:
            break
        rec = build_record(sid, idx, sample, args.split, args.source_dataset)
        if rec is None:
            skipped += 1
            continue
        records.append(rec)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} records to {out}")
    if skipped:
        print(f"Skipped {skipped} incomplete records")

if __name__ == "__main__":
    main()
