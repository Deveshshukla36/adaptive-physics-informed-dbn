"""Summaries of the NETL offshore pipeline and incident records used in Sec. IV-A.

Reads the EDX submission "U.S. Offshore Pipeline and Reported Incident Datasets"
(Romeo et al., NETL, doi:10.18141/2280823) from --data. Download the four files from
https://edx.netl.doe.gov/dataset/us-offshore-pipeline-and-reported-incident-datasets
(the version used in the paper was downloaded on 29 Sep 2026; see the SHA-256 in the output):

    pipeline_incidents.csv                  943 incident reports, 1986-2021
    pipeline_locations.csv                  points along BSEE pipeline segments
    pipeline_incidents_data_dictionary.csv  field definitions
    pipeline_location_data_dictionary.csv   field definitions

Nothing is imputed and the records are not split into training and test sets:
no model parameter is fitted to them. Each statistic uses the records in which
its field is reported, and the counts are written next to it.

Usage: python experiments/bsee_records.py --data ~/data/netl_pipelines
Writes results/bsee_records.json.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("pipeline_incidents.csv", "pipeline_locations.csv",
         "pipeline_incidents_data_dictionary.csv", "pipeline_location_data_dictionary.csv")
START, END = date(1986, 1, 1), date(2021, 12, 31)  # period covered by the incident reports
NEVER_INSTALLED = {"PROP", "CNCL"}  # BSEE status: proposed, cancelled
IN_PLACE = {"ACT", "OUT"}  # active, out of service: in place at the end of 2021 unless abandoned
SEGMENT_FIELDS = ("SEGMENT_LENGTH", "PPL_SIZE_C", "Stat_Cd", "Inst_Proxy", "Aban_Proxy", "Prod_Code")
CASE = {"diameter_in": 24.0, "wall_in": 0.75, "smys_psi": 52000.0}  # Table IV: 0.61 m, 19.1 mm, X52
C_FAIL_USD = 5.0e6  # Table V


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def in_range(x: float | None, lo: float, hi: float) -> float | None:
    """x if lo < x <= hi, else None (missing, zero or implausible)."""
    return x if x is not None and lo < x <= hi else None


def day(text: str) -> date | None:
    text = text.strip()
    return datetime.strptime(text.split()[0], "%m/%d/%Y").date() if text else None


def years_between(a: date, b: date) -> float:
    return max(0.0, (b - a).days / 365.25)


def incidents(path: Path) -> dict:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
    year = [int(re.search(r"\d{4}", r["Local_Date_Time"]).group()) for r in rows]
    blocks = [re.sub(r"\s+", "", r["OCS_Lease_Block"]).upper() for r in rows]
    yes = lambda field: sum(r[field] == "YES" for r in rows)  # noqa: E731

    diameter = [in_range(number(r["Pipe_Diameter"]), 0, float("inf")) for r in rows]
    wall = [in_range(number(r["Pipe_Wall_Thickness"]), 0, 2) for r in rows]
    smys = []
    for r in rows:
        s = number(r["Pipe_SMYS"])
        if s is not None and 0 < s < 1000:  # a few reports give SMYS in ksi
            s *= 1000
        smys.append(in_range(s, 0, 120000))
    cost = sorted(c for c in (number(r["Total_Cost_2021_USD"]) for r in rows) if c is not None and c > 0)

    d = sorted(x for x in diameter if x)
    w = sorted(x for x in wall if x)
    s = [x for x in smys if x]
    return {
        "records": len(rows),
        "fields": len(rows[0]),
        "by_source": dict(Counter(r["Original_Source"] for r in rows)),
        "years": [min(year), max(year)],
        "per_year": dict(sorted(Counter(year).items())),
        "with_lease_block": sum(bool(b) for b in blocks),
        "distinct_lease_blocks": len({b for b in blocks if b}),
        "internal_corrosion": yes("Internal_Corrosion_Flag"),
        "external_corrosion": yes("External_Corrosion_Flag"),
        "any_corrosion": sum(r["Internal_Corrosion_Flag"] == "YES" or r["External_Corrosion_Flag"] == "YES"
                             for r in rows),
        "outside_force_damage": yes("Outside_Force_Damage_Flag"),
        "diameter_in": {"reported": len(d), "median": statistics.median(d),
                        "at_least_case": sum(x >= CASE["diameter_in"] for x in d)},
        "wall_in": {"reported": len(w), "empty": sum(not r["Pipe_Wall_Thickness"].strip() for r in rows),
                    "median": statistics.median(w), "at_least_case": sum(x >= CASE["wall_in"] for x in w)},
        "smys_psi": {"reported": len(s), "most_common": Counter(s).most_common(3),
                     "case_grade": sum(x == CASE["smys_psi"] for x in s)},
        "cost_2021_usd": {"positive": len(cost), "median": statistics.median(cost),
                          "mean": statistics.fmean(cost), "max": cost[-1],
                          "below_c_fail": sum(c < C_FAIL_USD for c in cost)},
    }


def locations(path: Path) -> dict:
    segments: dict[str, dict] = {}
    conflicts = Counter()
    points = 0
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        columns = len(reader.fieldnames)
        for r in reader:
            points += 1
            seg = segments.setdefault(r["SEGMENT_NUM"], {k: r[k] for k in SEGMENT_FIELDS})
            for k in SEGMENT_FIELDS:
                if r[k] != seg[k]:
                    conflicts[k] += 1

    installed = {k: v for k, v in segments.items() if v["Stat_Cd"].strip() not in NEVER_INSTALLED}
    size = [number(v["PPL_SIZE_C"]) for v in installed.values()]
    size = sorted(x for x in size if x and x > 0)
    length_km = sum(number(v["SEGMENT_LENGTH"]) or 0.0 for v in installed.values()) * 0.3048 / 1000

    exposure, known = 0.0, 0
    for v in installed.values():
        start, stop = day(v["Inst_Proxy"]), day(v["Aban_Proxy"])
        if start is None:
            continue
        if stop is None:
            if v["Stat_Cd"].strip() not in IN_PLACE:
                continue  # removed or abandoned on an unknown date
            stop = END
        known += 1
        exposure += years_between(max(start, START), min(stop, END))
    return {
        "points": points,
        "columns": columns,
        "segments": len(segments),
        "conflicting_segment_values": dict(conflicts),
        "status": dict(Counter(v["Stat_Cd"].strip() for v in segments.values()).most_common()),
        "installed_segments": len(installed),
        "installed_length_km": length_km,
        "size_code": {"numeric": len(size), "median_in": statistics.median(size),
                      "at_least_case": sum(x >= CASE["diameter_in"] for x in size)},
        "exposure": {"segments": known, "segment_years": exposure},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True, help="folder with the four EDX files")
    args = ap.parse_args()
    missing = [f for f in FILES if not (args.data / f).exists()]
    if missing:
        sys.exit(f"missing in {args.data}: {', '.join(missing)}")

    inc = incidents(args.data / "pipeline_incidents.csv")
    loc = locations(args.data / "pipeline_locations.csv")
    res = {
        "source": "https://edx.netl.doe.gov/dataset/us-offshore-pipeline-and-reported-incident-datasets",
        "doi": "10.18141/2280823",
        "sha256": {f: sha256(args.data / f) for f in FILES},
        "incidents": inc,
        "locations": loc,
        "incidents_per_segment_year": inc["records"] / loc["exposure"]["segment_years"],
        "c_fail_percentile": 100 * inc["cost_2021_usd"]["below_c_fail"] / inc["cost_2021_usd"]["positive"],
    }
    out = ROOT / "results" / "bsee_records.json"
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
