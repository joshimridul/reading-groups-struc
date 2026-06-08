
/*==========================================================================

Title: peer_eff_quartiles.do 
Author: Mridul Joshi
Date: Thu Dec 14 02:39:55 2023

Description: Peer effects quartiles Kenya sample

===========================================================================*/



/*==========================================================================

Title: effect_on_quartiles.do 
Author: Mridul Joshi
Date: Wed Dec 13 14:59:38 2023

Description: effect of treatment by quartiles of baseline performance 

===========================================================================*/


use "${datadir}/Kenya/6_K_AG_full_wide_prepared_2.dta", clear 


* quartiles
tab bl_q, gen(bl_qtile)


gen peerXq1 = q4_peer*bl_qtile1
lab var peerXq1 "High ability peers $\times$ First quartile"

gen peerXq2 = q4_peer*bl_qtile2
lab var peerXq2 "High ability peers  $\times$ Second quartile"

gen peerXq3 = q4_peer*bl_qtile3
lab var peerXq3 "High ability peers $\times$ Third quartile"

gen peerXq4 = q4_peer*bl_qtile4
lab var peerXq4 "High ability peers  $\times$ Fourth quartile"

*lab var q4_peer "High ability peers "

*** outcomes ***

*local ylit "lit_index_t1 lit_index_t2 std_posttest_score"
*local ylang "lang_index_t1 lang_index_t2"

*local ylist "`ylit' `ylang'"



*** literacy regressions (Panel 1/2) ***

*loc coef "q4_peer peerXq3 peerXq2 peerXq1"
loc coef "peerXq4 peerXq3 peerXq2 peerXq1"


forval g = 0/2 {
			
	di "`g'"	

	loc star = ""
	reg std2_compscore_el peerXq4 peerXq3 peerXq2 peerXq1 bl_qtile? exp_q4_peer std2_compscore_bl P_t if gg`g' == 1, vce(clus academycode) 


	if _rc == 2000 {

		foreach c in `coef' {
			local b`c'`g'1 " "
			local s`c'`g'1 " "
		}

		local N`g'1 " "
		local lin`g'1 " "
		local linp`g'1 " "
	}

	else {

		foreach c in `coef' {

			local b`c'`g'1 : display string(_b[`c'],"%9.2f")

	
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
		

			local b`c'`g'1 "`b`c'`g'1'`star'"	
			local s`c'`g'1 : display string(_se[`c'],"%9.2fc")		
			local p`c'`g'1 = 2*(1-normal(`t'))
			local p`c'`g'1 : display string(`p`c'`g'1',"%9.2f")	
			local s`c'`g'1 "(`s`c'`g'1')"

		}	

		local N`g'1 : display string(e(N),"%9.0fc")

		forval i = 1/3 {
			
			*lincom q4_peer + peerXq`i'
			*local lin`g'`i' : display string(`r(estimate)', "%9.2fc")
			*local linp`g'`i' : display string(`r(p)', "%9.2fc")
		}

	}
}


foreach c in `coef' {

	loc blit`c' ""
	loc slit`c' ""

	forval g = 0/2 {

		loc blit`c' " `blit`c'' &  `b`c'`g'1' "
		loc slit`c' " `slit`c'' &  `s`c'`g'1' "
	}	

	di "`c'"
	di "`blit`c''"
	di "`slit`c''"
	
} 


loc linlit1 ""
loc linplit1 ""

forval i= 1/3 {

	loc linlit`i' ""
	loc linplit`i' ""
}


forval g = 0/2 {
	forval i = 1/3 {

		loc linlit`i' " `linlit`i'' &  `lin`g'`i'' "
		loc linplit`i' " `linplit`i'' &  `linp`g'`i'' "
		loc Nlit`i' " `Nlit' & `N`g'`i'' "
	}	

}	


forval i= 1/3 {

	di "`linlit`i''"
	di "`linplit`i''"
}




* ===================================================================== *
* -----------------         Create latex table        ----------------- *
* ===================================================================== *

local size "small"
	

file open let using "${outdir}/Kenya_new/peer_eff_on_qtiles_K.tex", write replace	
	file write let "\begin{center} " _n
	file write let "\caption{\small Differential effect of peers by baseline achievement quartiles} " _n
	file write let "\label{tab:peerfx} " _n
	file write let "\begin{`size'}" _n
	file write let "\begin{threeparttable}" _n
	file write let "\begin{tabular} {@{} l l c c c c c c  @{}} \toprule \toprule" _n
	file write let "& Full sample & Lower grade & Upper grade  \\" _n
	file write let "& (1) & (2) & (3) \\ \midrule " _n

	file write let "\\" _n
	
	foreach c of local coef {
		local clab : variable label `c'
		file write let " `clab'  `blit`c''  \\" _n
		file write let "         `slit`c''  \\" _n
	}

	file write let "\midrule" _n
	*file write let "Pval: Treated + Treated $\times$ First quartile `linplit1'  \\" _n		
	*file write let "Pval: Treated + Treated $\times$ Second quartile `linplit2'  \\" _n		
	*file write let "Pval: Treated + Treated $\times$ Third quartile `linplit3'  \\" _n		

	file write let "Observations `Nlit'  \\" _n		

	file write let "\bottomrule" _n

	file write let "\end{tabular}" _n
	file write let "\begin{tablenotes}" _n
	file write let "\item Notes: All specifications use control for pretest score and a linear control for the probability of the schools’ assignment to the tracking condition in all specifications. Standard errors are clustered at the strata level.  ***, **, and * indicate significance at 1\%, 5\%, and 10\% level. " 
	file write let "\end{tablenotes}" _n
	file write let "\end{threeparttable}" _n
	file write let "\end{`size'}" _n
	file write let "\end{center}" _n

	file write let "\clearpage" _n

file close let










