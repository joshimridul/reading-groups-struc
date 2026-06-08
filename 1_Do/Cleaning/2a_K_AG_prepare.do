
/*==========================================================================

Title: 2a_K_AG_prepare.do 
Author: Mridul Joshi
Date: Mon Mar 14 14:36:05 2022

Description: Create variables for structural analysis

===========================================================================*/


use "${datadir}/Kenya/5_K_AG_full_wide.dta", clear 

drop if stream == 2


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
* -----------------     Sample restrictions           ----------------- *
* ===================================================================== *

* no baseline scores for any student in a grade in an academy
bys academycode grade: egen mean_gr_comp_bl = mean(comp_score_bl)
bys academycode: egen max_gr_bl_score = max(mean_gr_comp_bl), missing
gen no_gr_bl_score = max_gr_bl_score == . 

lab var no_gr_bl_score "No baseline score reported in any grade in an academy"

* no endline scores for any student in a grade in an academy
bys academycode grade: egen mean_gr_comp_el = mean(comp_score_el)
bys academycode: egen max_gr_el_score = max(mean_gr_comp_el), missing
gen no_gr_el_score = max_gr_el_score == . 

lab var no_gr_el_score "No endline score reported in any grade in an academy"

* no baseline scores for any student in an academy
bys academycode: egen mean_comp_bl = mean(comp_score_bl)
gen no_bl_score = mean_comp_bl == .
lab var no_bl_score "No baseline score reported in academy"

* no endline scores for any student in an academy
bys academycode: egen mean_comp_el = mean(comp_score_el)
gen no_el_score = mean_comp_el == .
lab var no_el_score "No endline score reported in academy"

* there is only grade in one academy with a B stream - does it make sense to exclude it or count it as a single stream?
bys academycode: egen stream_mean = mean(stream)
gen twostreams = stream_mean != 1 
lab var twostreams "Academy has two streams"

* there are 8 schools with just one grade - should I remove them before or after calculating propensity scores? After for now. 
* all in the control group
bys academycode: egen grade_mean = mean(grade)
gen single_grade = grade_mean == 1
lab var single_grade "Academy has single grade"


* ===================================================================== *
* -----------------        Expected class size        ----------------- *
* ===================================================================== *

* class size at baseline 
bys academycode purple: egen N_t = count(studyid) if inlist(pupil_observed,2,3)
bys academycode grade: egen N_c = count(studyid)  if inlist(pupil_observed,2,3)

/* 838 only EL cases that generate missing values */

bys academycode purple: egen csize_t = max(N_t)
bys academycode grade: egen csize_c = max(N_c) 


* ===================================================================== *
* -----------------     Standardise test scores        ----------------- *
* ===================================================================== *

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


*************

gen log_csize_t = log(csize_t)
gen log_csize_c = log(csize_c)

gen exp_classsize = (P_t*csize_t) + (P_c*csize_c)
lab var exp_classsize "E[Class size]"

gen exp_logclasssize = (P_t*log_csize_t) + (P_c*log_csize_c)
lab var exp_logclasssize "E[Log Class size]"

gen classsize = csize_t
replace classsize = csize_c  if treat == 0
lab var classsize "Class size"

gen logclasssize = log_csize_t
replace logclasssize = log_csize_c if treat == 0
lab var logclasssize "Log Class size"

*keep academycode studyid exp_classsize classsize exp_logclasssize logclasssize csize_t csize_c 

*tempfile csize
*save `csize'

*restore 

*merge m:1 academycode studyid using `csize', gen(_mcsize)


* ===================================================================== *
* -----------------      Expected grade/level         ----------------- *
* ===================================================================== *

* for now treat lower grade as -1 and upper grade as 1

gen grade_recoded = 1
*replace grade_recoded = -1 if grade == 1
replace grade_recoded = 0 if grade == 1


gen level_c  = grade_recoded 
gen level_t = grade_recoded


gen grade_new_c = grade 
gen grade_new_t = grade 

replace grade_new_t = (grade + 1) if grade == 1 & purple == 1
replace grade_new_t = (grade - 1) if grade == 2 & purple == 0

replace level_t = (grade_recoded + 1) if grade == 1 & purple == 1
replace level_t = (grade_recoded - 1) if grade == 2 & purple == 0

