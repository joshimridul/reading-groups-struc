/*
02_nigeria_main_analysis.do — Nigeria tables in Kenya/Liberia style
====================================================================
Produces:
  1) Balance table
  2) Attrition table (baseline -> each follow-up wave)
  3) Main 3-column regression tables by term/window (math, numeracy, index)
  4) Over-time stacked tables (panel with wave FE)
  5) IRT table (T3 ETE numeracy)
  6) Interaction versions (Red/Blue/Yellow heterogeneity)

All .tex tables are written to:
  - 4_Stata2/output/
  - repo-root stata_output/
*/

di _n "{hline 70}"
di "02_nigeria_main_analysis.do — Nigeria table pipeline"
di "{hline 70}"

* ── Paths (standalone-safe) ─────────────────────────────────────────────
if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/02_nigeria_main_analysis.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/02_nigeria_main_analysis.do") {
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

* ── Helpers ─────────────────────────────────────────────────────────────
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

* ═════════════════════════════════════════════════════════════════════════
* make_threecol_table — cross-sectional OLS, 3 outcome columns
* ═════════════════════════════════════════════════════════════════════════
cap program drop make_threecol_table
program define make_threecol_table
    args fname caption label y1 y2 y3 h1 h2 h3

    if "`h1'" == "" local h1 "Math"
    if "`h2'" == "" local h2 "Numeracy"
    if "`h3'" == "" local h3 "Math + Numeracy Index"

    local j = 1
    foreach y in `y1' `y2' `y3' {
        qui reg `y' treat bl_score i.constit_id i.grade_id ///
            if !missing(`y', treat, bl_score, constit_id, grade_id), ///
            vce(cluster academycode)
        local b`j'  : di %7.3f _b[treat]
        local se`j' : di %7.3f _se[treat]
        local n`j' = e(N)
        local pv`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
        qui summ `y' if treat == 0 & !missing(`y')
        local cm`j' : di %7.3f r(mean)
        get_stars `pv`j''
        local st`j' "`r(stars)'"
        local ++j
    }

    tempname fh
    file open `fh' using "$out/`fname'", write replace
    file write `fh' "\begin{table}[!htbp]" _n
    file write `fh' "\centering" _n
    file write `fh' "\caption{`caption'}" _n
    file write `fh' "\label{`label'}" _n
    file write `fh' "\begin{threeparttable}" _n
    file write `fh' "\begin{tabular}[t]{lccc}" _n
    file write `fh' "\toprule" _n
    file write `fh' " & (1) & (2) & (3) \\" _n
    file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
    file write `fh' " & `h1' & `h2' & `h3' \\" _n
    file write `fh' "\midrule" _n
    file write `fh' "Treatment & `b1'`st1' & `b2'`st2' & `b3'`st3' \\" _n
    file write `fh' " & (`se1') & (`se2') & (`se3') \\" _n
    file write `fh' "\addlinespace" _n
    file write `fh' "Control Mean & `cm1' & `cm2' & `cm3' \\" _n
    file write `fh' "N & `n1' & `n2' & `n3' \\" _n
    file write `fh' "\bottomrule" _n
    file write `fh' "\end{tabular}" _n
    file write `fh' "\begin{tablenotes}[para]" _n
    file write `fh' "\item Notes: OLS with baseline score control, constituency FE, and grade FE. " _n
    file write `fh' "SEs clustered at academy level. ***, **, and * indicate 1\%, 5\%, and 10\%." _n
    file write `fh' "\end{tablenotes}" _n
    file write `fh' "\end{threeparttable}" _n
    file write `fh' "\end{table}" _n
    file close `fh'

    copy_to_paper `fname'
    di "  -> `fname'"
end

* ═════════════════════════════════════════════════════════════════════════
* make_interaction_table — cross-sectional with treat x group
* ═════════════════════════════════════════════════════════════════════════
cap program drop make_interaction_table
program define make_interaction_table
    args fname caption label y1 y2 y3

    local j = 1
    foreach y in `y1' `y2' `y3' {
        qui reg `y' i.treat##ib1.group_id bl_score i.constit_id i.grade_id ///
            if !missing(`y', treat, bl_score, constit_id, grade_id, group_id), ///
            vce(cluster academycode)

        local r_b`j'  : di %7.3f _b[1.treat]
        local r_se`j' : di %7.3f _se[1.treat]
        local r_p`j' = 2 * ttail(e(df_r), abs(_b[1.treat] / _se[1.treat]))
        get_stars `r_p`j''
        local r_st`j' "`r(stars)'"

        qui lincom 1.treat + 1.treat#2.group_id
        local b_b`j'  : di %7.3f r(estimate)
        local b_se`j' : di %7.3f r(se)
        local b_p`j'  = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))
        get_stars `b_p`j''
        local b_st`j' "`r(stars)'"

        qui lincom 1.treat + 1.treat#3.group_id
        local y_b`j'  : di %7.3f r(estimate)
        local y_se`j' : di %7.3f r(se)
        local y_p`j'  = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))
        get_stars `y_p`j''
        local y_st`j' "`r(stars)'"

        local n`j' = e(N)
        local ++j
    }

    tempname fh
    file open `fh' using "$out/`fname'", write replace
    file write `fh' "\begin{table}[!htbp]" _n
    file write `fh' "\centering" _n
    file write `fh' "\caption{`caption'}" _n
    file write `fh' "\label{`label'}" _n
    file write `fh' "\begin{threeparttable}" _n
    file write `fh' "\begin{tabular}[t]{lccc}" _n
    file write `fh' "\toprule" _n
    file write `fh' " & Math & Numeracy & Math + Numeracy Index \\" _n
    file write `fh' "\midrule" _n
    file write `fh' "Red group effect & `r_b1'`r_st1' & `r_b2'`r_st2' & `r_b3'`r_st3' \\" _n
    file write `fh' " & (`r_se1') & (`r_se2') & (`r_se3') \\" _n
    file write `fh' "Blue group effect & `b_b1'`b_st1' & `b_b2'`b_st2' & `b_b3'`b_st3' \\" _n
    file write `fh' " & (`b_se1') & (`b_se2') & (`b_se3') \\" _n
    file write `fh' "Yellow group effect & `y_b1'`y_st1' & `y_b2'`y_st2' & `y_b3'`y_st3' \\" _n
    file write `fh' " & (`y_se1') & (`y_se2') & (`y_se3') \\" _n
    file write `fh' "\addlinespace" _n
    file write `fh' "N & `n1' & `n2' & `n3' \\" _n
    file write `fh' "\bottomrule" _n
    file write `fh' "\end{tabular}" _n
    file write `fh' "\begin{tablenotes}[para]" _n
    file write `fh' "\item Notes: Rows report group-specific total treatment effects from treatment-by-group interaction regressions. " _n
    file write `fh' "Red is the treatment coefficient; Blue and Yellow are Treatment plus the corresponding interaction. Controls and SE clustering as in baseline tables." _n
    file write `fh' "\end{tablenotes}" _n
    file write `fh' "\end{threeparttable}" _n
    file write `fh' "\end{table}" _n
    file close `fh'

    copy_to_paper `fname'
    di "  -> `fname'"
end

* ═════════════════════════════════════════════════════════════════════════
* make_panel_threecol_table — stacked OLS with wave FE, cluster at academy
* ═════════════════════════════════════════════════════════════════════════
cap program drop make_panel_threecol_table
program define make_panel_threecol_table
    args fname caption label wavemode

    preserve
    keep studyid academycode treat bl_score constit_id grade_id group_id ///
        z_percscoret2_mte_maths z_percscoret2_ete_maths z_percscoret3_mte_maths z_percscoret3_ete_maths ///
        z_percscoret2_mte_numeracy z_percscoret2_ete_numeracy z_percscoret3_mte_numeracy z_percscoret3_ete_numeracy ///
        idx_t2_mte idx_t2_ete idx_t3_mte idx_t3_ete

    gen y_math_t2_mte = z_percscoret2_mte_maths
    gen y_math_t2_ete = z_percscoret2_ete_maths
    gen y_math_t3_mte = z_percscoret3_mte_maths
    gen y_math_t3_ete = z_percscoret3_ete_maths

    gen y_num_t2_mte  = z_percscoret2_mte_numeracy
    gen y_num_t2_ete  = z_percscoret2_ete_numeracy
    gen y_num_t3_mte  = z_percscoret3_mte_numeracy
    gen y_num_t3_ete  = z_percscoret3_ete_numeracy

    gen y_idx_t2_mte  = idx_t2_mte
    gen y_idx_t2_ete  = idx_t2_ete
    gen y_idx_t3_mte  = idx_t3_mte
    gen y_idx_t3_ete  = idx_t3_ete

    keep studyid academycode treat bl_score constit_id grade_id group_id y_math_* y_num_* y_idx_*
    reshape long y_math_ y_num_ y_idx_, i(studyid) j(wave) string
    encode wave, gen(wave_id)

    local j = 1
    foreach y in y_math_ y_num_ y_idx_ {
        if "`wavemode'" == "all" {
            qui reg `y' treat bl_score i.constit_id i.grade_id i.wave_id ///
                if inlist(wave, "t2_mte", "t2_ete", "t3_mte", "t3_ete") ///
                & !missing(`y', treat, bl_score, constit_id, grade_id, wave_id), ///
                vce(cluster academycode)
            qui summ `y' if treat == 0 & inlist(wave, "t2_mte", "t2_ete", "t3_mte", "t3_ete") & !missing(`y')
        }
        else if "`wavemode'" == "t2" {
            qui reg `y' treat bl_score i.constit_id i.grade_id i.wave_id ///
                if inlist(wave, "t2_mte", "t2_ete") ///
                & !missing(`y', treat, bl_score, constit_id, grade_id, wave_id), ///
                vce(cluster academycode)
            qui summ `y' if treat == 0 & inlist(wave, "t2_mte", "t2_ete") & !missing(`y')
        }
        else if "`wavemode'" == "t3" {
            qui reg `y' treat bl_score i.constit_id i.grade_id i.wave_id ///
                if inlist(wave, "t3_mte", "t3_ete") ///
                & !missing(`y', treat, bl_score, constit_id, grade_id, wave_id), ///
                vce(cluster academycode)
            qui summ `y' if treat == 0 & inlist(wave, "t3_mte", "t3_ete") & !missing(`y')
        }
        else {
            restore
            di as err "Unknown wavemode in make_panel_threecol_table: `wavemode'"
            exit 198
        }

        local cm`j' : di %7.3f r(mean)
        local b`j'  : di %7.3f _b[treat]
        local se`j' : di %7.3f _se[treat]
        local n`j' = e(N)
        local pv`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
        get_stars `pv`j''
        local st`j' "`r(stars)'"
        local ++j
    }
    restore

    tempname fh
    file open `fh' using "$out/`fname'", write replace
    file write `fh' "\begin{table}[!htbp]" _n
    file write `fh' "\centering" _n
    file write `fh' "\caption{`caption'}" _n
    file write `fh' "\label{`label'}" _n
    file write `fh' "\begin{threeparttable}" _n
    file write `fh' "\begin{tabular}[t]{lccc}" _n
    file write `fh' "\toprule" _n
    file write `fh' " & (1) & (2) & (3) \\" _n
    file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
    file write `fh' " & Math & Numeracy & Math + Numeracy Index \\" _n
    file write `fh' "\midrule" _n
    file write `fh' "Treatment & `b1'`st1' & `b2'`st2' & `b3'`st3' \\" _n
    file write `fh' " & (`se1') & (`se2') & (`se3') \\" _n
    file write `fh' "\addlinespace" _n
    file write `fh' "Control Mean & `cm1' & `cm2' & `cm3' \\" _n
    file write `fh' "N (student-waves) & `n1' & `n2' & `n3' \\" _n
    file write `fh' "\bottomrule" _n
    file write `fh' "\end{tabular}" _n
    file write `fh' "\begin{tablenotes}[para]" _n
    file write `fh' "\item Notes: Pooled OLS on stacked student-wave observations with wave FE, " _n
    file write `fh' "baseline score control, constituency FE, and grade FE. " _n
    file write `fh' "SEs clustered at academy level. ***, **, and * indicate 1\%, 5\%, and 10\%." _n
    file write `fh' "\end{tablenotes}" _n
    file write `fh' "\end{threeparttable}" _n
    file write `fh' "\end{table}" _n
    file close `fh'

    copy_to_paper `fname'
    di "  -> `fname'"
end

* ═════════════════════════════════════════════════════════════════════════
* make_panel_interaction_table — stacked OLS with treat x group, cluster at academy
* ═════════════════════════════════════════════════════════════════════════
cap program drop make_panel_interaction_table
program define make_panel_interaction_table
    args fname caption label wavemode

    preserve
    keep studyid academycode treat bl_score constit_id grade_id group_id ///
        z_percscoret2_mte_maths z_percscoret2_ete_maths z_percscoret3_mte_maths z_percscoret3_ete_maths ///
        z_percscoret2_mte_numeracy z_percscoret2_ete_numeracy z_percscoret3_mte_numeracy z_percscoret3_ete_numeracy ///
        idx_t2_mte idx_t2_ete idx_t3_mte idx_t3_ete

    gen y_math_t2_mte = z_percscoret2_mte_maths
    gen y_math_t2_ete = z_percscoret2_ete_maths
    gen y_math_t3_mte = z_percscoret3_mte_maths
    gen y_math_t3_ete = z_percscoret3_ete_maths

    gen y_num_t2_mte  = z_percscoret2_mte_numeracy
    gen y_num_t2_ete  = z_percscoret2_ete_numeracy
    gen y_num_t3_mte  = z_percscoret3_mte_numeracy
    gen y_num_t3_ete  = z_percscoret3_ete_numeracy

    gen y_idx_t2_mte  = idx_t2_mte
    gen y_idx_t2_ete  = idx_t2_ete
    gen y_idx_t3_mte  = idx_t3_mte
    gen y_idx_t3_ete  = idx_t3_ete

    keep studyid academycode treat bl_score constit_id grade_id group_id y_math_* y_num_* y_idx_*
    reshape long y_math_ y_num_ y_idx_, i(studyid) j(wave) string
    encode wave, gen(wave_id)

    local j = 1
    foreach y in y_math_ y_num_ y_idx_ {
        if "`wavemode'" == "all" {
            qui reg `y' i.treat##ib1.group_id bl_score i.constit_id i.grade_id i.wave_id ///
                if inlist(wave, "t2_mte", "t2_ete", "t3_mte", "t3_ete") ///
                & !missing(`y', treat, bl_score, constit_id, grade_id, group_id, wave_id), ///
                vce(cluster academycode)
        }
        else if "`wavemode'" == "t2" {
            qui reg `y' i.treat##ib1.group_id bl_score i.constit_id i.grade_id i.wave_id ///
                if inlist(wave, "t2_mte", "t2_ete") ///
                & !missing(`y', treat, bl_score, constit_id, grade_id, group_id, wave_id), ///
                vce(cluster academycode)
        }
        else if "`wavemode'" == "t3" {
            qui reg `y' i.treat##ib1.group_id bl_score i.constit_id i.grade_id i.wave_id ///
                if inlist(wave, "t3_mte", "t3_ete") ///
                & !missing(`y', treat, bl_score, constit_id, grade_id, group_id, wave_id), ///
                vce(cluster academycode)
        }
        else {
            restore
            di as err "Unknown wavemode in make_panel_interaction_table: `wavemode'"
            exit 198
        }

        local r_b`j'  : di %7.3f _b[1.treat]
        local r_se`j' : di %7.3f _se[1.treat]
        local r_p`j' = 2 * ttail(e(df_r), abs(_b[1.treat] / _se[1.treat]))
        get_stars `r_p`j''
        local r_st`j' "`r(stars)'"

        qui lincom 1.treat + 1.treat#2.group_id
        local b_b`j'  : di %7.3f r(estimate)
        local b_se`j' : di %7.3f r(se)
        local b_p`j'  = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))
        get_stars `b_p`j''
        local b_st`j' "`r(stars)'"

        qui lincom 1.treat + 1.treat#3.group_id
        local y_b`j'  : di %7.3f r(estimate)
        local y_se`j' : di %7.3f r(se)
        local y_p`j'  = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))
        get_stars `y_p`j''
        local y_st`j' "`r(stars)'"

        local n`j' = e(N)
        local ++j
    }
    restore

    tempname fh
    file open `fh' using "$out/`fname'", write replace
    file write `fh' "\begin{table}[!htbp]" _n
    file write `fh' "\centering" _n
    file write `fh' "\caption{`caption'}" _n
    file write `fh' "\label{`label'}" _n
    file write `fh' "\begin{threeparttable}" _n
    file write `fh' "\begin{tabular}[t]{lccc}" _n
    file write `fh' "\toprule" _n
    file write `fh' " & Math & Numeracy & Math + Numeracy Index \\" _n
    file write `fh' "\midrule" _n
    file write `fh' "Red group effect & `r_b1'`r_st1' & `r_b2'`r_st2' & `r_b3'`r_st3' \\" _n
    file write `fh' " & (`r_se1') & (`r_se2') & (`r_se3') \\" _n
    file write `fh' "Blue group effect & `b_b1'`b_st1' & `b_b2'`b_st2' & `b_b3'`b_st3' \\" _n
    file write `fh' " & (`b_se1') & (`b_se2') & (`b_se3') \\" _n
    file write `fh' "Yellow group effect & `y_b1'`y_st1' & `y_b2'`y_st2' & `y_b3'`y_st3' \\" _n
    file write `fh' " & (`y_se1') & (`y_se2') & (`y_se3') \\" _n
    file write `fh' "\addlinespace" _n
    file write `fh' "N (student-waves) & `n1' & `n2' & `n3' \\" _n
    file write `fh' "\bottomrule" _n
    file write `fh' "\end{tabular}" _n
    file write `fh' "\begin{tablenotes}[para]" _n
    file write `fh' "\item Notes: Pooled OLS on stacked student-wave observations with wave FE. Rows report group-specific total treatment effects. " _n
    file write `fh' "Red is the treatment coefficient; Blue and Yellow are Treatment plus the corresponding interaction. SEs clustered at academy level. Controls as in baseline tables." _n
    file write `fh' "\end{tablenotes}" _n
    file write `fh' "\end{threeparttable}" _n
    file write `fh' "\end{table}" _n
    file close `fh'

    copy_to_paper `fname'
    di "  -> `fname'"
end

* ── Load cleaned Nigeria wide file ───────────────────────────────────────
capture confirm file "$out/analysis_nigeria_wide.dta"
if _rc {
    di as err "analysis_nigeria_wide.dta missing. Run 00_clean_nigeria.do first."
    exit 601
}

use "$out/analysis_nigeria_wide.dta", clear
drop if missing(studyid)
drop if missing(treat)
drop if missing(academycode)

encode constituency, gen(constit_id)
encode gradename, gen(grade_id)

* ── 1) Balance table ─────────────────────────────────────────────────────
tempname fh
file open `fh' using "$out/tab_ng_balance.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Baseline Balance}" _n
file write `fh' "\label{tab:ng_balance}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Variable & Treat mean & Control mean & Diff & SE & p value \\" _n
file write `fh' "\midrule" _n

gen has_bl   = !missing(bl_score)
gen has_t2_mte = !missing(percscoret2_mte_maths) | !missing(percscoret2_mte_numeracy)
gen has_t2_ete = !missing(percscoret2_ete_maths) | !missing(percscoret2_ete_numeracy)
gen has_t3_mte = !missing(percscoret3_mte_maths) | !missing(percscoret3_mte_numeracy)
gen has_t3_ete = !missing(percscoret3_ete_maths) | !missing(percscoret3_ete_numeracy)

foreach v in bl_score has_bl has_t2_mte has_t2_ete has_t3_mte has_t3_ete {
    local vlab = subinstr("`v'", "_", "\_", .)
    qui summ `v' if treat == 1
    local tm : di %7.3f r(mean)
    qui summ `v' if treat == 0
    local cm : di %7.3f r(mean)
    qui reg `v' treat i.constit_id i.grade_id if !missing(`v', treat, constit_id, grade_id), vce(cluster academycode)
    local b  : di %7.3f _b[treat]
    local se : di %7.3f _se[treat]
    local pv = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    local pvf : di %5.3f `pv'
    file write `fh' "`vlab' & `tm' & `cm' & `b' & (`se') & `pvf' \\" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Follow-up indicators are 1 if student observed in that wave. " _n
file write `fh' "Diff column uses OLS with constituency and grade FE, clustered by academy." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_balance.tex
di "  -> tab_ng_balance.tex"

* ── 2) Attrition table ───────────────────────────────────────────────────
* Unconditional: defined for ALL students (not just those with baseline)
tempname fh
file open `fh' using "$out/tab_ng_attrition.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Attrition by Term and Window}" _n
file write `fh' "\label{tab:ng_attrition}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Wave/Outcome & Treat retain & Control retain & Diff & SE & p value \\" _n
file write `fh' "\midrule" _n

foreach pair in ///
    "t2_mte_math percscoret2_mte_maths" ///
    "t2_mte_num percscoret2_mte_numeracy" ///
    "t2_ete_math percscoret2_ete_maths" ///
    "t2_ete_num percscoret2_ete_numeracy" ///
    "t3_mte_math percscoret3_mte_maths" ///
    "t3_mte_num percscoret3_mte_numeracy" ///
    "t3_ete_math percscoret3_ete_maths" ///
    "t3_ete_num percscoret3_ete_numeracy" {

    local rn : word 1 of `pair'
    local vv : word 2 of `pair'
    local rlab = subinstr("`rn'", "_", "\_", .)
    gen attr_`rn' = !missing(`vv')

    qui summ attr_`rn' if treat == 1
    local tm : di %7.3f r(mean)
    qui summ attr_`rn' if treat == 0
    local cm : di %7.3f r(mean)

    qui reg attr_`rn' treat i.constit_id i.grade_id if !missing(attr_`rn', treat, constit_id, grade_id), vce(cluster academycode)
    local b  : di %7.3f _b[treat]
    local se : di %7.3f _se[treat]
    local pv = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    local pvf : di %5.3f `pv'

    file write `fh' "`rlab' & `tm' & `cm' & `b' & (`se') & `pvf' \\" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Retention indicators defined unconditionally for all students in sample. " _n
file write `fh' "OLS with constituency and grade FE, clustered by academy." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_attrition.tex
di "  -> tab_ng_attrition.tex"

* ── 3) Main wave-by-wave tables (math, numeracy, index) ──────────────────
make_threecol_table ///
    "tab_ng_t2_mte.tex" ///
    "Effect on T2 Midterm Outcomes" ///
    "tab:ng_t2_mte" ///
    "z_percscoret2_mte_maths" ///
    "z_percscoret2_mte_numeracy" ///
    "idx_t2_mte"

make_threecol_table ///
    "tab_ng_t2_ete.tex" ///
    "Effect on T2 Endterm Outcomes" ///
    "tab:ng_t2_ete" ///
    "z_percscoret2_ete_maths" ///
    "z_percscoret2_ete_numeracy" ///
    "idx_t2_ete"

make_threecol_table ///
    "tab_ng_t3_mte.tex" ///
    "Effect on T3 Midterm Outcomes" ///
    "tab:ng_t3_mte" ///
    "z_percscoret3_mte_maths" ///
    "z_percscoret3_mte_numeracy" ///
    "idx_t3_mte"

make_threecol_table ///
    "tab_ng_t3_ete.tex" ///
    "Effect on T3 Endterm Outcomes" ///
    "tab:ng_t3_ete" ///
    "z_percscoret3_ete_maths" ///
    "z_percscoret3_ete_numeracy" ///
    "idx_t3_ete"

* ── 3a/3b/3c) Over-time stacked tables ───────────────────────────────────
make_panel_threecol_table ///
    "tab_ng_over_terms.tex" ///
    "Effects Using Data Over Terms (Stacked)" ///
    "tab:ng_over_terms" ///
    "all"

make_panel_threecol_table ///
    "tab_ng_t2_over_time.tex" ///
    "T2 Midterm + T2 Endterm (Stacked)" ///
    "tab:ng_t2_over_time" ///
    "t2"

make_panel_threecol_table ///
    "tab_ng_t3_over_time.tex" ///
    "T3 Midterm + T3 Endterm (Stacked)" ///
    "tab:ng_t3_over_time" ///
    "t3"

* ── 4) IRT outcomes table — custom headers ───────────────────────────────
make_threecol_table ///
    "tab_ng_irt.tex" ///
    "IRT-Based Outcomes (T3 ETE Numeracy)" ///
    "tab:ng_irt" ///
    "z_percscoret3_ete_numeracy" ///
    "theta_irt_z" ///
    "theta_irt" ///
    "Pct Score (z)" ///
    "IRT Ability (z)" ///
    "IRT Ability (raw)"

* ── 5) Appendix transparency table (unrestricted Red/Blue/Yellow) ────────
make_panel_interaction_table ///
    "tab_ng_over_terms_interact.tex" ///
    "Over-Term Effects by Group Color (Red/Blue/Yellow, Stacked)" ///
    "tab:ng_over_terms_interact" ///
    "all"

* ── 6) Additional Nigeria tables (plan parity extensions) ──────────────────

* 6a) Summary statistics
preserve
tempname fh
file open `fh' using "$out/tab_ng_sumstats.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Summary Statistics}" _n
file write `fh' "\label{tab:ng_sumstats}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Variable & Control Mean & Treatment Mean & SD (All) & N \\" _n
file write `fh' "\midrule" _n

gen in_red = (group_id == 1) if !missing(group_id)
gen in_blueyellow = inlist(group_id, 2, 3) if !missing(group_id)
egen tag_acad = tag(academycode)

foreach pair in ///
    "Baseline score|bl_score" ///
    "Observed T2 midterm|has_t2_mte" ///
    "Observed T2 endterm|has_t2_ete" ///
    "Observed T3 midterm|has_t3_mte" ///
    "Observed T3 endterm|has_t3_ete" ///
    "Red group share|in_red" ///
    "Blue/Yellow group share|in_blueyellow" {

    local vlab = substr("`pair'", 1, strpos("`pair'", "|") - 1)
    local vv = substr("`pair'", strpos("`pair'", "|") + 1, .)

    qui summ `vv' if treat == 0
    local cm : di %7.3f r(mean)
    qui summ `vv' if treat == 1
    local tm : di %7.3f r(mean)
    qui summ `vv'
    local sd : di %7.3f r(sd)
    qui count if !missing(`vv')
    local nn = r(N)

    file write `fh' "`vlab' & `cm' & `tm' & `sd' & `nn' \\" _n
}

qui count if tag_acad == 1 & treat == 0
local ac0 = r(N)
qui count if tag_acad == 1 & treat == 1
local ac1 = r(N)
qui count if tag_acad == 1
local aca = r(N)
file write `fh' "Number of academies & `ac0' & `ac1' & -- & `aca' \\" _n

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Means and SDs at student level. Follow-up indicators equal 1 if observed in that wave." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_sumstats.tex
di "  -> tab_ng_sumstats.tex"
restore

* 6b) Sample flow
preserve
tempname fh
file open `fh' using "$out/tab_ng_sampleflow.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Sample Flow}" _n
file write `fh' "\label{tab:ng_sampleflow}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Step & Control & Treatment & Total \\" _n
file write `fh' "\midrule" _n

foreach step in ///
    "All observations|1" ///
    "Non-missing treat and academy|!missing(treat, academycode)" ///
    "With baseline score|!missing(bl_score)" ///
    "Observed in T2 midterm|has_t2_mte == 1" ///
    "Observed in T2 endterm|has_t2_ete == 1" ///
    "Observed in T3 midterm|has_t3_mte == 1" ///
    "Observed in T3 endterm|has_t3_ete == 1" {

    local slabel = substr("`step'", 1, strpos("`step'", "|") - 1)
    local cond = substr("`step'", strpos("`step'", "|") + 1, .)

    qui count if `cond' & treat == 0
    local n0 = r(N)
    qui count if `cond' & treat == 1
    local n1 = r(N)
    qui count if `cond'
    local na = r(N)

    file write `fh' "`slabel' & `n0' & `n1' & `na' \\" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Sample-flow counts in the Nigeria cleaned wide analysis file." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_sampleflow.tex
di "  -> tab_ng_sampleflow.tex"
restore

* 6c) Upper/lower track interaction (upper = Blue/Yellow group)
preserve
gen upper_group = inlist(group_id, 2, 3) if !missing(group_id)
gen treat_x_upper = treat * upper_group

local y1 "idx_t2_mte"
local y2 "idx_t2_ete"
local y3 "idx_t3_mte"
local y4 "idx_t3_ete"

forvalues j = 1/4 {
    local y "`y`j''"
    qui reg `y' treat treat_x_upper upper_group bl_score i.constit_id i.grade_id ///
        if !missing(`y', treat, treat_x_upper, upper_group, bl_score, constit_id, grade_id), ///
        vce(cluster academycode)

    local lb`j'  : di %7.3f _b[treat]
    local lse`j' : di %7.3f _se[treat]
    local lp`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `lp`j''
    local lst`j' "`r(stars)'"

    local xb`j'  : di %7.3f _b[treat_x_upper]
    local xse`j' : di %7.3f _se[treat_x_upper]
    local xp`j' = 2 * ttail(e(df_r), abs(_b[treat_x_upper] / _se[treat_x_upper]))
    get_stars `xp`j''
    local xst`j' "`r(stars)'"

    qui lincom treat + treat_x_upper
    local ub`j'  : di %7.3f r(estimate)
    local use`j' : di %7.3f r(se)
    local up`j' = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))
    get_stars `up`j''
    local ust`j' "`r(stars)'"

    qui summ `y' if treat == 0 & !missing(`y', treat_x_upper, upper_group, bl_score, constit_id, grade_id)
    local cm`j' : di %7.3f r(mean)
    local n`j' = e(N)
}

tempname fh
file open `fh' using "$out/tab_ng_upper_lower.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Treatment Effects by Two-Group Track Position}" _n
file write `fh' "\label{tab:ng_upper_lower}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & T2 MTE & T2 ETE & T3 MTE & T3 ETE \\" _n
file write `fh' "\midrule" _n
file write `fh' "Lower track (Treatment) & `lb1'`lst1' & `lb2'`lst2' & `lb3'`lst3' & `lb4'`lst4' \\" _n
file write `fh' " & (`lse1') & (`lse2') & (`lse3') & (`lse4') \\" _n
file write `fh' "Treatment x Upper & `xb1'`xst1' & `xb2'`xst2' & `xb3'`xst3' & `xb4'`xst4' \\" _n
file write `fh' " & (`xse1') & (`xse2') & (`xse3') & (`xse4') \\" _n
file write `fh' "Upper track total & `ub1'`ust1' & `ub2'`ust2' & `ub3'`ust3' & `ub4'`ust4' \\" _n
file write `fh' " & (`use1') & (`use2') & (`use3') & (`use4') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Control Mean & `cm1' & `cm2' & `cm3' & `cm4' \\" _n
file write `fh' "N & `n1' & `n2' & `n3' & `n4' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Upper group is the preferred support-aware two-group collapse, Blue/Yellow (\texttt{group\_id} = 2 or 3). Controls: baseline score, constituency FE, grade FE. SEs clustered at academy level." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_upper_lower.tex
di "  -> tab_ng_upper_lower.tex"
restore

* 6d) Specification robustness (primary outcome T3 ETE index + all waves)
capture which boottest
if _rc != 0 {
    capture ssc install boottest, replace
}

local y1 "idx_t2_mte"
local y2 "idx_t2_ete"
local y3 "idx_t3_mte"
local y4 "idx_t3_ete"

forvalues j = 1/4 {
    local y "`y`j''"

    qui reg `y' treat bl_score i.constit_id i.grade_id ///
        if !missing(`y', treat, bl_score, constit_id, grade_id), ///
        vce(cluster academycode)
    local ab`j'  : di %7.3f _b[treat]
    local ase`j' : di %7.3f _se[treat]
    local ap`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `ap`j''
    local ast`j' "`r(stars)'"
    local n`j' = e(N)
    local obs_t = abs(_b[treat] / _se[treat])

    capture qui boottest treat, reps(999) seed(12345) cluster(academycode) nograph
    if _rc == 0 {
        local wb`j' : di %5.3f r(p)
    }
    else {
        local wb`j' "---"
    }

    qui reg `y' treat i.constit_id i.grade_id ///
        if !missing(`y', treat, constit_id, grade_id), ///
        vce(cluster academycode)
    local bb`j'  : di %7.3f _b[treat]
    local bse`j' : di %7.3f _se[treat]
    local bp`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `bp`j''
    local bst`j' "`r(stars)'"

    if `j' == 4 {
        local nperm 999
        local pcount 0
        set seed 54321
        forvalues p = 1/`nperm' {
            preserve
            keep if !missing(`y', treat, bl_score, constit_id, grade_id, academycode)
            tempfile _pupil _pschool
            qui save `_pupil'
            collapse (first) treat constit_id, by(academycode)
            gen double _u = runiform()
            sort constit_id _u
            by constit_id: egen _nt = total(treat)
            by constit_id: gen _pt = (_n <= _nt)
            keep academycode _pt
            qui save `_pschool'
            use `_pupil', clear
            qui merge m:1 academycode using `_pschool', nogen
            qui reg `y' _pt bl_score i.constit_id i.grade_id, vce(cluster academycode)
            if abs(_b[_pt] / _se[_pt]) >= `obs_t' {
                local ++pcount
            }
            restore
        }
        local pp`j' : di %5.3f (`pcount' + 1) / (`nperm' + 1)
    }
    else {
        local pp`j' "--"
    }
}

tempname fh
file open `fh' using "$out/tab_ng_spec_robust.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria ITT Robustness Across Specifications}" _n
file write `fh' "\label{tab:ng_spec_robust}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\fontsize{9}{11}\selectfont" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & T2 MTE & T2 ETE & T3 MTE & T3 ETE \\" _n
file write `fh' "\midrule" _n
file write `fh' "Baseline + FE + BL control & `ab1'`ast1' & `ab2'`ast2' & `ab3'`ast3' & `ab4'`ast4' \\" _n
file write `fh' " & (`ase1') & (`ase2') & (`ase3') & (`ase4') \\" _n
file write `fh' "No baseline control (FE only) & `bb1'`bst1' & `bb2'`bst2' & `bb3'`bst3' & `bb4'`bst4' \\" _n
file write `fh' " & (`bse1') & (`bse2') & (`bse3') & (`bse4') \\" _n
file write `fh' "\midrule" _n
file write `fh' "Wild cluster bootstrap p value & `wb1' & `wb2' & `wb3' & `wb4' \\" _n
file write `fh' "Permutation p value & `pp1' & `pp2' & `pp3' & `pp4' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `n1' & `n2' & `n3' & `n4' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item Notes: Primary endpoint is T3 ETE (column 4). Wild bootstrap uses 999 replications. Permutation p values use 999 reassignments of academy treatment within constituency." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_spec_robust.tex
di "  -> tab_ng_spec_robust.tex"

* 6e) Lee bounds across all wave indices
local y1 "idx_t2_mte"
local y2 "idx_t2_ete"
local y3 "idx_t3_mte"
local y4 "idx_t3_ete"

forvalues j = 1/4 {
    local y "`y`j''"

    cap drop attrit_`j'
    gen attrit_`j' = missing(`y')
    qui summ attrit_`j' if treat == 0
    local ac`j' : di %5.3f r(mean)
    qui summ attrit_`j' if treat == 1
    local at`j' : di %5.3f r(mean)
    local ad`j' : di %5.3f `at`j'' - `ac`j''

    preserve
    keep if !missing(`y', treat, bl_score, constit_id, grade_id, academycode)

    qui reg `y' treat bl_score i.constit_id i.grade_id, vce(cluster academycode)
    local ols`j' : di %7.3f _b[treat]

    local attr_diff = `at`j'' - `ac`j''
    if `attr_diff' > 0 {
        local trim_arm 0
        local trim_frac = `attr_diff' / (1 - `ac`j'')
    }
    else if `attr_diff' < 0 {
        local trim_arm 1
        local trim_frac = -`attr_diff' / (1 - `at`j'')
    }
    else {
        local trim_arm -1
        local trim_frac 0
    }

    if `trim_frac' > 0 & `trim_frac' < 1 {
        qui centile `y' if treat == `trim_arm', centile(`=100*(1-`trim_frac')')
        local cutoff_upper = r(c_1)
        gen _keep_a = !(treat == `trim_arm' & `y' > `cutoff_upper')
        qui reg `y' treat bl_score i.constit_id i.grade_id if _keep_a == 1, vce(cluster academycode)
        local bound_a = _b[treat]
        drop _keep_a

        qui centile `y' if treat == `trim_arm', centile(`=100*`trim_frac'')
        local cutoff_lower = r(c_1)
        gen _keep_b = !(treat == `trim_arm' & `y' < `cutoff_lower')
        qui reg `y' treat bl_score i.constit_id i.grade_id if _keep_b == 1, vce(cluster academycode)
        local bound_b = _b[treat]
        drop _keep_b

        local lb`j' : di %7.3f min(`bound_a', `bound_b')
        local ub`j' : di %7.3f max(`bound_a', `bound_b')
    }
    else {
        local lb`j' "`ols`j''"
        local ub`j' "`ols`j''"
    }
    restore
}

tempname fh
file open `fh' using "$out/tab_ng_lee_bounds.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Lee Bounds by Assessment Wave}" _n
file write `fh' "\label{tab:ng_lee_bounds}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & T2 MTE & T2 ETE & T3 MTE & T3 ETE \\" _n
file write `fh' "\midrule" _n
file write `fh' "Control attrition rate & `ac1' & `ac2' & `ac3' & `ac4' \\" _n
file write `fh' "Treatment attrition rate & `at1' & `at2' & `at3' & `at4' \\" _n
file write `fh' "Difference (T-C) & `ad1' & `ad2' & `ad3' & `ad4' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "OLS ITT & `ols1' & `ols2' & `ols3' & `ols4' \\" _n
file write `fh' "Lee lower bound & `lb1' & `lb2' & `lb3' & `lb4' \\" _n
file write `fh' "Lee upper bound & `ub1' & `ub2' & `ub3' & `ub4' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Attrition is missing outcome in each wave-specific column. Lee bounds trim the lower-attrition arm to match attrition rates." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_lee_bounds.tex
di "  -> tab_ng_lee_bounds.tex"

