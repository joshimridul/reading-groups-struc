
/*==========================================================================

Title: 8_effect_dispersion.do 
Author: Mridul Joshi
Date: Sun Dec 12 17:12:49 2021

Description: Effect on within-class dispersion in test scors 

===========================================================================*/


* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/6_K_AG_full_stacked_prepared", clear 



loc xlist "dev_mean_bl dev_mean_ehat dev_mean_el"

forval g = 0/2 {

	foreach x in `xlist' {
			
			summ `x' if treat == 0 & g`g' == 1

				local mw`g'`x'k0 : display string(r(mean),"%9.3f")
				local Nmw`g'`x'k0 : display string(r(N),"%9.0fc")


			loc star = ""

			if "`x'" == "dev_mean_bl" {
				reghdfe `x' treat i.grade if g`g' == 1, a(constituency) vce(clus academycode)
			}

			else {
				reghdfe `x' treat std_score_bl i.grade if g`g' == 1, a(constituency) vce(clus academycode)
			}


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
* -----------------     	      Liberia             ----------------- *
* ===================================================================== *

use "${datadir}/Liberia/6_L_AG_full_stacked_prepared.dta", clear 


loc xlist "dev_mean_bl dev_mean_ehat dev_mean_el"

forval g = 0/4 {

	foreach x in `xlist' {
			
			summ `x' if treat == 0 & g`g' == 1

			local mw`g'`x'l0 : display string(r(mean),"%9.3f")
			local Nmw`g'`x'l0 : display string(r(N),"%9.0fc")
	

			loc star = ""


			if "`x'" == "dev_mean_bl" {
				reghdfe `x' treat i.grade if g`g' == 1, a(strata) vce(clus ggroup)
			}

			else {
				reghdfe `x' treat i.grade std_score_bl if g`g' == 1, a(strata) vce(clus ggroup)
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
forval g = 1/3{
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
	
	
file open let using "${outdir}/dispersion_effects.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effect on within-class dispersion in test scores} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c c c c c c c c  @{}} \toprule \toprule" _n
	file write let "&& \multicolumn{3}{c}{Baseline scores} && \multicolumn{3}{c}{Predicted outcomes} && \multicolumn{3}{c}{Actual outcomes}" _n
	file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9} \cmidrule{11-13}" _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n


	file write let "\\" _n

	file write let "\multicolumn{9}{l}{\textbf{\textit{Panel A: Kenya}}} \\" _n

	file write let "\\" _n

		forval g = 0/2 {
			local glab : variable label g`g'
			file write let "&`glab' &`ww`g'k' \\" _n
			file write let "& 		 &`sw`g'k' \\" _n

		}



	file write let "\\" _n

	file write let "\multicolumn{9}{l}{\textbf{\textit{Panel B: Liberia}}} \\" _n

	file write let "\\" _n

		forval g = 0/4 {
			local glab : variable label g`g'
			file write let "&`glab' &`ww`g'l' \\" _n
			file write let "& 		 &`sw`g'l' \\" _n

		}


	file write let "\midrule" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: The outcome is the absolute deviation of each student's standardised test score from the classroom mean. All specifications use controls for academy cohort dummies and grade dummies (where applicable). All specifications apart from the one with absolute deviation in baseline test scores control for the baseline test score. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%.   " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let






















