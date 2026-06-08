
/*==========================================================================

Title: 9_structural_pooled.do 
Author: Mridul Joshi
Date: Sun Dec 12 18:44:03 2021

Description: Endline score structural estimates 

===========================================================================*/

keep if finsamp

loc full "meanpeerscore_bl_eb dev_med_bl_eb classsize" 


		forvalues s = 0/2 {
		
			loc indep "meanpeerscore_bl_eb dev_med_bl_eb classsize"
			loc exp "exp_meanpeerscore_bl_eb exp_devmed_bl_eb exp_classsize"


			*reghdfe std_score_el `indep' `exp' std_score_bl i.grade, a(strata) vce(clus ggroup)
			reg std_score_el `indep' `exp' predicted_ability P_t if exp`s',  vce(clus ggroup)
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

			loc ntest`s' = 1
			loc ntestl "`ntestl' & `ntest`s''"

			loc N`s' = e(N)
			loc Nl "`Nl' & `N`s''"

			unique academycode
			loc Nc`s' = `r(unique)'
			loc Ncl "`Ncl' & `Nc`s''"

			}


foreach i in `full'{
	forval s = 0/2 {
		loc b`i'l  "`b`i'l' & `b`i'`s''"
		loc s`i'l  "`s`i'l' & `s`i'`s''"
	}

}	


* ===================================================================== *
* -----------------     	   Latex code             ----------------- *
* ===================================================================== *




local c = -2
forval g = 0/2{
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
	
	
file open let using "${outdir}/distance_median_lib.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on test scores} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l  c c c  @{}} \toprule \toprule" _n
	*file write let "&& \multicolumn{3}{c}{Baseline scores} && \multicolumn{3}{c}{Predicted outcomes} && \multicolumn{3}{c}{Actual outcomes}" _n
	*file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9} \cmidrule{11-13}" _n
	*file write let "`S'  \\" _n
	file write let " & & Stacked & Grades 3-4  & Grades 1-2 \\" _n
	file write let "& `C' \\ \midrule " _n


	file write let "\\" _n


		foreach i in `full' {
			local glab : variable label `i'
			file write let "`glab' & `b`i'l' \\" _n
			file write let " 		 & `s`i'l' \\" _n

		}


	file write let "\midrule" _n

	*file write let "Number of test scores & `ntestl' \\" _n	
	file write let "Number of students & `Nl' \\" _n
	file write let "Number of schools & `Ncl' \\" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications control linearly for randomization strata fixed effects and predicted ability. Each specification also controls for the expected value of the respective independent variable used in the specification. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let

