/*
01_descriptives.do — Summary statistics, balance, attrition + figures
=====================================================================
Produces LaTeX tables and PDF figures in $out/.
*/

di _n "{hline 70}"
di "01_descriptives.do"
di "{hline 70}"



* ═══════════════════════════════════════════════════════════════════════════
* PROGRAM: Write balance/attrition table for one study
* ═══════════════════════════════════════════════════════════════════════════

cap program drop write_balance_table
program define write_balance_table
	syntax, file(string) caption(string) label(string) cluster(varname)

	tempname fh
	file open `fh' using "`file'", write replace
	local cl_note "the supplied cluster"
	if "`cluster'" == "academycode" local cl_note "the school level"
	if "`cluster'" == "ggroup" local cl_note "the school grade group level"

	local panel "Experiment"
	if strpos("`caption'","Liberia") > 0 local panel "Experiment (Liberia)"
	if strpos("`caption'","Kenya") > 0   local panel "Experiment (Kenya)"

	file write `fh' "\begin{table}[H]" _n
	file write `fh' "\centering" _n
	file write `fh' "\caption{`caption'}" _n
	file write `fh' "\label{`label'}" _n
	file write `fh' "\begin{threeparttable}" _n
	file write `fh' "\begin{tabular}[t]{lccc}" _n
	file write `fh' "\toprule" _n
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{3}{c}{`panel'} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4}" _n
	file write `fh' " & Control Mean & Coefficient & N \\" _n
	file write `fh' "\midrule" _n

	foreach var in score_bl upper_group {
		if "`var'" == "score_bl"    local vlab "Baseline Score"
		if "`var'" == "upper_group" local vlab "Upper Group"

		qui summ `var' if treat == 0
		local cmean : di %7.3f r(mean)
		qui count if !mi(`var')
		local nn = r(N)

		cap qui reg `var' treat i.strata, vce(cluster `cluster')
		if _rc == 0 {
			local bb : di %7.3f _b[treat]
			local ss : di %7.3f _se[treat]
			local pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
			local star ""
			if `pv' < 0.10 local star "*"
			if `pv' < 0.05 local star "**"
			if `pv' < 0.01 local star "***"
		}
		else {
			local bb "--"
			local ss "--"
			local star ""
		}

		file write `fh' "`vlab' & `cmean' & `bb'`star' & `nn' \\" _n
		file write `fh' " & & (`ss') & \\" _n
	}

	file write `fh' "\bottomrule" _n
	file write `fh' "\end{tabular}" _n
	file write `fh' "\begin{tablenotes}[para]" _n
	file write `fh' "\item Notes: Pre-treatment characteristics only. All specifications control for randomization strata "
	file write `fh' "fixed effects. Standard errors are clustered at `cl_note'. "
	file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
	file write `fh' "\end{tablenotes}" _n
	file write `fh' "\end{threeparttable}" _n
	file write `fh' "\end{table}" _n

	file close `fh'
	di "  -> `file'"
end


cap program drop write_attrition_table
program define write_attrition_table
	syntax, file(string) caption(string) label(string) cluster(varname)

	cap gen attrited = !has_el

	tempname fh
	file open `fh' using "`file'", write replace
	local cl_note "cluster-robust SEs"
	if "`cluster'" == "academycode" local cl_note "SEs clustered at the school level"
	if "`cluster'" == "ggroup" local cl_note "SEs clustered at the school grade group level"

	file write `fh' "\begin{table}[H]" _n
	file write `fh' "\centering" _n
	file write `fh' "\caption{`caption'}" _n
	file write `fh' "\label{`label'}" _n
	file write `fh' "\begin{threeparttable}" _n
	file write `fh' "\begin{tabular}[t]{lcccc}" _n
	file write `fh' "\toprule" _n
	local panel "Experiment"
	if strpos("`caption'","Liberia") > 0 local panel "Experiment (Liberia)"
	if strpos("`caption'","Kenya") > 0   local panel "Experiment (Kenya)"
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{4}{c}{`panel'} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5}" _n
	file write `fh' "Sample & T missing & C missing & Adj.\ diff. & N \\" _n
	file write `fh' "\midrule" _n

	* Overall
	qui summ attrited if treat == 1
	local at : di %5.3f r(mean)
	qui summ attrited if treat == 0
	local ac : di %5.3f r(mean)
	qui reg attrited treat i.strata, vce(cluster `cluster')
	local bb : di %7.3f _b[treat]
	local ss : di %7.3f _se[treat]
	qui count
	local nn = r(N)
	file write `fh' "Overall & `at' & `ac' & `bb' & `nn' \\" _n
	file write `fh' " & & & (`ss') & \\" _n

	* By grade
	levelsof grade, local(grades)
	foreach g of local grades {
		qui summ attrited if treat == 1 & grade == `g'
		local at : di %5.3f r(mean)
		qui summ attrited if treat == 0 & grade == `g'
		local ac : di %5.3f r(mean)
		cap qui reg attrited treat i.strata if grade == `g', vce(cluster `cluster')
		if _rc == 0 {
			local bb : di %7.3f _b[treat]
			local ss : di %7.3f _se[treat]
		}
		else {
			local bb "--"
			local ss "--"
		}
		qui count if grade == `g'
		local nn = r(N)
		file write `fh' "Grade `g' & `at' & `ac' & `bb' & `nn' \\" _n
		file write `fh' " & & & (`ss') & \\" _n
	}

	file write `fh' "\bottomrule" _n
	file write `fh' "\end{tabular}" _n
	file write `fh' "\begin{tablenotes}[para]" _n
	file write `fh' "\item Notes: Attrition = missing endline. T missing and C missing are unadjusted arm means. "
	file write `fh' "Adjusted difference is the treatment coefficient from an OLS regression with strata FE; `cl_note'." _n
	file write `fh' "\end{tablenotes}" _n
	file write `fh' "\end{threeparttable}" _n
	file write `fh' "\end{table}" _n

	file close `fh'
	di "  -> `file'"
