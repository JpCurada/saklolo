"""Render metrics in the run-evals skill's report format."""

from saklolo.eval.metrics import Metric

PERCENT_METRICS = {
    "Critical recall",
    "Critical precision",
    "Correct barangay %",
    "Ask-back rate",
    "False-flag rate",
    "Recycled flagged %",
    "Dedupe precision",
    "Dedupe recall",
}


def format_value(metric: Metric) -> str:
    if metric.value is None:
        return "n/a"
    if metric.name in PERCENT_METRICS:
        return f"{metric.value:.1%}"
    if metric.name.startswith("Cost"):
        return f"${metric.value:.2f}"
    return f"{metric.value:.3f}"


def rows(metrics: list[Metric]) -> list[tuple[str, str, str]]:
    """(label, value, n) rows; dedupe precision and recall share one row as 'P / R'."""
    by_name = {m.name: m for m in metrics}
    result = []
    for metric in metrics:
        if metric.name == "Dedupe recall":
            continue
        if metric.name == "Dedupe precision":
            recall = by_name["Dedupe recall"]
            value = f"{format_value(metric)} / {format_value(recall)}"
            n = f"{metric.n} / {recall.n} pairs"
            result.append(("Dedupe P / R", value, n))
        else:
            result.append((metric.name, format_value(metric), str(metric.n)))
    return result


def render_run(title: str, notes: list[str], metrics: list[Metric]) -> str:
    lines = [f"# {title}", "", *[f"- {note}" for note in notes], ""]
    lines += ["| Metric | Value | n |", "|---|---|---|"]
    lines += [f"| {label} | {value} | {n} |" for label, value, n in rows(metrics)]
    return "\n".join(lines) + "\n"


def render_comparison(before: list[Metric], after: list[Metric]) -> str:
    before_rows = {label: value for label, value, _ in rows(before)}
    lines = ["| Metric | Before | After |", "|---|---|---|"]
    lines += [
        f"| {label} | {before_rows.get(label, 'n/a')} | {value} |"
        for label, value, _ in rows(after)
    ]
    return "\n".join(lines) + "\n"
