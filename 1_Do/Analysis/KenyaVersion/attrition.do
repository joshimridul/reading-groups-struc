

/*==========================================================================

Title: attrition.do 
Author: Mridul Joshi
Date: Tue Dec 12 15:31:28 2023

Description: Attrition Kenya sample

===========================================================================*/



use "${datadir}/Kenya/6_K_AG_full_wide_prepared_2.dta", clear 

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
			reghdfe has_anyscore treat std2_compscore_bl if gg`g' == 1, a(constituency) vce(clus academycode) // bl and el


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



forval g = 0/2 {

loc w`g' "`ms`g'k0'&`bs`g'k'&`Ns`g'k'"
loc s`g' " & `ss`g'k'"

di "`w`g''"
di "`s`g''"
	
} 



local S "&&\Longstack{Control\#mean}&\Longstack{Coef.}&\Longstack{N}"
local H "&&(1)&(2))&(3)"


local size "small"
	
	
file open let using "${outdir}/Kenya_new/attrition_K.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Test score follow-up} " _n
	file write let "\label{tab:attn} " _n
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
	file write let "\item Notes: All specifications use controls for pretest score and randomization strata fixed effects. Standard errors are clustered at the academy level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let



