/*
00_clean_nigeria.do — Build Nigeria analysis datasets for Stata tables
========================================================================
Inputs:
  - 2_Data/2_Cleaned/Nigeria/ng_assessments_student_long.dta
  - 2_Data/1_Raw/P123 Numeracy Groups/[Data Entry] Numeracy Groups Placement - 2020-2021.xlsx
  - 2_Data/2_Cleaned/Nigeria/ng_t3_ete_numeracy_irt_student.csv

Outputs:
  - 4_Stata2/output/analysis_nigeria_wide.dta
  - 4_Stata2/output/analysis_nigeria_attrition_long.dta
*/

di _n "{hline 70}"
di "00_clean_nigeria.do — Nigeria cleaning"
di "{hline 70}"

* ── Paths (standalone-safe) ─────────────────────────────────────────────
if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/00_clean_nigeria.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/00_clean_nigeria.do") {
        local root_dir = subinstr("`pwd'", "/4_Stata2", "", .)
        global root "`root_dir'"
    }
    else {
        di as err "Could not infer repo root. Set global root and rerun."
        exit 601
    }
}
global out "$root/4_Stata2/output"
cap mkdir "$out"

* ── Placement/group map (treatment truth + color groups) ────────────────
tempfile place
import excel "$root/2_Data/1_Raw/P123 Numeracy Groups/[Data Entry] Numeracy Groups Placement - 2020-2021.xlsx", firstrow clear
rename AcademyCode academycode
rename StudyID studyid
rename Treatment treat_pl
rename Group group_raw
replace group_raw = trim(regexr(group_raw, "[0-9]+", ""))
gen str8 group_color = proper(group_raw)
replace group_color = "Red" if strpos(group_color, "Red")
replace group_color = "Blue" if strpos(group_color, "Blue")
replace group_color = "Yellow" if strpos(group_color, "Yellow")
keep academycode studyid treat_pl group_color
duplicates drop studyid, force
save `place', replace

* ── Build long attrition-ready panel ─────────────────────────────────────
use "$root/2_Data/2_Cleaned/Nigeria/ng_assessments_student_long.dta", clear
rename treatment_harmonized treat
drop if missing(studyid)
drop if missing(academycode)
merge m:1 studyid using `place', keep(master match) nogen

replace treat = treat_pl if missing(treat) & !missing(treat_pl)
bys academycode: egen treat_mode = mode(treat)
replace treat = treat_mode if missing(treat)
drop treat_mode treat_pl

gen byte has_score = !missing(percscore)
gen byte is_bl = wave == "t1_ete_maths"
gen byte is_t2_mte = inlist(wave, "t2_mte_maths", "t2_mte_numeracy")
gen byte is_t2_ete = inlist(wave, "t2_ete_maths", "t2_ete_numeracy")
gen byte is_t3_mte = inlist(wave, "t3_mte_maths", "t3_mte_numeracy")
gen byte is_t3_ete = inlist(wave, "t3_ete_maths", "t3_ete_numeracy")

tempfile attr_long
save `attr_long', replace

* ── Build analysis-wide file (one row per student) ───────────────────────
preserve
keep studyid wave percscore
keep if inlist(wave, ///
    "t1_ete_maths", ///
    "t2_mte_maths", "t2_mte_numeracy", ///
    "t2_ete_maths", "t2_ete_numeracy", ///
    "t3_mte_maths", "t3_mte_numeracy", ///
    "t3_ete_maths", "t3_ete_numeracy")

bys studyid wave: keep if _n == 1
reshape wide percscore, i(studyid) j(wave) string
tempfile wide
save `wide', replace

* ── Student-level fixed fields (first non-missing, with minmode) ─────────
tempfile ids
restore
preserve
use `attr_long', clear
bys studyid: egen academycode_i = mode(academycode), minmode
bys studyid: egen treat_i = mode(treat), minmode
bys studyid: egen constituency_i = mode(constituency1), minmode
bys studyid: egen gradename_i = mode(gradename), minmode
bys studyid: egen group_i = mode(group_color), minmode
keep studyid academycode_i treat_i constituency_i gradename_i group_i
duplicates drop studyid, force
save `ids', replace
restore

