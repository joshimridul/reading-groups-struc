clear
#delimit;
set mem 200m;
set more off;

use student_test_data.dta, clear;

* CREATE VARIOUS VARIABLES;
gen etpteacher_tracking_lowstream=etpteacher*lowstream;
gen sbm_tracking_lowstream=sbm*tracking*lowstream;
foreach name in bottomhalf tophalf etpteacher  {;
	gen `name'_tracking=`name'*tracking;
};

gen percentilesq=percentile*percentile;
gen percentilecub=percentile^3;

* CLEAN AGE VARIABLE;
replace agetest=r2_age-1 if agetest==.;

* STANDARDIZE TEST SCORES;
for any litscore mathscoreraw totalscore letterscore wordscore sentscore spellscore  additions_score substractions_score 
multiplications_score: 
sum X if tracking==0  \
gen meancomp=r(mean) \
gen sdcomp=r(sd) \
gen stdR_X=(X-meancomp)/sdcomp \
drop meancomp sdcomp;

save forpeerpapers, replace;

******************;
*FIGURE 1;
******************;
use forpeerpapers,clear;
gen trackinggroup="Non-Tracking Schools" if tracking==0;
	replace trackinggroup="Tracking Schools" if tracking==1;
twoway hist std_mark, by(trackinggroup, note("")) xtitle("") saving(figI, replace);
drop trackinggroup;

******************;
*FIGURE 2;
******************;
use forpeerpapers,clear;

collapse stream_meanpercentile, by(quantile5p tracking);
gen streamscore_T=stream_meanpercentile if tracking==1;
gen streamscore_R=stream_meanpercentile if tracking==0;

twoway scatter streamscore_R streamscore_T quantile5p, ms(O d) c(i) clp(l) clw(med) mc(sand) clc(sand) xline(10.5) 
xtitle("Own Initial Attainment:  Baseline 20-Quantile") ytitle("Mean Standardized Baseline Score of Classmates") 
 yscale(titlegap(4)) xtick(1(1)20) xlabel(1(1)20) xscale(titlegap(3)) legend(label(1 "Random Schools") label(2 "Tracking Schools"))
saving(figII, replace);

******************;
*** FIGURE 3;
******************;
use forpeerpapers,clear;
set seed 101;

gen interval=realpercentile;
*cec is the above-the-cutff dummy;
	gen cec=0 if realpercentile!=.;
	replace cec=1 if quantile5p>10&quantile5p!=.;

rename stdR_totalscore Total;

collapse Total stream_meanpercentile , by(interval cec tracking);

forvalues x=2/3{;		
gen interval`x'=interval^`x';
};

foreach var of varlist  Total{;
forvalues x=0/1{;
reg `var' interval* if cec==`x' & tracking==1;
predict yT`x'`var' if e(sample), xb;
};
};
foreach var of varlist  Total{;
forvalues x=0/1{;
reg `var' interval* if cec==`x' & tracking==0;
predict yN`x'`var' if e(sample), xb;
};
};
gen TotalN=Total if tracking==0;
gen TotalT=Total if tracking==1;

foreach var of varlist Total {;
twoway scatter TotalT TotalN interval, ms(O O) c(i  i) clp(blank blank ) mfc(sand none) mlc(sand sienna ) clc(sand sienna ) xline(50)
	 || line yT1 yT0 yN1 yN0 interval, lc(navy navy maroon maroon) lw(medthick medthick medthick medthick)
	legend(order(1 3 2 5) label(1 "Local Average, Tracking Schools") label(3 "Polynomial Fit")
	label(2 "Local Average, Non-Tracking Schools") label(5 "Polynomial Fit"))
	xtitle("Initial Attainment Percentile") ytitle("Endline Test Scores", margin(medium))
	title("Effect of Tracking by Initital Attainment")
	saving(FigIII, replace);
};


************************;
***FIGURE A1 PANEL A;
************************;
use forpeerpapers,clear;
set seed 101;

gen interval=realpercentile;
*cec is the above-the-cutff dummy;
	gen cec=0 if realpercentile!=.;
	replace cec=1 if quantile5p>10&quantile5p!=.;

rename stdR_mathscoreraw Mathematics;
rename stdR_litscore Language;
rename stdR_totalscore Total;

keep if tracking==1;
collapse Mathematics Language Total stream_meanpercentile , by(interval cec);

forvalues x=2/3{;		
gen interval`x'=interval^`x';
};

foreach var of varlist Mathematics Language Total{;
forvalues x=0/1{;
reg `var' interval* if cec==`x';
predict y`x'`var' if e(sample), xb;
};
};

foreach var of varlist Total {;
	scatter `var' y1`var' y0`var' interval, ms(O i i) c(i l l) clp(blank l l) clw(med med med) mc(sand navy navy) clc(sand navy navy) xline(50) 
	legend(order(1 2) label(1 "Local Average") label(2 "Polynomial Fit"))
	xtitle("Initial Attainment Percentile") ytitle("Endline Test Scores")
	saving(FigA1_A, replace);
};


******************;
*** FIGURE A2 PANEL A;
******************;
use forpeerpapers,clear;
set seed 101;

gen interval=realpercentile;
*cec is the above-the-cutff dummy;
	gen cec=0 if realpercentile!=.;
	replace cec=1 if quantile5p>10&quantile5p!=.;

rename stdR_totalscore Total;

bys schoolid: egen etplow=max(etpteacher_tracking_lowstream);
collapse Total stream_meanpercentile , by(interval cec tracking etplow);

forvalues x=2/3{;		
gen interval`x'=interval^`x';
};

