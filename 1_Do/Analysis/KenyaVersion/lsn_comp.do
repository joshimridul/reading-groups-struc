
/*==========================================================================

Title: lsn_comp.do 
Author: Mridul Joshi
Date: 

Description: 

Key input: 
Key output: 

Last edited by:  

===========================================================================*/


use "${datadir}/Kenya/6_K_AG_full_wide_prepared_2.dta", clear 

keep P_t academycode class_ptr grade 

duplicates drop 

tempfile pt
save `pt'


import delimited "/Users/mriduljoshi/Library/CloudStorage/Dropbox/Bridge TARL/AbilityGrouping/2_Data/1_Raw/Kenya/Grade 2 Reading Club/KE_G2_TeacherAttendance_Blinded.csv", clear

tempfile tatt2
save `tatt2'
 

import delimited "/Users/mriduljoshi/Library/CloudStorage/Dropbox/Bridge TARL/AbilityGrouping/2_Data/1_Raw/Kenya/Grade 1 Reading Club/KE_G1_TeacherAttendance_Blinded.csv", clear

append using `tatt2'


gen grade = 1 if !mi(grade1 )
replace grade = 2 if !mi(grade2)

gen teach_attn = grade1
replace teach_attn = grade2 if mi(teach_attn)

keep academycode teach_attn grade

tempfile t_attn
save `t_attn'
 


import delimited using "/Users/mriduljoshi/Library/CloudStorage/Dropbox/Bridge TARL/AbilityGrouping/2_Data/1_Raw/Kenya/Grade 1 Reading Club/KE_G1_T3_LessonCompletion_Blinded.csv", clear

reshape long completed gradename opened percentage_completed percentage_opened scheduled  subject, i(academycode) j(new) str

tempfile compg1
save `compg1'


import delimited using "/Users/mriduljoshi/Library/CloudStorage/Dropbox/Bridge TARL/AbilityGrouping/2_Data/1_Raw/Kenya/Grade 2 Reading Club/KE_G2_T3_LessonCompletion_Blinded.csv", clear 


reshape long completed gradename opened percentage_completed percentage_opened scheduled  subject, i(academycode) j(new) str

append using `compg1'


gen grade = 1 if regexm(gradename, "1")
replace grade = 2 if regexm(gradename, "2")

drop gradename

gen treat = treatmentassignment == "Treatment"


merge m:1 academycode grade using `t_attn', gen(_mattn)

drop if _mattn == 2


merge m:1 academycode grade using `pt', gen(_macad)


* ===================================================================== *
* -----------------        	  Regressions             ----------------- *
* ===================================================================== *

lab var treat "Treat"
lab var percentage_completed "Lesson completion rate"
lab var teach_attn "Teacher attendance"
lab var class_ptr "Class size"

eststo clear
		
eststo r1: reg percentage_completed treat P_t, robust

eststo r2: reg percentage_completed treat teach_attn P_t, robust

eststo r3: reg percentage_completed treat class_ptr P_t, robust

eststo r4: reg percentage_completed treat class_ptr teach_attn P_t, robust



#delimit ;

loc tablerow treat teach_attn class_ptr;

	esttab r* using "${outdir}/Kenya_new/lsn_comp.tex",
		b(3) se booktabs star(* .1 ** .05 *** .01) brackets replace label gaps nonotes nomtitles
	prehead("{\def\sym#1{\ifmmode^{#1}\else\(^{#1}\)\fi}
		\begin{tabular}{@{\hskip\tabcolsep\extracolsep\fill}l*{4}{>{\centering\arraybackslash}m{3.0cm}}}
		\toprule \toprule \\
		& \multicolumn{4}{c}{Lesson completion rate}\\ \\")
		keep(`tablerow') order(`tablerow')	
	stats(N , labels("Observations" ) 
	fmt(2 2 %20s %20s)) title("ddddd") 
	addnotes( 
    "Notes: Robust standard errors are reported in brackets. ***, **, and * indicate significance at 1\%, 5\%, and 10\%." ) ;


#delimit cr






















