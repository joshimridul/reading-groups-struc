


use "${datadir}/Liberia/6_L_AG_full_stacked_prepared.dta", clear 

keep if treat == 0



egen bl_q_old = xtile(score_bl), nq(5) //by(academycode grade stream)

binscatter score_el bl_q if inlist(grade,3,4), xq(bl_q) by(grade) xtitle("Baseline score quantiles") ytitle("Endline score") legend(order(1 "Grade 3" 2 "Grade 4")) absorb(academy_cohort)

graph export "${outdir}/L_score_q_34_graph.pdf", replace as(pdf)



binscatter score_el bl_q if treat==0 & inlist(grade,1,2), xq(bl_q) by(grade) xtitle("Baseline score quantiles") ytitle("Endline score") legend(order(1 "Grade 1" 2 "Grade 2")) absorb(academy_cohort)

graph export "${outdir}/L_score_q_12_graph.pdf", replace as(pdf)





use "${datadir}/Kenya/6_K_AG_full_stacked_prepared.dta", clear 

*collapse (sum) score_el score_bl, by(studyid academycode grade stream treat)

egen bl_q = xtile(comp_score_bl), nq(5) //by(academycode grade stream)

** universal standardization

qui summ comp_score_bl if treat==0, detail

gen std2_compscore_bl = (comp_score_bl - `r(mean)')/`r(sd)'


qui summ comp_score_el if treat==0, detail

gen std2_compscore_el = (comp_score_el - `r(mean)')/`r(sd)'


egen bl_q = xtile(std2_compscore_bl), nq(5) //by(academycode grade stream)


binscatter std2_compscore_el bl_q if treat==0 , xq(bl_q) by(grade) xtitle("Baseline score quantiles") ytitle("Endline score") legend(order(1 "Grade 1" 2 "Grade 2")) absorb(academy_cohort)

graph export "${outdir}/K_score_q_12_graph.pdf", replace as(pdf)


graph drop _all




forval i = 1/2 {

	egen abs_bl_q_g`i' = xtile(std2_compscore_bl) if grade== `i', nq(4) 
}

gen abs_bl_q_4 = abs_bl_q_g1
replace abs_bl_q_4 = abs_bl_q_g2 if mi(abs_bl_q_4)



levelsof academycode, loc(acad)

foreach a in `acad' {

	forval i = 1/2 {

		egen abs_bl_q_g`i'_`a' = xtile(std2_compscore_bl) if grade== `i' & academycode == `a', nq(4) 
	}
}

egen abs_bl_q_4_acad = rowtotal(abs_bl_q_g?_*)
replace abs_bl_q_4_acad = . if abs_bl_q_4_acad == 0

drop abs_bl_q_g?_*







