
/*==========================================================================

Title: 2_tarl_combine.do 
Author: Mridul Joshi
Date: Thu May 13 16:46:02 2021

Description: This do-file combines the Liberia datasets for Bridge 
			 ability-grouping analysis

===========================================================================*/


* ===================================================================== *
* -----------------     	  Full wide dataset       ----------------- *
* ===================================================================== *

* parent ds
use "${datadir}/Liberia/0_L_AG_parent.dta", clear 


* baseline data 
merge 1:1 academycode studyid using "${datadir}/Liberia/1_L_AG_bl.dta", gen(_mbl)


* midline data 
merge 1:1 academycode studyid using "${datadir}/Liberia/2_L_AG_ml.dta", gen(_mml)


* baseline data 
merge 1:1 academycode studyid using "${datadir}/Liberia/3_L_AG_el.dta", gen(_mel)


* other covariates
merge m:1 academycode grade using "${datadir}/Liberia/4_L_AG_covars.dta", gen(_mcov)


* drop _mcov == 2 and the merge variables 
keep if _mcov == 3 | _mcov == 1  // 29 non-matching cases without corresponding outcome data are dropped here 
drop _m*


* standardised test scores 
summ score_bl if inlist(grade, 1, 2) & treat == 0
gen std_score_bl = (score_bl - `r(mean)')/`r(sd)'

summ score_bl if inlist(grade, 3, 4) & treat == 0
replace std_score_bl = (score_bl - `r(mean)')/`r(sd)' if inlist(grade,3,4)

lab var std_score_bl "Baseline score (std)"


summ score_ml if inlist(grade, 1, 2) & treat == 0
gen std_score_ml = (score_ml - `r(mean)')/`r(sd)'

summ score_ml if inlist(grade, 1, 2) & treat == 0
replace std_score_ml = (score_ml - `r(mean)')/`r(sd)' if inlist(grade,3,4)

lab var std_score_ml "Standardised midline score"


summ score_el if inlist(grade, 1, 2) & treat == 0
gen std_score_el = (score_el - `r(mean)')/`r(sd)'

summ score_el if inlist(grade, 1, 2) & treat == 0
replace std_score_el = (score_el - `r(mean)')/`r(sd)' if inlist(grade,3,4)

lab var std_score_el "Standardised endline score"


gen studygroup12 = 0 if inlist(grade, 1,2) & score_bl <= 23 & !mi(score_bl)
replace studygroup12 = 1 if inlist(grade, 1,2) & score_bl > 23 & !mi(score_bl)

replace studygroup12 = 0 if inlist(grade, 1,2) & !mi(treat) & mi(score_bl) // students with missing bl scores

lab def studygroup12 0 "Yellow" 1 "Orange"
lab val studygroup12 studygroup12
lab var studygroup12 "Orange"

gen studygroup34 = 0 if inlist(grade, 3,4) & score_bl <= 14 & !mi(score_bl)
replace studygroup34 = 1 if inlist(grade, 3,4) & score_bl > 14 & !mi(score_bl)

replace studygroup34 = 0 if inlist(grade, 3,4) & !mi(treat) & mi(score_bl) // students with missing bl scores

lab def studygroup34 0 "Blue" 1 "Purple"
lab val studygroup34 studygroup34
lab var studygroup34 "Purple"

order std_score_* studygroup*, after(maxscore_el)

gen acad_year = 1 if academy_cohort < td(22nov2016)
replace acad_year = 2 if academy_cohort > td(22nov2016)
lab var acad_year "Academy cohort year"

gen g12 = inlist(grade, 1, 2)
lab var g12 "Grades 1 and 2"
egen ggroup = group(g12 academycode)

gen std_grp = 1
replace std_grp = 2 if studygroup12 == 1 & studygroup34 == .
replace std_grp = 3 if studygroup12 == . & studygroup34 == 0
replace std_grp = 4 if studygroup12 == . & studygroup34 == 1

lab def std_grp 1 "yellow" 2 "orange" 3 "blue" 4 "purple"
lab var std_grp "Reading group"

lab val std_grp std_grp

gen miss_baseline = mi(score_bl)
lab var miss_baseline "Baseline score not available"

gen sample = !mi(treat)
lab var sample "Final sample"

egen strata=group(acad_year g12)
lab var strata "Randomization strata"


gen g0 = inlist(grade,1,2,3,4)
gen g1 = grade == 1 | grade == 3 
gen g2 = grade == 2 | grade == 4

*gen g3 = grade == 3
*gen g4 = grade == 4 

lab var g0 "Full sample"
lab var g1 "Lower grade"
lab var g2 "Upper grade"


gen upper = inlist(grade, 2,4)
lab var upper "Upper grade"

* save full wide dataset
save "${datadir}/Liberia/5_L_AG_full_wide.dta", replace

/*

* ===================================================================== *
* -----------------     	  Stacked dataset         ----------------- *
* ===================================================================== *


*** reading group info for stacked dataset 
keep academycode studyid score_bl studygroup12 studygroup34 strata

tempfile reading_grps
save `reading_grps'


*** append ml and el scores 

use "${datadir}/Liberia/2_L_AG_ml.dta", clear 

gen test_name = 1
rename *_ml *_mlel

tempfile ml
save `ml'
 

use "${datadir}/Liberia/3_L_AG_el.dta", clear 

gen test_name = 2
rename *_el *_mlel

append using `ml'

lab def mlel 1 "ML" 2 "EL"
lab val test_name mlel

lab var test_name "Midline or Endline"



tempfile score_appended
save `score_appended'


use "${datadir}/Liberia/0_L_AG_parent.dta", clear 

merge 1:1 academycode studyid using `reading_grps', gen(_mgrp)

merge 1:m academycode studyid using `score_appended', gen(_mstack)
 
drop _m*

summ score_mlel if treat == 0
gen std_score_mlel = (score_mlel - `r(mean)')/`r(sd)'
lab var std_score_mlel "Endline score (std)"


summ score_bl if treat == 0
gen std_score_bl = (score_bl- `r(mean)')/`r(sd)'
lab var std_score_bl "Baseline score (std)"

gen sample = !mi(treat)

gen g1 = grade == 1 
gen g2 = grade == 2
gen g3 = grade == 3
gen g4 = grade == 4 
gen g0 = inlist(grade,1,2,3,4)

lab var g0 "Full sample"
lab var g1 "Grade 1"
lab var g2 "Grade 2"
lab var g3 "Grade 3"
lab var g4 "Grade 4"


* save full wide dataset
save "${datadir}/Liberia/6_L_AG_full_stacked.dta", replace


*/