* 6f) Signal quality — incremental R² and rank persistence (matches tab_signal_quality_alt)
cap drop raw_idx_t2_mte raw_idx_t2_ete raw_idx_t3_mte raw_idx_t3_ete
egen raw_idx_t2_mte = rowmean(percscoret2_mte_maths percscoret2_mte_numeracy)
egen raw_idx_t2_ete = rowmean(percscoret2_ete_maths percscoret2_ete_numeracy)
egen raw_idx_t3_mte = rowmean(percscoret3_mte_maths percscoret3_mte_numeracy)
egen raw_idx_t3_ete = rowmean(percscoret3_ete_maths percscoret3_ete_numeracy)

local w1 "raw_idx_t2_mte"
local w2 "raw_idx_t2_ete"
local w3 "raw_idx_t3_mte"
local w4 "raw_idx_t3_ete"

forvalues j = 1/4 {
    local w "`w`j''"

    qui reg `w' i.grade_id if treat == 0 & !missing(`w', bl_score, grade_id)
    local r2g`j' : di %6.3f e(r2)

    qui reg `w' bl_score i.grade_id if treat == 0 & !missing(`w', bl_score, grade_id)
    local r2b`j' : di %6.3f e(r2)

    local incr`j' : di %6.3f `r2b`j'' - `r2g`j''

    local rank_sum = 0
    local rank_n = 0
    levelsof grade_id if treat == 0, local(gids)
    foreach g of local gids {
        qui count if treat == 0 & grade_id == `g' & !missing(`w', bl_score)
        if r(N) > 10 {
            cap drop _rk_bl _rk_el
            egen _rk_bl = rank(bl_score) if treat == 0 & grade_id == `g' & !missing(`w', bl_score)
            egen _rk_el = rank(`w')      if treat == 0 & grade_id == `g' & !missing(`w', bl_score)
            qui corr _rk_bl _rk_el if treat == 0 & grade_id == `g' & !missing(`w', bl_score)
            local rank_sum = `rank_sum' + r(rho) * r(N)
            local rank_n = `rank_n' + r(N)
        }
    }
    cap drop _rk_bl _rk_el
    if `rank_n' > 0 {
        local rp`j' : di %6.3f `rank_sum' / `rank_n'
    }
    else {
        local rp`j' "--"
    }
}

