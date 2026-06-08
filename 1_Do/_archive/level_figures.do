
/*==========================================================================

Title: level_figures.do 
Author: Mridul Joshi
Date: 

Description: 

Key input: 
Key output: 

Last edited by:  

===========================================================================*/


use "${datadir}/Kenya/6_K_AG_full_stacked.dta", clear 


egen bl_q = xtile(score_bl), nq(4) by(academycode grade stream)

lab var std_score_el "Standardised mean score"

binscatter std_score_el bl_q if  treat==0  , xq(bl_q) by(grade) xtitle("Baseline score quartiles") ytitle("Standardised endline score") absorb(academy_cohort)


graph export "${outdir}/K_quartiles12.pdf", replace 




use "${datadir}/Liberia/6_L_AG_full_stacked_prepared.dta", clear 


egen bl_q = xtile(score_bl), nq(4) by(academycode grade stream)

lab var std_score_el "Standardised mean score"

binscatter std_score_el bl_q if treat==0 & g12 == 1 , xq(bl_q) by(grade) xtitle("Baseline score quartiles") ytitle("Standardised endline score") absorb(academy_cohort)

graph export "${outdir}/L_quartiles12.pdf", replace 



binscatter std_score_el bl_q if treat==0 & g12 == 0 , xq(bl_q) by(grade) xtitle("Baseline score quartiles") ytitle("Standardised endline score") absorb(academy_cohort)

graph export "${outdir}/L_quartiles34.pdf", replace 






