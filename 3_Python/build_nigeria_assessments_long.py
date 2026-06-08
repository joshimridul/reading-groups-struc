#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


ROOT = Path("/Users/mriduljoshi/Github/AbilityGrouping")
RAW = ROOT / "2_Data" / "1_Raw" / "P123 Numeracy Groups"
T2 = RAW / "term 2"
T3 = RAW / "term 3"
OUT = ROOT / "2_Data" / "2_Cleaned" / "Nigeria"


def clean_name(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        s = "col"
    if s[0].isdigit():
        s = f"v_{s}"
    return s[:32]


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    seen: Dict[str, int] = {}
    cols: List[str] = []
    for c in df.columns:
        k = clean_name(str(c))
        if k in seen:
            seen[k] += 1
            k = f"{k}_{seen[k]}"
        else:
            seen[k] = 1
        cols.append(k[:32])
    out = df.copy()
    out.columns = cols
    return out


def read_xlsx(path: Path) -> pd.DataFrame:
    return clean_columns(pd.read_excel(path))


def maybe_numeric(df: pd.DataFrame, cols: List[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")


def first_mode_or_na(s: pd.Series):
    s = s.dropna()
    if s.empty:
        return pd.NA
    m = s.mode()
    if m.empty:
        return pd.NA
    return m.iloc[0]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    assessments = {
        "t1_ete_maths": T2 / "Assessment Scores by Pupil - MASTER v2 (P123 T1 ETE Maths).xlsx",
        "t2_ete_maths": T2 / "Assessment Scores by Pupil - MASTER v2 (P123 T2 ETE Maths).xlsx",
        "t2_ete_numeracy": T2 / "Assessment Scores by Pupil - MASTER v2 (P123 T2 ETE Numeracy).xlsx",
        "t2_mte_maths": T2 / "Assessment Scores by Pupil - MASTER v2 (P123 T2 MTE Maths).xlsx",
        "t2_mte_numeracy": T2 / "Assessment Scores by Pupil - MASTER v2 (P123 T2 MTE Numeracy).xlsx",
        "t3_ete_maths": T3 / "Assessment Scores by Pupil - MASTER v2 (P123 T3 ETE Maths).xlsx",
        "t3_ete_numeracy": T3 / "Assessment Scores by Pupil - MASTER v2 (P123 T3 ETE Numeracy).xlsx",
        "t3_mte_maths": T3 / "Assessment Scores by Pupil - MASTER v2 (P123 T3 MTE Maths).xlsx",
        "t3_mte_numeracy": T3 / "Assessment Scores by Pupil - MASTER v2 (P123 T3 MTE Numeracy).xlsx",
    }

    long_parts: List[pd.DataFrame] = []
    for wave, path in assessments.items():
        df = read_xlsx(path)
        maybe_numeric(df, ["studyid", "academycode", "treatment", "assessmentid", "score", "maxscore", "percscore"])
        if "studyid" not in df.columns:
            raise RuntimeError(f"{path.name}: missing studyid")

        # Keep first row in rare duplicate cases.
        df = df.sort_values("studyid").drop_duplicates(subset=["studyid"], keep="first")
        df["wave"] = wave
        parts = wave.split("_")
        df["term"] = int(parts[0].replace("t", ""))
        df["assessment_window"] = parts[1]
        df["subject"] = "numeracy" if "numeracy" in wave else "mathematics"
        long_parts.append(df)

    long_df = pd.concat(long_parts, ignore_index=True, sort=False)

    # Harmonize treatment at academy level (mode).
    if "academycode" in long_df.columns and "treatment" in long_df.columns:
        t_mode = (
            long_df.dropna(subset=["academycode", "treatment"])
            .groupby("academycode")["treatment"]
            .agg(first_mode_or_na)
        )
        long_df["treatment_harmonized"] = long_df["academycode"].map(t_mode)
        long_df["treatment_harmonized"] = long_df["treatment_harmonized"].fillna(long_df["treatment"])
    else:
        long_df["treatment_harmonized"] = pd.NA

    # Harmonize geography fields by academy mode.
    for geo in ["constituency1", "county", "demographiclocation"]:
        if geo in long_df.columns and "academycode" in long_df.columns:
            g_mode = (
                long_df.dropna(subset=["academycode", geo])
                .groupby("academycode")[geo]
                .agg(first_mode_or_na)
            )
            long_df[f"{geo}_harm"] = long_df["academycode"].map(g_mode)
            long_df[geo] = long_df[geo].fillna(long_df[f"{geo}_harm"])

    # Stable, analysis-friendly ordering.
    first_cols = [
        c
        for c in [
            "studyid",
            "academycode",
            "treatment_harmonized",
            "treatment",
            "term",
            "assessment_window",
            "subject",
            "wave",
            "assessmentid",
            "title",
            "score",
            "maxscore",
            "percscore",
            "constituency1",
            "county",
            "demographiclocation",
            "gradename",
            "stream",
            "assessmenttype",
            "assessmentdate",
        ]
        if c in long_df.columns
    ]
    other_cols = [c for c in long_df.columns if c not in first_cols and not c.endswith("_harm")]
    long_df = long_df[first_cols + other_cols].copy()

    # Add compact labels for term/window.
    long_df["post_t1"] = np.where(long_df["term"] >= 2, 1, 0)
    long_df["t3"] = np.where(long_df["term"] == 3, 1, 0)

    out_csv = OUT / "ng_assessments_student_long.csv"
    out_dta = OUT / "ng_assessments_student_long.dta"
    out_note = OUT / "ng_assessments_student_long_note.md"

    long_df.to_csv(out_csv, index=False)
    long_df.to_stata(out_dta, write_index=False, version=118)

    # Small audit summary
    n_rows = len(long_df)
    n_students = long_df["studyid"].nunique() if "studyid" in long_df.columns else np.nan
    n_schools = long_df["academycode"].nunique() if "academycode" in long_df.columns else np.nan
    wave_counts = long_df["wave"].value_counts(dropna=False).sort_index()

    with open(out_note, "w", encoding="utf-8") as f:
        f.write("# Nigeria assessments long panel\n\n")
        f.write(f"- Rows: {n_rows:,}\n")
        f.write(f"- Unique students: {n_students:,}\n")
        f.write(f"- Unique schools: {n_schools:,}\n")
        f.write(f"- Waves: {long_df['wave'].nunique() if 'wave' in long_df.columns else 0}\n\n")
        f.write("## Rows by wave\n")
        for w, c in wave_counts.items():
            f.write(f"- {w}: {int(c):,}\n")

    print(f"Wrote: {out_csv}")
    print(f"Wrote: {out_dta}")
    print(f"Wrote: {out_note}")
    print(f"Rows={n_rows}, students={n_students}, schools={n_schools}")


if __name__ == "__main__":
    main()