tempname fh
file open `fh' using "$out/tab_ng_signal_quality.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Signal Quality (Incremental R-squared, Control Group)}" _n
file write `fh' "\label{tab:ng_signal_quality}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & T2 MTE & T2 ETE & T3 MTE & T3 ETE \\" _n
file write `fh' "\midrule" _n
file write `fh' "R-squared grade FE only & `r2g1' & `r2g2' & `r2g3' & `r2g4' \\" _n
file write `fh' "R-squared grade FE + baseline & `r2b1' & `r2b2' & `r2b3' & `r2b4' \\" _n
file write `fh' "Incremental R-squared & `incr1' & `incr2' & `incr3' & `incr4' \\" _n
file write `fh' "Within-grade rank persistence & `rp1' & `rp2' & `rp3' & `rp4' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Control group only. Incremental R-squared = variance explained by adding baseline score to a grade FE only model predicting the raw follow-up index (math+numeracy average). Rank persistence is the within grade Spearman correlation, weighted by grade size. Comparable to Kenya (0.523) and Liberia (0.050)." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_signal_quality.tex
di "  -> tab_ng_signal_quality.tex"
cap drop raw_idx_t2_mte raw_idx_t2_ete raw_idx_t3_mte raw_idx_t3_ete

* 6g) Score variance decomposition by wave index
preserve
gen str64 class_id = string(academycode) + "_" + string(cond(treat == 1, group_id, grade_id))

