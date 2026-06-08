/*
02_main_analysis.do — Core treatment effect estimates with LaTeX output
=======================================================================
Produces: ITT table, upper/lower table, dispersion table, peer effects table.
*/

di _n "{hline 70}"
di "02_main_analysis.do — Main analysis"
di "{hline 70}"


* ═══════════════════════════════════════════════════════════════════════════
* HELPER: stars from p value
* ═══════════════════════════════════════════════════════════════════════════

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
* A. LIBERIA: estimate and store
* ═══════════════════════════════════════════════════════════════════════════

use "$out/analysis_liberia.dta", clear
keep if finsamp & has_el

* ITT
qui reg std_score_el treat std_eb i.strata, vce(cluster ggroup)
local lib_itt_b  : di %7.3f _b[treat]
local lib_itt_se : di %7.3f _se[treat]
local lib_itt_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `lib_itt_pv'
local lib_itt_star "`r(stars)'"
local lib_itt_n  = e(N)
qui summ std_score_el if treat == 0
local lib_itt_cm : di %7.3f r(mean)

* Upper/Lower
gen treat_x_upper = treat * upper_group
qui reg std_score_el treat treat_x_upper upper_group std_eb i.strata, vce(cluster ggroup)
local lib_lower_b  : di %7.3f _b[treat]
local lib_lower_se : di %7.3f _se[treat]
local lib_lower_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `lib_lower_pv'
local lib_lower_star "`r(stars)'"

local lib_txu_b  : di %7.3f _b[treat_x_upper]
local lib_txu_se : di %7.3f _se[treat_x_upper]
local lib_txu_pv = 2 * ttail(e(df_r), abs(_b[treat_x_upper]/_se[treat_x_upper]))
get_stars `lib_txu_pv'
local lib_txu_star "`r(stars)'"

qui lincom treat + treat_x_upper
local lib_upper_b  : di %7.3f r(estimate)
local lib_upper_se : di %7.3f r(se)
local lib_upper_pv = 2 * ttail(e(df_r), abs(r(estimate)/r(se)))
get_stars `lib_upper_pv'
local lib_upper_star "`r(stars)'"
local lib_ul_n = e(N)

* Dispersion
qui reg dev_eb treat std_eb i.strata, vce(cluster ggroup)
local lib_disp_b  : di %7.3f _b[treat]
local lib_disp_se : di %7.3f _se[treat]
local lib_disp_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `lib_disp_pv'
local lib_disp_star "`r(stars)'"
local lib_disp_n = e(N)

* Peer effects (BH)
egen dt_cell = group(bl_decile treat grade)
qui reg std_score_el peer_eb i.dt_cell i.strata, vce(cluster ggroup)
local lib_bh_b  : di %7.3f _b[peer_eb]
local lib_bh_se : di %7.3f _se[peer_eb]
local lib_bh_pv = 2 * ttail(e(df_r), abs(_b[peer_eb]/_se[peer_eb]))
get_stars `lib_bh_pv'
local lib_bh_star "`r(stars)'"
local lib_bh_n = e(N)


* ═══════════════════════════════════════════════════════════════════════════
* B. KENYA: estimate and store
* ═══════════════════════════════════════════════════════════════════════════

use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el

* ITT
qui reg std_score_el treat std_eb i.strata, vce(cluster academycode)
local ke_itt_b  : di %7.3f _b[treat]
local ke_itt_se : di %7.3f _se[treat]
local ke_itt_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `ke_itt_pv'
local ke_itt_star "`r(stars)'"
local ke_itt_n  = e(N)
qui summ std_score_el if treat == 0
local ke_itt_cm : di %7.3f r(mean)

* Upper/Lower
gen treat_x_upper = treat * upper_group
qui reg std_score_el treat treat_x_upper upper_group std_eb i.strata, vce(cluster academycode)
local ke_lower_b  : di %7.3f _b[treat]
local ke_lower_se : di %7.3f _se[treat]
local ke_lower_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `ke_lower_pv'
local ke_lower_star "`r(stars)'"

local ke_txu_b  : di %7.3f _b[treat_x_upper]
local ke_txu_se : di %7.3f _se[treat_x_upper]
local ke_txu_pv = 2 * ttail(e(df_r), abs(_b[treat_x_upper]/_se[treat_x_upper]))
get_stars `ke_txu_pv'
local ke_txu_star "`r(stars)'"

qui lincom treat + treat_x_upper
local ke_upper_b  : di %7.3f r(estimate)
local ke_upper_se : di %7.3f r(se)
local ke_upper_pv = 2 * ttail(e(df_r), abs(r(estimate)/r(se)))
get_stars `ke_upper_pv'
local ke_upper_star "`r(stars)'"
local ke_ul_n = e(N)

* Dispersion
qui reg dev_eb treat std_eb i.strata, vce(cluster academycode)
local ke_disp_b  : di %7.3f _b[treat]
local ke_disp_se : di %7.3f _se[treat]
local ke_disp_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `ke_disp_pv'
local ke_disp_star "`r(stars)'"
local ke_disp_n = e(N)

