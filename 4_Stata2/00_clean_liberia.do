/*
00_clean_liberia.do — Build Liberia analysis dataset from raw CSVs
==================================================================
Replicates 3_Python/00_clean.py.
Follows variable-naming conventions from 1_Do/Cleaning/3_L_AG_clean.do.

import delimited lowercases all CSV headers, so raw variables are:
  academycode, studyid, baselinescore, gradename, treatmentassignment_g12,
  treatmentassignment_g34, midlinescore, endlinescore, stream, ...

Suffix pattern: all non-id vars get _bl / _ml / _el suffix before merge.

Produces: $out/analysis_liberia.dta
*/

di _n "{hline 70}"
di "00_clean_liberia.do — Building Liberia analysis dataset"
di "{hline 70}"

tempfile bl ml el loc attn lp tch

* ═══════════════════════════════════════════════════════════════════════════
* 1. LOAD RAW DATA
* ═══════════════════════════════════════════════════════════════════════════

* ── Baseline ─────────────────────────────────────────────────────────────
import delimited "$raw/Liberia/LR_G1234_S1_BaselineData_Blinded.csv", clear
format studyid %12.0f

* Suffix all non-id vars with _bl
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_bl
}
save `bl'
di "Baseline loaded: " _N " rows"

* ── Midline ──────────────────────────────────────────────────────────────
import delimited "$raw/Liberia/LR_G1234_S1_ETE_Blinded.csv", clear
format studyid %12.0f

ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_ml
}

duplicates drop academycode studyid, force
save `ml'
di "Midline loaded: " _N " rows"

* ── Endline ──────────────────────────────────────────────────────────────
import delimited "$raw/Liberia/LR_G1234_S2_EndlineData_Blinded.csv", clear
format studyid %12.0f

ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_el
}

duplicates drop academycode studyid, force
save `el'
di "Endline loaded: " _N " rows"

* ── Locations ────────────────────────────────────────────────────────────
import excel "$raw/Liberia/updated academy locations.xlsx", firstrow clear

gen county_up = County
gen constituency = Constituency
gen cohort_up = Cohort

keep academycode county_up constituency cohort_up
save `loc'


* ═══════════════════════════════════════════════════════════════════════════
* 2. MERGE
* ═══════════════════════════════════════════════════════════════════════════

use `bl', clear
merge 1:1 academycode studyid using `ml', gen(_mml)
merge 1:1 academycode studyid using `el', gen(_mel)

gen in_bl = (_mml != 2)
gen in_ml = (_mml != 1)
gen in_el = (_mel != 2)

* Resolve grade from gradename_* (last character is digit)
gen grade = real(substr(gradename_el, -1, 1))
replace grade = real(substr(gradename_ml, -1, 1)) if mi(grade)
replace grade = real(substr(gradename_bl, -1, 1)) if mi(grade)

* Resolve stream
gen stream = stream_el
replace stream = stream_ml if mi(stream)

* Treatment: replace "na" with "", destring, prefer baseline assignment
foreach v of varlist treatmentassignment_g12_* treatmentassignment_g34_* {
	replace `v' = "" if `v' == "na"
	destring `v', replace
}

gen tr12 = treatmentassignment_g12_bl
replace tr12 = treatmentassignment_g12_ml if mi(tr12)
replace tr12 = treatmentassignment_g12_el if mi(tr12)

gen tr34 = treatmentassignment_g34_bl
replace tr34 = treatmentassignment_g34_ml if mi(tr34)
replace tr34 = treatmentassignment_g34_el if mi(tr34)

gen treat = tr12 if inlist(grade, 1, 2)
replace treat = tr34 if inlist(grade, 3, 4)

* Merge academy locations
merge m:1 academycode using `loc', keep(1 3) nogen

gen county = county_up

* Cohort year
gen cohort_date = date(cohort_up, "DMY")
format cohort_date %td
gen acad_year = cond(cohort_date < date("$lib_cohort_threshold", "YMD"), 1, 2)