gen exp_level = (P_t*level_t) + (P_c*level_c)
lab var exp_level "E[Level]"

gen realised_level = level_t
replace realised_level = level_c if treat == 0
lab var realised_level "Level"
 

* ===================================================================== *
* -----------------     Predicted endline scores      ----------------- *
* ===================================================================== *

** predicted endline scores (leave-academy i-out predictions)

gen std_comp_score_bl_gr = std_comp_score_bl*g1


* for control group
levelsof academycode if treat == 0, loc(acad)

foreach a in `acad' {
	reg std_comp_score_el std_comp_score_bl std_comp_score_bl_gr g1 if treat == 0 & academycode != `a'
	predict endline_hat_`a', xb
	replace endline_hat_`a' = . if academycode != `a'
	replace endline_hat_`a' = . if treat == 1

}

* for treatment group
reg std_comp_score_el std_comp_score_bl std_comp_score_bl_gr g1 if treat == 0 
predict endline_hat_t, xb
replace endline_hat_t = . if treat == 0

egen endline_hat = rowtotal(endline_hat_*)
replace endline_hat = . if endline_hat == 0

summ endline_hat if treat == 0
gen std_endline_hat = (endline_hat - `r(mean)')/`r(sd)'
lab var std_endline_hat "Ind. pred. score"

drop endline_hat_*

* ===================================================================== *
* -----------------   Peer achievement (predicted)    ----------------- *
* ===================================================================== *


* calculate expected peer achievement 

bys academycode purple: egen total_t = total(std_endline_hat)
bys academycode purple: egen count_t = count(std_endline_hat)

gen meanpeerscore_t= (total_t - std_endline_hat)/(count_t - 1)

bys academycode grade: egen total_c = total(std_endline_hat)
bys academycode grade: egen count_c = count(std_endline_hat)

gen meanpeerscore_c= (total_c - std_endline_hat)/(count_c - 1)

gen exp_meanpeerscore = (P_t*meanpeerscore_t) + (P_c*meanpeerscore_c)
lab var exp_meanpeerscore "E[Peer predicted score]"

gen meanpeerscore = meanpeerscore_t
replace meanpeerscore = meanpeerscore_c if treat == 0
lab var meanpeerscore "Peer predicted score"


* ===================================================================== *
* -----------------   SD of peer score (predicted)    ----------------- *
* ===================================================================== *

bys academycode purple: egen mean_std_endline_hat_t = mean(std_endline_hat)
gen num_sd_t = (std_endline_hat - mean_std_endline_hat_t)^2
bys academycode purple: egen demeansumsq_t = total(num_sd_t)

gen sdpeerscore_t = sqrt((demeansumsq_t - num_sd_t)/(count_t -1))



bys academycode grade: egen mean_std_endline_hat_c = mean(std_endline_hat)
gen num_sd_c = (std_endline_hat - mean_std_endline_hat_c)^2
bys academycode grade: egen demeansumsq_c = total(num_sd_c)

gen sdpeerscore_c = sqrt((demeansumsq_c - num_sd_c)/(count_c -1))

bys academycode grade: egen sd_c = sd(std_endline_hat)


gen exp_sdpeerscore = (P_t*sdpeerscore_t) + (P_c*sdpeerscore_c)
lab var exp_sdpeerscore "E[SD peer score]"


gen sdpeerscore = sdpeerscore_c
replace sdpeerscore = sdpeerscore_t if treat == 1 

lab var sdpeerscore "Dispersion in peer scores"



* ===================================================================== *
* -----------------   Peer achievement (baseline)     ----------------- *
* ===================================================================== *


* calculate expected peer achievement 

bys academycode purple: egen total_t_bl = total(std_comp_score_bl)
bys academycode purple: egen count_t_bl = count(std_comp_score_bl)

gen meanpeerscore_t_bl = (total_t_bl - std_comp_score_bl)/(count_t_bl - 1)

bys academycode grade: egen total_c_bl = total(std_comp_score_bl)
bys academycode grade: egen count_c_bl = count(std_comp_score_bl)

gen meanpeerscore_c_bl = (total_c_bl - std_comp_score_bl)/(count_c_bl - 1)

