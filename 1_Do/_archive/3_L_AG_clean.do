

/*==========================================================================

Title: 1_tarl_clean.do 
Author: Mridul Joshi
Date: Fri May  7 15:37:59 2021

Description: Examine the raw data and convert into dta files for for Bridge 
             ability-grouping analysis

 
===========================================================================*/



/**********************************************************************/
/*  SECTION 1: Baseline data  

    Notes: 1. 51 missing grade names - see if can be recovered from any other dataset
    	   2. 1 duplicate studyid
**********************************************************************/

import delimited using "${rawdir}/Liberia/LR_G1234_S1_BaselineData_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid

tab1 gradename baselinescore treatmentassignment_g12 treatmentassignment_g34, mi


*** rename all variables to indicate the datasource
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_bl
}

tempfile bl
save `bl'



/**********************************************************************/
/*  SECTION 2: Midline data  	

    Notes: 1. Constituency has 4,324 missing values
    	   2. Demographic location is always rural
    	   3. 2 duplicates of study id - check if unique within each academy
    	   4. religiouseducationsubject has no observations
    	   5. title and subjectgrouptitle is the same variable 
    	   6. 1,785 observations have a midline score of -1 and the corresponding pc score is negative
    	   7. assessmenttype is always End-Term
    	   8. assessmentdate is always 05-Feb-19 */
/**********************************************************************/

import delimited using "${rawdir}/Liberia/LR_G1234_S1_ETE_Blinded.csv", clear


tab1 constituency1 county demographiclocation academy_cohort term_period , mi

codebook academycode studyid assessmentid enrolled_date

duplicates report studyid

tab1 religiouseducationsubject gradename stream assessmentstatus ///
	 title subjectgrouptitle midlinemaxscore assessmenttype assessmentdate

summ midlinescore midlinepercscore


*** rename all variables to indicate the datasource
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_ml
}

tempfile ml
save `ml'



/**********************************************************************/
/*  SECTION 3: Endline data			
    Notes: 1. Constituency has 4,175 missing values
    	   2. Demographic location is always rural
    	   3. 2 duplicates of studyid
    	   4. 1,700 observations have a midline score of -1 and the corresponding pc score is negative
    	   5. assessmenttype is always End-Term
    	   6. assessmentdate is always 08-Jul-19.  */
/**********************************************************************/

import delimited using "${rawdir}/Liberia/LR_G1234_S2_EndlineData_Blinded.csv", clear


tab1 constituency1 county demographiclocation academy_cohort term_period, mi

codebook academycode studyid assessmentid  

duplicates report studyid

tab1 religiouseducationsubject gradename stream assessmentstatus ///
	 title subjectgrouptitle endlinemaxscore assessmenttype assessmentdate

summ endlinescore endlinepercscore


preserve 

duplicates drop academycode demographiclocation, force 
rename demographiclocation demographiclocation_final

keep academycode demographiclocation_final

tempfile demloc
save `demloc'

restore


*** rename all variables to indicate the datasource
ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_el
}

tempfile el
save `el'



* ===================================================================== *
* -----------------  Updated academy locations        ----------------- *
* ===================================================================== *

import excel using "${rawdir}/Liberia/updated academy locations.xlsx", clear firstr

gen county_up = County
gen constituency_up = Constituency
gen cohort_up = Cohort

keep county_up constituency_up cohort_up academycode

tempfile updated
save `updated'


/**********************************************************************/
/*  SECTION 7: Merge all student-level datasets  			
    Notes: */
/**********************************************************************/

use `bl', clear 

merge 1:1 academycode studyid using `ml', gen(_mml)
merge 1:1 academycode studyid using `el', gen(_mel)

* create a variable to indicate whether pupil recorded in BL, ML and EL
gen pupil_observed = .
replace pupil_observed= 1 if _mml ==1
replace pupil_observed= 2 if _mml ==2
replace pupil_observed= 3 if _mel ==2
replace pupil_observed= 4 if _mml ==3
replace pupil_observed= 5 if _mel ==3 & _mml ==2
replace pupil_observed= 6 if _mel ==3 & _mml ==1
replace pupil_observed= 7 if _mel ==3 & _mml ==3

lab define pupil_observed 1 "Only BL" 2 "Only ML" 3 "Only EL" 4 "BL & ML" 5 "ML & EL" 6 "BL & EL" 7 "BL & ML & EL"  
lab val pupil_observed pupil_observed


merge m:1 academycode using `updated', gen(_mup)

drop if _mup == 2 // 2 obs

drop _mup 

* constituency
gen constituency = constituency_up

* county
gen county = county_up

* rural/urban
merge m:1 academycode using `demloc', gen(_mdem)

encode demographiclocation_final, gen(demographiclocation) 


