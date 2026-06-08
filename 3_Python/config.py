"""
config.py — Paths, constants, and experimental parameters.
Stata analogue: the globals block in _master.do.

Supports: "liberia", "kenya" (2-grade composite), "kenya2" (2019 3-grade single-score),
           "nigeria" (Lagos P123 numeracy groups, 2021).
Pass country name via command line or use get_config(country).
"""
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent          # repo root
OUT  = Path(__file__).resolve().parent / "output"
OUT.mkdir(exist_ok=True)

# ── Inference ────────────────────────────────────────────────────────────────
SEED = 42


def get_config(country=None):
    """Return a dict of country-specific configuration."""
    if country is None:
        country = sys.argv[1] if len(sys.argv) > 1 else "liberia"
    country = country.lower()

    if country == "liberia":
        RAW = ROOT / "2_Data" / "1_Raw" / "Liberia"
        return dict(
            country="liberia",
            label="Liberia",
            RAW=RAW,
            ANALYSIS_FILE=OUT / "analysis_liberia.parquet",
            OUT_PREFIX="lib_",
            # Raw file paths
            FILE_BL=RAW / "LR_G1234_S1_BaselineData_Blinded.csv",
            FILE_ML=RAW / "LR_G1234_S1_ETE_Blinded.csv",
            FILE_EL=RAW / "LR_G1234_S2_EndlineData_Blinded.csv",
            FILE_ATTN=RAW / "LR_G1234_2019_PupilAttendance_Blinded.csv",
            FILE_LP=RAW / "LR_G1234_2019_LessonCompletion_Blinded.csv",
            FILE_TCH=RAW / "LR_G1_2019_TeacherAttendance_Blinded.csv",
            FILE_MGR=RAW / "LR_2019_AcademyManagerAttendance_Blinded.csv",
            FILE_LOC=RAW / "updated academy locations.xlsx",
            # Experimental parameters
            grades=[1, 2, 3, 4],
            grade_groups={"g12": [1, 2], "g34": [3, 4]},
            cutoffs={1: 23, 2: 23, 3: 14, 4: 14},  # per grade
            cutoff_g12=23,
            cutoff_g34=14,
            strata_vars=["acad_year", "g12"],
            cluster_var="ggroup",
            cohort_threshold="2016-11-22",
            has_midline=True,
            score_type="single",   # single score per wave
        )

    elif country == "kenya":
        RAW = ROOT / "2_Data" / "1_Raw" / "Kenya"
        return dict(
            country="kenya",
            label="Kenya",
            RAW=RAW,
            ANALYSIS_FILE=OUT / "analysis_kenya.parquet",
            OUT_PREFIX="ke_",
            # Raw file paths (Grade 1 Reading Club + Grade 2 Reading Club)
            FILE_G1_BL_LIT=RAW / "Grade 1 Reading Club" / "KE_G1_T2_Literacy_Midterm_Blinded.csv",
            FILE_G1_BL_ENG=RAW / "Grade 1 Reading Club" / "KE_G1_T2_English Language_Midterm_Blinded.csv",
            FILE_G2_BL_LIT=RAW / "Grade 2 Reading Club" / "KE_G2_T2_Literacy_Midterm_Blinded.csv",
            FILE_G2_BL_ENG=RAW / "Grade 2 Reading Club" / "KE_G2_T2_English Language_Midterm_Blinded.csv",
            FILE_G1_EL_LIT=RAW / "Grade 1 Reading Club" / "KE_G1_T3_Literacy_Endterm_Blinded.csv",
            FILE_G1_EL_ENG=RAW / "Grade 1 Reading Club" / "KE_G1_T3_English Language_Endterm_Blinded.csv",
            FILE_G2_EL_LIT=RAW / "Grade 2 Reading Club" / "KE_G2_T3_Literacy_Endterm_Blinded.csv",
            FILE_G2_EL_ENG=RAW / "Grade 2 Reading Club" / "KE_G2_T3_English Language_Endterm_Blinded.csv",
            FILE_G1_PTR=RAW / "Grade 1 Reading Club" / "KE_G1_PTR_Blinded.csv",
            FILE_G2_PTR=RAW / "Grade 2 Reading Club" / "KE_G2_PTR_Blinded.csv",
            # Experimental parameters
            grades=[1, 2],
            grade_groups={"g12": [1, 2]},
            cutoffs={1: 40, 2: 35},  # composite score cutoffs by grade
            strata_vars=["constituency"],
            cluster_var="academycode",  # treatment at academy level
            has_midline=False,
            score_type="composite",  # literacy + language
        )
    elif country == "kenya2":
        RAW = ROOT / "2_Data" / "1_Raw" / "Kenya" / "Reading Club (2019)" / "Reading Club (2019)"
        RAW_Y1 = ROOT / "2_Data" / "1_Raw" / "Kenya"
        return dict(
            country="kenya2",
            label="Kenya 2019",
            RAW=RAW,
            ANALYSIS_FILE=OUT / "analysis_kenya2.parquet",
            OUT_PREFIX="ke2_",
            FILE_G1_BL=RAW / "Grade 1" / "Term 1" / "KE_G1_T1_Baseline_Blinded.csv",
            FILE_G2_BL=RAW / "Grade 2" / "Term 1" / "KE_G2_T1_Baseline_Blinded.csv",
            FILE_G3_BL=RAW / "Grade 3" / "Term 1" / "KE_G3_T1_Baseline_Blinded.csv",
            FILE_G1_EL=RAW / "Grade 1" / "Term 3" / "KE_G1_T3_Endline_Blinded.csv",
            FILE_G2_EL=RAW / "Grade 2" / "Term 3" / "KE_G2_T3_Endline_Blinded.csv",
            FILE_G3_EL=RAW / "Grade 3" / "Term 3" / "KE_G3_T3_Endline_Blinded.csv",
            FILE_G1_ROSTER=RAW / "Roster of Pupils (All Grades)" / "KE_G1_T2 Roster of Pupils_Blinded.csv",
            FILE_G2_ROSTER=RAW / "Roster of Pupils (All Grades)" / "KE_G2_T2 Roster of Pupils_Blinded.csv",
            FILE_G3_ROSTER=RAW / "Roster of Pupils (All Grades)" / "KE_G3_T2 Roster of Pupils_Blinded.csv",
            # Year 1 files (for reading-group carryover)
            Y1_G1_BL_LIT=RAW_Y1 / "Grade 1 Reading Club" / "KE_G1_T2_Literacy_Midterm_Blinded.csv",
            Y1_G1_BL_ENG=RAW_Y1 / "Grade 1 Reading Club" / "KE_G1_T2_English Language_Midterm_Blinded.csv",
            Y1_G2_BL_LIT=RAW_Y1 / "Grade 2 Reading Club" / "KE_G2_T2_Literacy_Midterm_Blinded.csv",
            Y1_G2_BL_ENG=RAW_Y1 / "Grade 2 Reading Club" / "KE_G2_T2_English Language_Midterm_Blinded.csv",
            Y1_CUTOFFS={1: 40, 2: 35},
            cutoffs={1: 35, 2: 45, 3: 41},
            grades=[1, 2, 3],
            grade_groups={"g123": [1, 2, 3]},
            strata_vars=["constituency"],
            cluster_var="academycode",
            has_midline=False,
            score_type="single",
        )

    elif country == "nigeria":
        RAW = ROOT / "2_Data" / "1_Raw" / "P123 Numeracy Groups"
        return dict(
            country="nigeria",
            label="Nigeria (Lagos)",
            RAW=RAW,
            ANALYSIS_FILE=OUT / "analysis_nigeria.parquet",
            OUT_PREFIX="ng_",
            FILE_BL=RAW / "term 2" / "Assessment Scores by Pupil - MASTER v2 (P123 T1 ETE Maths).xlsx",
            FILE_EL_NUM=RAW / "term 3" / "Assessment Scores by Pupil - MASTER v2 (P123 T3 ETE Numeracy).xlsx",
            FILE_EL_MATH=RAW / "term 3" / "Assessment Scores by Pupil - MASTER v2 (P123 T3 ETE Maths).xlsx",
            FILE_PLACEMENT=RAW / "[Data Entry] Numeracy Groups Placement - 2020-2021.xlsx",
            FILE_ROSTER=RAW / "term 2" / "Roster of Pupils (P123 T2).xlsx",
            FILE_TCH=RAW / "term 2" / "Teacher Attendance Summary (P123 T2).xlsx",
            FILE_PUPIL_ATTN=RAW / "term 2" / "Student Attendance by Gender By Streams Summary (P123 T2).xlsx",
            FILE_LP=RAW / "term 2" / "Lesson Completion Detail (Aligned) Report (P123 T2).xlsx",
            grades=[1, 2, 3],
            grade_groups={"g123": [1, 2, 3]},
            cutoffs={1: 13, 2: 13, 3: 13},
            strata_vars=["constituency"],
            cluster_var="academycode",
            has_midline=False,
            score_type="single",
            # Sorting reliability: R²(Group→EL_num) in control, corrected for
            # discretization (3-cat ordinal → continuous). Estimated in
            # nigeria_reliability.py. Pooled P2+P3: 0.37; by grade: P2≈0.30, P3≈0.30.
            sorting_reliability=0.37,
        )

    else:
        raise ValueError(f"Unknown country: {country}")
