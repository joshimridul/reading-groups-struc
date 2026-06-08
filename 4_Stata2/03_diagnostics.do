/*
03_diagnostics.do — Diagnostic analyses with LaTeX tables + PDF figures
=======================================================================
Produces: signal quality table, cutoff heterogeneity table + figure,
          track × ability table + figure, class size controls table.
*/

di _n "{hline 70}"
di "03_diagnostics.do — Diagnostics and mechanisms"
di "{hline 70}"


cap program drop get_stars
program define get_stars, rclass
	args pval
	local s ""
	if `pval' < 0.10 local s "*"
	if `pval' < 0.05 local s "**"
	if `pval' < 0.01 local s "***"
	return local stars "`s'"
end

local ds = char(36)

* ═══════════════════════════════════════════════════════════════════════════
* 1. SIGNAL QUALITY TABLE (both studies)
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Signal Quality ---"

tempname fh
file open `fh' using "$out/tab_signal_quality.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Baseline-Endline Predictive Power}" _n
file write `fh' "\label{tab:signal_quality}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{llccc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{4}{c}{Control-group diagnostics} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5}" _n
file write `fh' "Study & Grade & N (Control) & Corr. & \(R^2\) \\" _n
file write `fh' "\midrule" _n

foreach study in kenya liberia {
	if "`study'" == "kenya"  local slab "Kenya"
	if "`study'" == "liberia" local slab "Liberia"

	use "$out/analysis_`study'.dta", clear
	keep if finsamp & treat == 0 & !mi(score_bl) & !mi(score_el)

	levelsof grade, local(grades)
	local first = 1
	foreach g of local grades {
		qui corr score_bl score_el if grade == `g'
		local rho : di %6.3f r(rho)
		local r2  : di %6.3f r(rho)^2
		qui count if grade == `g'
		local nc = r(N)
		if `first' {
			file write `fh' "`slab' & `g' & `nc' & `rho' & `r2' \\" _n
			local first = 0
		}
		else {
			file write `fh' " & `g' & `nc' & `rho' & `r2' \\" _n
		}
	}
	file write `fh' "\addlinespace" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Correlation is the Pearson correlation between baseline and endline raw scores "
file write `fh' "in the control group, by grade. \(R^2\) is the squared correlation and measures "
file write `fh' "the fraction of endline variance predicted by the baseline diagnostic." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_signal_quality.tex"


* ═══════════════════════════════════════════════════════════════════════════
* 2. LIBERIA: Cutoff heterogeneity (table + figure)
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Cutoff Heterogeneity ---"

use "$out/analysis_liberia.dta", clear
keep if finsamp & has_el

gen abs_dist = abs(dist_from_cutoff)
xtile dist_quintile = abs_dist, nq(5)

* Store results in a tempfile for the figure
tempfile cutoff_res
postfile pf_cut quintile mean_dist coef se using `cutoff_res'

tempname fh
file open `fh' using "$out/tab_cutoff_het.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{ITT Heterogeneity by Distance from Assignment Cutoff (Liberia)}" _n
file write `fh' "\label{tab:cutoff_het}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{4}{c}{Liberia} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5}" _n
file write `fh' "Quintile & Mean `ds'|s-c|`ds' & ITT & SE & N \\" _n
file write `fh' "\midrule" _n

forval q = 1/5 {
	qui summ abs_dist if dist_quintile == `q'
	local md : di %5.1f r(mean)
	local md_num = r(mean)

	qui reg std_score_el treat std_eb i.strata if dist_quintile == `q', vce(cluster ggroup)
	local bb : di %7.3f _b[treat]
	local ss : di %7.3f _se[treat]
	local pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars `pv'
	local star "`r(stars)'"
	local nn = e(N)

	post pf_cut (`q') (`md_num') (_b[treat]) (_se[treat])

	file write `fh' "Q`q' & `md' & `bb'`star' & (`ss') & `nn' \\" _n
}

* Continuous interaction
gen treat_x_absdist = treat * abs_dist
qui reg std_score_el treat treat_x_absdist abs_dist std_eb i.strata, vce(cluster ggroup)
local bi : di %7.4f _b[treat_x_absdist]
local si : di %7.4f _se[treat_x_absdist]
local pi = 2 * ttail(e(df_r), abs(_b[treat_x_absdist]/_se[treat_x_absdist]))
get_stars `pi'
local stari "`r(stars)'"
local ni = e(N)

