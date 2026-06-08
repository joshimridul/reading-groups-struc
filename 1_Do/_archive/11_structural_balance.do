
/*==========================================================================

Title: 11_structural_balance.do 
Author: Mridul Joshi
Date: Mon Dec 13 02:07:47 2021

Description: Structural balance on observables 

===========================================================================*/



* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/5_K_AG_full_wide.dta", clear 


gen g1 = grade == 1 
gen g2 = grade == 2
gen g3 = grade == 3
gen g4 = grade == 4 
gen g0 = inlist(grade,1,2,3,4)

lab var g0 "Full sample"
lab var g1 "Grade 1"
lab var g2 "Grade 2"
lab var g3 "Grade 3"
lab var g4 "Grade 4"

gen yr_operation = (assess_date_el - academy_cohort)/365
lab var yr_operation "Academy years of operation"

gen blscore = std_comp_score_bl
lab var blscore "Baseline test score"

gen blscore_1 = blscore if grade == 1
gen blscore_2 = blscore if grade == 2
gen blscore_3 = blscore if grade == 3
gen blscore_4 = blscore if grade == 4

lab var blscore_1 "Grade 1 average test score"
lab var blscore_2 "Grade 2 average test score"
lab var blscore_3 "Grade 3 average test score"
lab var blscore_4 "Grade 4 average test score"

preserve 

collapse treat, by(academycode)

egen P_t = mean(treat)
gen P_c = 1- P_t

keep academycode P_t P_c

tempfile prop
save `prop'

restore

merge m:1 academycode using `prop', gen(_mprop)  // contains the probability of treatment for each observation



*** calculate expected grade level

gen level_c  = grade 
gen level_t = grade


replace level_t = (grade + 1) if grade == 1 & purple == 1
replace level_t = (grade - 1) if grade == 2 & purple == 0

gen exp_level = (P_t*level_t) + (P_c*level_c)
lab var exp_level "E[Level]"

gen realised_level = level_t
replace realised_level = level_c if treat == 0
lab var realised_level "Level"


*** calculate expected class size 

bys academycode purple grade_stream: egen N_t = count(studyid) if inlist(data_avl,2,3)
bys academycode grade grade_stream: egen N_c = count(studyid) if inlist(data_avl,2,3)

gen exp_classsize = (P_t*N_t) + (P_c*N_c)
lab var exp_classsize "E[Class size]"

gen classsize = N_t 
replace classsize = N_c if treat == 0
lab var classsize "Class size"


** predicted endline scores
gen grade_dum = grade == 1
gen score_bl_gr = comp_score_bl*grade_dum
reg comp_score_el comp_score_bl score_bl_gr grade_dum if treat == 0

predict endline_hat, xb

