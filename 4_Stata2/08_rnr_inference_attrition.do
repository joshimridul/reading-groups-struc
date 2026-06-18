/*
08_rnr_inference_attrition.do — R&R inference and attrition hardening
=====================================================================
Produces:
  - tab_rnr_inference_checks.tex
  - tab_rnr_attrition_bounds.tex

These tables are designed for the referee-facing R&R pass.  They consolidate
cluster-robust, randomization-inference, attrition, IPW, and Lee-bound checks
without changing the preferred reduced-form estimands.
*/

di _n "{hline 70}"
di "08_rnr_inference_attrition.do — R&R inference and attrition checks"
di "{hline 70}"

if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/08_rnr_inference_attrition.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/08_rnr_inference_attrition.do") {
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

cap program drop fmt_cell
program define fmt_cell, rclass
    args x
    if missing(`x') {
        return local cell "--"
    }
    else {
        return local cell : di %6.3f `x'
    }
end

cap program drop post_attrition_row
program define post_attrition_row
    syntax, Study(string) Endpoint(string) Y(varname) ///
        Controls(string) Fe(string) Cluster(varname) ///
        Baseif(string) Responseif(string) POSTNAME(name)

    preserve
        keep if `baseif'
        tempvar attr response model_sample phat ipw keep_upper keep_lower
        gen byte `response' = `responseif'
        gen byte `attr' = !`response'
        gen byte `model_sample' = `response' == 1 & !missing(`y', treat, `controls')

        qui count
        local nbase = r(N)
        qui count if `response' == 1 & !missing(`y')
        local nobs = r(N)

        qui summ `attr' if treat == 1
        local at = r(mean)
        qui summ `attr' if treat == 0
        local ac = r(mean)

        qui reg `attr' treat `fe', vce(cluster `cluster')
        local adiff = _b[treat]
        local ase = _se[treat]

        qui reg `y' treat `controls' `fe' if `model_sample' == 1, vce(cluster `cluster')
        local ols = _b[treat]
        local ols_se = _se[treat]

        local ipwb = .
        local ipwse = .
        capture noisily logit `response' treat `controls' `fe'
        if _rc == 0 {
            predict double `phat' if e(sample), pr
            replace `phat' = . if `phat' < 0.02 | `phat' > 0.995
            gen double `ipw' = 1 / `phat'
            capture noisily reg `y' treat `controls' `fe' [pw=`ipw'] ///
                if `model_sample' == 1 & !missing(`ipw'), vce(cluster `cluster')
            if _rc == 0 {
                local ipwb = _b[treat]
                local ipwse = _se[treat]
            }
        }

        local attr_diff = `at' - `ac'
        if `attr_diff' > 0 {
            local trim_arm 0
            local trim_frac = `attr_diff' / (1 - `ac')
        }
        else if `attr_diff' < 0 {
            local trim_arm 1
            local trim_frac = -`attr_diff' / (1 - `at')
        }
        else {
            local trim_arm -1
            local trim_frac 0
        }

        if `trim_frac' > 0 & `trim_frac' < 1 {
            qui centile `y' if treat == `trim_arm' & `model_sample' == 1, ///
                centile(`=100*(1-`trim_frac')')
            local cutoff_upper = r(c_1)
            gen byte `keep_upper' = !(`response' == 1 & treat == `trim_arm' & `y' > `cutoff_upper')
            qui reg `y' treat `controls' `fe' if `model_sample' == 1 & `keep_upper' == 1, ///
                vce(cluster `cluster')
            local bound_a = _b[treat]

            qui centile `y' if treat == `trim_arm' & `model_sample' == 1, ///
                centile(`=100*`trim_frac'')
            local cutoff_lower = r(c_1)
            gen byte `keep_lower' = !(`response' == 1 & treat == `trim_arm' & `y' < `cutoff_lower')
            qui reg `y' treat `controls' `fe' if `model_sample' == 1 & `keep_lower' == 1, ///
                vce(cluster `cluster')
            local bound_b = _b[treat]

            local lb = min(`bound_a', `bound_b')
            local ub = max(`bound_a', `bound_b')
        }
        else {
            local lb = `ols'
            local ub = `ols'
        }

        post `postname' ("`study'") ("`endpoint'") ///
            (`at') (`ac') (`adiff') (`ase') ///
            (`ols') (`ols_se') (`ipwb') (`ipwse') ///
            (`lb') (`ub') (`nbase') (`nobs')
    restore
end

tempfile infer attrition
tempname pinf pattr

postfile `pinf' str12 study str24 assignment double b se_pref se_school p_wild p_rand N ///
    using `infer', replace

* -------------------------------------------------------------------------
* 1. Consolidated inference checks
* -------------------------------------------------------------------------

* Kenya: primary endpoint, school randomization
use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el
qui reg std_score_el treat std_eb i.strata, vce(cluster academycode)
local b = _b[treat]
local se_pref = _se[treat]
local se_school = _se[treat]
local n = e(N)
local obs_t = abs(_b[treat] / _se[treat])
local p_wild = .
capture which boottest
if _rc == 0 {
    capture noisily boottest treat, reps(999) seed(12345) cluster(academycode) nograph
    if _rc == 0 local p_wild = r(p)
}
local nperm 999
local pcount 0
set seed 54321
forvalues p = 1/`nperm' {
    preserve
        tempfile _pupil _punit
        qui save `_pupil'
        collapse (first) treat strata, by(academycode)
        gen double _u = runiform()
        sort strata _u
        by strata: egen _nt = total(treat)
        by strata: gen byte _pt = (_n <= _nt)
        keep academycode _pt
        qui save `_punit'
        use `_pupil', clear
        qui merge m:1 academycode using `_punit', nogen
        qui reg std_score_el _pt std_eb i.strata, vce(cluster academycode)
        if abs(_b[_pt] / _se[_pt]) >= `obs_t' local ++pcount
    restore
}
local p_rand = (`pcount' + 1) / (`nperm' + 1)
post `pinf' ("Kenya") ("school") (`b') (`se_pref') (`se_school') (`p_wild') (`p_rand') (`n')

* Liberia: preferred school-grade-group clustering plus broader school clustering
use "$out/analysis_liberia.dta", clear
keep if finsamp & has_el
qui reg std_score_el treat std_eb i.strata, vce(cluster ggroup)
local b = _b[treat]
local se_pref = _se[treat]
local n = e(N)
local obs_t = abs(_b[treat] / _se[treat])
qui reg std_score_el treat std_eb i.strata, vce(cluster academycode)
local se_school = _se[treat]
local p_wild = .
capture which boottest
if _rc == 0 {
    capture noisily boottest treat, reps(999) seed(12345) cluster(ggroup) nograph
    if _rc == 0 local p_wild = r(p)
}
local nperm 999
local pcount 0
set seed 54321
forvalues p = 1/`nperm' {
    preserve
        tempfile _pupil _punit
        qui save `_pupil'
        collapse (first) treat strata, by(ggroup)
        gen double _u = runiform()
        sort strata _u
        by strata: egen _nt = total(treat)
        by strata: gen byte _pt = (_n <= _nt)
        keep ggroup _pt
        qui save `_punit'
        use `_pupil', clear
        qui merge m:1 ggroup using `_punit', nogen
        qui reg std_score_el _pt std_eb i.strata, vce(cluster ggroup)
        if abs(_b[_pt] / _se[_pt]) >= `obs_t' local ++pcount
    restore
}
local p_rand = (`pcount' + 1) / (`nperm' + 1)
post `pinf' ("Liberia") ("school-grade group") (`b') (`se_pref') (`se_school') (`p_wild') (`p_rand') (`n')

* Nigeria: T3 endterm index, academy randomization
use "$out/analysis_nigeria_wide.dta", clear
egen constit_id = group(constituency)
egen grade_id = group(gradename)
keep if !missing(idx_t3_ete, treat, bl_score, constit_id, grade_id)
qui reg idx_t3_ete treat bl_score i.constit_id i.grade_id, vce(cluster academycode)
local b = _b[treat]
local se_pref = _se[treat]
local se_school = _se[treat]
local n = e(N)
local obs_t = abs(_b[treat] / _se[treat])
local p_wild = .
capture which boottest
if _rc == 0 {
    capture noisily boottest treat, reps(999) seed(12345) cluster(academycode) nograph
    if _rc == 0 local p_wild = r(p)
}
local nperm 999
local pcount 0
set seed 54321
forvalues p = 1/`nperm' {
    preserve
        tempfile _pupil _punit
        qui save `_pupil'
        collapse (first) treat constit_id, by(academycode)
        gen double _u = runiform()
        sort constit_id _u
        by constit_id: egen _nt = total(treat)
        by constit_id: gen byte _pt = (_n <= _nt)
        keep academycode _pt
        qui save `_punit'
        use `_pupil', clear
        qui merge m:1 academycode using `_punit', nogen
        qui reg idx_t3_ete _pt bl_score i.constit_id i.grade_id, vce(cluster academycode)
        if abs(_b[_pt] / _se[_pt]) >= `obs_t' local ++pcount
    restore
}
local p_rand = (`pcount' + 1) / (`nperm' + 1)
post `pinf' ("Nigeria") ("academy") (`b') (`se_pref') (`se_school') (`p_wild') (`p_rand') (`n')

postclose `pinf'

use `infer', clear
tempname fh
file open `fh' using "$out/tab_rnr_inference_checks.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Reduced-Form Inference Checks}" _n
file write `fh' "\label{tab:rnr_inference_checks}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\small" _n
file write `fh' "\begin{tabular}[t]{lcccccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Experiment & ITT & Preferred SE & School SE & Wild " _char(36) "p" _char(36) " & RI " _char(36) "p" _char(36) " & N \\" _n
file write `fh' "\midrule" _n
forvalues i = 1/`=_N' {
    local study = study[`i']
    local b = b[`i']
    local sep = se_pref[`i']
    local ses = se_school[`i']
    local pw = p_wild[`i']
    local pr = p_rand[`i']
    local nn = N[`i']
    local bstr : di %6.3f `b'
    local sepstr : di %6.3f `sep'
    local sesstr : di %6.3f `ses'
    fmt_cell `pw'
    local pwstr "`r(cell)'"
    fmt_cell `pr'
    local prstr "`r(cell)'"
    file write `fh' "`study' & `bstr' & (`sepstr') & (`sesstr') & `pwstr' & `prstr' & `nn' \\" _n
}
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} The ITT is the primary country endpoint: Kenya and Liberia endline literacy scores and Nigeria T3 endterm math--numeracy index. "
file write `fh' "Preferred standard errors cluster at the randomization unit: school in Kenya, school-grade group in Liberia, and academy in Nigeria. "
file write `fh' "The school-SE column reclusters Liberia at the academy level; for Kenya and Nigeria it repeats the preferred school/academy cluster. "
file write `fh' "Wild-cluster bootstrap " _char(36) "p" _char(36) "-values use 999 replications when the \texttt{boottest} package is available. "
file write `fh' "RI " _char(36) "p" _char(36) "-values are Fisher randomization-inference " _char(36) "p" _char(36) "-values from 999 reassignments within strata/constituency at the assignment unit." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_rnr_inference_checks.tex
di "  -> tab_rnr_inference_checks.tex"

* -------------------------------------------------------------------------
* 2. Attrition, IPW, and Lee-bound checks
* -------------------------------------------------------------------------

postfile `pattr' str12 study str12 endpoint double attr_t attr_c attr_diff attr_se ///
    ols ols_se ipw ipw_se lee_lb lee_ub N_base N_obs using `attrition', replace

use "$out/analysis_kenya.dta", clear
post_attrition_row, study("Kenya") endpoint("T3 endline") y(std_score_el) ///
    controls("std_eb") fe("i.strata") cluster(academycode) ///
    baseif("finsamp == 1") responseif("has_el == 1") postname(`pattr')

use "$out/analysis_liberia.dta", clear
post_attrition_row, study("Liberia") endpoint("endline") y(std_score_el) ///
    controls("std_eb") fe("i.strata") cluster(ggroup) ///
    baseif("finsamp == 1") responseif("has_el == 1") postname(`pattr')

use "$out/analysis_nigeria_wide.dta", clear
egen constit_id = group(constituency)
egen grade_id = group(gradename)
post_attrition_row, study("Nigeria") endpoint("T2 ETE") y(idx_t2_ete) ///
    controls("bl_score") fe("i.constit_id i.grade_id") cluster(academycode) ///
    baseif("!missing(treat, constit_id, grade_id)") responseif("!missing(idx_t2_ete)") postname(`pattr')

use "$out/analysis_nigeria_wide.dta", clear
egen constit_id = group(constituency)
egen grade_id = group(gradename)
post_attrition_row, study("Nigeria") endpoint("T3 ETE") y(idx_t3_ete) ///
    controls("bl_score") fe("i.constit_id i.grade_id") cluster(academycode) ///
    baseif("!missing(treat, constit_id, grade_id)") responseif("!missing(idx_t3_ete)") postname(`pattr')

postclose `pattr'

use `attrition', clear
tempname fa
file open `fa' using "$out/tab_rnr_attrition_bounds.tex", write replace
file write `fa' "\begin{table}[H]" _n
file write `fa' "\centering" _n
file write `fa' "\caption{Attrition, IPW, and Lee-Bound Checks}" _n
file write `fa' "\label{tab:rnr_attrition_bounds}" _n
file write `fa' "\begin{threeparttable}" _n
file write `fa' "\scriptsize" _n
file write `fa' "\setlength{\tabcolsep}{3pt}" _n
file write `fa' "\begin{tabular}[t]{llcccccc}" _n
file write `fa' "\toprule" _n
file write `fa' "Experiment & Endpoint & T attr. & C attr. & Adj. diff. & OLS ITT & IPW ITT & Lee bounds \\" _n
file write `fa' "\midrule" _n
forvalues i = 1/`=_N' {
    local study = study[`i']
    local endpoint = endpoint[`i']
    foreach v in attr_t attr_c attr_diff attr_se ols ols_se ipw ipw_se lee_lb lee_ub {
        local `v' = `v'[`i']
    }
    local atstr : di %5.3f `attr_t'
    local acstr : di %5.3f `attr_c'
    local adstr : di %6.3f `attr_diff'
    local asestr : di %6.3f `attr_se'
    local olsstr : di %6.3f `ols'
    local olsestr : di %6.3f `ols_se'
    fmt_cell `ipw'
    local ipwstr "`r(cell)'"
    fmt_cell `ipw_se'
    local ipwestr "`r(cell)'"
    local lbstr : di %6.3f `lee_lb'
    local ubstr : di %6.3f `lee_ub'
    file write `fa' "`study' & `endpoint' & `atstr' & `acstr' & `adstr' & `olsstr' & `ipwstr' & [`lbstr', `ubstr'] \\" _n
    file write `fa' " & & & & (`asestr') & (`olsestr') & (`ipwestr') & \\" _n
}
file write `fa' "\bottomrule" _n
file write `fa' "\end{tabular}" _n
file write `fa' "\begin{tablenotes}[para,flushleft]" _n
file write `fa' "\footnotesize" _n
file write `fa' "\item \textit{Notes:} Attrition is missing outcome for the listed endpoint. "
file write `fa' "Adjusted attrition differences use the same fixed effects as the corresponding outcome model. "
file write `fa' "OLS ITT is the preferred endpoint regression. IPW estimates weight observed outcome regressions by the inverse predicted response probability from a logit on treatment, baseline score, and design fixed effects. "
file write `fa' "Lee bounds trim the lower-attrition arm to equalize response rates and then re-estimate the covariate-adjusted endpoint regression. "
file write `fa' "Standard errors in parentheses are clustered at the preferred assignment unit." _n
file write `fa' "\end{tablenotes}" _n
file write `fa' "\end{threeparttable}" _n
file write `fa' "\end{table}" _n
file close `fa'
copy_to_paper tab_rnr_attrition_bounds.tex
di "  -> tab_rnr_attrition_bounds.tex"

di _n "08_rnr_inference_attrition.do complete."
