/*
03_pooled_analysis.do — Pooled Kenya/Liberia/Nigeria specifications
====================================================================
Produces:
  - tab_pooled_itt.tex
  - tab_pooled_upper_lower.tex
  - tab_pooled_dispersion.tex
  - tab_pooled_peer_effects.tex
  - tab_pooled_gradient.tex

All .tex tables are written to:
  - 4_Stata2/output/
  - repo-root stata_output/
*/

di _n "{hline 70}"
di "03_pooled_analysis.do — Pooled cross-country analysis"
di "{hline 70}"
set more off

* ── Paths (standalone-safe) ─────────────────────────────────────────────
if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/03_pooled_analysis.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/03_pooled_analysis.do") {
        local root_dir = subinstr("`pwd'", "/4_Stata2", "", .)
        global root "`root_dir'"
    }
    else {
        di as err "Could not infer repo root. Set global root and rerun."
        exit 601
    }
}
global out "$root/4_Stata2/output"
global paper "$root/stata_output"
cap mkdir "$out"
cap mkdir "$paper"

* ── Helpers ──────────────────────────────────────────────────────────────
cap program drop get_stars
program define get_stars, rclass
    args pval
    local s ""
    if `pval' < 0.10 local s "*"
    if `pval' < 0.05 local s "**"
    if `pval' < 0.01 local s "***"
    return local stars "`s'"
end

cap program drop copy_to_paper
program define copy_to_paper
    args fname
    cap copy "$out/`fname'" "$paper/`fname'", replace
end

* ── Harmonize and stack three countries ─────────────────────────────────
tempfile ke lib ng pooled

* Kenya
use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el
gen byte country = 1
gen str12 country_name = "Kenya"

gen std_outcome = std_score_el
gen std_outcome_alt = std_score_el
gen std_baseline = std_eb

gen upper_group_h = upper_group
gen dev_h = dev_eb
gen peer_h = peer_eb

gen grade_h = grade
gen strata_raw = strata
gen cluster_raw = academycode
gen bl_decile_h = bl_decile

gen sample_main = !missing(std_outcome, treat, std_baseline, strata_raw, cluster_raw)
gen sample_upper = !missing(std_outcome, treat, std_baseline, upper_group_h, strata_raw, cluster_raw)
gen sample_disp = !missing(dev_h, treat, std_baseline, strata_raw, cluster_raw)
gen sample_peer = !missing(std_outcome, peer_h, bl_decile_h, treat, grade_h, strata_raw, cluster_raw)

keep studyid country country_name treat ///
    std_outcome std_outcome_alt std_baseline ///
    upper_group_h dev_h peer_h ///
    grade_h strata_raw cluster_raw bl_decile_h ///
    sample_main sample_upper sample_disp sample_peer
save `ke', replace

* Liberia
use "$out/analysis_liberia.dta", clear
keep if finsamp & has_el
gen byte country = 2
gen str12 country_name = "Liberia"

gen std_outcome = std_score_el
gen std_outcome_alt = std_score_el
gen std_baseline = std_eb

gen upper_group_h = upper_group
gen dev_h = dev_eb
gen peer_h = peer_eb

gen grade_h = grade
gen strata_raw = strata
gen cluster_raw = ggroup
gen bl_decile_h = bl_decile

gen sample_main = !missing(std_outcome, treat, std_baseline, strata_raw, cluster_raw)
gen sample_upper = !missing(std_outcome, treat, std_baseline, upper_group_h, strata_raw, cluster_raw)
gen sample_disp = !missing(dev_h, treat, std_baseline, strata_raw, cluster_raw)
gen sample_peer = !missing(std_outcome, peer_h, bl_decile_h, treat, grade_h, strata_raw, cluster_raw)

keep studyid country country_name treat ///
    std_outcome std_outcome_alt std_baseline ///
    upper_group_h dev_h peer_h ///
    grade_h strata_raw cluster_raw bl_decile_h ///
    sample_main sample_upper sample_disp sample_peer
save `lib', replace

* Nigeria
use "$out/analysis_nigeria_wide.dta", clear
drop if missing(studyid, academycode, treat)
encode constituency, gen(constit_id)
encode gradename, gen(grade_id)