foreach var of varlist  Total{;
forvalues x=0/1{;
reg `var' interval* if cec==`x' & tracking==1&etplow==1-`x';
predict yT`x'`var' if e(sample), xb;
};
};
foreach var of varlist  Total{;
forvalues x=0/1{;
reg `var' interval* if cec==`x' & tracking==0;
predict yN`x'`var' if e(sample), xb;
};
};
gen TotalN=Total if tracking==0;
gen TotalT=Total if tracking==1&[(etplow==1&cec==0)|(etplow==0&cec==1)];
#delimit;
foreach var of varlist Total {;
twoway scatter TotalT TotalN interval, ms(O O) c(i  i) clp(blank blank ) mfc(sand none) mlc(sand sienna ) clc(sand sienna ) xline(50)
	 || line yT1 yT0 yN1 yN0 interval, lc(navy navy maroon maroon) lw(medthick medthick medthick medthick)
	legend(cols(2) order(- "Tracking Schools:" - " " 1 3 - "Non-Tracking Schools:" - " " 2 5) label(1 "Local Average") label(3 "Polynomial Fit")
	label(2 "Local Average") label(5 "Polynomial Fit"))
	xtitle("Initial Attainment Percentile") ytitle("Endline Test Scores", margin(medium))
	title("")
	saving(FigA2_A, replace);
};


******************;
*** FIGURE A2 PANEL B;
******************;
use forpeerpapers,clear;
set seed 101;
gen interval=realpercentile;
*cec is the above-the-cutff dummy;
	gen cec=0 if realpercentile!=.;
	replace cec=1 if quantile5p>10&quantile5p!=.;

rename stdR_totalscore Total;

bys schoolid: egen etplow=max(etpteacher_tracking_lowstream);
collapse Total stream_meanpercentile , by(interval cec tracking etplow);

forvalues x=2/3{;		
gen interval`x'=interval^`x';
};

foreach var of varlist  Total{;
forvalues x=0/1{;
reg `var' interval* if cec==`x' & tracking==1&etplow==`x';
predict yT`x'`var' if e(sample), xb;
};
};
foreach var of varlist  Total{;
forvalues x=0/1{;
reg `var' interval* if cec==`x' & tracking==0;
predict yN`x'`var' if e(sample), xb;
};
};
gen TotalN=Total if tracking==0;
gen TotalT=Total if tracking==1&[(etplow==1&cec==1)|(etplow==0&cec==0)];

foreach var of varlist Total {;
twoway scatter TotalT TotalN interval, ms(O O) c(i  i) clp(blank blank ) mfc(sand none) mlc(sand sienna ) clc(sand sienna ) xline(50)
	 || line yT1 yT0 yN1 yN0 interval, lc(navy navy maroon maroon) lw(medthick medthick medthick medthick)
	legend(cols(2) order(- "Tracking Schools:" - " " 1 3 - "Non-Tracking Schools:" - " " 2 5) label(1 "Local Average") label(3 "Polynomial Fit")
	label(2 "Local Average") label(5 "Polynomial Fit"))
	xtitle("Initial Attainment Percentile") ytitle("Endline Test Scores", margin(medium))
	title("")
	saving(FigA2_B, replace);
};




********************************************************;
****************TABLE II, PANEL A: OVERALL EFFECT -- SHORT RUN;
********************************************************;
use forpeerpapers, clear;
gen girl_tracking=girl*tracking;

foreach name in bottom second third top{;
	gen `name'quarter_tracking=`name'quarter*tracking;
};

sum stdR_totalscore if tracking==0;
gen mean_total=r(mean);
gen sd_total=r(sd);
reg stdR_totalscore  tracking bottomhalf  bottomhalf_tracking bottomquarter bottomquarter_tracking secondquarter secondquarter_tracking topquarter topquarter_tracking girl  percentile percentilesq agetest etpteacher , cluster(schoolid);
outreg using peersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_total, "Std Dev", sd_total) bdec(3) adec(3) replace;
drop mean_total sd_total;

foreach var in stdR_totalscore stdR_mathscore stdR_litscore {;
sum `var' if tracking==0;
gen mean_`var'=r(mean);
gen sd_`var'=r(sd);
reg `var' tracking, cluster(schoolid);
outreg using peersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var') bdec(3) adec(3) append;
reg `var' tracking girl percentile agetest etpteacher, cluster(schoolid);
outreg using peersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var') bdec(3) adec(3) append;
reg `var' tracking bottomhalf bottomhalf_tracking girl percentile agetest etpteacher, cluster(schoolid);
test tracking+bottomhalf_tracking=0;
outreg using peersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var',"F1", r(F), "P1", r(p)) bdec(3) adec(3) append;
reg `var' tracking bottomquarter bottomquarter_tracking secondquarter secondquarter_tracking topquarter topquarter_tracking girl percentile agetest etpteacher, cluster(schoolid);
test tracking+bottomquarter_tracking==0;
gen F1=r(F);
gen P1=r(p);
test tracking+secondquarter_tracking==0;
gen F2=r(F);
gen P2=r(p);
test tracking+topquarter_tracking==0;
gen F3=r(F);
gen P3=r(p);
test (tracking+topquarter_tracking)=(tracking+bottomquarter_tracking);
gen F4=r(F);
gen P4=r(p);
outreg using peersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var', "F1", F1, "P1", P1,"F2", F2, "P2", P2,"F3", F3, "P3", P3, "P4", P4) bdec(3) adec(3) append;
drop F1 F2 F3 P1 P2 P3 F4 P4;

drop mean_`var' sd_`var';
};

