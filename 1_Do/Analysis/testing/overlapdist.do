

/*==========================================================================

Title: overlapdist.do 
Author: Mridul Joshi
Date: Sat Dec  9 17:09:39 2023

Description: Overlapping distributions by academy

===========================================================================*/


use "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", clear 




tw (hist comp_score_bl if grade==1 & academycode == 4409, color(red%20) discrete freq) (hist comp_score_bl if grade==2 & academycode == 4409, color(blue%20) discrete freq)

tw (kdensity std_comp_score_bl if grade==1 & academycode == 4409, color(red%20) ) (kdensity std_comp_score_bl if grade==2 & academycode == 4409, color(blue%20))


** counterfactual distribution with tracking 

tw (kdensity std_comp_score_bl if purple==1 & academycode == 4409, color(purple) ) (kdensity std_comp_score_bl if purple==0 & academycode == 4409, color(blue)) ///
	(kdensity std_comp_score_bl if grade==1 & academycode == 4409, color(green) ) (kdensity std_comp_score_bl if grade==2 & academycode == 4409, color(red))

 