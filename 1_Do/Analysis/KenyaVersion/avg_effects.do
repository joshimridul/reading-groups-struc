
/*==========================================================================

Title: avg_effects.do 
Author: Mridul Joshi
Date: Tue Dec 12 19:20:23 2023

Description: Avg effects Kenya sample 

===========================================================================*/


use "${datadir}/Kenya/6_K_AG_full_wide_prepared_2.dta", clear 
*keep if finsamp

loc zlist "bl"

forval g = 0/2 {
			
			summ std_comp_score_el if treat == 0 & gg`g' == 1

			if `r(N)' == 0 {

				local ms`g'k0 " "
			    local Nms`g'k0 " "
			}

			else {

				local ms`g'k0 : display string(r(mean),"%9.3f")
				local Nms`g'k0 : display string(r(N),"%9.0fc")
			}	

			loc star = ""
			reg std_comp_score_el treat std_comp_score_bl i.grade P_t if gg`g' == 1, vce(clus academycode)


			if _rc {

				local bs`g'k " "
				local Ns`g'k " "
				local ss`g'k " "
			}

			else {

				local bs`g'k : display string(_b[treat],"%9.3f")

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
			

			local  bs`g'k "`bs`g'k'`star'"	

			local sw`g'k : display string(_se[treat],"%9.3fc")		
			local ps`g'k = 2*(1-normal(`t'))
			local ps`g'k : display string(`ps`g'k',"%9.3f")	
			local Ns`g'k : display string(e(N),"%9.0fc")
			local sw`g'k "(`sw`g'k')"
		}

}



forval g = 0/2 {

loc w`g' "`ms`g'k0'&`bs`g'k'&`Ns`g'k'"
loc s`g' " & `sw`g'k'"

di "`w`g''"
di "`s`g''"
	
} 



local S "&&\Longstack{Control\#mean}&\Longstack{Coef.}&\Longstack{N}"
local H "&&(1)&(2))&(3)"


local size "small"
	
	
file open let using "${outdir}/Kenya_new/avg_effect_K.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on student achievement} " _n
	file write let "\label{tab:avgfx} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c @{}} \toprule \toprule" _n
	file write let "`S' \\  " _n
	file write let "`H' \\ \midrule " _n

	file write let "\\" _n

		forval g = 0/2 {
			local glab : variable label gg`g'
			file write let "&`glab' &`w`g'' \\" _n
			file write let "& 		 &`s`g'' \\" _n

		}



	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications use control for pretest score and a linear control for the probability of the schools’ assignment to the tracking condition in all specifications. Standard errors are clustered at the academy level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let