****************************************************;
**********TABLE II, PANEL B: OVERALL EFFECT -- LONG RUN;
****************************************************;

for any litscore mathscoreraw totalscore letterscore wordscore sentscore spellscore  additions_score substractions_score 
multiplications_score: 
sum r2_X if tracking==0 \
gen meancomp=r(mean) \
gen sdcomp=r(sd) \
gen stdR_r2_X=(r2_X-meancomp)/sdcomp \
drop meancomp sdcomp;

sum stdR_r2_totalscore if tracking==0;
gen mean_total=r(mean);
gen sd_total=r(sd);
reg stdR_r2_totalscore  tracking bottomhalf   bottomhalf_tracking bottomquarter bottomquarter_tracking secondquarter secondquarter_tracking topquarter topquarter_tracking girl  percentile percentilesq agetest etpteacher , cluster(schoolid);
outreg using LTpeersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_total, "Std Dev", sd_total) adec(3) bdec(3) replace;
drop mean_total sd_total;

foreach var in stdR_r2_totalscore stdR_r2_mathscore stdR_r2_litscore {;
sum `var' if tracking==0;
gen mean_`var'=r(mean);
gen sd_`var'=r(sd);
reg `var' tracking, cluster(schoolid);
outreg using LTpeersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var') bdec(3) adec(3) append;
reg `var' tracking girl percentile agetest etpteacher, cluster(schoolid);
outreg using LTpeersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var') bdec(3) adec(3) append;
reg `var' tracking bottomhalf bottomhalf_tracking girl percentile agetest etpteacher, cluster(schoolid);
test tracking+bottomhalf_tracking=0;
outreg using LTpeersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var',"F1", r(F), "P1", r(p)) bdec(3) adec(3) append;
reg `var' tracking bottomquarter bottomquarter_tracking secondquarter secondquarter_tracking topquarter topquarter_tracking girl percentile agetest etpteacher, cluster(schoolid);
test tracking+bottomquarter_tracking==0;
gen F1=r(F);
gen P1=r(p);
test tracking+secondquarter_tracking==0;
gen F2=r(F);
gen P2=r(p);
test tracking+topquarter_tracking==0;
gen F3=r(F);
gen P3=r(p);
test (tracking+topquarter_tracking)=(tracking+bottomquarter_tracking);
gen F4=r(F);
gen P4=r(p);
outreg using LTpeersoverall.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var', "F1", F1, "P1", P1,"F2", F2, "P2", P2,"F3", F3, "P3", P3, "P4", P4) bdec(3) adec(3) append;
drop F1 F2 F3 P1 P2 P3 F4 P4;

drop mean_`var' sd_`var';
};


**************************************;
****************TABLE III: by subgroups;
**************************************;
use forpeerpapers, clear;

gen topage=1 if agetest>9&agetest!=.;
replace topage=0 if agetest<9;

for any litscore mathscoreraw totalscore letterscore wordscore sentscore spellscore  additions_score substractions_score 
multiplications_score: 
sum r2_X if tracking==0 \
gen meancomp=r(mean) \
gen sdcomp=r(sd) \
gen stdR_r2_X=(r2_X-meancomp)/sdcomp \
drop meancomp sdcomp;

gen cont=etpteacher;


