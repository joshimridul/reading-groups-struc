
/*==========================================================================

Title: 4a_L_AG_prepare.do 
Author: Mridul Joshi
Date: Mon Mar 14 15:58:07 2022

Description: Construct variables for structural analysis 

===========================================================================*/



use "${datadir}/Liberia/5_L_AG_full_wide.dta", clear 

drop if treat == .
drop if stream == 2

* ===================================================================== *
* -----------------   Create propensity scores        ----------------- *
* ===================================================================== *


preserve 

collapse treat, by(academycode acad_year g12)

bys acad_year g12: egen P_t = mean(treat)
gen P_c = 1- P_t

keep g12 academycode P_t P_c

tempfile prop
save `prop'

restore

merge m:1 g12 academycode using `prop', gen(_mprop)   // contains the probability of treatment for each observation


* ===================================================================== *
* -----------------     	    Restrictions          ----------------- *
* ===================================================================== *

* no baseline scores for any student in a grade in an academy
bys academycode grade: egen mean_gr_bl = mean(score_bl)
bys academycode ggroup: egen max_gr_bl_score = max(mean_gr_bl) //, missing
gen no_gr_bl_score = max_gr_bl_score == . 

lab var no_gr_bl_score "No baseline score reported in any grade in academy-grade group"

* no endline scores for any student in a grade in an academy
bys academycode grade: egen mean_gr_el = mean(score_el)
bys academycode ggroup: egen max_gr_el_score = max(mean_gr_el) //, missing
gen no_gr_el_score = max_gr_el_score == . 

lab var no_gr_el_score "No endline score reported in any grade in academy-grade group"



gen SCORE_EL = score_el 
replace SCORE_EL = score_ml if mi(score_el)

bys academycode grade: egen mean_gr_EL = mean(SCORE_EL)
bys academycode ggroup: egen max_gr_EL_score = max(mean_gr_EL) //, missing
gen no_gr_EL_score = max_gr_EL_score == . 

* no baseline scores for any student in an academy
bys academycode: egen acadmean_bl = mean(score_bl)
gen no_bl_score = acadmean_bl == .
lab var no_bl_score "No baseline score reported in academy"

* no endline scores for any student in an academy
bys academycode: egen acadmean_el = mean(score_el)
gen no_el_score = acadmean_el == .
lab var no_el_score "No endline score reported in academy"

* there is only grade in one academy with a B stream - does it make sense to exclude it or count it as a single stream?
bys academycode: egen stream_mean = mean(stream)
gen twostreams = stream_mean != 1 
lab var twostreams "Academy has two streams"

* there are 8 schools with just one grade - should I remove them before or after calculating propensity scores? 
* all in the control group
bys academycode g12: egen grade_mean = mean(grade)
gen single_grade = inlist(grade_mean,1,2,3,4)
lab var single_grade "Academy has single grade"



* standardised test scores 

