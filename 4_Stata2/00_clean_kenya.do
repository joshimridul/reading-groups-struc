/*
00_clean_kenya.do — Build Kenya Y1 analysis dataset from raw CSVs
=================================================================
Replicates 3_Python/00_clean_kenya.py.
Follows the variable-naming conventions from 1_Do/Cleaning/1_K_AG_clean.do.

import delimited lowercases all CSV headers, so raw variables are:
  academycode, studyid, score, maxscore, gradename, assessmentstatus,
  treatmentassignment, constituency1, county, demographiclocation,
  stream, academy_cohort, enrolled_date, ...

Produces: $out/analysis_kenya.dta
*/

* Standalone-safe defaults
if "$root" == "" global root "/Users/mriduljoshi/Github/AbilityGrouping"
if "$raw"  == "" global raw  "$root/2_Data/1_Raw"
if "$out"  == "" global out  "$root/4_Stata2/output"
if "$datadir" == "" global datadir "$root/2_Data/2_Cleaned"
if "$ke_cutoff_g1" == "" global ke_cutoff_g1 = 40
if "$ke_cutoff_g2" == "" global ke_cutoff_g2 = 35

di _n "{hline 70}"
di "00_clean_kenya.do — Building Kenya Y1 analysis dataset"
di "{hline 70}"


* ═══════════════════════════════════════════════════════════════════════════
* 1. LOAD AND MERGE BASELINE (T2 Midterm: Literacy + English)
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Loading baseline (T2 Midterm) ---"

tempfile bl_g1 bl_g2 el_g1 el_g2 bl el pt_design

*** Grade 1 Baseline ***

* English (language) — rename non-id vars to *_e
import delimited "$raw/Kenya/Grade 1 Reading Club/KE_G1_T2_English Language_Midterm_Blinded.csv", clear
format studyid %12.0f
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}
tempfile g1_bl_eng
save `g1_bl_eng'

* Literacy (reading) — merge with English
import delimited "$raw/Kenya/Grade 1 Reading Club/KE_G1_T2_Literacy_Midterm_Blinded.csv", clear
format studyid %12.0f
merge 1:1 academycode studyid using `g1_bl_eng', gen(_m_g1bl)
gen grade = 1
save `bl_g1'
di "  G1 BL: " _N " students"


*** Grade 2 Baseline ***

* English
import delimited "$raw/Kenya/Grade 2 Reading Club/KE_G2_T2_English Language_Midterm_Blinded.csv", clear
format studyid %12.0f
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}
tempfile g2_bl_eng
save `g2_bl_eng'

* Literacy
import delimited "$raw/Kenya/Grade 2 Reading Club/KE_G2_T2_Literacy_Midterm_Blinded.csv", clear
format studyid %12.0f
merge 1:1 academycode studyid using `g2_bl_eng', gen(_m_g2bl)
gen grade = 2
save `bl_g2'
di "  G2 BL: " _N " students"


*** Stack and construct composite ***
use `bl_g1', clear
append using `bl_g2'

* score = literacy, score_e = English (language)
* Convert to numeric (raw may contain "NA" or "-1" as strings)
destring score, replace force
destring score_e, replace force
replace score = . if score == -1
replace score_e = . if score_e == -1

gen score_bl = score + score_e

save `bl'
di "Baseline: " _N " students, " string(sum(!mi(score_bl)), "%9.0fc") " with composite"


* ═══════════════════════════════════════════════════════════════════════════
* 2. LOAD AND MERGE ENDLINE (T3 Endterm: Literacy + English)
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Loading endline (T3 Endterm) ---"

*** Grade 1 Endline ***

* English
import delimited "$raw/Kenya/Grade 1 Reading Club/KE_G1_T3_English Language_Endterm_Blinded.csv", clear
format studyid %12.0f
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}
tempfile g1_el_eng
save `g1_el_eng'

* Literacy
import delimited "$raw/Kenya/Grade 1 Reading Club/KE_G1_T3_Literacy_Endterm_Blinded.csv", clear
format studyid %12.0f
merge 1:1 academycode studyid using `g1_el_eng', gen(_m_g1el)
gen grade = 1
save `el_g1'
di "  G1 EL: " _N " students"