foreach cat in girl cont topage {;

	foreach half in bottomhalf tophalf {;
	gen `cat'_`half'=`cat'*`half';
	gen `cat'_tracking_`half'=`cat'*`half'_tracking;
	gen anti`cat'_tracking_`half'=(1-`cat')*`half'_tracking;
	};

*short-run;
reg stdR_totalscore `cat'_tracking_bottomhalf anti`cat'_tracking_bottomhalf  `cat'_tracking_tophalf anti`cat'_tracking_tophalf bottomhalf `cat'_bottomhalf percentile girl agetest etpteacher, cluster(schoolid);
test `cat'_tracking_bottomhalf=anti`cat'_tracking_bottomhalf;
gen P1=r(p);
test `cat'_tracking_tophalf=anti`cat'_tracking_tophalf;
gen P2=r(p);
test `cat'_tracking_tophalf=`cat'_tracking_bottomhalf;
gen PA=r(p);
test anti`cat'_tracking_tophalf=anti`cat'_tracking_bottomhalf;
gen PB=r(p);
outreg using peersoverall`cat'.xls, nor2 se nonote sigsymb(***,**,*) addstat("Vert1", P1, "Vert2", P2, "Hor1", PA, "Hor2", PB) bdec(3) adec(3) replace;
drop P1 P2 PA PB;

*long-run;
reg stdR_r2_totalscore `cat'_tracking_bottomhalf anti`cat'_tracking_bottomhalf  `cat'_tracking_tophalf anti`cat'_tracking_tophalf bottomhalf `cat'_bottomhalf percentile girl agetest etpteacher, cluster(schoolid);
test `cat'_tracking_bottomhalf=anti`cat'_tracking_bottomhalf;
gen P1=r(p);
test `cat'_tracking_tophalf=anti`cat'_tracking_tophalf;
gen P2=r(p);
test `cat'_tracking_tophalf=`cat'_tracking_bottomhalf;
gen PA=r(p);
test anti`cat'_tracking_tophalf=anti`cat'_tracking_bottomhalf;
gen PB=r(p);
outreg using LTpeersoverall`cat'.xls, nor2 se nonote sigsymb(***,**,*) addstat("Vert1", P1, "Vert2", P2, "Hor1", PA, "Hor2", PB) bdec(3) adec(3) replace;

drop P1 P2 PA PB;
};


********************************************************************************;
************TABLE 4: RANDOM VARIATION IN PEERS, NON-TRACKING SCHOOLS************;
*******************************************************************************;
use forpeerpapers, clear;
keep if tracking==0;

*PANEL A;
***cluster at stream level;
egen section=group(schoolid stream);

*TOTAL*;
areg stdR_totalscore  rMEANstream_std_baselinemark rSDstream_std_baselinemark   std_mark girl agetest etpteacher, absorb(schoolid) cluster(section);
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3)  replace;
areg stdR_totalscore  rMEANstream_std_baselinemark  std_mark girl agetest etpteacher, absorb(schoolid) cluster(section);
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3)  append;
areg stdR_totalscore rSDstream_std_baselinemark  std_mark girl agetest etpteacher, absorb(schoolid) cluster(section);
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3) append;

*MATH*;
areg stdR_mathscore  rMEANstream_std_baselinemark std_mark girl agetest etpteacher, absorb(schoolid) cluster(section);
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3)  append;

*LIT*;
areg stdR_litscore  rMEANstream_std_baselinemark std_mark girl agetest etpteacher, absorb(schoolid) cluster(section);
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3)  append;

*25-75th percentile*;
areg stdR_totalscore  rMEANstream_std_baselinemark   std_mark girl agetest etpteacher, absorb(schoolid) cluster(section), if std_mark>=-0.75&std_mark<=0.75;
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3)  append;

*<25th percentile*;
areg stdR_totalscore  rMEANstream_std_baselinemark   std_mark girl agetest etpteacher, absorb(schoolid) cluster(section), if std_mark<-0.275;
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3)  append;

*>75th percentile*;
areg stdR_totalscore  rMEANstream_std_baselinemark std_mark girl agetest etpteacher, absorb(schoolid) cluster(section), if std_mark>0.75;
outreg using peerA.xls, nor2 se nonote sigsymb(***,**,*)  bdec(3)  append;

***********;
*PANEL B;
***********;
use forpeerpapers, clear;
keep if tracking==0;

***cluster at stream level;
egen section=group(schoolid stream);

#delimit;
*first stages;
*col1;
xi: xtreg  rMEANstream_std_total  rMEANstream_std_baselinemark rSDstream_std_baselinemark etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark rSDstream_std_baselinemark etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) replace;

xi: xtreg  rSDstream_std_total  rMEANstream_std_baselinemark rSDstream_std_baselinemark etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark rSDstream_std_baselinemark etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3) replace;

*col2;
xi: xtreg  rMEANstream_std_total  rMEANstream_std_baselinemark etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

xi: reg rSDstream_std_total   rSDstream_std_baselinemark  etpteacher i.schoolid;
outreg rSDstream_std_baselinemark etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3)   append;

*col 3;
xi: xtreg  rMEANstream_std_total  rMEANstream_std_baselinemark etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

xi: reg rSDstream_std_total   rSDstream_std_baselinemark  etpteacher i.schoolid;
outreg rSDstream_std_baselinemark etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3)   append;

*col 4;
xi: xtreg  rMEANstream_std_math  rMEANstream_std_baselinemark etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

xi: xtreg  rSDstream_std_math  rMEANstream_std_baselinemark etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

*col 5;
xi: xtreg  rMEANstream_std_lit  rMEANstream_std_baselinemark etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

xi: xtreg  rSDstream_std_lit  rMEANstream_std_baselinemark   etpteacher,fe i(schoolid);
outreg  rMEANstream_std_baselinemark   etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

*col 6;
xi: xtreg  rMEANstream_std_total  rMEANstream_std_baselinemark   etpteacher,fe i(schoolid), if std_mark>=-0.75&std_mark<=0.25;
outreg  rMEANstream_std_baselinemark   etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

xi: xtreg  rSDstream_std_total  rMEANstream_std_baselinemark   etpteacher,fe i(schoolid), if std_mark>=-0.75&std_mark<=0.25;
outreg  rMEANstream_std_baselinemark   etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

*col 7;
xi: xtreg  rMEANstream_std_total  rMEANstream_std_baselinemark   etpteacher,fe i(schoolid), if std_mark<-0.75;
outreg  rMEANstream_std_baselinemark   etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

xi: xtreg  rSDstream_std_total  rMEANstream_std_baselinemark   etpteacher,fe i(schoolid), if std_mark<-0.75;
outreg  rMEANstream_std_baselinemark   etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

*col 8;
xi: xtreg  rMEANstream_std_total  rMEANstream_std_baselinemark   etpteacher,fe i(schoolid), if std_mark>0.75;
outreg  rMEANstream_std_baselinemark   etpteacher  using firststage6M.xls,  se nonote sigsymb(***,**,*) bdec(3) append;

xi: xtreg  rSDstream_std_total  rMEANstream_std_baselinemark   etpteacher,fe i(schoolid), if std_mark>0.75;
outreg  rMEANstream_std_baselinemark   etpteacher  using firststage6S.xls,  se nonote sigsymb(***,**,*) bdec(3) append;


*second-stage;
xi: ivreg stdR_totalscore ( rMEANstream_std_total rSDstream_std_total= rMEANstream_std_baselinemark  rSDstream_std_baselinemark   ) std_mark etpteacher girl agetest i.schoolid, cluster(section) ;
outreg  rMEANstream_std_total rSDstream_std_total std_mark etpteacher girl agetest  using RD6.xls, nor2 se nonote sigsymb(***,**,*) bdec(3) replace;

xi: ivreg stdR_totalscore ( rMEANstream_std_total= rMEANstream_std_baselinemark ) std_mark etpteacher girl agetest i.schoolid, cluster(section) ;
outreg  rMEANstream_std_total std_mark etpteacher girl agetest  using RD6.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)  append;

xi: ivreg stdR_totalscore (rSDstream_std_total = rSDstream_std_baselinemark  ) std_mark etpteacher girl agetest i.schoolid, cluster(section) ;
outreg rSDstream_std_total std_mark etpteacher girl agetest  using RD6.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)   append;

xi: ivreg stdR_mathscore ( rMEANstream_std_math = rMEANstream_std_baselinemark    ) std_mark etpteacher girl agetest i.schoolid, cluster(section) ;
outreg  rMEANstream_std_math std_mark etpteacher girl agetest  using RD6.xls, nor2 se nonote sigsymb(***,**,*) bdec(3) append;

xi: ivreg stdR_litscore ( rMEANstream_std_lit = rMEANstream_std_baselinemark    ) std_mark etpteacher girl agetest i.schoolid, cluster(section) ;
outreg  rMEANstream_std_lit std_mark etpteacher girl agetest  using RD6.xls, nor2 se nonote sigsymb(***,**,*) bdec(3) append;

xi: ivreg stdR_totalscore ( rMEANstream_std_total = rMEANstream_std_baselinemark    ) std_mark etpteacher girl agetest i.schoolid
, cluster(section), if std_mark>=-0.75&std_mark<=0.75;
outreg  rMEANstream_std_total std_mark etpteacher girl agetest  using RD6.xls, 
nor2 se nonote sigsymb(***,**,*) bdec(3) append;

xi: ivreg stdR_totalscore ( rMEANstream_std_total = rMEANstream_std_baselinemark    ) std_mark etpteacher girl agetest i.schoolid
, cluster(section), if std_mark<-0.75;
outreg  rMEANstream_std_total std_mark etpteacher girl agetest  using RD6.xls, 
nor2 se nonote sigsymb(***,**,*) bdec(3) append;

xi: ivreg stdR_totalscore ( rMEANstream_std_total = rMEANstream_std_baselinemark    ) std_mark etpteacher girl agetest i.schoolid
, cluster(section), if std_mark>0.75;
outreg  rMEANstream_std_total std_mark etpteacher girl agetest  using RD6.xls, 
nor2 se nonote sigsymb(***,**,*) bdec(3) append;




***********************************************;
******************** TABLE V, PANEL A  *******;
************************************************;
use forpeerpapers, clear;
keep if tracking==1;
sum stdR_totalscore if bottomhalf==1;
gen mean_total=r(mean);
gen sd_total=r(sd);
reg stdR_totalscore bottomhalf percentile percentilesq percentilecu etpteacher girl agetest, cluster(schoolid) ;
outreg using RDA1.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_total, Std Dev, sd_total) bdec(3) adec(2) replace;
drop mean_total sd_total;

foreach subject in total {;

*specification 1, no FE;
use forpeerpapers, clear;
keep if tracking==1;

sum stdR_`subject'score if bottomhalf==1;
gen mean_`subject'=r(mean);
gen sd_`subject'=r(sd);
reg stdR_`subject'score bottomhalf percentile percentilesq percentilecub etpteacher girl agetest, cluster(schoolid) ;
outreg using RDA1.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`subject', Std Dev, sd_`subject') bdec(3) adec(2) append;
drop mean_`subject' sd_`subject';

