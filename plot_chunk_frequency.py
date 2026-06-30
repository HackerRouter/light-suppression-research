from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec

from common import ensure_output, parse_chunk, parse_rect, read_batch_csv, rect_points


def heatmap_colormap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("half_blue_to_dark_blue", ["#a5deff", "#012c6c"])


def collect_counts(path: str) -> dict[tuple[int, int], int]:
    if "=" in path:
        path = path.split("=", 1)[1]
    df = read_batch_csv(path)
    counts = defaultdict(int)
    for _, row in df.iterrows():
        for index in range(1, 6):
            chunk = parse_chunk(row.get(f"top{index}Chunk", ""))
            count = int(row.get(f"top{index}Count", 0) or 0)
            if chunk is not None and count > 0:
                counts[chunk] += count
    return dict(counts)


def infer_range(counts: dict[tuple[int, int], int], highlights) -> tuple[int, int, int, int]:
    xs = [x for x, _ in counts]
    zs = [z for _, z in counts]
    for rect in highlights:
        xs.extend([rect.min_x, rect.max_x])
        zs.extend([rect.min_z, rect.max_z])
    if not xs:
        return 0, 0, 0, 0
    return min(xs), min(zs), max(xs), max(zs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--highlight", action="append", default=[])
    parser.add_argument("--range")
    parser.add_argument("--annotate", action="store_true")
    parser.add_argument("--cell-size", type=float, default=0.55)
    parser.add_argument("--font-size", type=float, default=8.0)
    parser.add_argument("--title", default="Chunk frequency")
    args = parser.parse_args()

    highlights = [parse_rect(item) for item in args.highlight]
    counts = collect_counts(args.input)
    if args.range:
        rect = parse_rect(args.range)
        min_x, min_z, max_x, max_z = rect.min_x, rect.min_z, rect.max_x, rect.max_z
    else:
        min_x, min_z, max_x, max_z = infer_range(counts, highlights)
    xs = list(range(min_x, max_x + 1))
    zs = list(range(min_z, max_z + 1))
    grid = np.zeros((len(zs), len(xs)), dtype=float)
    for (x, z), count in counts.items():
        if min_x <= x <= max_x and min_z <= z <= max_z:
            grid[z - min_z, x - min_x] = count

    ensure_output(Path(args.output).parent)
    map_width = len(xs) * args.cell_size
    map_height = len(zs) * args.cell_size
    colorbar_width = 0.35
    side_margin = 4
    top_bottom_margin = 2
    fig_width = map_width + colorbar_width + side_margin
    fig_height = map_height + top_bottom_margin
    fig = plt.figure(figsize=(fig_width, fig_height), constrained_layout=False)
    grid_spec = GridSpec(1, 2, figure=fig, width_ratios=[map_width, colorbar_width], left=0.08, right=0.96, top=0.86, bottom=0.12, wspace=0.08)
    ax = fig.add_subplot(grid_spec[0, 0])
    colorbar_ax = fig.add_subplot(grid_spec[0, 1])
    image = ax.imshow(grid, origin="lower", cmap=heatmap_colormap(), extent=[min_x, max_x + 1, min_z, max_z + 1], aspect="equal")
    ax.set_box_aspect(len(zs) / len(xs))
    fig.colorbar(image, cax=colorbar_ax, label="task count")
    ax.set_xticks([x + 0.5 for x in xs], labels=xs)
    ax.set_yticks([z + 0.5 for z in zs], labels=zs)
    ax.set_xlabel("chunk x")
    ax.set_ylabel("chunk z")
    ax.set_title(args.title)
    for rect in highlights:
        hx, hz = rect_points(rect)
        ax.plot(hx, hz, color="cyan", linewidth=2)
    if args.annotate:
        for z in zs:
            for x in xs:
                value = int(grid[z - min_z, x - min_x])
                if value:
                    ax.text(x + 0.5, z + 0.5, str(value), color="white", ha="center", va="center", fontsize=args.font_size)
    fig.savefig(args.output, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
