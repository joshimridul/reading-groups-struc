/*
06_robustness.do — Robustness tables
=====================================
Produces: tab_spec_robust.tex, tab_ceiling.tex,
          tab_score_variance.tex, tab_classsize_ctrl.tex
*/

di _n "{hline 70}"
di "06_robustness.do — Robustness tables"
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

if "$root" == "" {
	local pwd = c(pwd)
	if fileexists("`pwd'/4_Stata2/_master.do") {
		global root "`pwd'"
	}
	else if fileexists("`pwd'/_master.do") {
		local root_dir = subinstr("`pwd'", "/4_Stata2", "", .)
		global root "`root_dir'"
	}
	else {
		di as err "Could not infer repo root. Run from the repo root or 4_Stata2/, or set global root."
		exit 601
	}
}
if "$out" == ""  global out "$root/4_Stata2/output"
cap mkdir "$out"


* ═══════════════════════════════════════════════════════════════════════════
* 1. SPECIFICATION ROBUSTNESS TABLE
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== 1. Specification Robustness ==="

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & has_el

	if "`study'" == "kenya"   local cl "academycode"
	if "`study'" == "liberia" local cl "ggroup"

	* ── (a) Baseline: EB control + strata FE ──
	qui reg std_score_el treat std_eb i.strata, vce(cluster `cl')
	local `study'_a_b  : di %7.3f _b[treat]
	local `study'_a_se : di %7.3f _se[treat]
	local `study'_a_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_a_pv'
	local `study'_a_star "`r(stars)'"
	local `study'_a_n = e(N)

	* ── (b) Raw baseline score control (instead of EB) ──
	qui reg std_score_el treat std_score_bl i.strata, vce(cluster `cl')
	local `study'_b_b  : di %7.3f _b[treat]
	local `study'_b_se : di %7.3f _se[treat]
	local `study'_b_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_b_pv'
	local `study'_b_star "`r(stars)'"

	* ── (c) No baseline control ──
	qui reg std_score_el treat i.strata, vce(cluster `cl')
	local `study'_c_b  : di %7.3f _b[treat]
	local `study'_c_se : di %7.3f _se[treat]
	local `study'_c_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_c_pv'
	local `study'_c_star "`r(stars)'"

	* ── (d) Wild cluster bootstrap p value (baseline spec) ──
	qui reg std_score_el treat std_eb i.strata, vce(cluster `cl')
	capture which boottest
	if _rc != 0 {
		capture ssc install boottest, replace
	}
	capture noisily boottest treat, reps(999) seed(12345) cluster(`cl') nograph
	if _rc == 0 {
		local `study'_wb : di %5.3f r(p)
	}
	else {
		local `study'_wb "---"
	}

	* ── (e) Permutation inference (matching the country-specific assignment unit) ──
	qui reg std_score_el treat std_eb i.strata, vce(cluster `cl')
	local obs_t = abs(_b[treat] / _se[treat])
	local nperm 999
	local pcount 0
	set seed 54321
	forval p = 1/`nperm' {
		preserve
		* Collapse to the randomized unit, permute treatment within strata
		tempfile _pupil
		save `_pupil'
		collapse (first) treat strata, by(`cl')
		gen double _u = runiform()
		sort strata _u
		by strata: egen _nt = total(treat)
		by strata: gen _pt = (_n <= _nt)
		keep `cl' _pt
		tempfile _punit
		save `_punit'
		use `_pupil', clear
		merge m:1 `cl' using `_punit', nogen
		qui reg std_score_el _pt std_eb i.strata, vce(cluster `cl')
		if abs(_b[_pt] / _se[_pt]) >= `obs_t' {
			local ++pcount
		}
		restore
	}
	local `study'_pp : di %5.3f (`pcount' + 1) / (`nperm' + 1)
}

* Write table
tempname fh
file open `fh' using "$out/tab_spec_robust.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{ITT Estimates under Alternative Specifications}" _n
file write `fh' "\label{tab:spec_robust}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\fontsize{9}{11}\selectfont" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & \multicolumn{2}{c}{Kenya} & \multicolumn{2}{c}{Liberia} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3} \cmidrule(l{3pt}r{3pt}){4-5}" _n
file write `fh' " & Coef. & SE & Coef. & SE \\" _n
file write `fh' "\midrule" _n
file write `fh' "Baseline (EB + strata FE) & `kenya_a_b'`kenya_a_star' & (`kenya_a_se') & `liberia_a_b'`liberia_a_star' & (`liberia_a_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Raw baseline score control & `kenya_b_b'`kenya_b_star' & (`kenya_b_se') & `liberia_b_b'`liberia_b_star' & (`liberia_b_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "No baseline control & `kenya_c_b'`kenya_c_star' & (`kenya_c_se') & `liberia_c_b'`liberia_c_star' & (`liberia_c_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\midrule" _n
file write `fh' "Wild cluster bootstrap " _char(36) "p" _char(36) "-value & \multicolumn{2}{c}{`kenya_wb'} & \multicolumn{2}{c}{`liberia_wb'} \\" _n
file write `fh' "Permutation " _char(36) "p" _char(36) "-value & \multicolumn{2}{c}{`kenya_pp'} & \multicolumn{2}{c}{`liberia_pp'} \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & \multicolumn{2}{c}{`kenya_a_n'} & \multicolumn{2}{c}{`liberia_a_n'} \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Each row reports the ITT estimate of treatment on standardized endline scores under a different specification. "
file write `fh' "The baseline controls for empirical Bayes ability and strata fixed effects, with standard errors clustered at the school level in Kenya and at the school grade group level in Liberia. "
file write `fh' "The raw baseline score row replaces the EB shrinkage estimate with the standardized raw baseline score. "
file write `fh' "Wild cluster bootstrap " _char(36) "p" _char(36) "-values use 999 replications (\citealt{cameron2008bootstrap}). "
file write `fh' "Permutation " _char(36) "p" _char(36) "-values are from a Fisher-exact randomization test with 999 permutations within strata at the country-specific assignment unit: school in Kenya and school grade group in Liberia. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_spec_robust.tex"


* ═══════════════════════════════════════════════════════════════════════════
* 2. CEILING EFFECTS (TOBIT) — KENYA ONLY
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== 2. Ceiling Effects (Tobit) ==="

use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el

* ── OLS baseline ──
qui reg std_score_el treat std_eb i.strata, vce(cluster academycode)
local ols_b  : di %7.3f _b[treat]
local ols_se : di %7.3f _se[treat]
local ols_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `ols_pv'
local ols_star "`r(stars)'"
local ols_n = e(N)

* ── Tobit, censored at observed maximum of raw endline ──
qui summ score_el
local ceil = r(max)
qui summ score_el if score_el == `ceil'
local n_at_ceil = r(N)

* Control-group SD of raw endline for normalization
qui summ score_el if treat == 0
local raw_sd = r(sd)

qui tobit score_el treat score_bl i.strata, ul(`ceil') vce(cluster academycode)
local tobit_b_raw = _b[treat]
local tobit_se_raw = _se[treat]
local tobit_b  : di %7.3f `tobit_b_raw' / `raw_sd'
local tobit_se : di %7.3f `tobit_se_raw' / `raw_sd'
local tobit_pv = 2 * normal(-abs(`tobit_b_raw' / `tobit_se_raw'))
get_stars `tobit_pv'
local tobit_star "`r(stars)'"
local tobit_n = e(N)
local tobit_cens : di %7.0f `n_at_ceil'

* ── OLS dropping top baseline score decile ──
qui xtile _bl_pct = score_bl, nq(10)
qui reg std_score_el treat std_eb i.strata if _bl_pct < 10, vce(cluster academycode)
local trim_b  : di %7.3f _b[treat]
local trim_se : di %7.3f _se[treat]
local trim_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `trim_pv'
local trim_star "`r(stars)'"
local trim_n = e(N)
drop _bl_pct

* Write table
tempname fh
file open `fh' using "$out/tab_ceiling.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Robustness to Score Ceiling Effects (Kenya)}" _n
file write `fh' "\label{tab:ceiling}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & \makecell{(1) \\ OLS} & \makecell{(2) \\ Tobit} & \makecell{(3) \\ Trimmed OLS} \\" _n
file write `fh' "\midrule" _n
file write `fh' "Treatment & `ols_b'`ols_star' & `tobit_b'`tobit_star' & `trim_b'`trim_star' \\" _n
file write `fh' " & (`ols_se') & (`tobit_se') & (`trim_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `ols_n' & `tobit_n' & `trim_n' \\" _n
file write `fh' "Right-censored obs. & & `tobit_cens' & \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Column~(1) reproduces the baseline OLS ITT on standardized endline scores. "
file write `fh' "Column~(2) estimates a Tobit model on the raw endline composite (upper limit = `ceil' points), controlling for raw baseline score and strata FE; the coefficient and SE are divided by the control\mbox{-}group SD of raw endline scores for comparability with column~(1). "
file write `fh' "Column~(3) re-estimates OLS after dropping students in the top baseline score decile. "
file write `fh' "Columns~(1) and~(3) control for EB ability and strata FE; column~(2) controls for raw baseline score and strata FE\@. Standard errors are clustered at the school level. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_ceiling.tex"


* ═══════════════════════════════════════════════════════════════════════════
* 3. TREATMENT EFFECT ON SCORE VARIANCE
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== 3. Score Variance ==="

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & has_el

	if "`study'" == "kenya"   local cl "academycode"
	if "`study'" == "liberia" local cl "ggroup"

	* ── Panel A: raw variances ──
	qui summ std_score_el if treat == 0
	local `study'_var_c : di %7.3f r(Var)
	qui summ std_score_el if treat == 1
	local `study'_var_t : di %7.3f r(Var)

	* Grand mean for squared-deviation regressions
	qui summ std_score_el
	local gm = r(mean)

	* ── Panel B: total variance (squared deviation from grand mean) ──
	gen sq_dev = (std_score_el - `gm')^2
	qui reg sq_dev treat std_eb i.strata, vce(cluster `cl')
	local `study'_vb  : di %7.3f _b[treat]
	local `study'_vse : di %7.3f _se[treat]
	local `study'_vpv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_vpv'
	local `study'_vstar "`r(stars)'"
	local `study'_vn = e(N)

	* ── Within-class variance ──
	* Reading class: (academy, std_grp) for treatment; (academy, grade) for control
	gen str64 class_id = string(academycode) + "_" + string(treat) + "_" ///
		+ string(cond(treat == 1, std_grp, grade))
	bys class_id: egen cls_mean_el = mean(std_score_el)
	gen sq_within = (std_score_el - cls_mean_el)^2

	qui reg sq_within treat std_eb i.strata, vce(cluster `cl')
	local `study'_wb  : di %7.3f _b[treat]
	local `study'_wse : di %7.3f _se[treat]
	local `study'_wpv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_wpv'
	local `study'_wstar "`r(stars)'"

	* ── Between-class variance ──
	gen sq_between = (cls_mean_el - `gm')^2
	qui reg sq_between treat std_eb i.strata, vce(cluster `cl')
	local `study'_bb  : di %7.3f _b[treat]
	local `study'_bse : di %7.3f _se[treat]
	local `study'_bpv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_bpv'
	local `study'_bstar "`r(stars)'"

	drop sq_dev sq_within sq_between cls_mean_el class_id
}

* Write table
tempname fh
file open `fh' using "$out/tab_score_variance.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Treatment Effect on Score Variance}" _n
file write `fh' "\label{tab:score_variance}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' " & Kenya & Liberia \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{3}{l}{\textit{Panel A: Aggregate variance}} \\" _n
file write `fh' "\addlinespace[2pt]" _n
file write `fh' "Control & `kenya_var_c' & `liberia_var_c' \\" _n
file write `fh' "Treatment & `kenya_var_t' & `liberia_var_t' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{3}{l}{\textit{Panel B: Treatment on total variance}} \\" _n
file write `fh' "\addlinespace[2pt]" _n
file write `fh' "Treatment & `kenya_vb'`kenya_vstar' & `liberia_vb'`liberia_vstar' \\" _n
file write `fh' " & (`kenya_vse') & (`liberia_vse') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{3}{l}{\textit{Panel C: Treatment on within class variance}} \\" _n
file write `fh' "\addlinespace[2pt]" _n
file write `fh' "Treatment & `kenya_wb'`kenya_wstar' & `liberia_wb'`liberia_wstar' \\" _n
file write `fh' " & (`kenya_wse') & (`liberia_wse') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{3}{l}{\textit{Panel D: Treatment on between class variance}} \\" _n
file write `fh' "\addlinespace[2pt]" _n
file write `fh' "Treatment & `kenya_bb'`kenya_bstar' & `liberia_bb'`liberia_bstar' \\" _n
file write `fh' " & (`kenya_bse') & (`liberia_bse') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `kenya_vn' & `liberia_vn' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Panel~A reports raw variance of standardized endline scores by treatment arm. "
file write `fh' "Panels~B--D regress individual-level squared deviations on treatment, controlling for EB ability and strata FE\@. "
file write `fh' "Total variance uses deviations from the sample grand mean; within class variance uses deviations from realized reading classroom means; "
file write `fh' "between class variance uses the squared deviation of the classroom mean from the grand mean. "
file write `fh' "Standard errors are clustered at the school level in Kenya and at the school grade group level in Liberia. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_score_variance.tex"


* ═══════════════════════════════════════════════════════════════════════════
* 4. CLASS-SIZE CONTROLS
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== 4. Class-Size Controls ==="

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & has_el

	if "`study'" == "kenya"   local cl "academycode"
	if "`study'" == "liberia" local cl "ggroup"

	gen treat_x_upper = treat * upper_group

	* ── Without class size control ──
	qui reg std_score_el treat treat_x_upper upper_group std_eb i.strata, vce(cluster `cl')
	local `study'_nocs_lower_b  : di %7.3f _b[treat]
	local `study'_nocs_lower_se : di %7.3f _se[treat]
	local `study'_nocs_lower_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_nocs_lower_pv'
	local `study'_nocs_lower_star "`r(stars)'"

	local `study'_nocs_txu_b  : di %7.3f _b[treat_x_upper]
	local `study'_nocs_txu_se : di %7.3f _se[treat_x_upper]
	local `study'_nocs_txu_pv = 2 * ttail(e(df_r), abs(_b[treat_x_upper]/_se[treat_x_upper]))
	get_stars ``study'_nocs_txu_pv'
	local `study'_nocs_txu_star "`r(stars)'"

	qui lincom treat + treat_x_upper
	local `study'_nocs_upper_b  : di %7.3f r(estimate)
	local `study'_nocs_upper_se : di %7.3f r(se)
	local `study'_nocs_upper_pv = 2 * ttail(e(df_r), abs(r(estimate)/r(se)))
	get_stars ``study'_nocs_upper_pv'
	local `study'_nocs_upper_star "`r(stars)'"
	local `study'_nocs_n = e(N)

	* ── With class size control ──
	qui reg std_score_el treat treat_x_upper upper_group std_eb csize i.strata, vce(cluster `cl')
	local `study'_cs_lower_b  : di %7.3f _b[treat]
	local `study'_cs_lower_se : di %7.3f _se[treat]
	local `study'_cs_lower_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
	get_stars ``study'_cs_lower_pv'
	local `study'_cs_lower_star "`r(stars)'"

	local `study'_cs_txu_b  : di %7.3f _b[treat_x_upper]
	local `study'_cs_txu_se : di %7.3f _se[treat_x_upper]
	local `study'_cs_txu_pv = 2 * ttail(e(df_r), abs(_b[treat_x_upper]/_se[treat_x_upper]))
	get_stars ``study'_cs_txu_pv'
	local `study'_cs_txu_star "`r(stars)'"

	qui lincom treat + treat_x_upper
	local `study'_cs_upper_b  : di %7.3f r(estimate)
	local `study'_cs_upper_se : di %7.3f r(se)
	local `study'_cs_upper_pv = 2 * ttail(e(df_r), abs(r(estimate)/r(se)))
	get_stars ``study'_cs_upper_pv'
	local `study'_cs_upper_star "`r(stars)'"

	local `study'_cs_csize_b  : di %7.3f _b[csize]
	local `study'_cs_csize_se : di %7.3f _se[csize]

	drop treat_x_upper
}

* Write table
tempname fh
file open `fh' using "$out/tab_classsize_ctrl.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Treatment Effects With and Without Class-Size Controls}" _n
file write `fh' "\label{tab:classsize_control}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\fontsize{9}{11}\selectfont" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & \multicolumn{2}{c}{Kenya} & \multicolumn{2}{c}{Liberia} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3} \cmidrule(l{3pt}r{3pt}){4-5}" _n
file write `fh' " & (1) No CS & (2) With CS & (3) No CS & (4) With CS \\" _n
file write `fh' "\midrule" _n
file write `fh' "Lower track (Treatment) & `kenya_nocs_lower_b'`kenya_nocs_lower_star' & `kenya_cs_lower_b'`kenya_cs_lower_star' & `liberia_nocs_lower_b'`liberia_nocs_lower_star' & `liberia_cs_lower_b'`liberia_cs_lower_star' \\" _n
file write `fh' " & (`kenya_nocs_lower_se') & (`kenya_cs_lower_se') & (`liberia_nocs_lower_se') & (`liberia_cs_lower_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "T `ds'\times`ds' Upper & `kenya_nocs_txu_b'`kenya_nocs_txu_star' & `kenya_cs_txu_b'`kenya_cs_txu_star' & `liberia_nocs_txu_b'`liberia_nocs_txu_star' & `liberia_cs_txu_b'`liberia_cs_txu_star' \\" _n
file write `fh' " & (`kenya_nocs_txu_se') & (`kenya_cs_txu_se') & (`liberia_nocs_txu_se') & (`liberia_cs_txu_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Upper track total & `kenya_nocs_upper_b'`kenya_nocs_upper_star' & `kenya_cs_upper_b'`kenya_cs_upper_star' & `liberia_nocs_upper_b'`liberia_nocs_upper_star' & `liberia_cs_upper_b'`liberia_cs_upper_star' \\" _n
file write `fh' " & (`kenya_nocs_upper_se') & (`kenya_cs_upper_se') & (`liberia_nocs_upper_se') & (`liberia_cs_upper_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Class size & & `kenya_cs_csize_b' & & `liberia_cs_csize_b' \\" _n
file write `fh' " & & (`kenya_cs_csize_se') & & (`liberia_cs_csize_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `kenya_nocs_n' & `kenya_nocs_n' & `liberia_nocs_n' & `liberia_nocs_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Odd columns reproduce the track-interaction specification without class size controls. "
file write `fh' "Even columns add realized reading class size as a control. "
file write `fh' "Upper track total is the sum of the Treatment and T `ds'\times`ds' Upper coefficients. "
file write `fh' "All columns control for EB ability and strata FE\@. "
file write `fh' "Standard errors are clustered at the school level in Kenya and at the school grade group level in Liberia. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_classsize_ctrl.tex"


* ═══════════════════════════════════════════════════════════════════════════
* 5. LEE (2009) BOUNDS
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== 5. Lee Bounds ==="

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp

	if "`study'" == "kenya"   local cl "academycode"
	if "`study'" == "liberia" local cl "ggroup"

	* Attrition indicator
	gen attrit = !has_el

	* Attrition rate by arm
	qui summ attrit if treat == 0
	local `study'_attr_c : di %5.3f r(mean)
	qui summ attrit if treat == 1
	local `study'_attr_t : di %5.3f r(mean)
	local `study'_attr_d : di %5.3f ``study'_attr_t' - ``study'_attr_c'

	* Sample with endline
	keep if has_el

	* Baseline ITT for reference
	qui reg std_score_el treat std_eb i.strata, vce(cluster `cl')
	local `study'_ols : di %7.3f _b[treat]

	* Lee bounds: trim from the arm with lower attrition
	* Proportion to trim = |attrition_diff| / (1 - lower_attrition)
	local attr_diff = ``study'_attr_t' - ``study'_attr_c'

	if `attr_diff' > 0 {
		* Treatment has higher attrition → trim control from below/above
		local trim_arm 0
		local trim_frac = `attr_diff' / (1 - ``study'_attr_c')
	}
	else if `attr_diff' < 0 {
		* Control has higher attrition → trim treatment from below/above
		local trim_arm 1
		local trim_frac = -`attr_diff' / (1 - ``study'_attr_t')
	}
	else {
		local trim_arm -1
		local trim_frac 0
	}

	if `trim_frac' > 0 & `trim_frac' < 1 {
		local trim_frac_f : di %5.3f `trim_frac'

		* Lower bound: trim highest scores from the less-attrited arm
		preserve
		qui summ std_score_el if treat == `trim_arm', detail
		local cutoff_hi = r(p100) - `trim_frac' * (r(p100) - r(p1))
		qui centile std_score_el if treat == `trim_arm', centile(`=100*(1-`trim_frac')')
		local cutoff_upper = r(c_1)
		drop if treat == `trim_arm' & std_score_el > `cutoff_upper'
		qui reg std_score_el treat std_eb i.strata, vce(cluster `cl')
		local `study'_lb : di %7.3f _b[treat]
		restore

		* Upper bound: trim lowest scores from the less-attrited arm
		preserve
		qui centile std_score_el if treat == `trim_arm', centile(`=100*`trim_frac'')
		local cutoff_lower = r(c_1)
		drop if treat == `trim_arm' & std_score_el < `cutoff_lower'
		qui reg std_score_el treat std_eb i.strata, vce(cluster `cl')
		local `study'_ub : di %7.3f _b[treat]
		restore
	}
	else {
		local `study'_lb "``study'_ols'"
		local `study'_ub "``study'_ols'"
	}
}

tempname fh
file open `fh' using "$out/tab_lee_bounds.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Lee (2009) Bounds on ITT Estimates}" _n
file write `fh' "\label{tab:lee_bounds}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' " & Kenya & Liberia \\" _n
file write `fh' "\midrule" _n
file write `fh' "Control attrition rate & `kenya_attr_c' & `liberia_attr_c' \\" _n
file write `fh' "Treatment attrition rate & `kenya_attr_t' & `liberia_attr_t' \\" _n
file write `fh' "Attrition diff. (T `ds'-`ds' C) & `kenya_attr_d' & `liberia_attr_d' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "OLS ITT & `kenya_ols' & `liberia_ols' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Lee lower bound & `kenya_lb' & `liberia_lb' \\" _n
file write `fh' "Lee upper bound & `kenya_ub' & `liberia_ub' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Attrition is defined as having a baseline score but no endline score. "
file write `fh' "Lee (2009) bounds trim the distribution of endline scores in the arm with lower attrition "
file write `fh' "to equalize attrition rates, producing worst-case and best-case ITT estimates. "
file write `fh' "All specifications control for EB ability and strata FE\@. "
file write `fh' "The table reports point-estimate bounds; standard errors are not shown." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_lee_bounds.tex"


di _n "{hline 70}"
di "06_robustness.do complete."
di "{hline 70}"
