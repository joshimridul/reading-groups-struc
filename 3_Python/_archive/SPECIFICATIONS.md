# Econometric Specifications

## Experimental design

Two parallel cluster-randomised experiments in Bridge Liberia schools (2019):

- **Experiment 1 (Grades 3–4):** Academies randomised to track G3+G4 students
  into two reading groups by baseline literacy score (cutoff = 14).
- **Experiment 2 (Grades 1–2):** Same design for G1+G2 (cutoff = 23).

Randomisation stratified by (academy cohort year × grade group).
Treatment unit: academy–grade-group. ~54 academies in the analysis sample.

## Notation

| Symbol | Meaning |
|---|---|
| $Y_i$ | Standardised endline score (by grade, control-group mean/SD) |
| $T_j$ | Treatment indicator for academy $j$'s grade group |
| $s_i$ | Observed baseline score |
| $\theta_i$ | True (latent) ability: $s_i = \theta_i + u_i$ |
| $p_t$ | Propensity score $\Pr(T=1 \mid \text{strata})$ |
| $P_i$ | Realised mean peer score (leave-self-out) |
| $M_i$ | Realised distance from median instruction |
| $C_i$ | Realised class size |
| $\hat\theta_i^{EB}$ | Empirical Bayes predicted ability |
| $\rho$ | Reliability ratio $\text{Var}(\theta)/\text{Var}(s)$ |

---

## Phase 1: Reduced-form ITT

$$Y_i = \alpha + \beta\, T_j + \gamma\, \hat\theta_i^{EB} + \delta\, p_t + \varepsilon_i$$

- $\beta$ = intent-to-treat effect.
- Controls: EB predicted ability (or standardised BL score), linear propensity.
- Cluster SE at academy–grade-group level (`ggroup`).
- Run separately: Stacked (all grades), G3–4, G1–2.

**Why linear propensity instead of strata FE?** With ~54 schools and 4 strata,
FE consumes degrees of freedom. A linear control for $p_t$ is sufficient for
unconfoundedness (Abdulkadiroglu et al. 2017, Econometrica). Results are
robust to FE.

---

## Phase 2: Diagnostic reliability

### Test–retest R²
In the **control group only** (no treatment contamination):

$$Y_i^{EL} = a + b\, s_i^{BL} + e_i \qquad \text{by grade}$$

$R^2$ of this regression = an upper bound on the signal in the baseline test.
Also compute BL→ML and ML→EL to assess the full information structure.

### Empirical Bayes predicted ability
Given $s_i = \theta_i + u_i$ with $u_i \sim N(0, \sigma_u^2)$:

$$\hat\theta_i^{EB} = \rho \cdot s_i + (1 - \rho) \cdot \bar{s}_g$$

where $\rho = \sigma_\theta^2 / (\sigma_\theta^2 + \sigma_u^2)$ is estimated from
the baseline–midline correlation in the control group within each grade, and
$\bar{s}_g$ is the control-group grade mean.

---

## Phase 3: Treatment effect heterogeneity τ(s)

### Non-parametric: effects by decile
Partition students into deciles of $s_i$ within grade. Estimate Phase 1 spec
within each decile. Plot coefficients with 95% CIs.

### Parametric: interaction with upper-group indicator
$$Y_i = \alpha + \beta_1 T_j + \beta_2 (T_j \times H_i) + \beta_3 H_i + \delta\, p_t + \varepsilon_i$$

where $H_i = \mathbb{1}\{s_i > \text{cutoff}\}$ (assigned to upper reading group).

$\beta_1$ = effect on lower group. $\beta_1 + \beta_2$ = effect on upper group.

---

## Phase 4: Borusyak-Hull mechanism analysis

### The identification problem
Treatment changes three things simultaneously:
1. **Peers** $P_i$: who you sit with
2. **Mismatch** $M_i$: distance from instructional level
3. **Class size** $C_i$

These are endogenous: a student's peer group depends on their score $s_i$.

### The key insight
Selection into tracks operates through **observed scores** $s$, not true
ability $\theta$. Track assignment = $T_j \times \mathbb{1}\{s_i > c\}$.
So the peer group is a deterministic function of $(s_i, T_j, \text{academy})$.

We can compute the **expected treatment dose** for every student:

$$\mathbb{E}[P_i \mid s_i, \text{academy}] = p_t \cdot P_i^{T=1} + (1 - p_t) \cdot P_i^{T=0}$$

where $P_i^{T=1}$ = leave-self-out mean peer score in the reading group that
student $i$ would be assigned to under treatment, and $P_i^{T=0}$ = same
under control (i.e., within their grade).

### Under scripted instruction
Bridge teachers follow tablet-delivered lesson plans. The script is
grade-specific (or reading-group-specific under treatment), not teacher-chosen.
So mismatch $M_i$ is pinned down by the student's assigned level:
**conditional on grade/reading-group assignment, $M$ doesn't vary with
unobserved teacher effort**. This means controls for $\mathbb{E}[M \mid s, T]$
absorb the mismatch channel, letting us identify peer effects $\beta_P$
separately.

### Specification

$$Y_i = \alpha + \beta_P P_i + \beta_M M_i + \beta_C C_i + \gamma_P \mathbb{E}[P_i] + \gamma_M \mathbb{E}[M_i] + \gamma_C \mathbb{E}[C_i] + \delta\, \hat\theta_i^{EB} + \lambda\, p_t + \varepsilon_i$$

where all expectations condition on $(s_i, \text{academy}, \text{grade})$.

**Interpretation of $\beta_P$:** Among students with the same expected peer
exposure, those who *realise* higher peer quality (because their academy was
randomly treated/not treated) score $\beta_P$ SD higher per unit of peer quality.

---

## Phase 5: Model calibration

### Signal extraction
From Phase 2 we have $\hat\rho$ by grade. The threshold reliability for
beneficial tracking depends on the variance ratio:

$$\rho^* = 1 - \frac{\text{Var}(\text{between-grade})}{\text{Var}(\text{total})}$$

If $\rho < \rho^*$, the test is too noisy: tracking increases mismatch on net.

### Decomposition
Using the structural estimates from Phase 4 and the observed changes in
$P$, $M$, $C$ from treatment:

$$\hat\beta^{ITT} \approx \beta_P \cdot \Delta P + \beta_M \cdot \Delta M + \beta_C \cdot \Delta C$$

Check whether this accounting identity holds.

---

## Phase 6: Robustness

1. **Strata FE instead of linear propensity**
2. **Drop academies with no BL scores in one grade**
3. **Use raw BL score instead of EB prediction as control**
4. **Trim extreme BL scores (top/bottom 5%)**
5. **Lee bounds for selective attrition**
6. **Permutation inference (randomisation inference on treatment)**

---

## Clustering and inference

All standard errors clustered at `ggroup` = (academy × grade-group [G1–2 or G3–4]).
This is the level of treatment assignment. With ~108 clusters (54 academies ×
2 grade groups, minus some singletons), cluster-robust inference is standard.

Stars: * p<0.10, ** p<0.05, *** p<0.01 (two-sided).
