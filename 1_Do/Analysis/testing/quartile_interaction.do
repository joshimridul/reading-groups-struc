
/*==========================================================================

Title: quartile_interaction.do 
Author: Mridul Joshi
Date: Sun Dec 10 14:31:18 2023

===========================================================================*/


* ===================================================================== *
* -----------------     	  Kenya                   ----------------- *
* ===================================================================== *

use "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", clear 


** universal standardization

qui summ comp_score_bl if treat==0, detail

gen std2_compscore_bl = (comp_score_bl - `r(mean)')/`r(sd)'


qui summ comp_score_el if treat==0, detail

gen std2_compscore_el = (comp_score_el - `r(mean)')/`r(sd)'


egen bl_q = xtile(std2_compscore_bl), nq(4) //by(academycode grade stream)


forval i = 1/2 {

	egen abs_bl_q_g`i' = xtile(std2_compscore_bl) if grade== `i', nq(4) 
}

gen abs_bl_q_4 = abs_bl_q_g1
replace abs_bl_q_4 = abs_bl_q_g2 if mi(abs_bl_q_4)

loc zlist "bl"

gen g0 = gg0
keep if finsamp


** distance from median instruction 

* assuming that teachers teach to the median student

bys academycode grade: egen med_score_c = median(std2_compscore_bl)
bys grade: egen med_score_gr_c = median(std2_compscore_bl)


bys academycode purple: egen med_score_t = median(std2_compscore_bl)
bys purple: egen med_score_gr_t = median(std2_compscore_bl)

gen med_dist_t = abs(std2_compscore_bl - med_score_t)
gen med_dist_c = abs(std2_compscore_bl - med_score_c)

gen med_dist = med_dist_t
replace med_dist = med_dist_c if treat == 0

gen exp_med_dist = (P_t*med_dist_t) + (P_c*med_dist_c)




reg std2_compscore_el i.bl_q i.bl_q#treat std2_compscore_bl treat P_t if finsamp, vce(clus academycode)
estimates store model1


esttab model1 using results.tex, booktabs label replace ///
star(* 0.10 ** 0.05 *** 0.01) ///
nonumbers nomtitles ///
se









forval g = 0/2 {
			
			summ std_comp_score_el if treat == 0 & g`g' == 1

			if `r(N)' == 0 {

				local ms`g'k0 " "
			    local Nms`g'k0 " "
			}

			else {

				local ms`g'k0 : display string(r(mean),"%9.3f")
				local Nms`g'k0 : display string(r(N),"%9.0fc")
			}	

			loc star = ""
			cap reghdfe std_comp_score_el treat std_comp_score_bl i.grade if g`g' == 1, a(constituency) vce(clus academycode)


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



* ===================================================================== *
* -----------------     	     Liberia              ----------------- *
* ===================================================================== *

use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

gen g0 = gg0


qui summ score_bl if treat==0 & inlist(grade,3,4), detail

gen std2_score_bl_34 = (score_bl - `r(mean)')/`r(sd)'


qui summ score_el if treat==0  & inlist(grade,3,4), detail

gen std2_score_el_34 = (score_el - `r(mean)')/`r(sd)'


qui summ score_bl if treat==0 & inlist(grade,1,2), detail

gen std2_score_bl_12 = (score_bl - `r(mean)')/`r(sd)'


qui summ score_el if treat==0  & inlist(grade,1,2), detail

gen std2_score_el_12 = (score_el - `r(mean)')/`r(sd)'


gen std2_score_bl = std2_score_bl_34
replace std2_score_bl = std2_score_bl_12 if inlist(grade,1,2)

gen std2_score_el = std2_score_el_34
replace std2_score_el = std2_score_el_12 if inlist(grade,1,2)

drop std2_score_el_??


keep if sample == 1 
gen g34 = inlist(grade,3,4)

egen bl_q34 = xtile(std2_score_bl) if g34==1, nq(4) 
egen bl_q12 = xtile(std2_score_bl) if g34==0, nq(4) 
egen bl_q = rowtotal(bl_q12 bl_q34 )

replace bl_q = . if bl_q == 0

egen bl_q1 = xtile(std2_score_bl) if g1==1, nq(4) 
egen bl_q2 = xtile(std2_score_bl) if g2==1, nq(4) 
egen bl_q3 = xtile(std2_score_bl) if g3==1, nq(4) 
egen bl_q4 = xtile(std2_score_bl) if g4==1, nq(4) 

egen bl_q_4 = rowtotal(bl_q1 bl_q2 bl_q3 bl_q4)

replace bl_q_4 = . if bl_q_4 == 0


summarize std2_score_bl, detail
gen inrangedata =  inrange(std2_score_bl, r(p1), r(p99))



reg std2_score_el i.bl_q_4 i.bl_q_4#treat std2_score_bl treat P_t g34 if inrangedata , vce(clus ggroup)



gen high_q_peer = bl_q  == 4 

bys academycode std_grp: egen total_qt = total(high_q_peer)
bys academycode std_grp: egen count_qt = count(high_q_peer)

gen q4_peer_t= (total_qt - (high_q_peer==4))/(count_qt - 1)

bys academycode grade: egen total_qc = total(high_q_peer)
bys academycode grade: egen count_qc = count(high_q_peer)

gen q4_peer_c= (total_qc - (high_q_peer==4))/(count_qc - 1)

gen exp_q4_peer = (P_t*q4_peer_t) + (P_c*q4_peer_c)

gen q4_peer =q4_peer_t
replace q4_peer = q4_peer_c if treat == 0



* ===================================================================== *
* -----------------     	  Avg peer distance       ----------------- *
* ===================================================================== *

* control 
bysort academycode grade (studyid): gen id_c = _n
gen avg_distance_c = .

* Loop through each academy
levelsof academycode, local(acad)
foreach ac in `acad' {
	levelsof grade if academycode == `ac', local(grad)
	foreach g in `grad'{
    	* Identify the number of students in the current academy
    	sum id_c if academycode == `ac' & grade == `g', meanonly
    	di "`r(max) || '"
    	local num_students = r(max)

    	* Loop through each student within the academy
    	forval i = 1/`num_students' {
        	* Calculate the absolute differences between this student and all others
        	* Then take the average of these differences
        	qui sum std2_score_bl if academycode == `ac' & grade == `g' & id_c != `i', meanonly
        	local total_peers = r(N)  // this should be nonmissing entries
        	local sum_diff = 0
        	forval j = 1/`total_peers' {
            	qui sum std2_score_bl if academycode == `ac' & grade == `g' & id_c == `j', meanonly
            	local peer_score = r(mean)
            	qui sum std2_score_bl if academycode == `ac' & grade == `g' & id_c == `i', meanonly
            	local student_score = r(mean)
            	if `peer_score' != . {
            		local diff = abs(`student_score' - `peer_score')
            		local sum_diff = `sum_diff' + `diff'
            	}
        	}
        	local avg_diff = `sum_diff' / `total_peers'
        	replace avg_distance_c = `avg_diff' if academycode == `ac' & grade == `g' & id_c == `i'
    	}
	}
}


* treat 

bysort academycode std_grp (studyid): gen id_t = _n
gen avg_distance_t = .

* Loop through each academy
levelsof academycode, local(acad)
foreach ac in `acad' {
	levelsof std_grp if academycode == `ac', local(purp)
	foreach p in `purp'{
    	* Identify the number of students in the current academy
    	sum id_t if academycode == `ac' & std_grp == `p', meanonly
    	di "`r(max) || '"
    	local num_students = r(max)

    	* Loop through each student within the academy
    	forval i = 1/`num_students' {
        	* Calculate the absolute differences between this student and all others
        	* Then take the average of these differences
        	qui sum std2_score_bl if academycode == `ac' & std_grp == `p' & id_t != `i', meanonly
        	local total_peers = r(N)  // this should be nonmissing entries
        	local sum_diff = 0
        	forval j = 1/`total_peers' {
            	qui sum std2_score_bl if academycode == `ac' & std_grp == `p' & id_t == `j', meanonly
            	local peer_score = r(mean)
            	qui sum std2_score_bl if academycode == `ac' & std_grp == `p' & id_t == `i', meanonly
            	local student_score = r(mean)
            	if `peer_score' != . {
            		local diff = abs(`student_score' - `peer_score')
            		local sum_diff = `sum_diff' + `diff'
            	}
        	}
        	local avg_diff = `sum_diff' / `total_peers'
        	replace avg_distance_t = `avg_diff' if academycode == `ac' & std_grp == `p' & id_t == `i'
    	}
	}
}


gen avg_distance = avg_distance_t 
replace avg_distance = avg_distance_c if treat == 0


gen exp_avg_distance = (P_t*avg_distance_t) + (P_c*avg_distance_c)
lab var exp_avg_distance "E[Peer distance]"









forval g = 0/2 {

			sum std_score_el if treat == 0 & gg`g' == 1

			local mw`g'l0 : display string(r(mean),"%9.3f")
			local Nmw`g'l0 : display string(r(N),"%9.0fc")

			reghdfe std_score_el treat std_score_bl i.grade if gg`g' == 1, a(strata) vce(clus ggroup)

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

loc w`g' "`ms`g'k0'&`bs`g'k'&`Ns`g'k'&&`mw`g'l0'&`bw`g'l'&`Nw`g'l'"
loc s`g' " & `sw`g'k'&&&&`sw`g'l'& "

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
	
	
file open let using "${outdir}/test_score_effects.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Effects on test scores} " _n
	file write let "\label{tab:descriptives} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c c @{}} \toprule \toprule" _n
	file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9}" _n
	file write let "`S'  \\" _n
	file write let "`C' \\ \midrule " _n


	file write let "\\" _n

		forval g = 0/2 {
			local glab : variable label g`g'
			file write let "&`glab' &`w`g'' \\" _n
			file write let "& 		 &`s`g'' \\" _n

		}


	file write let "\midrule" _n

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications control for baseline score, grade dummies (where applicable) and randomization strata fixed effects. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let






