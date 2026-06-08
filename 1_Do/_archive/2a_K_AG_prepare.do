
/*==========================================================================

Title: 2a_K_AG_prepare.do 
Author: Mridul Joshi
Date: Mon Mar 14 14:36:05 2022

Description: Create variables for structural analysis

===========================================================================*/


use "${datadir}/Kenya/5_K_AG_full_wide.dta", clear 


* ===================================================================== *
* -----------------     	 Propensity scores        ----------------- *
* ===================================================================== *

* randomisation was stratified at the province level (constituency)

preserve 

collapse treat, by(academycode constituency)

bys constituency: egen P_t = mean(treat)
gen P_c = 1- P_t

keep academycode P_t P_c

tempfile prop
save `prop'

restore

merge m:1 academycode using `prop', gen(_mprop)  // contains the probability of treatment for each observation



* ===================================================================== *
* -----------------      Expected grade/level         ----------------- *
* ===================================================================== *

gen level_c  = grade 
gen level_t = grade


replace level_t = (grade + 1) if grade == 1 & purple == 1
replace level_t = (grade - 1) if grade == 2 & purple == 0

gen exp_level = (P_t*level_t) + (P_c*level_c)
lab var exp_level "E[Level]"

gen realised_level = level_t
replace realised_level = level_c if treat == 0
lab var realised_level "Level"


* ===================================================================== *
* -----------------        Expected class size        ----------------- *
* ===================================================================== *

preserve

duplicates drop academycode studyid, force 

* class size at baseline 
bys academycode purple stream: egen N_t = count(studyid) if inlist(pupil_observed,2,3)
bys academycode grade stream: egen N_c = count(studyid)  if inlist(pupil_observed,2,3)

bys academycode purple stream: egen csize_t = max(N_t)
bys academycode grade stream: egen csize_c = max(N_c) 

gen log_csize_t = log(csize_t)
gen log_csize_c = log(csize_c)

gen exp_classsize = (P_t*csize_t) + (P_c*csize_c)
lab var exp_classsize "E[Class size]"

gen exp_logclasssize = (P_t*log_csize_t) + (P_c*log_csize_c)
lab var exp_logclasssize "E[Log Class size]"

gen classsize = csize_t
replace classsize = csize_c  if treat == 0
lab var classsize "Class size ($\times$ 10)"

gen logclasssize = log_csize_t
replace logclasssize = log_csize_c if treat == 0
lab var logclasssize "Log Class size"


keep academycode studyid exp_classsize classsize exp_logclasssize logclasssize csize_t csize_c

tempfile csize
save `csize'

restore 

merge m:1 academycode studyid using `csize', gen(_mcsize)


* ===================================================================== *
* -----------------     Predicted endline scores      ----------------- *
* ===================================================================== *

** predicted endline scores (leave-academy i-out predictions)

gen comp_score_bl_gr = comp_score_bl*g1


* for control group
levelsof academycode if treat == 0, loc(acad)

foreach a in `acad' {
	reg comp_score_el comp_score_bl comp_score_bl_gr g1 if treat == 0 & academycode != `a'
	predict endline_hat_`a', xb
	replace endline_hat_`a' = . if academycode != `a'
	replace endline_hat_`a' = . if treat == 1

}

* for treatment group
reg comp_score_el comp_score_bl comp_score_bl_gr g1 if treat == 0 
predict endline_hat_t, xb
replace endline_hat_t = . if treat == 0

egen endline_hat = rowtotal(endline_hat_*)
replace endline_hat = . if endline_hat == 0

summ endline_hat if treat == 0
gen std_endline_hat = (endline_hat - `r(mean)')/`r(sd)'
lab var std_endline_hat "Ind. pred. score"



* ===================================================================== *
* -----------------   Peer achievement (predicted)    ----------------- *
* ===================================================================== *


* calculate expected peer achievement 