local y1 "idx_t2_mte"
local y2 "idx_t2_ete"
local y3 "idx_t3_mte"
local y4 "idx_t3_ete"

forvalues j = 1/4 {
    local y "`y`j''"

    qui summ `y' if treat == 0
    local varc`j' : di %7.3f r(Var)
    qui summ `y' if treat == 1
    local vart`j' : di %7.3f r(Var)
    qui summ `y' if !missing(`y')
    local gm = r(mean)

    gen sq_dev_`j' = (`y' - `gm')^2
    qui reg sq_dev_`j' treat bl_score i.constit_id i.grade_id ///
        if !missing(sq_dev_`j', treat, bl_score, constit_id, grade_id), ///
        vce(cluster academycode)
    local vb`j' : di %7.3f _b[treat]
    local vse`j' : di %7.3f _se[treat]
    local vp`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `vp`j''
    local vst`j' "`r(stars)'"
    local n`j' = e(N)

    bys class_id: egen cls_mean_`j' = mean(`y')
    gen sq_within_`j' = (`y' - cls_mean_`j')^2
    qui reg sq_within_`j' treat bl_score i.constit_id i.grade_id ///
        if !missing(sq_within_`j', treat, bl_score, constit_id, grade_id), ///
        vce(cluster academycode)
    local wb`j' : di %7.3f _b[treat]
    local wse`j' : di %7.3f _se[treat]
    local wp`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `wp`j''
    local wst`j' "`r(stars)'"

    gen sq_between_`j' = (cls_mean_`j' - `gm')^2
    qui reg sq_between_`j' treat bl_score i.constit_id i.grade_id ///
        if !missing(sq_between_`j', treat, bl_score, constit_id, grade_id), ///
        vce(cluster academycode)
    local bb`j' : di %7.3f _b[treat]
    local bse`j' : di %7.3f _se[treat]
    local bp`j' = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
    get_stars `bp`j''
    local bst`j' "`r(stars)'"
}

