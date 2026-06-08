

* ===================================================================== *
* -----------------     	  Liberia                 ----------------- *
* ===================================================================== *	


use "${datadir}/Liberia/5_L_AG_full_wide.dta", clear 

*keep if inlist(data_avl, 1,6,7)

gen g1 = grade == 1 
gen g2 = grade == 2
gen g3 = grade == 3
gen g4 = grade == 4 
gen g0 = inlist(grade,1,2,3,4)

lab var g0 "Full sample"
lab var g1 "Grade 1"
lab var g2 "Grade 2"
lab var g3 "Grade 3"
lab var g4 "Grade 4"

gen acad_year = 1 if academy_cohort < td(22nov2016)
replace acad_year = 2 if academy_cohort > td(22nov2016)

gen g12 = inlist(grade, 1, 2)
lab var g12 "Grades 1 and 2"
egen ggroup = group(g12 academycode)

gen std_grp = 1
replace std_grp = 2 if studygroup12 == 1 & studygroup34 == .
replace std_grp = 3 if studygroup12 == . & studygroup34 == 0
replace std_grp = 4 if studygroup12 == . & studygroup34 == 1

lab def std_grp 1 "yellow" 2 "orange" 3 "blue" 4 "purple"

lab val std_grp std_grp



preserve 

collapse treat, by(academycode acad_year g12)

bys acad_year g12: egen P_t = mean(treat)
gen P_c = 1- P_t

keep g12 academycode P_t P_c

tempfile prop
save `prop'

restore

merge m:1 g12 academycode using `prop', gen(_mprop)   // contains the probability of treatment for each observation


*** calculate expected grade level

gen level_c  = grade 
gen level_t = grade

replace level_t = (grade + 1) if inlist(grade,1,3) & inlist(std_grp,2,4)
replace level_t = (grade - 1) if inlist(grade,2,4) & inlist(std_grp,1,3)

gen exp_level = (P_t*level_t) + (P_c*level_c)

gen realised_level = level_t
replace realised_level = level_c if treat == 0

lab var exp_level "E[Level]"
lab var realised_level "Level"


*** calculate expected class size 

bys academycode std_grp stream: egen N_t = count(studyid) if inlist(data_avl, 1,4,6,7)
bys academycode grade stream: egen N_c = count(studyid) if inlist(data_avl, 1,4,6,7)

bys academycode std_grp stream: egen N_t1 = count(studyid) 
bys academycode grade stream: egen N_c1 = count(studyid) 


bys academycode std_grp stream: egen N_t_x = max(N_t)
bys academycode grade stream: egen N_c_x = max(N_c) 


*gen classsize = N_t_x
*replace classsize = N_c_x if treat == 0
*lab var classsize "Class size (\times 10)"



gen exp_classsize = (P_t*N_t) + (P_c*N_c)
lab var exp_classsize "E[Class size]"

gen classsize = N_t 
replace classsize = N_c if treat == 0
lab var classsize "Class size (\times 10)"

gen classsize1 = N_t1 
replace classsize1 = N_c1 if treat == 0
lab var classsize1 "Class size (\times 10)"


collapse (mean) classsize classsize1, by(academycode grade stream std_grp treat academy_cohort ggroup)


keep if inlist(grade,3,4)
drop if treat ==.

gen class_grp = 1  if treat == 1 & std_grp == 3 
replace class_grp = 2 if treat == 1 & std_grp ==4 
replace class_grp = 3 if treat == 0 & grade ==3
replace class_grp = 4 if treat == 0 & grade ==4

egen class_grp_stream = group(class_grp stream)



sort academycode class_grp



collapse (max) classsize classsize1, by(class_grp_stream academycode ggroup)


gen obs = _n 


graph dot (asis) classsize1 classsize, over(obs, sort(1) descending) vertical linetype(line) lines(lcolor(gs12) lw(vthin)) yla(, ang(v))




*restore








