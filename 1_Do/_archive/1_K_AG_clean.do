
/*==========================================================================

Title: 1_K_AG_clean.do 
Author: Mridul Joshi
Date: Sat Jul 17 15:49:25 2021

Description: Examine the raw data and convert into dta files for Kenya and 
		   Liberia Bridge ability-grouping analysis

===========================================================================*/


* ===================================================================== *
* -----------------     	  Baseline data           ----------------- *
* ===================================================================== *


*** grade 1 ***


* language 
import delimited using "${rawdir}/Kenya/Grade 1 Reading Club/KE_G1_T2_English Language_Midterm_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid


ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}

tempfile ble
save `ble'


* literacy
import delimited using "${rawdir}/Kenya/Grade 1 Reading Club/KE_G1_T2_Literacy_Midterm_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid

merge 1:1 academycode studyid using `ble', gen(_mble)


/**
    Result                           # of obs.
    -----------------------------------------
    not matched                             0
    matched                             5,498  (_mble==3)
    -----------------------------------------
*/


tempfile g1bl
save `g1bl'



*** grade 2 ***

*language
import delimited using "${rawdir}/Kenya/Grade 2 Reading Club/KE_G2_T2_English Language_Midterm_Blinded.csv", clear

format studyid %12.0f 

codebook academycode studyid

duplicates report studyid


ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}

tempfile ble
save `ble'

* literacy
import delimited using "${rawdir}/Kenya/Grade 2 Reading Club/KE_G2_T2_Literacy_Midterm_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid

merge 1:1 academycode studyid using `ble', gen(_mble2)

/*

    Result                           # of obs.
    -----------------------------------------
    not matched                             0
    matched                             5,151  (_mble2==3)
    -----------------------------------------

*/


append using `g1bl'


rename score bl_read_score
rename score_e bl_lang_score

gen bl_test_version = "A"
replace bl_test_version = "B" if regexm(title, "B")


rename assessmentstatus bl_assessmentstatus_read
rename assessmentstatus_e bl_assessmentstatus_lang

rename assessmentid bl_assessmentid_lang


gen grade = 1
replace grade = 2 if regexm(gradename, "2")


rename assessmentdate bl_assessmentdate 


gen bl_maxscore_read = maxscore

gen bl_maxscore_lang = maxscore


* convert to stata dates 
gen ac_date = academy_cohort
drop academy_cohort
gen academy_cohort = date(ac_date, "DM20Y")
format academy_cohort %td
lab var academy_cohort "Academy cohort"

gen enr_date = enrolled_date
drop enrolled_date
gen enrolled_date = date(enr_date, "DM20Y")
format enrolled_date %td 
lab var enrolled_date "Date of enrollment"

* treatment 
gen treat = treatmentassignment == "Treatment"

gen locationtype = .
replace locationtype = 0 if demographiclocation == "Rural"
replace locationtype = 1 if demographiclocation == "Peri-Urban"
replace locationtype = 2 if demographiclocation == "Urban"

lab def urban 0 "Rural" 1 "Peri-urban" 2 "Urban"
lab val locationtype urban

lab var locationtype "Urbanness"

* stream
gen stream1 = stream
drop stream 
gen stream = .
replace stream = 1 if stream1 == "A"
replace stream = 2 if stream1 == "B"

lab def stream  1 "A" 2 "B"
lab val stream stream

lab var stream "Stream"


*** other labels ***
lab var grade "Grade"
lab var treat "Treatment assignment"


keep constituency1 county locationtype academy_cohort term_period academycode treat ///
	 studyid religiouseducationsubject enrolled_date grade stream bl_assessmentstatus_* bl_assessmentid_lang bl_read_score ///
	 bl_lang_score bl_test_version bl_assessmentdate bl_maxscore_*



tempfile baseline
save `baseline'
 


* ===================================================================== *
* -----------------     	  Endline data           ----------------- *
* ===================================================================== *


*** grade 1 ***

* language
import delimited using "${rawdir}/Kenya/Grade 1 Reading Club/KE_G1_T3_English Language_Endterm_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid


ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}

tempfile ble
save `ble'


* literacy
import delimited using "${rawdir}/Kenya/Grade 1 Reading Club/KE_G1_T3_Literacy_Endterm_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid

merge 1:1 academycode studyid using `ble', gen(_mble)


/*

    Result                           # of obs.
    -----------------------------------------
    not matched                             0
    matched                             4,935  (_mble==3)
    -----------------------------------------

*/


tempfile g1bl
save `g1bl'