gen exp_meanpeerscore_bl = (P_t*meanpeerscore_t_bl) + (P_c*meanpeerscore_c_bl)
lab var exp_meanpeerscore_bl "E[Peer baseline score]"

gen meanpeerscore_bl = meanpeerscore_t_bl
replace meanpeerscore_bl = meanpeerscore_c_bl if treat == 0
lab var meanpeerscore_bl "Peer baseline score"


* ===================================================================== *
* -----------------   SD of peer score (baseline)    ----------------- *
* ===================================================================== *

bys academycode purple: egen mean_std_score_bl_t = mean(std_comp_score_bl)
gen num_sd_t_bl = (std_comp_score_bl - mean_std_score_bl_t)^2
bys academycode purple: egen demeansumsq_t_bl = total(num_sd_t_bl)

gen sdpeerscore_t_bl = sqrt((demeansumsq_t_bl - num_sd_t_bl)/(count_t_bl -1))


bys academycode grade: egen mean_std_score_bl_c = mean(std_comp_score_bl)
gen num_sd_c_bl = (std_comp_score_bl - mean_std_score_bl_c)^2
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
bys academycode purple: egen mean_ehat_t = mean(std_endline_hat)

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

bys academycode grade: egen mean_el_c = mean(std_comp_score_el)
bys academycode purple: egen mean_el_t = mean(std_comp_score_el)
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


bys academycode grade: egen mean_bl_c = mean(std_comp_score_bl)
bys academycode purple: egen mean_bl_t = mean(std_comp_score_bl)

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


*bys academycode: egen med_bl_1 = median(std_comp_score_bl) if grade == 1
bys academycode: egen med_bl_1 = pctile(std_comp_score_bl) if grade == 1, p(75)

bys academycode: egen median_inst_g1 = max(med_bl_1)

*bys academycode: egen med_bl_2 = median(std_comp_score_bl) if grade == 2
bys academycode: egen med_bl_2 = pctile(std_comp_score_bl) if grade == 2, p(75)

bys academycode: egen median_inst_g2 = max(med_bl_2)



*bys academycode purple: egen med_bl_t = median(std_comp_score_bl)
gen dev_med_t_ehat = abs(endline_hat -  median_inst_g1*(purple==0) - median_inst_g2*(purple==1))
gen dev_med_c_ehat = abs(endline_hat -  median_inst_g1*(grade==1) - median_inst_g2*(grade==2))


gen exp_devmed_ehat = (P_t*dev_med_t_ehat) + (P_c*dev_med_c_ehat)
lab var exp_devmed_ehat "E[Distance]"

gen dev_med_ehat = dev_med_t_ehat
replace dev_med_ehat = dev_med_c_ehat if treat == 0
lab var dev_med_ehat "Distance from median instruction"

/*

sum std_comp_score_bl if grade==1, detail
local l1 = `r(p50)'
sum std_comp_score_bl if grade==2, detail
local l2 = `r(p50)'

gen d0 = abs(std_comp_score_bl - `l1'*(level_c==-1) - `l2'*(level_c==1))
gen d1 = abs(std_comp_score_bl - `l1'*(level_t==-1) - `l2'*(level_t==1))
               
gen d0_hat = abs(std_endline_hat - `l1'*(level_c==-1) - `l2'*(level_c==1))
gen d1_hat = abs(std_endline_hat - `l1'*(level_t==-1) - `l2'*(level_t==1))


drop exp_devmed_ehat dev_mean_ehat

gen exp_devmed_ehat = P_t*d1_hat + (1-P_t)*d0_hat
gen dev_mean_ehat= d1_hat*treat + d0_hat*(1-treat)
*/

* ===================================================================== *
* ------------Distance from level of instruction (bl) ----------------- *
* ===================================================================== *


gen dev_med_t_bl = abs(std_comp_score_bl -  median_inst_g1*(purple==0) - median_inst_g2*(purple==1))
gen dev_med_c_bl = abs(std_comp_score_bl -  median_inst_g1*(grade==1) - median_inst_g2*(grade==2))


