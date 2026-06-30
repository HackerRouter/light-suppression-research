from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from common import apply_window, ensure_output, read_debug_csv, rolling_series


def x_values(df, mode):
    if mode == "recordMs" and "recordMs" in df.columns:
        return df["recordMs"]
    if mode == "tick" and "tick" in df.columns:
        return df["tick"]
    if mode == "normalized" and len(df) > 1:
        return [i / (len(df) - 1) for i in range(len(df))]
    return list(range(len(df)))


def line_style(index):
    colors = plt.get_cmap("tab20").colors
    linestyles = ["-", "--", "-.", ":"]
    return {
        "color": colors[index % len(colors)],
        "linestyle": linestyles[(index // len(colors)) % len(linestyles)],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="label=path")
    parser.add_argument("--columns", required=True, help="comma separated columns")
    parser.add_argument("--output", required=True)
    parser.add_argument("--rolling", type=int, default=1)
    parser.add_argument("--x-axis", choices=["normalized", "sample", "tick", "recordMs"], default="recordMs")
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    parser.add_argument("--no-filter-active", action="store_true")
    args = parser.parse_args()

    columns = [item.strip() for item in args.columns.split(",") if item.strip()]
    ensure_output(Path(args.output).parent)
    fig, axes = plt.subplots(len(columns), 1, figsize=(14, max(4, len(columns) * 3)), squeeze=False)
    for dataset_index, item in enumerate(args.input):
        label, path = item.split("=", 1)
        df = read_debug_csv(path, filter_active=not args.no_filter_active)
        df = apply_window(df, args.start, args.end)
        for index, column in enumerate(columns):
            if column not in df.columns:
                continue
            series = rolling_series(df[column], args.rolling)
            axes[index][0].plot(x_values(df, args.x_axis), series.to_numpy(), label=label, linewidth=1.4, alpha=0.9, **line_style(dataset_index))
    for index, column in enumerate(columns):
        axes[index][0].set_title(column)
        axes[index][0].set_xlabel(args.x_axis)
        axes[index][0].grid(True, alpha=0.25)
        axes[index][0].legend()
    fig.tight_layout()
    fig.savefig(args.output, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
