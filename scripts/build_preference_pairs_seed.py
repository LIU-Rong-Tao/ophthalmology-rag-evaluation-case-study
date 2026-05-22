import argparse
import json
from pathlib import Path


def load_records(path):
    path = Path(path)
    if path.suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    else:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            for key in ("samples", "records", "data", "test_cases"):
                if key in data:
                    yield from data[key]
                    return
            yield data
        elif isinstance(data, list):
            yield from data


def citation_suffix(rec):
    ids = [e["evidence_id"] for e in rec.get("evidence_spans", [])]
    return " ".join(f"[{x}]" for x in ids)


def make_prompt(rec):
    evidence = "\n".join(
        f"[{e['evidence_id']}] {e.get('section', 'EVIDENCE')}: {e.get('evidence_text', '')}"
        for e in rec.get("evidence_spans", [])
    )
    return (
        "请基于给定医学证据回答问题。要求：只使用证据支持的内容，"
        "医学断言需要引用证据编号；证据不足时说明不确定。\n\n"
        f"问题：{rec.get('question', '')}\n\n证据：\n{evidence}"
    )


def make_pair(rec, idx):
    answer = rec.get("answer") or rec.get("reference_answer") or ""
    citations = citation_suffix(rec)
    pair_type = ["citation_grounding", "unsupported_claim", "medical_abstain"][idx % 3]

    chosen = f"{answer}\n\n证据：{citations}".strip()

    if pair_type == "citation_grounding":
        rejected = answer
        rationale = "chosen 保留证据引用；rejected 缺少 citation，不能验证医学断言来源。"
    elif pair_type == "unsupported_claim":
        rejected = (
            f"{answer}\n\n此外，该结论可以直接推广到所有临床患者，并可作为诊断依据。"
        )
        rationale = "chosen 只回答证据支持内容；rejected 加入了无证据的临床泛化和诊断性断言。"
    else:
        rejected = (
            "可以直接根据这些信息给出明确医学诊断和治疗建议，不需要更多临床资料。"
        )
        rationale = "chosen 基于证据回答；rejected 违反医学安全边界，过度诊断。"

    return {
        "id": f"pref_seed_{idx + 1:04d}",
        "source_sample_id": rec.get("id"),
        "source_dataset": rec.get("source_dataset"),
        "split": "preference_seed",
        "pair_type": pair_type,
        "prompt": make_prompt(rec),
        "evidence_spans": rec.get("evidence_spans", []),
        "chosen": chosen,
        "rejected": rejected,
        "preference_label": "chosen",
        "rationale": rationale,
        "metadata": {
            "conversion": "automatic_preference_pair_seed_v1",
            "note": "Weak preference seed for evidence-grounded medical alignment, not clinician-verified preference annotation."
        }
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    records = list(load_records(args.input))[: args.limit]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        for idx, rec in enumerate(records):
            f.write(json.dumps(make_pair(rec, idx), ensure_ascii=False) + "\n")

    print(f"Wrote {len(records)} preference pairs to {out}")


if __name__ == "__main__":
    main()