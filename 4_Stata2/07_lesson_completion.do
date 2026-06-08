/*
07_lesson_completion.do — Kenya lesson completion table
=======================================================
Produces: tab_lesson_completion.tex
*/

di _n "{hline 70}"
di "07_lesson_completion.do — Kenya lesson completion"
di "{hline 70}"

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
if "$raw" == "" global raw "$root/2_Data/1_Raw"
if "$out" == "" global out "$root/4_Stata2/output"
cap mkdir "$out"

tempfile lp tch cls

* ── Lesson completion by academy × grade ───────────────────────────────────
import delimited "$raw/Kenya/Grade 1 Reading Club/KE_G1_T3_LessonCompletion_Blinded.csv", clear
gen grade = 1
ds percentage_completed*
local pctvars `r(varlist)'
tokenize `pctvars'
keep academycode grade treatmentassignment `1' `2'
rename `1' lp_comp1
rename `2' lp_comp2
tempfile lp1a
preserve
	keep academycode grade treatmentassignment lp_comp1
	rename lp_comp1 lp_comp
	save `lp1a'
restore
keep academycode grade treatmentassignment lp_comp2
rename lp_comp2 lp_comp
append using `lp1a'
tempfile lp1
save `lp1'

import delimited "$raw/Kenya/Grade 2 Reading Club/KE_G2_T3_LessonCompletion_Blinded.csv", clear
gen grade = 2
ds percentage_completed*
local pctvars `r(varlist)'
tokenize `pctvars'
keep academycode grade treatmentassignment `1' `2'
rename `1' lp_comp1
rename `2' lp_comp2
tempfile lp2a
preserve
	keep academycode grade treatmentassignment lp_comp1
	rename lp_comp1 lp_comp
	save `lp2a'
restore
keep academycode grade treatmentassignment lp_comp2
rename lp_comp2 lp_comp
append using `lp2a'
append using `lp1'
gen treat = (treatmentassignment == "Treatment")
drop treatmentassignment
save `lp'

* ── Teacher attendance by academy × grade ──────────────────────────────────
import delimited "$raw/Kenya/Grade 1 Reading Club/KE_G1_TeacherAttendance_Blinded.csv", clear
gen grade = 1
ds grade*
local attvars `r(varlist)'
tokenize `attvars'
rename `1' tch_attn
keep academycode grade tch_attn
tempfile tch1
save `tch1'

import delimited "$raw/Kenya/Grade 2 Reading Club/KE_G2_TeacherAttendance_Blinded.csv", clear
gen grade = 2
ds grade*
local attvars `r(varlist)'
tokenize `attvars'
rename `1' tch_attn
keep academycode grade tch_attn
append using `tch1'
save `tch'

* ── Class size from analytic data ──────────────────────────────────────────
use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el & !mi(csize)
collapse (mean) csize, by(academycode grade)
save `cls'

