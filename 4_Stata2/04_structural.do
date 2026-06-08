/*
04_structural.do — Structural estimation with LaTeX tables
==========================================================
Produces: signal quality alt table, accounting decomposition table,
          sensitivity grid table, four-margin summary table.
*/

di _n "{hline 70}"
di "04_structural.do — Structural estimation"
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

cap program drop kenya_exact_bh_toy_test
program define kenya_exact_bh_toy_test, rclass
	* One hand-checkable school composition duplicated into treated/control copies.
	preserve
	clear
	set obs 8
	gen academycode = .
	gen treat = .
	gen grade = .
	gen studyid = .
	gen score_bl = .
	gen std_eb = .
	gen P_t = .

	replace academycode = 1 in 1/4
	replace academycode = 2 in 5/8
	replace treat = 1 in 1/4
	replace treat = 0 in 5/8
	replace grade = 1 in 1/2
	replace grade = 2 in 3/4
	replace grade = 1 in 5/6
	replace grade = 2 in 7/8
	replace studyid = 101 in 1
	replace studyid = 102 in 2
	replace studyid = 103 in 3
	replace studyid = 104 in 4
	replace studyid = 201 in 5
	replace studyid = 202 in 6
	replace studyid = 203 in 7
	replace studyid = 204 in 8
	replace score_bl = 30 in 1
	replace score_bl = 50 in 2
	replace score_bl = 20 in 3
	replace score_bl = 45 in 4
	replace score_bl = 30 in 5
	replace score_bl = 50 in 6
	replace score_bl = 20 in 7
	replace score_bl = 45 in 8
	replace std_eb = -1 in 1
	replace std_eb = 0 in 2
	replace std_eb = 1 in 3
	replace std_eb = 2 in 4
	replace std_eb = -1 in 5
	replace std_eb = 0 in 6
	replace std_eb = 1 in 7
	replace std_eb = 2 in 8
	replace P_t = 0.25 in 1/8

	gen upper_group = .
	replace upper_group = (score_bl > 40) if grade == 1
	replace upper_group = (score_bl > 35) if grade == 2
	gen std_grp = cond(upper_group == 1, 2, 1)
	gen P_c = 1 - P_t

	bys academycode std_grp: egen _tot_t = total(std_eb)
	bys academycode std_grp: egen _cnt_t = count(std_eb)
	gen peer_std_eb_treat = (_tot_t - std_eb) / (_cnt_t - 1) if _cnt_t > 1
	drop _tot_t _cnt_t

	bys academycode grade: egen _tot_c = total(std_eb)
	bys academycode grade: egen _cnt_c = count(std_eb)
	gen peer_std_eb_ctrl = (_tot_c - std_eb) / (_cnt_c - 1) if _cnt_c > 1
	drop _tot_c _cnt_c

	gen peer_eb = cond(treat == 1, peer_std_eb_treat, peer_std_eb_ctrl)
	gen exp_peer_eb = P_t * peer_std_eb_treat + P_c * peer_std_eb_ctrl
	gen peer_exact_tilde = peer_eb - exp_peer_eb

	gen expected_p1 = .
	gen expected_p0 = .
	gen expected_mu = .
	gen expected_tilde = .

	replace expected_p1 = 1  if mod(studyid, 100) == 1
	replace expected_p1 = 2  if mod(studyid, 100) == 2
	replace expected_p1 = -1 if mod(studyid, 100) == 3
	replace expected_p1 = 0  if mod(studyid, 100) == 4

	replace expected_p0 = 0  if mod(studyid, 100) == 1
	replace expected_p0 = -1 if mod(studyid, 100) == 2
	replace expected_p0 = 2  if mod(studyid, 100) == 3
	replace expected_p0 = 1  if mod(studyid, 100) == 4

	replace expected_mu = 0.25 if mod(studyid, 100) == 1
	replace expected_mu = -0.25 if mod(studyid, 100) == 2
	replace expected_mu = 1.25 if mod(studyid, 100) == 3
	replace expected_mu = 0.75 if mod(studyid, 100) == 4

	replace expected_tilde = 0.75  if studyid == 101
	replace expected_tilde = 2.25  if studyid == 102
	replace expected_tilde = -2.25 if studyid == 103
	replace expected_tilde = -0.75 if studyid == 104
	replace expected_tilde = -0.25 if studyid == 201
	replace expected_tilde = -0.75 if studyid == 202
	replace expected_tilde = 0.75  if studyid == 203
	replace expected_tilde = 0.25  if studyid == 204

	assert abs(peer_std_eb_treat - expected_p1) < 1e-10
	assert abs(peer_std_eb_ctrl - expected_p0) < 1e-10
	assert abs(exp_peer_eb - expected_mu) < 1e-10
	assert abs(peer_exact_tilde - expected_tilde) < 1e-10

	return scalar passed = 1
	restore
end

local ds = char(36)

* Standalone-safe defaults
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
if "$out" == "" global out "$root/4_Stata2/output"
if "$ke_cutoff_g1" == "" global ke_cutoff_g1 = 40
if "$ke_cutoff_g2" == "" global ke_cutoff_g2 = 35
if "$lib_cutoff_g12" == "" global lib_cutoff_g12 = 23
if "$lib_cutoff_g34" == "" global lib_cutoff_g34 = 14
cap mkdir "$out"

* ═══════════════════════════════════════════════════════════════════════════
* A. ALTERNATIVE SIGNAL QUALITY TABLE
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== A. Alternative Signal Quality ==="