bys academycode purple stream: egen total_t = total(std_endline_hat)
bys academycode purple stream: egen count_t = count(std_endline_hat)

gen meanpeerscore_t= (total_t - std_endline_hat)/(count_t - 1)

bys academycode grade stream: egen total_c = total(std_endline_hat)
bys academycode grade stream: egen count_c = count(std_endline_hat)

gen meanpeerscore_c= (total_c - std_endline_hat)/(count_c - 1)

gen exp_meanpeerscore = (P_t*meanpeerscore_t) + (P_c*meanpeerscore_c)
lab var exp_meanpeerscore "E[Peer predicted score]"

gen meanpeerscore = meanpeerscore_t
replace meanpeerscore = meanpeerscore_c if treat == 0
lab var meanpeerscore "Peer predicted score"



* ===================================================================== *
* -----------------   Peer achievement (baseline)     ----------------- *
* ===================================================================== *


* calculate expected peer achievement 

bys academycode purple stream: egen total_t_bl = total(std_comp_score_bl)
bys academycode purple stream: egen count_t_bl = count(std_comp_score_bl)

gen meanpeerscore_t_bl = (total_t_bl - std_comp_score_bl)/(count_t_bl - 1)

bys academycode grade stream: egen total_c_bl = total(std_comp_score_bl)
bys academycode grade stream: egen count_c_bl = count(std_comp_score_bl)

gen meanpeerscore_c_bl = (total_c_bl - std_comp_score_bl)/(count_c_bl - 1)

gen exp_meanpeerscore_bl = (P_t*meanpeerscore_t_bl) + (P_c*meanpeerscore_c_bl)
lab var exp_meanpeerscore_bl "E[Peer baseline score]"

gen meanpeerscore_bl = meanpeerscore_t_bl
replace meanpeerscore_bl = meanpeerscore_c_bl if treat == 0
lab var meanpeerscore_bl "Peer baseline score"


* ===================================================================== *
* -----------------     Dispersion (predicted)        ----------------- *
* ===================================================================== *

bys academycode grade stream: egen mean_ehat_c = mean(std_endline_hat)
bys academycode purple stream: egen mean_ehat_t = mean(std_endline_hat)

gen dev_mean_t_ehat = abs(std_endline_hat -  mean_ehat_t)
gen dev_mean_c_ehat = abs(std_endline_hat -  mean_ehat_c)

gen exp_devmean_ehat = (P_t*dev_mean_t_ehat) + (P_c*dev_mean_c_ehat)
lab var exp_devmean_ehat "E[dispersion]"

gen mean_ehat = mean_ehat_c
replace mean_ehat = mean_ehat_t if treat == 1 

gen dev_mean_ehat = abs(std_endline_hat - mean_ehat)
lab var dev_mean_ehat "Dispersion"


* ===================================================================== *
* -----------------     Dispersion (endline)        ----------------- *
* ===================================================================== *

bys academycode grade stream: egen mean_el_c = mean(std_comp_score_el)
bys academycode purple stream: egen mean_el_t = mean(std_comp_score_el)

gen dev_mean_t = abs(std_comp_score_el -  mean_el_t)
gen dev_mean_c = abs(std_comp_score_el -  mean_el_c)

gen exp_devmean_el = (P_t*dev_mean_t) + (P_c*dev_mean_c)
lab var exp_devmean_el "E[dispersion]"

gen mean_el = mean_el_c
replace mean_el = mean_el_t if treat == 1 

gen dev_mean_el = abs(std_comp_score_el - mean_el)
lab var dev_mean_ehat "Dispersion"


* ===================================================================== *
* -----------------     Dispersion (baseline)        ----------------- *
* ===================================================================== *

bys academycode grade stream: egen mean_bl_c = mean(std_comp_score_bl)
bys academycode purple stream: egen mean_bl_t = mean(std_comp_score_bl)

