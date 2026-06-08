/*
_master.do — Master runner for Stata replication pipeline
=========================================================
Replicates the Python pipeline in 3_Python/ for validation.
Expects raw data in 2_Data/1_Raw/.
*/

clear all
set more off
set matsize 5000
version 19

set scheme s1mono

* ── Paths ──────────────────────────────────────────────────────────────────
if "$root" == "" {
	local pwd = c(pwd)
	if fileexists("`pwd'/4_Stata2/_master.do") {
		global root "`pwd'"
	}
	else if fileexists("`pwd'/_master.do") {
		local root_dir = subinstr("`pwd'", "/4_Stata2", "", .)
		global root "`root_dir'"
	}
	else {
		di as err "Could not infer repo root. Run from the repo root or 4_Stata2/, or set global root."
		exit 601
	}
}
global raw     "$root/2_Data/1_Raw"
global out     "$root/4_Stata2/output"
global do      "$root/4_Stata2"

cap mkdir "$out"

* ── Experimental parameters ────────────────────────────────────────────────
* Liberia
global lib_cutoff_g12 = 23
global lib_cutoff_g34 = 14
global lib_cohort_threshold "2016-11-22"

* Kenya Y1
global ke_cutoff_g1 = 40
global ke_cutoff_g2 = 35

* ── Pipeline ───────────────────────────────────────────────────────────────

di _n "{hline 70}"
di "Stage 1: Data Cleaning"
di "{hline 70}"
do "$do/00_clean_liberia.do"
do "$do/00_clean_kenya.do"

di _n "{hline 70}"
di "Stage 2: Descriptive Exhibits"
di "{hline 70}"
do "$do/01_descriptives.do"

di _n "{hline 70}"
di "Stage 3: Main Analysis"
di "{hline 70}"
do "$do/02_main_analysis.do"

di _n "{hline 70}"
di "Stage 4: Diagnostics and Mechanisms"
di "{hline 70}"
do "$do/03_diagnostics.do"

di _n "{hline 70}"
di "Stage 5: Structural Estimation"
di "{hline 70}"
do "$do/04_structural.do"

di _n "{hline 70}"
di "Stage 6: Robustness Tables"
di "{hline 70}"
do "$do/06_robustness.do"

di _n "{hline 70}"
di "Pipeline complete."
di "{hline 70}"
