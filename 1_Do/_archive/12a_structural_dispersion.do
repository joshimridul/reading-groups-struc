
/*==========================================================================

Title: 9_structural_pooled.do 
Author: Mridul Joshi
Date: Sun Dec 12 18:44:03 2021

Description: Structural estimates of test score dispersion

===========================================================================*/



* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/6_K_AG_full_stacked.dta", clear 

*keep if inlist(data_avl,2,3)


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

preserve

keep if inlist(data_avl,2,3)

duplicates drop academycode studyid, force 

bys academycode purple grade_stream: egen N_t = count(studyid) if inlist(data_avl,2,3)
bys academycode grade grade_stream: egen N_c = count(studyid) if inlist(data_avl,2,3)

gen exp_classsize = (P_t*N_t) + (P_c*N_c)
lab var exp_classsize "E[Class size]"

gen classsize = N_t 
replace classsize = N_c if treat == 0
lab var classsize "Class size (\times 10)"

keep academycode studyid exp_classsize classsize

tempfile csize
save `csize'

restore 

merge m:1 academycode studyid using `csize', gen(_mcsize)


** predicted endline scores
gen grade_dum = grade == 1
gen score_bl_gr = score_bl*grade_dum
reg score_el score_bl score_bl_gr grade_dum if treat == 0

predict endline_hat, xb

summ endline_hat if treat == 0
gen std_endline_hat = (endline_hat - `r(mean)')/`r(sd)'
lab var std_endline_hat "Individual pred. score"


* calculate expected peer achievement 

bys academycode purple grade_stream: egen total_t = total(std_endline_hat)
bys academycode purple grade_stream: egen count_t = count(std_endline_hat)

gen meanpeerscore_t= (total_t - std_endline_hat)/(count_t - 1)

bys academycode grade grade_stream: egen total_c = total(std_endline_hat)
bys academycode grade grade_stream: egen count_c = count(std_endline_hat)

gen meanpeerscore_ch= (total_c - std_endline_hat)/(count_c - 1)

gen exp_meanpeerscore = (P_t*meanpeerscore_t) + (P_c*meanpeerscore_c)
lab var exp_meanpeerscore "E[Peer pred. score]"

gen meanpeerscore = meanpeerscore_t
replace meanpeerscore = meanpeerscore_c if treat == 0
lab var meanpeerscore "Peer pred. score"

* create other variables 
gen ind_hatXpeer_hat = std_endline_hat*meanpeerscore
lab var ind_hatXpeer_hat "Peer pred. score \times Ind. pred. score"

gen levelXind_hat = realised_level*std_endline_hat
lab var levelXind_hat "Level \times Ind. pred. score"

gen classizeXind_hat = classsize*std_endline_hat
lab var classizeXind_hat "Class size \times Ind. pred. score (\times 10)"

gen test_type = assess_competency_el == 1


** actual outcome 
bys academycode grade grade_stream: egen mean_el_c = mean(std_score_el)
bys academycode purple grade_stream: egen mean_el_t = mean(std_score_el)

gen mean_el = mean_el_c
replace mean_el = mean_el_t if treat == 1 

gen dev_mean_el = abs(std_score_el - mean_el)




loc full "meanpeerscore_bl realised_level classsize" 


		forvalues s = 1/4 {
		
			if `s'== 1 {
				loc indep "meanpeerscore"
				loc exp "exp_meanpeerscore"
			}

		    if `s' == 2 {
				loc indep "realised_level"
				loc exp "exp_level"
			} 

		    if `s' == 3 {
				loc indep "classsize"
				loc exp "exp_classsize"
			} 

		    if `s' == 4 {
				loc indep "meanpeerscore realised_level classsize"
				loc exp "exp_meanpeerscore exp_level exp_classsize"
			} 


			*reghdfe dev_mean_el `indep' `exp' std_endline_hat std_score_bl i.grade test_type, a(academy_cohort) vce(clus academycode)
			reghdfe dev_mean_el `indep' `exp' std_endline_hat i.grade test_type, a(academy_cohort) vce(clus academycode)


			foreach i in `full' {

				if regexm("`indep'", "`i'") {

					local t=abs(_b[`i']/_se[`i'])
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
									
					if inlist("`i'", "classsize","classizeXind_hat") {

						local b`i'`s' : display string(_b[`i']*10,"%9.3f")
					    local b`i'`s' "`b`i'`s''`star'"
					    local s`i'`s' : display string(_se[`i']*10,"%9.3f")
					    local s`i'`s' "(`s`i'`s'')"
					}

					else {

						local b`i'`s' : display string(_b[`i'],"%9.3f")
						local b`i'`s' "`b`i'`s''`star'"
						local s`i'`s' : display string(_se[`i'],"%9.3f")
						local s`i'`s' "(`s`i'`s'')"

					}


				}

				else {
					local b`i'`s' ""
					local s`i'`s' ""
				}

			}

			loc ntest`s' = 2
			loc ntestk "`ntestk' & `ntest`s''"

			loc N`s' = e(N)
			loc Nk "`Nk' & `N`s''"

			unique academycode
			loc Nc`s' = `r(unique)'
			loc Nck "`Nck' & `Nc`s''"

			}


