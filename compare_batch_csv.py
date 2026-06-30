from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import LEVEL_COLUMNS, apply_window, ensure_output, entropy_from_columns, read_batch_csv, rolling_series, save_table, weighted_level_average


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    top_columns = [f"top{i}Count" for i in range(1, 6) if f"top{i}Count" in result.columns]
    if "batchSize" in result.columns:
        batch_size = result["batchSize"].replace(0, np.nan)
        for index in range(1, 6):
            column = f"top{index}Count"
            if column in result.columns:
                result[f"top{index}Ratio"] = result[column] / batch_size
        result["top5SumRatio"] = result[top_columns].sum(axis=1) / batch_size
    result["levelAvg"] = weighted_level_average(result)
    result["levelEntropy"] = entropy_from_columns(result, [column for column in LEVEL_COLUMNS if column in result.columns])
    return result


def x_values(df: pd.DataFrame, mode: str) -> pd.Series:
    if mode == "recordMs" and "recordMs" in df.columns:
        return df["recordMs"]
    if mode == "runUpdateId" and "runUpdateId" in df.columns:
        return df["runUpdateId"]
    if mode == "normalized" and len(df) > 1:
        return pd.Series([i / (len(df) - 1) for i in range(len(df))], index=df.index)
    return pd.Series(range(len(df)), index=df.index)


def line_style(index: int) -> dict:
    colors = plt.get_cmap("tab20").colors
    linestyles = ["-", "--", "-.", ":"]
    return {
        "color": colors[index % len(colors)],
        "linestyle": linestyles[(index // len(colors)) % len(linestyles)],
    }


def plot_lines(datasets: dict[str, pd.DataFrame], metrics: list[str], output: Path, rolling: int, x_axis: str) -> None:
    fig, axes = plt.subplots(len(metrics), 1, figsize=(17, max(4, len(metrics) * 3)), squeeze=False)
    legend_handles = {}
    for index, metric in enumerate(metrics):
        ax = axes[index][0]
        for dataset_index, (label, df) in enumerate(datasets.items()):
            if metric in df.columns:
                series = rolling_series(df[metric], rolling)
                line = ax.plot(x_values(df, x_axis), series.to_numpy(), label=label, linewidth=1.2, alpha=0.9, **line_style(dataset_index))[0]
                legend_handles.setdefault(label, line)
        ax.set_title(metric)
        ax.set_xlabel(x_axis)
        ax.grid(True, alpha=0.25)
    if legend_handles:
        fig.legend(legend_handles.values(), legend_handles.keys(), loc="center left", bbox_to_anchor=(0.86, 0.5), frameon=False)
    fig.tight_layout(rect=[0, 0, 0.84, 1])
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_level_histogram(summary: pd.DataFrame, output: Path) -> None:
    rows = []
    for _, row in summary.iterrows():
        for column in LEVEL_COLUMNS:
            if column in row.index:
                rows.append({"label": row["label"], "level": int(column[1:]), "value": row[column]})
    if not rows:
        return
    df = pd.DataFrame(rows)
    labels = list(df["label"].unique())
    levels = sorted(df["level"].unique())
    width = 0.8 / max(1, len(labels))
    fig, ax = plt.subplots(figsize=(12, 5))
    for index, label in enumerate(labels):
        values = [df[(df["label"] == label) & (df["level"] == level)]["value"].sum() for level in levels]
        xs = [level + (index - (len(labels) - 1) / 2) * width for level in levels]
        ax.bar(xs, values, width=width, label=label)
    ax.set_xlabel("queue level")
    ax.set_ylabel("average task count per batch")
    ax.set_title("Level composition")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="label=path")
    parser.add_argument("--output", default="output")
    parser.add_argument("--rolling", type=int, default=60)
    parser.add_argument("--x-axis", choices=["recordMs", "runUpdateId", "sample", "normalized"], default="recordMs")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()

    output = ensure_output(args.output)
    datasets = {}
    summaries = []
    for item in args.input:
        label, path = item.split("=", 1)
        df = add_derived(apply_window(read_batch_csv(path), args.start, args.end))
        datasets[label] = df
        numeric = df[[column for column in df.columns if not column.endswith("Chunk")]].select_dtypes(include="number")
        summary = numeric.mean().to_frame().T
        summary.insert(0, "label", label)
        summary.insert(1, "rows", len(df))
        summaries.append(summary)
    summary_df = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    save_table(summary_df, output / "batch_summary.csv")
    plot_lines(datasets, ["batchSize", "uniqueChunks", "maxChunkTasks", "top1Ratio", "top2Ratio", "top3Ratio", "top4Ratio", "top5Ratio", "top5SumRatio", "levelAvg", "levelEntropy"], output / "batch_timeseries.png", args.rolling, args.x_axis)
    plot_level_histogram(summary_df, output / "batch_level_histogram.png")


if __name__ == "__main__":
    main()