file write `fh' "\midrule" _n
file write `fh' "T $\times$ $|s-c|$ & & `bi'`stari' & (`si') & `ni' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Quintiles of absolute distance from the grade group assignment "
file write `fh' "cutoff. OLS with strata FE and EB ability control. Standard errors are clustered at the school grade group level. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_cutoff_het.tex"

postclose pf_cut

* Figure
preserve
	use `cutoff_res', clear
	gen ci_lo = coef - 1.96 * se
	gen ci_hi = coef + 1.96 * se
	tw (rcap ci_lo ci_hi mean_dist, lcolor(navy)) ///
	   (scatter coef mean_dist, mcolor(navy) msymbol(O) msize(medlarge)), ///
		yline(0, lcolor(gs10) lpattern(dash)) ///
		ytitle("ITT Effect (std. endline)") ///
		xtitle("Mean |distance from cutoff| in quintile") ///
		legend(off) ///
		scheme(s1mono)
	graph export "$out/fig_cutoff_het.pdf", replace
	di "  -> fig_cutoff_het.pdf"
restore


* ═══════════════════════════════════════════════════════════════════════════
* 3. LIBERIA: Track × ability tercile (table + figure)
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Track × Ability ---"

tempfile trackbin_res
postfile pf_tb track tercile coef se using `trackbin_res'

tempname fh
file open `fh' using "$out/tab_track_bins.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Treatment Effects by Track and Ability Tercile (Liberia)}" _n
file write `fh' "\label{tab:track_bins}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{llcccc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{2}{c}{ } & \multicolumn{4}{c}{Liberia} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){3-6}" _n
file write `fh' " &  & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5} \cmidrule(l{3pt}r{3pt}){6-6}" _n
file write `fh' "Track & Ability Bin & ITT & SE & p value & N \\" _n
file write `fh' "\midrule" _n

