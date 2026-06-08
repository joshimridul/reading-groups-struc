

/*==========================================================================

Title: 10d_structural_testscores_sep.do 
Author: Mridul Joshi
Date: Mon Mar 14 17:56:45 2022

Description: Separately estimating the effects for grades 1 & 2 and grades 3 & 4 in Liberia

===========================================================================*/



/*==========================================================================

Title: 9_structural_pooled.do 
Author: Mridul Joshi
Date: Sun Dec 12 18:44:03 2021

Description: Endline score structural estimates 

===========================================================================*/
 



* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/6_K_AG_full_stacked_prepared", clear 



loc full "dev_mean_bl dispXbl realised_level levelXbl logclasssize logclassizeXbl" 


		forvalues s = 1/8 {
		
			if `s'== 1 {
				loc indep "dev_mean_bl"
				loc exp "exp_devmean_bl"
			}
			if `s' == 2 {
				loc indep "dev_mean_bl dispXbl"
				loc exp "exp_devmean_bl"
			} 
		    if `s' == 3 {
				loc indep "realised_level"
				loc exp "exp_level"
			} 
		    if `s' == 4 {
				loc indep "realised_level levelXbl"
				loc exp "exp_level"
			} 
		    if `s' == 5 {
				loc indep "logclasssize"
				loc exp "exp_logclasssize"
			} 
		    if `s' == 6 {
				loc indep "logclasssize logclassizeXbl"
				loc exp "exp_logclasssize"
			} 
		    if `s' == 7 {
				loc indep "dev_mean_bl realised_level logclasssize"
				loc exp "exp_devmean_bl exp_level exp_logclasssize"
			} 
		    if `s' == 8 {
				loc indep "dev_mean_bl realised_level logclasssize dispXbl levelXbl logclassizeXbl"
				loc exp "exp_devmean_bl exp_level exp_logclasssize"
			}	

			reghdfe std_score_el `indep' `exp' std_score_bl i.grade test_type, a(academy_cohort) vce(clus academycode)
			*reghdfe std_score_el `indep' `exp' std_endline_hat i.grade test_type, a(academycode) vce(clus academycode)


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
	forval s = 1/8 {
		loc b`i'k  "`b`i'k' & `b`i'`s''"
		loc s`i'k  "`s`i'k' & `s`i'`s''"
	}

}	



* ===================================================================== *
* -----------------     	  Liberia (1-2)           ----------------- *
* ===================================================================== *	


use "${datadir}/Liberia/6_L_AG_full_stacked_prepared.dta", clear 

keep if sample == 1   // observations in the sample 

keep if g12 == 1 

loc full "dev_mean_bl dispXbl realised_level levelXbl logclasssize logclassizeXbl" 


		forvalues s = 1/8 {
		
			if `s'== 1 {
				loc indep "dev_mean_bl"
				loc exp "exp_devmean_bl"
			}
			if `s' == 2 {
				loc indep "dev_mean_bl dispXbl"
				loc exp "exp_devmean_bl"
			} 
		    if `s' == 3 {
				loc indep "realised_level"
				loc exp "exp_level"
			} 
		    if `s' == 4 {
				loc indep "realised_level levelXbl"
				loc exp "exp_level"
			} 
		    if `s' == 5 {
				loc indep "logclasssize"
				loc exp "exp_logclasssize"
			} 
		    if `s' == 6 {
				loc indep "logclasssize logclassizeXbl"
				loc exp "exp_logclasssize"
			} 
		    if `s' == 7 {
				loc indep "dev_mean_bl realised_level logclasssize"
				loc exp "exp_devmean_bl exp_level exp_logclasssize"
			} 
		    if `s' == 8 {
				loc indep "dev_mean_bl realised_level logclasssize dispXbl levelXbl logclassizeXbl"
				loc exp "exp_devmean_bl exp_level exp_logclasssize"
			}	

			reghdfe std_score_el `indep' `exp' std_score_bl i.grade, a(academy_cohort) vce(clus ggroup)
			*reghdfe std_score_el `indep' `exp' std_endline_hat i.grade, a(academycode) vce(clus ggroup)


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
			loc ntestl1 "`ntestl1' & `ntest`s''"

			loc N`s' = e(N)
			loc Nl1 "`Nl1' & `N`s''"

			unique academycode
			loc Nc`s' = `r(unique)'
			loc Ncl1 "`Ncl1' & `Nc`s''"

			}