tempname fh
file open `fh' using "$out/tab_signal_quality_alt.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Alternative Signal-Quality Diagnostics}" _n
file write `fh' "\label{tab:signal_quality_alt}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{2}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3}" _n
file write `fh' " & Kenya & Liberia \\" _n
file write `fh' "\midrule" _n

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & treat == 0 & !mi(score_bl) & !mi(score_el)

	* R² from grade FE only
	qui reg score_el i.grade
	local r2_grade_`study' : di %6.3f e(r2)

	* R² from grade FE + baseline
	qui reg score_el score_bl i.grade
	local r2_both_`study' : di %6.3f e(r2)

	* Incremental R²
	local incr_`study' : di %6.3f e(r2) - `r2_grade_`study''

	* Within-grade rank persistence
	local rank_sum = 0
	local rank_n = 0
	levelsof grade, local(grades)
	foreach g of local grades {
		qui count if grade == `g'
		if r(N) > 10 {
			preserve
				keep if grade == `g'
				egen rank_bl = rank(score_bl)
				egen rank_el = rank(score_el)
				qui corr rank_bl rank_el
				local rank_sum = `rank_sum' + r(rho) * r(N)
				local rank_n = `rank_n' + r(N)
			restore
		}
	}
	local rank_`study' : di %6.3f `rank_sum' / `rank_n'
}

file write `fh' "R-squared grade FE only & `r2_grade_kenya' & `r2_grade_liberia' \\" _n
file write `fh' "R-squared grade FE + baseline & `r2_both_kenya' & `r2_both_liberia' \\" _n
file write `fh' "Incremental R-squared & `incr_kenya' & `incr_liberia' \\" _n
file write `fh' "Within-grade rank persistence & `rank_kenya' & `rank_liberia' \\" _n

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item Notes: All computed in control group. Incremental R-squared = "
file write `fh' "additional variance explained by adding baseline score to a grade FE only "
file write `fh' "model. Rank persistence is the within grade Spearman correlation between "
file write `fh' "baseline and endline score ranks, weighted by grade size." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_signal_quality_alt.tex"


* ═══════════════════════════════════════════════════════════════════════════
* B. KENYA: PEER EFFECTS AND DESCRIPTIVE DECOMPOSITION
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== B. Kenya Peer Effects and Decomposition ==="

use "$out/analysis_kenya.dta", clear
keep if finsamp & has_el
keep if !mi(std_score_el) & !mi(std_eb) & !mi(peer_eb) & !mi(score_bl) & !mi(grade) & !mi(strata)

* Fix track targets (population-level, not school-specific)
bys std_grp grade: egen track_target_t = mean(cond(treat == 1, std_eb, .))
bys grade:         egen track_target_c = mean(cond(treat == 0, std_eb, .))
gen track_target = cond(treat == 1, track_target_t, track_target_c)
gen abs_misfit = abs(std_eb - track_target)
drop track_target_t track_target_c

* Within-class baseline SD
capture confirm variable std_score_bl
if _rc != 0 {
	di as error "Variable std_score_bl not found in Kenya analysis dataset."
	exit 111
}
bys academycode std_grp: egen _sd_bl_t = sd(std_score_bl) if treat == 1
bys academycode grade:   egen _sd_bl_c = sd(std_score_bl) if treat == 0
gen within_sd = cond(treat == 1, _sd_bl_t, _sd_bl_c)
drop _sd_bl_t _sd_bl_c

* BH cells: decile × treatment × grade
cap confirm variable bl_decile
if _rc != 0 {
	gen bl_decile = .
	forval g = 1/2 {
		qui xtile _dec = score_bl if grade == `g', nq(10)
		replace bl_decile = _dec if grade == `g'
		drop _dec
	}
}
egen dtg_cell = group(bl_decile treat grade)

* Part 1: BH peer estimate (preferred)
qui reg std_score_el peer_eb i.dtg_cell i.strata, vce(cluster academycode)
local zeta_hat = _b[peer_eb]
local zeta_se  = _se[peer_eb]
local zeta_pv  = 2 * ttail(e(df_r), abs(`zeta_hat'/`zeta_se'))
get_stars `zeta_pv'
local zeta_star "`r(stars)'"
local zeta_n   = e(N)
local zeta_f   : di %7.3f `zeta_hat'
local zeta_se_f : di %7.3f `zeta_se'
di "  BH peer (decile × T × grade): " `zeta_f' " (" `zeta_se_f' ")"

* BH peer estimate (ventile robustness)
gen bl_ventile = .
forval g = 1/2 {
	qui xtile _vent = score_bl if grade == `g', nq(20)
	replace bl_ventile = _vent if grade == `g'
	drop _vent
}
egen vtg_cell = group(bl_ventile treat grade)
qui reg std_score_el peer_eb i.vtg_cell i.strata, vce(cluster academycode)
local zeta_v     = _b[peer_eb]
local zeta_v_se  = _se[peer_eb]
local zeta_v_pv  = 2 * ttail(e(df_r), abs(`zeta_v'/`zeta_v_se'))
get_stars `zeta_v_pv'
local zeta_v_star "`r(stars)'"
local zeta_v_f    : di %7.3f `zeta_v'
local zeta_v_se_f : di %7.3f `zeta_v_se'
di "  BH peer (ventile × T × grade): " `zeta_v_f' " (" `zeta_v_se_f' ")"

* Part 1b: Density-based peer vs. rank decomposition
di _n "  Density-based peer vs. rank decomposition:"

gen f_density = .
tempfile g1_dens g2_dens
forval g = 1/2 {
    preserve
    keep if grade == `g'
    local Ng = _N

    * Silverman rule-of-thumb bandwidth
    qui summ score_bl
    local h = 1.06 * r(sd) * `Ng'^(-0.2)

    * Gaussian kernel density at each observation's own score (fallback loop)
    gen double __f_temp = .
    forval i = 1/`Ng' {
        qui summ score_bl in `i', meanonly
        local xi = r(mean)
        qui gen double __k = normalden((score_bl - `xi') / `h')
        qui summ __k, meanonly
        replace __f_temp = r(mean) / `h' in `i'
        drop __k
    }

    keep studyid __f_temp
    if `g' == 1 {
        save "`g1_dens'", replace
    }
    if `g' == 2 {
        save "`g2_dens'", replace
    }
    restore

    local denfile "`g1_dens'"
    if `g' == 2 local denfile "`g2_dens'"
    merge 1:1 studyid using "`denfile'", nogen keep(1 3) keepusing(__f_temp)
    replace f_density = __f_temp if grade == `g' & !mi(__f_temp)
    cap drop __f_temp
}

* Standardize density within grade (comparable across grades)
gen f_density_std = .
forval g = 1/2 {
    qui summ f_density if grade == `g'
    replace f_density_std = (f_density - r(mean)) / r(sd) if grade == `g'
}

* Create terciles of density (pooled after within grade standardization)
xtile f_tercile = f_density_std, nq(3)
label define f_terc 1 "Low density (tails)" 2 "Medium density" 3 "High density (middle)", replace
label values f_tercile f_terc

di "    Tercile definitions:"
di "      1 = Low density (tails)"
di "      2 = Medium density"
di "      3 = High density (middle)"

* BH regression by density tercile
di "  Peer effect by score-density tercile:"
forval t = 1/3 {
    qui reg std_score_el peer_eb i.dtg_cell i.strata if f_tercile == `t', vce(cluster academycode)
    local zeta_t`t' = _b[peer_eb]
    local zeta_t`t'_se = _se[peer_eb]
    local zeta_t`t'_pv = 2 * ttail(e(df_r), abs(_b[peer_eb]/_se[peer_eb]))
    get_stars `zeta_t`t'_pv'
    local zeta_t`t'_star "`r(stars)'"
    local zeta_t`t'_n = e(N)
    local zeta_t`t'_f : di %7.3f `zeta_t`t''
    local zeta_t`t'_se_f : di %7.3f `zeta_t`t'_se'
    di "    Tercile `t': zeta = `zeta_t`t'_f' (`zeta_t`t'_se_f')"
}

* Pooled interaction specification
gen peer_x_density = peer_eb * f_density_std
qui reg std_score_el peer_eb peer_x_density f_density_std i.dtg_cell i.strata, vce(cluster academycode)
local zeta_main = _b[peer_eb]
local zeta_int  = _b[peer_x_density]
local zeta_int_se = _se[peer_x_density]
local zeta_int_pv = 2 * ttail(e(df_r), abs(`zeta_int'/`zeta_int_se'))
get_stars `zeta_int_pv'
local zeta_int_star "`r(stars)'"
local zeta_main_f : di %7.3f `zeta_main'
local zeta_int_f  : di %7.3f `zeta_int'
local zeta_int_se_f : di %7.3f `zeta_int_se'
di "  Interaction: zeta x density = `zeta_int_f' (`zeta_int_se_f') p = " %5.3f `zeta_int_pv'

* Mean density by tercile
forval t = 1/3 {
    qui summ f_density if f_tercile == `t'
    local mean_dens_t`t' : di %7.4f r(mean)
    di "    Mean density, tercile `t': `mean_dens_t`t''"
}

di "  Interpretation note: if rank effects matter (eta != 0), zeta should be"
di "    more negative in high-density regions where within class rank shifts"
di "    are more responsive to peer composition changes."

* Write LaTeX table
tempname fh
file open `fh' using "$out/tab_density_decomp.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Approximate Peer/Rank Diagnostic by Score Density}" _n
file write `fh' "\label{tab:density_decomp}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & \multicolumn{3}{c}{Score-density tercile} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
file write `fh' " & (1) Low & (2) Medium & (3) High \\" _n
file write `fh' " & (tails) & & (middle) \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{4}{l}{\textit{Panel A: Approximate peer/rank estimate by density tercile}} \\" _n
file write `fh' "Peer mean EB ability (`ds'\hat{\zeta}`ds') & `zeta_t1_f'`zeta_t1_star' & `zeta_t2_f'`zeta_t2_star' & `zeta_t3_f'`zeta_t3_star' \\" _n
file write `fh' " & (`zeta_t1_se_f') & (`zeta_t2_se_f') & (`zeta_t3_se_f') \\" _n
file write `fh' "N & `zeta_t1_n' & `zeta_t2_n' & `zeta_t3_n' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\midrule" _n
file write `fh' " & \multicolumn{3}{c}{Pooled interaction} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4}" _n
file write `fh' "\multicolumn{4}{l}{\textit{Panel B: Interaction specification}} \\" _n
file write `fh' "Peer mean EB ability (`ds'\hat{\zeta}`ds') & \multicolumn{3}{c}{`zeta_main_f'} \\" _n
file write `fh' "Peer EB `ds'\times`ds' density interaction & \multicolumn{3}{c}{`zeta_int_f'`zeta_int_star'} \\" _n
file write `fh' " & \multicolumn{3}{c}{(`zeta_int_se_f')} \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\scriptsize" _n
file write `fh' "\setlength{\emergencystretch}{2em}" _n
file write `fh' "\item \textit{Notes:} Panel~A reports the approximate Borusyak--Hull control function peer/rank coefficient "
file write `fh' "(`ds'\hat{\zeta}`ds') separately for terciles of the baseline score density "
file write `fh' "evaluated at each student's own score. Students in the tails of the distribution "
file write `fh' "(low density) have few classmates at similar ability levels, so their within class "
file write `fh' "rank is insensitive to changes in peer composition. Students in the middle "
file write `fh' "(high density) have many nearby classmates, so rank shifts more with peer changes. "
file write `fh' "In the stylized rank model, `ds'\hat{\zeta} \approx \pi + \eta \cdot (-f(\theta_i))`ds', "
file write `fh' "where `ds'\pi`ds' is the mean peer effect, `ds'\eta`ds' is the rank effect, "
file write `fh' "and `ds'\,f(\theta_i)`ds' is the score density. If rank effects matter in this "
file write `fh' "reduced-form composite (`ds'\eta \neq 0`ds'), `ds'\hat{\zeta}`ds' would tend to be "
file write `fh' "more negative in the high-density tercile, where rank is more responsive to peer shifts. "
file write `fh' "Panel~B reports a pooled interaction of peer mean with standardized density; "
file write `fh' "the interaction is a diagnostic for whether the peer/rank coefficient changes with local score density. "
file write `fh' "All specifications include baseline-decile `ds'\times`ds' treatment "
file write `fh' "`ds'\times`ds' grade FE and strata FE, so they should be read as approximate "
file write `fh' "cell-control specifications rather than exact design-based recentering checks. "
file write `fh' "Density is estimated using a Gaussian kernel with Silverman bandwidth, "
file write `fh' "computed within grade, and standardized to mean zero and unit variance within grade. "
file write `fh' "Standard errors are clustered at the school level. "
file write `fh' "***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_density_decomp.tex"

* Part 2: Descriptive treatment-induced shifts
qui summ abs_misfit if treat == 0
local mis_c = r(mean)
qui summ abs_misfit if treat == 1
local mis_t = r(mean)
local d_mis = `mis_c' - `mis_t'
local d_mis_f : di %7.3f `d_mis'
local mis_c_f : di %7.3f `mis_c'
local mis_t_f : di %7.3f `mis_t'

qui summ peer_eb if treat == 0
local peer_c = r(mean)
qui summ peer_eb if treat == 1
local peer_t = r(mean)
local d_peer = `peer_t' - `peer_c'
local d_peer_f : di %7.3f `d_peer'

qui summ csize if treat == 0
local cs_c = r(mean)
qui summ csize if treat == 1
local cs_t = r(mean)
local d_cs = `cs_t' - `cs_c'
local d_cs_f : di %7.1f `d_cs'

qui summ within_sd if treat == 0
local sd_c = r(mean)
qui summ within_sd if treat == 1
local sd_t = r(mean)
local d_sd = `sd_c' - `sd_t'
local d_sd_f : di %7.3f `d_sd'

* Part 3: Peer contribution and remainder
qui reg std_score_el treat std_eb i.strata, vce(cluster academycode)
local itt     = _b[treat]
local itt_se  = _se[treat]
local itt_f   : di %7.3f `itt'
local itt_se_f : di %7.3f `itt_se'

local peer_contrib = `zeta_hat' * `d_peer'
local remainder    = `itt' - `peer_contrib'
local pc_f : di %7.3f `peer_contrib'
local rm_f : di %7.3f `remainder'

di _n "  Decomposition:"
di "    ITT:              " `itt_f'
di "    Peer contribution:" `pc_f' "  (zeta_hat × delta_peer)"
di "    Remainder:        " `rm_f'
di "    Sum check:        " %7.4f (`peer_contrib' + `remainder')

