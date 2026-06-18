/*
09_multiplicity_disclosure.do — PAP/status and multiplicity disclosure
======================================================================
Produces:
  - tab_multiplicity_disclosure.tex

The table separates primary endpoint estimates from support-aware
heterogeneity and mechanism diagnostics, and reports Benjamini-Hochberg
q-values within each displayed family.
*/

di _n "{hline 70}"
di "09_multiplicity_disclosure.do — PAP/status and multiplicity disclosure"
di "{hline 70}"
set more off

if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/09_multiplicity_disclosure.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/09_multiplicity_disclosure.do") {
        local root_dir = subinstr("`pwd'", "/4_Stata2", "", .)
        global root "`root_dir'"
    }
    else {
        di as err "Could not infer repo root. Set global root and rerun."
        exit 601
    }
}
if "$out" == ""   global out "$root/4_Stata2/output"
if "$paper" == "" global paper "$root/stata_output"
cap mkdir "$out"
cap mkdir "$paper"

cap program drop copy_to_paper
program define copy_to_paper
    args fname
    cap copy "$out/`fname'" "$paper/`fname'", replace
end

tempfile results ke lib ng pooled
tempname pf
postfile `pf' str28 family str60 test str30 status double estimate se pval N using `results', replace

* -------------------------------------------------------------------------
* Harmonized pooled file matching 03_pooled_analysis.do
* -------------------------------------------------------------------------

use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el
gen byte country = 1
gen str12 country_name = "Kenya"
gen std_outcome = std_score_el
gen std_baseline = std_eb
gen upper_group_h = upper_group
gen strata_raw = strata
gen cluster_raw = academycode
gen sample_main = !missing(std_outcome, treat, std_baseline, strata_raw, cluster_raw)
gen sample_upper = !missing(std_outcome, treat, std_baseline, upper_group_h, strata_raw, cluster_raw)
keep studyid country country_name treat std_outcome std_baseline upper_group_h strata_raw cluster_raw sample_main sample_upper
save `ke', replace

use "$out/analysis_liberia.dta", clear
keep if finsamp & has_el
gen byte country = 2
gen str12 country_name = "Liberia"
gen std_outcome = std_score_el
gen std_baseline = std_eb
gen upper_group_h = upper_group
gen strata_raw = strata
gen cluster_raw = ggroup
gen sample_main = !missing(std_outcome, treat, std_baseline, strata_raw, cluster_raw)
gen sample_upper = !missing(std_outcome, treat, std_baseline, upper_group_h, strata_raw, cluster_raw)
keep studyid country country_name treat std_outcome std_baseline upper_group_h strata_raw cluster_raw sample_main sample_upper
save `lib', replace

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
gen upper_group_h = inlist(group_id, 2, 3) if !missing(group_id)
gen strata_raw = constit_id * 100 + grade_id
gen cluster_raw = academycode
gen sample_main = !missing(std_outcome, treat, std_baseline, strata_raw, cluster_raw)
gen sample_upper = !missing(std_outcome, treat, std_baseline, upper_group_h, strata_raw, cluster_raw)
keep studyid country country_name treat std_outcome std_baseline upper_group_h strata_raw cluster_raw sample_main sample_upper
save `ng', replace

use `ke', clear
append using `lib'
append using `ng'
egen country_strata = group(country strata_raw)
egen cluster_id = group(country cluster_raw)
gen treat_x_upper = treat * upper_group_h
save `pooled', replace

* -------------------------------------------------------------------------
* Family 1: country primary endpoints
* -------------------------------------------------------------------------

forvalues c = 1/3 {
    use `pooled', clear
    keep if country == `c'
    qui reg std_outcome treat c.std_baseline i.country_strata if sample_main == 1, vce(cluster cluster_id)
    local b = _b[treat]
    local se = _se[treat]
    local p = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    local n = e(N)
    local cname = country_name[1]
    post `pf' ("Primary endpoints") ("`cname' primary ITT") ("Primary") (`b') (`se') (`p') (`n')
}

* -------------------------------------------------------------------------
* Family 2: primary-endpoint track-position heterogeneity
* -------------------------------------------------------------------------

