
/*==========================================================================

Title: 9_structural_pooled.do 
Author: Mridul Joshi
Date: Sun Dec 12 18:44:03 2021

Description: Endline score structural estimates (bl)

===========================================================================*/




* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/6_K_AG_full_wide_prepared", clear 

keep if finsamp 

loc full "meanpeerscore sdpeerscore dev_med_ehat classsize" 


		forvalues s = 1/7 {
		
			if `s'== 1 {
				loc indep "meanpeerscore_bl"
				loc exp "exp_meanpeerscore_bl"
			}
			
			if `s'== 2 {
				loc indep "sdpeerscore_bl"
				loc exp "exp_sdpeerscore_bl"
			}

		    if `s' == 3 {
				loc indep "dev_med_bl"
				loc exp "exp_devmed_bl"
			} 

		    if `s' == 4 {
				loc indep "classsize"
				loc exp "exp_classsize"
			} 

		    if `s' == 5 {
				loc indep "meanpeerscore_bl dev_med_bl classsize"
				loc exp "exp_meanpeerscore_bl exp_devmed_bl exp_classsize"
			} 

			if `s' == 6 {
				loc indep "sdpeerscore_bl dev_med_bl classsize"
				loc exp "exp_sdpeerscore_bl exp_devmed_bl exp_classsize"
			}


			if `s' == 7 {
				loc indep "meanpeerscore_bl sdpeerscore_bl dev_med_bl classsize"
				loc exp "exp_meanpeerscore_bl exp_sdpeerscore_bl exp_devmed_bl exp_classsize"
			}

			*reghdfe std_comp_score_el `indep' `exp' std_endline_hat i.grade, a(constituency) vce(clus academycode)
			reghdfe dev_mean_el `indep' `exp' std_comp_score_bl i.grade, a(constituency) vce(clus academycode)



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
					
					
					/*				
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
					*/

					local b`i'`s' : display string(_b[`i'],"%9.3f")
					local b`i'`s' "`b`i'`s''`star'"
					local s`i'`s' : display string(_se[`i'],"%9.3f")
					local s`i'`s' "(`s`i'`s'')"


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
	forval s = 1/7 {
		loc b`i'k  "`b`i'k' & `b`i'`s''"
		loc s`i'k  "`s`i'k' & `s`i'`s''"
	}

}	




* ===================================================================== *
* -----------------     	  Liberia                 ----------------- *
* ===================================================================== *	

use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

*keep if finsamp== 1 


reg score_el c.score_bl##i.grade if treat == 0, a(strata)
predict score_el_hat

reg score_ml c.score_bl##i.grade if treat == 0, a(strata)
predict score_ml_hat

gen delta_bl_ml = sqrt((score_ml_hat- score_bl)^2)

gen delta_bl_el = sqrt((score_el_hat- score_bl)^2)

gen stability_index = (delta_bl_el + delta_bl_ml)/2


drop if classsize < 5 
*| classsize > 100
*drop if classsize > 100

*keep if classsize <= 65 & classsize > 4 
 
loc full "meanpeerscore sdpeerscore dev_med_ehat classsize" 


		forvalues s = 1/7 {
		
			if `s'== 1 {
				loc indep "meanpeerscore_bl"
				loc exp "exp_meanpeerscore_bl"
			}
			
			if `s'== 2 {
				loc indep "sdpeerscore_bl"
				loc exp "exp_sdpeerscore_bl"
			}

		    if `s' == 3 {
				loc indep "dev_med_bl"
				loc exp "exp_devmed_bl"
			} 

		    if `s' == 4 {
				loc indep "classsize"
				loc exp "exp_classsize"
			} 

		    if `s' == 5 {
				loc indep "meanpeerscore_bl dev_med_bl classsize"
				loc exp "exp_meanpeerscore_bl exp_devmed_bl exp_classsize"
			} 

			if `s' == 6 {
				loc indep "sdpeerscore_bl dev_med_bl classsize"
				loc exp "exp_sdpeerscore_bl exp_devmed_bl exp_classsize"
			}


			if `s' == 7 {
				loc indep "meanpeerscore_bl sdpeerscore_bl dev_med_bl classsize"
				loc exp "exp_meanpeerscore_bl exp_sdpeerscore_bl exp_devmed_bl exp_classsize"
			}

			reghdfe dev_mean_el `indep' `exp' std_score_bl i.grade , a(strata) vce(clus ggroup)

			*reghdfe std_score_el `indep' `exp' std_score_bl i.grade, a(strata) vce(clus ggroup)
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
									

					/*if inlist("`i'", "classsize","classizeXind_hat") {

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

					} */

					local b`i'`s' : display string(_b[`i'],"%9.3f")
					local b`i'`s' "`b`i'`s''`star'"
					local s`i'`s' : display string(_se[`i'],"%9.3f")
					local s`i'`s' "(`s`i'`s'')"


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
	forval s = 1/7 {
		loc b`i'l  "`b`i'l' & `b`i'`s''"
		loc s`i'l  "`s`i'l' & `s`i'`s''"
	}

}	


* ===================================================================== *
* -----------------     	   Latex code             ----------------- *
* ===================================================================== *




local c = -2
forval g = 1/7{
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
	
	
file open let using "${outdir}/eff_on_disp_bl.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on dispersion in test scores} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c  @{}} \toprule \toprule" _n
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
	file write let "\item Notes: All specifications control for individual baseline test score, grade dummies and randomization strata fixed effects. Each specification also controls for the expected value of the respective independent variable used in the specification. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let