* Bootstrap SEs for decomposition components
cap program drop peer_decomp_boot
program define peer_decomp_boot, rclass
	cap drop _dtg_bs
	egen _dtg_bs = group(bl_decile treat grade)
	qui reg std_score_el peer_eb i._dtg_bs i.strata
	local z = _b[peer_eb]
	drop _dtg_bs

	qui summ peer_eb if treat == 0
	local pc = r(mean)
	qui summ peer_eb if treat == 1
	local pt = r(mean)

	qui reg std_score_el treat std_eb i.strata
	local itt = _b[treat]

	local contrib = `z' * (`pt' - `pc')
	return scalar zeta = `z'
	return scalar peer_contrib = `contrib'
	return scalar remainder = `itt' - `contrib'
	return scalar itt = `itt'
end

capture noisily bootstrap zeta=r(zeta) peer_contrib=r(peer_contrib) remainder=r(remainder) itt=r(itt), ///
	reps(1000) cluster(academycode) idcluster(_bsid) group(academycode) seed(20240101): ///
	peer_decomp_boot
if _rc == 0 {
	local bs_zeta_se : di %7.3f _se[zeta]
	local bs_pc_se   : di %7.3f _se[peer_contrib]
	local bs_rm_se   : di %7.3f _se[remainder]
	local bs_itt_se  : di %7.3f _se[itt]
}
else {
	di "  Bootstrap via prefix failed; using manual loop..."
	local B = 1000
	tempname bmat
	matrix `bmat' = J(`B', 4, .)
	preserve
	forval b = 1/`B' {
		restore, preserve
		bsample, cluster(academycode)
		cap drop _dtg_bs
		egen _dtg_bs = group(bl_decile treat grade)
		qui reg std_score_el peer_eb i._dtg_bs i.strata
		local z = _b[peer_eb]
		drop _dtg_bs
		qui summ peer_eb if treat == 0
		local pc = r(mean)
		qui summ peer_eb if treat == 1
		local pt = r(mean)
		qui reg std_score_el treat std_eb i.strata
		local itt_b = _b[treat]
		local contrib_b = `z' * (`pt' - `pc')
		matrix `bmat'[`b', 1] = `z'
		matrix `bmat'[`b', 2] = `contrib_b'
		matrix `bmat'[`b', 3] = `itt_b' - `contrib_b'
		matrix `bmat'[`b', 4] = `itt_b'
	}
	restore
	svmat `bmat', names(_bs_)
	foreach j in 1 2 3 4 {
		qui summ _bs_`j'
		local _bse_`j' = r(sd)
	}
	local bs_zeta_se : di %7.3f `_bse_1'
	local bs_pc_se   : di %7.3f `_bse_2'
	local bs_rm_se   : di %7.3f `_bse_3'
	local bs_itt_se  : di %7.3f `_bse_4'
	drop _bs_*
}

* Kenya table
tempname fh
file open `fh' using "$out/tab_suffstat_kenya.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
	file write `fh' "\caption{Peer/Rank Diagnostics and Accounting: Kenya}" _n
file write `fh' "\label{tab:suffstat}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{2}{c}{Kenya specifications} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3}" _n
file write `fh' " & Decile FE & Ventile FE \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{3}{l}{\textit{Panel A: Peer/rank composite (`ds'\hat{\zeta}`ds')}} \\" _n
file write `fh' "Effect of 1 SD increase in peer mean & `zeta_f'`zeta_star' & `zeta_v_f'`zeta_v_star' \\" _n
file write `fh' " & (`zeta_se_f') & (`zeta_v_se_f') \\" _n
file write `fh' "Observations & `zeta_n' & `zeta_n' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{3}{l}{\textit{Panel B: Treatment-induced classroom shifts}} \\" _n
file write `fh' "`ds'\Delta`ds' mismatch, `ds'\lvert\hat{\theta} - \hat{I}\rvert`ds' (C `ds'-`ds' T) & \multicolumn{2}{c}{`d_mis_f'} \\" _n
file write `fh' "`ds'\Delta`ds' peer composition (T `ds'-`ds' C) & \multicolumn{2}{c}{`d_peer_f'} \\" _n
file write `fh' "`ds'\Delta`ds' class size (T `ds'-`ds' C) & \multicolumn{2}{c}{`d_cs_f'} \\" _n
file write `fh' "`ds'\Delta`ds' within class baseline SD (C `ds'-`ds' T) & \multicolumn{2}{c}{`d_sd_f'} \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{3}{l}{\textit{Panel C: Accounting decomposition}} \\" _n
file write `fh' "Overall ITT & \multicolumn{2}{c}{`itt_f' (`bs_itt_se')} \\" _n
file write `fh' "Peer/rank contribution (`ds'\hat{\zeta} \times \Delta\bar{\theta}`ds') & \multicolumn{2}{c}{`pc_f' (`bs_pc_se')} \\" _n
file write `fh' "Remainder & \multicolumn{2}{c}{`rm_f' (`bs_rm_se')} \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Panel A reports the approximate Borusyak--Hull control function peer/rank coefficient from "
file write `fh' "regressing standardized endline scores on peer mean ability, excluding the focal student, "
file write `fh' "conditioning on baseline score bin `ds'\times`ds' treatment `ds'\times`ds' grade "
file write `fh' "fixed effects and strata FE\@. Standard errors are clustered at the school level. "
file write `fh' "Panel B reports mean treatment control differences in classroom characteristics. "
file write `fh' "Mismatch is measured as `ds'|\hat{\theta}^{EB}_i - \hat{I}_k|`ds' where "
file write `fh' "`ds'\hat{I}_k`ds' is the population-level track mean. "
	file write `fh' "Panel C reports the implied peer/rank contribution under the approximate specification "
	file write `fh' "(`ds'\hat{\zeta} \times`ds' observed peer shift) and a remainder that includes "
file write `fh' "assignment gains, productive-time effects, and other non-peer/rank channels. "
file write `fh' "Bootstrap SEs (1,000 replications, clustered at the school level) in parentheses in Panel C." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_suffstat_kenya.tex"

* Part 3b: Exact BH recentering table, diagnostics, and note
di _n "  Exact BH Kenya table and diagnostics:"

capture confirm variable peer_std_eb_treat
if _rc != 0 {
	di as error "Variable peer_std_eb_treat not found in Kenya analysis dataset."
	exit 111
}
capture confirm variable peer_std_eb_ctrl
if _rc != 0 {
	di as error "Variable peer_std_eb_ctrl not found in Kenya analysis dataset."
	exit 111
}
capture confirm variable exp_peer_eb
if _rc != 0 {
	di as error "Variable exp_peer_eb not found in Kenya analysis dataset."
	exit 111
}
capture confirm variable P_t
if _rc != 0 {
	di as error "Variable P_t not found in Kenya analysis dataset."
	exit 111
}

gen exact_mu_peer_eb = exp_peer_eb
gen peer_eb_exact_tilde = peer_eb - exact_mu_peer_eb
gen exact_mu_peer_eb_obsbl = exp_peer_eb_obsbl
gen peer_eb_exact_tilde_obsbl = peer_eb_obsbl - exact_mu_peer_eb_obsbl
gen eb2 = std_eb^2
gen eb3 = std_eb^3

egen approx_mu_decile = mean(peer_eb), by(bl_decile treat grade)

local flex_own_ctrls ///
	"c.std_eb##i.treat##i.grade c.eb2##i.treat##i.grade c.eb3##i.treat##i.grade"
local simple_own_ctrls ///
	"c.std_eb##i.treat##i.grade"

* Exact control function specification with no own-score controls.
qui reg std_score_el peer_eb exact_mu_peer_eb i.strata, vce(cluster academycode)
local exact_none_b   = _b[peer_eb]
local exact_none_se  = _se[peer_eb]
local exact_none_mu_b  = _b[exact_mu_peer_eb]
local exact_none_mu_se = _se[exact_mu_peer_eb]
local exact_none_n   = e(N)
local exact_none_b_f   : di %7.3f `exact_none_b'
local exact_none_se_f  : di %7.3f `exact_none_se'
local exact_none_mu_b_f   : di %7.3f `exact_none_mu_b'
local exact_none_mu_se_f  : di %7.3f `exact_none_mu_se'

* Exact control function specification with flexible own-score controls.
qui reg std_score_el peer_eb exact_mu_peer_eb `flex_own_ctrls' i.strata, vce(cluster academycode)
local exact_cf_b   = _b[peer_eb]
local exact_cf_se  = _se[peer_eb]
local exact_mu_b   = _b[exact_mu_peer_eb]
local exact_mu_se  = _se[exact_mu_peer_eb]
local exact_cf_pv  = 2 * ttail(e(df_r), abs(`exact_cf_b'/`exact_cf_se'))
local exact_mu_pv  = 2 * ttail(e(df_r), abs(`exact_mu_b'/`exact_mu_se'))
get_stars `exact_cf_pv'
local exact_cf_star "`r(stars)'"
get_stars `exact_mu_pv'
local exact_mu_star "`r(stars)'"
local exact_cf_n   = e(N)
local exact_cf_b_f   : di %7.3f `exact_cf_b'
local exact_cf_se_f  : di %7.3f `exact_cf_se'
local exact_mu_b_f   : di %7.3f `exact_mu_b'
local exact_mu_se_f  : di %7.3f `exact_mu_se'

* Exact recentered specification with the same flexible own-score controls.
qui reg std_score_el peer_eb_exact_tilde `flex_own_ctrls' i.strata, vce(cluster academycode)
local exact_rc_b   = _b[peer_eb_exact_tilde]
local exact_rc_se  = _se[peer_eb_exact_tilde]
local exact_rc_pv  = 2 * ttail(e(df_r), abs(`exact_rc_b'/`exact_rc_se'))
get_stars `exact_rc_pv'
local exact_rc_star "`r(stars)'"
local exact_rc_n   = e(N)
local exact_rc_b_f   : di %7.3f `exact_rc_b'
local exact_rc_se_f  : di %7.3f `exact_rc_se'

* Optional comparability spec: exact control function with simpler own-score controls.
qui reg std_score_el peer_eb exact_mu_peer_eb `simple_own_ctrls' i.strata, vce(cluster academycode)
local exact_cmp_b   = _b[peer_eb]
local exact_cmp_se  = _se[peer_eb]
local exact_cmp_mu_b  = _b[exact_mu_peer_eb]
local exact_cmp_mu_se = _se[exact_mu_peer_eb]
local exact_cmp_pv  = 2 * ttail(e(df_r), abs(`exact_cmp_b'/`exact_cmp_se'))
local exact_cmp_mu_pv = 2 * ttail(e(df_r), abs(`exact_cmp_mu_b'/`exact_cmp_mu_se'))
get_stars `exact_cmp_pv'
local exact_cmp_star "`r(stars)'"
get_stars `exact_cmp_mu_pv'
local exact_cmp_mu_star "`r(stars)'"
local exact_cmp_n   = e(N)
local exact_cmp_b_f   : di %7.3f `exact_cmp_b'
local exact_cmp_se_f  : di %7.3f `exact_cmp_se'
local exact_cmp_mu_b_f   : di %7.3f `exact_cmp_mu_b'
local exact_cmp_mu_se_f  : di %7.3f `exact_cmp_mu_se'

* Sensitivity: exclude missing-baseline students from both state-specific peer objects.
qui reg std_score_el peer_eb_obsbl exact_mu_peer_eb_obsbl `flex_own_ctrls' i.strata, vce(cluster academycode)
local exact_obsbl_cf_b   = _b[peer_eb_obsbl]
local exact_obsbl_cf_se  = _se[peer_eb_obsbl]
local exact_obsbl_mu_b   = _b[exact_mu_peer_eb_obsbl]
local exact_obsbl_mu_se  = _se[exact_mu_peer_eb_obsbl]
local exact_obsbl_cf_n   = e(N)
local exact_obsbl_cf_b_f   : di %7.3f `exact_obsbl_cf_b'
local exact_obsbl_cf_se_f  : di %7.3f `exact_obsbl_cf_se'
local exact_obsbl_mu_b_f   : di %7.3f `exact_obsbl_mu_b'
local exact_obsbl_mu_se_f  : di %7.3f `exact_obsbl_mu_se'

qui reg std_score_el peer_eb_exact_tilde_obsbl `flex_own_ctrls' i.strata, vce(cluster academycode)
local exact_obsbl_rc_b   = _b[peer_eb_exact_tilde_obsbl]
local exact_obsbl_rc_se  = _se[peer_eb_exact_tilde_obsbl]
local exact_obsbl_rc_n   = e(N)
local exact_obsbl_rc_b_f   : di %7.3f `exact_obsbl_rc_b'
local exact_obsbl_rc_se_f  : di %7.3f `exact_obsbl_rc_se'

* Approximate decile FE specification with the same cubic own-score controls.
qui reg std_score_el peer_eb i.dtg_cell `flex_own_ctrls' i.strata, vce(cluster academycode)
local approx_cubic_b   = _b[peer_eb]
local approx_cubic_se  = _se[peer_eb]
local approx_cubic_n   = e(N)
local approx_cubic_b_f   : di %7.3f `approx_cubic_b'
local approx_cubic_se_f  : di %7.3f `approx_cubic_se'

local d_none_to_linear = `exact_cmp_b' - `exact_none_b'
local d_linear_to_cubic = `exact_cf_b' - `exact_cmp_b'
local d_approx_to_exact_cubic = `exact_cf_b' - `approx_cubic_b'
local d_exact_to_obsbl_cubic = `exact_obsbl_cf_b' - `exact_cf_b'
local d_none_to_linear_f : di %7.3f `d_none_to_linear'
local d_linear_to_cubic_f : di %7.3f `d_linear_to_cubic'
local d_approx_to_exact_cubic_f : di %7.3f `d_approx_to_exact_cubic'
local d_exact_to_obsbl_cubic_f : di %7.3f `d_exact_to_obsbl_cubic'

* Mechanical checks.
gen exact_obs_gap = .
replace exact_obs_gap = abs(peer_eb - peer_std_eb_treat) if treat == 1
replace exact_obs_gap = abs(peer_eb - peer_std_eb_ctrl) if treat == 0
qui count if exact_obs_gap > 1e-10 & !mi(exact_obs_gap)
local exact_obs_fail = r(N)
qui summ exact_obs_gap, meanonly
local exact_obs_gap_max : di %9.3g r(max)

egen exact_mu_min = rowmin(peer_std_eb_treat peer_std_eb_ctrl)
egen exact_mu_max = rowmax(peer_std_eb_treat peer_std_eb_ctrl)
qui count if (P_t < 0 | P_t > 1) & !mi(P_t)
local exact_pt_out = r(N)
qui count if (exact_mu_peer_eb < exact_mu_min - 1e-10 | exact_mu_peer_eb > exact_mu_max + 1e-10) ///
	& !mi(exact_mu_peer_eb, exact_mu_min, exact_mu_max)
local exact_mu_fail = r(N)

local cf_rc_gap = abs(`exact_cf_b' - `exact_rc_b')
local cf_rc_gap_f : di %9.3g `cf_rc_gap'

qui corr exact_mu_peer_eb approx_mu_decile
local mu_dec_corr : di %6.3f r(rho)

local d_exact_dec = `exact_cf_b' - `zeta_hat'
local d_exact_ven = `exact_cf_b' - `zeta_v'
local d_exact_dec_f : di %7.3f `d_exact_dec'
local d_exact_ven_f : di %7.3f `d_exact_ven'

* Summary-stat diagnostics for P_obs, mu, and recentered peer regressor.
preserve
	clear
	set obs 3
	gen str18 variable = ""
	gen double mean = .
	gen double sd = .
	gen double p10 = .
	gen double p50 = .
	gen double p90 = .
	gen long N = .

	replace variable = "P_obs" in 1
	replace variable = "mu_exact" in 2
	replace variable = "P_tilde" in 3
restore

foreach vv in peer_eb exact_mu_peer_eb peer_eb_exact_tilde {
	qui summ `vv', detail
	if "`vv'" == "peer_eb" {
		local mean_1 = r(mean)
		local sd_1 = r(sd)
		local p10_1 = r(p10)
		local p50_1 = r(p50)
		local p90_1 = r(p90)
		local N_1 = r(N)
	}
	if "`vv'" == "exact_mu_peer_eb" {
		local mean_2 = r(mean)
		local sd_2 = r(sd)
		local p10_2 = r(p10)
		local p50_2 = r(p50)
		local p90_2 = r(p90)
		local N_2 = r(N)
	}
	if "`vv'" == "peer_eb_exact_tilde" {
		local mean_3 = r(mean)
		local sd_3 = r(sd)
		local p10_3 = r(p10)
		local p50_3 = r(p50)
		local p90_3 = r(p90)
		local N_3 = r(N)
	}
}

local mean_1_f : di %7.3f `mean_1'
local sd_1_f   : di %7.3f `sd_1'
local p50_1_f  : di %7.3f `p50_1'
local mean_2_f : di %7.3f `mean_2'
local sd_2_f   : di %7.3f `sd_2'
local p50_2_f  : di %7.3f `p50_2'
local mean_3_f : di %7.3f `mean_3'
local sd_3_f   : di %7.3f `sd_3'
local p50_3_f  : di %7.3f `p50_3'

preserve
	clear
	set obs 3
	gen str18 variable = ""
	gen double mean = .
	gen double sd = .
	gen double p10 = .
	gen double p50 = .
	gen double p90 = .
	gen long N = .

	replace variable = "P_obs" in 1
	replace mean = `mean_1' in 1
	replace sd = `sd_1' in 1
	replace p10 = `p10_1' in 1
	replace p50 = `p50_1' in 1
	replace p90 = `p90_1' in 1
	replace N = `N_1' in 1

	replace variable = "mu_exact" in 2
	replace mean = `mean_2' in 2
	replace sd = `sd_2' in 2
	replace p10 = `p10_2' in 2
	replace p50 = `p50_2' in 2
	replace p90 = `p90_2' in 2
	replace N = `N_2' in 2

	replace variable = "P_tilde" in 3
	replace mean = `mean_3' in 3
	replace sd = `sd_3' in 3
	replace p10 = `p10_3' in 3
	replace p50 = `p50_3' in 3
	replace p90 = `p90_3' in 3
	replace N = `N_3' in 3

	save "$out/kenya_exact_bh_summary_stats.dta", replace
	export delimited using "$out/kenya_exact_bh_summary_stats.csv", replace
restore

preserve
	clear
	set obs 5
	gen str28 specification = ""
	gen double coef_peer = .
	gen double se_peer = .
	gen double coef_mu = .
	gen double se_mu = .
	gen long N = .
	gen str28 own_score_controls = ""

	replace specification = "Current decile FE" in 1
	replace coef_peer = `zeta_hat' in 1
	replace se_peer = `zeta_se' in 1
	replace N = `zeta_n' in 1
	replace own_score_controls = "Decile x treat x grade FE" in 1

	replace specification = "Current ventile FE" in 2
	replace coef_peer = `zeta_v' in 2
	replace se_peer = `zeta_v_se' in 2
	replace N = `zeta_n' in 2
	replace own_score_controls = "Ventile x treat x grade FE" in 2

	replace specification = "Exact BH control function" in 3
	replace coef_peer = `exact_cf_b' in 3
	replace se_peer = `exact_cf_se' in 3
	replace coef_mu = `exact_mu_b' in 3
	replace se_mu = `exact_mu_se' in 3
	replace N = `exact_cf_n' in 3
	replace own_score_controls = "Cubic std_eb x treat x grade" in 3

	replace specification = "Exact BH recentered" in 4
	replace coef_peer = `exact_rc_b' in 4
	replace se_peer = `exact_rc_se' in 4
	replace N = `exact_rc_n' in 4
	replace own_score_controls = "Cubic std_eb x treat x grade" in 4

	replace specification = "Exact BH comparability" in 5
	replace coef_peer = `exact_cmp_b' in 5
	replace se_peer = `exact_cmp_se' in 5
	replace coef_mu = `exact_cmp_mu_b' in 5
	replace se_mu = `exact_cmp_mu_se' in 5
	replace N = `exact_cmp_n' in 5
	replace own_score_controls = "Linear std_eb x treat x grade" in 5

	save "$out/kenya_exact_bh_specs.dta", replace
	export delimited using "$out/kenya_exact_bh_specs.csv", replace
restore

preserve
	clear
	set obs 4
	gen str32 specification = ""
	gen double coef_peer = .
	gen double se_peer = .
	gen double coef_mu = .
	gen double se_mu = .
	gen long N = .
	gen str26 own_score_controls = ""

	replace specification = "Exact BH, no own-score ctrl" in 1
	replace coef_peer = `exact_none_b' in 1
	replace se_peer = `exact_none_se' in 1
	replace coef_mu = `exact_none_mu_b' in 1
	replace se_mu = `exact_none_mu_se' in 1
	replace N = `exact_none_n' in 1
	replace own_score_controls = "None" in 1

	replace specification = "Exact BH, linear own-score" in 2
	replace coef_peer = `exact_cmp_b' in 2
	replace se_peer = `exact_cmp_se' in 2
	replace coef_mu = `exact_cmp_mu_b' in 2
	replace se_mu = `exact_cmp_mu_se' in 2
	replace N = `exact_cmp_n' in 2
	replace own_score_controls = "Linear std_eb x T x grade" in 2

	replace specification = "Exact BH, cubic own-score" in 3
	replace coef_peer = `exact_cf_b' in 3
	replace se_peer = `exact_cf_se' in 3
	replace coef_mu = `exact_mu_b' in 3
	replace se_mu = `exact_mu_se' in 3
	replace N = `exact_cf_n' in 3
	replace own_score_controls = "Cubic std_eb x T x grade" in 3

	replace specification = "Approx decile FE + cubic" in 4
	replace coef_peer = `approx_cubic_b' in 4
	replace se_peer = `approx_cubic_se' in 4
	replace N = `approx_cubic_n' in 4
	replace own_score_controls = "Cubic std_eb x T x grade" in 4

	save "$out/kenya_exact_bh_control_sensitivity.dta", replace
	export delimited using "$out/kenya_exact_bh_control_sensitivity.csv", replace
restore

kenya_exact_bh_toy_test
local toy_test_passed = r(passed)

tempname fh
file open `fh' using "$out/tab_peer_effects_exact_kenya.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Kenya Peer/Rank Diagnostics: Approximate vs. Exact Borusyak--Hull Specifications}" _n
file write `fh' "\label{tab:peer_effects_exact_kenya}" _n
file write `fh' "\scriptsize" _n
file write `fh' "\resizebox{0.94\textwidth}{!}{%" _n
file write `fh' "\begin{tabular}[t]{lccccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) & (2) & (3) & (4) & (5) \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-6}" _n
file write `fh' " & Decile FE & Ventile FE & Exact CF & Exact recentered & Exact CF (simple) \\" _n
file write `fh' "\midrule" _n
file write `fh' "Peer mean EB ability & `zeta_f'`zeta_star' & `zeta_v_f'`zeta_v_star' & `exact_cf_b_f'`exact_cf_star' & `exact_rc_b_f'`exact_rc_star' & `exact_cmp_b_f'`exact_cmp_star' \\" _n
file write `fh' " & (`zeta_se_f') & (`zeta_v_se_f') & (`exact_cf_se_f') & (`exact_rc_se_f') & (`exact_cmp_se_f') \\" _n
file write `fh' "Exact `ds'\mu_i^{BH}`ds' control &  &  & `exact_mu_b_f'`exact_mu_star' &  & `exact_cmp_mu_b_f'`exact_cmp_mu_star' \\" _n
file write `fh' " &  &  & (`exact_mu_se_f') &  & (`exact_cmp_mu_se_f') \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Own-score controls & Cell FE & Cell FE & Cubic EB `ds'\times`ds' T `ds'\times`ds' grade & Cubic EB `ds'\times`ds' T `ds'\times`ds' grade & Linear EB `ds'\times`ds' T `ds'\times`ds' grade \\" _n
file write `fh' "Strata FE & Yes & Yes & Yes & Yes & Yes \\" _n
file write `fh' "School-clustered SE & Yes & Yes & Yes & Yes & Yes \\" _n
file write `fh' "Observations & `zeta_n' & `zeta_n' & `exact_cf_n' & `exact_rc_n' & `exact_cmp_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}%" _n
file write `fh' "}" _n
file write `fh' "\par\smallskip" _n
file write `fh' "\begin{minipage}{0.94\textwidth}" _n
file write `fh' "\scriptsize" _n
file write `fh' "\setlength{\emergencystretch}{2em}" _n
file write `fh' "\textit{Notes:} Columns~(1)--(2) report the approximate Kenya peer/rank diagnostic specifications using baseline score bins `ds'\times`ds' treatment `ds'\times`ds' grade fixed effects. Column~(3) is the exact Borusyak--Hull control function specification: it regresses standardized endline score on the realized peer mean, excluding the focal student, and the exact expected peer regressor \(\mu_i^{BH} = p_j P_i(1) + (1-p_j) P_i(0)\), where \(P_i(1)\) is the peer mean under the deterministic treated reading-group rule and \(P_i(0)\) is the peer mean under grade-based control classrooms. Column~(4) uses the exact recentered regressor \(\tilde{P}_i = P_i^{obs} - \mu_i^{BH}\). Column~(5) keeps the exact control function but replaces the flexible cubic own-score controls with a simpler linear EB `ds'\times`ds' treatment `ds'\times`ds' grade control set. All exact specifications include strata FE and clustered standard errors at the school level. The probability \(p_j\) is the constituency-specific assignment probability from the full Kenya year-1 randomization roster (50 of 292 schools assigned to treatment). ***, **, and * indicate significance at 1\%, 5\%, and 10\%." _n
file write `fh' "\end{minipage}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_peer_effects_exact_kenya.tex"

tempname fh
file open `fh' using "$out/tab_peer_effects_exact_kenya_diag.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Kenya Exact-BH Diagnostics}" _n
file write `fh' "\label{tab:peer_effects_exact_kenya_diag}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lccc}" _n
file write `fh' "\toprule" _n
file write `fh' "Variable & Mean & SD & P50 \\" _n
file write `fh' "\midrule" _n
file write `fh' "P_obs & `mean_1_f' & `sd_1_f' & `p50_1_f' \\" _n
file write `fh' "mu_exact & `mean_2_f' & `sd_2_f' & `p50_2_f' \\" _n
file write `fh' "P_tilde & `mean_3_f' & `sd_3_f' & `p50_3_f' \\" _n
file write `fh' "\midrule" _n
file write `fh' "Obs. state identity failures & \multicolumn{3}{c}{`exact_obs_fail'} \\" _n
file write `fh' "`ds'\mu_i^{BH}`ds' outside [P0_i, P1_i] & \multicolumn{3}{c}{`exact_mu_fail'} \\" _n
file write `fh' "|`ds'\hat{\beta}_{CF} - \hat{\beta}_{RC}`ds'| & \multicolumn{3}{c}{`cf_rc_gap_f'} \\" _n
file write `fh' "Corr(`ds'\mu_i^{BH}`ds', decile approximation) & \multicolumn{3}{c}{`mu_dec_corr'} \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} P_obs is the realized leave-self-out mean peer EB ability. `ds'\mu_i^{BH}`ds' is the exact expected peer regressor from the two treatment states. The decile approximation is the projection of P_obs onto the current baseline-decile `ds'\times`ds' treatment `ds'\times`ds' grade cells. The toy-school unit test embedded in the script passed = `toy_test_passed'. Additional summary-stat and spec-level CSV/DTA outputs are written alongside this table." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_peer_effects_exact_kenya_diag.tex"

tempname fh
file open `fh' using "$out/tab_peer_effects_exact_kenya_controls.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Kenya Exact-BH Sensitivity to Own-Score Controls}" _n
file write `fh' "\label{tab:peer_effects_exact_kenya_controls}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & (1) & (2) & (3) & (4) \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' " & Exact: none & Exact: linear & Exact: cubic & Approx: decile + cubic \\" _n
file write `fh' "\midrule" _n
file write `fh' "Peer mean EB ability & `exact_none_b_f' & `exact_cmp_b_f' & `exact_cf_b_f' & `approx_cubic_b_f' \\" _n
file write `fh' " & (`exact_none_se_f') & (`exact_cmp_se_f') & (`exact_cf_se_f') & (`approx_cubic_se_f') \\" _n
file write `fh' "Exact `ds'\mu_i^{BH}`ds' control & `exact_none_mu_b_f' & `exact_cmp_mu_b_f' & `exact_mu_b_f' &  \\" _n
file write `fh' " & (`exact_none_mu_se_f') & (`exact_cmp_mu_se_f') & (`exact_mu_se_f') &  \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Observations & `exact_none_n' & `exact_cmp_n' & `exact_cf_n' & `approx_cubic_n' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Columns~(1)--(3) hold fixed the exact Borusyak--Hull control function and vary only the own-score controls: none, linear `ds'\hat{\theta}^{EB}`ds' `ds'\times`ds' treatment `ds'\times`ds' grade, and cubic `ds'\hat{\theta}^{EB}`ds' with quadratic and cubic terms fully interacted with treatment and grade. Column~(4) returns to the paper's approximate decile FE logic while using the same cubic own-score controls as column~(3). Standard errors are clustered at the school level." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_peer_effects_exact_kenya_controls.tex"

tempname fh
file open `fh' using "$out/kenya_exact_bh_note.md", write replace
file write `fh' "# Kenya exact BH note" _n _n
file write `fh' "- Construction of mu_i^BH: mu_i^BH = p_j * P1_i + (1 - p_j) * P0_i, where P1_i is the leave-self-out mean peer EB ability under Kenya's deterministic treated reading-group rule and P0_i is the leave-self-out mean peer EB ability in the grade-based control classroom. In the current Kenya analysis dataset these are already stored as peer_std_eb_treat, peer_std_eb_ctrl, and exp_peer_eb." _n
file write `fh' "- Randomization probability used: P_t is the constituency-specific assignment probability recovered from the full Kenya year-1 raw school roster. In that roster, 50 of 292 schools are treated overall, and P_t varies across constituency strata with the realized design counts." _n
file write `fh' "- Estimate comparison: decile FE = `zeta_f'; ventile FE = `zeta_v_f'; exact control function = `exact_cf_b_f'; exact recentered = `exact_rc_b_f'; exact control function (simple own-score controls) = `exact_cmp_b_f'." _n
file write `fh' "- Exact-BH change relative to approximation: exact minus decile = `d_exact_dec_f'; exact minus ventile = `d_exact_ven_f'. The control function and recentered coefficients differ by `cf_rc_gap_f'." _n
file write `fh' "- Approximation closeness: corr(exact mu_i^BH, current decile-cell approximation) = `mu_dec_corr'." _n
file write `fh' "- Mechanical checks: treated/control identity failures = `exact_obs_fail'; mu_i^BH outside [P0_i, P1_i] = `exact_mu_fail'; P_t outside [0,1] = `exact_pt_out'; max identity gap = `exact_obs_gap_max'." _n
file write `fh' "- Decomposing the exact-BH change: exact BH with no own-score controls = `exact_none_b_f'; exact BH with linear own-score controls = `exact_cmp_b_f'; exact BH with cubic own-score controls = `exact_cf_b_f'; approximate decile FE with the same cubic own-score controls = `approx_cubic_b_f'." _n
file write `fh' "- Missing-baseline sensitivity: recomputing both state-specific peer objects after excluding students with missing baseline from the counterfactual classroom means gives exact BH control function = `exact_obsbl_cf_b_f' and exact recentered = `exact_obsbl_rc_b_f' (change relative to baseline exact cubic = `d_exact_to_obsbl_cubic_f')." _n
file write `fh' "- Control sensitivity differences: linear minus none = `d_none_to_linear_f'; cubic minus linear = `d_linear_to_cubic_f'; exact cubic minus approximate cubic = `d_approx_to_exact_cubic_f'." _n
file write `fh' "- Ambiguities and fallbacks used: the optional comparability spec is implemented as the exact control function regression with linear std_eb x treat x grade controls, while the preferred exact spec uses cubic std_eb, std_eb^2, and std_eb^3 each fully interacted with treatment and grade. Missing constituency labels in the raw Kenya files are filled from county using the same regional stratification implicit in the legacy cleaning code before constructing P_t." _n
file close `fh'
di "  -> kenya_exact_bh_note.md"

* Part 4: Cross-decile prediction check
cap drop treat_d*
forvalues d = 1/10 {
	gen treat_d`d' = treat * (bl_decile == `d')
}
qui reg std_score_el treat_d1-treat_d10 i.bl_decile std_eb i.strata, vce(cluster academycode)

tempfile overid_dat
postfile pf_ov decile actual predicted using `overid_dat'
forvalues d = 1/10 {
	local act = _b[treat_d`d']
	qui summ peer_eb if treat == 1 & bl_decile == `d'
	local pt_d = r(mean)
	qui summ peer_eb if treat == 0 & bl_decile == `d'
	local pc_d = r(mean)
	local pred = `zeta_hat' * (`pt_d' - `pc_d')
	post pf_ov (`d') (`act') (`pred')
}
postclose pf_ov

cap program drop overid_boot
program define overid_boot, rclass
	cap drop _dtg_bs
	egen _dtg_bs = group(bl_decile treat grade)
	qui reg std_score_el peer_eb i._dtg_bs i.strata
	local z = _b[peer_eb]
	drop _dtg_bs
	forvalues d = 1/10 {
		qui summ peer_eb if treat == 1 & bl_decile == `d'
		local pt = r(mean)
		qui summ peer_eb if treat == 0 & bl_decile == `d'
		local pc = r(mean)
		return scalar pred`d' = `z' * (`pt' - `pc')
	}
end

capture noisily bootstrap pred1=r(pred1) pred2=r(pred2) pred3=r(pred3) pred4=r(pred4) pred5=r(pred5) ///
	pred6=r(pred6) pred7=r(pred7) pred8=r(pred8) pred9=r(pred9) pred10=r(pred10), ///
	reps(1000) cluster(academycode) idcluster(_bsid2) group(academycode) seed(20240102): ///
	overid_boot
if _rc == 0 {
	forvalues d = 1/10 {
		local pse`d' = _se[pred`d']
	}
}
else {
	di "  Bootstrap overid failed; using manual loop..."
	local B = 1000
	tempname bmat2
	matrix `bmat2' = J(`B', 10, .)
	preserve
	forval b = 1/`B' {
		restore, preserve
		bsample, cluster(academycode)
		cap drop _dtg_bs
		egen _dtg_bs = group(bl_decile treat grade)
		qui reg std_score_el peer_eb i._dtg_bs i.strata
		local z = _b[peer_eb]
		drop _dtg_bs
		forvalues d = 1/10 {
			qui summ peer_eb if treat == 1 & bl_decile == `d'
			local pt = r(mean)
			qui summ peer_eb if treat == 0 & bl_decile == `d'
			local pc = r(mean)
			matrix `bmat2'[`b', `d'] = `z' * (`pt' - `pc')
		}
	}
	restore
	svmat `bmat2', names(_bov_)
	forvalues d = 1/10 {
		qui summ _bov_`d'
		local pse`d' = r(sd)
	}
	drop _bov_*
}