* create a numeric variable for grade 
gen grade = . 

replace grade = real(substr(gradename_bl,-1,1))
replace grade = real(substr(gradename_ml,-1,1)) if grade == .
replace grade = real(substr(gradename_el,-1,1)) if grade == .

* EL and ML have same grades when non-missing
assert gradename_el == gradename_ml if !mi(gradename_el) & !mi(gradename_ml)

* Create an indicator for different baseline grade 
gen ind_grd_dif_bl = 1 if (gradename_bl != gradename_el) & !mi(gradename_bl) & !mi(gradename_el) & !mi(gradename_ml)

* Create a variable containing the different baseline grade 
gen val_grd_dif_bl = real(substr(gradename_el,-1,1)) if (gradename_bl != gradename_el) & !mi(gradename_bl) & !mi(gradename_el) & !mi(gradename_ml)


* academy cohort 
gen academy_cohort = date(cohort_up, "DM20Y")
format academy_cohort %td 

* stream
gen stream1 = stream_el
replace stream1 = stream_ml if mi(stream1)  // 246 missing values 
encode stream1, gen(stream) 

* Create an indicator for different midline stream
gen ind_str_dif_bl = 1 if (stream_ml != stream_el) & !mi(stream_el) & !mi(stream_ml)

* Create a variable containing the different midline stream (all Bs)
gen val_str_dif_bl = 2 if ind_str_dif_bl == 1
lab val val_str_dif_bl stream 

* enrolled date
gen enrolled_date = date(enrolled_date_el, "DM20Y")
replace enrolled_date = date(enrolled_date_ml, "DM20Y") if mi(enrolled_date)  // 246 missing values 
format enrolled_date %td


* assessment dates 
gen assess_date_ml = date(assessmentdate_ml, "DM20Y")
format assess_date_ml %td
lab var assess_date_ml "Midline assessment date"

gen assess_date_el = date(assessmentdate_el, "DM20Y")
format assess_date_el %td
lab var assess_date_el "Endline assessment date"

* treatment assignment

ds treat* 

foreach v in `r(varlist)'{
    replace `v' = "" if `v' == "na"
    destring `v', replace
}


egen tr12 = rowmin(treatmentassignment_g12_el treatmentassignment_g12_ml treatmentassignment_g12_bl)
egen tr34 = rowmin(treatmentassignment_g34_el treatmentassignment_g34_ml treatmentassignment_g34_bl)


gen treat = tr12 if inlist(grade,1,2)
replace treat = tr34 if inlist(grade,3,4)
 
* label all final variables 
lab var academycode "Academy code"
lab var studyid "Student ID"
lab var constituency "Constituency"
lab var county "County"
lab var demographiclocation "Rural/urban"
lab var academy_cohort "Academy cohort"
lab var enrolled_date "Date of enrollment"
lab var grade "Grade"
lab var ind_grd_dif_bl "Indicator: takes 1 if grade at BL is different from ML and EL"
lab var val_grd_dif_bl "Grade at baseline if different from ML and EL"
lab var stream "Stream"
lab var ind_str_dif_bl "Indicator: takes 1 if stream at ML is different from EL"
lab var val_str_dif_bl "Stream at ML if different from EL"
lab var pupil_observed "Indicator: whether pupil observed in BL, ML and EL"
lab var treat "Treatment"

tempfile full
save `full'

/*----------------------------------------------------*/
   /* [>   1. Student-level parent ds   <] */ 
/*----------------------------------------------------*/

u `full', clear 

keep academycode studyid constituency county demographiclocation academy_cohort ///
     enrolled_date grade ind_grd_dif_bl val_grd_dif_bl stream ind_str_dif_bl ///
     val_str_dif_bl pupil_observed treat  


order academycode studyid county constituency demographiclocation academy_cohort ///
	  enrolled_date grade ind_grd_dif_bl val_grd_dif_bl stream ind_str_dif_bl  ///
	  val_str_dif_bl pupil_observed treat , first

save "${datadir}/Liberia/0_L_AG_parent.dta", replace


/*----------------------------------------------------*/
   /* [>   2.  BL scores   <] */ 
/*----------------------------------------------------*/

u `full', clear 

gen score_bl = baselinescore_bl
lab var score_bl "Baseline score"

gen maxscore_bl = 40  // need to check this
lab var maxscore_bl "Maximum achievable baseline score"

keep academycode studyid score_bl maxscore_bl
order academycode studyid score_bl maxscore_bl

save "${datadir}/Liberia/1_L_AG_bl.dta", replace


 
/*----------------------------------------------------*/
   /* [>   3.  ML scores   <] */ 
/*----------------------------------------------------*/

