
/*==========================================================================

Title: balance.do 
Author: Mridul Joshi
Date: Tue Dec 12 14:24:23 2023

Description: Baseline balance Kenya sample

===========================================================================*/



* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *


use "${datadir}/Kenya/6_K_AG_full_wide_prepared_2", clear 

keep if finsamp


loc xlist std2_compscore_bl yr_operation rural share_female new_to_bridge old_student


foreach x in `xlist' {
			
			di "`x'"

			cap summ `x' if treat == 0

			if `r(N)' == 0 {

				local m`x'k0 " "
			    local Nm`x'k0 " "
			}

			else {

				local m`x'k0 : display string(r(mean),"%9.3f")
				local Nm`x'k0 : display string(r(N),"%9.0fc")
			}	

			loc star = ""
			reg `x' treat P_t, vce(clus academycode) 



			if _rc == 2000 {

				local b`x'k " "
				local N`x'k " "
				local s`x'k " "
			}

			else {

				local b`x'k : display string(_b[treat],"%9.3f")

				local t=abs(_b[treat]/_se[treat])
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
					if missing(`t') {
						local star=""
					}		
			

			local  b`x'k "`b`x'k'`star'"	

			local s`x'k : display string(_se[treat],"%9.3fc")		
			local p`x'k = 2*(1-normal(`t'))
			local p`x'k : display string(`p`x'k',"%9.3f")	
			local N`x'k : display string(e(N),"%9.0fc")
			local s`x'k "(`s`x'k')"
		}

}

reghdfe treat std2_compscore_bl yr_operation rural share_female new_to_bridge old_student, a(constituency) vce(clus academycode) 
*areg treat class_size blscore , a(constituency) vce(clus academycode) 

	test std2_compscore_bl yr_operation rural share_female new_to_bridge old_student 

	local F1 : display string(r(F),"%9.3f")	
	local p1 : display string(r(p),"%9.3f")


foreach x in `xlist' {

loc w`x' "`m`x'k0'&`b`x'k'&`N`x'k'"
loc s`x' " & `s`x'k'"

di "`w`x''"
di "`s`x''"
	
} 

local S "&&\Longstack{Control\#mean}&\Longstack{Coef.}&\Longstack{N}"
local H "&&(1)&(2))&(3)"

local size "small"
	
	
file open let using "${outdir}/Kenya_new/baseline_balance_K.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Baseline balance} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c @{}} \toprule \toprule" _n
	file write let "`S' \\" _n
	file write let "`H' \\ \midrule " _n


	file write let "\\" _n

		foreach x of local xlist {
			local xlab : variable label `x'
			file write let "&`xlab' &`w`x'' \\" _n
			file write let "& 		 &`s`x'' \\" _n

		}

	file write let "\midrule" _n
	*file write let "\multicolumn{2}{l}{Observations} `Nearly_enrollment' \\" _n	
	file write let "\multicolumn{2}{l}{F-stat of joint test} && `F1' \\" _n		
	file write let "\multicolumn{2}{l}{P-value} && `p1' \\" _n	


	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications control for randomization strata fixed effects. Standard errors are clustered at the academy level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let















