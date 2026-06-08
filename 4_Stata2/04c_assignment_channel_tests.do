/*
04c_assignment_channel_tests.do — Kenya assignment-channel diagnostics
========================================================================
Tests whether the null Kenya ITT is consistent with a weak assignment
channel under scripted instruction.

Main tests:
  1. Mover vs stayer ITT heterogeneity
  2. Distance-from-cutoff dose among movers
  3. Control-group mismatch proxy
  4. Control-group classroom dispersion
  5. Grade × mover-direction ITTs

Requires: analysis_kenya.dta
Produces: assignment_channel_tests_kenya.{csv,dta,tex,md}
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
if "$ke_cutoff_g1" == "" global ke_cutoff_g1 = 40
if "$ke_cutoff_g2" == "" global ke_cutoff_g2 = 35

cap program drop get_stars
program define get_stars, rclass
	args pval
	local s ""
	if `pval' < 0.10 local s "*"
	if `pval' < 0.05 local s "**"
	if `pval' < 0.01 local s "***"
	return local stars "`s'"
end

di _n "{hline 70}"
di "04c_assignment_channel_tests.do — Kenya assignment-channel tests"
di "{hline 70}"

use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el
keep if !mi(std_score_el, std_eb, score_bl, grade, treat, strata)

* Flexible own-score controls used in reduced-form heterogeneity checks.
gen eb2 = std_eb^2
gen eb3 = std_eb^3
local flex "c.std_eb##i.grade c.eb2##i.grade c.eb3##i.grade"
local lin  "c.std_eb##i.grade"

* Design-implied movers and stayers.
gen mover_up   = grade == 1 & score_bl >  $ke_cutoff_g1
gen mover_down = grade == 2 & score_bl <= $ke_cutoff_g2
gen mover      = mover_up | mover_down
gen stayer     = 1 - mover

gen move_dist = .
replace move_dist = score_bl - $ke_cutoff_g1 if mover_up
replace move_dist = $ke_cutoff_g2 - score_bl if mover_down
assert move_dist >= 0 if mover

gen g1_stayer = grade == 1 & stayer
gen g1_mover  = mover_up
gen g2_mover  = mover_down
gen g2_stayer = grade == 2 & stayer

cap confirm variable bl_quintile
if _rc != 0 {
	gen bl_quintile = .
	forval g = 1/2 {
		qui xtile _q = score_bl if grade == `g', nq(5)
		replace bl_quintile = _q if grade == `g'
		drop _q
	}
}

* School-grade controls used in some diagnostics.
bys academycode grade: egen school_grade_mean_bl = mean(std_score_bl)
bys academycode grade: egen class_sd_ctrl = sd(std_eb)
bys academycode grade: egen class_mean_ctrl = mean(std_eb)

* Proxy instructional targets with the control-group grade means of EB ability.
qui summ std_eb if treat == 0 & grade == 1
local tgt_g1 = r(mean)
qui summ std_eb if treat == 0 & grade == 2
local tgt_g2 = r(mean)
gen grade_target = `tgt_g1' if grade == 1
replace grade_target = `tgt_g2' if grade == 2
gen mismatch_grade = (std_eb - grade_target)^2
gen track_target = `tgt_g1' if std_grp == 1
replace track_target = `tgt_g2' if std_grp == 2
gen assign_gain = (std_eb - grade_target)^2 - (std_eb - track_target)^2
gen assign_gain2 = assign_gain^2

tempfile res
postfile pf str4 section str60 specification double coef se pval N using `res'

* ═══════════════════════════════════════════════════════════════════════════
* T1. Movers vs stayers
* ═══════════════════════════════════════════════════════════════════════════
di _n "=== T1. Movers vs stayers ==="

qui reg std_score_el treat `flex' i.strata if mover, vce(cluster academycode)
local b_t1_m = _b[treat]
local se_t1_m = _se[treat]
local pv_t1_m = 2 * ttail(e(df_r), abs(`b_t1_m'/`se_t1_m'))
local n_t1_m = e(N)
di "  Movers:   " %7.3f `b_t1_m' " (" %5.3f `se_t1_m' ")"
post pf ("T1") ("Movers ITT") (`b_t1_m') (`se_t1_m') (`pv_t1_m') (`n_t1_m')

qui reg std_score_el treat `flex' i.strata if stayer, vce(cluster academycode)
local b_t1_s = _b[treat]
local se_t1_s = _se[treat]
local pv_t1_s = 2 * ttail(e(df_r), abs(`b_t1_s'/`se_t1_s'))
local n_t1_s = e(N)
di "  Stayers:  " %7.3f `b_t1_s' " (" %5.3f `se_t1_s' ")"
post pf ("T1") ("Stayers ITT") (`b_t1_s') (`se_t1_s') (`pv_t1_s') (`n_t1_s')

qui reg std_score_el ib0.treat##ib0.mover `flex' i.strata, vce(cluster academycode)
local b_t1_int = _b[1.treat#1.mover]
local se_t1_int = _se[1.treat#1.mover]
local pv_t1_int = 2 * ttail(e(df_r), abs(`b_t1_int'/`se_t1_int'))
local n_t1_int = e(N)
di "  Treat x mover: " %7.3f `b_t1_int' " (" %5.3f `se_t1_int' ")"
post pf ("T1") ("Treat x mover interaction") (`b_t1_int') (`se_t1_int') (`pv_t1_int') (`n_t1_int')

* ═══════════════════════════════════════════════════════════════════════════
* T2. Distance from cutoff among movers
* ═══════════════════════════════════════════════════════════════════════════
di _n "=== T2. Distance from cutoff among movers ==="

qui reg std_score_el i.treat##c.move_dist c.std_eb c.eb2 c.eb3 i.strata if mover_up, vce(cluster academycode)
local b_t2_up = _b[1.treat]
local se_t2_up = _se[1.treat]
local pv_t2_up = 2 * ttail(e(df_r), abs(`b_t2_up'/`se_t2_up'))
local n_t2_up = e(N)
local b_t2_upd = _b[1.treat#c.move_dist]
local se_t2_upd = _se[1.treat#c.move_dist]
local pv_t2_upd = 2 * ttail(e(df_r), abs(`b_t2_upd'/`se_t2_upd'))
di "  G1 movers up, ITT:      " %7.3f `b_t2_up' " (" %5.3f `se_t2_up' ")"
di "  G1 movers up, T x dist: " %7.3f `b_t2_upd' " (" %5.3f `se_t2_upd' ")"
post pf ("T2") ("G1 movers up: ITT") (`b_t2_up') (`se_t2_up') (`pv_t2_up') (`n_t2_up')
post pf ("T2") ("G1 movers up: Treat x distance") (`b_t2_upd') (`se_t2_upd') (`pv_t2_upd') (`n_t2_up')

qui reg std_score_el i.treat##c.move_dist c.std_eb c.eb2 c.eb3 i.strata if mover_down, vce(cluster academycode)
local b_t2_dn = _b[1.treat]
local se_t2_dn = _se[1.treat]
local pv_t2_dn = 2 * ttail(e(df_r), abs(`b_t2_dn'/`se_t2_dn'))
local n_t2_dn = e(N)
local b_t2_dnd = _b[1.treat#c.move_dist]
local se_t2_dnd = _se[1.treat#c.move_dist]
local pv_t2_dnd = 2 * ttail(e(df_r), abs(`b_t2_dnd'/`se_t2_dnd'))
di "  G2 movers down, ITT:      " %7.3f `b_t2_dn' " (" %5.3f `se_t2_dn' ")"
di "  G2 movers down, T x dist: " %7.3f `b_t2_dnd' " (" %5.3f `se_t2_dnd' ")"
post pf ("T2") ("G2 movers down: ITT") (`b_t2_dn') (`se_t2_dn') (`pv_t2_dn') (`n_t2_dn')
post pf ("T2") ("G2 movers down: Treat x distance") (`b_t2_dnd') (`se_t2_dnd') (`pv_t2_dnd') (`n_t2_dn')

* ═══════════════════════════════════════════════════════════════════════════
* T3. Control-group mismatch proxy
* ═══════════════════════════════════════════════════════════════════════════
di _n "=== T3. Control-group mismatch proxy ==="

qui reg std_score_el mismatch_grade `lin' i.strata if treat == 0, vce(cluster academycode)
local b_t3 = _b[mismatch_grade]
local se_t3 = _se[mismatch_grade]
local pv_t3 = 2 * ttail(e(df_r), abs(`b_t3'/`se_t3'))
local n_t3 = e(N)
di "  Mismatch proxy:                  " %7.3f `b_t3' " (" %5.3f `se_t3' ")"
post pf ("T3") ("Control: mismatch proxy") (`b_t3') (`se_t3') (`pv_t3') (`n_t3')

qui reg std_score_el mismatch_grade school_grade_mean_bl `lin' i.strata if treat == 0, vce(cluster academycode)
local b_t3s = _b[mismatch_grade]
local se_t3s = _se[mismatch_grade]
local pv_t3s = 2 * ttail(e(df_r), abs(`b_t3s'/`se_t3s'))
local n_t3s = e(N)
di "  Mismatch + school-grade mean BL: " %7.3f `b_t3s' " (" %5.3f `se_t3s' ")"
post pf ("T3") ("Control: mismatch + school-grade mean BL") (`b_t3s') (`se_t3s') (`pv_t3s') (`n_t3s')

* ═══════════════════════════════════════════════════════════════════════════
* T4. Control-group classroom dispersion
* ═══════════════════════════════════════════════════════════════════════════
di _n "=== T4. Control-group classroom dispersion ==="

qui reg std_score_el class_sd_ctrl class_mean_ctrl school_grade_mean_bl `lin' i.strata if treat == 0, vce(cluster academycode)
local b_t4 = _b[class_sd_ctrl]
local se_t4 = _se[class_sd_ctrl]
local pv_t4 = 2 * ttail(e(df_r), abs(`b_t4'/`se_t4'))
local n_t4 = e(N)
di "  Class SD in control classrooms: " %7.3f `b_t4' " (" %5.3f `se_t4' ")"
post pf ("T4") ("Control: class SD") (`b_t4') (`se_t4') (`pv_t4') (`n_t4')

* ═══════════════════════════════════════════════════════════════════════════
* T5. Grade × mover-direction ITTs
* ═══════════════════════════════════════════════════════════════════════════
di _n "=== T5. Grade × mover-direction ITTs ==="

qui reg std_score_el treat c.std_eb c.eb2 c.eb3 i.strata if g1_stayer, vce(cluster academycode)
local b_t6_g1s = _b[treat]
local se_t6_g1s = _se[treat]
local pv_t6_g1s = 2 * ttail(e(df_r), abs(`b_t6_g1s'/`se_t6_g1s'))
local n_t6_g1s = e(N)
di "  G1 stayers:    " %7.3f `b_t6_g1s' " (" %5.3f `se_t6_g1s' ")"
post pf ("T6") ("Grade 1 stayers") (`b_t6_g1s') (`se_t6_g1s') (`pv_t6_g1s') (`n_t6_g1s')

qui reg std_score_el treat c.std_eb c.eb2 c.eb3 i.strata if g1_mover, vce(cluster academycode)
local b_t6_g1m = _b[treat]
local se_t6_g1m = _se[treat]
local pv_t6_g1m = 2 * ttail(e(df_r), abs(`b_t6_g1m'/`se_t6_g1m'))
local n_t6_g1m = e(N)
di "  G1 movers up:  " %7.3f `b_t6_g1m' " (" %5.3f `se_t6_g1m' ")"
post pf ("T6") ("Grade 1 movers up") (`b_t6_g1m') (`se_t6_g1m') (`pv_t6_g1m') (`n_t6_g1m')

qui reg std_score_el treat c.std_eb c.eb2 c.eb3 i.strata if g2_mover, vce(cluster academycode)
local b_t6_g2m = _b[treat]
local se_t6_g2m = _se[treat]
local pv_t6_g2m = 2 * ttail(e(df_r), abs(`b_t6_g2m'/`se_t6_g2m'))
local n_t6_g2m = e(N)
di "  G2 movers down:" %7.3f `b_t6_g2m' " (" %5.3f `se_t6_g2m' ")"
post pf ("T6") ("Grade 2 movers down") (`b_t6_g2m') (`se_t6_g2m') (`pv_t6_g2m') (`n_t6_g2m')

qui reg std_score_el treat c.std_eb c.eb2 c.eb3 i.strata if g2_stayer, vce(cluster academycode)
local b_t6_g2s = _b[treat]
local se_t6_g2s = _se[treat]
local pv_t6_g2s = 2 * ttail(e(df_r), abs(`b_t6_g2s'/`se_t6_g2s'))
local n_t6_g2s = e(N)
di "  G2 stayers:    " %7.3f `b_t6_g2s' " (" %5.3f `se_t6_g2s' ")"
post pf ("T6") ("Grade 2 stayers") (`b_t6_g2s') (`se_t6_g2s') (`pv_t6_g2s') (`n_t6_g2s')

* ═══════════════════════════════════════════════════════════════════════════
* T7. Direct treatment × baseline-quintile heterogeneity
* ═══════════════════════════════════════════════════════════════════════════
di _n "=== T7. Direct baseline-quintile ITTs ==="

qui reg std_score_el i.bl_quintile##i.treat i.strata, vce(cluster academycode)
forval q = 1/5 {
	if `q' == 1 {
		local b_t7_q`q' = _b[1.treat]
		local se_t7_q`q' = _se[1.treat]
	}
	else {
		qui lincom 1.treat + `q'.bl_quintile#1.treat
		local b_t7_q`q' = r(estimate)
		local se_t7_q`q' = r(se)
	}
	local pv_t7_q`q' = 2 * normal(-abs(`b_t7_q`q'' / `se_t7_q`q''))
	local n_t7_q`q' = e(N)
	di "  Quintile `q': " %7.3f `b_t7_q`q'' " (" %5.3f `se_t7_q`q'' ")"
	post pf ("T7") ("Baseline quintile `q'") (`b_t7_q`q'') (`se_t7_q`q'') (`pv_t7_q`q'') (`n_t7_q`q'')
}

* ═══════════════════════════════════════════════════════════════════════════
* T8. Predicted assignment-gain interaction
* ═══════════════════════════════════════════════════════════════════════════
di _n "=== T8. Predicted assignment-gain interaction ==="

qui reg std_score_el i.treat##c.assign_gain c.assign_gain2 i.grade i.strata, vce(cluster academycode)
local b_t8_itt = _b[1.treat]
local se_t8_itt = _se[1.treat]
local pv_t8_itt = 2 * ttail(e(df_r), abs(`b_t8_itt'/`se_t8_itt'))
local n_t8 = e(N)
local b_t8_int = _b[1.treat#c.assign_gain]
local se_t8_int = _se[1.treat#c.assign_gain]
local pv_t8_int = 2 * ttail(e(df_r), abs(`b_t8_int'/`se_t8_int'))
di "  Treat main effect:      " %7.3f `b_t8_itt' " (" %5.3f `se_t8_itt' ")"
di "  Treat x assign_gain:    " %7.3f `b_t8_int' " (" %5.3f `se_t8_int' ")"
post pf ("T8") ("Predicted assignment gain: ITT") (`b_t8_itt') (`se_t8_itt') (`pv_t8_itt') (`n_t8')
post pf ("T8") ("Predicted assignment gain: Treat x gain") (`b_t8_int') (`se_t8_int') (`pv_t8_int') (`n_t8')

capture drop assign_gain_z assign_gain_z2
egen assign_gain_z = std(assign_gain)
gen assign_gain_z2 = assign_gain_z^2
qui reg std_score_el i.treat##c.assign_gain_z c.assign_gain_z2 i.grade i.strata, vce(cluster academycode)
local b_t8_intz = _b[1.treat#c.assign_gain_z]
local se_t8_intz = _se[1.treat#c.assign_gain_z]
local pv_t8_intz = 2 * ttail(e(df_r), abs(`b_t8_intz'/`se_t8_intz'))
local n_t8z = e(N)
di "  Treat x assignment gain, 1 SD: " %7.3f `b_t8_intz' " (" %5.3f `se_t8_intz' ")"
post pf ("T8") ("Predicted assignment gain: Treat x gain (1 SD)") (`b_t8_intz') (`se_t8_intz') (`pv_t8_intz') (`n_t8z')

postclose pf

use `res', clear
format coef se pval %9.3f
export delimited using "$out/assignment_channel_tests_kenya.csv", replace
save "$out/assignment_channel_tests_kenya.dta", replace
di _n "  -> assignment_channel_tests_kenya.csv"
di "  -> assignment_channel_tests_kenya.dta"

* LaTeX table
tempname fh
file open `fh' using "$out/tab_assignment_channel_tests_kenya.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Kenya Assignment-Channel Diagnostics}" _n
file write `fh' "\label{tab:assignment_channel_tests_kenya}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\scriptsize" _n
file write `fh' "\begin{tabular}[t]{llccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Section & Specification & Coef. & SE & N \\" _n
file write `fh' "\midrule" _n
local b_t1_m_f : di %7.3f `b_t1_m'
local se_t1_m_f : di %7.3f `se_t1_m'
local n_t1_m_f : di %7.0f `n_t1_m'
get_stars `pv_t1_m'
local st_t1_m "`r(stars)'"
file write `fh' "T1 & Movers ITT & `b_t1_m_f'`st_t1_m' & (`se_t1_m_f') & `n_t1_m_f' \\" _n

local b_t1_s_f : di %7.3f `b_t1_s'
local se_t1_s_f : di %7.3f `se_t1_s'
local n_t1_s_f : di %7.0f `n_t1_s'
get_stars `pv_t1_s'
local st_t1_s "`r(stars)'"
file write `fh' "T1 & Stayers ITT & `b_t1_s_f'`st_t1_s' & (`se_t1_s_f') & `n_t1_s_f' \\" _n

local b_t1_int_f : di %7.3f `b_t1_int'
local se_t1_int_f : di %7.3f `se_t1_int'
local n_t1_int_f : di %7.0f `n_t1_int'
get_stars `pv_t1_int'
local st_t1_int "`r(stars)'"
file write `fh' "T1 & Treat x mover interaction & `b_t1_int_f'`st_t1_int' & (`se_t1_int_f') & `n_t1_int_f' \\" _n

file write `fh' "\addlinespace" _n

local b_t2_up_f : di %7.3f `b_t2_up'
local se_t2_up_f : di %7.3f `se_t2_up'
get_stars `pv_t2_up'
local st_t2_up "`r(stars)'"
file write `fh' "T2 & G1 movers up: ITT & `b_t2_up_f'`st_t2_up' & (`se_t2_up_f') & `n_t2_up' \\" _n

local b_t2_upd_f : di %7.3f `b_t2_upd'
local se_t2_upd_f : di %7.3f `se_t2_upd'
get_stars `pv_t2_upd'
local st_t2_upd "`r(stars)'"
file write `fh' "T2 & G1 movers up: Treat x distance & `b_t2_upd_f'`st_t2_upd' & (`se_t2_upd_f') & `n_t2_up' \\" _n

local b_t2_dn_f : di %7.3f `b_t2_dn'
local se_t2_dn_f : di %7.3f `se_t2_dn'
get_stars `pv_t2_dn'
local st_t2_dn "`r(stars)'"
file write `fh' "T2 & G2 movers down: ITT & `b_t2_dn_f'`st_t2_dn' & (`se_t2_dn_f') & `n_t2_dn' \\" _n

local b_t2_dnd_f : di %7.3f `b_t2_dnd'
local se_t2_dnd_f : di %7.3f `se_t2_dnd'
get_stars `pv_t2_dnd'
local st_t2_dnd "`r(stars)'"
file write `fh' "T2 & G2 movers down: Treat x distance & `b_t2_dnd_f'`st_t2_dnd' & (`se_t2_dnd_f') & `n_t2_dn' \\" _n

file write `fh' "\addlinespace" _n

local b_t3_f : di %7.3f `b_t3'
local se_t3_f : di %7.3f `se_t3'
get_stars `pv_t3'
local st_t3 "`r(stars)'"
file write `fh' "T3 & Control: mismatch proxy & `b_t3_f'`st_t3' & (`se_t3_f') & `n_t3' \\" _n

local b_t3s_f : di %7.3f `b_t3s'
local se_t3s_f : di %7.3f `se_t3s'
get_stars `pv_t3s'
local st_t3s "`r(stars)'"
file write `fh' "T3 & Control: mismatch + school-grade mean BL & `b_t3s_f'`st_t3s' & (`se_t3s_f') & `n_t3s' \\" _n

file write `fh' "\addlinespace" _n

local b_t4_f : di %7.3f `b_t4'
local se_t4_f : di %7.3f `se_t4'
get_stars `pv_t4'
local st_t4 "`r(stars)'"
file write `fh' "T4 & Control: class SD & `b_t4_f'`st_t4' & (`se_t4_f') & `n_t4' \\" _n

local b_t6_g1s_f : di %7.3f `b_t6_g1s'
local se_t6_g1s_f : di %7.3f `se_t6_g1s'
get_stars `pv_t6_g1s'
local st_t6_g1s "`r(stars)'"
file write `fh' "T5 & Grade 1 stayers & `b_t6_g1s_f'`st_t6_g1s' & (`se_t6_g1s_f') & `n_t6_g1s' \\" _n

local b_t6_g1m_f : di %7.3f `b_t6_g1m'
local se_t6_g1m_f : di %7.3f `se_t6_g1m'
get_stars `pv_t6_g1m'
local st_t6_g1m "`r(stars)'"
file write `fh' "T5 & Grade 1 movers up & `b_t6_g1m_f'`st_t6_g1m' & (`se_t6_g1m_f') & `n_t6_g1m' \\" _n

local b_t6_g2m_f : di %7.3f `b_t6_g2m'
local se_t6_g2m_f : di %7.3f `se_t6_g2m'
get_stars `pv_t6_g2m'
local st_t6_g2m "`r(stars)'"
file write `fh' "T5 & Grade 2 movers down & `b_t6_g2m_f'`st_t6_g2m' & (`se_t6_g2m_f') & `n_t6_g2m' \\" _n

local b_t6_g2s_f : di %7.3f `b_t6_g2s'
local se_t6_g2s_f : di %7.3f `se_t6_g2s'
get_stars `pv_t6_g2s'
local st_t6_g2s "`r(stars)'"
file write `fh' "T5 & Grade 2 stayers & `b_t6_g2s_f'`st_t6_g2s' & (`se_t6_g2s_f') & `n_t6_g2s' \\" _n

file write `fh' "\addlinespace" _n

forvalues q = 1/5 {
	local bq_f : di %7.3f `b_t7_q`q''
	local sq_f : di %7.3f `se_t7_q`q''
	get_stars `pv_t7_q`q''
	local stq "`r(stars)'"
	file write `fh' "T7 & Baseline quintile `q' & `bq_f'`stq' & (`sq_f') & `n_t7_q`q'' \\" _n
}

file write `fh' "\addlinespace" _n

local b_t8_itt_f : di %7.3f `b_t8_itt'
local se_t8_itt_f : di %7.3f `se_t8_itt'
get_stars `pv_t8_itt'
local st_t8_itt "`r(stars)'"
file write `fh' "T8 & Predicted assignment gain: ITT & `b_t8_itt_f'`st_t8_itt' & (`se_t8_itt_f') & `n_t8' \\" _n

local b_t8_int_f : di %7.3f `b_t8_int'
local se_t8_int_f : di %7.3f `se_t8_int'
get_stars `pv_t8_int'
local st_t8_int "`r(stars)'"
file write `fh' "T8 & Predicted assignment gain: Treat x gain & `b_t8_int_f'`st_t8_int' & (`se_t8_int_f') & `n_t8' \\" _n

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} T1 compares treatment effects for movers and stayers, where movers are Grade 1 students above the upper cutoff and Grade 2 students at or below the lower cutoff. T2 interacts treatment with distance from the cutoff among movers separately by direction. T3 uses a control\mbox{-}group mismatch proxy based on squared distance between EB ability and the control-grade mean EB target. T4 tests whether within-class EB dispersion predicts achievement in control classrooms. T5 reports grade-specific ITTs for movers and stayers. Standard errors are clustered at the school level." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_assignment_channel_tests_kenya.tex"

* Compact paper-facing table: randomized assignment-payoff tests plus
* descriptive revealed-value checks in the control group.
tempname fh
file open `fh' using "$out/tab_assignment_payoff_kenya.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Kenya: Assignment Payoff Diagnostics}" _n
file write `fh' "\label{tab:assignment_payoff_kenya}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\scriptsize" _n
file write `fh' "\begin{tabular}[t]{p{0.58\linewidth}ccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Measure & Coef. & SE & N \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{4}{l}{\textit{A. Randomized reallocation contrasts}} \\" _n

local b_t1_m_f : di %7.3f `b_t1_m'
local se_t1_m_f : di %7.3f `se_t1_m'
local n_t1_m_f : di %7.0f `n_t1_m'
get_stars `pv_t1_m'
local st_t1_m "`r(stars)'"
file write `fh' "Movers ITT & `b_t1_m_f'`st_t1_m' & (`se_t1_m_f') & `n_t1_m_f' \\" _n

local b_t1_s_f : di %7.3f `b_t1_s'
local se_t1_s_f : di %7.3f `se_t1_s'
local n_t1_s_f : di %7.0f `n_t1_s'
get_stars `pv_t1_s'
local st_t1_s "`r(stars)'"
file write `fh' "Stayers ITT & `b_t1_s_f'`st_t1_s' & (`se_t1_s_f') & `n_t1_s_f' \\" _n

local b_t1_int_f : di %7.3f `b_t1_int'
local se_t1_int_f : di %7.3f `se_t1_int'
local n_t1_int_f : di %7.0f `n_t1_int'
get_stars `pv_t1_int'
local st_t1_int "`r(stars)'"
file write `fh' "Treatment \(\times\) mover & `b_t1_int_f'`st_t1_int' & (`se_t1_int_f') & `n_t1_int_f' \\" _n

file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{4}{l}{\textit{B. Assignment intensity among movers}} \\" _n

local b_t2_upd_f : di %7.3f `b_t2_upd'
local se_t2_upd_f : di %7.3f `se_t2_upd'
local n_t2_up_f : di %7.0f `n_t2_up'
get_stars `pv_t2_upd'
local st_t2_upd "`r(stars)'"
file write `fh' "G1 movers up: Treatment \(\times\) cutoff distance & `b_t2_upd_f'`st_t2_upd' & (`se_t2_upd_f') & `n_t2_up_f' \\" _n

local b_t2_dnd_f : di %7.3f `b_t2_dnd'
local se_t2_dnd_f : di %7.3f `se_t2_dnd'
local n_t2_dn_f : di %7.0f `n_t2_dn'
get_stars `pv_t2_dnd'
local st_t2_dnd "`r(stars)'"
file write `fh' "G2 movers down: Treatment \(\times\) cutoff distance & `b_t2_dnd_f'`st_t2_dnd' & (`se_t2_dnd_f') & `n_t2_dn_f' \\" _n

file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{4}{l}{\textit{C. Predicted assignment gain}} \\" _n

local b_t8_intz_f : di %7.3f `b_t8_intz'
local se_t8_intz_f : di %7.3f `se_t8_intz'
local n_t8z_f : di %7.0f `n_t8z'
get_stars `pv_t8_intz'
local st_t8_intz "`r(stars)'"
file write `fh' "Treatment \(\times\) predicted assignment gain (1 SD) & `b_t8_intz_f'`st_t8_intz' & (`se_t8_intz_f') & `n_t8z_f' \\" _n

file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{4}{l}{\textit{D. Descriptive control-group revealed-value checks}} \\" _n

local b_t3_f : di %7.3f `b_t3'
local se_t3_f : di %7.3f `se_t3'
local n_t3_f : di %7.0f `n_t3'
get_stars `pv_t3'
local st_t3 "`r(stars)'"
file write `fh' "Mismatch proxy & `b_t3_f'`st_t3' & (`se_t3_f') & `n_t3_f' \\" _n

local b_t3s_f : di %7.3f `b_t3s'
local se_t3s_f : di %7.3f `se_t3s'
local n_t3s_f : di %7.0f `n_t3s'
get_stars `pv_t3s'
local st_t3s "`r(stars)'"
file write `fh' "Mismatch proxy + school-grade mean BL & `b_t3s_f'`st_t3s' & (`se_t3s_f') & `n_t3s_f' \\" _n

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Outcome is the standardized endline test score. Movers are students whose treatment reading-group assignment differs from their enrolled grade: Grade 1 students above the upper-track cutoff and Grade 2 students at or below the lower-track cutoff. Cutoff distance is signed so larger values indicate more clearly assigned movers. Predicted assignment gain is the standardized reduction in squared EB-score mismatch from replacing the grade target with the treatment-track target; the regression also controls for its square. Panel D is estimated only in control classrooms and is descriptive rather than randomized. Standard errors are clustered at the school level." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_assignment_payoff_kenya.tex"

* Short markdown note
local b_t1_m_f   : di %7.3f `b_t1_m'
local se_t1_m_f  : di %7.3f `se_t1_m'
local b_t1_s_f   : di %7.3f `b_t1_s'
local se_t1_s_f  : di %7.3f `se_t1_s'
local b_t2_upd_f : di %7.3f `b_t2_upd'
local b_t2_dnd_f : di %7.3f `b_t2_dnd'
local b_t3_f     : di %7.3f `b_t3'
local b_t3s_f    : di %7.3f `b_t3s'
local b_t4_f     : di %7.3f `b_t4'
local b_t6_g1s_f : di %7.3f `b_t6_g1s'
local b_t6_g1m_f : di %7.3f `b_t6_g1m'
local b_t6_g2m_f : di %7.3f `b_t6_g2m'
local b_t6_g2s_f : di %7.3f `b_t6_g2s'
local b_t7_q1_f : di %7.3f `b_t7_q1'
local b_t7_q2_f : di %7.3f `b_t7_q2'
local b_t7_q3_f : di %7.3f `b_t7_q3'
local b_t7_q4_f : di %7.3f `b_t7_q4'
local b_t7_q5_f : di %7.3f `b_t7_q5'
local b_t8_int_f : di %7.3f `b_t8_int'
local b_t8_intz_f : di %7.3f `b_t8_intz'

tempname fh
file open `fh' using "$out/assignment_channel_tests_kenya.md", write replace
file write `fh' "# Kenya assignment-channel diagnostics" _n _n
file write `fh' "- Movers ITT = `b_t1_m_f' (SE `se_t1_m_f'); stayers ITT = `b_t1_s_f' (SE `se_t1_s_f')." _n
file write `fh' "- Among movers, the treatment-by-distance slope is `b_t2_upd_f' for Grade 1 movers up and `b_t2_dnd_f' for Grade 2 movers down." _n
file write `fh' "- In control classrooms, the mismatch proxy coefficient is `b_t3_f' without and `b_t3s_f' with school-grade mean baseline control." _n
file write `fh' "- The control-classroom dispersion coefficient is `b_t4_f'." _n
file write `fh' "- Grade-direction ITTs: G1 stayers = `b_t6_g1s_f', G1 movers up = `b_t6_g1m_f', G2 movers down = `b_t6_g2m_f', G2 stayers = `b_t6_g2s_f'." _n
file write `fh' "- Direct treatment-by-baseline-quintile ITTs: Q1 = `b_t7_q1_f', Q2 = `b_t7_q2_f', Q3 = `b_t7_q3_f', Q4 = `b_t7_q4_f', Q5 = `b_t7_q5_f'." _n
file write `fh' "- Predicted assignment-gain interaction: treat x assign_gain = `b_t8_int_f'." _n
file write `fh' "- Predicted assignment-gain interaction per 1 SD: `b_t8_intz_f'." _n
file close `fh'
di "  -> assignment_channel_tests_kenya.md"

di _n "{hline 70}"
di "Done."
di "{hline 70}"
