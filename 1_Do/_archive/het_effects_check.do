
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


gen dif_meanpeerscore_bl = meanpeerscore_t_bl - meanpeerscore_c_bl 
gen trXdif_meanpeerscore_bl = treat*dif_meanpeerscore_bl 

gen dif_level = level_t - level_c 
gen trXdif_level = treat*dif_level 

gen dif_class = csize_t - csize_c 
gen trXdif_class = treat*dif_class 

lab var trXdif_meanpeerscore_bl "Treat X $\Delta$ Peer Score"
lab var trXdif_level "Treat X $\Delta$ Level"
lab var trXdif_class "Treat X $\Delta$ Classsize" 


gen trXmeanpeerscore_t_bl = treat*meanpeerscore_t_bl
gen trXlevel_t = treat*level_t
gen trXclass_t = treat*csize_t

gen trXmeanpeerscore_c_bl = treat*meanpeerscore_c_bl
gen trXlevel_c = treat*level_c
gen trXclass_c = treat*csize_c

lab var trXmeanpeerscore_t_bl "Treat X D1 Peer Score"
lab var trXlevel_t "Treat X D1 Level"
lab var trXclass_t "Treat X D1 Classsize"



*loc full "trXdif_meanpeerscore_bl trXdif_level trXdif_class trXmeanpeerscore_t_bl trXlevel_t trXclass_t" 
loc full "trXdif_meanpeerscore_bl trXdif_level trXdif_class " 

		forvalues s = 1/4 {
		
			if `s'== 1 {
				loc indep "trXdif_meanpeerscore_bl"
				loc exp "dif_meanpeerscore_bl treat meanpeerscore_c_bl"
			}

			if `s' == 2 {
				loc indep "trXdif_level"
				loc exp "dif_level treat level_c"
			} 

		    if `s' == 3 {
				loc indep "trXdif_class"
				loc exp "dif_class treat csize_c"
			} 


		    if `s' == 4 {
				loc indep "trXdif_meanpeerscore_bl trXdif_level trXdif_class"
				loc exp "dif_meanpeerscore_bl dif_level dif_class treat meanpeerscore_c_bl level_c csize_c"
			} 			


			reghdfe std_score_el `indep' `exp' std_score_bl i.grade test_type, a(constituency) vce(clus academycode)


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

use "${datadir}/Liberia/6_L_AG_full_stacked_prepared.dta", clear 

keep if sample == 1 

gen dif_meanpeerscore_bl = meanpeerscore_t_bl - meanpeerscore_c_bl 
gen trXdif_meanpeerscore_bl = treat*dif_meanpeerscore_bl 

gen dif_level = level_t - level_c 
gen trXdif_level = treat*dif_level 

gen dif_class = csize_t - csize_c
gen trXdif_class = treat*dif_class 

lab var trXdif_meanpeerscore_bl "Treat X $\Delta$ Peer Score"
lab var trXdif_level "Treat X $\Delta$ Level"
lab var trXdif_class "Treat X $\Delta$ Classsize" 


gen trXmeanpeerscore_t_bl = treat*meanpeerscore_t_bl
gen trXlevel_t = treat*level_t
gen trXclass_t = treat*csize_t


gen trXmeanpeerscore_c_bl = treat*meanpeerscore_c_bl
gen trXlevel_c = treat*level_c
gen trXclass_c = treat*csize_c


lab var trXmeanpeerscore_t_bl "Treat X D1 Peer Score"
lab var trXlevel_t "Treat X D1 Level"
lab var trXclass_t "Treat X D1 Classsize"


loc full "trXdif_meanpeerscore_bl trXdif_level trXdif_class" 

		forvalues s = 1/4 {
		
			if `s'== 1 {
				loc indep "trXdif_meanpeerscore_bl"
				loc exp "dif_meanpeerscore_bl treat meanpeerscore_c_bl"
			}

			if `s' == 2 {
				loc indep "trXdif_level"
				loc exp "dif_level treat level_c"
			} 

		    if `s' == 3 {
				loc indep "trXdif_class"
				loc exp "dif_class treat csize_c"
			} 

		    if `s' == 4 {
				loc indep "trXdif_meanpeerscore_bl trXdif_level trXdif_class"
				loc exp "dif_meanpeerscore_bl dif_level dif_class treat meanpeerscore_c_bl level_c csize_c"
			} 			


			reghdfe std_score_el `indep' `exp' std_score_bl i.grade, a(strata) vce(clus ggroup)
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

di "`b`i'l' |||"

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




local size "scriptsize"
	
	
file open let using "${outdir}/heteffects.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on test scores} " _n
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
	file write let "\item Notes: All specifications control for baseline test score, a dummy for treatment, grade dummies, and randomization strata fixed effects. All specifications also control for $\Delta$ and D0. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let