foreach i in `full'{
	forval s = 1/4 {
		loc b`i'k  "`b`i'k' & `b`i'`s''"
		loc s`i'k  "`s`i'k' & `s`i'`s''"
	}

}	





* ===================================================================== *
* -----------------     	  Liberia                 ----------------- *
* ===================================================================== *	


use "${datadir}/Liberia/5_L_AG_full_wide.dta", clear 

*keep if inlist(data_avl, 1,6,7)

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


bys academycode std_grp stream: egen N_t = count(studyid) if inlist(data_avl, 1,4,6,7)
bys academycode grade stream: egen N_c = count(studyid) if inlist(data_avl, 1,4,6,7)

bys academycode std_grp stream: egen N_t1 = count(studyid) 
bys academycode grade stream: egen N_c1 = count(studyid) 


bys academycode std_grp stream: egen N_t_x = max(N_t)
bys academycode grade stream: egen N_c_x = max(N_c) 


*gen classsize = N_t_x
*replace classsize = N_c_x if treat == 0
*lab var classsize "Class size (\times 10)"



gen exp_classsize = (P_t*N_t_x) + (P_c*N_c_x)
lab var exp_classsize "E[Class size]"

gen classsize = N_t_x 
replace classsize = N_c_x if treat == 0
lab var classsize "Class size (\times 10)"




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
lab var classizeXind_hat "Class size $\times$ Individual predicted score (\times 10)"

** actual outcome 
bys academycode grade stream: egen mean_el_c = mean(std_score_el)
bys academycode std_grp stream: egen mean_el_t = mean(std_score_el)

gen mean_el = mean_el_c
replace mean_el = mean_el_t if treat == 1 

gen dev_mean_el = abs(std_score_el - mean_el)



loc full "meanpeerscore realised_level classsize " 


		forvalues s = 1/4 {
			
			if `s'== 1 {
				loc indep "meanpeerscore"
				loc exp "exp_meanpeerscore"
			}

		    if `s' == 2 {
				loc indep "realised_level"
				loc exp "exp_level"
			} 

		    if `s' == 3 {
				loc indep "classsize"
				loc exp "exp_classsize"
			} 

		    if `s' == 4 {
				loc indep "meanpeerscore realised_level classsize"
				loc exp "exp_meanpeerscore exp_level exp_classsize"
			} 


			*reghdfe dev_mean_el `indep' `exp' std_score_bl std_endline_hat i.grade, a(academy_cohort) vce(clus ggroup)
			reghdfe dev_mean_el `indep' `exp' std_endline_hat i.grade, a(academy_cohort) vce(clus ggroup)


			foreach i in `full' {

				if regexm("`indep'", "`i'") {

					local t=abs(_b[`i']/_se[`i'])
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
									

					if inlist("`i'", "classsize","classizeXind_hat") {

						local b`i'`s' : display string(_b[`i']*10,"%9.3f")
					    local b`i'`s' "`b`i'`s''`star'"
					    local s`i'`s' : display string(_se[`i']*10,"%9.3f")
					    local s`i'`s' "(`s`i'`s'')"
					}

					else {

						local b`i'`s' : display string(_b[`i'],"%9.3f")
						local b`i'`s' "`b`i'`s''`star'"
						local s`i'`s' : display string(_se[`i'],"%9.3f")
						local s`i'`s' "(`s`i'`s'')"

					}


				}

				else {
					local b`i'`s' ""
					local s`i'`s' ""
				}


			}

			loc ntest`s' = 1
			loc ntestl "`ntestl' & `ntest`s''"

			loc N`s' = e(N)
			loc Nl "`Nl' & `N`s''"

			unique academycode
			loc Nc`s' = `r(unique)'
			loc Ncl "`Ncl' & `Nc`s''"

			}