summ endline_hat if treat == 0
gen std_endline_hat = (endline_hat - `r(mean)')/`r(sd)'
lab var std_endline_hat "Individual predicted score"


* calculate expected peer achievement 

bys academycode purple grade_stream: egen total_t = total(std_endline_hat)
bys academycode purple grade_stream: egen count_t = count(std_endline_hat)

gen meanpeerscore_t= (total_t - std_endline_hat)/(count_t - 1)

bys academycode grade grade_stream: egen total_c = total(std_endline_hat)
bys academycode grade grade_stream: egen count_c = count(std_endline_hat)

gen meanpeerscore_ch= (total_c - std_endline_hat)/(count_c - 1)

gen exp_meanpeerscore = (P_t*meanpeerscore_t) + (P_c*meanpeerscore_c)
lab var exp_meanpeerscore "E[Peer predicted score]"

gen meanpeerscore = meanpeerscore_t
replace meanpeerscore = meanpeerscore_c if treat == 0
lab var meanpeerscore "Peer predicted score"



gen ind_hatXpeer_hat = std_endline_hat*meanpeerscore
lab var ind_hatXpeer_hat "Peer predicted score $\times$ Individual predicted score"

gen levelXind_hat = realised_level*std_endline_hat
lab var levelXind_hat "Level $\times$ Individual predicted score"

gen classizeXind_hat = classsize*std_endline_hat
lab var classizeXind_hat "Class size $\times$ Individual predicted score"



*loc full "yr_operation blscore blscore_1 blscore_2 blscore_3 blscore_4" 
loc full "blscore blscore_1 blscore_2 blscore_3 blscore_4" 


		forvalues s = 1/3 {
		
			if `s'== 1 {
				loc indep "meanpeerscore"
				loc exp "exp_meanpeerscore"
			}


		    if `s' == 2 {
				loc indep "realised_level"
				loc exp "exp_level"
			} 

		    if `s' == 3{
				loc indep "classsize"
				loc exp "exp_classsize"
			}	



		foreach i in `full' {

			cap reghdfe `i' `indep' `exp'  i.grade, a(academy_cohort) vce(clus academycode)

			if _rc  {

				local b`i'`s'k " "
				local N`i'`s'k " "
				local s`i'`s'k " "
			}

			else {

					local t=abs(_b[`indep']/_se[`indep'])
					local star ""			
					if `t'>=2.33{
						local star="***"
					}
					else if `t'>=1.96{
						local star="**"
					}
					else if `t'>=1.64{
						local star="*"
					}
					else {
						local star=""
					}
									
					local b`i'`s'k : display string(_b[`indep'],"%9.3f")
					local b`i'`s'k "`b`i'`s'k'`star'"
					local s`i'`s'k : display string(_se[`indep'],"%9.3f")
					local s`i'`s'k "(`s`i'`s'k')"


				}


			}	


		*areg `indep' yr_operation blscore , vce(clus academycode) a(academy_cohort)
		areg `indep' blscore , vce(clus academycode) a(academy_cohort)

		test blscore
		*test yr_operation blscore


		local F`s'1 : display string(r(F),"%9.3f")	
		local p`s'1 : display string(r(p),"%9.3f")

		}


foreach i in `full'{
	forval s = 1/3 {
		loc b`i'k  "`b`i'k' & `b`i'`s'k'"
		loc s`i'k  "`s`i'k' & `s`i'`s'k'"
	}

di "xxx `b`i'k' || `s`i'k' "

}	



* ===================================================================== *
* -----------------     	       Liberia            ----------------- *
* ===================================================================== *


use "${datadir}/Liberia/5_L_AG_full_wide.dta", clear 

gen yr_operation = (assess_date_el - academy_cohort)/365
lab var yr_operation "Academy years of operation"

gen g1 = grade == 1 
gen g2 = grade == 2
gen g3 = grade == 3
gen g4 = grade == 4 
gen g0 = inlist(grade,1,2,3,4)

lab var g0 "Full sample"
lab var g1 "Grade 1"
lab var g2 "Grade 2"
lab var g3 "Grade 3"
lab var g4 "Grade 4"

gen blscore = std_score_bl
lab var blscore "Baseline test score"

gen blscore_1 = blscore if grade == 1
gen blscore_2 = blscore if grade == 2
gen blscore_3 = blscore if grade == 3
gen blscore_4 = blscore if grade == 4

lab var blscore_1 "Grade 1 average test score"
lab var blscore_2 "Grade 2 average test score"
lab var blscore_3 "Grade 3 average test score"
lab var blscore_4 "Grade 4 average test score"


gen acad_year = 1 if academy_cohort < td(22nov2016)
replace acad_year = 2 if academy_cohort > td(22nov2016)

gen g12 = inlist(grade, 1, 2)
lab var g12 "Grades 1 and 2"
egen ggroup = group(g12 academycode)

gen std_grp = 1
replace std_grp = 2 if studygroup12 == 1 & studygroup34 == .
replace std_grp = 3 if studygroup12 == . & studygroup34 == 0
replace std_grp = 4 if studygroup12 == . & studygroup34 == 1

lab def std_grp 1 "yellow" 2 "orange" 3 "blue" 4 "purple"

lab val std_grp std_grp



preserve 

collapse treat, by(academycode acad_year g12)

bys acad_year g12: egen P_t = mean(treat)
gen P_c = 1- P_t

keep g12 academycode P_t P_c

tempfile prop
save `prop'

restore

merge m:1 g12 academycode using `prop', gen(_mprop)   // contains the probability of treatment for each observation


*** calculate expected grade level

gen level_c  = grade 
gen level_t = grade

replace level_t = (grade + 1) if inlist(grade,1,3) & inlist(std_grp,2,4)
replace level_t = (grade - 1) if inlist(grade,2,4) & inlist(std_grp,1,3)

gen exp_level = (P_t*level_t) + (P_c*level_c)

gen realised_level = level_t
replace realised_level = level_c if treat == 0

lab var exp_level "E[Level]"
lab var realised_level "Level"


*** calculate expected class size 

bys academycode std_grp stream: egen N_t = count(studyid)  if inlist(data_avl, 1,4,6,7)
bys academycode grade stream: egen N_c = count(studyid)  if inlist(data_avl, 1,4,6,7) 

gen exp_classsize = (P_t*N_t) + (P_c*N_c)
lab var exp_classsize "E[Class size]"

gen classsize = N_t 
replace classsize = N_c if treat == 0
lab var classsize "Class size"


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


summ endline_hat if treat == 0
gen std_endline_hat = (endline_hat - `r(mean)')/`r(sd)'
lab var std_endline_hat "Individual predicted score"


* calculate expected peer achievement 

bys academycode std_grp stream: egen total_t = total(std_endline_hat)
bys academycode std_grp stream: egen count_t = count(std_endline_hat)

gen meanpeerscore_t= (total_t - std_endline_hat)/(count_t - 1)

bys academycode grade stream: egen total_c = total(std_endline_hat)
bys academycode grade stream: egen count_c = count(std_endline_hat)

gen meanpeerscore_ch= (total_c - std_endline_hat)/(count_c - 1)

gen exp_meanpeerscore = (P_t*meanpeerscore_t) + (P_c*meanpeerscore_c)
lab var exp_meanpeerscore "E[Peer predicted score]"

gen meanpeerscore = meanpeerscore_t
replace meanpeerscore = meanpeerscore_c if treat == 0
lab var meanpeerscore "Peer predicted score"



gen ind_hatXpeer_hat = std_endline_hat*meanpeerscore
lab var ind_hatXpeer_hat "Peer predicted score $\times$ Individual predicted score"

gen levelXind_hat = realised_level*std_endline_hat
lab var levelXind_hat "Level $\times$ Individual predicted score"

gen classizeXind_hat = classsize*std_endline_hat
lab var classizeXind_hat "Class size $\times$ Individual predicted score"



*loc full "yr_operation blscore blscore_1 blscore_2 blscore_3 blscore_4" 
loc full "blscore blscore_1 blscore_2 blscore_3 blscore_4" 


		forvalues s = 1/3 {
		
			if `s'== 1 {
				loc indep "meanpeerscore"
				loc exp "exp_meanpeerscore"
			}


		    if `s' == 2 {
				loc indep "realised_level"
				loc exp "exp_level"
			} 

		    if `s' == 3{
				loc indep "classsize"
				loc exp "exp_classsize"
			}	



		foreach i in `full' {

			cap noisily reghdfe `i' `indep' `exp'  i.grade, a(academy_cohort) vce(clus ggroup)

			if _rc  {

				local b`i'`s'l " "
				local N`i'`s'l " "
				local s`i'`s'l " "
			}

			else {

					local t=abs(_b[`indep']/_se[`indep'])
					local star ""			
					if `t'>=2.33{
						local star="***"
					}
					else if `t'>=1.96{
						local star="**"
					}
					else if `t'>=1.64{
						local star="*"
					}
					else {
						local star=""
					}
									
					local b`i'`s'l : display string(_b[`indep'],"%9.3f")
					local b`i'`s'l "`b`i'`s'l'`star'"
					local s`i'`s'l : display string(_se[`indep'],"%9.3f")
					local s`i'`s'l "(`s`i'`s'l')"


				}


			}	

		*areg `indep' yr_operation blscore , vce(clus ggroup) a(academy_cohort)
		areg `indep' blscore , vce(clus ggroup) a(academy_cohort)

		test blscore
		*test yr_operation blscore

		local F`s'2 : display string(r(F),"%9.3f")	
		local p`s'2 : display string(r(p),"%9.3f")

		}


foreach i in `full'{
	forval s = 1/3 {
		loc b`i'l  "`b`i'l' & `b`i'`s'l'"
		loc s`i'l  "`s`i'l' & `s`i'`s'l'"

		di " `b`i'l' "
	}

}	




* ===================================================================== *
* -----------------     	      Latex code          ----------------- *
* ===================================================================== *



foreach i in `full' {

loc w`i' "`b`i'k'&`b`i'l'"
loc s`i' "`s`i'k'&`s`i'l'"

di "`w`i''"
di "`s`i''"
	
} 


loc P "&`p11'&`p21'&`p31'&&`p12'&`p22'&`p32'"



tokenize "Kenya Liberia"

local c = -2
forval g = 1/2{
		local c1 = `c'+3
		local c2 = `c'+4
		local c3 = `c'+5
		local glab "Experiment `g' (``g'')"
		local H "`H'&&\multicolumn{3}{c}{`glab'}"
		local S "`S'&&\Longstack{Predicted\#peer score}&\Longstack{Level}&\Longstack{Class size}"
		local C "`C'&&(`c1')&(`c2')&(`c3')"
		*local P "`P'&&&&{`p`g''}"
		*local F "`F'&&&&{`F`g''}"
		di "`P' | `F'"
		local c = `c'+3
}

/*
foreach l in H S C P F {
	local l = substr("`l'",2,.)	
}
*/


local size "scriptsize"
	
	
file open let using "${outdir}/structural_balance.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Bivariate structural balance on observables} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c @{}} \toprule \toprule" _n
	file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9}" _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n


	file write let "\\" _n

		foreach i in `full' {
			local xlab : variable label `i'
			file write let "&`xlab' `w`i'' \\" _n
			file write let "& 		 `s`i'' \\" _n
		}

	*file write let "\midrule" _n
	*file write let "\multicolumn{2}{l}{Observations} `Nearly_enrollment' \\" _n	
	*file write let "\multicolumn{2}{l}{F-stat of joint test} `F' \\" _n		
	*file write let "\multicolumn{2}{l}{P-value of joint test} `P' \\" _n	



	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications are at the academy-grade level and use controls for academy cohort dummies and grade dummies. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%."
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let






