* specification 4, no FE;
drop if stdR_`subject'score==.;
egen topkid=max(std_mark), by(schoolid bottomhalf);
egen botkid=min(std_mark), by(schoolid bottomhalf);
keep if (std_mark==topkid&bottomhalf==1)|(std_mark==botkid&bottomhalf==0);
sum stdR_`subject'score if bottomhalf==1;
gen mean_`subject'=r(mean);
gen sd_`subject'=r(sd);
reg stdR_`subject'score bottomhalf etpteacher girl agetest  std_mark, cluster(schoolid) ;
outreg using RDA1.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`subject', Std Dev, sd_`subject') bdec(3) adec(2) append;
drop mean_`subject' sd_`subject';


*specification 1, with FE;
use forpeerpapers, clear;
keep if tracking==1;
sum stdR_`subject'score if bottomhalf==1;
gen mean_`subject'=r(mean);
gen sd_`subject'=r(sd);
areg stdR_`subject'score bottomhalf percentile percentilesq percentilecub etpteacher girl agetest, absorb(schoolid);
outreg bottomhalf percentile percentilesq percentilecub etpteacher girl agetest using RDA1.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`subject', Std Dev, sd_`subject') bdec(3) adec(2) append;
drop mean_`subject' sd_`subject';

* specification 4, with FE;
drop if stdR_`subject'score==.;
egen topkid=max(std_mark), by(schoolid bottomhalf);
egen botkid=min(std_mark), by(schoolid bottomhalf);
keep if (std_mark==topkid&bottomhalf==1)|(std_mark==botkid&bottomhalf==0);
sum stdR_`subject'score if bottomhalf==1;
gen mean_`subject'=r(mean);
gen sd_`subject'=r(sd);
areg stdR_`subject'score bottomhalf etpteacher girl agetest std_mark, absorb(schoolid) ;
outreg bottomhalf etpteacher girl agetest using RDA1.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`subject', Std Dev, sd_`subject') bdec(3) adec(2) append;
drop mean_`subject' sd_`subject' topkid botkid;

};

***** SPECIFICATION 2;

mat RDQUAD=J(2,12,0);