end

cap program drop write_sumstats_table
program define write_sumstats_table
	syntax, file(string) caption(string) label(string)

	tempname fh
	file open `fh' using "`file'", write replace

	local panel "Experiment"
	if strpos("`caption'","Liberia") > 0 local panel "Experiment (Liberia)"
	if strpos("`caption'","Kenya") > 0   local panel "Experiment (Kenya)"

	file write `fh' "\begin{table}[H]" _n
	file write `fh' "\centering" _n
	file write `fh' "\caption{`caption'}" _n
	file write `fh' "\label{`label'}" _n
	file write `fh' "\begin{threeparttable}" _n
	file write `fh' "\begin{tabular}[t]{lcccc}" _n
	file write `fh' "\toprule" _n
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{4}{c}{`panel'} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5}" _n
	file write `fh' "Variable & Control Mean & Treatment Mean & SD (All) & N \\" _n
	file write `fh' "\midrule" _n

	foreach var in score_bl score_el upper_group has_el csize {
		if "`var'" == "score_bl"    local vlab "Baseline score"
		if "`var'" == "score_el"    local vlab "Endline score"
		if "`var'" == "upper_group" local vlab "Upper-track assignment"
		if "`var'" == "has_el"      local vlab "Has endline"
		if "`var'" == "csize"       local vlab "Class size"

		qui summ `var' if finsamp & treat == 0
		local cmean : di %7.3f r(mean)
		qui summ `var' if finsamp & treat == 1
		local tmean : di %7.3f r(mean)
		qui summ `var' if finsamp
		local sdev : di %7.3f r(sd)
		qui count if finsamp & !mi(`var')
		local nn = r(N)

		file write `fh' "`vlab' & `cmean' & `tmean' & `sdev' & `nn' \\" _n
	}

	file write `fh' "\bottomrule" _n
	file write `fh' "\end{tabular}" _n
	file write `fh' "\begin{tablenotes}[para]" _n
	file write `fh' "\item Notes: Means and standard deviations are reported in the analytic "
	file write `fh' "sample. Endline outcomes are based on observations with non-missing "
	file write `fh' "endline test scores." _n
	file write `fh' "\end{tablenotes}" _n
	file write `fh' "\end{threeparttable}" _n
	file write `fh' "\end{table}" _n

	file close `fh'
	di "  -> `file'"
end


