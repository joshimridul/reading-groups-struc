
/*==========================================================================

Title: 5_descriptives.do 
Author: Mridul Joshi
Date: Fri Dec 10 18:39:32 2021

Description: Descriptives and balance table for Kenya and Liberia Bridge 
			 ability-grouping analysis


Last edited by: MJ on Fri Dec 10 19:03:53 2021

===========================================================================*/


* ===================================================================== *
* -----------------     	      Kenya               ----------------- *
* ===================================================================== *


use "${datadir}/Kenya/5_K_AG_full_wide.dta", clear 


keep if inlist(pupil_observed,2,3)


bys academycode grade stream: gen class_size = _N 

gen yr_operation = (assess_date_el - academy_cohort)/365

gen class_size_1 = class_size if grade == 1
gen class_size_2 = class_size if grade == 2

* we only have grades 1-2 in the Kenya experiment
gen class_size_3 = .
gen class_size_4 = .



gen blscore = std_comp_score_bl

gen blscore_1 = blscore if grade == 1
gen blscore_2 = blscore if grade == 2

* we only have grades 1-2 in the Kenya experiment
gen blscore_3 = .
gen blscore_4 = .


collapse (mean) yr_operation class_size class_size_? blscore blscore_?, by(academycode treat grade stream academy_cohort constituency county)


collapse (mean) yr_operation class_size class_size_? blscore blscore_?, by(academycode treat academy_cohort constituency county)


lab var class_size "Class size"
lab var yr_operation "Academy years of operation"
lab var class_size_1 "Grade 1 class size"
lab var class_size_2 "Grade 2 class size"
lab var class_size_3 "Grade 3 class size"
lab var class_size_4 "Grade 4 class size"
lab var blscore "Baseline test score"
lab var blscore_1 "Grade 1 baseline score"
lab var blscore_2 "Grade 2 baseline score"
lab var blscore_3 "Grade 3 baseline score"
lab var blscore_4 "Grade 4 baseline score"


loc xlist "class_size class_size_1 class_size_2 class_size_3 class_size_4 blscore blscore_1 blscore_2 blscore_3 blscore_4" 


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
			cap areg `x' treat, a(constituency) vce(clus academycode) 



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


areg treat class_size blscore, a(constituency) vce(clus academycode) 

	test class_size blscore

	local F1 : display string(r(F),"%9.3f")	
	local p1 : display string(r(p),"%9.3f")



* ===================================================================== *
* -----------------     	      Liberia             ----------------- *
* ===================================================================== *



use "${datadir}/Liberia/5_L_AG_full_wide.dta", clear 

keep if sample == 1 // i.e. pupils in the experiment

bys academycode grade stream: gen class_size1 = _N 

gen class_grp = inlist(pupil_observed,1,4,6,7)
bys academycode grade stream class_grp: gen cs = _N  

replace cs = . if class_grp == 0

bys academycode grade stream: egen class_size = max(cs)

drop cs

gen yr_operation = (assess_date_el - academy_cohort)/365

gen class_size_1 = class_size if grade == 1
gen class_size_2 = class_size if grade == 2
gen class_size_3 = class_size if grade == 3
gen class_size_4 = class_size if grade == 4


gen blscore = std_score_bl

gen blscore_1 = blscore if grade == 1
gen blscore_2 = blscore if grade == 2
gen blscore_3 = blscore if grade == 3
gen blscore_4 = blscore if grade == 4



collapse (mean) yr_operation class_size class_size_? blscore blscore_?, by(academycode grade stream treat academy_cohort ggroup strata)

collapse (mean) yr_operation class_size class_size_? blscore blscore_?, by(academycode academy_cohort ggroup treat strata)



lab var class_size "Class size"
lab var yr_operation "Academy years of operation"
lab var class_size_1 "Grade 1 class size"
lab var class_size_2 "Grade 2 class size"
lab var class_size_3 "Grade 3 class size"
lab var class_size_4 "Grade 4 class size"
lab var blscore "Baseline test score"
lab var blscore_1 "Grade 1 baseline score"
lab var blscore_2 "Grade 2 baseline score"
lab var blscore_3 "Grade 3 baseline score"
lab var blscore_4 "Grade 4 baseline score"

loc xlist "class_size class_size_1 class_size_2 class_size_3 class_size_4 blscore blscore_1 blscore_2 blscore_3 blscore_4" 


foreach x in `xlist' {
			
			di "`x'"

			summ `x' if treat == 0 


			local m`x'l0 : display string(r(mean),"%9.3f")
			local Nm`x'l0 : display string(r(N),"%9.0fc")

			areg `x' treat, vce(clus ggroup) a(strata) 
			*cap reg `x' treat   



			local b`x'l : display string(_b[treat],"%9.3f")

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
			local  b`x'l "`b`x'l'`star'"	
			local s`x'l : display string(_se[treat],"%9.3fc")		
			local p`x'l = 2*(1-normal(`t'))
			local p`x'l : display string(`p`x'l',"%9.3f")	
			local N`x'l : display string(e(N),"%9.0fc")
			local s`x'l "(`s`x'l')"

}


areg treat class_size blscore , vce(clus ggroup) a(strata)
	*test yr_operation class_size blscore
	test class_size blscore

	local F2 : display string(r(F),"%9.3f")	
	local p2 : display string(r(p),"%9.3f")


	*local w`x' = substr("`w`x''",2,.)
	*local N`x' = substr("`N`x''",2,.)	
	*local s`x' = substr("`s`x''",2,.)	



foreach x in `xlist' {

loc w`x' "`m`x'k0'&`b`x'k'&`N`x'k'&&`m`x'l0'&`b`x'l'&`N`x'l'"
loc s`x' " & `s`x'k'&&&&`s`x'l'& "

di "`w`x''"
di "`s`x''"
	
} 




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
		local P "`P'&&&&{`p`g''}"
		local F "`F'&&&&{`F`g''}"
		di "`P' | `F'"
		local c = `c'+3
}

/*
foreach l in H S C P F {
	local l = substr("`l'",2,.)	
}
*/

local P = substr("`P'",2,.)
local F = substr("`F'",2,.)


local size "scriptsize"
	
	
file open let using "${outdir}/baseline_balance_bygrade.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Baseline balance} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c @{}} \toprule \toprule" _n
	file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9}" _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n


	file write let "\\" _n

		foreach x of local xlist {
			local xlab : variable label `x'
			file write let "&`xlab' &`w`x'' \\" _n
			file write let "& 		 &`s`x'' \\" _n

		}

	file write let "\midrule" _n
	*file write let "\multicolumn{2}{l}{Observations} `Nearly_enrollment' \\" _n	
	file write let "\multicolumn{2}{l}{F-stat of joint test} `F' \\" _n		
	file write let "\multicolumn{2}{l}{P-value} `P' \\" _n	



	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications are at the academy-grade level and control for randomization strata fixed effects. Standard errors are clustered at the academy-grade group level. The joint test specification includes only class size and baseline test score. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let