u `full', clear 

encode title_ml, gen(subj_ml)
lab var title_ml "Midline asssessment subject title"

gen score_ml = midlinescore_ml
lab var score_ml "Midline score"

replace score_ml = . if score_ml == -1  // absent has been graded as -1 

gen maxscore_ml = midlinemaxscore_ml
lab var maxscore_ml "Maximum achievable midline score"

encode assessmentstatus_ml, gen(assess_status_ml)
lab var assess_status_ml "Midline assessment status"

gen assess_id_ml = assessmentid_ml
lab var assess_id_ml "Midline assessment ID"


keep academycode studyid assess_date_ml assess_id_ml assess_status_ml title_ml score_ml maxscore_ml
order academycode studyid assess_date_ml assess_id_ml assess_status_ml title_ml score_ml maxscore_ml

save "${datadir}/Liberia/2_L_AG_ml.dta", replace


 
/*----------------------------------------------------*/
   /* [>   4.  EL scores   <] */ 
/*----------------------------------------------------*/

u `full', clear 

replace title_el = subjectgrouptitle_el if mi(title_el)
encode title_el, gen(subj_el)
lab var title_el "Endline asssessment subject title"

gen score_el = endlinescore_el
lab var score_el "Endline score"

replace score_el = . if score_el == -1  // absent has been graded as -1 

gen maxscore_el = endlinemaxscore_el
lab var maxscore_el "Maximum achievable endline score"

encode assessmentstatus_el, gen(assess_status_el)
lab var assess_status_el "Endline assessment status"

gen assess_id_el = assessmentid_el
lab var assess_id_el "Endline assessment ID"


keep academycode studyid assess_date_el assess_id_el assess_status_el title_el score_el maxscore_el
order academycode studyid assess_date_el assess_id_el assess_status_el title_el score_el maxscore_el

save "${datadir}/Liberia/3_L_AG_el.dta", replace




/**********************************************************************/
/*  SECTION 8: Merge academy-grade level datasets  			
    Notes: */
/**********************************************************************/

*** Pupil attendance 
import delimited using "${rawdir}/Liberia/LR_G1234_2019_PupilAttendance_Blinded.csv", clear 

lab var attendancetaken "Fraction attendance taken"
lab var pupilattendance "Fraction pupil attendance"
lab var boyattendance "Fraction boys' attendance"
lab var girlattendance "Fraction girls' attendance"
lab var unknownattendance "Fraction unknown's attendance"


* create a numeric variable for grade 
gen grade = real(substr(gradename,-1,1))

keep academycode grade attendancetaken pupilattendance  boyattendance girlattendance unknownattendance 

tempfile attn
save `attn'

*** Lesson completion
import delimited using "${rawdir}/Liberia/LR_G1234_2019_LessonCompletion_Blinded.csv", clear 
 
gen lp_opened = percentage_opened 
lab var lp_opened "Fraction opened lesson plans"

gen lp_comp = percentage_completed
lab var lp_comp "Fraction completed lesson plans"

* create a numeric variable for grade 
gen grade = real(substr(gradename,-1,1))

keep academycode grade lp_opened lp_comp

tempfile lp
save `lp'


*** Teacher attendance
import delimited using "${rawdir}/Liberia/LR_G1_2019_TeacherAttendance_Blinded.csv", clear 

gen tch_attn = teacherattendance
lab var tch_attn "Teacher attendance"   // what does 0 mean - absent or missing?

gen all_tch_attn = allteacherattendance
lab var all_tch_attn "All teacher attendance"  // what is this variable? 

* create a numeric variable for grade 
gen grade = real(substr(gradename,-1,1))

keep academycode grade tch_attn all_tch_attn

tempfile tch_attn
save `tch_attn'


*** Academy manager attendance (academy level)
import delimited using "${rawdir}/Liberia/LR_2019_AcademyManagerAttendance_Blinded.csv", clear 

gen acd_mang_attn = academymanagerattendance 
lab var acd_mang_attn "Academy manager attendance (academy level)"

keep academycode acd_mang_attn 

tempfile acd
save `acd'


*** merge datasets 

u `attn', clear

merge 1:1 academycode grade using `lp', gen(_mlp) 
merge 1:1 academycode grade using `tch_attn', gen(_mtch)

merge m:1 academycode using `acd', gen(_macd)


lab var grade "Grade"

keep academycode grade attendancetaken pupilattendance  boyattendance girlattendance ///
     unknownattendance lp_opened lp_comp tch_attn all_tch_attn tch_attn all_tch_attn ///
     acd_mang_attn

order academycode grade attendancetaken pupilattendance  boyattendance girlattendance ///
	  unknownattendance lp_opened lp_comp tch_attn all_tch_attn tch_attn all_tch_attn ///
	  acd_mang_attn


save "${datadir}/Liberia/4_L_AG_covars.dta", replace