tempname fh
file open `fh' using "$out/tab_ng_score_variance.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Treatment Effect on Score Variance}" _n
file write `fh' "\label{tab:ng_score_variance}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & T2 MTE & T2 ETE & T3 MTE & T3 ETE \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{5}{l}{\textit{Panel A: Aggregate variance}} \\" _n
file write `fh' "Control & `varc1' & `varc2' & `varc3' & `varc4' \\" _n
file write `fh' "Treatment & `vart1' & `vart2' & `vart3' & `vart4' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{5}{l}{\textit{Panel B: Treatment on total variance}} \\" _n
file write `fh' "Treatment & `vb1'`vst1' & `vb2'`vst2' & `vb3'`vst3' & `vb4'`vst4' \\" _n
file write `fh' " & (`vse1') & (`vse2') & (`vse3') & (`vse4') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{5}{l}{\textit{Panel C: Treatment on within class variance}} \\" _n
file write `fh' "Treatment & `wb1'`wst1' & `wb2'`wst2' & `wb3'`wst3' & `wb4'`wst4' \\" _n
file write `fh' " & (`wse1') & (`wse2') & (`wse3') & (`wse4') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{5}{l}{\textit{Panel D: Treatment on between class variance}} \\" _n
file write `fh' "Treatment & `bb1'`bst1' & `bb2'`bst2' & `bb3'`bst3' & `bb4'`bst4' \\" _n
file write `fh' " & (`bse1') & (`bse2') & (`bse3') & (`bse4') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `n1' & `n2' & `n3' & `n4' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Treatment classes are academy by \texttt{group\_id}; control classes are academy by grade. Controls: baseline score, constituency FE, grade FE." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_score_variance.tex
di "  -> tab_ng_score_variance.tex"
restore

* 6h) Ceiling-effects robustness (T3 ETE math)
preserve
qui reg z_percscoret3_ete_maths treat bl_score i.constit_id i.grade_id ///
    if !missing(z_percscoret3_ete_maths, treat, bl_score, constit_id, grade_id), ///
    vce(cluster academycode)
