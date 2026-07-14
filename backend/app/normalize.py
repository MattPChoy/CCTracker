"""Normalize the shapes ccusage emits into a single canonical form.

ccusage reports cost under different keys depending on the sub-command
(costUSD in daily rows, totalCost in totals, totalCostUSD in summary), and
model IDs are long dated strings. We collapse both so breakdowns group cleanly.
"""

from __future__ import annotations

import re

# Cost can arrive under any of these keys; first present (in order) wins.
_COST_KEYS = ("costUSD", "cost_usd", "totalCost", "totalCostUSD", "cost")

# Token field aliases: canonical name -> possible incoming keys.
_TOKEN_ALIASES = {
    "input_tokens": ("inputTokens", "input_tokens", "input"),
    "output_tokens": ("outputTokens", "output_tokens", "output"),
    "cache_creation_tokens": ("cacheCreationTokens", "cache_creation_tokens", "cacheCreation"),
    "cache_read_tokens": ("cacheReadTokens", "cache_read_tokens", "cacheRead"),
    "total_tokens": ("totalTokens", "total_tokens", "total"),
}

# family slug -> (regex on the raw model id, human label prefix)
_FAMILIES = [
    ("opus", re.compile(r"opus", re.I), "Opus"),
    ("sonnet", re.compile(r"sonnet", re.I), "Sonnet"),
    ("haiku", re.compile(r"haiku", re.I), "Haiku"),
]

# Pull a version like "4-1" / "4.5" out of the id, if present.
_VERSION = re.compile(r"(\d+)[-.](\d+)")


def normalize_cost(row: dict) -> float:
    for k in _COST_KEYS:
        v = row.get(k)
        if v is not None:
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def normalize_tokens(row: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for canonical, aliases in _TOKEN_ALIASES.items():
        val = 0
        for a in aliases:
            if row.get(a) is not None:
                try:
                    val = int(row[a])
                except (TypeError, ValueError):
                    val = 0
                break
        out[canonical] = val
    # If ccusage didn't give an explicit total, sum the components.
    if not out.get("total_tokens"):
        out["total_tokens"] = (
            out["input_tokens"]
            + out["output_tokens"]
            + out["cache_creation_tokens"]
            + out["cache_read_tokens"]
        )
    return out


def normalize_model(raw: str) -> tuple[str, str]:
    """Return (family_slug, display_label). Unknown ids fall back to the raw id."""
    raw = (raw or "").strip()
    for slug, pat, label_prefix in _FAMILIES:
        if pat.search(raw):
            m = _VERSION.search(raw)
            label = f"{label_prefix} {m.group(1)}.{m.group(2)}" if m else label_prefix
            return slug, label
    return (raw or "unknown"), (raw or "unknown")
