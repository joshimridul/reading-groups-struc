/*
05_sufficientstats.do — Deprecated wrapper
==========================================

This file used to contain a separate sufficient-statistics implementation.
The maintained version now lives in `04_structural.do`.

It is kept as a compatibility wrapper so older notes or commands do not fail.
*/

di _n "{hline 70}"
di "05_sufficientstats.do — Deprecated wrapper"
di "{hline 70}"

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

global out "$root/4_Stata2/output"
cap mkdir "$out"

di as text "NOTE: 05_sufficientstats.do is deprecated."
di as text "Running updated implementation in 04_structural.do instead."
do "$root/4_Stata2/04_structural.do"
