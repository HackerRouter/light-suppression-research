from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec

from common import ensure_output, parse_rect, parse_ticket, rect_points


@dataclass(frozen=True)
class PlaneTicket:
    x: int
    z: int
    center_level: int
    label: str
    max_distance: int
    source_radius: int = 0

    @property
    def max_radius(self) -> int:
        return self.max_distance

    def level_at(self, x: int, z: int) -> int:
        distance = max(abs(x - self.x), abs(z - self.z))
        return self.center_level + max(0, distance - self.source_radius)

    def applies(self, x: int, z: int) -> bool:
        return max(abs(x - self.x), abs(z - self.z)) <= this_max_distance(self) and self.level_at(x, z) <= 33


def this_max_distance(ticket: PlaneTicket) -> int:
    return ticket.source_radius + ticket.max_distance


def parse_level_ticket(value: str) -> PlaneTicket:
    parts = value.split(",")
    if len(parts) == 3:
        x, z, level = parts
        label = f"level_{level}_{x}_{z}"
    elif len(parts) == 4:
        x, z, level, label = parts
    else:
        raise ValueError("Level ticket format must be x,z,level or x,z,level,label")
    return PlaneTicket(int(x), int(z), int(level), label, max(0, 33 - int(level)))


def from_region_ticket(value: str) -> PlaneTicket:
    ticket = parse_ticket(value)
    return PlaneTicket(ticket.x, ticket.z, 33 - ticket.radius, ticket.label, ticket.radius)


def parse_center_ticket(value: str, center_level: int, max_distance: int, default_label: str) -> PlaneTicket:
    parts = value.split(",")
    if len(parts) == 2:
        x, z = parts
        label = default_label
    elif len(parts) == 3:
        x, z, label = parts
    else:
        raise ValueError("Ticket format must be x,z or x,z,label")
    return PlaneTicket(int(x), int(z), center_level, label, max_distance)


def parse_player_ticket(value: str) -> PlaneTicket:
    parts = value.split(",")
    if len(parts) == 3:
        x, z, view_distance = parts
        label = "PLAYER"
    elif len(parts) == 4:
        x, z, view_distance, label = parts
    else:
        raise ValueError("Player ticket format must be x,z,viewDistance or x,z,viewDistance,label")
    return PlaneTicket(int(x), int(z), 31, label, 2, int(view_distance))


def build_grid(tickets: list[PlaneTicket], xs: list[int], zs: list[int]) -> np.ndarray:
    grid = np.full((len(zs), len(xs)), np.nan, dtype=float)
    for zi, z in enumerate(zs):
        for xi, x in enumerate(xs):
            best_level = None
            for ticket in tickets:
                if not ticket.applies(x, z):
                    continue
                level = ticket.level_at(x, z)
                if best_level is None or level < best_level:
                    best_level = level
            if best_level is not None:
                grid[zi, xi] = best_level
    return grid


def ticket_colormap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("ticket_blues", ["#012c6c", "#a5deff"])


