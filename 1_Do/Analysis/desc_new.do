
/*==========================================================================

Title: desc_new.do
Author: Mridul Joshi

Description: Exploratory descriptive analysis for noisy measurement /
             ability grouping project.

             Key questions:
             1. How noisy is the baseline test? (score distributions,
                floor/ceiling, baseline-endline signal)
             2. How well did sorting work? (group separation, overlap,
                misclassification)
             3. Do treatment effects vary by baseline ability level?
             4. Did sorting reduce within-group dispersion?

===========================================================================*/


* ===================================================================== *
* -----------------     	    Setup                 ----------------- *
* ===================================================================== *

cap mkdir "${outdir}/desc_new"
local gdir "${outdir}/desc_new"

set scheme s2color



********************************************************************************
***                                                                          ***
***                              KENYA                                       ***
***                                                                          ***
********************************************************************************


use "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", clear

keep if finsamp
keep if inlist(pupil_observed,2,3)


* ===================================================================== *
* 1. SCORE DISTRIBUTIONS — Kenya
* ===================================================================== *

* --- 1a. Summary statistics ---

di ""
di "===== KENYA: SCORE SUMMARY STATISTICS ====="
di ""
di "--- Baseline ---"
tabstat comp_score_bl, by(grade) stats(n mean sd min p10 p25 p50 p75 p90 max skewness kurtosis) columns(statistics)

di "--- Endline ---"
tabstat comp_score_el, by(grade) stats(n mean sd min p10 p25 p50 p75 p90 max skewness kurtosis) columns(statistics)


* --- 1b. Floor and ceiling effects ---
* Need to know the actual min/max of the test

sum comp_score_bl, detail
local bl_min_k = r(min)
local bl_max_k = r(max)

sum comp_score_el, detail
local el_min_k = r(min)
local el_max_k = r(max)

di ""
di "Kenya BL score range: `bl_min_k' to `bl_max_k'"
di "Kenya EL score range: `el_min_k' to `el_max_k'"

gen floor_bl_k  = comp_score_bl == `bl_min_k'
gen ceil_bl_k   = comp_score_bl == `bl_max_k'
gen floor_el_k  = comp_score_el == `el_min_k'
gen ceil_el_k   = comp_score_el == `el_max_k'

di ""
di "--- Floor/Ceiling rates by grade ---"
tabstat floor_bl_k ceil_bl_k floor_el_k ceil_el_k, by(grade) stats(mean) columns(statistics)


* --- 1c. Density plots ---

twoway  (kdensity std_comp_score_bl if treat==0 & grade==1, lcolor(navy) lwidth(medium) lpattern(solid)) ///
		(kdensity std_comp_score_bl if treat==1 & grade==1, lcolor(cranberry) lwidth(medium) lpattern(dash)) ///
		(kdensity std_comp_score_bl if treat==0 & grade==2, lcolor(navy) lwidth(thin) lpattern(solid)) ///
		(kdensity std_comp_score_bl if treat==1 & grade==2, lcolor(cranberry) lwidth(thin) lpattern(dash)), ///
		legend(label(1 "Control, G1") label(2 "Treat, G1") ///
		       label(3 "Control, G2") label(4 "Treat, G2")) ///
		xtitle("Standardized baseline score") ytitle("Density") ///
		title("Kenya: Baseline Score Distribution") ///
		note("Final sample, observed at baseline and endline")
graph export "`gdir'/K_bl_dist.pdf", replace

twoway  (kdensity std_comp_score_el if treat==0 & grade==1, lcolor(navy) lwidth(medium) lpattern(solid)) ///
		(kdensity std_comp_score_el if treat==1 & grade==1, lcolor(cranberry) lwidth(medium) lpattern(dash)) ///
		(kdensity std_comp_score_el if treat==0 & grade==2, lcolor(navy) lwidth(thin) lpattern(solid)) ///
		(kdensity std_comp_score_el if treat==1 & grade==2, lcolor(cranberry) lwidth(thin) lpattern(dash)), ///
		legend(label(1 "Control, G1") label(2 "Treat, G1") ///
		       label(3 "Control, G2") label(4 "Treat, G2")) ///
		xtitle("Standardized endline score") ytitle("Density") ///
		title("Kenya: Endline Score Distribution")