cap program drop rdquad;
program define rdquad, eclass;
args score percentile percentilesq  bottomhalf etpteacher girl agetest;
gen bottom_percentile=`bottomhalf'*percentile;
gen bottom_percentilesq=`bottomhalf'*percentilesq;
reg `score' `percentile' `percentilesq'  bottom_percentile bottom_percentilesq `bottomhalf' `etpteacher' `girl' `agetest';
gen pred_top=_b[_cons]+_b[`percentile']*50+_b[`percentilesq']*50*50;
gen pred_bot=_b[_cons]+_b[`percentile']*50+_b[`percentilesq']*50*50+_b[`bottomhalf']+_b[bottom_percentile]*50+_b[bottom_percentilesq]*50*50; 
gen diff=pred_bot-pred_top;
ereturn scalar diff=diff;
drop pred_top pred_bot diff bottom_percentile*;
end;

cap program drop rdquadfe;
program define rdquadfe, eclass;
args score percentile percentilesq  bottomhalf etpteacher  girl agetest schoolid;
gen bottom_percentile=`bottomhalf'*percentile;
gen bottom_percentilesq=`bottomhalf'*percentilesq;
xtreg `score' `percentile' `percentilesq'  bottom_percentile bottom_percentilesq `bottomhalf' `etpteacher' `girl' `agetest' , fe i(`schoolid');
gen pred_top=_b[_cons]+_b[`percentile']*50+_b[`percentilesq']*50*50;
gen pred_bot=_b[_cons]+_b[`percentile']*50+_b[`percentilesq']*50*50+_b[`bottomhalf']+_b[bottom_percentile]*50+_b[bottom_percentilesq]*50*50; 
gen diff=pred_bot-pred_top;
ereturn scalar diff=diff;
drop pred_top pred_bot diff bottom_percentile*;
end;

use forpeerpapers, clear;
keep if tracking==1;
bootstrap e(diff), reps(1000): rdquad  stdR_totalscore percentile percentilesq  bottomhalf etpteacher girl agetest , cluster(schoolid);
mat RDQUAD[1,1]=_b[_bs_1];
mat RDQUAD[2,1]=_se[_bs_1];
bootstrap e(diff), reps(1000): rdquadfe  stdR_totalscore percentile percentilesq bottomhalf etpteacher girl agetest schoolid;
mat RDQUAD[1,2]=_b[_bs_1];
mat RDQUAD[2,2]=_se[_bs_1];

use forpeerpapers, clear;
keep if tracking==1&etpteacher==0;
bootstrap e(diff), reps(1000): rdquad  stdR_totalscore percentile percentilesq  bottomhalf etpteacher girl agetest , cluster(schoolid);
mat RDQUAD[1,3]=_b[_bs_1];
mat RDQUAD[2,3]=_se[_bs_1];

svmat RDQUAD;
keep  RDQUAD1- RDQUAD3;
drop if _n>2;
outsheet using RDQUAD.xls, replace;

* SPECIFICATION 3: FAN LOCALLY WEIGHTED****;
use forpeerpapers, clear;

cap program drop lowrex;
program def lowrex;
local ic=1;
gen `3'=.;
gen `4'=.;
gen `7'=.;
while `ic' <= $gsize {;
dis `ic';
quietly {;
local xx=`6'[`ic'];
gen z=abs((`2'-`xx')/`5');
gen kz=(15/16)*(1-z^2)^2 if z <= 1;
reg `1' `2' [pweight=kz] if kz ~= .;
replace `4'=_b[`2'] in `ic';
replace `3'=_b[_cons]+_b[`2']*`xx' in `ic';
reg `1' [pweight=kz] if kz ~= .;
replace `7'=_b[_cons] in `ic';
drop z kz;
};
local ic=`ic'+1;
};
end; 

****FIGURE III PANEL A****;
local h 2;
		
	while `h'<=4 {;
	global h=`h'/2;
	local k=`h'+1;
	global gsize=100;

		***bottom stream tracking;
		use forpeerpapers, clear;
		qui keep if tracking==1;
		qui drop if bottomhalf==0;
		global xmin=1;
		global xmax=50;
		global st=($xmax-$xmin)/($gsize-1);
		qui gen xgrid=$xmin+(_n-1)*$st in 1/$gsize;
		quietly lowrex stdR_totalscore realpercentile pred_botT dsmth $h xgrid mean;
		qui drop dsmth;
		sort xgrid;
		qui keep in 1/$gsize;
		qui keep pred_botT xgrid mean;
		qui save pred_botT, replace;
		
		***top stream tracking;
		use forpeerpapers, clear;
		qui drop if bottomhalf==1;
		qui keep if tracking==1;
		global xmin=51;
		global xmax=99;
		global st=($xmax-$xmin)/($gsize-1);
		qui gen xgrid=$xmin+(_n-1)*$st in 1/$gsize;
		quietly lowrex stdR_totalscore realpercentile pred_topT dsmth $h xgrid mean;
		qui drop dsmth;
		sort xgrid;
		qui keep in 1/$gsize;
		qui keep pred_topT xgrid mean;
		qui save pred_topT, replace;
		
		append using pred_botT;
		save pred_fan$h, replace;
		label var xgrid "Initial Attainment Percentile";
		label var pred_topT "Tracking Schools";
		label var pred_botT "Tracking Schools";
		
		*****GRAPH FIGURE A1 PANEL B;
		twoway line pred_botT pred_topT xgrid, c(ll) s(ii)  xline(50.5) saving(FigA1_B, replace) legend(off);
		
	local h=`h'+2;
	};

*BACK TO TABLE 5, SPECIFICATION 3;
#delimit;
cap program drop RDfan;
program define RDfan, eclass; 
args stdR_totalscore tracking bottomhalf realpercentile band1 band2; 
preserve;

global band1 `band1';
global band2 `band2';

gen stdR_totalscore_top=`stdR_totalscore' if `tracking'==1&`bottomhalf'==0;
gen stdR_totalscore_bot=`stdR_totalscore' if `tracking'==1&`bottomhalf'==1;
global xmin_top=1;
global xmax_top=50;
global xmin_bot=51;
global xmax_bot=99;
global gsize=100;
global st_top=($xmax_top-$xmin_top)/($gsize-1);
global st_bot=($xmax_bot-$xmin_bot)/($gsize-1);

gen xgrid_top=$xmin_top+(_n-1)*$st_top in 1/$gsize;
gen xgrid_bot=$xmin_bot+(_n-1)*$st_bot in 1/$gsize;
sort xgrid_bot;
lowrex stdR_totalscore_bot `realpercentile' pred_bot${band1} dsmth `band1' xgrid_top mean;
drop dsmth mean;
sort xgrid_top;
lowrex stdR_totalscore_top `realpercentile' pred_top${band1} dsmth `band1' xgrid_bot mean;
drop dsmth mean;