*gen exp_devmed_bl = (P_t*dev_med_t_bl) + (P_c*dev_med_c_bl)
gen exp_devmed_bl = (P_t*dev_med_t_bl) + (P_c*dev_med_c_bl)
lab var exp_devmed_ehat "E[Distance]"

gen dev_med_bl = dev_med_t_bl
replace dev_med_bl = dev_med_c_bl if treat == 0
lab var dev_med_bl "Distance from median instruction"

*gen dev_med_bl =  d1*treat + d0*(1-treat)

*gen dev_med_bl = abs(std_comp_score_bl - med_bl)
lab var dev_med_bl "Distance from median instruction"


* ===================================================================== *
* -----------------     	  Avg peer distance       ----------------- *
* ===================================================================== *

* control 
bysort academycode grade (studyid): gen id_c = _n
gen avg_distance_c = .

* Loop through each academy
levelsof academycode, local(acad)
foreach ac in `acad' {
	levelsof grade if academycode == `ac', local(grad)
	foreach g in `grad'{
    	* Identify the number of students in the current academy
    	sum id_c if academycode == `ac' & grade == `g', meanonly
    	di "`r(max) || '"
    	local num_students = r(max)

    	* Loop through each student within the academy
    	forval i = 1/`num_students' {
        	* Calculate the absolute differences between this student and all others
        	* Then take the average of these differences
        	qui sum std2_compscore_bl if academycode == `ac' & grade == `g' & id_c != `i', meanonly
        	local total_peers = r(N)  // this should be nonmissing entries
        	local sum_diff = 0
        	forval j = 1/`total_peers' {
            	qui sum std2_compscore_bl if academycode == `ac' & grade == `g' & id_c == `j', meanonly
            	local peer_score = r(mean)
            	qui sum std2_compscore_bl if academycode == `ac' & grade == `g' & id_c == `i', meanonly
            	local student_score = r(mean)
            	if `peer_score' != . {
            		local diff = abs(`student_score' - `peer_score')
            		local sum_diff = `sum_diff' + `diff'
            	}
        	}
        	local avg_diff = `sum_diff' / `total_peers'
        	replace avg_distance_c = `avg_diff' if academycode == `ac' & grade == `g' & id_c == `i'
    	}
	}
}


* treat 

bysort academycode purple (studyid): gen id_t = _n
gen avg_distance_t = .

* Loop through each academy
levelsof academycode, local(acad)
foreach ac in `acad' {
	levelsof purple if academycode == `ac', local(purp)
	foreach p in `purp'{
    	* Identify the number of students in the current academy
    	sum id_t if academycode == `ac' & purple == `p', meanonly
    	di "`r(max) || '"
    	local num_students = r(max)

    	* Loop through each student within the academy
    	forval i = 1/`num_students' {
        	* Calculate the absolute differences between this student and all others
        	* Then take the average of these differences
        	qui sum std2_compscore_bl if academycode == `ac' & purple == `p' & id_t != `i', meanonly
        	local total_peers = r(N)  // this should be nonmissing entries
        	local sum_diff = 0
        	forval j = 1/`total_peers' {
            	qui sum std2_compscore_bl if academycode == `ac' & purple == `p' & id_t == `j', meanonly
            	local peer_score = r(mean)
            	qui sum std2_compscore_bl if academycode == `ac' & purple == `p' & id_t == `i', meanonly
            	local student_score = r(mean)
            	if `peer_score' != . {
            		local diff = abs(`student_score' - `peer_score')
            		local sum_diff = `sum_diff' + `diff'
            	}
        	}
        	local avg_diff = `sum_diff' / `total_peers'
        	replace avg_distance_t = `avg_diff' if academycode == `ac' & purple == `p' & id_t == `i'
    	}
	}
}


gen avg_distance = avg_distance_t 
replace avg_distance = avg_distance_c if treat == 0


gen exp_avg_distance = (P_t*avg_distance_t) + (P_c*avg_distance_c)
lab var exp_avg_distance "E[Peer distance]"



* ===================================================================== *
* -----------------   Proportion of high q peers.     ----------------- *
* ===================================================================== *


* calculate expected peer achievement 

gen high_q_peer = bl_q  == 4 

bys academycode purple: egen total_qt = total(high_q_peer)
bys academycode purple: egen count_qt = count(high_q_peer)

gen q4_peer_t= (total_qt - (high_q_peer==4))/(count_qt - 1)

bys academycode grade: egen total_qc = total(high_q_peer)
bys academycode grade: egen count_qc = count(high_q_peer)

gen q4_peer_c= (total_qc - (high_q_peer==4))/(count_qc - 1)

gen exp_q4_peer = (P_t*q4_peer_t) + (P_c*q4_peer_c)
lab var exp_meanpeerscore "E[Proportion high achieving peer]"

gen q4_peer =q4_peer_t
replace q4_peer = q4_peer_c if treat == 0
lab var meanpeerscore "Proportion high achieving peer"




gen high_q_peer34 = bl_q  >= 3

bys academycode purple: egen total_qt34 = total(high_q_peer34)
bys academycode purple: egen count_qt34 = count(high_q_peer34)

gen q4_peer_t34= (total_qt34 - (high_q_peer34>=3))/(count_qt34 - 1)

bys academycode grade: egen total_qc34 = total(high_q_peer34)
bys academycode grade: egen count_qc34 = count(high_q_peer34)

gen q4_peer_c34= (total_qc34 - (high_q_peer34>=3))/(count_qc34 - 1)

gen exp_q4_peer34 = (P_t*q4_peer_t34) + (P_c*q4_peer_c34)
lab var exp_q4_peer34 "E[Proportion high achieving peer]"

gen q4_peer34 =q4_peer_t34
replace q4_peer34 = q4_peer_c34 if treat == 0
lab var q4_peer34 "Proportion high achieving peer"



gen low_q_peer = bl_q == 1

bys academycode purple: egen total_qtl = total(low_q_peer)
bys academycode purple: egen count_qtl = count(low_q_peer)

gen q4_peer_tl= (total_qtl - (low_q_peer==1))/(count_qtl - 1)

bys academycode grade: egen total_qcl = total(low_q_peer)
bys academycode grade: egen count_qcl = count(low_q_peer)

gen q4_peer_cl= (total_qcl - (low_q_peer==1))/(count_qcl - 1)

gen exp_q4_peerl = (P_t*q4_peer_tl) + (P_c*q4_peer_cl)
lab var exp_q4_peerl "E[Proportion high achieving peer]"

gen q4_peerl =q4_peer_tl
replace q4_peerl = q4_peer_cl if treat == 0
lab var q4_peerl "Proportion of low achieving peer"

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
lab var classizeXind_hat "Class size $\times$ Ind. pred. score"

gen classizeXbl = classsize*std_comp_score_bl
lab var classizeXbl "Class size $\times$ Std. baseline score"

gen dispXind_hat = dev_mean_el*std_endline_hat
lab var dispXind_hat "Dispersion $\times$ Ind. pred. score"

gen dispXbl = dev_mean_bl*std_comp_score_bl
lab var dispXbl "Dispersion $\times$ Std. baseline score"

gen logclassizeXind_hat = logclasssize*std_endline_hat
lab var logclassizeXind_hat "Log Class size $\times$ Ind. pred. score"

gen logclassizeXbl = logclasssize*std_comp_score_bl
lab var logclassizeXbl "Log Class size $\times$ Std. baseline score"




* ===================================================================== *
* -----------------            	 Restrictions         ----------------- *
* ===================================================================== *


drop if no_gr_bl_score
*drop if no_gr_el_score
**drop if no_bl_score
drop if no_el_score
drop if single_grade

* kids who moved between academies 
duplicates tag studyid , gen(dups_acad_change)
lab var dups_acad_change "Pupils switched academy mid-intervention"

gen has_noscore = !inlist(pupil_observed,3)  // observed at baseline and endline 


gen nostudent_readinggrp = (count_c_bl  < = 1 | count_t_bl <= 1)
lab var nostudent_readinggrp "Fewer than one baseline testscores in reading group"

gen mi_bl = mi(comp_score_bl)

*gen mi_el = mi(comp_score_el)

gen finsamp = !dups_acad_change & !(mi_bl == 1 | nostudent_readinggrp ==1) & stream != 2


* ===================================================================== *
* -----------------     	    Save dataset          ----------------- *
* ===================================================================== *

save "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", replace

