foreach i in `full'{
	forval s = 1/8 {
		loc b`i'l1  "`b`i'l1' & `b`i'`s''"
		loc s`i'l1  "`s`i'l1' & `s`i'`s''"
	}

}


* ===================================================================== *
* -----------------     	  Liberia  3-4               ----------------- *
* ===================================================================== *	


use "${datadir}/Liberia/6_L_AG_full_stacked_prepared.dta", clear 

keep if sample == 1   // observations in the sample 

keep if g12 == 0 


loc full "dev_mean_bl dispXbl realised_level levelXbl logclasssize logclassizeXbl" 


		forvalues s = 1/8 {
		
			if `s'== 1 {
				loc indep "dev_mean_bl"
				loc exp "exp_devmean_bl"
			}
			if `s' == 2 {
				loc indep "dev_mean_bl dispXbl"
				loc exp "exp_devmean_bl"
			} 
		    if `s' == 3 {
				loc indep "realised_level"
				loc exp "exp_level"
			} 
		    if `s' == 4 {
				loc indep "realised_level levelXbl"
				loc exp "exp_level"
			} 
		    if `s' == 5 {
				loc indep "logclasssize"
				loc exp "exp_logclasssize"
			} 
		    if `s' == 6 {
				loc indep "logclasssize logclassizeXbl"
				loc exp "exp_logclasssize"
			} 
		    if `s' == 7 {
				loc indep "dev_mean_bl realised_level logclasssize"
				loc exp "exp_devmean_bl exp_level exp_logclasssize"
			} 
		    if `s' == 8 {
				loc indep "dev_mean_bl realised_level logclasssize dispXbl levelXbl logclassizeXbl"
				loc exp "exp_devmean_bl exp_level exp_logclasssize"
			}	

			reghdfe std_score_el `indep' `exp' std_score_bl i.grade, a(academy_cohort) vce(clus ggroup)
			*reghdfe std_score_el `indep' `exp' std_endline_hat i.grade, a(academycode) vce(clus ggroup)



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
			loc ntestl2 "`ntestl2' & `ntest`s''"

			loc N`s' = e(N)
			loc Nl2 "`Nl2' & `N`s''"

			unique academycode
			loc Nc`s' = `r(unique)'
			loc Ncl2 "`Ncl2' & `Nc`s''"

			}


foreach i in `full'{
	forval s = 1/8 {
		loc b`i'l2  "`b`i'l2' & `b`i'`s''"
		loc s`i'l2  "`s`i'l2' & `s`i'`s''"
	}

}	



* ===================================================================== *
* -----------------     	   Latex code             ----------------- *
* ===================================================================== *

local c = -2
forval g = 1/8{
		local c1 = `c'+3
		local c2 = `c'+4
		local c3 = `c'+5
		*local glab "Experiment `g' (``g'')"
		local H "`H'&&\multicolumn{3}{c}{`glab'}"
		local S "`S'&\Longstack{Coef.}"
		local C "`C'&(`c1')"
		local c = `c'+1
}




local size "scriptsize"
	
	
file open let using "${outdir}/structural_testscores_disp_sep_logbl.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on test scores (by grade groups; dispersion; log classize)} " _n
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

	file write let "\multicolumn{3}{l}{\textbf{\textit{Panel B: Experiment 2a (Liberia, grades 1-2)}}} \\" _n

	file write let "\\" _n

		foreach i in `full' {
			local glab : variable label `i'
			file write let "`glab' & `b`i'l1' \\" _n
			file write let " 		 & `s`i'l1' \\" _n

		}


	file write let "\midrule" _n

	file write let "Number of test scores & `ntestl1' \\" _n	
	file write let "Number of students & `Nl1' \\" _n
	file write let "Number of schools & `Ncl1' \\" _n


	file write let " \midrule" _n

	file write let "\\" _n

	file write let "\multicolumn{3}{l}{\textbf{\textit{Panel C: Experiment 2b (Liberia, grades 3-4)}}} \\" _n

	file write let "\\" _n

		foreach i in `full' {
			local glab : variable label `i'
			file write let "`glab' & `b`i'l2' \\" _n
			file write let " 		 & `s`i'l2' \\" _n

		}


	file write let "\midrule" _n

	file write let "Number of test scores & `ntestl2' \\" _n	
	file write let "Number of students & `Nl2' \\" _n
	file write let "Number of schools & `Ncl2' \\" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications control for baseline test score, academy cohort dummies and grade dummies. Each specification also controls for the expected value of the respective independent variable used in the specification viz. dispersion, level and log class size. Standard errors are clustered at the academy level. In the final period control group, one standard deviation is roughly equivalent to an 18\% increase in test scores in Kenya and 23\% in Liberia. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let




