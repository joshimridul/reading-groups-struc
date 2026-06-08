/*
02b_nigeria_two_group.do — Nigeria preferred two-group reduced form
================================================================
Estimates Nigeria reduced-form effects under the preferred two-group
collapse used in the manuscript.

The main collapse is Red versus Blue+Yellow, which treats the sparse Yellow
cell as part of a broader higher-level instructional group. Unrestricted
Red/Blue/Yellow estimates are reported separately as the appendix
transparency table.
*/

di _n "{hline 70}"
di "02b_nigeria_two_group.do — Nigeria preferred two-group reduced form"
di "{hline 70}"
set more off

if "$root" == "" {
    local pwd = c(pwd)
    if fileexists("`pwd'/4_Stata2/02b_nigeria_two_group.do") {
        global root "`pwd'"
    }
    else if fileexists("`pwd'/02b_nigeria_two_group.do") {
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

cap program drop fit_twogroup
program define fit_twogroup, rclass
    syntax varname, GROUP(varname)

    qui reg `varlist' i.treat##ib0.`group' bl_score i.constit_id i.grade_id ///
        if !missing(`varlist', treat, `group', bl_score, constit_id, grade_id), ///
        vce(cluster academycode)

    return scalar n = e(N)
    return scalar b0 = _b[1.treat]
    return scalar se0 = _se[1.treat]
    return scalar p0 = 2 * ttail(e(df_r), abs(_b[1.treat] / _se[1.treat]))

    return scalar bx = _b[1.treat#1.`group']
    return scalar sex = _se[1.treat#1.`group']
    return scalar px = 2 * ttail(e(df_r), abs(_b[1.treat#1.`group'] / _se[1.treat#1.`group']))

    qui lincom 1.treat + 1.treat#1.`group'
    return scalar b1 = r(estimate)
    return scalar se1 = r(se)
    return scalar p1 = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))

    qui summ `varlist' if treat == 0 & !missing(`varlist', treat, `group', bl_score, constit_id, grade_id)
    return scalar cm = r(mean)
end

cap program drop fit_twogroup_stacked_ete
program define fit_twogroup_stacked_ete, rclass
    syntax, GROUP(varname)

    preserve
    keep studyid academycode treat bl_score constit_id grade_id `group' idx_t2_ete idx_t3_ete
    gen y_2 = idx_t2_ete
    gen y_3 = idx_t3_ete
    reshape long y_, i(studyid) j(wave_id)

    qui reg y_ i.treat##ib0.`group' bl_score i.constit_id i.grade_id i.wave_id ///
        if !missing(y_, treat, `group', bl_score, constit_id, grade_id, wave_id), ///
        vce(cluster academycode)

    return scalar n = e(N)
    return scalar b0 = _b[1.treat]
    return scalar se0 = _se[1.treat]
    return scalar p0 = 2 * ttail(e(df_r), abs(_b[1.treat] / _se[1.treat]))

    return scalar bx = _b[1.treat#1.`group']
    return scalar sex = _se[1.treat#1.`group']
    return scalar px = 2 * ttail(e(df_r), abs(_b[1.treat#1.`group'] / _se[1.treat#1.`group']))

    qui lincom 1.treat + 1.treat#1.`group'
    return scalar b1 = r(estimate)
    return scalar se1 = r(se)
    return scalar p1 = 2 * ttail(e(df_r), abs(r(estimate) / r(se)))

    qui summ y_ if treat == 0 & !missing(y_, treat, `group', bl_score, constit_id, grade_id, wave_id)
    return scalar cm = r(mean)
    restore
end

use "$out/analysis_nigeria_wide.dta", clear
drop if missing(studyid, academycode, treat)
encode constituency, gen(constit_id)
encode gradename, gen(grade_id)

gen byte high2 = inlist(group_id, 2, 3) if !missing(group_id)
label define high2 0 "Red" 1 "Blue/Yellow", replace
label values high2 high2

di _n "Nominal group counts by treatment arm"
tab treat group_id, missing
di _n "Two-group collapse counts by treatment arm"
tab treat high2, missing

local outcomes idx_t2_mte idx_t2_ete idx_t3_mte idx_t3_ete

tempfile results counts
tempname pf
postfile `pf' str24 collapse str28 row str12 col double estimate se p n cm using `results', replace

foreach gspec in high2 {
    local cname "Red vs Blue/Yellow"
    local row0 "Red effect"
    local row1 "Blue/Yellow effect"
    local rowx "Blue/Yellow - Red"

    local j = 1
    foreach y of local outcomes {
        if `j' == 1 local col "T2 MTE"
        if `j' == 2 local col "T2 ETE"
        if `j' == 3 local col "T3 MTE"
        if `j' == 4 local col "T3 ETE"
        fit_twogroup `y', group(`gspec')
        post `pf' ("`cname'") ("`row0'") ("`col'") (r(b0)) (r(se0)) (r(p0)) (r(n)) (r(cm))
        post `pf' ("`cname'") ("`row1'") ("`col'") (r(b1)) (r(se1)) (r(p1)) (r(n)) (r(cm))
        post `pf' ("`cname'") ("`rowx'") ("`col'") (r(bx)) (r(sex)) (r(px)) (r(n)) (r(cm))
        local ++j
    }

    fit_twogroup_stacked_ete, group(`gspec')
    post `pf' ("`cname'") ("`row0'") ("Stacked ETE") (r(b0)) (r(se0)) (r(p0)) (r(n)) (r(cm))
    post `pf' ("`cname'") ("`row1'") ("Stacked ETE") (r(b1)) (r(se1)) (r(p1)) (r(n)) (r(cm))
    post `pf' ("`cname'") ("`rowx'") ("Stacked ETE") (r(bx)) (r(sex)) (r(px)) (r(n)) (r(cm))
}
postclose `pf'

preserve
use `results', clear
export delimited using "$out/ng_two_group_results.csv", replace
save "$out/ng_two_group_results.dta", replace
restore

tempname cf
postfile `cf' str16 sample str12 arm str12 group long n using `counts', replace
foreach y in idx_t2_ete idx_t3_ete {
    foreach t in 0 1 {
        foreach g in 1 2 3 {
            qui count if treat == `t' & group_id == `g' & !missing(`y', bl_score, constit_id, grade_id)
            local arm = cond(`t' == 1, "Treatment", "Control")
            local gl = cond(`g' == 1, "Red", cond(`g' == 2, "Blue", "Yellow"))
            post `cf' ("`y'") ("`arm'") ("`gl'") (r(N))
        }
    }
}
postclose `cf'

preserve
use `counts', clear
export delimited using "$out/ng_two_group_counts.csv", replace
restore

preserve
use `results', clear

cap program drop pull_cell
program define pull_cell, rclass
    syntax, COLLAPSE(string) ROW(string) COL(string)
    qui summ estimate if collapse == "`collapse'" & row == "`row'" & col == "`col'", meanonly
    local b = r(mean)
    qui summ se if collapse == "`collapse'" & row == "`row'" & col == "`col'", meanonly
    local s = r(mean)
    qui summ p if collapse == "`collapse'" & row == "`row'" & col == "`col'", meanonly
    local p = r(mean)
    qui summ n if collapse == "`collapse'" & row == "`row'" & col == "`col'", meanonly
    local n = r(mean)

    local bf : di %7.3f `b'
    local sf : di %7.3f `s'
    get_stars `p'
    return local est "`bf'`r(stars)'"
    return local se "(`sf')"
    return scalar p = `p'
    return scalar n = `n'
end

cap program drop collect_row
program define collect_row, rclass
    syntax, COLLAPSE(string) ROW(string)
    local j = 1
    foreach c in "T2 MTE" "T2 ETE" "T3 MTE" "T3 ETE" "Stacked ETE" {
        pull_cell, collapse("`collapse'") row("`row'") col("`c'")
        return local est`j' "`r(est)'"
        return local se`j' "`r(se)'"
        return scalar n`j' = r(n)
        local ++j
    }
end

collect_row, collapse("Red vs Blue/Yellow") row("Red effect")
forvalues j = 1/5 {
    local a_red_b`j' "`r(est`j')'"
    local a_red_s`j' "`r(se`j')'"
    local a_n`j' = r(n`j')
}
collect_row, collapse("Red vs Blue/Yellow") row("Blue/Yellow effect")
forvalues j = 1/5 {
    local a_high_b`j' "`r(est`j')'"
    local a_high_s`j' "`r(se`j')'"
}
collect_row, collapse("Red vs Blue/Yellow") row("Blue/Yellow - Red")
forvalues j = 1/5 {
    local a_diff_b`j' "`r(est`j')'"
    local a_diff_s`j' "`r(se`j')'"
}

tempname fh
file open `fh' using "$out/tab_ng_two_group.tex", write replace
file write `fh' "\begin{table}[!htbp]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Nigeria Reduced-Form Effects Under the Preferred Two-Group Collapse}" _n
file write `fh' "\label{tab:ng_two_group}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\footnotesize" _n
file write `fh' "\begin{tabular}[t]{lccccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & T2 MTE & T2 ETE & T3 MTE & T3 ETE & Stacked ETE \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{6}{l}{\textit{Effective two-track collapse: Red vs Blue/Yellow}} \\" _n
file write `fh' "Red effect & `a_red_b1' & `a_red_b2' & `a_red_b3' & `a_red_b4' & `a_red_b5' \\" _n
file write `fh' " & `a_red_s1' & `a_red_s2' & `a_red_s3' & `a_red_s4' & `a_red_s5' \\" _n
file write `fh' "Blue/Yellow effect & `a_high_b1' & `a_high_b2' & `a_high_b3' & `a_high_b4' & `a_high_b5' \\" _n
file write `fh' " & `a_high_s1' & `a_high_s2' & `a_high_s3' & `a_high_s4' & `a_high_s5' \\" _n
file write `fh' "Blue/Yellow $-$ Red & `a_diff_b1' & `a_diff_b2' & `a_diff_b3' & `a_diff_b4' & `a_diff_b5' \\" _n
file write `fh' " & `a_diff_s1' & `a_diff_s2' & `a_diff_s3' & `a_diff_s4' & `a_diff_s5' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "N & `a_n1' & `a_n2' & `a_n3' & `a_n4' & `a_n5' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item Notes: Outcomes are standardized math+numeracy index outcomes. Each column estimates a treatment-by-two-group interaction with baseline score, constituency fixed effects, and grade fixed effects; the stacked endterm column pools T2 and T3 endterm observations and adds wave fixed effects. Standard errors are clustered at the academy level. The table uses the preferred support-disciplined Nigeria collapse, combining Blue and Yellow into a higher-level group because the realized Yellow cell is thin. ***, **, and * indicate 1\%, 5\%, and 10\% significance." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
restore

copy_to_paper tab_ng_two_group.tex

file open `fh' using "$out/ng_two_group_note.md", write replace
file write `fh' "# Nigeria two-group reduced-form check" _n _n
file write `fh' "The preferred support-disciplined collapse combines Blue and Yellow into a higher-level group and compares it with Red. Unrestricted Red/Blue/Yellow estimates are reported separately as an appendix transparency table." _n _n
file write `fh' "Primary T3 ETE estimates: Red effect = `a_red_b4' `a_red_s4'; Blue/Yellow effect = `a_high_b4' `a_high_s4'; difference = `a_diff_b4' `a_diff_s4'." _n
file write `fh' "Stacked ETE estimates: Red effect = `a_red_b5' `a_red_s5'; Blue/Yellow effect = `a_high_b5' `a_high_s5'; difference = `a_diff_b5' `a_diff_s5'." _n
file close `fh'

di "  -> tab_ng_two_group.tex"
di "  -> ng_two_group_results.csv"
di "  -> ng_two_group_counts.csv"
di "  -> ng_two_group_note.md"
di _n "{hline 70}"
di "Done."
di "{hline 70}"
