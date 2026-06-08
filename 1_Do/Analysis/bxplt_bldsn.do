
/*==========================================================================

Title: dst_exhibits.do 
Author: Mridul Joshi
Date: Mon Nov 28 12:30:10 2022

Description: Distribution exhibits for reading groups paper

===========================================================================*/


set scheme s1mono
graph drop _all

* ===================================================================== *
* -----------------     	         Kenya            ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", clear 

keep if finsamp

lab var std_endline_hat "Predicted endline score (standardised)"
lab var std_comp_score_bl "Baseline score (standardised)"


lab def lev 0 "Lower grade" 1 "Upper grade"
lab val gg2 lev

graph box std_endline_hat if treat == 0, over(gg2) title("Kenya") name(kp)

*graph box std_comp_score_bl if treat == 0, over(gg2) title("Kenya") name(kb)


graph box std2_compscore_bl, over(grade) title("Kenya") 

tw (hist std_comp_score_bl if grade==1, color(red%20)) (hist std_comp_score_bl if grade==2, color(blue%20))

* ===================================================================== *
* -----------------     	        Liberia           ----------------- *
* ===================================================================== *

use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

keep if finsamp== 1 

lab var std_endline_hat "Predicted endline score (standardised)"
lab var std_score_bl "Baseline score (standardised)"


lab def lev 0 "Lower grade" 1 "Upper grade"
lab val gg2 lev

*graph box std_endline_hat if treat == 0, over(gg2) title("Liberia")  name(lp)

*graph box std_score_bl if treat == 0, over(gg2) title("Liberia")  name(lb)


graph box std_endline_hat if treat == 0, over(g4) title("Liberia")  name(lp)

graph box std_score_bl if treat == 0, over(g4) title("Liberia")  name(lb)


graph box std_score_bl if treat == 0, over(grade4) title("Liberia")  name(lb)



graph box score_bl if treat == 0, over(grade2) title("Liberia") 



* ===================================================================== *
* -----------------     	  Combine and export      ----------------- *
* ===================================================================== *


graph combine kp lp, ycommon title("") note("Notes: The analysis is restricted to the control group. Predicted scores are leave-academy i-out predictions")

*graph export "${outdir}/bxplt_preddsn.pdf", replace 



graph combine kb lb, ycommon title("") note("Notes: The analysis is restricted to the control group.")

*graph export "${outdir}/bxplt_bldsn.pdf", replace 