*** Grade 2 Endline ***

* English
import delimited "$raw/Kenya/Grade 2 Reading Club/KE_G2_T3_English Language_Endterm_Blinded.csv", clear
format studyid %12.0f
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}
tempfile g2_el_eng
save `g2_el_eng'

* Literacy
import delimited "$raw/Kenya/Grade 2 Reading Club/KE_G2_T3_Literacy_Endterm_Blinded.csv", clear
format studyid %12.0f
merge 1:1 academycode studyid using `g2_el_eng', gen(_m_g2el)
gen grade = 2
save `el_g2'
di "  G2 EL: " _N " students"


*** Stack and construct composite ***
use `el_g1', clear
append using `el_g2'

destring score, replace force
destring score_e, replace force
replace score = . if score == -1
replace score_e = . if score_e == -1

gen score_el = score + score_e

* Keep only what we need for merge
keep academycode studyid grade score_el
save `el'
di "Endline: " _N " students"


* ═══════════════════════════════════════════════════════════════════════════
* 3. MERGE BL + EL
* ═══════════════════════════════════════════════════════════════════════════

use `bl', clear
merge 1:1 academycode studyid using `el', gen(_mel)
gen in_bl = (_mel != 2)
gen in_el = (_mel != 1)

* Use EL grade if BL grade missing
replace grade = 1 if mi(grade) & !mi(score_el)
drop _mel
di "After BL-EL merge: " _N " rows"

* Treatment: from BL treatmentassignment variable
gen treat = (treatmentassignment == "Treatment") if !mi(treatmentassignment)

* Recover design-based school treatment probabilities from the vetted legacy
* Kenya cleaning pipeline, which preserves the full 292-school year-1 roster.
preserve
	use "$datadir/Kenya/0_K_AG_parent.dta", clear
	keep academycode constituency treat
	bys academycode: keep if _n == 1
	assert !mi(constituency, treat)
	gen constituency_design = strtrim(constituency)
	bys constituency_design: egen P_t_design = mean(treat)
	keep academycode constituency_design P_t_design
	duplicates drop
	save `pt_design'
restore


* ═══════════════════════════════════════════════════════════════════════════
* 4. SAMPLE RESTRICTIONS
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Sample restrictions ---"

keep if inlist(grade, 1, 2)
di "Valid grade: " _N

keep if !mi(treat)
di "Non-missing treatment: " _N

* Stream: numeric 1=A, 2=B after encode, or string
cap confirm string variable stream
if _rc == 0 {
	replace stream = strtrim(stream)
	drop if stream == "B"
}
else {
	drop if stream == 2
}
di "Drop Stream B: " _N

gen g12 = 1
egen ggroup = group(academycode)

* Drop single-grade academies
bys academycode: egen n_grades = nvals(grade)
drop if n_grades == 1
drop n_grades
di "Drop single-grade: " _N

* Need BL scores in academy
bys academycode: egen has_any_bl = max(!mi(score_bl))
keep if has_any_bl
drop has_any_bl
di "BL scores exist: " _N

* Drop cross-academy duplicate students
duplicates tag studyid, gen(_dup)
drop if _dup > 0
drop _dup
di "After dedup: " _N

gen has_bl = !mi(score_bl)
gen has_el = !mi(score_el)
bys ggroup: egen n_bl_in_grp = total(has_bl)
gen finsamp = (has_bl & n_bl_in_grp > 1)
di "Final sample (finsamp): " string(sum(finsamp), "%9.0fc")


* ═══════════════════════════════════════════════════════════════════════════
* 5. CONSTRUCT VARIABLES
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Constructing variables ---"

merge m:1 academycode using `pt_design', nogen keep(master match)

* Strata: by constituency, using the full-school randomization roster.
gen constituency = constituency_design
drop constituency_design
rename P_t_design P_t
assert !mi(constituency, P_t)
egen strata = group(constituency)

gen P_c = 1 - P_t

* Upper group
gen upper_group = .
replace upper_group = (score_bl > $ke_cutoff_g1) if grade == 1 & !mi(score_bl)
replace upper_group = (score_bl > $ke_cutoff_g2) if grade == 2 & !mi(score_bl)
replace upper_group = 0 if mi(score_bl) & !mi(treat)

