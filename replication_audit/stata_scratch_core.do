/*
Scratch Stata rebuild for the audit.

This intentionally avoids the shipped masters because several three-country
scripts overwrite 4_Stata2/output/ and copy directly to Overleaf. Outputs here
go only to replication_audit/stata_scratch/.
*/

clear all
set more off
set matsize 5000
version 19
set scheme s1mono

global root "/Users/mriduljoshi/Github/reading-groups-struc"
global raw  "$root/2_Data/1_Raw"
global do   "$root/4_Stata2"
global out  "$root/replication_audit/stata_scratch"

cap mkdir "$out"

global lib_cutoff_g12 = 23
global lib_cutoff_g34 = 14
global lib_cohort_threshold "2016-11-22"

global ke_cutoff_g1 = 40
global ke_cutoff_g2 = 35

di _n "{hline 70}"
di "Scratch Stata audit run: Kenya/Liberia core"
di "{hline 70}"
di "Output directory: $out"

do "$do/00_clean_liberia.do"
do "$do/00_clean_kenya.do"
do "$do/01_descriptives.do"
do "$do/02_main_analysis.do"
do "$do/03_diagnostics.do"
do "$do/04_structural.do"
do "$do/06_robustness.do"
do "$do/07_lesson_completion.do"

di _n "{hline 70}"
di "Scratch Stata audit run complete."
di "{hline 70}"