graph export "`gdir'/K_el_dist.pdf", replace


* --- 1d. Baseline-Endline signal: how much does BL predict EL? ---
*     Higher R2 = more signal (less noise) in the baseline test

di ""
di "===== KENYA: BASELINE -> ENDLINE SIGNAL (control group) ====="

reg std_comp_score_el std_comp_score_bl i.grade if treat == 0
di "  R-squared (BL -> EL, control): " %5.3f `e(r2)'
di "  Adj R-sq:                      " %5.3f `e(r2_a)'

* Also: how much does BL score explain conditional on grade fixed effects?
reg std_comp_score_el std_comp_score_bl if treat == 0 & grade == 1
local r2_k_g1 = e(r2)
reg std_comp_score_el std_comp_score_bl if treat == 0 & grade == 2
local r2_k_g2 = e(r2)

di "  R-sq by grade - G1: " %5.3f `r2_k_g1' "  G2: " %5.3f `r2_k_g2'

* Scatter plot: BL vs EL in control group
twoway  (scatter std_comp_score_el std_comp_score_bl if treat==0 & grade==1, ///
         mcolor(navy%20) msymbol(oh) msize(tiny)) ///
        (lfit std_comp_score_el std_comp_score_bl if treat==0 & grade==1, ///
         lcolor(navy) lwidth(medium)) ///
		(scatter std_comp_score_el std_comp_score_bl if treat==0 & grade==2, ///
         mcolor(cranberry%20) msymbol(oh) msize(tiny)) ///
        (lfit std_comp_score_el std_comp_score_bl if treat==0 & grade==2, ///
         lcolor(cranberry) lwidth(medium)), ///
		xtitle("Baseline score (std)") ytitle("Endline score (std)") ///
		title("Kenya: Baseline-Endline Correlation (Control)") ///
		legend(label(1 "Grade 1") label(2 "") label(3 "Grade 2") label(4 ""))
graph export "`gdir'/K_bl_el_scatter.pdf", replace


* --- 1e. ICC: how much variation is between-academy-grade vs. within? ---
*     High ICC on BL -> groups differ systematically (signal)
*     Low ICC on BL -> most variation is within-class (relative noise dominant)

di ""
di "===== KENYA: INTRACLASS CORRELATION (baseline score) ====="
xtmixed std_comp_score_bl i.grade || academycode: || grade:
estat icc
* Rough version using anova if xtmixed is too slow:
*  anova std_comp_score_bl academycode##grade
*  di "Eta-squared (between academy-grade): " (e(ss_1)+e(ss_2)) / e(ss_T)



* ===================================================================== *
* 2. SORTING QUALITY — Kenya
* ===================================================================== *

* In treatment schools: purple=1 is (presumably) the higher ability group
* Check: does purple assignment correlate with baseline score?

di ""
di "===== KENYA: SORTING QUALITY (treatment schools) ====="

* Mean BL score by group
tabstat std_comp_score_bl if treat==1, by(purple) stats(n mean sd) columns(statistics)

* Within-academy-grade: how well separated are the two groups?
* Step 1: compute mean BL score for each group within each academy-grade