* ── Merge analysis sample ───────────────────────────────────────────────────
use `lp', clear
merge m:1 academycode grade using `tch', nogen
merge m:1 academycode grade using `cls', nogen
drop if mi(lp_comp) | mi(treat)

* ── Regressions ─────────────────────────────────────────────────────────────
qui reg lp_comp treat, vce(cluster academycode)
local b1  : di %5.3f _b[treat]
local se1 : di %5.3f _se[treat]
local p1 = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
qui summ lp_comp if treat == 0, meanonly
local cm1 : di %5.3f r(mean)

qui reg lp_comp treat tch_attn if !mi(tch_attn), vce(cluster academycode)
local b2  : di %5.3f _b[treat]
local se2 : di %5.3f _se[treat]
local ta2 : di %5.3f _b[tch_attn]
local tse2: di %5.3f _se[tch_attn]
local p2 = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
local pt2 = 2 * ttail(e(df_r), abs(_b[tch_attn] / _se[tch_attn]))
local n2 = e(N)
qui summ lp_comp if treat == 0 & !mi(tch_attn), meanonly
local cm2 : di %5.3f r(mean)

qui reg lp_comp treat csize if !mi(csize), vce(cluster academycode)
local b3  : di %5.3f _b[treat]
local se3 : di %5.3f _se[treat]
local cs3 : di %5.3f _b[csize]
local cse3: di %5.3f _se[csize]
local p3 = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
local pc3 = 2 * ttail(e(df_r), abs(_b[csize] / _se[csize]))
local n3 = e(N)
qui summ lp_comp if treat == 0 & !mi(csize), meanonly
local cm3 : di %5.3f r(mean)

qui reg lp_comp treat tch_attn csize if !mi(tch_attn) & !mi(csize), vce(cluster academycode)
local b4  : di %5.3f _b[treat]
local se4 : di %5.3f _se[treat]
local ta4 : di %5.3f _b[tch_attn]
local tse4: di %5.3f _se[tch_attn]
local cs4 : di %5.3f _b[csize]
local cse4: di %5.3f _se[csize]
local p4 = 2 * ttail(e(df_r), abs(_b[treat] / _se[treat]))
local pt4 = 2 * ttail(e(df_r), abs(_b[tch_attn] / _se[tch_attn]))
local pc4 = 2 * ttail(e(df_r), abs(_b[csize] / _se[csize]))
local n4 = e(N)
qui summ lp_comp if treat == 0 & !mi(tch_attn) & !mi(csize), meanonly
local cm4 : di %5.3f r(mean)

qui count
local n1 = r(N)
local n_all = `n1'

cap program drop get_stars
program define get_stars, rclass
	args pval
	local s ""
	if `pval' < 0.10 local s "*"
	if `pval' < 0.05 local s "**"
	if `pval' < 0.01 local s "***"
	return local stars "`s'"
end

get_stars `p1'
local st1 "`r(stars)'"
get_stars `p2'
local st2 "`r(stars)'"
get_stars `p3'
local st3 "`r(stars)'"
get_stars `p4'
local st4 "`r(stars)'"
get_stars `pt2'
local ta_st2 "`r(stars)'"
get_stars `pt4'
local ta_st4 "`r(stars)'"
get_stars `pc3'
local cs_st3 "`r(stars)'"
get_stars `pc4'
local cs_st4 "`r(stars)'"

tempname fh
file open `fh' using "$out/tab_lesson_completion.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Treatment Effects on Lesson Completion Rate (Kenya)}" _n
file write `fh' "\label{tab:lesson_completion}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{l*{4}{>{\centering\arraybackslash}m{2.65cm}}}" _n
file write `fh' "\toprule" _n
file write `fh' " & \multicolumn{4}{c}{Lesson completion rate} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' " & (1) & (2) & (3) & (4) \\" _n
file write `fh' "\midrule" _n
file write `fh' "Treat & `b1'`st1' & `b2'`st2' & `b3'`st3' & `b4'`st4' \\" _n
file write `fh' " & [`se1'] & [`se2'] & [`se3'] & [`se4'] \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Teacher attendance &  & `ta2'`ta_st2' &  & `ta4'`ta_st4' \\" _n
file write `fh' " &  & [`tse2'] &  & [`tse4'] \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Class size &  &  & `cs3'`cs_st3' & `cs4'`cs_st4' \\" _n
file write `fh' " &  &  & [`cse3'] & [`cse4'] \\" _n
file write `fh' "\midrule" _n
file write `fh' "Control mean & `cm1' & `cm2' & `cm3' & `cm4' \\" _n
file write `fh' "Observations & `n_all' & `n2' & `n3' & `n4' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\scriptsize" _n
file write `fh' "\setlength{\emergencystretch}{2em}" _n
file write `fh' "\item \textit{Notes:} Each column reports the coefficient from a regression of lesson completion rate on treatment status. The unit of observation is a school--subject--grade cell. Lesson completion is the fraction of scripted literacy-revision lessons completed, recorded in NewGlobe's classroom management system. Columns~2--4 add controls for teacher attendance rate and reading class size. Control means are computed in each column's estimation sample. Standard errors are clustered at the school level in brackets. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'

di "  -> tab_lesson_completion.tex"