*** grade 2 ***

* language
import delimited using "${rawdir}/Kenya/Grade 2 Reading Club/KE_G2_T3_English Language_Endterm_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid


ds academycode studyid, not
foreach v in `r(varlist)' {
	rename `v' `v'_e
}

tempfile ble
save `ble'


* literacy
import delimited using "${rawdir}/Kenya/Grade 2 Reading Club/KE_G2_T3_Literacy_Endterm_Blinded.csv", clear


format studyid %12.0f 

codebook academycode studyid

duplicates report studyid

merge 1:1 academycode studyid using `ble', gen(_mble2)

/*

    Result                           # of obs.
    -----------------------------------------
    not matched                             0
    matched                             4,731  (_mble2==3)
    -----------------------------------------
*/

append using `g1bl'


rename score el_read_score
rename score_e el_lang_score

gen el_test_version = "A"
replace el_test_version = "B" if regexm(title, "B")


rename assessmentstatus el_assessmentstatus_read
rename assessmentstatus_e el_assessmentstatus_lang

rename assessmentid el_assessmentid_lang


gen grade = 1
replace grade = 2 if regexm(gradename, "2")

rename assessmentdate el_assessmentdate 


gen el_maxscore_read = maxscore

gen el_maxscore_lang = maxscore



* convert to stata dates 
gen ac_date = academy_cohort
drop academy_cohort
gen academy_cohort = date(ac_date, "DM20Y")
format academy_cohort %td
lab var academy_cohort "Academy cohort"

gen enr_date = enrolled_date
drop enrolled_date
gen enrolled_date = date(enr_date, "DM20Y")
format enrolled_date %td 
lab var enrolled_date "Date of enrollment"

* treatment 
gen treat = treatmentassignment == "Treatment"

gen locationtype = .
replace locationtype = 0 if demographiclocation == "Rural"
replace locationtype = 1 if demographiclocation == "Peri-Urban"
replace locationtype = 2 if demographiclocation == "Urban"

lab def urban 0 "Rural" 1 "Peri-urban" 2 "Urban"
lab val locationtype urban

lab var locationtype "Urbanness"

* stream
gen stream1 = stream
drop stream
gen stream = .
replace stream = 1 if stream1 == "A"
replace stream = 2 if stream1 == "B"

lab def stream  1 "A" 2 "B"
lab val stream stream

lab var stream "Stream"


*** other labels ***
lab var grade "Grade"
lab var treat "Treatment assignment"


keep constituency1 county locationtype academy_cohort term_period academycode treat enrolled_date grade stream ///
	academycode studyid el_assessmentstatus_* el_assessmentid_lang el_read_score ///
	el_lang_score el_test_version el_assessmentdate el_maxscore_*


* ===================================================================== *
* -----------------     	 Merge bl and el data     ----------------- *
* ===================================================================== *


merge 1:1 academycode studyid using `baseline', gen(_mbl)   

/*
    Result                           # of obs.
    -----------------------------------------
    not matched                         2,661
        from master                       839  (_mbl==1)
        from using                      1,822  (_mbl==2)

    matched                             8,827  (_mbl==3)
    -----------------------------------------
*/


* create a variable to indicate whether pupil observed in BL, ML and EL
gen pupil_observed = .
replace pupil_observed= 1 if _mbl ==1
replace pupil_observed= 2 if _mbl ==2
replace pupil_observed= 3 if _mbl ==3

lab define pupil_observed 1 "Only EL" 2 "Only BL" 3 "BL & EL" 
lab val pupil_observed pupil_observed


* label variables 

lab var el_maxscore_read "Maximum achievable endline reading score"
lab var el_maxscore_lang "Maximum achievable endline language score"
lab var bl_maxscore_read "Maximum achievable baseline reading score"
lab var bl_maxscore_lang "Maximum achievable baseline language score"

lab var pupil_observed "Indicator: whether pupil observed in BL, EL, or both"


tempfile full
save `full'



* ===================================================================== *
* -----------------    Student-level parent ds        ----------------- *
* ===================================================================== *


use `full', clear 

preserve

collapse (lastnm) constituency1, by(county)

gen constituency = trim(constituency1)
replace constituency = "North Eastern" if county == "Garissa"
replace constituency = "Eastern" if county == "Tharaka Nithi"
replace constituency = "Rift Valley" if county == "Elgeyo Marakwet"

lab var constituency "Constituency"

keep county constituency

tempfile cons
save `cons'

restore

merge m:1 county using `cons', gen(_mcons)

replace county = trim(county)

