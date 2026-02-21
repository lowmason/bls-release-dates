# CES State methodology: a complete reference for Bayesian nowcasting

**CES State and Area Employment (SAE) is a fundamentally different statistical product than CES National, and those differences directly affect how a Bayesian state space model should treat official state-level employment data.** The most consequential distinctions are: state estimates undergo full QCEW replacement during benchmarking rather than the national program's March-only wedge-back; birth/death factors are not independently modeled at the state level but instead raked down from national ARIMA forecasts; over 55% of the roughly 6,000 basic CES-SA series rely on small area models rather than direct sample estimation; and seasonal adjustment uses a unique two-step method that separately adjusts population-derived and sample-derived segments of each time series. These properties create measurement characteristics—revision magnitudes, seasonal factor instability, model-dependence—that differ materially from national CES and must be explicitly parameterized in any Bayesian measurement equation.

---

## How CES State differs from CES National and why it matters

CES National and CES State share the same underlying sample of approximately **121,000 businesses representing ~631,000 worksites**, but they produce estimates independently using different estimation structures, benchmarking procedures, and seasonal adjustment methods. The national program defines over 500 estimation cells by detailed NAICS industry. The state program uses a top-down approach where detailed all-employees estimates are constrained to values derived at the **Estimation Super Sector (ESS) level**, typically 2-digit NAICS. This prevents estimation noise in small-sample cells from propagating upward to total nonfarm.

BLS explicitly states that **state estimates are not forced to sum to the national total**. The "wedge" between sum-of-states and national CES arises from four sources: different estimation cell structures, different birth/death implementations, different benchmarking procedures, and different seasonal adjustment methods. BLS does not compile or publish a sum-of-states series, cautioning that such a series is "subject to a volatile error structure." For a Bayesian model reconciling state-level microdata signals with official statistics, this means treating the national-vs-state relationship as a soft constraint with an estimated discrepancy term rather than an identity.

The state program publishes later than national: **state data release on the fifth Friday after the 12th of the reference month**, roughly two weeks after the national Employment Situation. Metropolitan area data follow two Wednesdays after that. This timing gap creates a natural information advantage for any nowcasting system that can process payroll microdata before the official state release.

---

## Sample design, allocation, and coverage across states

The CES sample is drawn from the **Longitudinal Database (LDB)**, derived from QCEW's universe of approximately 10.7 million UI-covered business establishments. Private-sector establishments are stratified by **state × 13 industries × 8 size classes**, yielding 104 allocation cells per state. Allocation follows Neyman's optimum procedure: a fixed sample size per state is distributed across strata to minimize variance of the over-the-month change in total state employment. Allocation is reviewed roughly every five years by the CES Policy Council.

Sample sizes vary enormously. California's 13,550 UI accounts represent 67,560 establishments, while Vermont has 990 accounts covering 2,180 establishments. Critically, **establishments with 1,000+ employees are sampled with certainty** (weight = 1), and these certainty units, while comprising only 0.2% of all UI accounts, cover approximately **29% of total private employment**. This means payroll provider microdata that overrepresents large employers will correlate strongly with the certainty stratum of CES, potentially providing very precise signals for that component while being less informative about the small-establishment tail.

The government sample is **not probability-based**—it uses a quota design achieving roughly 70% universe employment coverage through direct payroll counts from government agencies. Government estimates are summed with total private to produce total nonfarm. For Bayesian modeling, the government component should be treated as having fundamentally different error properties than the private-sector sample-based component.

Sample rotation follows a quarterly enrollment scheme: four industry groups phase in across quarters, with minimum two-year tenure for sample units and swap-out after four or more consecutive years. Approximately **66% of the private CES sample overlaps year-to-year**, which creates serial correlation in sampling error that a state space model should account for.

---

## The weighted link relative estimator and robust estimation

The core estimator for all-employees (AE) employment at each estimation cell is the **robust weighted link relative (WLR)**:

**AÊ_c = [AÊ_p − Σ(ae*_p,j) − NCE] × [Σ(w_i × r_i × d_i × ae_c,i) / Σ(w_i × r_i × d_i × ae_p,i)] + Σ(ae*_c,j) + b_c + NCE**