preserve
	use `overid_dat', clear
	gen se_pred = .
	forvalues d = 1/10 {
		replace se_pred = `pse`d'' if decile == `d'
	}
	gen lb = predicted - 1.645 * se_pred
	gen ub = predicted + 1.645 * se_pred

	qui corr actual predicted
	local ov_corr : di %5.2f r(rho)
	gen sq = (actual - predicted)^2
	qui summ sq
	local ov_rmse : di %5.3f sqrt(r(mean))

	twoway ///
		(rarea ub lb decile, fcolor(gs12) lcolor(none)) ///
		(connected actual decile, lcolor(navy) mcolor(navy) msymbol(O) lwidth(medthick)) ///
		(connected predicted decile, lcolor(maroon) mcolor(maroon) msymbol(D) lpattern(dash)), ///
		yline(0, lcolor(gs10) lpattern(dash)) ///
		xlabel(1(1)10) ///
		xtitle("Baseline score decile") ///
		ytitle("ITT effect (SD)") ///
		legend(order(2 "Actual ITT" 3 "Predicted (peer channel)" 1 "90% CI") ///
			pos(6) row(1) size(small)) ///
		note("Correlation: `ov_corr'    RMSE: `ov_rmse'") ///
		scheme(s1mono)
	graph export "$out/fig_overid_kenya.pdf", replace
