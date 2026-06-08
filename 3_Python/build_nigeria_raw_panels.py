#!/usr/bin/env python3
"""
Build cleaned Nigeria raw-data panels from term 2 / term 3 folders.

Outputs are written to:
  2_Data/2_Cleaned/Nigeria/

The script:
1) Builds a suffix-safe student assessment wide file across all tests.
2) Harmonizes fixed vars using baseline-first fill and audits instability.
3) Builds domain-specific panels for academy manager attendance, teacher
   attendance, PTR, lesson completion, and attendance files.
4) Writes the T3 item-level numeracy file separately.
5) Produces an internal audit markdown + csv summary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

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
    df = df.copy()
    df.columns = cols
    return df


def stata_safe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce Stata naming constraints after suffixing/truncation:
    - <= 32 chars
    - lowercase alnum + underscore
    - unique
    - avoid reserved words
    """
    reserved = {
        "_all",
        "_b",
        "_se",
        "_n",
        "_N",
        "_pi",
        "_skip",
        "using",
        "if",
        "in",
        "byte",
        "int",
        "long",
        "float",
        "double",
        "str",
        "strL",
        "class",
    }
    out = df.copy()
    seen: Dict[str, int] = {}
    new_cols: List[str] = []
    for col in out.columns:
        base = clean_name(str(col))[:32]
        if base in reserved:
            base = f"v_{base}"[:32]
        name = base
        while name in seen:
            seen[base] += 1
            suf = f"_{seen[base]}"
            name = f"{base[: max(1, 32 - len(suf))]}{suf}"
        seen.setdefault(base, 1)
        seen[name] = 1
        new_cols.append(name)
    out.columns = new_cols
    return out


def read_xlsx(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path)
    return clean_columns(df)


