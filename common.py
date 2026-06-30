from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DEFAULT_DEBUG_METRICS = [
    "lqNet",
    "lqSize",
    "lqIn",
    "lqOut",
    "runUpd",
    "lightMbx",
    "sorterMbx",
    "avgRunUpdMs",
    "nodes",
    "blkChk",
    "blkDec",
    "blkInc",
    "qLen",
]

LEVEL_COLUMNS = [f"l{i}" for i in range(22, 34)]


@dataclass(frozen=True)
class Rect:
    min_x: int
    min_z: int
    max_x: int
    max_z: int


@dataclass(frozen=True)
class Ticket:
    x: int
    z: int
    radius: int
    label: str


def ensure_output(path: str | Path) -> Path:
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def read_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for column in df.columns:
        if column.startswith("top") and column.endswith("Chunk"):
            continue
        converted = pd.to_numeric(df[column], errors="coerce")
        if converted.notna().any():
            df[column] = converted
    return df


def read_debug_csv(path: str | Path, filter_active: bool = True) -> pd.DataFrame:
    df = read_csv(path)
    if filter_active:
        masks = []
        for column in ["runUpd", "lightMbx", "sorterMbx", "nodes", "blkChk", "qLen"]:
            if column in df.columns:
                masks.append(pd.to_numeric(df[column], errors="coerce").fillna(0) > 0)
        if masks:
            mask = masks[0]
            for item in masks[1:]:
                mask = mask | item
            df = df[mask].copy()
    df.reset_index(drop=True, inplace=True)
    return df


def read_batch_csv(path: str | Path) -> pd.DataFrame:
    df = read_csv(path)
    if "batchSize" in df.columns:
        df = df[pd.to_numeric(df["batchSize"], errors="coerce").fillna(0) > 0].copy()
    df.reset_index(drop=True, inplace=True)
    return df


def apply_window(df: pd.DataFrame, start: int | None, end: int | None) -> pd.DataFrame:
    result = df
    if start is not None:
        result = result.iloc[start:]
    if end is not None:
        result = result.iloc[: end - (start or 0)]
    return result.copy()


def rolling_series(series: pd.Series, window: int | None) -> pd.Series:
    if window is None or window <= 1:
        return series
    return series.rolling(window, min_periods=1).mean()


def numeric_columns(df: pd.DataFrame, columns: Iterable[str]) -> list[str]:
    return [column for column in columns if column in df.columns and pd.api.types.is_numeric_dtype(df[column])]


def parse_rect(value: str) -> Rect:
    left, right = value.split(":", 1)
    min_x, min_z = [int(item) for item in left.split(",", 1)]
    max_x, max_z = [int(item) for item in right.split(",", 1)]
    return Rect(min(min_x, max_x), min(min_z, max_z), max(min_x, max_x), max(min_z, max_z))


def parse_ticket(value: str) -> Ticket:
    parts = value.split(",")
    if len(parts) == 3:
        x, z, radius = parts
        label = f"ticket_{x}_{z}_{radius}"
    elif len(parts) == 4:
        x, z, radius, label = parts
    else:
        raise ValueError("Ticket format must be x,z,radius or x,z,radius,label")
    return Ticket(int(x), int(z), int(radius), label)


def parse_chunk(value: str) -> tuple[int, int] | None:
    if not isinstance(value, str) or not value:
        return None
    if ":" in value:
        x, z = value.split(":", 1)
    elif "," in value:
        x, z = value.split(",", 1)
    else:
        return None
    return int(x), int(z)


def rect_points(rect: Rect) -> tuple[list[int], list[int]]:
    xs = [rect.min_x, rect.max_x + 1, rect.max_x + 1, rect.min_x, rect.min_x]
    zs = [rect.min_z, rect.min_z, rect.max_z + 1, rect.max_z + 1, rect.min_z]
    return xs, zs


def ticket_level(ticket: Ticket, x: int, z: int) -> int:
    return 33 - ticket.radius + max(abs(x - ticket.x), abs(z - ticket.z))


def ticket_applies(ticket: Ticket, x: int, z: int) -> bool:
    return max(abs(x - ticket.x), abs(z - ticket.z)) <= ticket.radius


def save_table(df: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def weighted_level_average(df: pd.DataFrame) -> pd.Series:
    columns = [column for column in LEVEL_COLUMNS if column in df.columns]
    if not columns:
        return pd.Series(np.nan, index=df.index)
    total = df[columns].sum(axis=1).replace(0, np.nan)
    weighted = sum(int(column[1:]) * df[column] for column in columns)
    return weighted / total


def entropy_from_columns(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    if not columns:
        return pd.Series(np.nan, index=df.index)
    values = df[columns].to_numpy(dtype=float)
    totals = values.sum(axis=1)
    result = []
    for row, total in zip(values, totals):
        if total <= 0:
            result.append(np.nan)
            continue
        p = row[row > 0] / total
        result.append(float(-(p * np.log2(p)).sum()))
    return pd.Series(result, index=df.index)