restore
di "  -> fig_overid_kenya.pdf"

* Quintile version (cleaner 5-bin overid check)
cap drop bl_quintile treat_q*
gen bl_quintile = .
levelsof grade, local(grades_q)
foreach g of local grades_q {
	qui xtile _q = score_bl if grade == `g', nq(5)
	replace bl_quintile = _q if grade == `g'
	drop _q
}
forvalues q = 1/5 {
	gen treat_q`q' = treat * (bl_quintile == `q')
}
qui reg std_score_el treat_q1-treat_q5 i.bl_quintile std_eb i.strata, vce(cluster academycode)

tempfile overid_dat_q
postfile pf_ovq quintile actual predicted using `overid_dat_q'
forvalues q = 1/5 {
	local act = _b[treat_q`q']
	qui summ peer_eb if treat == 1 & bl_quintile == `q'
	local pt_q = r(mean)
	qui summ peer_eb if treat == 0 & bl_quintile == `q'
	local pc_q = r(mean)
	local pred = `zeta_hat' * (`pt_q' - `pc_q')
	post pf_ovq (`q') (`act') (`pred')
}
postclose pf_ovq

cap program drop overid_boot_q
program define overid_boot_q, rclass
	cap drop _qtg_bs
	egen _qtg_bs = group(bl_quintile treat grade)
	qui reg std_score_el peer_eb i._qtg_bs i.strata
	local z = _b[peer_eb]
	drop _qtg_bs
	forvalues q = 1/5 {
		qui summ peer_eb if treat == 1 & bl_quintile == `q'
		local pt = r(mean)
		qui summ peer_eb if treat == 0 & bl_quintile == `q'
		local pc = r(mean)
		return scalar pred`q' = `z' * (`pt' - `pc')
	}
end

capture noisily bootstrap pred1=r(pred1) pred2=r(pred2) pred3=r(pred3) pred4=r(pred4) pred5=r(pred5), ///
	reps(1000) cluster(academycode) idcluster(_bsid3) group(academycode) seed(20240103): ///
	overid_boot_q
if _rc == 0 {
	forvalues q = 1/5 {
		local pse_q`q' = _se[pred`q']
	}
}
else {
	local B = 1000
	tempname bmat3
	matrix `bmat3' = J(`B', 5, .)
	preserve
	forval b = 1/`B' {
		restore, preserve
		bsample, cluster(academycode)
		cap drop _qtg_bs
		egen _qtg_bs = group(bl_quintile treat grade)
		qui reg std_score_el peer_eb i._qtg_bs i.strata
		local z = _b[peer_eb]
		drop _qtg_bs
		forvalues q = 1/5 {
			qui summ peer_eb if treat == 1 & bl_quintile == `q'
			local pt = r(mean)
			qui summ peer_eb if treat == 0 & bl_quintile == `q'
			local pc = r(mean)
			matrix `bmat3'[`b', `q'] = `z' * (`pt' - `pc')
		}
	}
	restore
	svmat `bmat3', names(_bovq_)
	forvalues q = 1/5 {
		qui summ _bovq_`q'
		local pse_q`q' = r(sd)
	}
	drop _bovq_*
}

