

/*==========================================================================

Title: distance_from_instruction.do 
Author: Mridul Joshi
Date: Tue Nov 15 13:20:11 2022

Description: Distance from different quantiles of baseline test scores

Key input: 
Key output: 

Last edited by:  

===========================================================================*/


use "${datadir}/Kenya/6_K_AG_full_wide_prepared.dta", clear 

keep if finsamp

cap drop d0 d1

/*
gen prebl = .
levels academycode
// create prebl
foreach x in `r(levels)' {
    xi : reg std_comp_score_el i.grade*std_comp_score_bl if academycode!=`x'
    predict temppred
    replace prebl = temppred if academycode==`x'
    drop temppred
}
*/



mat res = J(100,4,.)
local r 0 
foreach i in 10 25  50  75  90  {
    foreach j in 10  25 50 75 90  {  
        local ++r
        cap drop d0 d1 Ed d 
        local pt1 = `i'
        local pt2 = `j'
    
        sum std_comp_score_bl if grade==1, detail
        local l1 = `r(p`pt1')'
        sum std_comp_score_bl if grade==2, detail
        local l2 = `r(p`pt2')'
    
        gen d0 = abs(std_comp_score_bl - `l1'*(level_c==-1) - `l2'*(level_c==1))
        gen d1 = abs(std_comp_score_bl - `l1'*(level_t==-1) - `l2'*(level_t==1))
        gen Ed = P_t*d1 + (1-P_t)*d0
        gen d = d1*treat + d0*(1-treat)
        di "`i' || `j'"

        reghdfe std_comp_score_el Ed d std_comp_score_bl i.grade, a(constituency) vce(clus academycode)
        
        mat res[`r',1] = `i'
        mat res[`r',2] = `j'
        mat res[`r',3] = _b[d] 
        mat res[`r',4] = _se[d]
    }
}

svmat res

/*
tostring res3, format(%6.3f) replace force

tostring res4, format(%6.3f) replace force 
 
gen res5 = res3 + " (" + res4 + ")"


keep res?
keep if !mi(res1)

drop res3 res4
reshape wide res5, i(res1) j(res2)
*/


levelsof res1, loc(lowergr)

foreach l in `lowergr' {
    levelsof res2 if res1 == `l', loc(uppergr)

    sum res3 if res1 == `l' & res2 == `u', meanonly
    loc est `r(mean)'

    foreach u in `uppergr' {
         
        local t=abs(_b[`i']/_se[`i'])
        local star ""  

        if `t'>=2.33 {

        local star="***"
        }
                
        else if `t'>=1.96{
            local star="**"
        }
                
        else if `t'>=1.64{
            local star="*"
        }
        
        else {
            local star=""
        }
                    
    }

}






local size "scriptsize"
    
    
file open let using "${outdir}/dst_qtiles_K.tex", write replace   
    file write let "\begin{center} " _n
    file write let "\caption{\small Effect of distance from different quantiles of baseline test scores on endline test scores} " _n
    file write let "\label{tab:dist_qt_K} " _n
    file write let "\begin{`size'}" _n
    file write let "\begin{threeparttable}" _n
    file write let "\begin{tabular} {@{} l c c c c c@{}} \toprule \toprule" _n
    *file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9}" _n
    *file write let "`S'  \\" _n
    *file write let "`C' \\ \midrule " _n


    file write let "\\" _n

    file write "10 & 25 & 50 & 75 & 90"


        forval g = 0/2 {
            local glab : variable label g`g'
            file write let "&`glab' &`w`g'' \\" _n
            file write let "&        &`s`g'' \\" _n

        }


    file write let "\midrule" _n

    file write let "\bottomrule" _n

    file write let "\end{tabular}" _n
    file write let "\begin{tablenotes}" _n
    file write let "\item Notes: All specifications control for baseline score, grade dummies (where applicable) and randomization strata fixed effects. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
    file write let "\end{tablenotes}" _n
    file write let "\end{threeparttable}" _n
    file write let "\end{`size'}" _n
    file write let "\end{center}" _n

    file write let "\clearpage" _n

file close let








e


use "${datadir}/Liberia/6_L_AG_full_wide_prepared.dta", clear 

keep if finsamp

cap drop d0 d1

/*
gen prebl = .
levels academycode
// create prebl
foreach x in `r(levels)' {
    xi : reg std_comp_score_el i.grade*std_comp_score_bl if academycode!=`x'
    predict temppred
    replace prebl = temppred if academycode==`x'
    drop temppred
}
*/



mat res = J(100,4,.)
local r 0 
foreach i in 10 25  50  75  90  {
    foreach j in 10  25 50 75  90  {  
        local ++r
        cap drop d0 d1 Ed d 
        local pt1 = `i'
        local pt2 = `j'
    
        sum std_score_bl if gg2==0, detail
        local l1 = `r(p`pt1')'
        sum std_score_bl if gg2==1, detail
        local l2 = `r(p`pt2')'
    
        gen d0 = abs(std_score_bl - `l1'*(level_c==-1) - `l2'*(level_c==1))
        gen d1 = abs(std_score_bl - `l1'*(level_t==-1) - `l2'*(level_t==1))
        gen Ed = P_t*d1 + (1-P_t)*d0
        gen d = d1*treat + d0*(1-treat)
        di "`i' || `j'"

        reghdfe std_score_el Ed d std_score_bl i.grade, a(strata) vce(clus ggroup)
        
        mat res[`r',1] = `i'
        mat res[`r',2] = `j'
        mat res[`r',3] = _b[d] 
        mat res[`r',4] = _se[d]
    }
}

svmat res

tostring res3, format(%6.3f) replace force

tostring res4, format(%6.3f) replace force 
 
gen res5 = res3 + " (" + res4 + ")"


keep res?
keep if !mi(res1)


drop res3 res4
reshape wide res5, i(res1) j(res2)




local c = -2
forval g = 1/2{
        local c1 = `c'+3
        local c2 = `c'+4
        local c3 = `c'+5
        local glab "Experiment `g' (``g'')"
        local H "`H'&&\multicolumn{3}{c}{`glab'}"
        local S "`S'&&\Longstack{Control\#mean}&\Longstack{Coef.}&\Longstack{N}"
        local C "`C'&&(`c1')&(`c2')&(`c3')"
        local c = `c'+3
}




local size "scriptsize"
    
    
file open let using "${outdir}/dst_qtiles_K.tex", write replace   
    file write let "\begin{center} " _n
    file write let "\caption{\small Distance from different quantiles of baseline test scores} " _n
    file write let "\label{tab:dist_qt_K} " _n
    file write let "\begin{`size'}" _n
    file write let "\begin{threeparttable}" _n
    file write let "\begin{tabular} {@{} l c c c c c@{}} \toprule \toprule" _n
    *file write let "`H' \\  \cmidrule{3-5} \cmidrule{7-9}" _n
    *file write let "`S'  \\" _n
    *file write let "`C' \\ \midrule " _n


    file write let "\\" _n

    file write "10 & 25 & 50 & 75 & 90"


        forval g = 0/2 {
            local glab : variable label g`g'
            file write let "&`glab' &`w`g'' \\" _n
            file write let "&        &`s`g'' \\" _n

        }


    file write let "\midrule" _n

    file write let "\bottomrule" _n

    file write let "\end{tabular}" _n
    file write let "\begin{tablenotes}" _n
    file write let "\item Notes: All specifications control for baseline score, grade dummies (where applicable) and randomization strata fixed effects. Standard errors are clustered at the academy-grade group level. ***, **, and * indicate significance at 1\%, 5\%, and 10\%. " 
    file write let "\end{tablenotes}" _n
    file write let "\end{threeparttable}" _n
    file write let "\end{`size'}" _n
    file write let "\end{center}" _n

    file write let "\clearpage" _n

file close let









