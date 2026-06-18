#!/usr/bin/env python3
"""Fetch the Bundesliga 2025/26 table and print it as a clean formatted table.

Data source: OpenLigaDB (https://www.openligadb.de) — a free, community-run
JSON API for German football. No API key required.

Usage:
    python3 bundesliga_table.py            # current (2025/26) season, 1. Bundesliga
    python3 bundesliga_table.py --season 2024
    python3 bundesliga_table.py --league bl2   # 2. Bundesliga
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import requests

API_URL = "https://api.openligadb.de/getbltable/{league}/{season}"
TIMEOUT = 20
HEADERS = {"User-Agent": "bundesliga-table/1.0 (+https://www.openligadb.de)"}


def fetch_table(league: str, season: str) -> list[dict[str, Any]]:
    """Return the raw standings list from OpenLigaDB."""
    url = API_URL.format(league=league, season=season)
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list) or not data:
        raise ValueError(f"No table data returned for league={league} season={season}")
    return data


def normalize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reduce the raw API rows to just the fields we render."""
    table = []
    for row in rows:
        table.append(
            {
                "team": row.get("shortName") or row.get("teamName", "?"),
                "played": int(row.get("matches", 0)),
                "won": int(row.get("won", 0)),
                "draw": int(row.get("draw", 0)),
                "lost": int(row.get("lost", 0)),
                "gf": int(row.get("goals", 0)),
                "ga": int(row.get("opponentGoals", 0)),
                "gd": int(row.get("goalDiff", 0)),
                "points": int(row.get("points", 0)),
            }
        )
    return table


def render(table: list[dict[str, Any]], title: str) -> str:
    """Render the standings as a clean fixed-width text table."""
    headers = ["#", "Team", "Pl", "W", "D", "L", "GF", "GA", "GD", "Pts"]
    name_w = max(len(headers[1]), max(len(r["team"]) for r in table))

    def fmt_row(cells: list[str]) -> str:
        c = cells
        return (
            f"{c[0]:>2}  {c[1]:<{name_w}}  "
            f"{c[2]:>2} {c[3]:>2} {c[4]:>2} {c[5]:>2}  "
            f"{c[6]:>3} {c[7]:>3} {c[8]:>4}  {c[9]:>3}"
        )

    header_line = fmt_row(headers)
    sep = "-" * len(header_line)
    lines = [title, sep, header_line, sep]
    for i, r in enumerate(table, start=1):
        gd = f"+{r['gd']}" if r["gd"] > 0 else str(r["gd"])
        lines.append(
            fmt_row(
                [
                    str(i),
                    r["team"],
                    str(r["played"]),
                    str(r["won"]),
                    str(r["draw"]),
                    str(r["lost"]),
                    str(r["gf"]),
                    str(r["ga"]),
                    gd,
                    str(r["points"]),
                ]
            )
        )
    lines.append(sep)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the Bundesliga table.")
    parser.add_argument("--league", default="bl1", help="bl1 (default) or bl2")
    parser.add_argument("--season", default="2025", help="Season start year, e.g. 2025 for 2025/26")
    args = parser.parse_args(argv)

    season_label = f"{args.season}/{str(int(args.season) + 1)[-2:]}"
    league_label = {"bl1": "1. Bundesliga", "bl2": "2. Bundesliga"}.get(args.league, args.league)
    title = f"{league_label} — Season {season_label}"

    try:
        rows = fetch_table(args.league, args.season)
    except requests.RequestException as exc:
        print(f"Error fetching data: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    table = normalize(rows)
    print(render(table, title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
