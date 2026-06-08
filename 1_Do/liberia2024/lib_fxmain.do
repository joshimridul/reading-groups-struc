
/*==========================================================================

Title: lib_fxmain.do 
Author: Mridul Joshi
Date: Sun Dec  8 13:17:34 2024

Description: impact of program

===========================================================================*/


* ===================================================================== *
* -----------------     	     Liberia              ----------------- *
* ===================================================================== *

*use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

*keep if finsamp== 1 




forval g = 0/2 {

			sum std_score_el if treat == 0 & exp`g' == 1

			local mw`g'l0 : display string(r(mean),"%9.3f")
			local Nmw`g'l0 : display string(r(N),"%9.0fc")

			reg std_score_el treat std_pred_eb P_t if exp`g' == 1, vce(clus ggroup)

			local bw`g'l : display string(_b[treat],"%9.3f")

			di "`bw`g'l'"

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
			local bw`g'l "`bw`g'l'`star'"	
			local sw`g'l : display string(_se[treat],"%9.3fc")		
			local pw`g'l = 2*(1-normal(`t'))
			local pw`g'l : display string(`pw`g'l',"%9.3f")	
			local Nw`g'l : display string(e(N),"%9.0fc")
			local sw`g'l "(`sw`g'l')"

}




forval g = 0/2 {

loc w`g' "`mw`g'l0'&`bw`g'l'&`Nw`g'l'"
loc s`g' "&`sw`g'l'& "

di "`w`g''"
di "`s`g''"
	
} 


* ===================================================================== *
* -----------------     	     Latex code           ----------------- *
* ===================================================================== *


tokenize "Liberia"

local c = -2
forval g = 1/1{
		local c1 = `c'+3
		local c2 = `c'+4
		local c3 = `c'+5
		local glab "Experiment `g' (``g'')"
		local H "`H'&&\multicolumn{3}{c}{`glab'}"
		local S "`S'&&\Longstack{Control\#mean}&\Longstack{Coef.}&\Longstack{N}"
		local C "`C'&&(`c1')&(`c2')&(`c3')"
		local c = `c'+3
}




local size "small"
	
	
file open let using "${outdir}/test_score_effects_lib24.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effects on test scores} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c @{}} \toprule \toprule" _n
	*file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9}" _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n


	file write let "\\" _n

		forval g = 0/2 {
			local glab : variable label exp`g'
			file write let "&`glab' &`w`g'' \\" _n
			file write let "& 		 &`s`g'' \\" _n

		}


	file write let "\midrule" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications control linearly for randomization strata fixed effects and predicted ability. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let


