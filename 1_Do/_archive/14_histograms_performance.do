
/*==========================================================================

Title: 14_histograms_performance.do 
Author: Mridul Joshi
Date: Thu Feb  3 12:47:37 2022

Description: Histograms of baseline and predicted scores 

===========================================================================*/



* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *

graph drop _all


use "${datadir}/Kenya/5_K_AG_full_wide.dta", clear 



twoway (histogram comp_score_bl if treat==0 & grade == 1, start(2) width(5) color(red%30)) ///        
       (histogram comp_score_bl if treat==0 & grade == 2, start(2) width(5) color(green%30)), ///   
       legend(order(1 "Grade 1" 2 "Grade 2" )) name(k1)



** predicted endline scores
gen grade_dum = grade == 1
gen score_bl_gr = comp_score_bl*grade_dum
reg comp_score_el comp_score_bl score_bl_gr grade_dum if treat == 0
predict endline_hat, xb

lab var endline_hat "Predicted endline score"


twoway (histogram endline_hat if treat==0 & grade == 1, start(2) width(5) color(red%30)) ///        
       (histogram endline_hat if treat==0 & grade == 2, start(2) width(5) color(green%30)), ///   
       legend(order(1 "Grade 1" 2 "Grade 2" )) name(k2)



graph combine k1 k2, ycommon       
graph export "${outdir}/kenya_hist.pdf", replace as(pdf)


graph drop _all



* ===================================================================== *
* -----------------     	       Liberia            ----------------- *
* ===================================================================== *


use "${datadir}/Liberia/5_L_AG_full_wide.dta", clear 



twoway (histogram score_bl if treat==0 & grade == 1, start(0) width(5) color(red%30)) ///        
       (histogram score_bl if treat==0 & grade == 2, start(0) width(5) color(green%30)), ///   
       legend(order(1 "Grade 1" 2 "Grade 2" )) name(l1)




** predicted endline scores
gen grade_dum1 = grade == 1 
gen grade_dum2 = grade == 2
gen grade_dum3 = grade == 3 
gen grade_dum4 = grade == 4

gen score_bl_gr1 = score_bl*grade_dum1
gen score_bl_gr2 = score_bl*grade_dum2
gen score_bl_gr3 = score_bl*grade_dum3
gen score_bl_gr4 = score_bl*grade_dum4

gen score_ml_gr1 = score_ml*grade_dum1
gen score_ml_gr2 = score_ml*grade_dum2
gen score_ml_gr3 = score_ml*grade_dum3
gen score_ml_gr4 = score_ml*grade_dum4

reg score_el score_bl score_ml score_bl_gr? score_ml_gr? grade_dum? if treat == 0
predict endline_hat, xb

lab var endline_hat "Predicted endline score"



twoway (histogram endline_hat if treat==0 & grade == 1, start(0) width(5) color(red%30)) ///        
       (histogram endline_hat if treat==0 & grade == 2, start(0) width(5) color(green%30)), ///   
       legend(order(1 "Grade 1" 2 "Grade 2" )) name(l2)





graph combine l1 l2, ycommon       
graph export "${outdir}/liberia_hist.pdf", replace as(pdf)


graph drop _all


**** grade 3 and 4 

use "${datadir}/Liberia/5_L_AG_full_wide.dta", clear 


twoway (histogram score_bl if treat==0 & grade == 3, start(0) width(5) color(red%30)) ///        
       (histogram score_bl if treat==0 & grade == 4, start(0) width(5) color(green%30)), ///   
       legend(order(1 "Grade 1" 2 "Grade 2" )) name(l3)



** predicted endline scores
gen grade_dum1 = grade == 1 
gen grade_dum2 = grade == 2
gen grade_dum3 = grade == 3 
gen grade_dum4 = grade == 4

gen score_bl_gr1 = score_bl*grade_dum1
gen score_bl_gr2 = score_bl*grade_dum2
gen score_bl_gr3 = score_bl*grade_dum3
gen score_bl_gr4 = score_bl*grade_dum4

gen score_ml_gr1 = score_ml*grade_dum1
gen score_ml_gr2 = score_ml*grade_dum2
gen score_ml_gr3 = score_ml*grade_dum3
gen score_ml_gr4 = score_ml*grade_dum4

reg score_el score_bl score_ml score_bl_gr? score_ml_gr? grade_dum? if treat == 0
predict endline_hat, xb

lab var endline_hat "Predicted endline score"



twoway (histogram endline_hat if treat==0 & grade == 3, start(0) width(5) color(red%30)) ///        
       (histogram endline_hat if treat==0 & grade == 4, start(0) width(5) color(green%30)), ///   
       legend(order(1 "Grade 3" 2 "Grade 4" )) name(l4)





graph combine l3 l4, ycommon       
graph export "${outdir}/liberia_hist_34.pdf", replace as(pdf)


graph drop _all