forvalues c = 1/3 {
    use `pooled', clear
    keep if country == `c'
    qui reg std_outcome treat treat_x_upper upper_group_h c.std_baseline i.country_strata ///
        if sample_upper == 1, vce(cluster cluster_id)
    local cname = country_name[1]

    local b = _b[treat]
    local se = _se[treat]
    local p = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    local n = e(N)
    post `pf' ("Track-position") ("`cname': lower-track effect") ("Heterogeneity") (`b') (`se') (`p') (`n')

    local b = _b[treat_x_upper]
    local se = _se[treat_x_upper]
    local p = 2 * ttail(e(df_r), abs(_b[treat_x_upper] / _se[treat_x_upper]))
    post `pf' ("Track-position") ("`cname': higher-track differential") ("Heterogeneity") (`b') (`se') (`p') (`n')

    qui lincom treat + treat_x_upper
    local b = r(estimate)
    local se = r(se)
    local p = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))
    post `pf' ("Track-position") ("`cname': higher-track effect") ("Heterogeneity") (`b') (`se') (`p') (`n')
}

* -------------------------------------------------------------------------
* Family 3: Kenya assignment-payoff diagnostics
* -------------------------------------------------------------------------

preserve
use "$out/assignment_channel_tests_kenya.dta", clear
keep if inlist(specification, ///
    "Treat x mover interaction", ///
    "Predicted assignment gain: Treat x gain (1 SD)", ///
    "Top assignment-gain tercile ITT", ///
    "Treat x top assignment-gain tercile")
forvalues i = 1/`=_N' {
    local test = specification[`i']
    local b = coef[`i']
    local se = se[`i']
    local p = pval[`i']
    local n = N[`i']
    post `pf' ("Kenya payoff diagnostics") ("`test'") ("Mechanism") (`b') (`se') (`p') (`n')
}
restore

postclose `pf'

use `results', clear
gen long orig_order = _n
sort family pval
by family: gen rank = _n
by family: gen m = _N
gen q_raw = pval * m / rank
replace q_raw = min(q_raw, 1)
gsort family -rank
by family: gen q_bh = q_raw if _n == 1
by family: replace q_bh = min(q_raw, q_bh[_n-1]) if _n > 1
replace q_bh = min(q_bh, 1)
sort orig_order

export delimited using "$out/multiplicity_disclosure.csv", replace
save "$out/multiplicity_disclosure.dta", replace

tempname fh
file open `fh' using "$out/tab_multiplicity_disclosure.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Analysis Status and Multiplicity Disclosure}" _n
file write `fh' "\label{tab:multiplicity_disclosure}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\scriptsize" _n
file write `fh' "\setlength{\tabcolsep}{3pt}" _n
file write `fh' "\begin{tabular}[t]{p{3.1cm}p{4.8cm}p{1.8cm}cccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Family & Estimate & Status & Coef. & SE & Raw " _char(36) "p" _char(36) " & BH " _char(36) "q" _char(36) " \\" _n
file write `fh' "\midrule" _n

local lastfam ""
forvalues i = 1/`=_N' {
    local fam = family[`i']
    local test = test[`i']
    local status = status[`i']
    local b = estimate[`i']
    local se = se[`i']
    local p = pval[`i']
    local q = q_bh[`i']
    local bf : di %7.3f `b'
    local sef : di %7.3f `se'
    local pf : di %5.3f `p'
    local qf : di %5.3f `q'
    if "`fam'" != "`lastfam'" & "`lastfam'" != "" {
        file write `fh' "\addlinespace" _n
    }
    file write `fh' "`fam' & `test' & `status' & `bf' & (`sef') & `pf' & `qf' \\" _n
    local lastfam "`fam'"
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} The table reports Benjamini-Hochberg false-discovery-rate q-values within each displayed family. "
file write `fh' "The primary-endpoint family contains the country-specific ITTs that anchor the reduced form. "
file write `fh' "The track-position family uses the primary endpoint in each country and the support-aware Nigeria two-group collapse. "
file write `fh' "The Kenya payoff-diagnostic family contains mechanism tests used to ask whether students with larger predicted assignment gains benefited more. "
file write `fh' "Multiplicity adjustments are reported for transparency; the paper's main conclusions rely on the pattern of estimates, implementation evidence, and structural benchmarking rather than on any single adjusted rejection." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'

copy_to_paper tab_multiplicity_disclosure.tex
di "  -> tab_multiplicity_disclosure.tex"
di "  -> multiplicity_disclosure.csv"

di _n "09_multiplicity_disclosure.do complete."