preserve
	keep if treat == 1
	keep if !mi(std_comp_score_bl)

	collapse (mean)  mean_bl = std_comp_score_bl ///
	         (sd)    sd_bl   = std_comp_score_bl ///
	         (count) n_bl    = std_comp_score_bl, ///
	         by(academycode grade purple)

	* Reshape: one row per academy-grade, columns for each group
	reshape wide mean_bl sd_bl n_bl, i(academycode grade) j(purple)

	* Separation: difference in group means (positive = purple=1 is higher)
	gen sort_diff = mean_bl1 - mean_bl0
	lab var sort_diff "Mean BL score: high group minus low group"

	* Pooled within-group SD
	gen pooled_sd = sqrt( ((n_bl0-1)*sd_bl0^2 + (n_bl1-1)*sd_bl1^2) / (n_bl0+n_bl1-2) )
	gen sort_d = sort_diff / pooled_sd   // Cohen's d between groups
	lab var sort_d "Cohen's d: BL score separation between groups"

	di ""
	di "--- Distribution of group separation (Cohen's d) ---"
	sum sort_diff sort_d, detail

	* What fraction of schools have correct ordering (high group > low group)?
	gen correct_order = sort_diff > 0
	tabstat correct_order, stats(mean n)
	di "Fraction with correct ordering (high group has higher mean BL score): " ///
	   %5.3f `r(mean)'

	hist sort_d, ///
	    title("Kenya: Ability Group Separation (Cohen's d)") ///
	    xtitle("Cohen's d (BL score, high vs. low group)") ///
	    xline(0, lcolor(red) lpattern(dash)) ///
	    note("Each obs = one academy-grade. Treatment schools only. Red line = 0.")
	graph export "`gdir'/K_sort_separation.pdf", replace

restore


* Step 2: Misclassification rate
*  Define "correct" group = above academy-grade median -> should be high group

preserve
	keep if treat == 1
	keep if !mi(std_comp_score_bl)

	* Academy-grade median
	bys academycode grade: egen med_bl = median(std_comp_score_bl)

	* Correct assignment: above median -> purple=1 (or below -> purple=0)
	* NOTE: verify which value of purple is the high group once you see output
	gen correct_assign = (std_comp_score_bl >= med_bl & purple == 1) | ///
	                     (std_comp_score_bl <  med_bl & purple == 0)
	gen misclassified  = !correct_assign

	di ""
	tabstat misclassified, by(grade) stats(n mean) columns(statistics)
	sum misclassified
	di "Overall misclassification rate (Kenya): " %5.3f `r(mean)'

restore


* Step 3: Density overlap between groups (visual)

twoway  (kdensity std_comp_score_bl if treat==1 & purple==0 & grade==1, ///
         lcolor(cranberry) lwidth(medium) lpattern(dash)) ///
        (kdensity std_comp_score_bl if treat==1 & purple==1 & grade==1, ///
         lcolor(navy) lwidth(medium) lpattern(solid)) ///
		(kdensity std_comp_score_bl if treat==1 & purple==0 & grade==2, ///
         lcolor(cranberry) lwidth(thin) lpattern(dash)) ///
        (kdensity std_comp_score_bl if treat==1 & purple==1 & grade==2, ///
         lcolor(navy) lwidth(thin) lpattern(solid)), ///
		legend(label(1 "Low group, G1") label(2 "High group, G1") ///
		       label(3 "Low group, G2") label(4 "High group, G2")) ///
		xtitle("Standardized baseline score") ytitle("Density") ///
		title("Kenya: BL Score by Ability Group (Treatment Schools)")
graph export "`gdir'/K_group_overlap.pdf", replace


* ===================================================================== *
* 3. TREATMENT EFFECTS BY BASELINE QUARTILE — Kenya
* ===================================================================== *

di ""
di "===== KENYA: TREATMENT EFFECTS BY BASELINE QUARTILE ====="

* Quartiles within grade (so comparison is grade-specific)
cap drop bl_q_new
bys grade: xtile bl_q_new = std_comp_score_bl if !mi(std_comp_score_bl), nq(4)

* Run treatment effect regression for each quartile
* Store results in a matrix
matrix K_TE_byQ = J(4, 4, .)   // rows=quartile, cols=[coef, se, ci_lo, ci_hi]

