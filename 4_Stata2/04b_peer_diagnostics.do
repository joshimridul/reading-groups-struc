/*
04b_peer_diagnostics.do — Diagnose cross-school confounding in peer estimate
=============================================================================
Three diagnostics to understand why the decile FE spec and exact CF spec
disagree on the peer coefficient:

  1. Add school-level controls to decile FE spec
  2. Split decile FE by treated/control subsamples
  3. Isolate own-score controls vs exact_mu contribution

Requires: analysis_kenya.dta from 00_clean_kenya.do
Produces: tab_peer_diagnostics_kenya.tex, peer_diagnostics_kenya.csv
*/

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
		di as err "Could not infer repo root."
		exit 601
	}
}
if "$out" == "" global out "$root/4_Stata2/output"

di _n "{hline 70}"
di "04b_peer_diagnostics.do — Cross-school confounding diagnostics"
di "{hline 70}"

use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el
keep if !mi(std_score_el) & !mi(std_eb) & !mi(peer_eb) & !mi(score_bl) & !mi(grade) & !mi(strata)

* ── Prepare variables ─────────────────────────────────────────────────────

* BH cells
cap confirm variable bl_decile
if _rc != 0 {
	gen bl_decile = .
	forval g = 1/2 {
		qui xtile _dec = score_bl if grade == `g', nq(10)
		replace bl_decile = _dec if grade == `g'
		drop _dec
	}
}
egen dtg_cell = group(bl_decile treat grade)

* Cubic own-score controls
gen eb2 = std_eb^2
gen eb3 = std_eb^3
local flex "c.std_eb##i.treat##i.grade c.eb2##i.treat##i.grade c.eb3##i.treat##i.grade"

* School-level controls
bys academycode: egen school_n = count(studyid)
cap confirm variable rural
if _rc != 0 {
	gen rural = (demographiclocation == "Rural") if !mi(demographiclocation)
}
cap confirm variable academy_cohort
* Use academy_cohort as proxy for school age if available


* ═════════════════════════════════════════════════════════════════════════
* DIAGNOSTIC 1: Add school-level controls to decile FE spec
* ═════════════════════════════════════════════════════════════════════════

di _n "=== Diagnostic 1: School-level controls ==="

* Baseline: decile FE only
qui reg std_score_el peer_eb i.dtg_cell i.strata, vce(cluster academycode)
local b_base = _b[peer_eb]
local se_base = _se[peer_eb]
local n_base = e(N)
di "  (1a) Baseline decile FE:     " %7.3f `b_base' " (" %5.3f `se_base' ")"

* Add school enrollment
qui reg std_score_el peer_eb school_n i.dtg_cell i.strata, vce(cluster academycode)
local b_enroll = _b[peer_eb]
local se_enroll = _se[peer_eb]
di "  (1b) + school enrollment:    " %7.3f `b_enroll' " (" %5.3f `se_enroll' ")"

* Add school enrollment + rural
cap confirm variable rural
if _rc == 0 {
	qui reg std_score_el peer_eb school_n rural i.dtg_cell i.strata, vce(cluster academycode)
	local b_enr_rur = _b[peer_eb]
	local se_enr_rur = _se[peer_eb]
	di "  (1c) + enrollment + rural:   " %7.3f `b_enr_rur' " (" %5.3f `se_enr_rur' ")"
}
else {
	local b_enr_rur = .
	local se_enr_rur = .
	di "  (1c) rural variable not available, skipped"
}

* Add class size directly
qui reg std_score_el peer_eb csize i.dtg_cell i.strata, vce(cluster academycode)
local b_csize = _b[peer_eb]
local se_csize = _se[peer_eb]
di "  (1d) + class size:           " %7.3f `b_csize' " (" %5.3f `se_csize' ")"

* Add school-grade mean baseline (direct school quality proxy)
bys academycode grade: egen school_grade_mean_bl = mean(std_score_bl)
qui reg std_score_el peer_eb school_grade_mean_bl i.dtg_cell i.strata, vce(cluster academycode)
local b_sgm = _b[peer_eb]
local se_sgm = _se[peer_eb]
di "  (1e) + school-grade mean BL: " %7.3f `b_sgm' " (" %5.3f `se_sgm' ")"

* Kitchen sink: school enrollment + class size + school-grade mean BL
qui reg std_score_el peer_eb school_n csize school_grade_mean_bl i.dtg_cell i.strata, vce(cluster academycode)
local b_all = _b[peer_eb]
local se_all = _se[peer_eb]
di "  (1f) + all school controls:  " %7.3f `b_all' " (" %5.3f `se_all' ")"