preserve
	use `overid_dat_q', clear
	gen se_pred = .
	forvalues q = 1/5 {
		replace se_pred = `pse_q`q'' if quintile == `q'
	}
	gen lb = predicted - 1.645 * se_pred
	gen ub = predicted + 1.645 * se_pred
	qui corr actual predicted
	local ovq_corr : di %5.2f r(rho)
	gen sq = (actual - predicted)^2
	qui summ sq
	local ovq_rmse : di %5.3f sqrt(r(mean))

	twoway ///
		(rarea ub lb quintile, fcolor(gs12) lcolor(none)) ///
		(connected actual quintile, lcolor(navy) mcolor(navy) msymbol(O) lwidth(medthick)) ///
		(connected predicted quintile, lcolor(maroon) mcolor(maroon) msymbol(D) lpattern(dash)), ///
		yline(0, lcolor(gs10) lpattern(dash)) ///
		xlabel(1(1)5) ///
		xtitle("Baseline score quintile") ///
		ytitle("ITT effect (SD)") ///
		legend(order(2 "Actual ITT" 3 "Predicted (peer channel)" 1 "90% CI") ///
			pos(6) row(1) size(small)) ///
		note("Correlation: `ovq_corr'    RMSE: `ovq_rmse'") ///
		scheme(s1mono)
	graph export "$out/fig_overid_kenya_quintile.pdf", replace
restore
di "  -> fig_overid_kenya_quintile.pdf"

* ═══════════════════════════════════════════════════════════════════════════
* C. LIBERIA: DESCRIPTIVE SHIFTS AND BH NULL
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== C. Liberia Descriptive Decomposition ==="

use "$out/analysis_liberia.dta", clear
keep if finsamp & has_el
keep if !mi(std_score_el) & !mi(std_eb) & !mi(peer_eb) & !mi(score_bl) & !mi(grade) & !mi(strata)

bys std_grp grade: egen track_target_t = mean(cond(treat == 1, std_eb, .))
bys grade:         egen track_target_c = mean(cond(treat == 0, std_eb, .))
gen track_target = cond(treat == 1, track_target_t, track_target_c)
gen abs_misfit = abs(std_eb - track_target)
drop track_target_t track_target_c

* Within-class baseline SD
capture confirm variable std_score_bl
if _rc != 0 {
	di as error "Variable std_score_bl not found in Liberia analysis dataset."
	exit 111
}
capture confirm variable schoolcode
if _rc == 0 {
	local schid schoolcode
}
else {
	capture confirm variable academycode
	if _rc == 0 local schid academycode
	else {
		di as error "No school identifier found (expected schoolcode or academycode)."
		exit 111
	}
}
bys `schid' std_grp: egen _sd_bl_t = sd(std_score_bl) if treat == 1
bys `schid' grade:   egen _sd_bl_c = sd(std_score_bl) if treat == 0
gen within_sd = cond(treat == 1, _sd_bl_t, _sd_bl_c)
drop _sd_bl_t _sd_bl_c

cap confirm variable bl_decile
if _rc != 0 {
	gen bl_decile = .
	levelsof grade, local(grades_lb)
	foreach g of local grades_lb {
		qui xtile _dec = score_bl if grade == `g', nq(10)
		replace bl_decile = _dec if grade == `g'
		drop _dec
	}
}
egen dtg_cell = group(bl_decile treat grade)