keep academycode studyid constituency county locationtype academy_cohort ///
     enrolled_date grade stream pupil_observed treat  

order academycode studyid county constituency locationtype academy_cohort ///
     enrolled_date grade stream pupil_observed treat , first

save "${datadir}/Kenya/0_K_AG_parent.dta", replace



* ===================================================================== *
* -----------------     	    BL score lang         ----------------- *
* ===================================================================== *


u `full', clear 

gen assess_date_bl = date(bl_assessmentdate, "DM20Y")
format assess_date_bl %td
lab var assess_date_bl "Baseline assessment date"

gen version_bl = bl_test_version
lab var version_bl "Baseline test version"


gen score_bl_lang = real(bl_lang_score)   // bl_lang_score also takes the values "NA" and "-1"
lab var score_bl_lang "Baseline score (language)"


replace score_bl_lang = . if score_bl_lang == -1  

gen maxscore_bl_lang = bl_maxscore_lang
lab var maxscore_bl_lang "Maximum achievable baseline score (language)"

encode bl_assessmentstatus_lang, gen(assess_status_bl_lang)
lab var assess_status_bl_lang "Baseline assessment status (language)"


keep academycode studyid assess_date_bl assess_status_bl_lang score_bl_lang maxscore_bl_lang
order academycode studyid assess_date_bl assess_status_bl_lang score_bl_lang maxscore_bl_lang


save "${datadir}/Kenya/1_K_AG_bl_lang.dta", replace




* ===================================================================== *
* -----------------     	 BL score reading         ----------------- *
* ===================================================================== *


u `full', clear 

gen assess_date_bl = date(bl_assessmentdate, "DM20Y")
format assess_date_bl %td
lab var assess_date_bl "Baseline assessment date"


gen version_bl = bl_test_version
lab var version_bl "Baseline test version"

gen score_bl_read = real(bl_read_score)
lab var score_bl_read "Baseline score (reading)"


replace score_bl_read = . if score_bl_read == -1  

gen maxscore_bl_read = bl_maxscore_read
lab var maxscore_bl_read "Maximum achievable baseline score (reading)"

encode bl_assessmentstatus_read, gen(assess_status_bl_read)
lab var assess_status_bl_read "Baseline assessment status (reading)"


keep academycode studyid assess_date_bl assess_status_bl_read score_bl_read maxscore_bl_read
order academycode studyid assess_date_bl assess_status_bl_read score_bl_read maxscore_bl_read


save "${datadir}/Kenya/2_K_AG_bl_read.dta", replace



* ===================================================================== *
* -----------------     	    EL score lang         ----------------- *
* ===================================================================== *


u `full', clear 

gen assess_date_el = date(el_assessmentdate, "DM20Y")
format assess_date_el %td
lab var assess_date_el "Endline assessment date"

gen version_el = el_test_version
lab var version_el "Endline test version"

gen score_el_lang = real(el_lang_score)
lab var score_el_lang "Endline score (language)"


replace score_el_lang = . if score_el_lang == -1  

gen maxscore_el_lang = el_maxscore_lang
lab var maxscore_el_lang "Maximum achievable endline score (language)"

encode el_assessmentstatus_lang, gen(assess_status_el_lang)
lab var assess_status_el_lang "Endline assessment status (language)"


keep academycode studyid assess_date_el assess_status_el_lang score_el_lang maxscore_el_lang
order academycode studyid assess_date_el assess_status_el_lang score_el_lang maxscore_el_lang



save "${datadir}/Kenya/3_K_AG_el_lang.dta", replace



* ===================================================================== *
* -----------------         EL score reading          ----------------- *
* ===================================================================== *


u `full', clear 

gen assess_date_el = date(el_assessmentdate, "DM20Y")
format assess_date_el %td
lab var assess_date_el "Endline assessment date"

gen version_el = el_test_version
lab var version_el "Endline test version"

gen score_el_read = real(el_read_score)
lab var score_el_read "Endline score (reading)"


replace score_el_read = . if score_el_read == -1 

gen maxscore_el_read = el_maxscore_read
lab var maxscore_el_read "Maximum achievable endline score (reading)"

encode el_assessmentstatus_read, gen(assess_status_el_read)
lab var assess_status_el_read "Endlne assessment status (reading)"



keep academycode studyid assess_date_el assess_status_el_read score_el_read maxscore_el_read
order academycode studyid assess_date_el assess_status_el_read score_el_read maxscore_el_read


save "${datadir}/Kenya/4_K_AG_el_read.dta", replace