gen std_grp = cond(upper_group == 1, 2, 1)

* Standardize scores (control-group mean/sd within grade)
foreach var in score_bl score_el {
	gen std_`var' = .
	forval g = 1/2 {
		qui summ `var' if treat == 0 & grade == `g'
		if r(sd) > 0 & !mi(r(sd)) {
			replace std_`var' = (`var' - r(mean)) / r(sd) if grade == `g'
		}
	}
}

* Empirical Bayes ability: θ̂ = μ_g + ρ²_g × (s_i − μ_g)
gen eb_ability = .
forval g = 1/2 {
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
forval g = 1/2 {
	qui summ eb_ability if treat == 0 & grade == `g'
	if r(sd) > 0 & !mi(r(sd)) {
		replace std_eb = (eb_ability - r(mean)) / r(sd) if grade == `g'
	}
}


* ═══════════════════════════════════════════════════════════════════════════
* 6. PEER VARIABLES
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Peer variables ---"

* Leave-self-out means
foreach pvar in std_score_bl std_eb {
	bys academycode std_grp: egen _tot_t = total(`pvar')
	bys academycode std_grp: egen _cnt_t = count(`pvar')
	gen peer_`pvar'_treat = (_tot_t - `pvar') / (_cnt_t - 1) if _cnt_t > 1
	drop _tot_t _cnt_t

	bys academycode grade: egen _tot_c = total(`pvar')
	bys academycode grade: egen _cnt_c = count(`pvar')
	gen peer_`pvar'_ctrl = (_tot_c - `pvar') / (_cnt_c - 1) if _cnt_c > 1
	drop _tot_c _cnt_c

	* Sensitivity: exclude students with missing baseline from both state objects.
	gen _`pvar'_obsbl = `pvar' if has_bl
	bys academycode std_grp: egen _tot_t_obsbl = total(_`pvar'_obsbl)
	bys academycode std_grp: egen _cnt_t_obsbl = count(_`pvar'_obsbl)
	gen peer_`pvar'_treat_obsbl = (_tot_t_obsbl - `pvar') / (_cnt_t_obsbl - 1) ///
		if has_bl & _cnt_t_obsbl > 1
	drop _tot_t_obsbl _cnt_t_obsbl

	bys academycode grade: egen _tot_c_obsbl = total(_`pvar'_obsbl)
	bys academycode grade: egen _cnt_c_obsbl = count(_`pvar'_obsbl)
	gen peer_`pvar'_ctrl_obsbl = (_tot_c_obsbl - `pvar') / (_cnt_c_obsbl - 1) ///
		if has_bl & _cnt_c_obsbl > 1
	drop _tot_c_obsbl _cnt_c_obsbl _`pvar'_obsbl
}

gen peer_bl = cond(treat == 1, peer_std_score_bl_treat, peer_std_score_bl_ctrl)
gen peer_eb = cond(treat == 1, peer_std_eb_treat, peer_std_eb_ctrl)
gen exp_peer_eb = P_t * peer_std_eb_treat + P_c * peer_std_eb_ctrl
gen peer_bl_obsbl = cond(treat == 1, peer_std_score_bl_treat_obsbl, peer_std_score_bl_ctrl_obsbl)
gen peer_eb_obsbl = cond(treat == 1, peer_std_eb_treat_obsbl, peer_std_eb_ctrl_obsbl)
gen exp_peer_eb_obsbl = P_t * peer_std_eb_treat_obsbl + P_c * peer_std_eb_ctrl_obsbl

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
forval g = 1/2 {
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
replace dist_from_cutoff = abs(score_bl - $ke_cutoff_g1) if grade == 1 & !mi(score_bl)
replace dist_from_cutoff = abs(score_bl - $ke_cutoff_g2) if grade == 2 & !mi(score_bl)


* ═══════════════════════════════════════════════════════════════════════════
* 7. SAVE
* ═══════════════════════════════════════════════════════════════════════════

compress
save "$out/analysis_kenya.dta", replace
di _n "Saved: $out/analysis_kenya.dta"
di "  N = " _N ", finsamp = " string(sum(finsamp), "%9.0fc")
tab grade treat if finsamp, row
