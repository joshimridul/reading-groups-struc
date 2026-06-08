

*use "${datadir}/Kenya/6_K_AG_full_wide_prepared", clear 


use "${datadir}/Liberia/6_L_AG_full_wide_prepared", clear 

keep if finsamp

keep if g12 == 1

*drop if std_comp_score_bl < -3

*keep if class_ptr > 9

*bys academycode purple: egen xtotal_t_bl = total(comp_score_bl)
*bys academycode purple: egen xcount_t_bl = count(comp_score_bl)


bys academycode studygroup12: egen xtotal_t_bl = total(score_bl)
bys academycode studygroup12: egen xcount_t_bl = count(score_bl)

gen xmeanpeerscore_t_bl = (xtotal_t_bl - score_bl)/(xcount_t_bl - 1)

*bys academycode grade: egen xtotal_c_bl = total(com_score_bl)
*bys academycode grade: egen xcount_c_bl = count(comp_score_bl)

*gen xmeanpeerscore_t_bl = (xtotal_t_bl - comp_score_bl)/(xcount_t_bl - 1)

bys academycode grade: egen xtotal_c_bl = total(score_bl)
bys academycode grade: egen xcount_c_bl = count(score_bl)

gen xmeanpeerscore_c_bl = (xtotal_c_bl - score_bl)/(xcount_c_bl - 1)

gen xexp_meanpeerscore_bl = (P_t*xmeanpeerscore_t_bl) + (P_c*xmeanpeerscore_c_bl)
lab var xexp_meanpeerscore_bl "E[Peer baseline score]"

gen xmeanpeerscore_bl = xmeanpeerscore_t_bl
replace xmeanpeerscore_bl = xmeanpeerscore_c_bl if treat == 0
lab var xmeanpeerscore_bl "Peer baseline score"


xtile bl20 = std_score_bl  , nq(15)

*xtile bl20 = score_bl  , nq(20)


reg meanpeerscore_bl i.academycode

predict predpeers, xb

gen meanpeers_acad = meanpeerscore_bl - predpeers 

lab var xmeanpeerscore_bl "Mean peer score"


collapse xmeanpeerscore_bl meanpeerscore_bl meanpeers_acad , by(bl20 treat grade)