foreach track_val in 0 1 {
	if `track_val' == 0 local tlab "Lower"
	if `track_val' == 1 local tlab "Upper"

	preserve
		keep if upper_group == `track_val'
		xtile ability_terc = std_score_bl, nq(3)

		local first = 1
		forval t = 1/3 {
			if `t' == 1 local tlabel "Bottom"
			if `t' == 2 local tlabel "Middle"
			if `t' == 3 local tlabel "Top"

			cap qui reg std_score_el treat std_eb i.strata if ability_terc == `t', vce(cluster ggroup)
			if _rc == 0 {
				local bb : di %7.3f _b[treat]
				local ss : di %7.3f _se[treat]
				local pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
				local pv_f : di %5.3f `pv'
				get_stars `pv'
				local star "`r(stars)'"
				local nn = e(N)
				post pf_tb (`track_val') (`t') (_b[treat]) (_se[treat])
			}
			else {
				local bb "--"
				local ss "--"
				local pv_f "--"
				local star ""
				local nn "."
			}

			if `first' {
				file write `fh' "`tlab' & `tlabel' & `bb'`star' & (`ss') & `pv_f' & `nn' \\" _n
				local first = 0
			}
			else {
				file write `fh' " & `tlabel' & `bb'`star' & (`ss') & `pv_f' & `nn' \\" _n
			}
		}
		file write `fh' "\addlinespace" _n
	restore
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Within-track ability terciles. OLS with strata FE and EB control. "
file write `fh' "Standard errors are clustered at the school grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_track_bins.tex"

postclose pf_tb

* Figure: grouped bars
preserve
	use `trackbin_res', clear
	gen ci_lo = coef - 1.96 * se
	gen ci_hi = coef + 1.96 * se
	gen x = tercile + 4 * track
	label define xlb 1 "Bottom" 2 "Middle" 3 "Top" 5 "Bottom" 6 "Middle" 7 "Top"
	label values x xlb
	tw (bar coef x if track == 0, barwidth(0.6) color(blue%60)) ///
	   (bar coef x if track == 1, barwidth(0.6) color(red%60)) ///
	   (rcap ci_lo ci_hi x, lcolor(black)), ///
		yline(0, lcolor(gs10) lpattern(dash)) ///
		xlabel(1 "Bottom" 2 "Middle" 3 "Top" 5 "Bottom" 6 "Middle" 7 "Top") ///
		xtitle("") ytitle("ITT (std. endline)") ///
		legend(order(1 "Lower Track" 2 "Upper Track") pos(6) row(1)) ///
		text(-0.5 2 "Lower Track", place(s) size(small)) ///
		text(-0.5 6 "Upper Track", place(s) size(small)) ///
		scheme(s1mono)
	graph export "$out/fig_track_bins.pdf", replace
	di "  -> fig_track_bins.pdf"
restore


* ═══════════════════════════════════════════════════════════════════════════
* 4. LIBERIA: Misclassification by distance from cutoff (figure)
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Misclassification by Distance ---"

use "$out/analysis_liberia.dta", clear
keep if finsamp

gen double theta_eb = .
gen double pr_misclass = .
gen double dist_cut = .
gen double z_cut = .

foreach g in 1 2 3 4 {
	if inlist(`g', 1, 2) local c = $lib_cutoff_g12
	if inlist(`g', 3, 4) local c = $lib_cutoff_g34
	qui corr score_bl score_el if treat == 0 & grade == `g' & !mi(score_bl) & !mi(score_el)
	local r2 = r(rho)^2
	qui summ score_bl if treat == 0 & grade == `g' & !mi(score_bl)
	local smean = r(mean)
	local ssd = r(sd)
	local sig_theta = sqrt((1 - `r2')) * `ssd'

		replace theta_eb = `smean' + `r2' * (score_bl - `smean') if grade == `g' & !mi(score_bl)
		replace dist_cut = score_bl - `c' if grade == `g' & !mi(score_bl)
		replace z_cut = (`c' - theta_eb) / `sig_theta' if grade == `g' & !mi(theta_eb)
		replace pr_misclass = normal(z_cut) if grade == `g' & score_bl >= `c' & !mi(z_cut)
		replace pr_misclass = 1 - normal(z_cut) if grade == `g' & score_bl < `c' & !mi(z_cut)
	}

preserve
	keep if treat == 1 & !mi(pr_misclass) & !mi(dist_cut)
	capture label define grade_lbl 1 "Grade 1" 2 "Grade 2" 3 "Grade 3" 4 "Grade 4", replace
	label values grade grade_lbl
	bys grade (dist_cut): gen long rank_in_grp = _n
	bys grade: gen long n_in_grp = _N
	gen dist_bin = ceil(12 * rank_in_grp / n_in_grp)
	collapse (mean) pr_misclass dist_cut (count) n = pr_misclass, by(grade dist_bin)
	drop if n < 10
	tw (scatter pr_misclass dist_cut, mcolor(navy) msymbol(O)), ///
		by(grade, rows(1) note("")) ///
		yline(0.5, lcolor(gs10) lpattern(dash)) ///
		ytitle("Pr(misclassified)") ///
		xtitle("Distance from cutoff (score - c)") ///
		scheme(s1mono)
	graph export "$out/fig_misclass.pdf", replace
	di "  -> fig_misclass.pdf"
restore


* ═══════════════════════════════════════════════════════════════════════════
* 5. CLASS-SIZE CONTROLS TABLE
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- Class-Size Controls ---"

tempname fh
file open `fh' using "$out/tab_classsize_diag.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{ITT With and Without Class-Size Control}" _n
file write `fh' "\label{tab:classsize_diag}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{4}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5}" _n
file write `fh' " & \multicolumn{2}{c}{Average ITT} & \multicolumn{2}{c}{T `ds'\times`ds' Upper} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3} \cmidrule(l{3pt}r{3pt}){4-5}" _n
file write `fh' " & No control & + Class size & No control & + Class size \\" _n
file write `fh' "\midrule" _n

foreach study in kenya liberia {
	if "`study'" == "kenya"  local slab "Kenya"
	if "`study'" == "liberia" local slab "Liberia"
	if "`study'" == "kenya"  local cl "academycode"
	if "`study'" == "liberia" local cl "ggroup"

	use "$out/analysis_`study'.dta", clear
	keep if finsamp & has_el & !mi(csize)
	gen treat_x_upper = treat * upper_group

	* ITT without class size
	qui reg std_score_el treat std_eb i.strata, vce(cluster `cl')
	local b1 : di %7.3f _b[treat]
	local s1 : di %7.3f _se[treat]

	* ITT with class size
	qui reg std_score_el treat std_eb csize i.strata, vce(cluster `cl')
	local b2 : di %7.3f _b[treat]
	local s2 : di %7.3f _se[treat]

	* T×Upper without class size
	qui reg std_score_el treat treat_x_upper upper_group std_eb i.strata, vce(cluster `cl')
	local b3 : di %7.3f _b[treat_x_upper]
	local s3 : di %7.3f _se[treat_x_upper]

	* T×Upper with class size
	qui reg std_score_el treat treat_x_upper upper_group std_eb csize i.strata, vce(cluster `cl')
	local b4 : di %7.3f _b[treat_x_upper]
	local s4 : di %7.3f _se[treat_x_upper]

	file write `fh' "`slab' & `b1' & `b2' & `b3' & `b4' \\" _n
	file write `fh' " & (`s1') & (`s2') & (`s3') & (`s4') \\" _n
	file write `fh' "\addlinespace" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: All specifications include strata FE and EB ability control. "
file write `fh' "Standard errors are clustered at the school level in Kenya and at the school grade group level in Liberia." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_classsize_diag.tex"


* ═══════════════════════════════════════════════════════════════════════════
* 6. FIRST-STAGE EFFECTS ON WITHIN-CLASS DISPERSION (KENYA + LIBERIA)
* ═══════════════════════════════════════════════════════════════════════════

di _n "--- First-stage effects on dispersion (Kenya + Liberia) ---"

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp

	if "`study'" == "kenya" local cl "academycode"
	if "`study'" == "liberia" local cl "ggroup"

	* Realized reading class: treated classes by std_grp, control classes by grade
	gen str32 class_id = string(academycode) + "_" + string(cond(treat == 1, std_grp, grade))

	* Dispersion outcomes by realized class
	bys class_id: egen mu_bl = mean(std_score_bl)
	gen dev_bl = abs(std_score_bl - mu_bl)

	bys class_id: egen mu_pred = mean(std_eb)
	gen dev_pred = abs(std_eb - mu_pred)

	bys class_id: egen mu_el = mean(std_score_el)
	gen dev_el = abs(std_score_el - mu_el)

	drop mu_bl mu_pred mu_el

	* Sample blocks
	gen samp_full = 1
	if "`study'" == "kenya" {
		gen samp_low = (grade == 1)
		gen samp_up  = (grade == 2)
	}
	else {
		gen samp_low = inlist(grade, 1, 2)
		gen samp_up  = inlist(grade, 3, 4)
	}

	foreach s in full low up {
		foreach y in bl pred el {
			if "`y'" == "bl"   local dep "dev_bl"
			if "`y'" == "pred" local dep "dev_pred"
			if "`y'" == "el"   local dep "dev_el"

			qui summ `dep' if treat == 0 & samp_`s' == 1 & !mi(`dep')
			local cm_`study'_`s'_`y' : di %6.3f r(mean)

			if "`y'" == "bl" {
				qui reg `dep' treat i.strata if samp_`s' == 1 & !mi(`dep'), vce(cluster `cl')
			}
			else {
				qui reg `dep' treat std_score_bl i.strata if samp_`s' == 1 & !mi(`dep') & !mi(std_score_bl), vce(cluster `cl')
			}

			local bb : di %7.3f _b[treat]
			local ss : di %7.3f _se[treat]
			local pv = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
			get_stars `pv'
			local st "`r(stars)'"

			local b_`study'_`s'_`y' "`bb'`st'"
			local se_`study'_`s'_`y' "`ss'"
			local n_`study'_`s'_`y' = e(N)
		}
	}
}

tempname fh
file open `fh' using "$out/tab_dispersion_firststage.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Effect on Within-Class Dispersion in Test Scores}" _n
file write `fh' "\label{tab:dispersion_firststage}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\fontsize{9}{11}\selectfont" _n
file write `fh' "\begin{tabular}[t]{lccccccccc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{10}{c}{ } \\" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{3}{c}{Baseline Scores} & \multicolumn{3}{c}{Predicted Outcomes} & \multicolumn{3}{c}{Endline Scores} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4} \cmidrule(l{3pt}r{3pt}){5-7} \cmidrule(l{3pt}r{3pt}){8-10}" _n
file write `fh' "\multicolumn{10}{c}{ } \\" _n
file write `fh' " & \Longstack{Control \\ mean \\ (1)} & \Longstack{Coef. \\  \\ (2)} & \Longstack{N \\ \\ (3)} & \Longstack{Control \\ mean \\ (4)} & \Longstack{Coef. \\ \\ (5)} & \Longstack{N \\ \\ (6)} & \Longstack{Control \\ mean \\ (7)} & \Longstack{Coef. \\ \\ (8)} & \Longstack{N \\ \\ (9)} \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{10}{l}{\textbf{\textit{Panel A: Kenya}}} \\" _n

foreach s in full low up {
	if "`s'" == "full" local rowname "Full Sample"
	if "`s'" == "low"  local rowname "Lower Grade"
	if "`s'" == "up"   local rowname "Upper Grade"
	file write `fh' "`rowname' & `cm_kenya_`s'_bl' & `b_kenya_`s'_bl' & `n_kenya_`s'_bl' & `cm_kenya_`s'_pred' & `b_kenya_`s'_pred' & `n_kenya_`s'_pred' & `cm_kenya_`s'_el' & `b_kenya_`s'_el' & `n_kenya_`s'_el' \\" _n
	file write `fh' " &  & (`se_kenya_`s'_bl') &  &  & (`se_kenya_`s'_pred') &  &  & (`se_kenya_`s'_el') & \\" _n
}

file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{10}{l}{\textbf{\textit{Panel B: Liberia}}} \\" _n

foreach s in full low up {
	if "`s'" == "full" local rowname "Full Sample"
	if "`s'" == "low"  local rowname "Lower Grade"
	if "`s'" == "up"   local rowname "Upper Grade"
	file write `fh' "`rowname' & `cm_liberia_`s'_bl' & `b_liberia_`s'_bl' & `n_liberia_`s'_bl' & `cm_liberia_`s'_pred' & `b_liberia_`s'_pred' & `n_liberia_`s'_pred' & `cm_liberia_`s'_el' & `b_liberia_`s'_el' & `n_liberia_`s'_el' \\" _n
	file write `fh' " &  & (`se_liberia_`s'_bl') &  &  & (`se_liberia_`s'_pred') &  &  & (`se_liberia_`s'_el') & \\" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: The outcome is the absolute deviation of each student's standardized score from the classroom mean. All specifications include randomization-strata fixed effects. The baseline score columns omit the baseline control because the outcome is constructed from baseline scores; the predicted-outcome and endline score columns control for standardized baseline score. Standard errors are clustered at the school level in Kenya and at the school grade group level in Liberia. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_dispersion_firststage.tex"

di _n "Diagnostics complete."