local ols_b  : di %7.3f _b[treat]
local ols_se : di %7.3f _se[treat]
local ols_pv = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
get_stars `ols_pv'
local ols_st "`r(stars)'"
local ols_n = e(N)

qui summ percscoret3_ete_maths if treat == 0 & !missing(percscoret3_ete_maths)
local raw_sd = r(sd)
qui count if percscoret3_ete_maths >= 100 & !missing(percscoret3_ete_maths)
local n_at_ceil = r(N)
qui tobit percscoret3_ete_maths treat bl_score i.constit_id i.grade_id ///
    if !missing(percscoret3_ete_maths, treat, bl_score, constit_id, grade_id), ///
    ul(100) vce(cluster academycode)
local tobit_b_raw = _b[treat]
local tobit_se_raw = _se[treat]
local tobit_b : di %7.3f `tobit_b_raw' / `raw_sd'
local tobit_se : di %7.3f `tobit_se_raw' / `raw_sd'
local tobit_pv = 2 * normal(-abs(`tobit_b_raw' / `tobit_se_raw'))
get_stars `tobit_pv'
local tobit_st "`r(stars)'"
local tobit_n = e(N)

xtile _bl_pct = bl_score, nq(10)
qui reg z_percscoret3_ete_maths treat bl_score i.constit_id i.grade_id ///
    if _bl_pct < 10 & !missing(z_percscoret3_ete_maths, treat, bl_score, constit_id, grade_id), ///
    vce(cluster academycode)
local trim_b : di %7.3f _b[treat]
local trim_se : di %7.3f _se[treat]
local trim_pv = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
get_stars `trim_pv'
local trim_st "`r(stars)'"
local trim_n = e(N)
drop _bl_pct

tempname fh
file open `fh' using "$out/tab_ng_ceiling.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Robustness to Ceiling Effects (T3 ETE Math)}" _n
file write `fh' "\label{tab:ng_ceiling}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) OLS & (2) Tobit & (3) Trimmed OLS \\" _n
file write `fh' "\midrule" _n
file write `fh' "Treatment & `ols_b'`ols_st' & `tobit_b'`tobit_st' & `trim_b'`trim_st' \\" _n
file write `fh' " & (`ols_se') & (`tobit_se') & (`trim_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `ols_n' & `tobit_n' & `trim_n' \\" _n
file write `fh' "Right-censored obs. & & `n_at_ceil' & \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Column (2) is Tobit on raw percent score with upper limit 100, normalized by control\mbox{-}group SD. Column (3) drops top baseline decile." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_ceiling.tex
di "  -> tab_ng_ceiling.tex"
restore

* ═══════════════════════════════════════════════════════════════════════════
* 7. DISPERSION, PEER EFFECTS, ACCOUNTING, CLASSROOM REALLOCATION,
*    TRACK BINS, CLASS-SIZE CONTROL
* ═══════════════════════════════════════════════════════════════════════════

* ── Construct classroom ID and classroom-level variables ────────────────
use "$out/analysis_nigeria_wide.dta", clear
encode constituency, gen(constit_id)
encode gradename, gen(grade_id)

qui summ bl_score
gen std_bl = (bl_score - r(mean)) / r(sd) if !missing(bl_score)

gen str64 class_id = string(academycode) + "_" + ///
    cond(treat == 1, string(group_id), string(grade_id))
encode class_id, gen(class_num)

bys class_num: egen class_mean_bl = mean(std_bl)
bys class_num: egen class_sd_bl = sd(std_bl)
bys class_num: egen class_size = count(studyid)

gen dev_bl = abs(std_bl - class_mean_bl) if !missing(std_bl)

bys class_num: egen peer_sum_bl = total(std_bl) if !missing(std_bl)
bys class_num: egen peer_n_bl = count(std_bl) if !missing(std_bl)
gen peer_lo_bl = (peer_sum_bl - std_bl) / (peer_n_bl - 1) if peer_n_bl > 1

egen bl_decile = xtile(bl_score), n(10)
egen bl_ventile = xtile(bl_score), n(20)

bys class_num: egen n_grades_in_class = nvals(grade_id) if !missing(grade_id)
bys class_num: egen grade_var_in_class = sd(grade_id) if !missing(grade_id)
replace grade_var_in_class = grade_var_in_class^2 if !missing(grade_var_in_class)
replace grade_var_in_class = 0 if missing(grade_var_in_class) & !missing(class_num)

* 7a) Dispersion first stage (tab_ng_dispersion.tex)
di _n "=== 7a. Dispersion first stage ==="

local primary "idx_t3_ete"

local y1 "dev_bl"
foreach v in idx_t2_mte idx_t2_ete idx_t3_mte idx_t3_ete {
    bys class_num: egen cm_`v' = mean(`v')
    gen dev_`v' = abs(`v' - cm_`v') if !missing(`v')
}
local y2 "dev_idx_t2_ete"
local y3 "dev_idx_t3_ete"

tempname fh
file open `fh' using "$out/tab_ng_dispersion.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria: Effect on Within-Class Dispersion}" _n
file write `fh' "\label{tab:ng_dispersion}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) Baseline & (2) T2 ETE & (3) T3 ETE \\" _n
file write `fh' "\midrule" _n

local j = 0
foreach y in `y1' `y2' `y3' {
    local ++j
    local ctrl "bl_score i.constit_id i.grade_id"
    if `j' == 1 local ctrl "i.constit_id i.grade_id"
    qui reg `y' treat `ctrl' if !missing(`y', treat), vce(cluster academycode)
    local b`j' : di %7.3f _b[treat]
    local se`j' : di %7.3f _se[treat]
    local pv`j' = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
    get_stars `pv`j''
    local st`j' "`r(stars)'"
    local n`j' = e(N)
    qui summ `y' if treat == 0 & e(sample)
    local cm`j' : di %7.3f r(mean)
}

file write `fh' "Treatment & `b1'`st1' & `b2'`st2' & `b3'`st3' \\" _n
file write `fh' " & (`se1') & (`se2') & (`se3') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Control Mean & `cm1' & `cm2' & `cm3' \\" _n
file write `fh' "N & `n1' & `n2' & `n3' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Outcome is absolute deviation of student score from classroom mean. Classroom = academy $\times$ group (treatment) or academy $\times$ grade (control). Baseline dispersion column omits baseline control. All columns include constituency and grade FE. SEs clustered at academy. ***, **, and * indicate 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_dispersion.tex
di "  -> tab_ng_dispersion.tex"


* 7b) Classroom reallocation (tab_ng_classroom_reallocation.tex)
di _n "=== 7b. Classroom reallocation ==="

preserve
bys class_num: keep if _n == 1

foreach arm in 0 1 {
    qui summ class_size if treat == `arm'
    local cs_`arm' : di %6.1f r(mean)
    qui summ grade_var_in_class if treat == `arm'
    local gv_`arm' : di %6.3f r(mean)
    qui summ n_grades_in_class if treat == `arm'
    local ng_`arm' : di %6.3f r(mean)
    qui summ class_sd_bl if treat == `arm'
    local sd_`arm' : di %6.3f r(mean)
    qui summ class_mean_bl if treat == `arm'
    local pm_`arm' : di %6.3f r(mean)
}

tempname fh
file open `fh' using "$out/tab_ng_classroom_reallocation.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria: Classroom Reallocation under Ability Grouping}" _n
file write `fh' "\label{tab:ng_classroom_reallocation}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' " & Control & Treatment \\" _n
file write `fh' "\midrule" _n
file write `fh' "Class size & `cs_0' & `cs_1' \\" _n
file write `fh' "Within class grade variance & `gv_0' & `gv_1' \\" _n
file write `fh' "Number of grades in class & `ng_0' & `ng_1' \\" _n
file write `fh' "Within class baseline SD & `sd_0' & `sd_1' \\" _n
file write `fh' "Peer mean baseline ability & `pm_0' & `pm_1' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Arm-specific means at the classroom level. Treatment classrooms are academy-by-group; control classrooms are academy-by-grade." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_classroom_reallocation.tex
di "  -> tab_ng_classroom_reallocation.tex"
restore


* 7c) Peer effects — BH style (tab_ng_peer_effects.tex)
di _n "=== 7c. Peer effects (BH) ==="

egen dt_cell = group(bl_decile treat grade_id)

qui reg idx_t3_ete peer_lo_bl i.dt_cell i.constit_id, vce(cluster academycode)
local bh_b  : di %7.3f _b[peer_lo_bl]
local bh_se : di %7.3f _se[peer_lo_bl]
local bh_pv = 2 * ttail(e(df_r), abs(_b[peer_lo_bl]/_se[peer_lo_bl]))
get_stars `bh_pv'
local bh_st "`r(stars)'"
local bh_n = e(N)

qui reg idx_t2_ete peer_lo_bl i.dt_cell i.constit_id, vce(cluster academycode)
local bh2_b  : di %7.3f _b[peer_lo_bl]
local bh2_se : di %7.3f _se[peer_lo_bl]
local bh2_pv = 2 * ttail(e(df_r), abs(_b[peer_lo_bl]/_se[peer_lo_bl]))
get_stars `bh2_pv'
local bh2_st "`r(stars)'"
local bh2_n = e(N)

tempname fh
file open `fh' using "$out/tab_ng_peer_effects.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria: Peer Composition Effects (Borusyak-Hull)}" _n
file write `fh' "\label{tab:ng_peer_effects}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) T2 ETE Index & (2) T3 ETE Index \\" _n
file write `fh' "\midrule" _n
file write `fh' "Leave-out peer mean & `bh2_b'`bh2_st' & `bh_b'`bh_st' \\" _n
file write `fh' " & (`bh2_se') & (`bh_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `bh2_n' & `bh_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Leave-out peer mean is the standardized mean baseline score of all other students in the same classroom (academy $\times$ group for treated, academy $\times$ grade for control), excluding the focal student. Controls: baseline-decile $\times$ treatment $\times$ grade FE, constituency FE. SEs clustered at academy. ***, **, and * indicate 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_peer_effects.tex
di "  -> tab_ng_peer_effects.tex"


* 7d) Accounting decomposition (tab_ng_suffstat.tex)
di _n "=== 7d. Accounting decomposition ==="

qui reg idx_t3_ete treat bl_score i.constit_id i.grade_id ///
    if !missing(idx_t3_ete, treat, bl_score, constit_id, grade_id), ///
    vce(cluster academycode)
local itt_b  : di %7.3f _b[treat]
local itt_se : di %7.3f _se[treat]

qui summ peer_lo_bl if treat == 1 & !missing(idx_t3_ete, peer_lo_bl)
local peer_t = r(mean)
qui summ peer_lo_bl if treat == 0 & !missing(idx_t3_ete, peer_lo_bl)
local peer_c = r(mean)
local d_peer : di %7.3f `peer_t' - `peer_c'

local peer_contrib : di %7.3f `bh_b' * (`peer_t' - `peer_c')

qui summ dev_bl if treat == 1 & !missing(idx_t3_ete)
local disp_t = r(mean)
qui summ dev_bl if treat == 0 & !missing(idx_t3_ete)
local disp_c = r(mean)
local d_disp : di %7.3f `disp_c' - `disp_t'

qui summ class_size if treat == 1 & !missing(idx_t3_ete)
local cs_t = r(mean)
qui summ class_size if treat == 0 & !missing(idx_t3_ete)
local cs_c = r(mean)
local d_cs : di %5.1f `cs_t' - `cs_c'

local remainder : di %7.3f `itt_b' - `peer_contrib'

tempname fh
file open `fh' using "$out/tab_ng_suffstat.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria: Peer Effects and Accounting Decomposition (T3 ETE)}" _n
file write `fh' "\label{tab:ng_suffstat}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{2}{l}{\textit{Panel A: Peer/rank composite}} \\" _n
file write `fh' "Effect of 1 SD increase in peer mean & `bh_b'`bh_st' \\" _n
file write `fh' " & (`bh_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{2}{l}{\textit{Panel B: Treatment-induced shifts}} \\" _n
file write `fh' "$\Delta$ within class dispersion (C $-$ T) & `d_disp' \\" _n
file write `fh' "$\Delta$ peer composition (T $-$ C) & `d_peer' \\" _n
file write `fh' "$\Delta$ class size (T $-$ C, student-wtd.) & `d_cs' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{2}{l}{\textit{Panel C: Accounting}} \\" _n
file write `fh' "Overall ITT & `itt_b' (`itt_se') \\" _n
file write `fh' "Peer/rank contribution ($\hat{\zeta} \times \Delta\bar{\theta}$) & `peer_contrib' \\" _n
file write `fh' "Remainder & `remainder' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Panel A reports the BH peer estimate from regressing the T3 ETE index on leave-out peer mean, conditioning on baseline-decile $\times$ treatment $\times$ grade FE and constituency FE, clustered at academy. Panel B reports student-weighted mean treatment control differences in the T3 accounting sample. Classroom level means are reported separately in Table~\ref{tab:ng_classroom_reallocation}. Panel C decomposes the ITT into the peer channel and a remainder." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_suffstat.tex
di "  -> tab_ng_suffstat.tex"


* 7e) Track ability bins (tab_ng_track_bins.tex)
di _n "=== 7e. Track ability bins ==="

