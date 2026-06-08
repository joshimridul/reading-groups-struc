
/*==========================================================================

Title: lib_fxupper.do 
Author: Mridul Joshi
Date: Sun Dec  8 14:02:37 2024

Description: impact of program by upper/lower group


===========================================================================*/



*use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

*keep if finsamp== 1 



*** outcomes ***


*** literacy regressions (Panel 1/2) ***

loc coef "treat trXpurplefull purplefull"

forval y = 0/2 {
			
	loc star = ""

	reg std_score_el treat trXpurplefull purplefull  P_t if exp`y' == 1, vce(clus ggroup) 


	if _rc == 2000 {

		foreach c in `coef' {
			local b`c'`y'1 " "
			local s`c'`y'1 " "
		}

		local N`y'1 " "
		local lin`y'1 " "
		local linp`y'1 " "
	}

	else {

		foreach c in `coef' {

			local b`c'`y'1 : display string(_b[`c'],"%9.2f")

	
			local t=abs(_b[`c']/_se[`c'])
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
		

			local b`c'`y'1 "`b`c'`y'1'`star'"	
			local s`c'`y'1 : display string(_se[`c'],"%9.2fc")		
			local p`c'`y'1 = 2*(1-normal(`t'))
			local p`c'`y'1 : display string(`p`c'`y'1',"%9.2f")	
			local s`c'`y'1 "(`s`c'`y'1')"

		}	

		local N`y'1 : display string(e(N),"%9.0fc")

		lincom treat + trXpurplefull

		local lin`y'1 : display string(`r(estimate)', "%9.2fc")
		local linp`y'1 : display string(`r(p)', "%9.2fc")
	}
}


foreach c in `coef' {

	loc blit`c' ""
	loc slit`c' ""

	forval y = 0/2 {

		loc blit`c' " `blit`c'' &  `b`c'`y'1' "
		loc slit`c' " `slit`c'' &  `s`c'`y'1' "
	}	

	di "`c'"
	di "`blit`c''"
	di "`slit`c''"
	
} 


loc linlit ""
loc linplit ""

forval y = 0/2 {

	loc linlit " `linlit' &  `lin`y'1' "
	loc linplit " `linplit' &  `linp`y'1' "
	loc Nlit " `Nlit' & `N`y'1' "

}	

di "`linlit'"
di "`linplit'"




* ===================================================================== *
* -----------------         Create latex table        ----------------- *
* ===================================================================== *

local size "small"
	

file open let using "${outdir}/effect_leveled_index_lib.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small The Effect of treatment by upper or lower group placement} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c   @{}} \toprule \toprule" _n
	file write let "& Stacked & Grades 3-4 & Grades 1-2 & \\" _n 
	file write let "`C' \\ \midrule " _n

	file write let "\\" _n
	
	foreach c of local coef {
		local clab : variable label `c'
		file write let " `clab'  `blit`c''  \\" _n
		file write let "         `slit`c''  \\" _n
	}

	file write let "\midrule" _n
	*file write let "Coef: Treatment + Treatment $\times$ Upper group `linlit'  \\" _n		
	file write let "Pval: Treatment + Treatment $\times$ Upper group `linplit'  \\" _n		
	file write let "Observations `Nlit'  \\" _n		

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications control linearly for randomization strata fixed effects. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let