use `wide', clear
merge 1:1 studyid using `ids', nogen
rename academycode_i academycode
rename treat_i treat
rename constituency_i constituency
rename gradename_i gradename
rename group_i group_color

di "  Debug treat distribution in wide file:"
tab treat, missing
qui count if treat == 0
di "  Controls in wide file: " r(N)

* Baseline control
rename percscoret1_ete_maths bl_score

* Standardize each outcome within control group
local raw_outcomes ///
    percscoret2_mte_maths percscoret2_mte_numeracy ///
    percscoret2_ete_maths percscoret2_ete_numeracy ///
    percscoret3_mte_maths percscoret3_mte_numeracy ///
    percscoret3_ete_maths percscoret3_ete_numeracy

foreach v of local raw_outcomes {
    capture confirm variable `v'
    if _rc == 0 {
        qui count if treat == 0 & !missing(`v')
        local nctrl = r(N)
        qui summ `v' if treat == 0 & !missing(`v')
        local mu = r(mean)
        local sig = r(sd)
        di "  Standardizing `v': nctrl=`nctrl' mean=`mu' sd=`sig'"
        if `nctrl' > 1 & `sig' > 0 {
            gen z_`v' = (`v' - `mu') / `sig' if !missing(`v')
            qui count if !missing(z_`v')
            di "    -> non-missing z_`v' = " r(N)
        }
        else {
            gen z_`v' = .
            di "    -> z_`v' set missing (insufficient control variation)"
        }
    }
}

* Wave-level math+numeracy indices — use available-case (rowmean)
egen idx_t2_mte = rowmean(z_percscoret2_mte_maths z_percscoret2_mte_numeracy)
egen idx_t2_ete = rowmean(z_percscoret2_ete_maths z_percscoret2_ete_numeracy)
egen idx_t3_mte = rowmean(z_percscoret3_mte_maths z_percscoret3_mte_numeracy)
egen idx_t3_ete = rowmean(z_percscoret3_ete_maths z_percscoret3_ete_numeracy)

* Group id for interactions — actual placement-based groups only
gen byte group_id = .
replace group_id = 1 if group_color == "Red"
replace group_id = 2 if group_color == "Blue"
replace group_id = 3 if group_color == "Yellow"

* For CONTROL students only, create counterfactual groups from baseline
* score terciles within grade so interactions are estimable in both arms.
gen byte grade_num = .
replace grade_num = real(regexs(1)) if regexm(gradename, "([0-9]+)")
gen byte group_cf = .
forvalues g = 1/3 {
    cap drop _tmp_cf
    egen _tmp_cf = xtile(bl_score) if treat == 0 & missing(group_id) & grade_num == `g' & !missing(bl_score), n(3)
    replace group_cf = _tmp_cf if missing(group_cf) & grade_num == `g'
    drop _tmp_cf
}
replace group_id = group_cf if treat == 0 & missing(group_id) & !missing(group_cf)
drop group_cf grade_num

label define group_id 1 "Red" 2 "Blue" 3 "Yellow"
label values group_id group_id

di "  group_id coverage by treatment arm:"
tab treat group_id, missing

* Merge IRT outcome (T3 ETE numeracy) — keep only master+match
tempfile irt
preserve
import delimited "$root/2_Data/2_Cleaned/Nigeria/ng_t3_ete_numeracy_irt_student.csv", clear
keep studyid theta_irt theta_irt_z raw_total raw_total_eq50 n_answered
duplicates drop studyid, force
save `irt', replace
restore

merge 1:1 studyid using `irt', keep(master match) nogen

save "$out/analysis_nigeria_wide.dta", replace
di "  -> analysis_nigeria_wide.dta"

* Save attrition panel
use `attr_long', clear
save "$out/analysis_nigeria_attrition_long.dta", replace
di "  -> analysis_nigeria_attrition_long.dta"

di _n "Nigeria cleaning complete."