qui summ bl_score if treat == 0 & !missing(bl_score)
local ng_mu = r(mean)
local ng_sd = r(sd)
gen std_baseline = (bl_score - `ng_mu') / `ng_sd' if !missing(bl_score) & `ng_sd' > 0

gen byte country = 3
gen str12 country_name = "Nigeria"

gen std_outcome = idx_t3_ete
gen std_outcome_alt = idx_t2_ete
gen upper_group_h = inlist(group_id, 2, 3) if !missing(group_id)

* Reconstruct mechanism variables in pooled file for harmonization
qui summ bl_score
gen std_bl = (bl_score - r(mean)) / r(sd) if !missing(bl_score)

gen str64 class_id = string(academycode) + "_" + ///
    cond(treat == 1, string(group_id), string(grade_id))
encode class_id, gen(class_num)

bys class_num: egen class_mean_bl = mean(std_bl)
bys class_num: egen peer_sum_bl = total(std_bl) if !missing(std_bl)
bys class_num: egen peer_n_bl = count(std_bl) if !missing(std_bl)
gen peer_lo_bl = (peer_sum_bl - std_bl) / (peer_n_bl - 1) if peer_n_bl > 1
gen dev_bl = abs(std_bl - class_mean_bl) if !missing(std_bl)
egen bl_decile = xtile(bl_score), n(10)

gen dev_h = dev_bl
gen peer_h = peer_lo_bl

gen grade_h = grade_id
gen strata_raw = constit_id * 100 + grade_id
gen cluster_raw = academycode
gen bl_decile_h = bl_decile

gen sample_main = !missing(std_outcome, treat, std_baseline, strata_raw, cluster_raw)
gen sample_upper = !missing(std_outcome, treat, std_baseline, upper_group_h, strata_raw, cluster_raw)
gen sample_disp = !missing(dev_h, treat, std_baseline, strata_raw, cluster_raw)
gen sample_peer = !missing(std_outcome, peer_h, bl_decile_h, treat, grade_h, strata_raw, cluster_raw)

keep studyid country country_name treat ///
    std_outcome std_outcome_alt std_baseline ///
    upper_group_h dev_h peer_h ///
    grade_h strata_raw cluster_raw bl_decile_h ///
    sample_main sample_upper sample_disp sample_peer
save `ng', replace

* Stack
use `ke', clear
append using `lib'
append using `ng'

egen country_strata = group(country strata_raw)
egen cluster_id = group(country cluster_raw)
egen dt_cell = group(country bl_decile_h treat grade_h)
gen treat_x_upper = treat * upper_group_h

save `pooled', replace
di "  Harmonized pooled sample built."

* ─────────────────────────────────────────────────────────────────────────
* Table 0: Careful pooled estimands and heterogeneity diagnostics
* ─────────────────────────────────────────────────────────────────────────
use `pooled', clear
gen rho_c = .
replace rho_c = 0.533 if country == 1
replace rho_c = 0.055 if country == 2
replace rho_c = 0.121 if country == 3

gen omega_c = .
replace omega_c = 1.000 if country == 1
replace omega_c = 1.000 if country == 2
replace omega_c = 0.841 if country == 3

gen tau_c = .
replace tau_c = 0.500 if country == 1
replace tau_c = 0.385 if country == 2
replace tau_c = 0.312 if country == 3

gen complement_c = rho_c * omega_c * tau_c
gen treat_x_rho = treat * rho_c
gen treat_x_tau = treat * tau_c
gen treat_x_comp = treat * complement_c

* Student-weighted individual-participant-data estimate.
qui reg std_outcome treat i.country#c.std_baseline i.country_strata ///
    if sample_main == 1, vce(cluster cluster_id)
local sw_b = _b[treat]
local sw_se = _se[treat]
local sw_n = e(N)
local sw_p = 2 * ttail(e(df_r), abs(`sw_b' / `sw_se'))
get_stars `sw_p'
local sw_st "`r(stars)'"
local sw_b_s : di %7.3f `sw_b'
local sw_se_s : di %7.3f `sw_se'
local sw_p_s : di %7.3f `sw_p'

* Experiment-balanced individual-participant-data estimate: each experiment
* receives total weight one-third, regardless of student sample size.
bys country: egen n_country_main = total(sample_main == 1)
gen exp_bal_w = 1 / n_country_main if sample_main == 1
qui reg std_outcome treat i.country#c.std_baseline i.country_strata [aw=exp_bal_w] ///
    if sample_main == 1, vce(cluster cluster_id)
local eb_b = _b[treat]
local eb_se = _se[treat]
local eb_p = 2 * ttail(e(df_r), abs(`eb_b' / `eb_se'))
get_stars `eb_p'
local eb_st "`r(stars)'"
local eb_b_s : di %7.3f `eb_b'
local eb_se_s : di %7.3f `eb_se'
local eb_p_s : di %7.3f `eb_p'

* Study-specific effects from a single stacked regression.
qui reg std_outcome i.treat##ib1.country i.country#c.std_baseline i.country_strata ///
    if sample_main == 1, vce(cluster cluster_id)
local ke_b = _b[1.treat]
local ke_se = _se[1.treat]
local ke_p = 2 * ttail(e(df_r), abs(`ke_b' / `ke_se'))
get_stars `ke_p'
local ke_st "`r(stars)'"
local ke_b_s : di %7.3f `ke_b'
local ke_se_s : di %7.3f `ke_se'

