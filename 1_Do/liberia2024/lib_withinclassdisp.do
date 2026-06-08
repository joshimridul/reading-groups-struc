
/*==========================================================================

Title: lib_withinclassdisp.do 
Author: Mridul Joshi
Date: Sun Dec  8 21:55:34 2024

Description: Effect on within-class dispersion

===========================================================================*/



loc xlist "dev_mean_bl_eb dev_mean_el"

forval g = 0/2 {

	foreach x in `xlist' {
			
			summ `x' if treat == 0 & exp`g' == 1

			local mw`g'`x'l0 : display string(r(mean),"%9.3f")
			local Nmw`g'`x'l0 : display string(r(N),"%9.0fc")
	

			loc star = ""


			if "`x'" == "dev_mean_bl_eb" {
				reg `x' treat P_t if exp`g' == 1, vce(clus ggroup)
			}

			else {
				reg `x' treat P_t if exp`g' == 1, vce(clus ggroup)
			}


			local bw`g'`x'l : display string(_b[treat],"%9.3f")

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
			

			local  bw`g'`x'l "`bw`g'`x'l'`star'"	

			local sw`g'`x'l : display string(_se[treat],"%9.3fc")		
			local pw`g'`x'l = 2*(1-normal(`t'))
			local pw`g'`x'l : display string(`pw`g'`x'l',"%9.3f")	
			local Nw`g'`x'l : display string(e(N),"%9.0fc")
			local sw`g'`x'l "(`sw`g'`x'l')"
	}


	foreach x in `xlist' {
		loc ww`g'l "`ww`g'l'&& `mw`g'`x'l0'&`bw`g'`x'l'&`Nw`g'`x'l'"
		loc sw`g'l "`sw`g'l'&&& `sw`g'`x'l'&"
	}	


 di "`ww`g'l'|ddddddddd"

	local ww`g'l = substr("`ww`g'l'",3,.)
    local sw`g'l = substr("`sw`g'l'",3,.)

 di "`ww`g'l'|xxxxxxxxx"

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




local size "scriptsize"
	
	
file open let using "${outdir}/dispersion_effects_lib.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on within-class dispersion in test scores} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c c @{}} \toprule \toprule" _n
	file write let "&& \multicolumn{3}{c}{Predicted ability} &&  \multicolumn{3}{c}{Actual outcomes}" _n
	file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9} " _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n

	file write let "\\" _n

		forval g = 0/2 {
			local glab : variable label exp`g'
			file write let "&`glab' &`ww`g'l' \\" _n
			file write let "& 		 &`sw`g'l' \\" _n

		}


	file write let "\midrule" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: The outcome is the absolute deviation of each student's standardized test score from the classroom mean. All specifications control linearly for randomization strata fixed effects. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let








