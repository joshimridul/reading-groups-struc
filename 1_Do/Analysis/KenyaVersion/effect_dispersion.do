
/*==========================================================================

Title: effect_dispersion.do 
Author: Mridul Joshi
Date: Thu Dec 14 12:51:05 2023

Description: Effect on dispersion 

===========================================================================*/


use "${datadir}/Kenya/6_K_AG_full_wide_prepared_2.dta", clear 

keep if finsamp

loc xlist "dev_mean_bl2 dev_mean_el2"

forval g = 0/2 {

	foreach x in `xlist' {
			
			summ `x' if treat == 0 & gg`g' == 1

				local mw`g'`x'k0 : display string(r(mean),"%9.3f")
				local Nmw`g'`x'k0 : display string(r(N),"%9.0fc")


			loc star = ""

			reg `x' treat std2_compscore_bl P_t if gg`g' == 1, vce(clus academycode)
	

				local bw`g'`x'k : display string(_b[treat],"%9.3f")

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
			

			local  bw`g'`x'k "`bw`g'`x'k'`star'"	

			local sw`g'`x'k : display string(_se[treat],"%9.3fc")		
			local pw`g'`x'k = 2*(1-normal(`t'))
			local pw`g'`x'k : display string(`pw`g'`x'k',"%9.3f")	
			local Nw`g'`x'k : display string(e(N),"%9.0fc")
			local sw`g'`x'k "(`sw`g'`x'k')"


	}


	foreach x in `xlist' {
		loc ww`g'k "`ww`g'k'&& `mw`g'`x'k0'&`bw`g'`x'k'&`Nw`g'`x'k'"
		loc sw`g'k "`sw`g'k'&&& `sw`g'`x'k'&"
	}	

	local ww`g'k = substr("`ww`g'k'",3,.)
    local sw`g'k = substr("`sw`g'k'",3,.)
}




* ===================================================================== *
* -----------------     	     Latex code           ----------------- *
* ===================================================================== *



local c = -2
forval g = 1/2{
		local c1 = `c'+3
		local c2 = `c'+4
		local c3 = `c'+5
		*local glab "Experiment `g' (``g'')"
		local H "`H'&&\multicolumn{3}{c}{`glab'}"
		local S "`S'&&\Longstack{Control\#mean}&\Longstack{Coef.}&\Longstack{N}"
		local C "`C'&&(`c1')&(`c2')&(`c3')"
		local c = `c'+3
}




local size "small"
	
	
file open let using "${outdir}/Kenya_new/eff_disp_K.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on within-class dispersion in student achievement} " _n
	file write let "\label{tab:dispfx} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c c c c @{}} \toprule \toprule" _n
	file write let "&& \multicolumn{3}{c}{Baseline scores} && \multicolumn{3}{c}{Actual outcomes} " _n
	file write let " \\  \cmidrule{3-5} \cmidrule{7-9} " _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n


	*file write let "\multicolumn{9}{l}{\textbf{\textit{Panel A: Kenya}}} \\" _n

	file write let "\\" _n

		forval g = 0/2 {
			local glab : variable label gg`g'
			file write let "&`glab' &`ww`g'k' \\" _n
			file write let "& 		 &`sw`g'k' \\" _n

		}


	file write let "\midrule" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: The outcome is the absolute deviation of each student's standardised test score from the classroom mean. All specifications use control for pretest score and a linear control for the probability of the schools’ assignment to the tracking in all specifications. Standard errors are clustered at the academy level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%.   " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let








