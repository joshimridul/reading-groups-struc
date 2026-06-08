

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


tempfile classdata
save `classdata'




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

gen Iscore_bl_lang = score_bl_lang
qui summ score_bl_lang if treat == 0 & grade == 1
replace Iscore_bl_lang = `r(mean)' if mi(Iscore_bl_lang) & grade == 1

qui summ score_bl_lang if treat == 0 & grade == 2
replace Iscore_bl_lang = `r(mean)' if mi(Iscore_bl_lang) & grade == 2


gen purple = 0 
replace purple =1 if comp_score_bl > 40 & !mi(comp_score_bl) & grade == 1
replace purple =1 if comp_score_bl > 35 & !mi(comp_score_bl) & grade == 2

lab var purple "Reading group"


/*
* create standardised scores 
summ comp_score_bl if treat == 0 & grade == 1
gen std_comp_score_bl = (comp_score_bl - `r(mean)')/`r(sd)' if grade == 1

summ comp_score_bl if treat == 0 & grade == 2
replace std_comp_score_bl = (comp_score_bl - `r(mean)')/`r(sd)' if grade == 2

lab var std_comp_score_bl "Baseline score (std)"

summ comp_score_el if treat == 0 & grade == 1
gen std_comp_score_el = (comp_score_el - `r(mean)')/`r(sd)' if grade== 1

summ comp_score_el if treat == 0 & grade == 2
replace std_comp_score_el = (comp_score_el - `r(mean)')/`r(sd)' if grade== 2

lab var std_comp_score_el "Endline score (std)"


summ comp_score_bl if treat == 0 
gen std_comp_score_bl_orig = (comp_score_bl - `r(mean)')/`r(sd)' 
*/


*merge m:1 academycode grade using `ptr', gen(_mptr)

merge m:1 academycode grade using `classdata', gen(_mclassdata)

drop if _mclassdata == 2


gen g1 = grade == 1
gen g2 = grade == 2

lab var g1 "Grade 1"
lab var g2 "Grade 2"


gen gg0 = inlist(grade,1,2)
gen gg1 = grade == 1 
gen gg2 = grade == 2

lab var gg0 "Full sample"
lab var gg1 "Lower grade"
lab var gg2 "Upper grade"


* save full wide dataset
save "${datadir}/Kenya/5_K_AG_full_wide.dta", replace