def draw_grid(ax, grid: np.ndarray, rect, xs: list[int], zs: list[int], title: str, annotate: bool, font_size: float):
    masked = np.ma.masked_invalid(grid)
    image = ax.imshow(masked, origin="lower", cmap=ticket_colormap(), vmin=22, vmax=33, extent=[rect.min_x, rect.max_x + 1, rect.min_z, rect.max_z + 1], aspect="equal")
    ax.set_box_aspect(len(zs) / len(xs))
    ax.set_xticks([x + 0.5 for x in xs], labels=xs)
    ax.set_yticks([z + 0.5 for z in zs], labels=zs)
    ax.set_xlabel("chunk x")
    ax.set_ylabel("chunk z")
    ax.set_title(title)
    if annotate:
        for zi, z in enumerate(zs):
            for xi, x in enumerate(xs):
                if not np.isnan(grid[zi, xi]):
                    ax.text(x + 0.5, z + 0.5, str(int(grid[zi, xi])), color="white", ha="center", va="center", fontsize=font_size)
    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--range", required=True, dest="chunk_range", help="minX,minZ:maxX,maxZ")
    parser.add_argument("--ticket", action="append", default=[], help="x,z,radius,label; center level is 33 - radius")
    parser.add_argument("--level-ticket", action="append", default=[], help="x,z,level,label")
    parser.add_argument("--start-ticket", action="append", default=[], help="x,z,label; center level 22, max distance 11")
    parser.add_argument("--portal-ticket", action="append", default=[], help="x,z,label; center level 30, max distance 3")
    parser.add_argument("--player-ticket", action="append", default=[], help="x,z,viewDistance,label; level 31 source field within view distance, then propagates to 33")
    parser.add_argument("--highlight", action="append", default=[])
    parser.add_argument("--output", required=True)
    parser.add_argument("--annotate", action="store_true")
    parser.add_argument("--cell-size", type=float, default=0.55)
    parser.add_argument("--font-size", type=float, default=9.0)
    parser.add_argument("--mode", choices=["effective", "separate", "both"], default="both")
    parser.add_argument("--title", default="Ticket level plane")
    args = parser.parse_args()

    rect = parse_rect(args.chunk_range)
    tickets = [from_region_ticket(item) for item in args.ticket]
    tickets.extend(parse_level_ticket(item) for item in args.level_ticket)
    tickets.extend(parse_center_ticket(item, 22, 11, "START") for item in args.start_ticket)
    tickets.extend(parse_center_ticket(item, 30, 3, "PORTAL") for item in args.portal_ticket)
    tickets.extend(parse_player_ticket(item) for item in args.player_ticket)
    highlights = [parse_rect(item) for item in args.highlight]
    xs = list(range(rect.min_x, rect.max_x + 1))
    zs = list(range(rect.min_z, rect.max_z + 1))

    ensure_output(Path(args.output).parent)
    panels = []
    if args.mode in ["effective", "both"]:
        panels.append(("effective", build_grid(tickets, xs, zs), tickets))
    if args.mode in ["separate", "both"]:
        for ticket in tickets:
            panels.append((ticket.label, build_grid([ticket], xs, zs), [ticket]))

    map_width = len(xs) * args.cell_size
    map_height = len(zs) * args.cell_size
    colorbar_width = 0.35
    side_margin = 0.8
    top_bottom_margin = 1.2
    gap_width = 0.45
    fig_width = len(panels) * map_width + max(0, len(panels) - 1) * gap_width + colorbar_width + side_margin
    fig_height = map_height + top_bottom_margin
    fig = plt.figure(figsize=(fig_width, fig_height), constrained_layout=False)
    ratios = []
    for index in range(len(panels)):
        if index > 0:
            ratios.append(gap_width)
        ratios.append(map_width)
    ratios.append(colorbar_width)
    grid_spec = GridSpec(1, len(ratios), figure=fig, width_ratios=ratios, left=0.06, right=0.96, top=0.86, bottom=0.12, wspace=0.0)
    axes = []
    column = 0
    for index in range(len(panels)):
        if index > 0:
            column += 1
        axes.append(fig.add_subplot(grid_spec[0, column]))
        column += 1
    colorbar_ax = fig.add_subplot(grid_spec[0, -1])
    image = None
    for panel_index, (title, grid, panel_tickets) in enumerate(panels):
        ax = axes[panel_index]
        image = draw_grid(ax, grid, rect, xs, zs, title if len(panels) > 1 else args.title, args.annotate, args.font_size)

        for ticket in panel_tickets:
            ax.scatter(ticket.x + 0.5, ticket.z + 0.5, marker="x", s=120, linewidths=2.5, label=f"{ticket.label} L={ticket.center_level}")
            if ticket.source_radius > 0:
                source_boundary = [
                    ticket.x - ticket.source_radius,
                    ticket.z - ticket.source_radius,
                    ticket.x + ticket.source_radius,
                    ticket.z + ticket.source_radius,
                ]
                sx = [source_boundary[0], source_boundary[2] + 1, source_boundary[2] + 1, source_boundary[0], source_boundary[0]]
                sz = [source_boundary[1], source_boundary[1], source_boundary[3] + 1, source_boundary[3] + 1, source_boundary[1]]
                ax.plot(sx, sz, linewidth=1.2, linestyle="--", alpha=0.9)
            boundary = [
                ticket.x - this_max_distance(ticket),
                ticket.z - this_max_distance(ticket),
                ticket.x + this_max_distance(ticket),
                ticket.z + this_max_distance(ticket),
            ]
            bx = [boundary[0], boundary[2] + 1, boundary[2] + 1, boundary[0], boundary[0]]
            bz = [boundary[1], boundary[1], boundary[3] + 1, boundary[3] + 1, boundary[1]]
            ax.plot(bx, bz, linewidth=1.2, alpha=0.7)

        for highlight in highlights:
            hx, hz = rect_points(highlight)
            ax.plot(hx, hz, color="cyan", linewidth=2.5)

        if panel_tickets:
            ax.legend(loc="upper right")
    if image is not None:
        fig.colorbar(image, cax=colorbar_ax, label="ticket level")
    fig.savefig(args.output, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