di "After merge: " _N " rows"
drop _mml _mel


* ═══════════════════════════════════════════════════════════════════════════
* 3. SCORES
* ═══════════════════════════════════════════════════════════════════════════

gen score_bl = baselinescore_bl

gen score_ml = midlinescore_ml
replace score_ml = . if score_ml == -1

gen score_el = endlinescore_el
replace score_el = . if score_el == -1


* ═══════════════════════════════════════════════════════════════════════════
* 4. SAMPLE RESTRICTIONS
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Sample restrictions ---"

keep if inlist(grade, 1, 2, 3, 4)
di "Valid grade: " _N

keep if !mi(treat)
di "Non-missing treatment: " _N

* Drop Stream B
cap confirm string variable stream
if _rc == 0 {
	replace stream = strtrim(stream)
	drop if stream == "B"
}
else {
	drop if stream == 2
}
di "Drop Stream B: " _N

* Grade group
gen g12 = inlist(grade, 1, 2)
egen ggroup = group(g12 academycode)

* Drop single-grade academies
bys academycode g12: egen n_grades = nvals(grade)
drop if n_grades == 1
drop n_grades
di "Drop single-grade academies: " _N

* Need BL scores in academy-grade group
bys ggroup: egen has_any_bl = max(!mi(score_bl))
keep if has_any_bl == 1
drop has_any_bl
di "BL scores exist in group: " _N

* Drop duplicates
duplicates drop academycode studyid, force
di "After dedup: " _N

* Sample flags
gen has_bl = !mi(score_bl)
gen has_el = !mi(score_el)
bys ggroup: egen n_bl_in_grp = total(has_bl)
gen finsamp = (has_bl & n_bl_in_grp > 1)
di "Final sample (finsamp): " ///
	string(sum(finsamp), "%9.0fc")


* ═══════════════════════════════════════════════════════════════════════════
* 5. CONSTRUCT VARIABLES
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Constructing variables ---"

* Strata: acad_year × g12 (two experiments)
egen strata = group(acad_year g12)

* Propensity score: P(T=1) within each acad_year × g12 stratum
preserve
	collapse (mean) treat, by(academycode acad_year g12)
	bys acad_year g12: egen P_t = mean(treat)
	gen P_c = 1 - P_t
	keep g12 academycode P_t P_c
	duplicates drop
	tempfile pt
	save `pt'
restore
merge m:1 g12 academycode using `pt', nogen

* Upper group assignment
gen upper_group = .
replace upper_group = (score_bl > $lib_cutoff_g12) if inlist(grade, 1, 2) & !mi(score_bl)
replace upper_group = (score_bl > $lib_cutoff_g34) if inlist(grade, 3, 4) & !mi(score_bl)
replace upper_group = 0 if mi(score_bl) & !mi(treat)

* Reading group label: 1=lower G12, 2=upper G12, 3=lower G34, 4=upper G34
gen std_grp = .
replace std_grp = 1 if inlist(grade, 1, 2) & upper_group == 0
replace std_grp = 2 if inlist(grade, 1, 2) & upper_group == 1
replace std_grp = 3 if inlist(grade, 3, 4) & upper_group == 0
replace std_grp = 4 if inlist(grade, 3, 4) & upper_group == 1

* Standardize scores by grade (control-group mean/sd)
foreach var in score_bl score_el {
	gen std_`var' = .
	forval g = 1/4 {
		qui summ `var' if treat == 0 & grade == `g'
		if r(sd) > 0 & !mi(r(sd)) {
			replace std_`var' = (`var' - r(mean)) / r(sd) if grade == `g'
		}
	}
}

