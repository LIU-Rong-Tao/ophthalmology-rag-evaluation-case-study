from pathlib import Path
import csv
import html


RESULT_DIR = Path("eval/results")
FIG_DIR = RESULT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(row, key):
    return float(row[key])


def esc(value):
    return html.escape(str(value))


def draw_grouped_chart(title, labels, series, latency, output):
    width, height = 980, 520
    left, right, top, bottom = 70, 90, 55, 90
    plot_w = width - left - right
    plot_h = height - top - bottom

    max_latency = max(latency) * 1.15
    group_w = plot_w / len(labels)
    bar_w = min(46, group_w / (len(series) + 1.4))
    colors = ["#4C78A8", "#59A14F", "#F28E2B", "#B07AA1"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="20" font-family="Arial" font-weight="700">{esc(title)}</text>',
    ]

    # axes
    x0, y0 = left, top + plot_h
    parts.append(f'<line x1="{x0}" y1="{top}" x2="{x0}" y2="{y0}" stroke="#333"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{left+plot_w}" y2="{y0}" stroke="#333"/>')
    parts.append(f'<line x1="{left+plot_w}" y1="{top}" x2="{left+plot_w}" y2="{y0}" stroke="#333"/>')

    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        y = y0 - tick * plot_h
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left+plot_w}" y2="{y}" stroke="#eee"/>')
        parts.append(f'<text x="{left-10}" y="{y+4}" text-anchor="end" font-size="12" font-family="Arial">{tick:.2f}</text>')

    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        value = tick * max_latency
        y = y0 - tick * plot_h
        parts.append(f'<text x="{left+plot_w+10}" y="{y+4}" font-size="12" font-family="Arial">{value:.0f}</text>')

    # bars
    for i, label in enumerate(labels):
        center = left + group_w * i + group_w / 2
        parts.append(f'<text x="{center}" y="{height-38}" text-anchor="middle" font-size="13" font-family="Arial">{esc(label)}</text>')

        start_x = center - (len(series) * bar_w) / 2
        for j, item in enumerate(series):
            value = item["values"][i]
            bar_h = value * plot_h
            x = start_x + j * bar_w
            y = y0 - bar_h
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_w*0.82}" height="{bar_h}" fill="{colors[j]}"/>')
            parts.append(f'<text x="{x + bar_w*0.41}" y="{y-5}" text-anchor="middle" font-size="11" font-family="Arial">{value:.2f}</text>')

    # latency line
    points = []
    for i, value in enumerate(latency):
        x = left + group_w * i + group_w / 2
        y = y0 - (value / max_latency) * plot_h
        points.append((x, y, value))

    polyline = " ".join(f"{x},{y}" for x, y, _ in points)
    parts.append(f'<polyline points="{polyline}" fill="none" stroke="#D62728" stroke-width="3"/>')
    for x, y, value in points:
        parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#D62728"/>')
        parts.append(f'<text x="{x}" y="{y-10}" text-anchor="middle" font-size="11" font-family="Arial" fill="#D62728">{value:.0f}ms</text>')

    # legends
    legend_x, legend_y = left, height - 18
    for j, item in enumerate(series):
        x = legend_x + j * 175
        parts.append(f'<rect x="{x}" y="{legend_y-12}" width="12" height="12" fill="{colors[j]}"/>')
        parts.append(f'<text x="{x+18}" y="{legend_y-2}" font-size="12" font-family="Arial">{esc(item["name"])}</text>')

    x = legend_x + len(series) * 175
    parts.append(f'<line x1="{x}" y1="{legend_y-6}" x2="{x+18}" y2="{legend_y-6}" stroke="#D62728" stroke-width="3"/>')
    parts.append(f'<text x="{x+25}" y="{legend_y-2}" font-size="12" font-family="Arial">latency</text>')

    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def plot_retrieval():
    rows = read_csv(RESULT_DIR / "retrieval_ablation_summary.csv")
    labels = [r["mode"] for r in rows]
    series = [
        {"name": "source_hit@5", "values": [num(r, "source_hit@5") for r in rows]},
        {"name": "source_mrr@5", "values": [num(r, "source_mrr@5") for r in rows]},
    ]
    latency = [num(r, "avg_query_ms") for r in rows]
    draw_grouped_chart(
        "Retrieval Ablation: Quality vs Latency",
        labels,
        series,
        latency,
        FIG_DIR / "retrieval_ablation.svg",
    )


def plot_generation():
    rows = read_csv(RESULT_DIR / "generation_topk_ablation_summary.csv")
    labels = [r["setting"] for r in rows]
    series = [
        {"name": "source_hit@k", "values": [num(r, "retrieval_source_hit@k") for r in rows]},
        {"name": "source_coverage@k", "values": [num(r, "retrieval_source_coverage@k") for r in rows]},
        {"name": "citation_coverage", "values": [num(r, "rag_citation_coverage") for r in rows]},
    ]
    latency = [num(r, "rag_total_avg_ms") for r in rows]
    draw_grouped_chart(
        "Generation Ablation: Coverage vs Latency",
        labels,
        series,
        latency,
        FIG_DIR / "generation_ablation.svg",
    )


def main():
    plot_retrieval()
    plot_generation()
    print(f"Wrote {FIG_DIR / 'retrieval_ablation.svg'}")
    print(f"Wrote {FIG_DIR / 'generation_ablation.svg'}")


if __name__ == "__main__":
    main()