forval q = 1/4 {
	cap reghdfe std_comp_score_el treat std_comp_score_bl i.grade ///
	    if bl_q_new == `q', a(constituency) vce(clus academycode)
	if !_rc {
		local b  = _b[treat]
		local se = _se[treat]
		matrix K_TE_byQ[`q', 1] = `b'
		matrix K_TE_byQ[`q', 2] = `se'
		matrix K_TE_byQ[`q', 3] = `b' - 1.96*`se'
		matrix K_TE_byQ[`q', 4] = `b' + 1.96*`se'
		di "Q`q': b=" %6.3f `b' "  se=" %6.3f `se' "  N=" `e(N)'
	}
	else {
		di "Q`q': regression failed"
	}
}

* Save and plot
preserve
	clear
	svmat K_TE_byQ, names(col)
	rename c1 coef
	rename c2 se
	rename c3 ci_lo
	rename c4 ci_hi
	gen quartile = _n

	twoway  (rcap ci_hi ci_lo quartile, lcolor(navy) lwidth(medthick)) ///
	        (scatter coef quartile, mcolor(navy) msymbol(O) msize(medium)), ///
	        yline(0, lcolor(gs8) lpattern(dash)) ///
	        xlabel(1 `"Q1"' 2 `"Q2"' 3 `"Q3"' 4 `"Q4"', noticks) ///
	        xtitle("Baseline ability quartile (within grade)") ///
	        ytitle("Treatment effect (std. endline score)") ///
	        title("Kenya: Treatment Effect by Baseline Quartile") ///
	        legend(off) ///
	        note("Within-grade quartiles. 95% CI. Controls: BL score, grade FE, strata FE.")
	graph export "`gdir'/K_te_byquartile.pdf", replace
restore


* Interaction specification (single regression with quartile interactions)
reghdfe std_comp_score_el i.bl_q_new##i.treat std_comp_score_bl i.grade, ///
        a(constituency) vce(clus academycode)

di ""
di "Interaction test: are treatment effects heterogeneous across quartiles?"
testparm i.bl_q_new#i.treat


* ===================================================================== *
* 4. WITHIN-GROUP DISPERSION — Kenya
* ===================================================================== *
*    Did grouping actually reduce within-group spread in BL scores?
*    Compare: SD within ability groups (treat) vs. SD within grade-classes (ctrl)

di ""
di "===== KENYA: WITHIN-GROUP DISPERSION ====="

preserve

	* Treatment: dispersion within ability group (academy x grade x purple)
	keep if treat == 1 & !mi(std_comp_score_bl)
	collapse (sd) sd_within_t = std_comp_score_bl ///
	         (count) n_t = std_comp_score_bl, ///
	         by(academycode grade purple)
	keep if n_t > 3   // require at least 4 students for a meaningful SD
	tempfile disp_treat
	save `disp_treat'
restore

preserve
	* Control: dispersion within grade-class (academy x grade)
	keep if treat == 0 & !mi(std_comp_score_bl)
	collapse (sd) sd_within_c = std_comp_score_bl ///
	         (count) n_c = std_comp_score_bl, ///
	         by(academycode grade)
	keep if n_c > 3
	tempfile disp_ctrl
	save `disp_ctrl'
restore

* Summarize and compare
di "--- Within-group SD (treatment) ---"
use `disp_treat', clear
sum sd_within_t, detail

di "--- Within-class SD (control) ---"
use `disp_ctrl', clear
sum sd_within_c, detail

* Plot both distributions
use `disp_treat', clear
tempfile combo
gen group = "Treatment (within ability group)"
rename sd_within_t sd
save `combo'
use `disp_ctrl', clear
gen group = "Control (within grade-class)"
rename sd_within_c sd
append using `combo'

twoway  (kdensity sd if group=="Control (within grade-class)", ///
         lcolor(navy) lwidth(medium) lpattern(solid)) ///
        (kdensity sd if group=="Treatment (within ability group)", ///
         lcolor(cranberry) lwidth(medium) lpattern(dash)), ///
		legend(label(1 "Control (within grade-class)") ///
		       label(2 "Treatment (within ability group)")) ///
		xtitle("Within-group SD of baseline score") ytitle("Density") ///
		title("Kenya: Did Grouping Reduce Within-Group Dispersion?") ///
		note("Unit of observation: academy-grade(-group)")
graph export "`gdir'/K_dispersion_reduce.pdf", replace


* Reload main Kenya dataset
use "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", clear
keep if finsamp
keep if inlist(pupil_observed,2,3)



********************************************************************************
***                                                                          ***
***                              LIBERIA                                     ***
***                                                                          ***
********************************************************************************


use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear

keep if finsamp == 1


* ===================================================================== *
* 1. SCORE DISTRIBUTIONS — Liberia
* ===================================================================== *

* NOTE: Liberia uses score_bl / score_el and std_score_bl / std_score_el

di ""
di "===== LIBERIA: SCORE SUMMARY STATISTICS ====="

di "--- Baseline ---"
tabstat score_bl, by(grade) stats(n mean sd min p10 p25 p50 p75 p90 max skewness kurtosis) columns(statistics)

di "--- Endline ---"
tabstat score_el, by(grade) stats(n mean sd min p10 p25 p50 p75 p90 max skewness kurtosis) columns(statistics)


sum score_bl, detail
local bl_min_l = r(min)
local bl_max_l = r(max)
sum score_el, detail
local el_min_l = r(min)
local el_max_l = r(max)

di ""
di "Liberia BL score range: `bl_min_l' to `bl_max_l'"
di "Liberia EL score range: `el_min_l' to `el_max_l'"

gen floor_bl_l = score_bl == `bl_min_l'
gen ceil_bl_l  = score_bl == `bl_max_l'
gen floor_el_l = score_el == `el_min_l'
gen ceil_el_l  = score_el == `el_max_l'

tabstat floor_bl_l ceil_bl_l floor_el_l ceil_el_l, by(grade) stats(mean) columns(statistics)


* Density plots by grade (too many grades to combine, do by grade pair)
twoway  (kdensity std_score_bl if treat==0 & grade==1, lcolor(navy) lwidth(medium)) ///
        (kdensity std_score_bl if treat==1 & grade==1, lcolor(cranberry) lwidth(medium) lpattern(dash)) ///
        (kdensity std_score_bl if treat==0 & grade==2, lcolor(blue) lwidth(thin)) ///
        (kdensity std_score_bl if treat==1 & grade==2, lcolor(red) lwidth(thin) lpattern(dash)), ///
		legend(label(1 "Ctrl G1") label(2 "Treat G1") label(3 "Ctrl G2") label(4 "Treat G2")) ///
		xtitle("Standardized baseline score") title("Liberia: BL Score, Grades 1-2")
graph export "`gdir'/L_bl_dist_g12.pdf", replace

twoway  (kdensity std_score_bl if treat==0 & grade==3, lcolor(navy) lwidth(medium)) ///
        (kdensity std_score_bl if treat==1 & grade==3, lcolor(cranberry) lwidth(medium) lpattern(dash)) ///
        (kdensity std_score_bl if treat==0 & grade==4, lcolor(blue) lwidth(thin)) ///
        (kdensity std_score_bl if treat==1 & grade==4, lcolor(red) lwidth(thin) lpattern(dash)), ///
		legend(label(1 "Ctrl G3") label(2 "Treat G3") label(3 "Ctrl G4") label(4 "Treat G4")) ///
		xtitle("Standardized baseline score") title("Liberia: BL Score, Grades 3-4")
graph export "`gdir'/L_bl_dist_g34.pdf", replace


* Baseline-Endline signal
di ""
di "===== LIBERIA: BASELINE -> ENDLINE SIGNAL (control group) ====="

reg std_score_el std_score_bl i.grade if treat == 0
di "  R-squared (BL -> EL, control): " %5.3f `e(r2)'

forval g = 1/4 {
	cap reg std_score_el std_score_bl if treat == 0 & grade == `g'
	if !_rc di "  R-sq grade `g': " %5.3f `e(r2)'
}

twoway  (scatter std_score_el std_score_bl if treat==0, ///
         mcolor(navy%15) msymbol(oh) msize(tiny)) ///
        (lfit std_score_el std_score_bl if treat==0, ///
         lcolor(navy) lwidth(medium)), ///
		by(grade, title("Liberia: Baseline-Endline Correlation (Control)")) ///
		xtitle("Baseline score (std)") ytitle("Endline score (std)") ///
		legend(off)
graph export "`gdir'/L_bl_el_scatter.pdf", replace


* ICC
di ""
di "===== LIBERIA: INTRACLASS CORRELATION (baseline score) ====="
xtmixed std_score_bl i.grade || academycode: || grade:
estat icc


* ===================================================================== *
* 2. SORTING QUALITY — Liberia
* ===================================================================== *

* NOTE: Liberia's group indicator variable — check what variable marks the
*       high/low group within treatment schools. Update `grpvar' below if needed.
*       Based on prepare file, `ggroup' is the grade-group, not the ability-group.
*       The within-school ability group may be stored differently.
*       CHECK: list the relevant variables for a few treatment schools to confirm.

di ""
di "===== LIBERIA: GROUP VARIABLE CHECK (first 5 treatment schools) ====="
tab academycode if treat == 1, sort
* Inspect a few schools to identify the ability group variable
bys academycode grade: tab treat if treat == 1   // see if there's a subgroup indicator

* Placeholder: if Liberia also uses `purple', substitute below
* local grpvar "purple"    // <- UPDATE if different variable name
cap confirm variable purple
if !_rc {
	local grpvar "purple"
	di "Using 'purple' as ability group indicator"
}
else {
	di "WARNING: 'purple' not found in Liberia data. Check group variable name."
	di "Sorting quality analysis skipped until variable is confirmed."
}

cap {   // wrap in cap so file runs even if grpvar is missing

	preserve
		keep if treat == 1
		keep if !mi(std_score_bl)

		collapse (mean)  mean_bl = std_score_bl ///
		         (sd)    sd_bl   = std_score_bl ///
		         (count) n_bl    = std_score_bl, ///
		         by(academycode grade `grpvar')

		reshape wide mean_bl sd_bl n_bl, i(academycode grade) j(`grpvar')

		gen sort_diff = mean_bl1 - mean_bl0
		gen pooled_sd = sqrt( ((n_bl0-1)*sd_bl0^2 + (n_bl1-1)*sd_bl1^2) / (n_bl0+n_bl1-2) )
		gen sort_d = sort_diff / pooled_sd

		sum sort_d, detail
		gen correct_order = sort_diff > 0
		tabstat correct_order, stats(mean n)

		hist sort_d, ///
		    title("Liberia: Ability Group Separation (Cohen's d)") ///
		    xtitle("Cohen's d (BL score, high vs. low group)") ///
		    xline(0, lcolor(red) lpattern(dash))
		graph export "`gdir'/L_sort_separation.pdf", replace
	restore

	preserve
		keep if treat == 1 & !mi(std_score_bl)
		bys academycode grade: egen med_bl = median(std_score_bl)
		gen correct_assign = (std_score_bl >= med_bl & `grpvar'==1) | ///
		                     (std_score_bl <  med_bl & `grpvar'==0)
		gen misclassified  = !correct_assign
		tabstat misclassified, by(grade) stats(n mean) columns(statistics)
		sum misclassified
		di "Overall misclassification rate (Liberia): " %5.3f `r(mean)'
	restore
}


* ===================================================================== *
* 3. TREATMENT EFFECTS BY BASELINE QUARTILE — Liberia
* ===================================================================== *

di ""
di "===== LIBERIA: TREATMENT EFFECTS BY BASELINE QUARTILE ====="

cap drop bl_q_new
bys grade: xtile bl_q_new = std_score_bl if !mi(std_score_bl), nq(4)

matrix L_TE_byQ = J(4, 4, .)

forval q = 1/4 {
	cap reghdfe std_score_el treat std_score_bl i.grade ///
	    if bl_q_new == `q', a(strata) vce(clus ggroup)
	if !_rc {
		local b  = _b[treat]
		local se = _se[treat]
		matrix L_TE_byQ[`q', 1] = `b'
		matrix L_TE_byQ[`q', 2] = `se'
		matrix L_TE_byQ[`q', 3] = `b' - 1.96*`se'
		matrix L_TE_byQ[`q', 4] = `b' + 1.96*`se'
		di "Q`q': b=" %6.3f `b' "  se=" %6.3f `se' "  N=" `e(N)'
	}
	else {
		di "Q`q': regression failed"
	}
}

preserve
	clear
	svmat L_TE_byQ, names(col)
	rename c1 coef
	rename c2 se
	rename c3 ci_lo
	rename c4 ci_hi
	gen quartile = _n

	twoway  (rcap ci_hi ci_lo quartile, lcolor(cranberry) lwidth(medthick)) ///
	        (scatter coef quartile, mcolor(cranberry) msymbol(O) msize(medium)), ///
	        yline(0, lcolor(gs8) lpattern(dash)) ///
	        xlabel(1 `"Q1"' 2 `"Q2"' 3 `"Q3"' 4 `"Q4"', noticks) ///
	        xtitle("Baseline ability quartile (within grade)") ///
	        ytitle("Treatment effect (std. endline score)") ///
	        title("Liberia: Treatment Effect by Baseline Quartile") ///
	        legend(off) ///
	        note("Within-grade quartiles. 95% CI. Controls: BL score, grade FE, strata FE.")
	graph export "`gdir'/L_te_byquartile.pdf", replace
restore

reghdfe std_score_el i.bl_q_new##i.treat std_score_bl i.grade, ///
        a(strata) vce(clus ggroup)
testparm i.bl_q_new#i.treat


* ===================================================================== *
* 4. WITHIN-GROUP DISPERSION — Liberia
* ===================================================================== *

di ""
di "===== LIBERIA: WITHIN-GROUP DISPERSION ====="

cap {
	preserve
		keep if treat == 1 & !mi(std_score_bl)
		collapse (sd) sd_within_t = std_score_bl ///
		         (count) n_t = std_score_bl, ///
		         by(academycode grade `grpvar')
		keep if n_t > 3
		tempfile disp_treat_l
		save `disp_treat_l'
	restore

	preserve
		keep if treat == 0 & !mi(std_score_bl)
		collapse (sd) sd_within_c = std_score_bl ///
		         (count) n_c = std_score_bl, ///
		         by(academycode grade)
		keep if n_c > 3
		tempfile disp_ctrl_l
		save `disp_ctrl_l'
	restore

	use `disp_treat_l', clear
	gen group = "Treatment (within ability group)"
	rename sd_within_t sd
	tempfile combo_l
	save `combo_l'
	use `disp_ctrl_l', clear
	gen group = "Control (within grade-class)"
	rename sd_within_c sd
	append using `combo_l'

	twoway  (kdensity sd if group=="Control (within grade-class)", ///
	         lcolor(navy) lwidth(medium) lpattern(solid)) ///
	        (kdensity sd if group=="Treatment (within ability group)", ///
	         lcolor(cranberry) lwidth(medium) lpattern(dash)), ///
			legend(label(1 "Control (within grade-class)") ///
			       label(2 "Treatment (within ability group)")) ///
			xtitle("Within-group SD of baseline score") ytitle("Density") ///
			title("Liberia: Did Grouping Reduce Within-Group Dispersion?")
	graph export "`gdir'/L_dispersion_reduce.pdf", replace
}



********************************************************************************
***                                                                          ***
***                      CROSS-COUNTRY COMPARISON                            ***
***                                                                          ***
********************************************************************************

di ""
di "===== CROSS-COUNTRY COMPARISON ====="

* R-sq from BL->EL regression (signal comparison)
di ""
di "Signal quality (R-sq from BL->EL in control group):"
di "  Kenya:   R-sq = `r2_k_g1' (G1)  `r2_k_g2' (G2)"

* Reload Liberia to get grade-level R-sq
use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear
keep if finsamp == 1

forval g = 1/4 {
	cap reg std_score_el std_score_bl if treat == 0 & grade == `g'
	if !_rc di "  Liberia G`g': R-sq = " %5.3f `e(r2)'
}


di ""
di "===== DONE: desc_new.do ====="
di "Outputs saved to: `gdir'"