The matched sample—units reporting in both the current and prior month—drives the link ratio. The ratio captures month-to-month change, which is then applied to the previous month's level estimate. Atypical units (strikes, disasters, extreme outliers) are removed from the ratio and added back directly. The birth/death factor **b_c** accounts for employment at establishments not yet on the sampling frame.

The Winsorization procedure for outlier detection operates on **weighted residuals** at the UI account level: d_i = w_i × (ae_c,i − R_t × ae_p,i), where R_t is the cell's sample link relative. Residuals are centered within size classes, sorted, and a cutoff value L is computed using a sequential procedure. For certainty units, an initial adjustment factor below 0.5 causes the unit to be reclassified as "atypical" and removed from the link ratio. For non-certainty units, the threshold is 0.3. A two-pass procedure runs the entire process twice, excluding first-pass atypicals during the second pass. Importantly, if the resulting estimate falls within historically observed bounds, the intervention is reversed—a safeguard against over-trimming during genuinely unusual economic periods.

For hours and earnings, CES uses a **weighted difference-link-and-taper estimator** with a 0.9/0.1 taper ensuring month-to-month changes are driven by matched sample differences while the level tracks the sample average. There is **no population benchmark for hours and earnings**—QCEW does not collect hours data—making outlier detection especially critical for these series.

---

## Small area models cover more than half of all CES-SA series

A cell's sample is deemed adequate for direct estimation only if it has either **≥30 unique UI accounts** or a minimum population of 3,000 with ≥50% sample coverage. Series failing this test are estimated using the **Small Area Model Generation 3 (SAM Gen3)**, implemented in January 2022. This model, a Bayesian nonparametric generalization of the Fay-Herriot model, uses linear regression linking direct survey estimates with the **same-month five-year average of relative employment change in benchmark data**. Unlike classical Fay-Herriot, SAM Gen3 relaxes the assumption that sampling variances are fixed and known.

The practical consequence is striking: **approximately 55% of the 6,000+ basic CES-SA series are model-based** rather than purely sample-driven. For a Bayesian nowcasting model, this means that for many state-industry cells, the official "data" already embeds model assumptions—particularly regression toward historical seasonal patterns. Payroll microdata signals may be more informative than the official estimates in precisely these small-domain cells, since the microdata captures actual current-month dynamics that the SAM Gen3 model partially smooths away.

Variance estimation for CES-SA uses **Generalized Variance Functions (GVFs)** rather than direct replication, connecting variance to employment size, number of respondents, and sample fraction. Published standard errors reflect **sampling error only** and do not capture model error for model-based series, birth/death forecast error, or nonsampling error. This means published confidence intervals systematically understate total uncertainty.

---

## Birth/death adjustment: national model, state-level raking

The net birth/death model addresses the structural lag between a business opening and its appearance on the CES sampling frame. The model has two components. First, **death imputation**: sample units going out of business are not reflected in estimation, effectively imputing to them the same trend as continuing firms. This offsets the missing birth employment without requiring explicit identification of business deaths. Second, an **ARIMA time series model** forecasts the residual between actual birth/death dynamics (observed retrospectively in QCEW data) and what the death imputation captures. The model uses five years of historical birth/death residual values derived from QCEW microdata.

At the state level, CES-SA **does not independently run birth/death ARIMA models**. Instead, national birth/death factors are **raked across states** proportional to each state's share of national employment within each 3-digit NAICS. This ratio-adjustment procedure means state-level birth/death factors are mechanically derived from the national model—they do not reflect state-specific business formation dynamics. During the COVID-19 pandemic, BLS modified the raking procedure by capping any state from receiving more than 2× its normal rake share and using zero-drop/zero-return proportions rather than employment shares.

Starting with the **2024 benchmark (February 2025)**, BLS added a regression component to the ARIMA model, exploiting the linear relationship between the natural log of the sample-based WLR and actual birth/death values from lagged QCEW. Effective with **January 2026 data**, this regression-enhanced model permanently replaced the pure ARIMA approach for all future monthly releases at both national and state levels. The modification was motivated by persistent, relatively large birth/death forecast errors since the 2020 benchmark—three consecutive years of overestimation totaling roughly **−266K (2023), −589K (2024), and −861K (2025)** in benchmark revisions.

