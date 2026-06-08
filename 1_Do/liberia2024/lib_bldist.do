
/*==========================================================================

Title: lib_bldist.do 
Author: Mridul Joshi
Date: Sun Dec  8 16:50:56 2024

===========================================================================*/


*use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

*keep if finsamp== 1 

lab var std_score_bl "Baseline score (standardised)"

lab def g4 0 "Grade 3" 1 "Grade 4"
lab def g2 0 "Grade 1" 1 "Grade 2"

lab val g4 g4 
lab val g2 g2

graph box score_bl if exp1 , over(g4) name(l34)

graph box score_bl if exp2, over(g2) name(l12)


graph combine l34 l12, ycommon title("") 

graph export "${outdir}/bxplt_lib.pdf", replace 


forval g = 1/4 {

	egen bl_q_`g' = xtile(std_pred_eb) if grade == `g', nq(10) //by(academycode grade stream)

}

egen bl_q = rowtotal(bl_q_*)


*gen trXg2 = 1 if treat == 1 & g2 ==1

*replace trXg2 = 2 if treat == 1 & g2 ==0
*replace trXg2 = 3 if treat == 0 & g2 ==1
*replace trXg2 = 4 if treat == 0 & g2 ==0


*binscatter score_el bl_q if exp1 & treat==0, xq(bl_q) by(g4) xtitle("Baseline score quantiles") ytitle("Endline score") legend(order(1 "Grade 3" 2 "Grade 4"))



binscatter score_el bl_q if exp2 & treat==1, xq(bl_q) by(g2) xtitle("Ability grouping progression") ytitle("Endline score") legend(order(1 "Grade 1" 2 "Grade 2")) name(bs12t) line(lfit) absorb(strata)

binscatter score_el bl_q if exp2 & treat==0, xq(bl_q) by(g2) xtitle("Natural grade progression") ytitle("Endline score") legend(order(1 "Grade 1" 2 "Grade 2")) name(bs12c) line (lfit) absorb(strata)

graph combine bs12c bs12t

graph export "${outdir}/q_12_lib.pdf", replace as(pdf)



binscatter score_el bl_q if exp1 & treat==1, xq(bl_q) by(g4) xtitle("Ability grouping progression") ytitle("Endline score") legend(order(1 "Grade 3" 2 "Grade 4")) name(bs34t) line(lfit) absorb(strata)

binscatter score_el bl_q if exp1 & treat==0, xq(bl_q) by(g4) xtitle("Natural grade progression") ytitle("Endline score") legend(order(1 "Grade 3" 2 "Grade 4")) name(bs34c) line (lfit) absorb(strata)

graph combine bs34c bs34t

graph export "${outdir}/q_34_lib.pdf", replace as(pdf)



tw kdensity predicted_ability if grade == 1, color(red%50) || (kdensity predicted_ability if grade == 2, color(blue%50)),  ytitle("Predicted ability") legend(order(1 "Grade 1" 2 "Grade 2"))

graph export "${outdir}/ability_dist12_lib.pdf", replace as(pdf)


tw kdensity predicted_ability if grade == 3, color(red%50) || (kdensity predicted_ability if grade == 4, color(blue%50)),  ytitle("Predicted ability") legend(order(1 "Grade 3" 2 "Grade 4"))

graph export "${outdir}/ability_dist34_lib.pdf", replace as(pdf)



binscatter std_pred_eb std_score_bl, xtitle("Std. baseline score") ytitle("Std. predicted ability (empirical bayes)") name(bineb1)



binscatter std_pred_eb std_score_ml , xtitle("Std. midline score (control group)") ytitle("Std. predicted ability (empirical bayes)") name(bineb2)


graph combine bineb1 bineb2

graph export "${outdir}/corr_bl_eb.pdf", replace as(pdf)


forval g = 1/2 {

	egen bl_q_exp`g' = xtile(std_score_bl) if exp`g' == 1, nq(10) //by(academycode grade stream)

}


binscatter score_el bl_q_exp1 if exp1 & treat==1, xq(bl_q) by(g4) xtitle("Predicted ability deciles") ytitle("Endline score") legend(order(1 "Grade 3" 2 "Grade 4"))

binscatter score_el bl_q_exp2 if exp2 & treat==1, xq(bl_q) by(g2) xtitle("Predicted") ytitle("Endline score") legend(order(1 "Grade 1" 2 "Grade 2")) 




graph export "${outdir}/L_score_q_34_graph.pdf", replace as(pdf)


end 



forval g = 1/4 {

	summ score_bl if treat==0 & grade == `g'
	g baseline_mean_control_`g' = r(mean)
	g baseline_var_control_`g' = r(Var)

	summ score_ml if treat==0 & grade == `g'
	g midline_mean_control_`g' = r(mean)
	g midline_var_control_`g' = r(Var)

}

egen baseline_mean_control = rowtotal(baseline_mean_control_*)
egen baseline_var_control = rowtotal(baseline_var_control_*)

egen midline_mean_control = rowtotal(midline_mean_control_*)
egen midline_var_control = rowtotal(midline_var_control_*)


// Calculate weights
gen w_baseline = 1 / baseline_var_control / (1 / baseline_var_control + 1 / midline_var_control)
gen w_midline = 1 / midline_var_control / (1 / baseline_var_control + 1 / midline_var_control)

// Predicted ability for all data
gen predicted_ability = w_baseline * score_bl + w_midline * score_ml + ///
                        (1 - w_baseline - w_midline) * (baseline_mean_control + midline_mean_control) / 2





// Attach group statistics to individuals
gen group_baseline_mean = .
gen group_baseline_var = .
gen group_midline_mean = .
gen group_midline_var = .

forval g = 1/4 {
    replace group_baseline_mean = baseline_mean_control_`g' if grade == `g'
    replace group_baseline_var = baseline_var_control_`g' if grade == `g'
    replace group_midline_mean = midline_mean_control_`g' if grade == `g'
    replace group_midline_var = midline_var_control_`g' if grade == `g'
}


// Compute shrinkage weights for baseline and control midline
gen w_baseline3 = group_baseline_var / (group_baseline_var + group_midline_var)
gen w_midline3 = group_midline_var / (group_baseline_var + group_midline_var)

// Predicted ability using baseline and control group midline statistics
gen predicted_ability3 = (w_baseline3 * score_bl) + (w_midline3 * group_midline_mean) + ///
                        ((1 - w_baseline3 - w_midline3) * (group_baseline_mean + group_midline_mean) / 2)




// Assume individual variance is constant within the group
gen individual_var = baseline_var_control  // Placeholder; update if you have individual-level variances

// Compute the shrinkage weight
gen weight2 = group_var / (group_var + individual_var)



// Apply the Empirical Bayes formula
gen predicted_ability2 = (weight2 * score_bl) + ((1 - weight2) * group_mean)







