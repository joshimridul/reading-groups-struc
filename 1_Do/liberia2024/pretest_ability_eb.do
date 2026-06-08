
/*==========================================================================

Title: pretest_ability_eb.do 
Author: Mridul Joshi
Date: Mon Dec  9 12:42:23 2024

===========================================================================*/


use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

* 1) Compute control‐group baseline mean & variance by grade
forval g = 1/4 {
    quietly summarize score_bl if treat==0 & grade==`g'
    generate double baseline_mean_control_`g' = r(mean)
    generate double baseline_var_control_`g'  = r(Var)
}

* 2) Attach those group‐level stats to every student
generate double group_bl_mean = .
generate double group_bl_var  = .
forval g = 1/4 {
    replace group_bl_mean = baseline_mean_control_`g' if grade==`g'
    replace group_bl_var  = baseline_var_control_`g'  if grade==`g'
}

* 3) Plug in rho = baseline–midline correlation
scalar rho = 0.20

* 4) Compute grade‐specific measurement‐error variance
generate double sigma_e2 = group_bl_var * (1 - rho)

* 5) EB weight on each student’s own baseline
generate double w_bl = group_bl_var / (group_bl_var + sigma_e2)

* 6) Shrunk “predicted ability”
generate double predicted_ability = w_bl*score_bl + (1-w_bl)*group_bl_mean

* 7) (Optional) Standardize within control arm by grade
generate double std_pred_eb = .
forval g = 1/4 {
    quietly summarize predicted_ability if treat==0 & grade==`g'
    replace std_pred_eb = (predicted_ability - r(mean)) / r(sd) if grade==`g'
}

* 8) Quick check
summ predicted_ability std_pred_eb, detail

* ===================================================================== *
* ----------------- Peer achievement (empirical bayes)----------------- *
* ===================================================================== *

* calculate expected peer achievement 

local blable "predicted_ability"


