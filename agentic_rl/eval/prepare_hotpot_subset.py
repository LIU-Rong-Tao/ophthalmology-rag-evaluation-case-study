from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="将 HotpotQA 原始 JSON 转换为 Agentic Evidence RAG 使用的轻量 subset。"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="HotpotQA 原始 JSON 文件路径。",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="输出 subset JSON 路径。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="最多保留多少条样本。",
    )
    return parser.parse_args()


def load_hotpot(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "examples", "cases"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError(f"不支持的 HotpotQA 数据格式：{path}")


def normalize_case(case: dict[str, Any], idx: int) -> dict[str, Any]:
    supporting_facts = case.get("supporting_facts", [])
    context = case.get("context", [])

    gold_titles = []
    for item in supporting_facts:
        if isinstance(item, list) and item:
            title = str(item[0])
            if title not in gold_titles:
                gold_titles.append(title)
        elif isinstance(item, dict):
            title = item.get("title") or item.get("source") or item.get("doc_title")
            if title and title not in gold_titles:
                gold_titles.append(str(title))

    context_titles = []
    for item in context:
        if isinstance(item, list) and item:
            title = str(item[0])
            if title not in context_titles:
                context_titles.append(title)

    return {
        "id": case.get("_id") or case.get("id") or f"hotpot_{idx}",
        "question": case.get("question", ""),
        "answer": case.get("answer", ""),
        "supporting_facts": supporting_facts,
        "gold_titles": gold_titles,
        "context_titles": context_titles,
        "source_dataset": "HotpotQA",
    }


def main() -> int:
    args = parse_args()
    cases = load_hotpot(Path(args.input))

    subset = []
    for idx, case in enumerate(cases[: args.limit], start=1):
        subset.append(normalize_case(case, idx))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(subset, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"写入 {output}，样本数：{len(subset)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())