/*
_master_paper.do -- Full Stata runner for the three-country paper
=================================================================

This is the Stata entry point used by the repository-level run_all.sh. It
regenerates the reduced-form tables that feed main_3country_new.tex and copies
paper-facing tables into repo-local stata_output/ when individual scripts do so.

Run through:
  /Applications/StataNow/StataMP.app/Contents/MacOS/stata-mp -b do 4_Stata2/_master_paper.do
*/

clear all
set more off
set matsize 5000
version 19
set scheme s1mono

if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/_master_paper.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/_master_paper.do") {
        local root_dir = subinstr("`pwd'", "/4_Stata2", "", .)
        global root "`root_dir'"
    }
    else {
        di as err "Could not infer repo root. Run from repo root or 4_Stata2/, or set global root."
        exit 601
    }
}

global raw   "$root/2_Data/1_Raw"
global out   "$root/4_Stata2/output"
global paper "$root/stata_output"
global do    "$root/4_Stata2"

cap mkdir "$out"
cap mkdir "$paper"
cap mkdir "$root/build"
cap mkdir "$root/build/logs"

cap log close _all
log using "$root/build/logs/stata_master_paper.log", text replace

di _n "{hline 78}"
di "Three-country paper Stata pipeline"
di "Repo root: $root"
di "Output:    $out"
di "Paper:     $paper"
di "{hline 78}"

* Liberia
global lib_cutoff_g12 = 23
global lib_cutoff_g34 = 14
global lib_cohort_threshold "2016-11-22"

* Kenya Year 1
global ke_cutoff_g1 = 40
global ke_cutoff_g2 = 35

di _n "{hline 78}"
di "Stage 1. Clean Kenya and Liberia"
di "{hline 78}"
do "$do/00_clean_liberia.do"
do "$do/00_clean_kenya.do"

di _n "{hline 78}"
di "Stage 2. Kenya/Liberia descriptive and reduced-form tables"
di "{hline 78}"
do "$do/01_descriptives.do"
do "$do/02_main_analysis.do"
do "$do/03_diagnostics.do"
do "$do/04_structural.do"
do "$do/04c_assignment_channel_tests.do"
do "$do/06_robustness.do"
do "$do/07_lesson_completion.do"

di _n "{hline 78}"
di "Stage 3. Nigeria reduced-form tables"
di "{hline 78}"
do "$do/00_clean_nigeria.do"
do "$do/02_nigeria_main_analysis.do"
do "$do/02b_nigeria_two_group.do"

di _n "{hline 78}"
di "Stage 4. Pooled three-country tables"
di "{hline 78}"
do "$do/03_pooled_analysis.do"

di _n "{hline 78}"
di "Three-country paper Stata pipeline complete."
di "{hline 78}"

log close
exit, clear
