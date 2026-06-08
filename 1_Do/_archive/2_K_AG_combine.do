

/*==========================================================================

Title: 2_K_AG_combine.do 
Author: Mridul Joshi
Date: Mon Jul 19 10:08:27 2021

Description: This do-file combines the Kenya datasets for Bridge 
			 ability-grouping analysis

===========================================================================*/



* ===================================================================== *
* -----------------     	  Full wide dataset       ----------------- *
* ===================================================================== *


*** calculate classsize from Bridge PTR data and compare

import delimited using "${rawdir}/Kenya/Grade 2 Reading Club/KE_G2_PTR_Blinded.csv", clear 

gen class_ptr = real(g2pupils)
gen female = real(g2female)
gen acadsize = academypupils
gen numteachers = academyteachers

gen grade = 2 


keep academycode class_ptr acadsize numteachers grade female


tempfile g2_pupils
save `g2_pupils'
 
import delimited using "${rawdir}/Kenya/Grade 1 Reading Club/KE_G1_PTR_Blinded.csv", clear


gen class_ptr = g2pupils
gen female = g2female
gen acadsize = academypupils
gen numteachers = academyteachers

gen grade = 1 


keep academycode class_ptr acadsize numteachers grade female


append using `g2_pupils'

lab var class_ptr "Pupil-teacher ratio (Bridge data)"

tempfile ptr
save `ptr'




use "${datadir}/Kenya/0_K_AG_parent.dta", clear 

* baseline language
merge 1:1 academycode studyid using "${datadir}/Kenya/1_K_AG_bl_lang.dta", gen(_mbll)


* baseline reading 
merge 1:1 academycode studyid using "${datadir}/Kenya/2_K_AG_bl_read.dta", gen(_mblr)


* endline language
merge 1:1 academycode studyid using "${datadir}/Kenya/3_K_AG_el_lang.dta", gen(_mell)


* endline reading 
merge 1:1 academycode studyid using "${datadir}/Kenya/4_K_AG_el_read.dta", gen(_melr)


drop _m*  


* tracking groups were based on these composite scores

gen comp_score_bl = score_bl_lang + score_bl_read
lab var comp_score_bl "Baseline composite score"

gen comp_score_el = score_el_lang + score_el_read
lab var comp_score_el "Endline composite score"

gen purple = 0 
replace purple =1 if comp_score_bl > 40 & !mi(comp_score_bl) & grade == 1
replace purple =1 if comp_score_bl > 35 & !mi(comp_score_bl) & grade == 2

lab var purple "Reading group"


* create standardised scores 
summ comp_score_bl if treat == 0
gen std_comp_score_bl = (comp_score_bl - `r(mean)')/`r(sd)'
lab var std_comp_score_bl "Baseline score (std)"

summ comp_score_el if treat == 0
gen std_comp_score_el = (comp_score_el - `r(mean)')/`r(sd)'
lab var std_comp_score_el "Endline score (std)"


*merge m:1 academycode grade using `ptr', gen(_mptr)

merge m:1 academycode grade using `ptr', gen(_mptr)

drop if _mptr == 2


* save full wide dataset
save "${datadir}/Kenya/5_K_AG_full_wide.dta", replace




* ===================================================================== *
* -----------------     	  Stacked dataset         ----------------- *
* ===================================================================== *


*** reading group info for stacked dataset 
keep academycode studyid comp_score_bl comp_score_el purple acadsize numteachers class_ptr female 

tempfile reading_grps
save `reading_grps'


* bl and el language scores 
use "${datadir}/Kenya/1_K_AG_bl_lang.dta", clear 
merge 1:1 academycode studyid using "${datadir}/Kenya/3_K_AG_el_lang.dta", gen(_mell)

* language or reading
gen assess_competency_el = 1

* rename other vars to append (remove _lang suffix)
rename *_lang *

drop _mell


tempfile lang
save `lang'
 

* bl and el reading scores 
use "${datadir}/Kenya/2_K_AG_bl_read.dta", clear 
merge 1:1 academycode studyid using "${datadir}/Kenya/4_K_AG_el_read.dta", gen(_melr)

* language or reading 
gen assess_competency_el = 2 

* rename other vars to append (remove _read suffix)
rename *_read *

drop _melr

append using `lang'

lab def competency 1 "Language" 2 "Reading"
lab val assess_competency_el competency

lab var assess_competency_el "Language or Reading"


tempfile score_appended
save `score_appended'
 

use "${datadir}/Kenya/0_K_AG_parent.dta", clear 

merge 1:1 academycode studyid using `reading_grps', gen(_mgrp)

merge 1:m academycode studyid using `score_appended', gen(_mstack)
 
drop _m*

* create standardised scores 
summ score_bl if treat == 0
gen std_score_bl = (score_bl- `r(mean)')/`r(sd)'
lab var std_score_bl "Baseline score (std)"

summ score_el if treat == 0
gen std_score_el = (score_el - `r(mean)')/`r(sd)'
lab var std_score_el "Endline score (std)"


order assess_competency_el, after(purple)
order std_score_bl, after(score_bl)
order std_score_el, after(score_el)

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
save "${datadir}/Kenya/6_K_AG_full_stacked.dta", replace