* Empirical Bayes predicted ability: θ̂ = μ_g + ρ²_g × (s_i − μ_g)
gen eb_ability = .
forval g = 1/4 {
	qui corr score_bl score_el if treat == 0 & grade == `g'
	local r2_g = max(r(rho)^2, 0.01)
	qui summ score_bl if treat == 0 & grade == `g'
	local mu_g = r(mean)
	replace eb_ability = `mu_g' + `r2_g' * (score_bl - `mu_g') ///
		if grade == `g' & !mi(score_bl)
	replace eb_ability = `mu_g' if grade == `g' & mi(score_bl)
	di "  Grade `g': rho2 = " %6.4f `r2_g'
}
gen std_eb = .
forval g = 1/4 {
	qui summ eb_ability if treat == 0 & grade == `g'
	if r(sd) > 0 & !mi(r(sd)) {
		replace std_eb = (eb_ability - r(mean)) / r(sd) if grade == `g'
	}
}


* ═══════════════════════════════════════════════════════════════════════════
* 6. PEER VARIABLES
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Peer variables ---"

* Leave-self-out peer mean (treatment: academy × std_grp; control: academy × grade)
foreach pvar in std_score_bl std_eb {
	bys academycode std_grp: egen _tot_t = total(`pvar')
	bys academycode std_grp: egen _cnt_t = count(`pvar')
	gen peer_`pvar'_treat = (_tot_t - `pvar') / (_cnt_t - 1) if _cnt_t > 1
	drop _tot_t _cnt_t

	bys academycode grade: egen _tot_c = total(`pvar')
	bys academycode grade: egen _cnt_c = count(`pvar')
	gen peer_`pvar'_ctrl = (_tot_c - `pvar') / (_cnt_c - 1) if _cnt_c > 1
	drop _tot_c _cnt_c
}

* Realized peer quality
gen peer_bl = cond(treat == 1, peer_std_score_bl_treat, peer_std_score_bl_ctrl)
gen peer_eb = cond(treat == 1, peer_std_eb_treat, peer_std_eb_ctrl)

* Expected peer quality (BH)
gen exp_peer_eb = P_t * peer_std_eb_treat + P_c * peer_std_eb_ctrl

* Class size
bys academycode std_grp: egen csize_treat = count(studyid)
bys academycode grade:   egen csize_ctrl  = count(studyid)
gen csize = cond(treat == 1, csize_treat, csize_ctrl)

* Within-class EB dispersion
bys academycode std_grp: egen _mn_eb_t = mean(std_eb)
bys academycode grade:   egen _mn_eb_c = mean(std_eb)
gen dev_eb_treat = abs(std_eb - _mn_eb_t)
gen dev_eb_ctrl  = abs(std_eb - _mn_eb_c)
gen dev_eb = cond(treat == 1, dev_eb_treat, dev_eb_ctrl)
drop _mn_eb_t _mn_eb_c

* Baseline deciles
gen bl_decile = .
forval g = 1/4 {
	xtile _dec = score_bl if grade == `g', nq(10)
	replace bl_decile = _dec if grade == `g'
	drop _dec
}

* Misfit: (θ̂_i − Ī_k)²
bys academycode std_grp: egen class_mean_eb_t = mean(std_eb) if has_bl
bys academycode grade:   egen class_mean_eb_c = mean(std_eb) if has_bl
gen class_mean_eb = cond(treat == 1, class_mean_eb_t, class_mean_eb_c)
gen misfit = (std_eb - class_mean_eb)^2
drop class_mean_eb_t class_mean_eb_c

* Distance from cutoff
gen dist_from_cutoff = .
replace dist_from_cutoff = abs(score_bl - $lib_cutoff_g12) if inlist(grade, 1, 2) & !mi(score_bl)
replace dist_from_cutoff = abs(score_bl - $lib_cutoff_g34) if inlist(grade, 3, 4) & !mi(score_bl)


* ═══════════════════════════════════════════════════════════════════════════
* 7. SAVE
* ═══════════════════════════════════════════════════════════════════════════

compress
save "$out/analysis_liberia.dta", replace
di _n "Saved: $out/analysis_liberia.dta"
di "  N = " _N ", finsamp = " string(sum(finsamp), "%9.0fc")
tab grade treat if finsamp, row