bys academycode std_grp: egen total_t_bl_eb = total(`blable')
bys academycode std_grp: egen count_t_bl_eb = count(`blable')

gen meanpeerscore_t_bl_eb = (total_t_bl - `blable')/(count_t_bl - 1)

bys academycode grade: egen total_c_bl_eb = total(`blable')
bys academycode grade: egen count_c_bl_eb = count(`blable')

gen meanpeerscore_c_bl_eb = (total_c_bl_eb - `blable')/(count_c_bl_eb - 1)

gen exp_meanpeerscore_bl_eb = (P_t*meanpeerscore_t_bl_eb) + (P_c*meanpeerscore_c_bl_eb)
lab var exp_meanpeerscore_bl_eb "E[Mean peer ability]"

gen meanpeerscore_bl_eb = meanpeerscore_t_bl_eb
replace meanpeerscore_bl_eb = meanpeerscore_c_bl_eb if treat == 0
lab var meanpeerscore_bl_eb "Mean peer ability"

* sd

bys academycode std_grp: egen mean_std_endline_hat_t_eb = mean(`blable')
gen num_sd_t_eb = (`blable' - mean_std_endline_hat_t_eb)^2
bys academycode std_grp: egen demeansumsq_t_eb = total(num_sd_t_eb)

gen sdpeerscore_t_eb = sqrt((demeansumsq_t_eb - num_sd_t_eb)/(count_t_bl_eb -1))


bys academycode grade: egen mean_std_endline_hat_c_eb = mean(`blable')
gen num_sd_c_eb = (`blable' - mean_std_endline_hat_c_eb )^2
bys academycode grade: egen demeansumsq_c_eb = total(num_sd_c_eb)

gen sdpeerscore_c_eb = sqrt((demeansumsq_c_eb - num_sd_c_eb)/(count_c_bl_eb -1))


gen exp_sdpeerscore_eb = (P_t*sdpeerscore_t_eb) + (P_c*sdpeerscore_c_eb)
lab var exp_sdpeerscore_eb "E[Mean peer score dispersion]"


gen sdpeerscore_eb = sdpeerscore_c_eb
replace sdpeerscore_eb = sdpeerscore_t_eb if treat == 1 

lab var sdpeerscore_eb "Mean peer score dispersion"




* ===================================================================== *
* -----------------     	   Dispersion bl          ----------------- *
* ===================================================================== *


bys academycode grade: egen mean_bl_c_eb = mean(`blable')
bys academycode std_grp: egen mean_bl_t_eb = mean(`blable')

gen dev_mean_t_bl_eb = abs(`blable' -  mean_bl_t_eb)
gen dev_mean_c_bl_eb = abs(`blable' -  mean_bl_c_eb)

gen exp_devmean_bl_eb = (P_t*dev_mean_t_bl_eb) + (P_c*dev_mean_c_bl_eb)
lab var exp_devmean_bl_eb "E[Distance from mean instruction]"

gen mean_bl_eb = mean_bl_c_eb
replace mean_bl_eb = mean_bl_t_eb if treat == 1 

gen dev_mean_bl_eb = abs(`blable' - mean_bl_eb)
lab var dev_mean_bl_eb "Distance from mean instruction"


bys academycode grade: egen med_bl_c_eb2 = median(`blable')
bys academycode std_grp: egen med_bl_t_eb2 = median(`blable')

gen dev_med_t_bl_eb2 = abs(`blable' -  med_bl_t_eb2)
gen dev_med_c_bl_eb2 = abs(`blable' -  med_bl_c_eb2)

gen exp_devmed_bl_eb2 = (P_t*dev_med_t_bl_eb2) + (P_c*dev_med_c_bl_eb2)
lab var exp_devmed_bl_eb2 "E[Distance from median instruction]"

gen med_bl_eb2 = med_bl_c_eb2
replace med_bl_eb2 = med_bl_t_eb2 if treat == 1 

gen dev_med_bl_eb2 = abs(`blable' - med_bl_eb2)
lab var dev_med_bl_eb2 "Distance from median instruction"



gen highability = 0
gen lowability = 0
gen medability = 0 
gen medianability = 0



forval g = 1/4 {
	summ `blable' if grade == `g', d
	replace highability = 1 if `blable' > `r(p75)' & grade==`g'
	replace lowability = 1 if `blable' < `r(p25)' & grade==`g'
	replace medability = 1 if `blable' >= `r(p25)' & `blable' <= `r(p75)' & grade==`g'
	replace medianability = 1 if `blable' < `r(p50)' & grade==`g'

}



* ===================================================================== *
* ------------Distance from level of instruction (eb) ----------------- *
* ===================================================================== *
/*
bys academycode: egen med_bl_1_eb = median(predicted_ability) if grade == 1
bys academycode: egen median_inst_g1_eb = max(med_bl_1_eb)

bys academycode: egen med_bl_2_eb = median(predicted_ability) if grade == 2
bys academycode: egen median_inst_g2_eb = max(med_bl_2_eb)

bys academycode: egen med_bl_3_eb = median(predicted_ability) if grade == 3
bys academycode: egen median_inst_g3_eb = max(med_bl_3_eb)

bys academycode: egen med_bl_4_eb = median(predicted_ability) if grade == 4
bys academycode: egen median_inst_g4_eb = max(med_bl_4_eb)

gen dev_med_t_eb = abs(predicted_ability -  median_inst_g1*(std_grp==1) - median_inst_g2*(std_grp==2) - median_inst_g3*(std_grp==3) - median_inst_g4*(std_grp==4))
gen dev_med_c_eb = abs(predicted_ability -  median_inst_g1*(grade==1) - median_inst_g2*(grade==2) - median_inst_g3*(grade==3) - median_inst_g4*(grade==4))

gen exp_devmed_eb = (P_t*dev_med_t_bl_eb) + (P_c*dev_med_c_bl_eb)
lab var exp_devmed_eb "E[Distance from median instruction]"

gen dev_med_eb = dev_med_t_eb
replace dev_med_eb = dev_med_c_eb if treat == 0
lab var dev_med_eb "Distance from median instruction"

*/


gen exp0 = gg0 
lab var exp0 "Stacked"

gen exp1 = 1-g12
lab var exp1 "Grades 3-4"


gen exp2 = g12
lab var exp2 "Grades 1-2"

gen purplefull = studygroup34==1 | studygroup12 == 1
gen trXpurplefull = treat*purplefull 

lab var purplefull "Upper group"
lab var trXpurplefull "Treatment $\times$ Upper group"


















