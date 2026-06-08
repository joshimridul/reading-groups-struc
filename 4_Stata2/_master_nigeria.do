/*
_master_nigeria.do — Nigeria-only Stata pipeline
================================================
Runs:
  1) 00_clean_nigeria.do
  2) 02_nigeria_main_analysis.do
*/

clear all
set more off
capture version 19

if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/_master_nigeria.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/_master_nigeria.do") {
        local root_dir = subinstr("`pwd'", "/4_Stata2", "", .)
        global root "`root_dir'"
    }
    else {
        di as err "Could not infer repo root. Set global root and rerun."
        exit 601
    }
}

global do  "$root/4_Stata2"
global out "$root/4_Stata2/output"
cap mkdir "$out"

di _n "{hline 70}"
di "Nigeria Stata pipeline"
di "{hline 70}"

do "$do/00_clean_nigeria.do"
do "$do/02_nigeria_main_analysis.do"

di _n "{hline 70}"
di "Nigeria Stata pipeline complete."
di "{hline 70}"