* ═════════════════════════════════════════════════════════════════════════
* DIAGNOSTIC 2: Subsample split by treatment status
* ═════════════════════════════════════════════════════════════════════════

di _n "=== Diagnostic 2: Treated vs control subsamples ==="

* For control students: peer_eb = grade-mates mean = school-grade composition
* For treated students: peer_eb = track-mates mean = sorting-determined
qui reg std_score_el peer_eb i.dtg_cell i.strata if treat == 1, vce(cluster academycode)
local b_treat = _b[peer_eb]
local se_treat = _se[peer_eb]
local n_treat = e(N)
di "  (2a) Treated only:   " %7.3f `b_treat' " (" %5.3f `se_treat' ")  N = " `n_treat'

qui reg std_score_el peer_eb i.dtg_cell i.strata if treat == 0, vce(cluster academycode)
local b_ctrl = _b[peer_eb]
local se_ctrl = _se[peer_eb]
local n_ctrl = e(N)
di "  (2b) Control only:   " %7.3f `b_ctrl' " (" %5.3f `se_ctrl' ")  N = " `n_ctrl'

* Interaction test: does zeta differ by treatment status?
gen peer_x_treat = peer_eb * treat
qui reg std_score_el peer_eb peer_x_treat i.dtg_cell i.strata, vce(cluster academycode)
local b_int = _b[peer_x_treat]
local se_int = _se[peer_x_treat]
local pv_int = 2 * ttail(e(df_r), abs(`b_int'/`se_int'))
di "  (2c) Interaction (peer x treat): " %7.3f `b_int' " (" %5.3f `se_int' ")  p = " %5.3f `pv_int'


* ═════════════════════════════════════════════════════════════════════════
* DIAGNOSTIC 3: Isolate own-score controls vs exact_mu
* ═════════════════════════════════════════════════════════════════════════

di _n "=== Diagnostic 3: Decomposing the spec change ==="

* (3a) Baseline: cell FE, no polynomial
qui reg std_score_el peer_eb i.dtg_cell i.strata, vce(cluster academycode)
local b_3a = _b[peer_eb]
local se_3a = _se[peer_eb]
di "  (3a) Cell FE only:                     " %7.3f `b_3a' " (" %5.3f `se_3a' ")"

* (3b) Cell FE + cubic polynomial (does within-cell functional form matter?)
qui reg std_score_el peer_eb i.dtg_cell `flex' i.strata, vce(cluster academycode)
local b_3b = _b[peer_eb]
local se_3b = _se[peer_eb]
di "  (3b) Cell FE + cubic own-score:        " %7.3f `b_3b' " (" %5.3f `se_3b' ")"

* (3c) Cubic polynomial only, no cell FE, no exact_mu
qui reg std_score_el peer_eb `flex' i.strata, vce(cluster academycode)
local b_3c = _b[peer_eb]
local se_3c = _se[peer_eb]
di "  (3c) Cubic own-score only (no FE):     " %7.3f `b_3c' " (" %5.3f `se_3c' ")"

* (3d) Cubic polynomial + exact_mu (the exact CF spec)
cap confirm variable exp_peer_eb
if _rc == 0 {
	gen exact_mu = exp_peer_eb
}
else {
	cap confirm variable exact_mu_peer_eb
	if _rc == 0 {
		gen exact_mu = exact_mu_peer_eb
	}
	else {
		cap confirm variable P_t
		if _rc == 0 {
			gen exact_mu = P_t * peer_std_eb_treat + (1 - P_t) * peer_std_eb_ctrl
		}
		else {
			di as err "Cannot construct exact_mu"
			exit 111
		}
	}
}

qui reg std_score_el peer_eb exact_mu `flex' i.strata, vce(cluster academycode)
local b_3d = _b[peer_eb]
local se_3d = _se[peer_eb]
local b_mu_3d = _b[exact_mu]
local se_mu_3d = _se[exact_mu]
di "  (3d) Cubic + exact_mu:                 " %7.3f `b_3d' " (" %5.3f `se_3d' ")  mu: " %7.3f `b_mu_3d' " (" %5.3f `se_mu_3d' ")"

* (3e) Cell FE + exact_mu (does mu matter even with cell FEs?)
qui reg std_score_el peer_eb exact_mu i.dtg_cell i.strata, vce(cluster academycode)
local b_3e = _b[peer_eb]
local se_3e = _se[peer_eb]
local b_mu_3e = _b[exact_mu]
local se_mu_3e = _se[exact_mu]
di "  (3e) Cell FE + exact_mu:               " %7.3f `b_3e' " (" %5.3f `se_3e' ")  mu: " %7.3f `b_mu_3e' " (" %5.3f `se_mu_3e' ")"

* (3f) Cell FE + cubic + exact_mu (kitchen sink)
qui reg std_score_el peer_eb exact_mu i.dtg_cell `flex' i.strata, vce(cluster academycode)
local b_3f = _b[peer_eb]
local se_3f = _se[peer_eb]
local b_mu_3f = _b[exact_mu]
local se_mu_3f = _se[exact_mu]
di "  (3f) Cell FE + cubic + exact_mu:       " %7.3f `b_3f' " (" %5.3f `se_3f' ")  mu: " %7.3f `b_mu_3f' " (" %5.3f `se_mu_3f' ")"


* ═════════════════════════════════════════════════════════════════════════
* SUMMARY
* ═════════════════════════════════════════════════════════════════════════

di _n "=== Interpretation guide ==="
di ""
di "Diagnostic 1 answers: Is the decile FE estimate sensitive to school-level controls?"
di "  If (1e) or (1f) move toward zero, school-level OVB is confirmed."
di ""
di "Diagnostic 2 answers: Does the peer estimate differ for treated vs control students?"
di "  For control students, peer_eb = school-grade mean (maximally confounded)."
di "  For treated students, peer_eb = track mean (sorting-determined)."
di "  If (2b) is more negative than (2a), the control subsample drives the bias."
di ""
di "Diagnostic 3 answers: What drives the difference — own-score controls or exact_mu?"
di "  Compare (3a) vs (3b): does adding cubic within cells change the estimate?"
di "    If no  -> within-cell functional form is not the issue."
di "  Compare (3a) vs (3e): does adding exact_mu to cell FEs change the estimate?"
di "    If yes -> school-composition confounding is the issue."
di "  Compare (3c) vs (3d): does adding exact_mu to cubic (no cell FEs) change the estimate?"
di "    If yes -> same conclusion, and the cell FEs were not solving the problem."
di ""


* ═════════════════════════════════════════════════════════════════════════
* EXPORT
* ═════════════════════════════════════════════════════════════════════════

preserve
	clear
	set obs 15
	gen str50 specification = ""
	gen double coef = .
	gen double se = .
	gen str8 diagnostic = ""

	local r = 1
	foreach spec in base enroll csize sgm all {
		replace diagnostic = "D1" in `r'
		if "`spec'" == "base"   replace specification = "Decile FE baseline" in `r'
		if "`spec'" == "enroll" replace specification = "+ school enrollment" in `r'
		if "`spec'" == "csize"  replace specification = "+ class size" in `r'
		if "`spec'" == "sgm"    replace specification = "+ school-grade mean BL" in `r'
		if "`spec'" == "all"    replace specification = "+ all school controls" in `r'
		replace coef = `b_`spec'' in `r'
		replace se = `se_`spec'' in `r'
		local r = `r' + 1
	}

	replace diagnostic = "D2" in `r'
	replace specification = "Treated subsample" in `r'
	replace coef = `b_treat' in `r'
	replace se = `se_treat' in `r'
	local r = `r' + 1

	replace diagnostic = "D2" in `r'
	replace specification = "Control subsample" in `r'
	replace coef = `b_ctrl' in `r'
	replace se = `se_ctrl' in `r'
	local r = `r' + 1

	foreach s in 3a 3b 3c 3d 3e 3f {
		replace diagnostic = "D3" in `r'
		if "`s'" == "3a" replace specification = "Cell FE only" in `r'
		if "`s'" == "3b" replace specification = "Cell FE + cubic" in `r'
		if "`s'" == "3c" replace specification = "Cubic only (no FE)" in `r'
		if "`s'" == "3d" replace specification = "Cubic + exact_mu" in `r'
		if "`s'" == "3e" replace specification = "Cell FE + exact_mu" in `r'
		if "`s'" == "3f" replace specification = "Cell FE + cubic + exact_mu" in `r'
		replace coef = `b_`s'' in `r'
		replace se = `se_`s'' in `r'
		local r = `r' + 1
	}

	drop if mi(specification)
	export delimited using "$out/peer_diagnostics_kenya.csv", replace
	save "$out/peer_diagnostics_kenya.dta", replace
restore

di _n "  -> peer_diagnostics_kenya.csv"
di "  -> peer_diagnostics_kenya.dta"
di _n "{hline 70}"
di "Done."
di "{hline 70}"
