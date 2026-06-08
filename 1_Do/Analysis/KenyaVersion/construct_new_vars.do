
/*==========================================================================

Title: construct_new_vars.do 
Author: Mridul Joshi
Date: Tue Dec 12 14:29:35 2023

Description: Construct new variables that will be used in the Kenya-specific analysis

===========================================================================*/



use "${datadir}/Kenya/6_K_AG_full_wide_prepared", clear 

*keep if finsamp

gen rural = locationtype == 0
lab var rural "Rural area"

gen yr_operation = (assess_date_el - academy_cohort)/365
lab var yr_operation "Academy years of operation"

gen new_to_bridge = enrolled_date >= td(01january2018)
lab var new_to_bridge "Recently enrolled"


gen old_student = enrolled_date <= td(11jun2017)
lab var old_student "Enrolled at least one year ago"


gen share_female = female / class_ptr 
lab var share_female "Proportion of female students"



** universal standardization

qui summ comp_score_bl if treat==0, detail

gen std2_compscore_bl = (comp_score_bl - `r(mean)')/`r(sd)'
lab var std2_compscore_bl "Standardized pretest score"

qui summ comp_score_el if treat==0, detail

gen std2_compscore_el = (comp_score_el - `r(mean)')/`r(sd)'


egen bl_q = xtile(std2_compscore_bl), nq(4) //by(academycode grade stream)


forval i = 1/2 {

	egen abs_bl_q_g`i' = xtile(std2_compscore_bl) if grade== `i', nq(4) 
}

gen abs_bl_q_4 = abs_bl_q_g1
replace abs_bl_q_4 = abs_bl_q_g2 if mi(abs_bl_q_4)


egen bl_q3 = xtile(std2_compscore_bl), nq(3) //by(academycode grade stream)



gen high_q_peer = bl_q  == 4 

bys academycode purple: egen total_qt = total(high_q_peer)
bys academycode purple: egen count_qt = count(high_q_peer)

gen q4_peer_t= (total_qt - (high_q_peer==4))/(count_qt - 1)

bys academycode grade: egen total_qc = total(high_q_peer)
bys academycode grade: egen count_qc = count(high_q_peer)

gen q4_peer_c= (total_qc - (high_q_peer==4))/(count_qc - 1)

gen exp_q4_peer = (P_t*q4_peer_t) + (P_c*q4_peer_c)

gen q4_peer =q4_peer_t
replace q4_peer = q4_peer_c if treat == 0



bys academycode grade: egen mean_bl_c2 = mean(std2_compscore_bl)
bys academycode purple: egen mean_bl_t2 = mean(std2_compscore_bl)

gen dev_mean_t_bl2 = abs(std2_compscore_bl -  mean_bl_t)
gen dev_mean_c_bl2 = abs(std2_compscore_bl -  mean_bl_c)

gen exp_devmean_bl2 = (P_t*dev_mean_t_bl2) + (P_c*dev_mean_c_bl2)
lab var exp_devmean_bl2 "E[Dispersion]"

gen mean_bl2 = mean_bl_c2
replace mean_bl2 = mean_bl_t2 if treat == 1 

*gen dev_mean_bl = abs(std2_comp_score_bl - mean_bl)

gen dev_mean_bl2 = dev_mean_t_bl2 
replace dev_mean_bl2 = dev_mean_c_bl2 if treat== 0

lab var dev_mean_bl2 "Dispersion"


bys academycode grade: egen mean_el_c2 = mean(std2_compscore_el)
bys academycode purple: egen mean_el_t2 = mean(std2_compscore_el)

gen dev_mean_t_el2 = abs(std2_compscore_el -  mean_el_t)
gen dev_mean_c_el2 = abs(std2_compscore_el -  mean_el_c)

gen exp_devmean_el2 = (P_t*dev_mean_t_el2) + (P_c*dev_mean_c_el2)
lab var exp_devmean_el2 "E[Dispersion]"

gen mean_el2 = mean_el_c2
replace mean_el2 = mean_el_t2 if treat == 1 

*gen dev_mean_bl = abs(std2_comp_score_bl - mean_bl)

gen dev_mean_el2 = dev_mean_t_el2 
replace dev_mean_el2 = dev_mean_c_el2 if treat== 0

lab var dev_mean_el2 "Dispersion"




save "${datadir}/Kenya/6_K_AG_full_wide_prepared_2.dta", replace



