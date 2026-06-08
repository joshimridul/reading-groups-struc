
/*==========================================================================

Title: 6_attrition.do 
Author: Mridul Joshi
Date: Sun Dec 12 13:34:40 2021

Description: Attrition table for Kenya and Liberia ability grouping analysis

===========================================================================*/



* ===================================================================== *
* -----------------     	  Kenya                   ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", clear 

gen has_anyscore = !mi(comp_score_el)

loc zlist "bl"

forval g = 0/2 {
			
			summ has_anyscore if treat == 0 & gg`g' == 1

			if `r(N)' == 0 {

				local ms`g'k0 " "
			    local Nms`g'k0 " "
			}

			else {

				local ms`g'k0 : display string(r(mean),"%9.3f")
				local Nms`g'k0 : display string(r(N),"%9.0fc")
			}	

			loc star = ""
			cap areg has_anyscore treat i.grade std_comp_score_bl if gg`g' == 1, a(constituency) vce(clus academycode) // bl and el


			if _rc == 2000 {

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

			local ss`g'k : display string(_se[treat],"%9.3fc")		
			local ps`g'k = 2*(1-normal(`t'))
			local ps`g'k : display string(`ps`g'k',"%9.3f")	
			local Ns`g'k : display string(e(N),"%9.0fc")
			local ss`g'k "(`ss`g'k')"
		}

}


* ===================================================================== *
* -----------------     	 Liberia                  ----------------- *
* ===================================================================== *

use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

gen has_el = !mi(score_el)


forval g = 0/2 {

			sum has_el if treat == 0 & gg`g' == 1

			local mw`g'l0 : display string(r(mean),"%9.3f")
			local Nmw`g'l0 : display string(r(N),"%9.0fc")

			areg has_el treat i.grade std_score_bl if gg`g'==1, vce(clus ggroup) a(strata) 
			local bw`g'l : display string(_b[treat],"%9.3f")

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

loc w`g' "`ms`g'k0'&`bs`g'k'&`Ns`g'k'&&`mw`g'l0'&`bw`g'l'&`Nw`g'l'"
loc s`g' " & `ss`g'k'&&&&`sw`g'l'& "

di "`w`g''"
di "`s`g''"
	
} 


* ===================================================================== *
* -----------------     	     Latex code           ----------------- *
* ===================================================================== *


tokenize "Kenya Liberia"

local c = -2
forval g = 1/2{
		local c1 = `c'+3
		local c2 = `c'+4
		local c3 = `c'+5
		local glab "Experiment `g' (``g'')"
		local H "`H'&&\multicolumn{3}{c}{`glab'}"
		local S "`S'&&\Longstack{Control\#mean}&\Longstack{Coef.}&\Longstack{N}"
		local C "`C'&&(`c1')&(`c2')&(`c3')"
		local c = `c'+3
}




local size "scriptsize"
	
	
file open let using "${outdir}/attrition.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Test score follow-up} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c @{}} \toprule \toprule" _n
	file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9}" _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n

	file write let "\\" _n

		forval g = 0/2 {
			local glab : variable label gg`g'
			file write let "&`glab' &`w`g'' \\" _n
			file write let "& 		 &`s`g'' \\" _n

		}


	file write let "\midrule" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications use controls for baseline score, grade dummies (where applicable) and randomization strata fixed effects. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let