sort xgrid_bot;
lowrex stdR_totalscore_bot `realpercentile' pred_bot${band2} dsmth `band2' xgrid_top mean;
drop dsmth mean;
sort xgrid_top;
lowrex stdR_totalscore_top `realpercentile' pred_top${band2} dsmth `band2' xgrid_bot mean;
drop dsmth mean;

sort xgrid_top xgrid_bot;
keep in 1/100;
local gap${band1}=pred_bot${band1}[99]-pred_top${band1}[2];
local gap${band2}=pred_bot${band2}[99]-pred_top${band2}[2];
ereturn scalar Fangap${band1}=`gap${band1}';
ereturn scalar Fangap${band2}=`gap${band2}';
drop xgrid_top xgrid_bot std_totalscore* pred*;
restore;
end;

#delimit;
mat RDfan=J(2,2,0);
use forpeerpapers, clear;
keep if tracking==1;
bootstrap e(Fangap4) e(Fangap5), reps(100): RDfan stdR_totalscore tracking bottomhalf realpercentile 4 5;
mat RDfan[1,1]=_b[_bs_1];
mat RDfan[2,1]=_se[_bs_1];
mat RDfan[1,2]=_b[_bs_2];
mat RDfan[2,2]=_se[_bs_2];
svmat RDfan;
keep  RDfan1 RDfan2;
drop if _n>2;
outsheet using RDfanboot2.xls, replace;


**********************************;
**************  TABLE V, PANEL B;
**********************************;

use forpeerpapers, clear;
keep if tracking==1;

* specification 1, no FE;
reg stdR_totalscore  rMEANstream_std_total  rMEANstream_std_math  rMEANstream_std_lit percentile percentilesq percentilecub etpteacher girl agetest, cluster(schoolid) ;
outreg  rMEANstream_std_total  rMEANstream_std_math  rMEANstream_std_lit using RDIV.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)   replace;

reg stdR_totalscore bottomhalf percentile percentilesq percentilecub etpteacher girl agetest, cluster(schoolid) ;
outreg using firststage.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)   replace;