* Peer effects (BH)
egen dt_cell = group(bl_decile treat grade)
qui reg std_score_el peer_eb i.dt_cell i.strata, vce(cluster academycode)
local ke_bh_b  : di %7.3f _b[peer_eb]
local ke_bh_se : di %7.3f _se[peer_eb]
local ke_bh_pv = 2 * ttail(e(df_r), abs(_b[peer_eb]/_se[peer_eb]))
get_stars `ke_bh_pv'
local ke_bh_star "`r(stars)'"
local ke_bh_n = e(N)


* ═══════════════════════════════════════════════════════════════════════════
* C. WRITE LaTeX TABLES
* ═══════════════════════════════════════════════════════════════════════════

* ── ITT table ────────────────────────────────────────────────────────────
tempname fh
file open `fh' using "$out/tab_itt.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Effect of Ability Grouping on Test Scores}" _n
file write `fh' "\label{tab:itt}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{2}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3}" _n
file write `fh' " & \multicolumn{1}{c}{Kenya} & \multicolumn{1}{c}{Liberia} \\" _n
file write `fh' "\midrule" _n
file write `fh' "Treatment & `ke_itt_b'`ke_itt_star' & `lib_itt_b'`lib_itt_star' \\" _n
file write `fh' " & (`ke_itt_se') & (`lib_itt_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Control Mean & `ke_itt_cm' & `lib_itt_cm' \\" _n
file write `fh' "N & `ke_itt_n' & `lib_itt_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Dependent variable is standardized endline score. All specifications "
file write `fh' "control for EB ability and strata FE\@. Standard errors are clustered at the school level in Kenya "
file write `fh' "and at the school grade group level in Liberia. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_itt.tex"


* ── Upper/Lower table ────────────────────────────────────────────────────
tempname fh
file open `fh' using "$out/tab_upper_lower.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Treatment Effects by Track}" _n
file write `fh' "\label{tab:upper_lower}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{2}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3}" _n
file write `fh' " & \multicolumn{1}{c}{Kenya} & \multicolumn{1}{c}{Liberia} \\" _n
file write `fh' "\midrule" _n
file write `fh' "Lower track (Treatment) & `ke_lower_b'`ke_lower_star' & `lib_lower_b'`lib_lower_star' \\" _n
file write `fh' " & (`ke_lower_se') & (`lib_lower_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "T `ds'\times`ds' Upper & `ke_txu_b'`ke_txu_star' & `lib_txu_b'`lib_txu_star' \\" _n
file write `fh' " & (`ke_txu_se') & (`lib_txu_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Upper track total & `ke_upper_b'`ke_upper_star' & `lib_upper_b'`lib_upper_star' \\" _n
file write `fh' " & (`ke_upper_se') & (`lib_upper_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `ke_ul_n' & `lib_ul_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Upper track total is Treatment + T `ds'\times`ds' Upper. Controls: EB ability, "
file write `fh' "strata FE\@. Standard errors are clustered at the school level in Kenya and at the school grade group level in Liberia. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_upper_lower.tex"


* ── Dispersion table ─────────────────────────────────────────────────────
tempname fh
file open `fh' using "$out/tab_dispersion.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Effect on Within-Class Ability Dispersion}" _n
file write `fh' "\label{tab:dispersion}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{2}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3}" _n
file write `fh' " & \multicolumn{1}{c}{Kenya} & \multicolumn{1}{c}{Liberia} \\" _n
file write `fh' "\midrule" _n
file write `fh' "Treatment & `ke_disp_b'`ke_disp_star' & `lib_disp_b'`lib_disp_star' \\" _n
file write `fh' " & (`ke_disp_se') & (`lib_disp_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `ke_disp_n' & `lib_disp_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Dependent variable is `ds'|\hat{\theta}_i - \bar{\theta}_k|`ds': "
file write `fh' "absolute deviation of EB ability from class mean. Controls: EB ability, "
file write `fh' "strata FE\@. Standard errors are clustered at the school level in Kenya and at the school grade group level in Liberia. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_dispersion.tex"


* ── Peer effects table ───────────────────────────────────────────────────
tempname fh
file open `fh' using "$out/tab_peer_effects.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Approximate Peer/Rank Diagnostic (Borusyak--Hull Control Function)}" _n
file write `fh' "\label{tab:peer_effects}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{2}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3}" _n
file write `fh' " & \multicolumn{1}{c}{Kenya} & \multicolumn{1}{c}{Liberia} \\" _n
file write `fh' "\midrule" _n
file write `fh' "Peer mean EB ability & `ke_bh_b'`ke_bh_star' & `lib_bh_b'`lib_bh_star' \\" _n
file write `fh' " & (`ke_bh_se') & (`lib_bh_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `ke_bh_n' & `lib_bh_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Dependent variable is standardized endline score. Peer mean EB ability "
file write `fh' "is the mean of classmates' EB ability, excluding the focal student. "
file write `fh' "This is the approximate control function implementation: controls include baseline-decile `ds'\times`ds' treatment `ds'\times`ds' grade FE and strata FE\@. Standard errors are clustered at the school level in Kenya and at the school grade group level in Liberia. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_peer_effects.tex"


di _n "{hline 70}"
di "SUMMARY: ITT Estimates"
di "{hline 70}"
di "  Kenya ITT:   `ke_itt_b'`ke_itt_star' (`ke_itt_se')"
di "  Liberia ITT: `lib_itt_b'`lib_itt_star' (`lib_itt_se')"
di _n "Main analysis complete."