def maybe_numeric(df: pd.DataFrame, cols: Iterable[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")


def maybe_datetime(df: pd.DataFrame, cols: Iterable[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")


def add_stata_labels(
    path: Path,
    df: pd.DataFrame,
    var_labels: Dict[str, str] | None = None,
    value_labels: Dict[str, Dict[int, str]] | None = None,
) -> None:
    var_labels = var_labels or {}
    value_labels = value_labels or {}
    df = stata_safe_columns(df)
    auto_labels = {c: c.replace("_", " ").strip() for c in df.columns}
    auto_labels.update(var_labels)
    df.to_stata(
        str(path),
        write_index=False,
        version=118,
        variable_labels={k: v for k, v in auto_labels.items() if k in df.columns},
        value_labels={k: v for k, v in value_labels.items() if k in df.columns},
        convert_dates={"date" + k: "td" for k in []},
    )


@dataclass
class AuditRow:
    dataset: str
    metric: str
    value: str


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    audit_rows: List[AuditRow] = []

    # ------------------------------------------------------------------
    # 1) Assessments: suffix-safe student wide panel
    # ------------------------------------------------------------------
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

    key = "studyid"
    merged: pd.DataFrame | None = None
    assessment_cols_by_wave: Dict[str, List[str]] = {}

    for wave, path in assessments.items():
        df = read_xlsx(path)
        if key not in df.columns:
            raise RuntimeError(f"{path.name}: missing {key}")
        if df[key].duplicated().any():
            # keep first row per student if duplicates exist (e.g., T3 MTE maths)
            df = df.sort_values(key).drop_duplicates(subset=[key], keep="first")

        maybe_numeric(
            df,
            [
                "academycode",
                "studyid",
                "treatment",
                "assessmentid",
                "score",
                "maxscore",
                "percscore",
            ],
        )
        maybe_datetime(df, ["assessmentdate", "enrolled_date"])

        id_like = [key]
        wave_cols = [c for c in df.columns if c not in id_like]
        assessment_cols_by_wave[wave] = wave_cols
        rename = {c: f"{c}_{wave}" for c in wave_cols}
        dsw = df.rename(columns=rename)

        merged = dsw if merged is None else merged.merge(dsw, on=[key], how="outer", validate="1:1")

        audit_rows.append(AuditRow("assessments", f"rows_{wave}", str(len(df))))
        audit_rows.append(AuditRow("assessments", f"students_{wave}", str(df[key].nunique())))
        if "academycode" in df.columns:
            audit_rows.append(AuditRow("assessments", f"academies_{wave}", str(df["academycode"].nunique())))

    assert merged is not None

    # Harmonize fixed vars: baseline-first, then forward-fill from other waves.
    fixed_vars = [
        "academycode",
        "treatment",
        "constituency1",
        "county",
        "demographiclocation",
        "academy_cohort",
        "term_period",
        "religiouseducationsubject",
        "enrolled_date",
        "gradename",
        "stream",
    ]
    preferred_wave = "t1_ete_maths"
    wave_order = list(assessments.keys())

    harm = merged.copy()
    change_summary: Dict[str, int] = {}
    for v in fixed_vars:
        cols = [f"{v}_{w}" for w in wave_order if f"{v}_{w}" in harm.columns]
        if not cols:
            continue
        # count instability among non-missing values
        row_nuniq = harm[cols].apply(
            lambda r: pd.Series(r.dropna().astype(str).unique()).nunique(), axis=1
        )
        change_summary[v] = int((row_nuniq > 1).sum())

        first = f"{v}_{preferred_wave}" if f"{v}_{preferred_wave}" in harm.columns else cols[0]
        out = harm[first].copy()
        for c in cols:
            out = out.fillna(harm[c])
        harm[v] = out

    # Second-pass academy-level fill from term-level operational sheets.
    # Use explicit geography columns where available:
    # - PTR T2: county/constituency
    # - Roster T2/T3: leveltwo (matches constituency), levelthree
    # - Manager attendance T2/T3: region (matches constituency)
    ptr_t2_raw = read_xlsx(T2 / "PTR by Classroom (P123 T2).xlsx")
    ros_t2_raw = read_xlsx(T2 / "Roster of Pupils (P123 T2).xlsx")
    ros_t3_raw = read_xlsx(T3 / "Roster of Pupils (P123 T3).xlsx")
    mgr_t2_raw = read_xlsx(T2 / "Academy Manager Attendance Summary (T2).xlsx")
    mgr_t3_raw = read_xlsx(T3 / "Academy Manager Attendance Summary (T3).xlsx")

    for d in [ptr_t2_raw, ros_t2_raw, ros_t3_raw, mgr_t2_raw, mgr_t3_raw]:
        maybe_numeric(d, ["academycode", "treatment"])

    ptr_map = (
        ptr_t2_raw[[c for c in ["academycode", "county", "constituency"] if c in ptr_t2_raw.columns]]
        .dropna(subset=["academycode"])
        .drop_duplicates()
    )
    if not ptr_map.empty:
        ptr_map = ptr_map.groupby("academycode", as_index=False).agg(
            {c: (lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA) for c in ptr_map.columns if c != "academycode"}
        )

    ros = pd.concat([ros_t2_raw, ros_t3_raw], ignore_index=True, sort=False)
    ros_map = (
        ros[[c for c in ["academycode", "leveltwo", "levelthree", "treatment"] if c in ros.columns]]
        .dropna(subset=["academycode"])
        .drop_duplicates()
    )
    if not ros_map.empty:
        ros_map = ros_map.groupby("academycode", as_index=False).agg(
            {c: (lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA) for c in ros_map.columns if c != "academycode"}
        )

    mgr = pd.concat([mgr_t2_raw, mgr_t3_raw], ignore_index=True, sort=False)
    mgr_map = (
        mgr[[c for c in ["academycode", "region", "treatment"] if c in mgr.columns]]
        .dropna(subset=["academycode"])
        .drop_duplicates()
    )
    if not mgr_map.empty:
        mgr_map = mgr_map.groupby("academycode", as_index=False).agg(
            {c: (lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA) for c in mgr_map.columns if c != "academycode"}
        )

    # Merge helper maps
    acad_map = pd.DataFrame({"academycode": pd.to_numeric(harm["academycode"], errors="coerce")}).dropna().drop_duplicates()
    if not ptr_map.empty:
        acad_map = acad_map.merge(ptr_map, on="academycode", how="left")
    if not ros_map.empty:
        acad_map = acad_map.merge(ros_map, on="academycode", how="left", suffixes=("", "_ros"))
    if not mgr_map.empty:
        acad_map = acad_map.merge(mgr_map, on="academycode", how="left", suffixes=("", "_mgr"))

    # Fill treatment from academy-level maps if missing, then enforce academy-level mode.
    if "treatment" in harm.columns:
        t_fill = harm["academycode"].map(acad_map.set_index("academycode").get("treatment"))
        if "treatment_ros" in acad_map.columns:
            t_fill = t_fill.fillna(harm["academycode"].map(acad_map.set_index("academycode")["treatment_ros"]))
        if "treatment_mgr" in acad_map.columns:
            t_fill = t_fill.fillna(harm["academycode"].map(acad_map.set_index("academycode")["treatment_mgr"]))
        harm["treatment"] = pd.to_numeric(harm["treatment"], errors="coerce").fillna(t_fill)
        # enforce academy-level mode as final harmonization
        mode_t = (
            harm.dropna(subset=["academycode", "treatment"])
            .groupby("academycode")["treatment"]
            .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA)
        )
        harm["treatment"] = harm["academycode"].map(mode_t).fillna(harm["treatment"])

    # Fill constituency/county/geography with academy-level maps.
    if "constituency1" in harm.columns:
        c_fill = harm["academycode"].map(acad_map.set_index("academycode").get("constituency"))
        if "leveltwo" in acad_map.columns:
            c_fill = c_fill.fillna(harm["academycode"].map(acad_map.set_index("academycode")["leveltwo"]))
        if "region" in acad_map.columns:
            c_fill = c_fill.fillna(harm["academycode"].map(acad_map.set_index("academycode")["region"]))
        harm["constituency1"] = harm["constituency1"].fillna(c_fill)
    if "county" in harm.columns and "county" in acad_map.columns:
        harm["county"] = harm["county"].fillna(harm["academycode"].map(acad_map.set_index("academycode")["county"]))

    # Post-harmonization academy-level consistency audit
    for v in ["treatment", "constituency1", "county"]:
        if v in harm.columns:
            tmp = harm.dropna(subset=["academycode", v]).groupby("academycode")[v].nunique()
            audit_rows.append(AuditRow("assessments_post_consistency", f"{v}_academy_nuniq_gt1", str(int((tmp > 1).sum()))))

    # Baseline aliases used often in analysis
    if "score_t1_ete_maths" in harm.columns:
        harm["score_bl"] = harm["score_t1_ete_maths"]
    if "percscore_t1_ete_maths" in harm.columns:
        harm["percscore_bl"] = harm["percscore_t1_ete_maths"]
    if "score_t3_ete_numeracy" in harm.columns:
        harm["score_el_num_t3"] = harm["score_t3_ete_numeracy"]
    if "percscore_t3_ete_numeracy" in harm.columns:
        harm["percscore_el_num_t3"] = harm["percscore_t3_ete_numeracy"]

    # Types / labels
    maybe_numeric(harm, ["studyid", "academycode", "treatment"])
    if "treatment" in harm.columns:
        harm["treatment"] = pd.to_numeric(harm["treatment"], errors="coerce")
        harm["treatment"] = harm["treatment"].astype("Int64")

    harm = stata_safe_columns(harm)
    assess_wide = OUT / "ng_assessments_student_wide.dta"
    var_labels = {
        "studyid": "Pupil Study ID",
        "academycode": "Academy code (harmonized)",
        "treatment": "Treatment status (harmonized; baseline-first)",
        "score_bl": "Baseline score (T1 ETE Maths)",
        "percscore_bl": "Baseline percent score (T1 ETE Maths)",
        "score_el_num_t3": "Term 3 end-term numeracy raw score",
        "percscore_el_num_t3": "Term 3 end-term numeracy percent score",
    }
    value_labels = {"treatment": {0: "Control", 1: "Treatment"}}
    add_stata_labels(assess_wide, harm, var_labels=var_labels, value_labels=value_labels)

    audit_rows.append(AuditRow("assessments", "students_wide", str(harm["studyid"].nunique())))
    audit_rows.append(
        AuditRow(
            "assessments",
            "missing_treatment_after_fill",
            str(int(harm["treatment"].isna().sum())) if "treatment" in harm.columns else "NA",
        )
    )
    if "constituency1" in harm.columns:
        audit_rows.append(AuditRow("assessments", "missing_constituency_after_fill", str(int(harm["constituency1"].isna().sum()))))
    if "county" in harm.columns:
        audit_rows.append(AuditRow("assessments", "missing_county_after_fill", str(int(harm["county"].isna().sum()))))
    for v, n in change_summary.items():
        audit_rows.append(AuditRow("assessments_fixedvar_changes", v, str(n)))

    # ------------------------------------------------------------------
    # 2) Academy manager attendance (academy x term)
    # ------------------------------------------------------------------
    am_t2 = read_xlsx(T2 / "Academy Manager Attendance Summary (T2).xlsx")
    am_t3 = read_xlsx(T3 / "Academy Manager Attendance Summary (T3).xlsx")
    maybe_numeric(am_t2, ["academycode", "treatment", "attendance_average", "attendance_arrived", "attendance_departed"])
    maybe_numeric(am_t3, ["academycode", "treatment", "attendance_average", "attendance_arrived", "attendance_departed"])

    am_t2 = am_t2.rename(columns={c: f"{c}_t2" for c in am_t2.columns if c != "academycode"})
    am_t3 = am_t3.rename(columns={c: f"{c}_t3" for c in am_t3.columns if c != "academycode"})
    am = am_t2.merge(am_t3, on="academycode", how="outer", validate="1:1")
    if "treatment_t2" in am.columns or "treatment_t3" in am.columns:
        am["treatment"] = am.get("treatment_t2", pd.Series(index=am.index)).fillna(am.get("treatment_t3"))
    am = stata_safe_columns(am)
    add_stata_labels(
        OUT / "ng_academy_manager_attendance_wide.dta",
        am,
        var_labels={"treatment": "Treatment status (baseline-first fill across terms)"},
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    audit_rows.append(AuditRow("academy_manager_attendance", "rows", str(len(am))))
    audit_rows.append(AuditRow("academy_manager_attendance", "academies", str(am["academycode"].nunique())))

    # ------------------------------------------------------------------
    # 3) Teacher attendance (academy x grade x term)
    # ------------------------------------------------------------------
    tch_t2 = read_xlsx(T2 / "Teacher Attendance Summary (P123 T2).xlsx")
    tch_t3 = read_xlsx(T3 / "Teacher Attendance Summary (P123 T3).xlsx")
    maybe_numeric(
        tch_t2,
        [
            "academycode",
            "treatment",
            "attendance_academy_average",
            "attendance_academy_arrived",
            "attendance_academy_departed",
            "attendance_grade_average",
            "attendance_grade_arrived",
            "attendance_grade_departed",
        ],
    )
    maybe_numeric(
        tch_t3,
        [
            "academycode",
            "treatment",
            "attendance_academy_average",
            "attendance_academy_arrived",
            "attendance_academy_departed",
            "attendance_grade_average",
            "attendance_grade_arrived",
            "attendance_grade_departed",
        ],
    )
    k_tch = ["academycode", "gradename"]
    tch_t2 = tch_t2.rename(columns={c: f"{c}_t2" for c in tch_t2.columns if c not in k_tch})
    tch_t3 = tch_t3.rename(columns={c: f"{c}_t3" for c in tch_t3.columns if c not in k_tch})
    tch = tch_t2.merge(tch_t3, on=k_tch, how="outer", validate="1:1")
    if "treatment_t2" in tch.columns or "treatment_t3" in tch.columns:
        tch["treatment"] = tch.get("treatment_t2", pd.Series(index=tch.index)).fillna(tch.get("treatment_t3"))
    tch = stata_safe_columns(tch)
    add_stata_labels(
        OUT / "ng_teacher_attendance_wide.dta",
        tch,
        var_labels={"treatment": "Treatment status (baseline-first fill across terms)"},
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    audit_rows.append(AuditRow("teacher_attendance", "rows", str(len(tch))))

    # ------------------------------------------------------------------
    # 4) PTR by classroom (academy x grade x classroom x term)
    # ------------------------------------------------------------------
    ptr_t2 = read_xlsx(T2 / "PTR by Classroom (P123 T2).xlsx")
    ptr_t3 = read_xlsx(T3 / "PTR by Classroom (P123 T3).xlsx")
    maybe_numeric(ptr_t2, ["academycode", "treatment", "enrollment_academy", "teachers_academy", "ptr_academy", "classrooms", "ptr"])
    maybe_numeric(ptr_t3, ["academycode", "treatment", "enrollment_academy", "teachers_academy", "ptr_academy", "classrooms", "ptr"])
    k_ptr = [c for c in ["academycode", "gradename", "classroom"] if c in ptr_t2.columns and c in ptr_t3.columns]
    ptr_t2 = ptr_t2.rename(columns={c: f"{c}_t2" for c in ptr_t2.columns if c not in k_ptr})
    ptr_t3 = ptr_t3.rename(columns={c: f"{c}_t3" for c in ptr_t3.columns if c not in k_ptr})
    ptr = ptr_t2.merge(ptr_t3, on=k_ptr, how="outer")
    if "treatment_t2" in ptr.columns or "treatment_t3" in ptr.columns:
        ptr["treatment"] = ptr.get("treatment_t2", pd.Series(index=ptr.index)).fillna(ptr.get("treatment_t3"))
    ptr = stata_safe_columns(ptr)
    add_stata_labels(
        OUT / "ng_ptr_classroom_wide.dta",
        ptr,
        var_labels={"treatment": "Treatment status (baseline-first fill across terms)"},
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    audit_rows.append(AuditRow("ptr", "rows", str(len(ptr))))

    # ------------------------------------------------------------------
    # 5) Lesson completion
    # ------------------------------------------------------------------
    lc_sum_t2 = read_xlsx(T2 / "Lesson Completion (Aligned) Report (P123 T2).xlsx")
    maybe_numeric(lc_sum_t2, ["academycode", "treatment", "lessons_completed", "data_collected"])
    lc_sum_t2 = stata_safe_columns(lc_sum_t2)
    add_stata_labels(
        OUT / "ng_lesson_completion_summary_t2.dta",
        lc_sum_t2,
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    audit_rows.append(AuditRow("lesson_completion_summary_t2", "rows", str(len(lc_sum_t2))))

    lc_det_t2 = read_xlsx(T2 / "Lesson Completion Detail (Aligned) Report (P123 T2).xlsx")
    lc_det_t3 = read_xlsx(T3 / "Lesson Completion Detail (Aligned) Report (P123 T3).xlsx")
    lc_det_t2["term"] = 2
    lc_det_t3["term"] = 3
    lc_det = pd.concat([lc_det_t2, lc_det_t3], ignore_index=True, sort=False)
    maybe_numeric(
        lc_det,
        [
            "academycode",
            "treatment",
            "percentage_completed",
            "expect_duration_mins",
            "actual_duration_mins",
            "time_difference_mins",
            "time_difference_percentage",
        ],
    )
    maybe_datetime(lc_det, ["date", "start_time", "actual_start"])
    lc_det = stata_safe_columns(lc_det)
    add_stata_labels(
        OUT / "ng_lesson_completion_detail_long.dta",
        lc_det,
        var_labels={"term": "Term (2/3)"},
        value_labels={"treatment": {0: "Control", 1: "Treatment"}, "term": {2: "Term 2", 3: "Term 3"}},
    )
    audit_rows.append(AuditRow("lesson_completion_detail", "rows", str(len(lc_det))))

    # ------------------------------------------------------------------
    # 6) Attendance / roster datasets (units differ, keep separate)
    # ------------------------------------------------------------------
    pupil_att_t2 = read_xlsx(T2 / "Student Attendance by Gender By Streams Summary (P123 T2).xlsx")
    pupil_att_t3 = read_xlsx(T3 / "Pupil Attendance (P123 T3).xlsx")
    maybe_numeric(pupil_att_t2, ["academycode", "attendance_percent_grade", "treatment"])
    maybe_numeric(pupil_att_t3, ["academycode", "studyid", "attrecords", "present", "classdays", "treatment"])
    pupil_att_t2 = stata_safe_columns(pupil_att_t2)
    add_stata_labels(
        OUT / "ng_pupil_attendance_summary_t2.dta",
        pupil_att_t2,
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    pupil_att_t3 = stata_safe_columns(pupil_att_t3)
    add_stata_labels(
        OUT / "ng_pupil_attendance_student_t3.dta",
        pupil_att_t3,
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    audit_rows.append(AuditRow("pupil_attendance_t2_summary", "rows", str(len(pupil_att_t2))))
    audit_rows.append(AuditRow("pupil_attendance_t3_student", "rows", str(len(pupil_att_t3))))

    roster_t2 = read_xlsx(T2 / "Roster of Pupils (P123 T2).xlsx")
    roster_t3 = read_xlsx(T3 / "Roster of Pupils (P123 T3).xlsx")
    maybe_numeric(roster_t2, ["academycode", "studyid", "treatment", "placementexamscore"])
    maybe_numeric(roster_t3, ["academycode", "studyid", "treatment", "placementexamscore"])
    k_ros = [c for c in ["academycode", "studyid"] if c in roster_t2.columns and c in roster_t3.columns]
    r2 = roster_t2.rename(columns={c: f"{c}_t2" for c in roster_t2.columns if c not in k_ros})
    r3 = roster_t3.rename(columns={c: f"{c}_t3" for c in roster_t3.columns if c not in k_ros})
    roster = r2.merge(r3, on=k_ros, how="outer", validate="1:1")
    if "treatment_t2" in roster.columns or "treatment_t3" in roster.columns:
        roster["treatment"] = roster.get("treatment_t2", pd.Series(index=roster.index)).fillna(roster.get("treatment_t3"))
    roster = stata_safe_columns(roster)
    add_stata_labels(
        OUT / "ng_roster_student_wide.dta",
        roster,
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    audit_rows.append(AuditRow("roster", "rows", str(len(roster))))

    # ------------------------------------------------------------------
    # 7) Item-level dataset (own dataset)
    # ------------------------------------------------------------------
    item = read_xlsx(T3 / "(Item Level Data) P123 Numeracy T3 ETE.xlsx")
    maybe_numeric(item, ["academycode", "studyid", "treatment", "grade"])
    # Convert all q* columns numeric where possible
    qcols = [c for c in item.columns if re.match(r"^q[0-9]+(_a)?$", c)]
    maybe_numeric(item, qcols)
    item = stata_safe_columns(item)
    add_stata_labels(
        OUT / "ng_itemlevel_t3_ete_numeracy.dta",
        item,
        var_labels={
            "academycode": "Academy code",
            "studyid": "Pupil Study ID",
            "treatment": "Treatment status from raw item file",
            "grade": "Grade",
        },
        value_labels={"treatment": {0: "Control", 1: "Treatment"}},
    )
    audit_rows.append(AuditRow("item_level_t3_ete_numeracy", "rows", str(len(item))))
    audit_rows.append(AuditRow("item_level_t3_ete_numeracy", "students", str(item["studyid"].nunique() if "studyid" in item else "NA")))

    # ------------------------------------------------------------------
    # 8) Merge integrity and internal audit outputs
    # ------------------------------------------------------------------
    # Simple merge checks against harmonized assessment student file
    if "studyid" in harm.columns:
        harm_ids = set(harm["studyid"].dropna().astype(int).tolist())
        roster_ids = set(roster["studyid"].dropna().astype(int).tolist()) if "studyid" in roster.columns else set()
        inter = len(harm_ids & roster_ids)
        audit_rows.append(AuditRow("merge_check_assessment_vs_roster", "assessment_ids", str(len(harm_ids))))
        audit_rows.append(AuditRow("merge_check_assessment_vs_roster", "roster_ids", str(len(roster_ids))))
        audit_rows.append(AuditRow("merge_check_assessment_vs_roster", "intersection_ids", str(inter)))

    audit_df = pd.DataFrame([r.__dict__ for r in audit_rows])
    audit_df.to_csv(OUT / "ng_build_audit.csv", index=False)

    # Markdown audit summary
    lines = [
        "# Nigeria Build Audit",
        "",
        f"- Output directory: `{OUT}`",
        f"- Assessment student-wide rows: {len(harm):,}",
        f"- Assessment student-wide unique studyid: {harm['studyid'].nunique():,}" if "studyid" in harm else "- Assessment student-wide unique studyid: NA",
        "",
        "## Fixed-variable instability counts (non-missing disagreements across waves)",
    ]
    for v in fixed_vars:
        if v in change_summary:
            lines.append(f"- `{v}`: {change_summary[v]:,}")
    lines += [
        "",
        "## Generated datasets",
        "- `ng_assessments_student_wide.dta`",
        "- `ng_academy_manager_attendance_wide.dta`",
        "- `ng_teacher_attendance_wide.dta`",
        "- `ng_ptr_classroom_wide.dta`",
        "- `ng_lesson_completion_summary_t2.dta`",
        "- `ng_lesson_completion_detail_long.dta`",
        "- `ng_pupil_attendance_summary_t2.dta`",
        "- `ng_pupil_attendance_student_t3.dta`",
        "- `ng_roster_student_wide.dta`",
        "- `ng_itemlevel_t3_ete_numeracy.dta`",
        "",
        "## Notes",
        "- All variable names are lower snake_case and truncated to <=32 chars for Stata compatibility.",
        "- `treatment` in harmonized datasets is baseline-first then forward-filled from later terms.",
        "- Detailed audit metrics are in `ng_build_audit.csv`.",
    ]
    (OUT / "ng_build_audit.md").write_text("\n".join(lines))

    print("Nigeria panels built successfully.")
    print(f"Output folder: {OUT}")


if __name__ == "__main__":
    main()

