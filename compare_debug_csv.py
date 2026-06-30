from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import DEFAULT_DEBUG_METRICS, apply_window, ensure_output, numeric_columns, read_debug_csv, rolling_series, save_table


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    if "lqIn" in result.columns and "lqNet" in result.columns:
        result["lqOut"] = result["lqIn"] - result["lqNet"]
    if "nodes" in result.columns and "blkChk" in result.columns:
        result["nodesPerCheck"] = result["nodes"] / result["blkChk"].replace(0, np.nan)
    if "blkDec" in result.columns and "blkChk" in result.columns:
        result["decPerCheck"] = result["blkDec"] / result["blkChk"].replace(0, np.nan)
    if "blkInc" in result.columns and "blkChk" in result.columns:
        result["incPerCheck"] = result["blkInc"] / result["blkChk"].replace(0, np.nan)
    if "sorterMbx" in result.columns and "lightMbx" in result.columns:
        result["lightMbxGap"] = result["sorterMbx"] - result["lightMbx"]
    return result


def x_values(df: pd.DataFrame, mode: str) -> pd.Series:
    if mode == "recordMs" and "recordMs" in df.columns:
        return df["recordMs"]
    if mode == "tick" and "tick" in df.columns:
        return df["tick"]
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


def plot_metrics(datasets: dict[str, pd.DataFrame], metrics: list[str], output: Path, rolling: int | None, x_axis: str) -> None:
    metrics = [metric for metric in metrics if any(metric in df.columns for df in datasets.values())]
    if not metrics:
        return
    cols = 2
    rows = (len(metrics) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(17, max(4, rows * 3)), squeeze=False)
    legend_handles = {}
    for index, metric in enumerate(metrics):
        ax = axes[index // cols][index % cols]
        for dataset_index, (label, df) in enumerate(datasets.items()):
            if metric not in df.columns:
                continue
            series = rolling_series(df[metric], rolling)
            line = ax.plot(x_values(df, x_axis), series.to_numpy(), label=label, linewidth=1.4, alpha=0.9, **line_style(dataset_index))[0]
            legend_handles.setdefault(label, line)
        ax.set_title(metric)
        ax.set_xlabel(x_axis)
        ax.grid(True, alpha=0.25)
    for index in range(len(metrics), rows * cols):
        axes[index // cols][index % cols].axis("off")
    if legend_handles:
        fig.legend(legend_handles.values(), legend_handles.keys(), loc="center left", bbox_to_anchor=(0.86, 0.5), frameon=False)
    fig.tight_layout(rect=[0, 0, 0.84, 1])
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="label=path")
    parser.add_argument("--output", default="output")
    parser.add_argument("--metrics", default=",".join(DEFAULT_DEBUG_METRICS + ["nodesPerCheck", "decPerCheck", "incPerCheck", "lightMbxGap"]))
    parser.add_argument("--rolling", type=int, default=30)
    parser.add_argument("--x-axis", choices=["normalized", "sample", "tick", "recordMs"], default="recordMs")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    parser.add_argument("--no-filter-active", action="store_true")
    args = parser.parse_args()

    output = ensure_output(args.output)
    datasets = {}
    summaries = []
    for item in args.input:
        label, path = item.split("=", 1)
        df = read_debug_csv(path, filter_active=not args.no_filter_active)
        df = apply_window(df, args.start, args.end)
        df = add_derived(df)
        datasets[label] = df
        numeric = df.select_dtypes(include="number")
        summary = numeric.mean().to_frame().T
        summary.insert(0, "label", label)
        summary.insert(1, "rows", len(df))
        summaries.append(summary)

    summary_df = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    save_table(summary_df, output / "debug_summary.csv")

    if len(summary_df) >= 2:
        labels = list(datasets.keys())
        base = summary_df[summary_df["label"] == labels[0]].select_dtypes(include="number").iloc[0]
        rows = []
        for label in labels[1:]:
            current = summary_df[summary_df["label"] == label].select_dtypes(include="number").iloc[0]
            diff = current - base
            ratio = current / base.replace(0, np.nan)
            row = pd.DataFrame({"metric": diff.index, "diff": diff.values, "ratio": ratio.values})
            row.insert(0, "label", f"{label}_vs_{labels[0]}")
            rows.append(row)
        save_table(pd.concat(rows, ignore_index=True), output / "debug_diff.csv")

    metrics = [metric.strip() for metric in args.metrics.split(",") if metric.strip()]
    plot_metrics(datasets, numeric_columns(pd.concat(datasets.values(), ignore_index=True), metrics), output / "debug_timeseries.png", args.rolling, args.x_axis)


if __name__ == "__main__":
    main()
