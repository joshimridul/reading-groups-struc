# Quickstart

## What this is
A self-contained Python pipeline that replicates and extends the analysis of
cross-grade ability grouping in Liberia, starting from the **raw CSV files**.
Nothing depends on the old Stata `.dta` files.

## Requirements
```
pip install -r requirements.txt
```
Python 3.9+. All dependencies are standard scientific-Python packages
(pandas, numpy, statsmodels, matplotlib, scipy).

## How to run
Scripts are numbered and run in order. Each produces tables/figures in `output/`.

```bash
cd 3_Python/
python 00_clean.py            # Build analysis dataset from raw CSVs
python 01_reduced_form.py     # Phase 1: ITT effects (just randomization)
python 02_diagnostic.py       # Phase 2: Diagnostic reliability (R² by grade)
python 03_het_effects.py      # Phase 3: τ(s) — treatment effect by baseline score
python 04_mechanism.py        # Phase 4: Borusyak-Hull (peer effects β_P)
python 05_calibrate.py        # Phase 5: Back out ρ, compare to threshold
python 06_robustness.py       # Phase 6: Robustness checks
```

Or run everything:
```bash
for f in 0*.py; do python "$f"; done
```

## File map

| File | Purpose | Stata analogue |
|---|---|---|
| `config.py` | Paths, constants, cutoffs | Globals in `_master.do` |
| `utils.py` | Regression helpers, table formatters | — |
| `00_clean.py` | Raw CSV → analysis dataset | `3_L_AG_clean.do` + `4_L_AG_combine.do` + `4a_L_AG_prepare.do` |
| `01_reduced_form.py` | ITT on endline scores | `treat_effect_main.do` / `lib_fxmain.do` |
| `02_diagnostic.py` | Baseline→endline R², EB construction | `pretest_ability_eb.do` |
| `03_het_effects.py` | τ(s) by decile, interaction models | `lib_fxupper.do` / `lib_bldist.do` |
| `04_mechanism.py` | Borusyak-Hull: peers, distance, class size | `lib_struc.do` / `4a_L_AG_prepare.do` |
| `05_calibrate.py` | Structural: back out ρ, threshold | New |
| `06_robustness.py` | Alt samples, specs, placebo | New |

## Key design choices (departures from old pipeline)
1. **No inherited `.dta` files.** Everything from raw CSVs.
2. **Empirical Bayes ρ estimated from data**, not hardcoded at 0.20.
3. **Borusyak-Hull conditioning on E[P|s, T]** uses observed scores s,
   not latent ability θ. This is the identification: selection into tracks
   operates through s, so conditioning on E[P|s, T] removes confounding.
4. **Linear propensity control** (not strata FE) following Abdulkadiroglu
   et al. (2017). Gains degrees of freedom with ~54 schools.
5. **Explicit sample-restriction log** printed by `00_clean.py`.

## For Stata users
Each Python operation has a comment explaining the Stata equivalent, e.g.:
```python
# Stata: bys academycode grade: egen peer_mean = mean(score_bl)
df['peer_mean'] = df.groupby(['academycode', 'grade'])['score_bl'].transform('mean')
```
See SPECIFICATIONS.md for the econometric details.