Monthly birth/death magnitudes are large and highly seasonal: cumulative annual additions typically range from **200,000 to 1,400,000 jobs**. October and April typically see the largest positive factors (+350K to +425K), while January sees large negative factors (−100K to −120K). For a Bayesian model, the birth/death component represents a substantial source of systematic, predictable error in preliminary estimates—especially at economic turning points when the ARIMA model cannot anticipate regime changes.

---

## Benchmarking to QCEW: full replacement for states versus national wedge-back

The benchmarking difference between CES National and CES State is arguably the single most important distinction for vintage tracking systems. **CES National replaces only the March estimate** with the QCEW-derived benchmark level, then distributes the revision linearly across the preceding 11 months (the "wedge-back"). CES State, by contrast, **replaces every monthly estimate from April of the prior benchmark year through September of the current benchmark year** with direct QCEW population counts—approximately 18 months of full replacement. Only the October–December post-benchmark quarter uses re-estimated sample data anchored to the new September level.

The rationale is straightforward: for national aggregates, sampling error is small relative to the QCEW's own administrative noise, so the survey-based month-to-month change is considered the best estimate. For state and metro domains, **sampling error dominates**, making direct QCEW replacement preferable. This means that benchmarked state data from April through September is essentially administrative records data, not survey data—a fundamentally different data-generating process than the sample-based estimates that a nowcasting model tracks in real time.

QCEW data become available with a **~6-month lag**: Q1 data (January–March) are released in September, Q2 in December, Q3 in March, and Q4 in June. The state benchmark is finalized in **March of year Y+1**, covering data through September of year Y. Data from April–September are initially replaced during one benchmark cycle using preliminary QCEW, then **re-replaced** the following year with revised QCEW. This creates a double-revision structure.

Benchmark revision magnitudes at the state level are substantially larger than national. The **average absolute percentage revision across all states for total nonfarm is approximately 0.7%**, compared to 0.1% at the national level over the prior decade. Individual state revisions have ranged from **−2.4% to +1.8%** (September 2024), and metropolitan area revisions can reach ±6%. By industry, information-sector revisions average **4.9%** and professional/business services **2.5%** at the state level.

Several Federal Reserve Banks produce **early benchmark estimates** that incorporate QCEW data quarterly rather than annually. The Philadelphia Fed releases early benchmarks for all 50 states approximately one week after each QCEW quarterly release, and the Dallas Fed pioneered this approach in 1993. These early benchmarks substantially reduce the gap between preliminary CES estimates and final benchmarked values and may serve as useful intermediate signals in a nowcasting framework.

---

## Seasonal adjustment uses the unique two-step Berger-Phillips method

CES-SA time series are inherently **hybrid**: QCEW population data through the latest benchmark month, followed by sample data to the current month. Research by Berger and Phillips (1994, Dallas Fed) demonstrated that these two data sources exhibit **different seasonal patterns**, and applying a single seasonal adjustment model creates distortions at the splice point.

The two-step method works as follows. First, census-derived (QCEW) employment counts are seasonally adjusted using seasonal trends found in the population data. Second, sample-based estimates are independently adjusted using CES sample-based seasonal trends. The two series are **spliced together at the October re-estimate point**. This procedure, unique to CES-SA, has been in use since 1994.

CES-SA converted to **concurrent seasonal adjustment in March 2018** (with January 2018 data), where new seasonal factors are calculated every month using all data through the current month. The national program adopted concurrent adjustment in 2003—a 15-year lag. Before 2018, state seasonal factors were projected annually during benchmark processing and held fixed for the following year, introducing a source of systematic error as actual seasonal patterns deviated from projections.

The software is **X-13ARIMA-SEATS**, with REGARIMA models evaluating 11 survey-interval variables (one per month except March) to control for the 4- versus 5-week effect between reference periods. For statewide data, seasonally adjusted total nonfarm is an **indirect aggregate** of independently adjusted supersector components. For metropolitan areas, total nonfarm is adjusted **directly** at the aggregate level. Five years of seasonal factors are revised annually during benchmarking.

Prior adjustments for known nonseasonal events (Census hiring, strikes) have been applied since June 2020. The adjustment removes the event's rounded effect from NSA data before running X-13, then reincorporates it afterward. Outlier identification during concurrent processing relies on automatic AO/LS detection via t-tests supplemented by **analyst knowledge of local events**—a stricter critical value policy was found beneficial in research.