foreach subject in total math lit {;
use forpeerpapers, clear;
keep if tracking==1;

reg  rMEANstream_std_`subject' bottomhalf percentile percentilesq percentilecub etpteacher girl agetest, cluster(schoolid);
outreg using firststage.xls,  se nonote sigsymb(***,**,*) bdec(3)   append;
reg stdR_`subject'score  rMEANstream_std_`subject' percentile percentilesq percentilecub etpteacher girl agetest (bottomhalf percentile percentilesq percentilecub etpteacher girl agetest ), cluster(schoolid) ;
outreg  rMEANstream_std_`subject' using RDIV.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)   append;


* specification 4, no FE; 
drop if stdR_`subject'score==.;
egen topkid=max(std_mark), by(schoolid bottomhalf);
egen botkid=min(std_mark), by(schoolid bottomhalf);
keep if (std_mark==topkid&bottomhalf==1)|(std_mark==botkid&bottomhalf==0);
reg  rMEANstream_std_`subject' bottomhalf  etpteacher girl agetest, cluster(schoolid);
outreg using firststage.xls,  se nonote sigsymb(***,**,*) bdec(3)   append;
reg stdR_`subject'score  rMEANstream_std_`subject' etpteacher girl agetest (bottomhalf  etpteacher girl agetest ), cluster(schoolid) ;
outreg  rMEANstream_std_`subject' using RDIV.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)   append;


* specification 1, with FE;
use forpeerpapers, clear;
keep if tracking==1;

xtreg  rMEANstream_std_`subject' bottomhalf percentile percentilesq percentilecub etpteacher girl agetest, fe i(schoolid) cluster(schoolid);
outreg using firststage.xls, se nonote sigsymb(***,**,*) bdec(3)   append;
xi: ivreg stdR_`subject'score  percentile percentilesq percentilecub etpteacher girl agetest ( rMEANstream_std_`subject'=bottomhalf) i.schoolid, cluster(schoolid);
outreg  rMEANstream_std_`subject' using RDIV.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)   append;

* specification 4, with FE;
drop if stdR_`subject'score==.;
egen topkid=max(std_mark), by(schoolid bottomhalf);
egen botkid=min(std_mark), by(schoolid bottomhalf);
keep if (std_mark==topkid&bottomhalf==1)|(std_mark==botkid&bottomhalf==0);
xtreg  rMEANstream_std_`subject' bottomhalf  etpteacher girl agetest, fe i(schoolid) cluster(schoolid);
outreg using firststage.xls,  se nonote sigsymb(***,**,*) bdec(3)   append;
xi: ivreg stdR_`subject'score etpteacher girl agetest ( rMEANstream_std_`subject'=bottomhalf) i.schoolid, cluster(schoolid);
outreg  rMEANstream_std_`subject' using RDIV.xls, nor2 se nonote sigsymb(***,**,*) bdec(3)   append;
};


*****************************************;
**************** TABLE VI  **************;
*****************************************;
* TEACHER EFFORT; 
use teacher_pres_data, replace;

global indepvar5="tracking lowstream  yrstaught female bungoma visitno realdate";

sum pres if tracking==0;
gen mean=r(mean);
xi: reg pres ${indepvar5}, cluster(schoolid);
test ${indepvar5};
outreg using teachernamelisttracking.xls,nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean,"F test", r(F), "Prob >F", r(p) ) bdec(3) adec(4) replace;
drop mean;

sum inclass if tracking==0;
gen mean=r(mean);
xi: reg inclass ${indepvar5}, cluster(schoolid);
test ${indepvar5};
outreg using teachernamelisttracking.xls,nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean,"F test", r(F), "Prob >F", r(p) ) bdec(3) adec(4) append;
drop mean;

sum pres if etpteacher==0&tracking==0;
gen mean=r(mean);
xi: reg pres ${indepvar5}, cluster(schoolid), if etpteacher==0;
test ${indepvar5};
outreg using teachernamelisttracking.xls,nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean,"F test", r(F), "Prob >F", r(p) ) bdec(3) adec(4) append;
drop mean;

sum inclass if etpteacher==0&tracking==0;
gen mean=r(mean);
xi: reg inclass ${indepvar5}, cluster(schoolid), if etpteacher==0;
test ${indepvar5};
outreg using teachernamelisttracking.xls,nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean,"F test", r(F), "Prob >F", r(p) ) bdec(3) adec(4) append;
drop mean;

sum pres if etpteacher==1&tracking==0;
gen mean=r(mean);
xi: reg pres ${indepvar5}, cluster(schoolid), if etpteacher==1;
test ${indepvar5};
outreg using teachernamelisttracking.xls,nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean,"F test", r(F), "Prob >F", r(p) ) bdec(3) adec(4) append;
drop mean;

sum inclass if etpteacher==1&tracking==0;
gen mean=r(mean);
xi: reg inclass ${indepvar5}, cluster(schoolid), if etpteacher==1;
test ${indepvar5};
outreg using teachernamelisttracking.xls,nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean,"F test", r(F), "Prob >F", r(p) ) bdec(3) adec(4) append;


* STUDENT PRESENCE; 
use student_pres_data, clear;
gen etpteacher_tracking=etpteacher*tracking;
gen bottomhalf_tracking=bottomhalf*tracking;
global indepvar1="tracking bottomhalf_tracking bottomhalf girl etpteacher etpteacher_tracking bungoma realdate";

sum pres if tracking==0;
gen mean=r(mean);
xi: reg pres ${indepvar1}, cluster(schoolid);
testparm   ${indepvar1};
outreg using pupils_attendanceTRACK.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean in comp group", mean, "F test", r(F), "Prob >F", r(p) ) bdec(3) adec(3) replace;
drop mean;




*****************************************;
**************** TABLE VII: COMPLEXITY;
*****************************************;
use forpeerpapers, clear;
drop if attrition==1;
egen diff1_score=rsum(a1_correct a2_correct);
egen diff2_score=rsum(a3_correct a4_correct a5_correct);
replace diff2_score=diff2_score/9*6;
egen diff3_score=rsum(a6_correct a7_correct);


local i 1;
while `i'<4 {;
         reg diff`i'_score bottomhalf tracking bottomhalf_tracking agetest girl;
         est store DIFF`i';
         local i=`i'+1;
 };

suest DIFF1 DIFF2 DIFF3, cluster(schoolid);

test [DIFF1_mean]bottomhalf_tracking=[DIFF3_mean]bottomhalf_tracking;
test [DIFF1_mean]bottomhalf_tracking+[DIFF1_mean]tracking=[DIFF3_mean]bottomhalf_tracking+[DIFF3_mean]tracking;
test [DIFF1_mean]tracking=[DIFF3_mean]tracking;

sum diff1_score if tracking==0;
gen mean_letter=r(mean);
gen sd_letter=r(sd);

reg diff1_score  bottomhalf tracking bottomhalf_tracking  agetest girl, cluster(schoolid);
test tracking+bottomhalf_tracking==0;
gen F1=r(F);
gen P1=r(p);
outreg using complex1.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var',"F1", F1, "P1", P1) bdec(2) adec(2) replace;
drop F1  P1 ;
foreach var in diff2_score diff3_score letterscore24  wordscore spellscore24  sentscore24  {;
sum `var' if tracking==0;
gen mean_`var'=r(mean);
gen sd_`var'=r(sd);
reg `var' bottomhalf tracking bottomhalf_tracking  agetest girl , cluster(schoolid);
test tracking+bottomhalf_tracking==0;
gen F1=r(F);
gen P1=r(p);

outreg using complex1.xls, nor2 se nonote sigsymb(***,**,*) addstat("Mean", mean_`var', Std Dev, sd_`var',"F1", F1, "P1", P1) bdec(2) adec(2) append;
drop mean_`var' sd_`var';
drop F1  P1 ;
};