qui lincom 1.treat + 1.treat#2.country
local lib_b = r(estimate)
local lib_se = r(se)
local lib_p = 2 * ttail(e(df_r), abs(`lib_b' / `lib_se'))
get_stars `lib_p'
local lib_st "`r(stars)'"
local lib_b_s : di %7.3f `lib_b'
local lib_se_s : di %7.3f `lib_se'

qui lincom 1.treat + 1.treat#3.country
local ng_b = r(estimate)
local ng_se = r(se)
local ng_p = 2 * ttail(e(df_r), abs(`ng_b' / `ng_se'))
get_stars `ng_p'
local ng_st "`r(stars)'"
local ng_b_s : di %7.3f `ng_b'
local ng_se_s : di %7.3f `ng_se'
local study_n = e(N)

qui test 1.treat#2.country 1.treat#3.country
local joint_het_p = r(p)
local joint_het_p_s : di %7.3f `joint_het_p'

* Study-level fixed-effect and random-effects meta-analytic summaries. These
* use the three study-specific estimates, not individual observations.
local w_ke = 1 / (`ke_se'^2)
local w_lib = 1 / (`lib_se'^2)
local w_ng = 1 / (`ng_se'^2)
local w_sum = `w_ke' + `w_lib' + `w_ng'
local fe_b = (`w_ke' * `ke_b' + `w_lib' * `lib_b' + `w_ng' * `ng_b') / `w_sum'
local fe_se = sqrt(1 / `w_sum')
local fe_p = 2 * normal(-abs(`fe_b' / `fe_se'))
get_stars `fe_p'
local fe_st "`r(stars)'"
local fe_b_s : di %7.3f `fe_b'
local fe_se_s : di %7.3f `fe_se'
local fe_p_s : di %7.3f `fe_p'

local q = `w_ke' * (`ke_b' - `fe_b')^2 + `w_lib' * (`lib_b' - `fe_b')^2 + `w_ng' * (`ng_b' - `fe_b')^2
local q_p = chi2tail(2, `q')
local denom = `w_sum' - (`w_ke'^2 + `w_lib'^2 + `w_ng'^2) / `w_sum'
local tau2 = max(0, (`q' - 2) / `denom')
local i2 = max(0, (`q' - 2) / `q') * 100

local rw_ke = 1 / (`ke_se'^2 + `tau2')
local rw_lib = 1 / (`lib_se'^2 + `tau2')
local rw_ng = 1 / (`ng_se'^2 + `tau2')
local rw_sum = `rw_ke' + `rw_lib' + `rw_ng'
local re_b = (`rw_ke' * `ke_b' + `rw_lib' * `lib_b' + `rw_ng' * `ng_b') / `rw_sum'
local re_se_dl = sqrt(1 / `rw_sum')
local hk_q = `rw_ke' * (`ke_b' - `re_b')^2 + `rw_lib' * (`lib_b' - `re_b')^2 + `rw_ng' * (`ng_b' - `re_b')^2
local re_se = sqrt(max(1, `hk_q' / 2) / `rw_sum')
local re_p = 2 * ttail(2, abs(`re_b' / `re_se'))
get_stars `re_p'
local re_st "`r(stars)'"
local re_b_s : di %7.3f `re_b'
local re_se_s : di %7.3f `re_se'
local re_p_s : di %7.3f `re_p'
local q_s : di %7.3f `q'
local q_p_s : di %7.3f `q_p'
local i2_s : di %7.1f `i2'
local tau2_s : di %7.3f `tau2'

* Primitive-score gradient is retained only as a descriptive check. Since the
* primitive score is country-level, its slope has three support points.
qui reg std_outcome treat treat_x_comp i.country#c.std_baseline i.country_strata ///
    if sample_main == 1 & !missing(complement_c), vce(cluster cluster_id)
local comp_slope = _b[treat_x_comp]
local comp_slope_se = _se[treat_x_comp]
local comp_slope_s : di %7.3f `comp_slope'
local comp_slope_se_s : di %7.3f `comp_slope_se'

qui summ complement_c if sample_main == 1
local comp_min = r(min)
local comp_max = r(max)
local eff_low = _b[treat] + _b[treat_x_comp] * `comp_min'
local eff_high = _b[treat] + _b[treat_x_comp] * `comp_max'
local comp_low_s : di %7.3f `eff_low'
local comp_high_s : di %7.3f `eff_high'

tempname fh
file open `fh' using "$out/tab_pooled_power.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Pooled and Meta-Analytic Treatment Effects Across Experiments}" _n
file write `fh' "\label{tab:pooled_power}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\footnotesize" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "Estimand or diagnostic & Estimate & SE / statistic \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{3}{l}{\textit{Common-effect estimands}} \\" _n
file write `fh' "Student-weighted IPD & `sw_b_s'`sw_st' & (`sw_se_s') \\" _n
file write `fh' "Experiment-balanced IPD & `eb_b_s'`eb_st' & (`eb_se_s') \\" _n
file write `fh' "Fixed-effect meta-analysis & `fe_b_s'`fe_st' & (`fe_se_s') \\" _n
file write `fh' "Random-effects meta-analysis & `re_b_s'`re_st' & (`re_se_s') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{3}{l}{\textit{Study-specific effects from stacked IPD}} \\" _n
file write `fh' "Kenya & `ke_b_s'`ke_st' & (`ke_se_s') \\" _n
file write `fh' "Liberia & `lib_b_s'`lib_st' & (`lib_se_s') \\" _n
file write `fh' "Nigeria & `ng_b_s'`ng_st' & (`ng_se_s') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{3}{l}{\textit{Heterogeneity and primitive-score diagnostics}} \\" _n
file write `fh' "Treatment-effect heterogeneity test &  & p = `joint_het_p_s' \\" _n
file write `fh' "Meta-analysis Q statistic &  & Q = `q_s', p = `q_p_s' \\" _n
file write `fh' "I-squared / tau-squared &  & `i2_s'\% / `tau2_s' \\" _n
file write `fh' "Treatment $\times$ ($\rho\omega\tau$) slope & `comp_slope_s' & (`comp_slope_se_s') \\" _n
file write `fh' "Implied effect: lowest/highest score & `comp_low_s' / `comp_high_s' & descriptive \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Student observations / studies & `sw_n' & 3 \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item Notes: IPD = individual participant data. Student-weighted IPD weights each student equally; experiment-balanced IPD weights each experiment equally. Meta-analytic rows pool the three study-specific estimates, with the random-effects SE using a Hartung-Knapp-style small-sample adjustment. All IPD specifications include country-specific baseline slopes and country-nested strata FE, with SEs clustered at harmonized assignment clusters. The primitive-score slope is descriptive because $\rho\omega\tau$ varies only at the experiment level." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_pooled_power.tex
di "  -> tab_pooled_power.tex"

* ─────────────────────────────────────────────────────────────────────────
* Table 1: Pooled ITT
* ─────────────────────────────────────────────────────────────────────────
foreach c in 1 2 3 0 {
    preserve
    use `pooled', clear
    if `c' > 0 keep if country == `c'

    qui reg std_outcome treat i.country#c.std_baseline i.country_strata ///
        if sample_main == 1, vce(cluster cluster_id)
    local itt_b`c' : di %7.3f _b[treat]
    local itt_se`c' : di %7.3f _se[treat]
    local itt_n`c' = e(N)
    local itt_p`c' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `itt_p`c''
    local itt_st`c' "`r(stars)'"

    qui summ std_outcome if sample_main == 1 & treat == 0
    local itt_cm`c' : di %7.3f r(mean)
    restore
}

* Robustness pooled ITT with Nigeria T2 ETE index
use `pooled', clear
gen std_outcome_rb = cond(country == 3, std_outcome_alt, std_outcome)
qui reg std_outcome_rb treat i.country#c.std_baseline i.country_strata ///
    if !missing(std_outcome_rb, treat, std_baseline, country_strata, cluster_id), ///
    vce(cluster cluster_id)
local itt_rb_b : di %7.3f _b[treat]
local itt_rb_se : di %7.3f _se[treat]
local itt_rb_p = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
get_stars `itt_rb_p'
local itt_rb_st "`r(stars)'"

tempname fh
file open `fh' using "$out/tab_pooled_itt.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Pooled ITT Across Kenya, Liberia, and Nigeria}" _n
file write `fh' "\label{tab:pooled_itt}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) & (2) & (3) & (4) \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' " & Kenya & Liberia & Nigeria & Pooled \\" _n
file write `fh' "\midrule" _n
file write `fh' "Treatment & `itt_b1'`itt_st1' & `itt_b2'`itt_st2' & `itt_b3'`itt_st3' & `itt_b0'`itt_st0' \\" _n
file write `fh' " & (`itt_se1') & (`itt_se2') & (`itt_se3') & (`itt_se0') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Control Mean & `itt_cm1' & `itt_cm2' & `itt_cm3' & `itt_cm0' \\" _n
file write `fh' "N & `itt_n1' & `itt_n2' & `itt_n3' & `itt_n0' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Pooled ITT (Nigeria T2 ETE alt) & \multicolumn{3}{c}{ } & `itt_rb_b'`itt_rb_st' \\" _n
file write `fh' " & \multicolumn{3}{c}{ } & (`itt_rb_se') \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Outcome is standardized endline score for Kenya/Liberia and T3 ETE math+numeracy index for Nigeria. " _n
file write `fh' "Controls: country-specific baseline slopes and country-nested strata FE. " _n
file write `fh' "SEs clustered at country-specific cluster units (school for Kenya, school\mbox{-}grade\mbox{-}group for Liberia, academy for Nigeria). " _n
file write `fh' "Final row shows pooled robustness replacing Nigeria T3 ETE with T2 ETE index. " _n
file write `fh' "***, **, and * indicate 1\%, 5\%, and 10\% significance." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_pooled_itt.tex
di "  -> tab_pooled_itt.tex"

* ─────────────────────────────────────────────────────────────────────────
* Table 2: Pooled Upper vs Lower
* ─────────────────────────────────────────────────────────────────────────
foreach c in 1 2 3 0 {
    preserve
    use `pooled', clear
    if `c' > 0 keep if country == `c'

    qui reg std_outcome treat treat_x_upper upper_group_h i.country#c.std_baseline i.country_strata ///
        if sample_upper == 1, vce(cluster cluster_id)

    local ul_low_b`c' : di %7.3f _b[treat]
    local ul_low_se`c' : di %7.3f _se[treat]
    local ul_low_p`c' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `ul_low_p`c''
    local ul_low_st`c' "`r(stars)'"

    local ul_txu_b`c' : di %7.3f _b[treat_x_upper]
    local ul_txu_se`c' : di %7.3f _se[treat_x_upper]
    local ul_txu_p`c' = 2 * ttail(e(df_r), abs(_b[treat_x_upper] / _se[treat_x_upper]))
    get_stars `ul_txu_p`c''
    local ul_txu_st`c' "`r(stars)'"

    qui lincom treat + treat_x_upper
    local ul_up_b`c' : di %7.3f r(estimate)
    local ul_up_se`c' : di %7.3f r(se)
    local ul_up_p`c' = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))
    get_stars `ul_up_p`c''
    local ul_up_st`c' "`r(stars)'"

    local ul_n`c' = e(N)
    restore
}

tempname fh
file open `fh' using "$out/tab_pooled_upper_lower.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Treatment Effects by Track Position Across Countries}" _n
file write `fh' "\label{tab:pooled_upper_lower}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) & (2) & (3) \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
file write `fh' " & Kenya & Liberia & Nigeria \\" _n
file write `fh' "\midrule" _n
file write `fh' "Lower-track effect & `ul_low_b1'`ul_low_st1' & `ul_low_b2'`ul_low_st2' & `ul_low_b3'`ul_low_st3' \\" _n
file write `fh' " & (`ul_low_se1') & (`ul_low_se2') & (`ul_low_se3') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Higher-track differential & `ul_txu_b1'`ul_txu_st1' & `ul_txu_b2'`ul_txu_st2' & `ul_txu_b3'`ul_txu_st3' \\" _n
file write `fh' " & (`ul_txu_se1') & (`ul_txu_se2') & (`ul_txu_se3') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Higher-track effect & `ul_up_b1'`ul_up_st1' & `ul_up_b2'`ul_up_st2' & `ul_up_b3'`ul_up_st3' \\" _n
file write `fh' " & (`ul_up_se1') & (`ul_up_se2') & (`ul_up_se3') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `ul_n1' & `ul_n2' & `ul_n3' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Each column estimates a country-specific treatment-by-track-position interaction. The higher track is the upper reading group in Kenya and Liberia; in Nigeria it is the preferred two-group collapse, Blue/Yellow (\texttt{group\_id} = 2 or 3). " _n
file write `fh' "Controls are country-specific baseline slopes and country-nested strata fixed effects. SEs are clustered at the harmonized assignment cluster." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_pooled_upper_lower.tex
di "  -> tab_pooled_upper_lower.tex"

* ─────────────────────────────────────────────────────────────────────────
* Table 3: Pooled Dispersion First Stage
* ─────────────────────────────────────────────────────────────────────────
foreach c in 1 2 3 0 {
    preserve
    use `pooled', clear
    if `c' > 0 keep if country == `c'

    qui reg dev_h treat i.country#c.std_baseline i.country_strata ///
        if sample_disp == 1, vce(cluster cluster_id)

    local disp_b`c' : di %7.3f _b[treat]
    local disp_se`c' : di %7.3f _se[treat]
    local disp_n`c' = e(N)
    local disp_p`c' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `disp_p`c''
    local disp_st`c' "`r(stars)'"
    restore
}

tempname fh
file open `fh' using "$out/tab_pooled_dispersion.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Pooled First Stage: Effect on Within-Class Dispersion}" _n
file write `fh' "\label{tab:pooled_dispersion}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) & (2) & (3) & (4) \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' " & Kenya & Liberia & Nigeria & Pooled \\" _n
file write `fh' "\midrule" _n
file write `fh' "Treatment & `disp_b1'`disp_st1' & `disp_b2'`disp_st2' & `disp_b3'`disp_st3' & `disp_b0'`disp_st0' \\" _n
file write `fh' " & (`disp_se1') & (`disp_se2') & (`disp_se3') & (`disp_se0') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `disp_n1' & `disp_n2' & `disp_n3' & `disp_n0' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Harmonized dispersion measure is absolute deviation from classroom mean baseline ability. " _n
file write `fh' "Nigeria uses \texttt{dev\_bl}; Kenya/Liberia use \texttt{dev\_eb}. Controls are country-specific baseline slopes and country-nested strata fixed effects. SEs are clustered at the harmonized assignment cluster." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_pooled_dispersion.tex
di "  -> tab_pooled_dispersion.tex"

* ─────────────────────────────────────────────────────────────────────────
* Table 4: Pooled Peer Effects (BH-style)
* ─────────────────────────────────────────────────────────────────────────
foreach c in 1 2 3 0 {
    preserve
    use `pooled', clear
    if `c' > 0 keep if country == `c'

    qui reg std_outcome peer_h i.dt_cell i.country_strata ///
        if sample_peer == 1, vce(cluster cluster_id)

    local peer_b`c' : di %7.3f _b[peer_h]
    local peer_se`c' : di %7.3f _se[peer_h]
    local peer_n`c' = e(N)
    local peer_p`c' = 2 * ttail(e(df_r), abs(_b[peer_h] / _se[peer_h]))
    get_stars `peer_p`c''
    local peer_st`c' "`r(stars)'"
    restore
}

tempname fh
file open `fh' using "$out/tab_pooled_peer_effects.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Pooled Peer Composition Effects (BH-style)}" _n
file write `fh' "\label{tab:pooled_peer_effects}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) & (2) & (3) & (4) \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' " & Kenya & Liberia & Nigeria & Pooled \\" _n
file write `fh' "\midrule" _n
file write `fh' "Peer baseline ability (leave-out mean) & `peer_b1'`peer_st1' & `peer_b2'`peer_st2' & `peer_b3'`peer_st3' & `peer_b0'`peer_st0' \\" _n
file write `fh' " & (`peer_se1') & (`peer_se2') & (`peer_se3') & (`peer_se0') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `peer_n1' & `peer_n2' & `peer_n3' & `peer_n0' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Borusyak-Hull-style reduced form with baseline-decile $\times$ treatment $\times$ grade FE and country-nested strata FE. " _n
file write `fh' "Peer variable is harmonized leave-self-out baseline ability (\texttt{peer\_eb} for Kenya/Liberia, \texttt{peer\_lo\_bl} for Nigeria). SEs are clustered at the harmonized assignment cluster." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_pooled_peer_effects.tex
di "  -> tab_pooled_peer_effects.tex"

* ─────────────────────────────────────────────────────────────────────────
* Table 5: Implementation quality gradient summary
* ─────────────────────────────────────────────────────────────────────────
use `pooled', clear
gen disp_fs_country = .
replace disp_fs_country = `disp_b1' if country == 1
replace disp_fs_country = `disp_b2' if country == 2
replace disp_fs_country = `disp_b3' if country == 3
gen treat_x_disp_fs = treat * disp_fs_country

qui reg std_outcome treat treat_x_disp_fs i.country#c.std_baseline i.country_strata ///
    if sample_main == 1 & !missing(disp_fs_country), vce(cluster cluster_id)

local grad_t_b : di %7.3f _b[treat]
local grad_t_se : di %7.3f _se[treat]
local grad_t_p = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
get_stars `grad_t_p'
local grad_t_st "`r(stars)'"

local grad_x_b : di %7.3f _b[treat_x_disp_fs]
local grad_x_se : di %7.3f _se[treat_x_disp_fs]
local grad_x_p = 2 * ttail(e(df_r), abs(_b[treat_x_disp_fs] / _se[treat_x_disp_fs]))
get_stars `grad_x_p'
local grad_x_st "`r(stars)'"

tempname fh
file open `fh' using "$out/tab_pooled_gradient.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Cross-Country Gradient in Implementation Quality and Effects}" _n
file write `fh' "\label{tab:pooled_gradient}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & Kenya & Liberia & Nigeria \\" _n
file write `fh' "\midrule" _n
file write `fh' "Assignment mechanism & Sharp cutoffs & Moderate & Discretionary/noisy \\" _n
file write `fh' "Dispersion first stage & `disp_b1'`disp_st1' & `disp_b2'`disp_st2' & `disp_b3'`disp_st3' \\" _n
file write `fh' "Average ITT & `itt_b1'`itt_st1' & `itt_b2'`itt_st2' & `itt_b3'`itt_st3' \\" _n
file write `fh' "Upper track total & `ul_up_b1'`ul_up_st1' & `ul_up_b2'`ul_up_st2' & `ul_up_b3'`ul_up_st3' \\" _n
file write `fh' "Peer effect (BH-style) & `peer_b1'`peer_st1' & `peer_b2'`peer_st2' & `peer_b3'`peer_st3' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Gradient regression (pooled microdata): outcome on Treatment and Treatment $\times$ country-level dispersion first stage. " _n
file write `fh' "Treatment coeff = `grad_t_b'`grad_t_st' (`grad_t_se'); interaction coeff = `grad_x_b'`grad_x_st' (`grad_x_se'). " _n
file write `fh' "Interpretation is suggestive only (3 countries)." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_pooled_gradient.tex
di "  -> tab_pooled_gradient.tex"

di _n "{hline 70}"
di "Pooled cross-country analysis complete."
di "{hline 70}"