summ score_bl if grade == 1 & treat == 0
gen std_score_bl = (score_bl - `r(mean)')/`r(sd)'

summ score_bl if grade == 2 & treat == 0
replace std_score_bl = (score_bl - `r(mean)')/`r(sd)' if grade ==2

summ score_bl if grade == 3 & treat == 0
replace std_score_bl = (score_bl - `r(mean)')/`r(sd)' if grade ==3

summ score_bl if grade == 4 & treat == 0
replace std_score_bl = (score_bl - `r(mean)')/`r(sd)' if grade ==4




summ score_ml if grade == 1 & treat == 0
gen std_score_ml = (score_ml - `r(mean)')/`r(sd)'

summ score_ml if grade == 2 & treat == 0
replace std_score_ml = (score_ml - `r(mean)')/`r(sd)' if grade ==2

summ score_ml if grade == 3 & treat == 0
replace std_score_ml = (score_ml - `r(mean)')/`r(sd)' if grade ==3

summ score_ml if grade == 4 & treat == 0
replace std_score_ml = (score_ml - `r(mean)')/`r(sd)' if grade ==4




/*
summ score_ml if inlist(grade, 1, 2) & treat == 0
gen std_score_ml = (score_ml - `r(mean)')/`r(sd)'

summ score_ml if inlist(grade, 1, 2) & treat == 0
replace std_score_ml = (score_ml - `r(mean)')/`r(sd)' if inlist(grade,3,4)

lab var std_score_ml "Standardised midline score"
*/

summ score_el if grade == 1 & treat == 0
gen std_score_el = (score_el - `r(mean)')/`r(sd)'

summ score_el if grade == 2 & treat == 0
replace std_score_el = (score_el - `r(mean)')/`r(sd)' if grade ==2

summ score_el if grade == 3 & treat == 0
replace std_score_el = (score_el - `r(mean)')/`r(sd)' if grade ==3

summ score_el if grade == 4 & treat == 0
replace std_score_el = (score_el - `r(mean)')/`r(sd)' if grade ==4


/*
summ score_bl if inlist(grade, 1, 2) & treat == 0
gen std_score_bl = (score_bl - `r(mean)')/`r(sd)'

summ score_bl if inlist(grade, 3, 4) & treat == 0
replace std_score_bl = (score_bl - `r(mean)')/`r(sd)' if inlist(grade,3,4)

lab var std_score_bl "Standardised baseline score"


gen MISSING_EL = mi(score_el)


summ SCORE_EL if inlist(grade, 1, 2) & treat == 0
gen std_score_EL = (SCORE_EL - `r(mean)')/`r(sd)'

summ SCORE_EL if inlist(grade, 3, 4) & treat == 0
replace std_score_EL = (SCORE_EL - `r(mean)')/`r(sd)' if inlist(grade,3,4)

lab var std_score_EL "Standardised endline score"


*drop score_el
*gen score_el = SCORE_EL 

summ score_el if inlist(grade, 1, 2) & treat == 0
gen std_score_el = (score_el - `r(mean)')/`r(sd)'

summ score_el if inlist(grade, 3, 4) & treat == 0
replace std_score_el = (score_el - `r(mean)')/`r(sd)' if inlist(grade,3,4)

lab var std_score_el "Standardised endline score"
*/

* ===================================================================== *
* -----------------     Expected grade/level          ----------------- *
* ===================================================================== *

gen grade_recoded = 1
replace grade_recoded = -1 if inlist(grade, 1,3)


gen level_c  = grade_recoded 
gen level_t = grade_recoded

replace level_t = (grade_recoded + 2) if inlist(grade,1,3) & inlist(std_grp,2,4)
replace level_t = (grade_recoded - 2) if inlist(grade,2,4) & inlist(std_grp,1,3)

gen exp_level = (P_t*level_t) + (P_c*level_c)

gen realised_level = level_t
replace realised_level = level_c if treat == 0

lab var exp_level "E[Level]"
lab var realised_level "Level"


* ===================================================================== *
* -----------------        Expected class size        ----------------- *
* ===================================================================== *


*bys academycode std_grp: egen N_t = count(studyid) if enrolled_date < td(09nov2018) 
*bys academycode grade: egen N_c = count(studyid) if enrolled_date < td(09nov2018) 

bys academycode std_grp: egen N_t = count(studyid) if (pupil_observed == 6 | pupil_observed == 7 | pupil_observed == 1) 
bys academycode grade: egen N_c = count(studyid) if (pupil_observed == 6 | pupil_observed == 7 | pupil_observed == 1) 

bys academycode std_grp: egen csize_t = max(N_t)
bys academycode grade: egen csize_c = max(N_c) 

gen log_csize_t = log(csize_t)
gen log_csize_c = log(csize_c)


gen exp_classsize = (P_t*csize_t) + (P_c*csize_c)
lab var exp_classsize "E[Class size]"

gen exp_logclasssize = (P_t*csize_t) + (P_c*csize_c)
lab var exp_logclasssize "E[Log Class size]"


gen classsize = csize_t
replace classsize = csize_c if treat == 0
lab var classsize "Class size"

gen logclasssize = log_csize_t
replace logclasssize = log_csize_t if treat == 0
lab var logclasssize "Log Class size"



* ===================================================================== *
* -----------------    Predicted endline scores       ----------------- *
* ===================================================================== *

tab grade, gen(gr)

gen score_bl_gr1 = score_bl*gr1
gen score_bl_gr2 = score_bl*gr2
gen score_bl_gr3 = score_bl*gr3
gen score_bl_gr4 = score_bl*gr4

gen score_ml_gr1 = score_ml*gr1
gen score_ml_gr2 = score_ml*gr2
gen score_ml_gr3 = score_ml*gr3
gen score_ml_gr4 = score_ml*gr4


** predicted endline scores (leave-academy i-out predictions)

levelsof academycode if treat == 0, loc(acad)

foreach a in `acad' {
	reg score_el score_bl score_bl_gr* score_ml score_ml_gr* gr* if treat !=1 & academycode != `a'
	predict endline_hat_`a', xb
	replace endline_hat_`a' = . if academycode != `a'
	replace endline_hat_`a' = . if treat != 0
}

reg score_el score_bl score_bl_gr* score_ml score_ml_gr* gr* if treat == 0 
predict endline_hat_t, xb
replace endline_hat_t = . if treat !=1


egen endline_hat = rowtotal(endline_hat_*)
replace endline_hat = . if endline_hat == 0

summ endline_hat if treat == 0
gen std_endline_hat = (endline_hat - `r(mean)')/`r(sd)'
lab var std_endline_hat "Ind. pred. score"

drop endline_hat_*



* ===================================================================== *
* -----------------    Peer achievement (predicted)   ----------------- *
* ===================================================================== *


bys academycode std_grp: egen total_t = total(std_endline_hat)
bys academycode std_grp: egen count_t = count(std_endline_hat)

gen meanpeerscore_t= (total_t - std_endline_hat)/(count_t - 1)

bys academycode grade: egen total_c = total(std_endline_hat)
bys academycode grade: egen count_c = count(std_endline_hat)

gen meanpeerscore_c = (total_c - std_endline_hat)/(count_c - 1)

gen exp_meanpeerscore = (P_t*meanpeerscore_t) + (P_c*meanpeerscore_c)
lab var exp_meanpeerscore "E[Peer predicted score]"

gen meanpeerscore = meanpeerscore_t
replace meanpeerscore = meanpeerscore_c if treat == 0
lab var meanpeerscore "Peer predicted score"


* ===================================================================== *
* -----------------   SD of peer score (predicted)    ----------------- *
* ===================================================================== *

bys academycode std_grp: egen mean_std_endline_hat_t = mean(std_endline_hat)
gen num_sd_t = (std_endline_hat - mean_std_endline_hat_t)^2
bys academycode std_grp stream: egen demeansumsq_t = total(num_sd_t)

gen sdpeerscore_t = sqrt((demeansumsq_t - num_sd_t)/(count_t -1))


bys academycode grade: egen mean_std_endline_hat_c = mean(std_endline_hat)
gen num_sd_c = (std_endline_hat - mean_std_endline_hat_c )^2
bys academycode grade: egen demeansumsq_c = total(num_sd_c)

gen sdpeerscore_c = sqrt((demeansumsq_c - num_sd_c)/(count_c -1))


gen exp_sdpeerscore = (P_t*sdpeerscore_t) + (P_c*sdpeerscore_c)
lab var exp_sdpeerscore "E[SD peer score]"


gen sdpeerscore = sdpeerscore_c
replace sdpeerscore = sdpeerscore_t if treat == 1 

lab var sdpeerscore "Dispersion in peer scores"


* ===================================================================== *
* -----------------   Peer achievement (baseline)     ----------------- *
* ===================================================================== *

* calculate expected peer achievement 

bys academycode std_grp: egen total_t_bl = total(std_score_bl)
bys academycode std_grp: egen count_t_bl = count(std_score_bl)

gen meanpeerscore_t_bl = (total_t_bl - std_score_bl)/(count_t_bl - 1)

bys academycode grade: egen total_c_bl = total(std_score_bl)
bys academycode grade: egen count_c_bl = count(std_score_bl)

gen meanpeerscore_c_bl = (total_c_bl - std_score_bl)/(count_c_bl - 1)

gen exp_meanpeerscore_bl = (P_t*meanpeerscore_t_bl) + (P_c*meanpeerscore_c_bl)
lab var exp_meanpeerscore_bl "E[Peer baseline score]"

gen meanpeerscore_bl = meanpeerscore_t_bl
replace meanpeerscore_bl = meanpeerscore_c_bl if treat == 0
lab var meanpeerscore_bl "Peer baseline score"


* ===================================================================== *
* -----------------   SD of peer score (baseline)    ----------------- *
* ===================================================================== *

bys academycode std_grp: egen mean_std_score_bl_t = mean(std_score_bl)
gen num_sd_t_bl = (std_score_bl - mean_std_score_bl_t)^2
bys academycode std_grp: egen demeansumsq_t_bl = total(num_sd_t_bl)

gen sdpeerscore_t_bl = sqrt((demeansumsq_t_bl - num_sd_t_bl)/(count_t_bl -1))


bys academycode grade: egen mean_std_score_bl_c = mean(std_score_bl)
gen num_sd_c_bl = (std_score_bl - mean_std_score_bl_c)^2
bys academycode grade: egen demeansumsq_c_bl = total(num_sd_c_bl)

gen sdpeerscore_c_bl = sqrt((demeansumsq_c_bl - num_sd_c_bl)/(count_c_bl -1))


gen exp_sdpeerscore_bl = (P_t*sdpeerscore_t_bl) + (P_c*sdpeerscore_c_bl)
lab var exp_sdpeerscore_bl "E[SD baseline peer score]"


gen sdpeerscore_bl = sdpeerscore_c_bl
replace sdpeerscore_bl = sdpeerscore_t_bl if treat == 1 

lab var sdpeerscore_bl "Dispersion in baseline peer scores"


* ===================================================================== *
* -----------------     Dispersion (predicted)        ----------------- *
* ===================================================================== *

bys academycode grade: egen mean_ehat_c = mean(std_endline_hat)
bys academycode std_grp: egen mean_ehat_t = mean(std_endline_hat)

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

bys academycode grade: egen mean_el_c = mean(std_score_el)
bys academycode std_grp: egen mean_el_t = mean(std_score_el)

gen dev_mean_t = abs(std_score_el -  mean_el_t)
gen dev_mean_c = abs(std_score_el -  mean_el_c)

gen exp_devmean_el = (P_t*dev_mean_t) + (P_c*dev_mean_c)
lab var exp_devmean_el "E[dispersion]"

gen mean_el = mean_el_c
replace mean_el = mean_el_t if treat == 1 

gen dev_mean_el = abs(std_score_el - mean_el)
lab var dev_mean_ehat "Dispersion"


* ===================================================================== *
* -----------------     Dispersion (baseline)        ----------------- *
* ===================================================================== *

bys academycode grade: egen mean_bl_c = mean(std_score_bl)
bys academycode std_grp: egen mean_bl_t = mean(std_score_bl)

gen dev_mean_t_bl = abs(std_score_bl -  mean_bl_t)
gen dev_mean_c_bl = abs(std_score_bl -  mean_bl_c)

gen exp_devmean_bl = (P_t*dev_mean_t_bl) + (P_c*dev_mean_c_bl)
lab var exp_devmean_bl "E[Dispersion]"

gen mean_bl = mean_bl_c
replace mean_bl = mean_bl_t if treat == 1 

gen dev_mean_bl = abs(std_score_bl - mean_bl)
lab var dev_mean_bl "Dispersion"



* ===================================================================== *
* ----------------- Distance from level of instruction ----------------- *
* ===================================================================== *

bys academycode: egen med_bl_1 = median(std_score_bl) if grade == 1
bys academycode: egen median_inst_g1 = max(med_bl_1)

bys academycode: egen med_bl_2 = median(std_score_bl) if grade == 2
bys academycode: egen median_inst_g2 = max(med_bl_2)

bys academycode: egen med_bl_3 = median(std_score_bl) if grade == 3
bys academycode: egen median_inst_g3 = max(med_bl_3)

bys academycode: egen med_bl_4 = median(std_score_bl) if grade == 4
bys academycode: egen median_inst_g4 = max(med_bl_4)

*bys academycode purple: egen med_bl_t = median(std_comp_score_bl)
gen dev_med_t_ehat = abs(std_endline_hat -  median_inst_g1*(std_grp==1) - median_inst_g2*(std_grp==2) - median_inst_g3*(std_grp==3) - median_inst_g4*(std_grp==4))
gen dev_med_c_ehat = abs(std_endline_hat -  median_inst_g1*(grade==1) - median_inst_g2*(grade==2) - median_inst_g3*(grade==3) - median_inst_g4*(grade==4))

gen exp_devmed_ehat = (P_t*dev_med_t_ehat) + (P_c*dev_med_c_ehat)
lab var exp_devmed_ehat "E[Distance]"

gen dev_med_ehat = dev_med_t_ehat
replace dev_med_ehat = dev_med_c_ehat if treat == 0
lab var dev_med_ehat "Distance from median instruction"


* ===================================================================== *
* ------------Distance from level of instruction (bl) ----------------- *
* ===================================================================== *


gen dev_med_t_bl = abs(std_score_bl -  median_inst_g1*(std_grp==1) - median_inst_g2*(std_grp==2) - median_inst_g3*(std_grp==3) - median_inst_g4*(std_grp==4))
gen dev_med_c_bl = abs(std_score_bl -  median_inst_g1*(grade==1) - median_inst_g2*(grade==2) - median_inst_g3*(grade==3) - median_inst_g4*(grade==4))

gen exp_devmed_bl = (P_t*dev_med_t_bl) + (P_c*dev_med_c_bl)
lab var exp_devmed_ehat "E[Distance]"

gen dev_med_bl = dev_med_t_bl
replace dev_med_bl = dev_med_c_bl if treat == 0
lab var dev_med_bl "Distance from median instruction"




* ===================================================================== *
* -----------------     	   Interactions           ----------------- *
* ===================================================================== *

gen peer_hatXind_hat = std_endline_hat*meanpeerscore
lab var peer_hatXind_hat "Peer predicted score $\times$ Ind. pred. score"

gen peer_hat_blXbl = std_score_bl*meanpeerscore_bl
lab var peer_hat_blXbl "Peer baseline score $\times$ Std. baseline score"

gen peer_hatXbl = std_score_bl*meanpeerscore
lab var peer_hatXbl "Peer predicted score $\times$ Std. baseline score"

gen levelXind_hat = realised_level*std_endline_hat
lab var levelXind_hat "Level $\times$ Ind. pred. score"

gen levelXbl = realised_level*std_score_bl
lab var levelXbl "Level $\times$ Std. baseline score"

gen classizeXind_hat = classsize*std_endline_hat
lab var classizeXind_hat "Class size $\times$ Ind. pred. score"

*gen classize_elXind_hat = classsize_el*std_endline_hat
*lab var classize_elXind_hat "Class size $\times$ Ind. pred. score"

gen classizeXbl = classsize*std_score_bl
lab var classizeXbl "Class size $\times$ Std. baseline score"

*gen classize_elXbl = classsize_el*std_score_bl
*lab var classize_elXbl "Class size $\times$ Std. baseline score"

gen dispXind_hat = dev_mean_el*std_endline_hat
lab var dispXind_hat "Dispersion $\times$ Ind. pred. score"

gen dispXbl = dev_mean_bl*std_score_bl
lab var dispXbl "Dispersion $\times$ Std. baseline score"

gen logclassizeXind_hat = logclasssize*std_endline_hat
lab var logclassizeXind_hat "Log Class size $\times$ Ind. pred. score"

gen logclassizeXbl = logclasssize*std_score_bl
lab var logclassizeXbl "Log Class size $\times$ Std. baseline score"



* ===================================================================== *
* -----------------            	 Restrictions         ----------------- *
* ===================================================================== *

drop if no_gr_bl_score
*drop if no_gr_el_score
*drop if no_gr_EL_score
*drop if no_bl_score
*drop if no_el_score
drop if single_grade

* kids who moved between academies  
duplicates tag academycode studyid , gen(dups_acad_change)
lab var dups_acad_change "Pupils switched academy mid-intervention"

gen has_noscore = !(pupil_observed == 6 | pupil_observed == 7)  // observed at baseline and endline 


gen nostudent_readinggrp = (count_c_bl  < = 1 | count_t_bl <= 1)
lab var nostudent_readinggrp "Fewer than one baseline testscores in reading group"

gen mi_bl = mi(score_bl)

*gen mi_el = mi(score_el)

gen finsamp = !dups_acad_change & !(mi_bl == 1 | nostudent_readinggrp ==1) & sample==1

*gen finsamp = !dups_acad_change & !mi_el & !(nostudent_readinggrp ==1) & sample==1


* ===================================================================== *
* -----------------     	    Save dataset          ----------------- *
* ===================================================================== *

save "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", replace