tempname fh
file open `fh' using "$out/tab_ng_track_bins.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria: Treatment Effects by Two-Group Track Position and Within-Group Ability Tercile (T3 ETE)}" _n
file write `fh' "\label{tab:ng_track_bins}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{llcccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Group & Ability Bin & ITT & SE & p value & N \\" _n
file write `fh' "\midrule" _n

foreach gval in 1 2 {
    if `gval' == 1 local glab "Red"
    if `gval' == 2 local glab "Blue/Yellow"

    cap drop _within_terc
    egen _within_terc = xtile(bl_score) if cond(`gval' == 1, group_id == 1, inlist(group_id, 2, 3)) & !missing(bl_score), n(3)

    local first = 1
    forvalues terc = 1/3 {
        if `terc' == 1 local tlab "Bottom"
        if `terc' == 2 local tlab "Middle"
        if `terc' == 3 local tlab "Top"

        cap qui reg idx_t3_ete treat bl_score i.constit_id i.grade_id ///
            if cond(`gval' == 1, group_id == 1, inlist(group_id, 2, 3)) & _within_terc == `terc' ///
            & !missing(idx_t3_ete, treat, bl_score, constit_id, grade_id), ///
            vce(cluster academycode)
        if _rc == 0 & e(N) > 10 {
            local tb : di %7.3f _b[treat]
            local tse : di %7.3f _se[treat]
            local tpv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
            get_stars `tpv'
            local tst "`r(stars)'"
            local tpvf : di %5.3f `tpv'
            local tn = e(N)
        }
        else {
            local tb "--"
            local tse "--"
            local tpvf "--"
            local tst ""
            local tn "--"
        }

        if `first' {
            file write `fh' "`glab' & `tlab' & `tb'`tst' & (`tse') & `tpvf' & `tn' \\" _n
            local first = 0
        }
        else {
            file write `fh' " & `tlab' & `tb'`tst' & (`tse') & `tpvf' & `tn' \\" _n
        }
    }
    file write `fh' "\addlinespace" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Nigeria is grouped using the preferred two-group collapse: Red versus Blue/Yellow. Within-group ability terciles are based on baseline score. OLS with baseline score, constituency FE, grade FE, SEs clustered at academy. ***, **, and * indicate 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_track_bins.tex
di "  -> tab_ng_track_bins.tex"
cap drop _within_terc


* 7f) Class size control (tab_ng_classsize_ctrl.tex)
di _n "=== 7f. Class size control ==="