cap program drop write_sampleflow_table
program define write_sampleflow_table
	syntax, file(string) caption(string) label(string)

	tempname fh
	file open `fh' using "`file'", write replace

	local panel "Experiment"
	if strpos("`caption'","Liberia") > 0 local panel "Experiment (Liberia)"
	if strpos("`caption'","Kenya") > 0   local panel "Experiment (Kenya)"

	file write `fh' "\begin{table}[H]" _n
	file write `fh' "\centering" _n
	file write `fh' "\caption{`caption'}" _n
	file write `fh' "\label{`label'}" _n
	file write `fh' "\begin{threeparttable}" _n
	file write `fh' "\begin{tabular}[t]{lccc}" _n
	file write `fh' "\toprule" _n
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{3}{c}{`panel'} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
	file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} \\" _n
	file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4}" _n
	file write `fh' "Sample flow step & Control & Treatment & Total \\" _n
	file write `fh' "\midrule" _n

	local flow_1 "1"
	local flow_2 "finsamp"
	local flow_3 "finsamp & !mi(score_bl)"
	local flow_4 "finsamp & has_el"

	forvalues k = 1/4 {
		local cond "`flow_`k''"
		if `k' == 1 local rowlab "All observations"
		if `k' == 2 local rowlab "Analytic sample"
		if `k' == 3 local rowlab "With baseline score"
		if `k' == 4 local rowlab "With endline score"

		qui count if `cond' & treat == 0
		local nc = r(N)
		qui count if `cond' & treat == 1
		local nt = r(N)
		qui count if `cond'
		local na = r(N)

		file write `fh' "`rowlab' & `nc' & `nt' & `na' \\" _n
	}

	file write `fh' "\bottomrule" _n
	file write `fh' "\end{tabular}" _n
	file write `fh' "\begin{tablenotes}[para]" _n
	file write `fh' "\item Notes: Counts shown by treatment status at each sample construction "
	file write `fh' "step in the cleaned analysis dataset. The analytic sample keeps students "
	file write `fh' "with a nonmissing baseline score and at least two baseline scored students "
	file write `fh' "in the assignment unit used to form peer and classroom measures." _n
	file write `fh' "\end{tablenotes}" _n
	file write `fh' "\end{threeparttable}" _n
	file write `fh' "\end{table}" _n

	file close `fh'
	di "  -> `file'"
end


cap program drop write_binscatter_fig
program define write_binscatter_fig
	syntax, file(string)

	preserve
		keep if finsamp & !mi(score_bl) & !mi(score_el)
		bys grade treat (score_bl): gen long rank_in_grp = _n
		bys grade treat: gen long n_in_grp = _N
		gen bl_bin = ceil(20 * rank_in_grp / n_in_grp)
		collapse (mean) score_bl score_el, by(grade treat bl_bin)
		capture label define grade_lbl 1 "Grade 1" 2 "Grade 2" 3 "Grade 3" 4 "Grade 4", replace
		label values grade grade_lbl
		twoway ///
			(scatter score_el score_bl if treat == 0, mcolor(navy) msymbol(O) msize(medium)) ///
			(scatter score_el score_bl if treat == 1, mcolor(maroon) msymbol(T) msize(medium)) ///
			(lfit score_el score_bl if treat == 0, lcolor(navy) lpattern(solid)) ///
			(lfit score_el score_bl if treat == 1, lcolor(maroon) lpattern(dash)), ///
			by(grade, rows(1) note("")) ///
			legend(order(1 "Control" 2 "Treatment") pos(6) row(1)) ///
			xtitle("Baseline score (bin means)") ytitle("Endline score (bin means)") ///
			scheme(s1mono)
		graph export "`file'", replace
		di "  -> `file'"
	restore
end


* ═══════════════════════════════════════════════════════════════════════════
* LIBERIA
* ═══════════════════════════════════════════════════════════════════════════

use "$out/analysis_liberia.dta", clear

di _n "=== LIBERIA ==="

write_sumstats_table, file("$out/lib_sumstats.tex") ///
	caption("Summary Statistics --- Liberia") ///
	label("tab:lib_sumstats")

write_sampleflow_table, file("$out/lib_sampleflow.tex") ///
	caption("Sample Flow --- Liberia") ///
	label("tab:lib_sampleflow")

keep if finsamp
capture label define grade_lbl 1 "Grade 1" 2 "Grade 2" 3 "Grade 3" 4 "Grade 4", replace
label values grade grade_lbl

* Balance table
write_balance_table, file("$out/lib_balance.tex") ///
	caption("Baseline Balance --- Liberia") ///
	label("tab:lib_balance") cluster(ggroup)

* Attrition table
write_attrition_table, file("$out/lib_attrition.tex") ///
	caption("Attrition --- Liberia") ///
	label("tab:lib_attrition") cluster(ggroup)

* BL distribution figure
tw (hist score_bl if treat == 0, color(blue%40) frac) ///
   (hist score_bl if treat == 1, color(red%40) frac), ///
	by(grade, note("") rows(1)) ///
	legend(order(1 "Control" 2 "Treatment") pos(6) row(1)) ///
	xtitle("Baseline Score") ytitle("Fraction") ///
	xlabel(0(10)40) ///
	scheme(s1mono)
graph export "$out/lib_bl_dist.pdf", replace
di "  -> lib_bl_dist.pdf"

* EL distribution figure
tw (hist score_el if treat == 0 & has_el, color(blue%40) frac) ///
   (hist score_el if treat == 1 & has_el, color(red%40) frac), ///
	by(grade, note("") rows(1)) ///
	legend(order(1 "Control" 2 "Treatment") pos(6) row(1)) ///
	xtitle("Endline Score") ytitle("Fraction") ///
	xlabel(0(10)40) ///
	scheme(s1mono)
graph export "$out/lib_el_dist.pdf", replace
di "  -> lib_el_dist.pdf"