gen dev_mean_t_bl = abs(std_comp_score_bl -  mean_bl_t)
gen dev_mean_c_bl = abs(std_comp_score_bl -  mean_bl_c)

gen exp_devmean_bl = (P_t*dev_mean_t_bl) + (P_c*dev_mean_c_bl)
lab var exp_devmean_bl "E[Dispersion]"

gen mean_bl = mean_bl_c
replace mean_bl = mean_bl_t if treat == 1 

gen dev_mean_bl = abs(std_comp_score_bl - mean_bl)
lab var dev_mean_bl "Dispersion"



* ===================================================================== *
* ----------------- Distance from level of instruction ----------------- *
* ===================================================================== *


bys academycode grade: egen med_bl_c = median(std_comp_score_bl)
bys academycode purple: egen med_bl_t = median(std_comp_score_bl)

gen dev_med_t_ehat = abs(endline_hat -  med_bl_t)
gen dev_med_c_ehat = abs(endline_hat -  med_bl_c)


gen exp_devmed_ehat = (P_t*dev_med_t_ehat) + (P_c*dev_med_c_ehat)
lab var exp_devmed_ehat "E[Distance]"

gen med_bl = med_bl_c
replace med_bl = med_bl_t if treat == 1 

gen dev_med_ehat = abs(endline_hat - med_bl)
lab var dev_med_ehat "Distance from median instruction"



* ===================================================================== *
* ------------Distance from level of instruction (bl) ----------------- *
* ===================================================================== *

gen dev_med_t_bl = abs(std_comp_score_bl -  med_bl_t)
gen dev_med_c_bl = abs(std_comp_score_bl -  med_bl_c)

gen exp_devmed_bl = (P_t*dev_med_t_bl) + (P_c*dev_med_c_bl)
lab var exp_devmed_ehat "E[Distance]"

gen dev_med_bl = abs(std_comp_score_bl - med_bl)
lab var dev_med_bl "Distance from median instruction"

* ===================================================================== *
* -----------------     	   Interactions           ----------------- *
* ===================================================================== *

gen peer_hatXind_hat = std_endline_hat*meanpeerscore
lab var peer_hatXind_hat "Peer predicted score $\times$ Ind. pred. score"

gen peer_hat_blXbl = std_comp_score_bl*meanpeerscore_bl
lab var peer_hat_blXbl "Peer baseline score $\times$ Std. baseline score"

gen peer_hatXbl = std_comp_score_bl*meanpeerscore
lab var peer_hatXbl "Peer predicted score $\times$ Std. baseline score"

gen levelXind_hat = realised_level*std_endline_hat
lab var levelXind_hat "Level $\times$ Ind. pred. score"

gen levelXbl = realised_level*std_comp_score_bl
lab var levelXbl "Level $\times$ Std. baseline score"

gen classizeXind_hat = classsize*std_endline_hat
lab var classizeXind_hat "Class size $\times$ Ind. pred. score ($\times$ 10)"

gen classizeXbl = classsize*std_comp_score_bl
lab var classizeXbl "Class size $\times$ Std. baseline score ($\times$ 10)"

gen dispXind_hat = dev_mean_el*std_endline_hat
lab var dispXind_hat "Dispersion $\times$ Ind. pred. score"

gen dispXbl = dev_mean_bl*std_comp_score_bl
lab var dispXbl "Dispersion $\times$ Std. baseline score"

gen logclassizeXind_hat = logclasssize*std_endline_hat
lab var logclassizeXind_hat "Log Class size $\times$ Ind. pred. score"

gen logclassizeXbl = logclasssize*std_comp_score_bl
lab var logclassizeXbl "Log Class size $\times$ Std. baseline score"




* ===================================================================== *
* -----------------     	  Other variables         ----------------- *
* ===================================================================== *

*gen test_type = assess_competency_el == 1



* ===================================================================== *
* -----------------     	    Save dataset          ----------------- *
* ===================================================================== *

save "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", replace

















