
/*==========================================================================

Title: 0_master.do 
Author: Mridul Joshi
Date: Wed Nov 17 12:05:15 2021

Description: Master do-file for Kenya and Liberia Bridge ability-grouping analysis

===========================================================================*/

clear all
version 16.0
set more off
pause off
cap log close 


* ===================================================================== *
* -----------------     	  Set path globals        ----------------- *
* ===================================================================== *
 
if "`c(username)'" == "mriduljoshi" {

	global maindir 	"/Users/mriduljoshi/Dropbox/Bridge TARL/AbilityGrouping"
	global gitdir   "/Users/mriduljoshi/Github/AbilityGrouping"
	*global outdir	"/Users/mriduljoshi/Dropbox/Overleaf/Reading groups/Tables_combined"
	global outdir	"/Users/mriduljoshi/Dropbox/Apps/Overleaf/Reading groups/Liberia2024"


}


if "`c(username)'" == "ggray" {

	global maindir 	"C:/Users/ggray/Dropbox/Bridge TARL/AbilityGrouping"
	global gitdir   ""
	global outdir	"C:/Users/ggray/Dropbox/Overleaf/Reading groups/Tables_combined"

}



global dodir	"${gitdir}/1_Do"
global rawdir 	"${maindir}/2_Data/1_Raw"
global datadir	"${maindir}/2_Data/2_Cleaned"



* ===================================================================== *
* -----------------     	  Kenya cleaning          ----------------- *
* ===================================================================== *

do "${dodir}/1_K_AG_clean.do"
do "${dodir}/2_K_AG_combine.do"
do "${dodir}/2a_K_AG_prepare.do"

* ===================================================================== *
* -----------------     	 Liberia cleaning         ----------------- *
* ===================================================================== *

do "${dodir}/3_L_AG_clean.do"
do "${dodir}/4_L_AG_combine.do"
do "${dodir}/4a_L_AG_prepare.do"


* ===================================================================== *
* -----------------     	       Analysis           ----------------- *
* ===================================================================== *

do "${dodir}/5_descriptives.do"

do "${dodir}/6_attrition.do"

do "${dodir}/7_effect_testscores.do"

do "${dodir}/8_effect_dispersion.do"

do "${dodir}/9_structural_pooled.do"

do "${dodir}/10_structural_finalscores.do"

do "${dodir}/11_structural_balance.do"