For the Bayesian measurement equation, the two-step method means that **seasonal factors applied to benchmarked months versus sample-based months are estimated from different distributions**. A state space model should either work with NSA data and model seasonality explicitly, or account for the fact that seasonal adjustment introduces a structural break at the benchmark splice point each year.

---

## Guaranteed publication levels and data granularity

Publication guarantees depend on geographic and employment size. **All states** and **MSAs with over 100,000 total nonfarm jobs** receive the full expanded supersector structure: total nonfarm broken into total private, goods-producing, and service-providing, with 10 supersectors including mining/logging, construction, manufacturing, wholesale trade, retail trade, transportation/utilities, information, financial activities, professional/business services, education/health, leisure/hospitality, other services, and three government levels (federal, state, local).

**MSAs below 100,000 jobs** receive only aggregate levels: total nonfarm, total private, goods-producing, service-providing, and government. Series beyond guaranteed levels must pass the sufficiency test (≥30 UI accounts or ≥3,000 universe employment with ≥50% sample coverage). At the statewide level, BLS supports model-based estimates for 11 NAICS sector series (transportation/warehousing, utilities, finance/insurance, real estate, professional services, management, administrative services, educational services, healthcare, arts/entertainment, accommodation/food services) if sample is insufficient.

---

## Revision patterns and vintage tracking implications

State CES data pass through a well-defined revision cascade with distinct statistical properties at each stage:

- **First preliminary (~3 weeks post-reference)**: Based on approximately **60% response rate** (down from ~70% pre-pandemic). Highest variance, most valuable for nowcasting signal extraction.
- **Second preliminary (one month later)**: Based on ~90% response rate. Substantial variance reduction.
- **Third/final monthly estimate (two months later)**: Based on ~95% response rate. Held constant until benchmark.
- **Annual benchmark (March Y+1)**: Full QCEW replacement for April(Y-1)–September(Y); re-estimation for October–December(Y); five years of SA data revised.
- **Second-year re-replacement**: April–September data re-replaced with final QCEW in the subsequent benchmark cycle.

The benchmark revision magnitude at the state level (**~0.7% average absolute**) is roughly **7× larger** than the national average. Revisions are systematically larger during turning points when the birth/death model fails to anticipate regime changes. The persistent overestimation pattern from 2023–2025 (cumulative downward revisions exceeding 1.7 million jobs nationally) suggests that any nowcasting model should incorporate a structural prior for mean-reverting birth/death forecast error, especially during periods when payroll microdata signals diverge from the birth/death model's seasonal ARIMA extrapolation.

For a vintage tracking system, the key insight is that **state-level benchmarked data (April–September) is fundamentally administrative records**, while post-benchmark data (October–current month) is survey-based with model components. The data-generating process changes discretely at the September/October boundary each year. A well-specified Bayesian model should allow different observation error variances and potentially different bias structures for these two regimes.

---

## Conclusion: design implications for Bayesian state space nowcasting

Five properties of CES-SA methodology create specific design requirements for a Bayesian model that reconciles payroll microdata with official statistics. First, **the birth/death component is raked from a national model, not estimated at the state level**, meaning state-level birth/death error is mechanically correlated across states and does not reflect state-specific business dynamics—payroll microdata may provide genuinely orthogonal information here. Second, **over 55% of basic series are model-based**, so official estimates in small domains already embed regression-to-historical-mean assumptions that microdata can potentially improve upon. Third, **the full QCEW replacement benchmarking means state data undergo a regime change from administrative to survey data each October**, requiring the measurement equation to accommodate heterogeneous error structures. Fourth, **the two-step seasonal adjustment creates a structural break in seasonal factors at the benchmark splice point**, which a model working with SA data must parameterize. Fifth, **state benchmark revisions averaging 0.7% (with individual states reaching ±2.4%) dwarf national revisions**, meaning vintage-conditional inference at the state level requires substantially wider measurement error priors than a national-only model would suggest. The recently enhanced birth/death model—now incorporating real-time WLR information via regression—may reduce these revision magnitudes going forward, but the structural features of state-level estimation remain fundamentally noisier than national aggregates.