* Within-class dispersion boxplot
preserve
	gen class_id = string(academycode) + "_" + string(cond(treat==1, std_grp, grade))
	collapse (sd) within_sd = score_bl, by(class_id treat)
	drop if mi(within_sd)
	label define tlab 0 "Control" 1 "Treatment"
	label values treat tlab
	graph box within_sd, over(treat) ///
		ytitle("Within-Class SD of Baseline Scores") ///
		box(1, color(blue%60)) box(2, color(red%60)) ///
		scheme(s1mono)
	graph export "$out/lib_dispersion_box.pdf", replace
	di "  -> lib_dispersion_box.pdf"
restore

* Class size distribution
preserve
	gen class_id = string(academycode) + "_" + string(cond(treat==1, std_grp, grade))
	collapse (count) class_size = studyid, by(class_id treat)
	label define tlab 0 "Control" 1 "Treatment", replace
	label values treat tlab
	tw (hist class_size if treat == 0, color(blue%40) frac width(5)) ///
	   (hist class_size if treat == 1, color(red%40) frac width(5)), ///
		legend(order(1 "Control" 2 "Treatment") pos(6) row(1)) ///
		xtitle("Students per Class") ytitle("Fraction") ///
		scheme(s1mono)
	graph export "$out/lib_classsize.pdf", replace
	di "  -> lib_classsize.pdf"
restore

write_binscatter_fig, file("$out/lib_binscatter.pdf")


* ═══════════════════════════════════════════════════════════════════════════
* KENYA Y1
* ═══════════════════════════════════════════════════════════════════════════

use "$out/analysis_kenya.dta", clear

di _n "=== KENYA Y1 ==="

write_sumstats_table, file("$out/ke_sumstats.tex") ///
	caption("Summary Statistics --- Kenya") ///
	label("tab:ke_sumstats")

write_sampleflow_table, file("$out/ke_sampleflow.tex") ///
	caption("Sample Flow --- Kenya") ///
	label("tab:ke_sampleflow")

keep if finsamp
capture label define grade_lbl 1 "Grade 1" 2 "Grade 2", replace
label values grade grade_lbl

write_balance_table, file("$out/ke_balance.tex") ///
	caption("Baseline Balance --- Kenya") ///
	label("tab:ke_balance") cluster(academycode)

write_attrition_table, file("$out/ke_attrition.tex") ///
	caption("Attrition --- Kenya") ///
	label("tab:ke_attrition") cluster(academycode)

* BL distribution
tw (hist score_bl if treat == 0, color(blue%40) frac) ///
   (hist score_bl if treat == 1, color(red%40) frac), ///
	by(grade, note("") rows(1)) ///
	legend(order(1 "Control" 2 "Treatment") pos(6) row(1)) ///
	xtitle("Baseline Composite Score") ytitle("Fraction") ///
	scheme(s1mono)
graph export "$out/ke_bl_dist.pdf", replace

* EL distribution
tw (hist score_el if treat == 0 & has_el, color(blue%40) frac) ///
   (hist score_el if treat == 1 & has_el, color(red%40) frac), ///
	by(grade, note("") rows(1)) ///
	legend(order(1 "Control" 2 "Treatment") pos(6) row(1)) ///
	xtitle("Endline Composite Score") ytitle("Fraction") ///
	scheme(s1mono)
graph export "$out/ke_el_dist.pdf", replace

* Dispersion boxplot
preserve
	gen class_id = string(academycode) + "_" + string(cond(treat==1, std_grp, grade))
	collapse (sd) within_sd = score_bl, by(class_id treat)
	drop if mi(within_sd)
	label define tlab 0 "Control" 1 "Treatment", replace
	label values treat tlab
	graph box within_sd, over(treat) ///
		ytitle("Within-Class SD of Baseline Scores") ///
		box(1, color(blue%60)) box(2, color(red%60)) ///
		scheme(s1mono)
	graph export "$out/ke_dispersion_box.pdf", replace
restore

* Class size distribution
preserve
	gen class_id = string(academycode) + "_" + string(cond(treat==1, std_grp, grade))
	collapse (count) class_size = studyid, by(class_id treat)
	label define tlab 0 "Control" 1 "Treatment", replace
	label values treat tlab
	tw (hist class_size if treat == 0, color(blue%40) frac width(5)) ///
	   (hist class_size if treat == 1, color(red%40) frac width(5)), ///
		legend(order(1 "Control" 2 "Treatment") pos(6) row(1)) ///
		xtitle("Students per Class") ytitle("Fraction") ///
		scheme(s1mono)
	graph export "$out/ke_classsize.pdf", replace
	di "  -> ke_classsize.pdf"
restore

write_binscatter_fig, file("$out/ke_binscatter.pdf")

di _n "Descriptives complete."