* BH peer estimate
qui reg std_score_el peer_eb i.dtg_cell i.strata, vce(cluster ggroup)
local zl_hat  = _b[peer_eb]
local zl_se   = _se[peer_eb]
local zl_pv   = 2 * ttail(e(df_r), abs(`zl_hat'/`zl_se'))
get_stars `zl_pv'
local zl_star "`r(stars)'"
local zl_n    = e(N)
local zl_f    : di %7.3f `zl_hat'
local zl_se_f : di %7.3f `zl_se'

* Descriptive shifts
qui summ abs_misfit if treat == 0
local lm_c = r(mean)
qui summ abs_misfit if treat == 1
local lm_t = r(mean)
local ld_mis : di %7.3f `lm_c' - `lm_t'

qui summ peer_eb if treat == 0
local lp_c = r(mean)
qui summ peer_eb if treat == 1
local lp_t = r(mean)
local ld_peer : di %7.3f `lp_t' - `lp_c'

qui summ csize if treat == 0
local lc_c = r(mean)
qui summ csize if treat == 1
local lc_t = r(mean)
local ld_cs : di %7.1f `lc_t' - `lc_c'

qui summ within_sd if treat == 0
local ls_c = r(mean)
qui summ within_sd if treat == 1
local ls_t = r(mean)
local ld_sd : di %7.3f `ls_c' - `ls_t'

* Liberia ITT
qui reg std_score_el treat std_eb i.strata, vce(cluster ggroup)
local litt   = _b[treat]
local litt_se = _se[treat]
local litt_f  : di %7.3f `litt'
local litt_se_f : di %7.3f `litt_se'

tempname fh
file open `fh' using "$out/tab_suffstat_liberia.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Peer/Rank Diagnostics and Classroom Shifts: Liberia}" _n
file write `fh' "\label{tab:suffstat_liberia}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{Liberia} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2}" _n
file write `fh' " & Estimate \\" _n
file write `fh' "\midrule" _n
file write `fh' "\multicolumn{2}{l}{\textit{Panel A: Approximate Borusyak--Hull peer/rank coefficient}} \\" _n
file write `fh' "`ds'\hat{\zeta}_{Lib}`ds' & `zl_f'`zl_star' (`zl_se_f') \\" _n
file write `fh' "Observations & `zl_n' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "\multicolumn{2}{l}{\textit{Panel B: Treatment-induced classroom shifts}} \\" _n
file write `fh' "`ds'\Delta`ds' absolute EB-to-target mismatch (C `ds'-`ds' T) & `ld_mis' \\" _n
file write `fh' "`ds'\Delta`ds' peer composition (T `ds'-`ds' C) & `ld_peer' \\" _n
file write `fh' "`ds'\Delta`ds' class size (T `ds'-`ds' C) & `ld_cs' \\" _n
file write `fh' "`ds'\Delta`ds' within class baseline SD (C `ds'-`ds' T) & `ld_sd' \\" _n
file write `fh' "\addlinespace" _n
file write `fh' "Overall ITT & `litt_f' (`litt_se_f') \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Panel A reports the approximate Borusyak--Hull control function peer/rank coefficient "
file write `fh' "using decile `ds'\times`ds' treatment `ds'\times`ds' grade FE\@. Standard errors "
file write `fh' "clustered at the school grade group level. Panel B reports treatment control differences "
file write `fh' "in classroom characteristics. The near-zero peer/rank coefficient and small "
file write `fh' "classroom composition shift provide little evidence that the measured "
file write `fh' "peer/rank channel explains the negative Liberia ITT pattern." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_suffstat_liberia.tex"


* ── Liberia sensitivity grid ──────────────────────────────────────────────
* Uses Kenya zeta_hat transported to Liberia shifts
* Normalize class size change by pooled SD so grid parameters are per-SD
qui summ csize
local cs_sd = r(sd)
local dm_l = `lm_c' - `lm_t'
local dp_l = `lp_t' - `lp_c'
local dd_l = (`lc_t' - `lc_c') / `cs_sd'

tempname fh
file open `fh' using "$out/tab_lib_sensitivity.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Liberia Sensitivity: Predicted Effect under Transported Kenya Parameters}" _n
file write `fh' "\label{tab:lib_sensitivity}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{l*{5}{c}}" _n
file write `fh' "\toprule" _n
file write `fh' " & \multicolumn{5}{c}{Disruption cost (`ds'\psi`ds')} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-6}" _n
file write `fh' "`ds'\lambda`ds' & 0.0 & 0.1 & 0.3 & 0.5 & 1.0 \\" _n
file write `fh' "\midrule" _n

foreach lam in 0.00 0.05 0.10 0.20 0.30 0.50 {
	local row : di %4.2f `lam'
	foreach psi in 0.0 0.1 0.3 0.5 1.0 {
		local eff = `lam' * `dm_l' + `zeta_hat' * `dp_l' - `psi' * `dd_l'
		local ef : di %7.3f `eff'
		local row "`row' & `ef'"
	}
	file write `fh' "`row' \\" _n
}

file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para,flushleft]" _n
file write `fh' "\footnotesize" _n
file write `fh' "\item \textit{Notes:} Each cell reports the predicted Liberia ITT: "
file write `fh' "`ds'\lambda \cdot \Delta\text{Mismatch} + \hat{\zeta}_{\text{Ken}} \cdot \Delta\text{Peer} - \psi \cdot \Delta\text{ClassSize}`ds'. "
file write `fh' "Liberia treatment control shifts are used; class size change is divided by its pooled SD. "
file write `fh' "`ds'\lambda`ds' (mismatch return) and `ds'\psi`ds' (disruption cost per SD of class size) vary over the grid; "
file write `fh' "`ds'\hat{\zeta}_{\text{Ken}}`ds' is fixed at the Kenya BH peer estimate. "
file write `fh' "Positive values indicate that ability grouping is predicted to raise scores." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_lib_sensitivity.tex"


* ═══════════════════════════════════════════════════════════════════════════
* D. FOUR-MARGIN SUMMARY TABLE
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== D. Four-Margin Summary ==="

* Signal quality
foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & treat == 0 & !mi(score_bl) & !mi(score_el)
	local wt_r2 = 0
	local wt_n = 0
	levelsof grade, local(grades)
	foreach g of local grades {
		qui corr score_bl score_el if grade == `g'
		local r2 = r(rho)^2
		qui count if grade == `g'
		local ng = r(N)
		local wt_r2 = `wt_r2' + `r2' * `ng'
		local wt_n = `wt_n' + `ng'
	}
	local r2g_`study' : di %6.3f `wt_r2' / `wt_n'
}

* Observed cutoff compliance among treated students
foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & treat == 1 & !mi(score_bl) & !mi(upper_group)
	gen byte _det_rule = .
	if "`study'" == "kenya" {
		replace _det_rule = (score_bl > $ke_cutoff_g1) if grade == 1
		replace _det_rule = (score_bl > $ke_cutoff_g2) if grade == 2
	}
	if "`study'" == "liberia" {
		replace _det_rule = (score_bl > $lib_cutoff_g12) if inlist(grade, 1, 2)
		replace _det_rule = (score_bl > $lib_cutoff_g34) if inlist(grade, 3, 4)
	}
	gen byte _noncomply = _det_rule != upper_group if !mi(_det_rule)
	qui summ _noncomply
	local comply_`study' : di %6.3f 1 - r(mean)
}

* Mismatch reduction + class size difference (using corrected track-level grand means)
foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & has_el
	keep if !mi(std_eb) & !mi(grade)
	bys std_grp grade: egen _tt_t = mean(cond(treat == 1, std_eb, .))
	bys grade:         egen _tt_c = mean(cond(treat == 0, std_eb, .))
	gen _track_tgt = cond(treat == 1, _tt_t, _tt_c)
	gen _abs_misfit = abs(std_eb - _track_tgt)
	qui summ _abs_misfit if treat == 0
	local mis_c = r(mean)
	qui summ _abs_misfit if treat == 1
	local mis_t = r(mean)
	local dmis_`study' : di %6.3f `mis_c' - `mis_t'
	qui summ csize if treat == 1
	local cs_t = r(mean)
	qui summ csize if treat == 0
	local cs_c = r(mean)
	local dcs_`study' : di %6.1f `cs_t' - `cs_c'
}

tempname fh
file open `fh' using "$out/tab_four_margins.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Four-Margin Summary: Kenya vs.\ Liberia}" _n
file write `fh' "\label{tab:four_margins}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{2}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3}" _n
file write `fh' " & Kenya & Liberia \\" _n
file write `fh' "\midrule" _n
file write `fh' "Weighted R-squared (R2_g) & `r2g_kenya' & `r2g_liberia' \\" _n
file write `fh' "Cutoff compliance & `comply_kenya' & `comply_liberia' \\" _n
file write `fh' "Absolute mismatch reduction (C-T) & `dmis_kenya' & `dmis_liberia' \\" _n
file write `fh' "Class size difference (T-C) & `dcs_kenya' & `dcs_liberia' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Weighted R-squared (R2_g) averages across grades by control\mbox{-}group size. "
file write `fh' "Cutoff compliance = 1 indicates that observed track assignments exactly follow the published deterministic cutoffs. "
file write `fh' "Absolute mismatch reduction is the control-minus-treatment difference in mean `ds'\lvert\hat{\theta}^{EB}_i - \bar{I}_k\rvert`ds'. "
file write `fh' "Class size difference is treatment-minus-control difference in mean classroom size." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_four_margins.tex"


* Four-margins visualization
preserve
	clear
	set obs 8
	gen str26 margin = ""
	gen str8 study = ""
	gen double value = .
	replace margin = "Weighted rho2" in 1
	replace study = "Kenya" in 1
	replace value = `r2g_kenya' in 1
	replace margin = "Weighted rho2" in 2
	replace study = "Liberia" in 2
	replace value = `r2g_liberia' in 2
	replace margin = "Cutoff compliance" in 3
	replace study = "Kenya" in 3
	replace value = `comply_kenya' in 3
	replace margin = "Cutoff compliance" in 4
	replace study = "Liberia" in 4
	replace value = `comply_liberia' in 4
	replace margin = "Mismatch red. (C-T)" in 5
	replace study = "Kenya" in 5
	replace value = `dmis_kenya' in 5
	replace margin = "Mismatch red. (C-T)" in 6
	replace study = "Liberia" in 6
	replace value = `dmis_liberia' in 6
	replace margin = "Class size chg. (T-C)" in 7
	replace study = "Kenya" in 7
	replace value = `dcs_kenya' in 7
	replace margin = "Class size chg. (T-C)" in 8
	replace study = "Liberia" in 8
	replace value = `dcs_liberia' in 8
	graph bar (asis) value, over(margin, label(angle(0))) over(study) ///
		asyvars legend(order(1 "Signal quality (R2)" 2 "Cutoff compliance" 3 "Mismatch reduction" 4 "Class-size shift") pos(6) row(2) size(small)) ///
		yline(0, lcolor(gs10) lpattern(dash)) ///
		ytitle("") ///
		scheme(s1mono)
	graph export "$out/fig_four_margins.pdf", replace
	di "  -> fig_four_margins.pdf"
restore


* ═══════════════════════════════════════════════════════════════════════════
* E. ASSIGNMENT CUTOFF TABLE + DETERMINISTIC CUTOFF FIGURE
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== E. Assignment cutoffs and deterministic rule ==="

foreach g in 1 2 3 4 {
	local k_cut_`g' ""
	local k_nt_`g' ""
	local k_err_`g' ""
	local l_cut_`g' ""
	local l_nt_`g' ""
	local l_err_`g' ""
}

use "$out/analysis_kenya.dta", clear
keep if finsamp & treat == 1 & !mi(score_bl) & !mi(upper_group)
foreach g in 1 2 {
	if `g' == 1 local c = $ke_cutoff_g1
	if `g' == 2 local c = $ke_cutoff_g2
	qui count if grade == `g'
	local k_nt_`g' = r(N)
	gen byte det_rule = score_bl > `c' if grade == `g'
	gen byte rule_error = det_rule != upper_group if grade == `g'
	qui summ rule_error if grade == `g'
	local k_err_`g' : di %5.3f r(mean)
	local k_cut_`g' "`c'"
	drop det_rule rule_error
}

use "$out/analysis_liberia.dta", clear
keep if finsamp & treat == 1 & !mi(score_bl) & !mi(upper_group)
foreach g in 1 2 3 4 {
	if inlist(`g', 1, 2) local c = $lib_cutoff_g12
	if inlist(`g', 3, 4) local c = $lib_cutoff_g34
	qui count if grade == `g'
	local l_nt_`g' = r(N)
	gen byte det_rule = score_bl > `c' if grade == `g'
	gen byte rule_error = det_rule != upper_group if grade == `g'
	qui summ rule_error if grade == `g'
	local l_err_`g' : di %5.3f r(mean)
	local l_cut_`g' "`c'"
	drop det_rule rule_error
}

tempname fh
file open `fh' using "$out/tab_assignment_cutoffs.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Deterministic Assignment Cutoffs}" _n
file write `fh' "\label{tab:assignment_cutoffs}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{l c c c c c c}" _n
file write `fh' "\toprule" _n
file write `fh' "& \multicolumn{6}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-7}" _n
file write `fh' " & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} & \multicolumn{1}{c}{(5)} & \multicolumn{1}{c}{(6)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5} \cmidrule(l{3pt}r{3pt}){6-6} \cmidrule(l{3pt}r{3pt}){7-7}" _n
file write `fh' "& \multicolumn{3}{c}{Kenya} & \multicolumn{3}{c}{Liberia} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-4} \cmidrule(l{3pt}r{3pt}){5-7}" _n
file write `fh' "Grade & Cutoff & N treated & Rule error & Cutoff & N treated & Rule error \\" _n
file write `fh' "\midrule" _n
file write `fh' "1 & `k_cut_1' & `k_nt_1' & `k_err_1' & `l_cut_1' & `l_nt_1' & `l_err_1' \\" _n
file write `fh' "2 & `k_cut_2' & `k_nt_2' & `k_err_2' & `l_cut_2' & `l_nt_2' & `l_err_2' \\" _n
file write `fh' "3 &  &  &  & `l_cut_3' & `l_nt_3' & `l_err_3' \\" _n
file write `fh' "4 &  &  &  & `l_cut_4' & `l_nt_4' & `l_err_4' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: The table reports score thresholds used to assign treated students "
file write `fh' "to the upper reading track. Rule error is the share of treated students whose observed "
file write `fh' "upper-track assignment differs from the published deterministic cutoff rule." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_assignment_cutoffs.tex"

* Deterministic cutoff figure (Kenya panel)
use "$out/analysis_kenya.dta", clear
keep if finsamp & treat == 1 & !mi(score_bl) & !mi(upper_group)
bys grade (score_bl): gen long rank_in_grp = _n
bys grade: gen long n_in_grp = _N
gen bl_bin = ceil(12 * rank_in_grp / n_in_grp)
collapse (mean) score_bl upper_group, by(grade bl_bin)
qui summ score_bl
local xmin_k = r(min)
local xmax_k = r(max)
twoway ///
	(scatter upper_group score_bl if grade == 1, mcolor(navy) msymbol(o)) ///
	(scatter upper_group score_bl if grade == 2, mcolor(maroon) msymbol(triangle)) ///
	(function y = x > $ke_cutoff_g1, range(`xmin_k' `xmax_k') lcolor(navy) lpattern(dash)) ///
	(function y = x > $ke_cutoff_g2, range(`xmin_k' `xmax_k') lcolor(maroon) lpattern(dash)), ///
	ytitle("Pr(upper track)") xtitle("Baseline score") ///
	title("Kenya") legend(order(1 "G1 binned" 2 "G2 binned" 3 "G1 cutoff" 4 "G2 cutoff") pos(6) row(2)) ///
	name(g_det_k, replace) scheme(s1mono)

* Deterministic cutoff figure (Liberia panel)
use "$out/analysis_liberia.dta", clear
keep if finsamp & treat == 1 & !mi(score_bl) & !mi(upper_group)
gen byte grade_block = cond(inlist(grade, 1, 2), 12, 34)
bys grade_block (score_bl): gen long rank_in_grp = _n
bys grade_block: gen long n_in_grp = _N
gen bl_bin = ceil(12 * rank_in_grp / n_in_grp)
collapse (mean) score_bl upper_group, by(grade_block bl_bin)
qui summ score_bl
local xmin_l = r(min)
local xmax_l = r(max)
twoway ///
	(scatter upper_group score_bl if grade_block == 12, mcolor(navy) msymbol(o)) ///
	(scatter upper_group score_bl if grade_block == 34, mcolor(maroon) msymbol(triangle)) ///
	(function y = x > $lib_cutoff_g12, range(`xmin_l' `xmax_l') lcolor(navy) lpattern(dash)) ///
	(function y = x > $lib_cutoff_g34, range(`xmin_l' `xmax_l') lcolor(maroon) lpattern(dash)), ///
	ytitle("Pr(upper track)") xtitle("Baseline score") ///
	title("Liberia") legend(off) name(g_det_l, replace) scheme(s1mono)

graph combine g_det_k g_det_l, cols(2) ///
	imargin(2 2 2 2) scheme(s1mono)
graph export "$out/fig_deterministic_cutoffs.pdf", replace
di "  -> fig_deterministic_cutoffs.pdf"


* ═══════════════════════════════════════════════════════════════════════════
* F. CLASSROOM REALLOCATION TABLE + FIGURE
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== F. Classroom reallocation ==="

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp

	gen str class_id = string(academycode) + "_" + string(cond(treat == 1, std_grp, grade))
	bys class_id: egen class_size = count(studyid)
	bys class_id: egen grade_sd = sd(grade)
	gen grade_var = grade_sd^2
	replace grade_var = 0 if mi(grade_var)
	bys class_id grade: gen byte grade_tag = _n == 1
	bys class_id: egen n_grades = total(grade_tag)

	bys std_grp grade: egen target_t = mean(std_eb) if treat == 1
	bys grade:   egen target_c = mean(std_eb) if treat == 0
	gen track_target = cond(treat == 1, target_t, target_c)
	gen mismatch_track = (std_eb - track_target)^2

	foreach arm in 0 1 {
		qui summ class_size if treat == `arm'
		local cs_`study'_`arm' : di %6.2f r(mean)
		qui summ grade_var if treat == `arm'
		local gv_`study'_`arm' : di %6.3f r(mean)
		qui summ n_grades if treat == `arm'
		local ng_`study'_`arm' : di %6.3f r(mean)
		qui summ mismatch_track if treat == `arm'
		local mm_`study'_`arm' : di %6.3f r(mean)
		qui summ peer_eb if treat == `arm'
		local pe_`study'_`arm' : di %6.3f r(mean)
	}

	local dcs_`study' = `cs_`study'_1' - `cs_`study'_0'
	local dgv_`study' = `gv_`study'_1' - `gv_`study'_0'
	local dng_`study' = `ng_`study'_1' - `ng_`study'_0'
}

tempname fh
file open `fh' using "$out/tab_classroom_reallocation.tex", write replace
file write `fh' "\begin{table}[H]" _n
file write `fh' "\centering" _n
file write `fh' "\caption{Classroom Reallocation under Cross-Grade Grouping}" _n
file write `fh' "\label{tab:classroom_reallocation}" _n
file write `fh' "\begin{threeparttable}" _n
file write `fh' "\begin{tabular}[t]{lcccc}" _n
file write `fh' "\toprule" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{4}{c}{Experiments} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-5}" _n
file write `fh' "\multicolumn{1}{c}{ } & \multicolumn{1}{c}{(1)} & \multicolumn{1}{c}{(2)} & \multicolumn{1}{c}{(3)} & \multicolumn{1}{c}{(4)} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-2} \cmidrule(l{3pt}r{3pt}){3-3} \cmidrule(l{3pt}r{3pt}){4-4} \cmidrule(l{3pt}r{3pt}){5-5}" _n
file write `fh' " & \multicolumn{2}{c}{Kenya} & \multicolumn{2}{c}{Liberia} \\" _n
file write `fh' "\cmidrule(l{3pt}r{3pt}){2-3} \cmidrule(l{3pt}r{3pt}){4-5}" _n
file write `fh' " & Control & Treat & Control & Treat \\" _n
file write `fh' "\midrule" _n
file write `fh' "Class size & `cs_kenya_0' & `cs_kenya_1' & `cs_liberia_0' & `cs_liberia_1' \\" _n
file write `fh' "Within-class grade variance & `gv_kenya_0' & `gv_kenya_1' & `gv_liberia_0' & `gv_liberia_1' \\" _n
file write `fh' "Number of grades in class & `ng_kenya_0' & `ng_kenya_1' & `ng_liberia_0' & `ng_liberia_1' \\" _n
file write `fh' "Squared track target misfit & `mm_kenya_0' & `mm_kenya_1' & `mm_liberia_0' & `mm_liberia_1' \\" _n
file write `fh' "Peer mean EB ability & `pe_kenya_0' & `pe_kenya_1' & `pe_liberia_0' & `pe_liberia_1' \\" _n
file write `fh' "\bottomrule" _n
file write `fh' "\end{tabular}" _n
file write `fh' "\begin{tablenotes}[para]" _n
file write `fh' "\item Notes: Entries are arm-specific means in the structural analysis sample. "
file write `fh' "Realized classroom margins use treated-track classes in treatment and grade "
file write `fh' "classes in control. Squared track target misfit is the square of EB ability minus the track target." _n
file write `fh' "\end{tablenotes}" _n
file write `fh' "\end{threeparttable}" _n
file write `fh' "\end{table}" _n
file close `fh'
di "  -> tab_classroom_reallocation.tex"

preserve
	clear
	set obs 6
	gen str22 metric = ""
	gen str8 study = ""
	gen double delta = .
	replace metric = "Class size" in 1
	replace study = "Kenya" in 1
	replace delta = `dcs_kenya' in 1
	replace metric = "Class size" in 2
	replace study = "Liberia" in 2
	replace delta = `dcs_liberia' in 2
	replace metric = "Grade variance" in 3
	replace study = "Kenya" in 3
	replace delta = `dgv_kenya' in 3
	replace metric = "Grade variance" in 4
	replace study = "Liberia" in 4
	replace delta = `dgv_liberia' in 4
	replace metric = "Number of grades" in 5
	replace study = "Kenya" in 5
	replace delta = `dng_kenya' in 5
	replace metric = "Number of grades" in 6
	replace study = "Liberia" in 6
	replace delta = `dng_liberia' in 6
	graph bar delta, over(metric) over(study) asyvars ///
		legend(order(1 "Class size" 2 "Grade mixing" 3 "Grades per class") pos(6) row(1) size(small)) ///
		yline(0, lcolor(gs10) lpattern(dash)) ///
		ytitle("Treatment - Control") ///
		scheme(s1mono)
	graph export "$out/fig_classroom_reallocation.pdf", replace
	di "  -> fig_classroom_reallocation.pdf"
restore


* ═══════════════════════════════════════════════════════════════════════════
* G. POSTERIOR SHRINKAGE FIGURE (raw baseline vs EB posterior)
* ═══════════════════════════════════════════════════════════════════════════

di _n "=== G. Posterior shrinkage figure ==="

foreach study in kenya liberia {
	use "$out/analysis_`study'.dta", clear
	keep if finsamp & !mi(score_bl)
	gen double a_hat = .
	levelsof grade, local(grades)
	foreach g of local grades {
		qui corr score_bl score_el if treat == 0 & grade == `g' & !mi(score_bl) & !mi(score_el)
		local rho2 = r(rho)^2
		qui summ score_bl if treat == 0 & grade == `g' & !mi(score_bl)
		local mu = r(mean)
		replace a_hat = `mu' + `rho2' * (score_bl - `mu') if grade == `g'
	}
	keep if !mi(a_hat)
	qui count
	if r(N) > 3000 {
		set seed 12345
		gen u = runiform()
		sort u
		keep in 1/3000
		drop u
	}
	if "`study'" == "kenya" local stlab "Kenya"
	if "`study'" == "liberia" local stlab "Liberia"
	if "`study'" == "kenya" {
		twoway ///
			(scatter a_hat score_bl if grade == 1, mcolor(navy%35) msymbol(oh) msize(vsmall)) ///
			(scatter a_hat score_bl if grade == 2, mcolor(maroon%35) msymbol(oh) msize(vsmall)), ///
			xtitle("Raw baseline score") ytitle("Posterior mean ability") ///
			title("Kenya") ///
			legend(order(1 "Grade 1" 2 "Grade 2") pos(6) row(1) size(small)) ///
			name(g_ps_`study', replace) scheme(s1mono)
	}
	if "`study'" == "liberia" {
		twoway ///
			(scatter a_hat score_bl if grade == 1, mcolor(navy%35) msymbol(oh) msize(vsmall)) ///
			(scatter a_hat score_bl if grade == 2, mcolor(maroon%35) msymbol(oh) msize(vsmall)) ///
			(scatter a_hat score_bl if grade == 3, mcolor(forest_green%35) msymbol(oh) msize(vsmall)) ///
			(scatter a_hat score_bl if grade == 4, mcolor(orange%35) msymbol(oh) msize(vsmall)), ///
			xtitle("Raw baseline score") ytitle("Posterior mean ability") ///
			title("Liberia") ///
			legend(order(1 "Grade 1" 2 "Grade 2" 3 "Grade 3" 4 "Grade 4") pos(6) row(1) size(small)) ///
			name(g_ps_`study', replace) scheme(s1mono)
	}
}

graph combine g_ps_kenya g_ps_liberia, cols(2) ///
	scheme(s1mono)
graph export "$out/fig_posterior_shrinkage.pdf", replace
di "  -> fig_posterior_shrinkage.pdf"


di _n "{hline 70}"
di "Structural estimation complete."
di "{hline 70}"