foreach i in `full'{
	forval s = 1/4 {
		loc b`i'l  "`b`i'l' & `b`i'`s''"
		loc s`i'l  "`s`i'l' & `s`i'`s''"
	}

}	


* ===================================================================== *
* -----------------     	   Latex code             ----------------- *
* ===================================================================== *




local c = -2
forval g = 1/4{
		local c1 = `c'+3
		local c2 = `c'+4
		local c3 = `c'+5
		*local glab "Experiment `g' (``g'')"
		local H "`H'&&\multicolumn{3}{c}{`glab'}"
		local S "`S'&\Longstack{Coef.}"
		local C "`C'&(`c1')"
		local c = `c'+1
}




local size "small"
	
	
file open let using "${outdir}/structural_dispersion_testscores.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on within-class dispersion of test scores} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c c c c  @{}} \toprule \toprule" _n
	*file write let "&& \multicolumn{3}{c}{Baseline scores} && \multicolumn{3}{c}{Predicted outcomes} && \multicolumn{3}{c}{Actual outcomes}" _n
	*file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9} \cmidrule{11-13}" _n
	*file write let "`S'  \\" _n
	file write let "& `C' \\ \midrule " _n


	file write let "\\" _n

	file write let "\multicolumn{3}{l}{\textbf{\textit{Panel A: Experiment 1 (Kenya)}}} \\" _n

	file write let "\\" _n

		foreach i in `full' {
			local glab : variable label `i'
			file write let "`glab' & `b`i'k' \\" _n
			file write let " 		 & `s`i'k' \\" _n

		}

	file write let "\midrule" _n

	file write let "Number of test scores & `ntestk' \\" _n	
	file write let "Number of students & `Nk' \\" _n
	file write let "Number of schools & `Nck' \\" _n

	file write let " \midrule" _n

	file write let "\\" _n

	file write let "\multicolumn{3}{l}{\textbf{\textit{Panel B: Experiment 2 (Liberia)}}} \\" _n

	file write let "\\" _n

		foreach i in `full' {
			local glab : variable label `i'
			file write let "`glab' & `b`i'l' \\" _n
			file write let " 		 & `s`i'l' \\" _n

		}


	file write let "\midrule" _n

	file write let "Number of test scores & `ntestl' \\" _n	
	file write let "Number of students & `Nl' \\" _n
	file write let "Number of schools & `Ncl' \\" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: The outcome is the absolute deviation of each student's standardized test score from the classroom mean. All specifications control for baseline test score, indicator for the pooled test scores, individual predicted test score, academy cohort dummies and grade dummies. Each specification also controls for the expected value of the respective independent variable used in the specification viz. peer predicted score, level and class size. Standard errors are clustered at the academy-grade group level. In the pooled control, one standard deviation is roughly equivalent to an 20\% increase in test scores in Kenya and 24\% in Liberia. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let











 