gen upper_group = inlist(group_id, 2, 3) if !missing(group_id)
gen treat_x_upper = treat * upper_group

qui reg idx_t3_ete treat treat_x_upper upper_group bl_score ///
    i.constit_id i.grade_id ///
    if !missing(idx_t3_ete, treat, treat_x_upper, upper_group, bl_score, constit_id, grade_id), ///
    vce(cluster academycode)
local no_lower_b  : di %7.3f _b[treat]
local no_lower_se : di %7.3f _se[treat]
local no_lower_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `no_lower_pv'
local no_lower_st "`r(stars)'"
local no_txu_b  : di %7.3f _b[treat_x_upper]
local no_txu_se : di %7.3f _se[treat_x_upper]
local no_txu_pv = 2 * ttail(e(df_r), abs(_b[treat_x_upper]/_se[treat_x_upper]))
get_stars `no_txu_pv'
local no_txu_st "`r(stars)'"
qui lincom treat + treat_x_upper
local no_upper_b  : di %7.3f r(estimate)
local no_upper_se : di %7.3f r(se)
local no_upper_pv = 2 * ttail(e(df_r), abs(r(estimate)/r(se)))
get_stars `no_upper_pv'
local no_upper_st "`r(stars)'"
local no_n = e(N)

qui reg idx_t3_ete treat treat_x_upper upper_group bl_score class_size ///
    i.constit_id i.grade_id ///
    if !missing(idx_t3_ete, treat, treat_x_upper, upper_group, bl_score, class_size, constit_id, grade_id), ///
    vce(cluster academycode)
local cs_lower_b  : di %7.3f _b[treat]
local cs_lower_se : di %7.3f _se[treat]
local cs_lower_pv = 2 * ttail(e(df_r), abs(_b[treat]/_se[treat]))
get_stars `cs_lower_pv'
local cs_lower_st "`r(stars)'"
local cs_txu_b  : di %7.3f _b[treat_x_upper]
local cs_txu_se : di %7.3f _se[treat_x_upper]
local cs_txu_pv = 2 * ttail(e(df_r), abs(_b[treat_x_upper]/_se[treat_x_upper]))
get_stars `cs_txu_pv'
local cs_txu_st "`r(stars)'"
qui lincom treat + treat_x_upper
local cs_upper_b  : di %7.3f r(estimate)
local cs_upper_se : di %7.3f r(se)
local cs_upper_pv = 2 * ttail(e(df_r), abs(r(estimate)/r(se)))
get_stars `cs_upper_pv'
local cs_upper_st "`r(stars)'"
local cs_cs_b  : di %7.3f _b[class_size]
local cs_cs_se : di %7.3f _se[class_size]
local cs_n = e(N)

local ds = char(36)

tempname fh
file open `fh' using "$out/tab_ng_classsize_ctrl.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria: Treatment Effects With and Without Class-Size Controls (T3 ETE)}" _n
file write `fh' "\label{tab:ng_classsize_ctrl}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) No CS & (2) With CS \\" _n
file write `fh' "\midrule" _n
file write `fh' "Lower track (Treatment) & `no_lower_b'`no_lower_st' & `cs_lower_b'`cs_lower_st' \\" _n
file write `fh' " & (`no_lower_se') & (`cs_lower_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "T `ds'\times`ds' Upper & `no_txu_b'`no_txu_st' & `cs_txu_b'`cs_txu_st' \\" _n
file write `fh' " & (`no_txu_se') & (`cs_txu_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Upper track total & `no_upper_b'`no_upper_st' & `cs_upper_b'`cs_upper_st' \\" _n
file write `fh' " & (`no_upper_se') & (`cs_upper_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Class size & & `cs_cs_b' \\" _n
file write `fh' " & & (`cs_cs_se') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `no_n' & `cs_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Upper = Blue/Yellow group under the preferred support-aware two-group collapse. Upper track total = Treatment + T `ds'\times`ds' Upper. Controls: baseline score, constituency FE, grade FE. SEs clustered at academy. ***, **, and * indicate 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_classsize_ctrl.tex
di "  -> tab_ng_classsize_ctrl.tex"

drop upper_group treat_x_upper


* 7g) Density decomposition (tab_ng_density_decomp.tex)
di _n "=== 7g. Density decomposition ==="

cap drop _dens _dens_std _dens_terc
gen _dens = 0
levelsof grade_id, local(gids)
foreach g of local gids {
    qui summ bl_score if grade_id == `g' & !missing(bl_score)
    local bw = 1.06 * r(sd) * r(N)^(-0.2)
    if `bw' > 0 {
        qui count if grade_id == `g' & !missing(bl_score)
        local ng = r(N)
        forvalues i = 1/`=_N' {
            if grade_id[`i'] == `g' & !missing(bl_score[`i']) {
                local si = bl_score[`i']
                qui count if grade_id == `g' & !missing(bl_score) ///
                    & abs(bl_score - `si') <= `bw'
                qui replace _dens = r(N) / (`ng' * `bw') in `i'
            }
        }
    }
}
egen _dens_std = std(_dens), by(grade_id)
egen _dens_terc = xtile(_dens_std), n(3)

tempname fh
file open `fh' using "$out/tab_ng_density_decomp.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria: Peer Effect Heterogeneity by Score Density (T3 ETE)}" _n
file write `fh' "\label{tab:ng_density_decomp}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & \multicolumn{3}{c}{Score-density tercile} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
file write `fh' " & (1) Low & (2) Medium & (3) High \\" _n
file write `fh' " & (tails) & & (middle) \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{4}{l}{\textit{Panel A: BH peer estimate by density tercile}} \\" _n

forvalues d = 1/3 {
    cap qui reg idx_t3_ete peer_lo_bl i.dt_cell i.constit_id ///
        if _dens_terc == `d', vce(cluster academycode)
    if _rc == 0 & e(N) > 10 {
        local db`d' : di %7.3f _b[peer_lo_bl]
        local dse`d' : di %7.3f _se[peer_lo_bl]
        local dpv`d' = 2 * ttail(e(df_r), abs(_b[peer_lo_bl]/_se[peer_lo_bl]))
        get_stars `dpv`d''
        local dst`d' "`r(stars)'"
        local dn`d' = e(N)
    }
    else {
        local db`d' "--"
        local dse`d' "--"
        local dst`d' ""
        local dn`d' "--"
    }
}

file write `fh' "Peer mean ($\hat{\zeta}$) & `db1'`dst1' & `db2'`dst2' & `db3'`dst3' \\" _n
file write `fh' " & (`dse1') & (`dse2') & (`dse3') \\" _n
file write `fh' "N & `dn1' & `dn2' & `dn3' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\midrule" _n
file write `fh' " & \multicolumn{3}{c}{Pooled interaction} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
file write `fh' "\multicolumn{4}{l}{\textit{Panel B: Interaction specification}} \\" _n

gen _peer_x_dens = peer_lo_bl * _dens_std
cap qui reg idx_t3_ete peer_lo_bl _peer_x_dens i.dt_cell i.constit_id, ///
    vce(cluster academycode)
if _rc == 0 {
    local int_b : di %7.3f _b[peer_lo_bl]
    local int_d : di %7.3f _b[_peer_x_dens]
    local int_dse : di %7.3f _se[_peer_x_dens]
}
else {
    local int_b "--"
    local int_d "--"
    local int_dse "--"
}

file write `fh' "Peer mean ($\hat{\zeta}$) & \multicolumn{3}{c}{`int_b'} \\" _n
file write `fh' "Peer $\times$ density ($\approx \hat{\eta}$) & \multicolumn{3}{c}{`int_d'} \\" _n
file write `fh' " & \multicolumn{3}{c}{(`int_dse')} \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Panel A reports BH peer estimates by tercile of baseline score density. Panel B interacts peer mean with standardized density. All specifications include baseline-decile $\times$ treatment $\times$ grade FE and constituency FE. SEs clustered at academy. ***, **, and * indicate 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
copy_to_paper tab_ng_density_decomp.tex
di "  -> tab_ng_density_decomp.tex"

cap drop _dens _dens_std _dens_terc _peer_x_dens


di _n "{hline 70}"
di "Nigeria analysis tables complete."
di "Tables written to:"
di "  $out"
di "  $paper"
di "{hline 70}"
