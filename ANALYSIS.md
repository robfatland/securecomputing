\newpage

<!-- SOURCE: ANALYSIS.md -->

# Analysis and Narrative

## Narrative

A clinical research team studying nephrolithiasis (kidney stones) in 11,000 patients discovers that combining four independent data modalities — electronic health records, crystallographic composition analysis, genomic sequencing, and longitudinal lab results — produces an unrealistically clean predictive model for stone recurrence and type. The synthetic data demonstrates what a "best case" multi-modal integration looks like: every signal is present, every correlation is detectable, and the noise floor is low enough that even modest statistical methods find the story.

## Analysis Overview

The analysis proceeds in stages, each building on the outputs of the prior:

1. **Data Loading and Cohort Summary** — Load PD0 (OMOP), characterize the patient population, verify linkage across datasets via MRN
2. **Stone Composition Profiling (PD1)** — Parse CIF files, extract mineral phase percentages from PXRD patterns and FTIR absorption bands
3. **Genomic Correlation (PD2)** — Map pathogenic variants in stone-associated genes to stone type; quantify genotype-phenotype concordance
4. **Lab Value Trajectories (PD3)** — Identify longitudinal lab patterns (urine calcium, oxalate, citrate, pH) that precede stone episodes
5. **Multi-Modal Integration** — Combine all four data types into a unified patient view; demonstrate that the synthetic correlations are recoverable
6. **Predictive Model** — Build a classifier for stone type from genomics + labs alone (without requiring crystallography), achieving unrealistically high accuracy as a demonstration of the data coherence

## Detailed Methods and Results

*To be developed as analysis notebooks are completed. Each section below will be populated with figures, tables, and interpretation.*

### Step 1: Data Loading and Cohort Summary

*(In progress — see `analysis/notebooks/analysis_main.ipynb`)*

### Pathogenic Variants

A **pathogenic variant** is a specific change (mutation) in a person's DNA sequence that has been determined to cause or significantly contribute to disease.

Every person has millions of genetic variants — places where their DNA differs from the reference genome. The vast majority are **benign** (no health impact) or **variants of uncertain significance** (VUS — not enough evidence either way).

A variant is classified as **pathogenic** when there's strong evidence — from functional studies, family segregation, population frequency data, and clinical observations — that it disrupts gene function in a way that causes disease.

In the context of this synthetic data: a pathogenic variant in `SLC3A1` or `SLC7A9` means the patient has a mutation that impairs cystine transport in the kidneys, leading to cystine stone formation. A pathogenic variant in `AGXT` means the enzyme that breaks down oxalate is deficient, leading to calcium oxalate stones.

The classification system (benign → likely benign → VUS → likely pathogenic → pathogenic) follows the ACMG/AMP guidelines — a standardized framework used by clinical genetics labs worldwide.

In the PD2 VCF files, the `PATHOGENIC` flag is a simplification: the synthetic data generator tagged 1–4 variants per stone patient as definitively disease-causing, placed in the appropriate genes for their stone type. Real clinical data would have more ambiguity (VUS, incomplete penetrance, polygenic contributions).

#### Why Stone Type d shows >100% pathogenic variant frequency for SLC22A12

The heatmap cell for stone type `d` (pure_uric_acid) and gene `SLC22A12` shows ~103%. This exceeds 100% because the normalization denominator is the number of *patients* with that primary stone type, while the numerator is the number of *pathogenic variants* in that gene across those patients.

A single patient can carry multiple pathogenic variants in the same gene (e.g., compound heterozygosity — one pathogenic variant on each copy of the chromosome). The synthetic data generator assigns 1–4 pathogenic variants per stone patient, and some patients receive more than one variant in `SLC22A12`. When you divide total SLC22A12 pathogenic variants by total pure_uric_acid patients, you get a ratio slightly above 1.0.

This is not a bug — it reflects the biological reality that recessive conditions (like uric acid stones from SLC22A12 loss-of-function) often require two hits (one per allele). In clinical genomics, >100% variant frequency per gene per cohort is expected whenever compound heterozygotes or homozygotes are present.

#### Reading the heatmap: a primer

A **variant** in this context is a single nucleotide change — one letter of DNA that differs from the reference human genome at a specific position. Every person carries millions of variants; the vast majority are harmless. A **pathogenic** variant is one that lands in a critical spot in a gene, breaking the protein that gene produces.

The heatmap percentage is *not* about the length of the gene or how much of it is "wrong." It counts:

- Take all patients with a given stone type (e.g., 742 uric acid stone patients)
- Count the total number of pathogenic variants in a specific gene across those patients
- Divide: (total pathogenic variants) / (number of patients) × 100

So "103%" means: across 742 patients, there are ~765 pathogenic SLC22A12 variants — more variants than patients.

**Why can this exceed 100%?** Every person has two copies of each gene (one from each parent). For SLC22A12, a single working copy is sufficient — you need *both* copies broken to develop uric acid stones. Many of these patients therefore carry two separate pathogenic variants in SLC22A12 (one per chromosome). The variant count exceeds the patient count.

An alternative reading of the table — "what fraction of patients carry at least one pathogenic variant in this gene" — would cap at 100% but loses the information about compound heterozygosity.

### Step 4: Lab Value Trajectories

The Step 4 box plots show the distribution of six key urine/serum chemistry values, broken out by primary stone type. Each box represents the interquartile range (25th–75th percentile) of that lab measurement across all visits for patients of that stone type; the line inside is the median; whiskers extend to 1.5× the interquartile range; dots beyond are outliers.

**What the charts reveal (by design — the synthetic data was generated with these correlations):**

- **Urine Calcium** — Elevated in calcium stone formers (types a, b, c: pure COM, mixed COM/COD, COM + calcium phosphate). Normal in uric acid and cystine patients. Elevated 24-hour urine calcium is called *hypercalciuria* and is the single most common metabolic abnormality in calcium stone formers.

- **Urine Oxalate** — Expected to be elevated in oxalate-dominant stone formers (types a, b). However, the Step 4 box plots show urine oxalate is flat across all stone types — **this is a data generation bug.** The `generate_pd3.py` script in `securecomputing-datagen` did not implement the oxalate shift for COM/COD patients. See the to-do item below.

- **Urine Citrate** — LOW in calcium stone formers. Citrate is a natural inhibitor of calcium crystallization in urine. *Hypocitraturia* (low citrate) removes this protective effect and is a treatable risk factor.

- **Urine pH** — The most discriminating single test. Uric acid stones form in acidic urine (pH < 5.5); calcium phosphate and struvite stones form in alkaline urine (pH > 6.5). The box plots should show a clear separation between uric acid (low pH) and struvite/brushite (high pH) stone types.

- **Uric Acid (serum)** — Elevated in uric acid stone formers. *Hyperuricemia* can also contribute to calcium stone formation by providing nucleation sites.

- **Urine Cystine** — Dramatically elevated ONLY in cystinuria patients (type j). Normal in all other stone types. This is the most binary signal in the dataset — cystine stones are caused by a specific genetic defect (SLC3A1/SLC7A9) that prevents cystine reabsorption in the kidney.

**Clinical relevance:** In real practice, these labs guide treatment decisions. High urine calcium → thiazide diuretics. Low citrate → potassium citrate supplementation. Low urine pH → alkalinization. High cystine → tiopronin + high fluid intake. The synthetic data reproduces these patterns cleanly, making the stone type predictable from labs alone — which is unrealistically clean compared to real patient data where multiple metabolic abnormalities overlap and treatment effects confound measurements.

---

## Data Generation Fixes (Resolved)

### ~~Fix urine oxalate correlation in PD3~~ ✓ DONE (verified July 2026)

**Resolution:** The `STONE_LAB_SHIFTS` dictionary in `securecomputing-datagen/generators/generate_pd3.py` includes oxalate shifts for COM/COD stone types. The generated data (`pd3/lab_results.csv`) confirms differentiation:

| Group | n | Mean (mg/day) | SD |
|-------|---|---------------|-----|
| COM types (pure_com, mixed_com_cod, pure_cod, com_calcium_phosphate) | 46,348 | 53.7 | 15.5 |
| Uric acid types | 4,311 | 28.0 | 8.0 |
| No stones | 8,403 | 28.2 | 8.0 |
| Other stones | 3,496 | 27.6 | 8.2 |

COM/COD formers show ~2× normal mean urine oxalate, consistent with hyperoxaluria. Non-oxalate types cluster at the normal population mean (~28 mg/day). Fix was applied, data regenerated, and synced to S3.

### Step 6: Predictive Model

A Random Forest classifier trained on genomics (pathogenic variant counts per gene) + labs (mean stone panel values) — without crystallography — achieves ~64% overall accuracy across 10 stone type classes. For context, random guessing would yield ~10%.

#### Why 64% and not 95%

The model correctly identifies stone types with unique lab/gene signatures at high accuracy:
- **Cystine** (~100%): uniquely elevated urine cystine + SLC3A1/SLC7A9 variants
- **Pure uric acid** (~90%): low urine pH + elevated serum uric acid + SLC22A12 variants
- **Struvite** (~85%): high urine pH + elevated WBC

But it confuses calcium oxalate subtypes with each other:
- **pure_com** vs **mixed_com_cod** vs **pure_cod**: All three have elevated urine calcium, elevated oxalate, and low citrate. The only reliable differentiator is the COM:COD ratio in crystallography — which this model deliberately excludes.
- **uric_acid_com** shares features with both uric acid and calcium oxalate families.
- **mixed_other** has weak/generic signals by design.

This is clinically realistic: you often cannot distinguish COM from COD from labs alone — you need the stone composition analysis. The model demonstrates that genomics + labs predict the *family* of stone (calcium vs uric acid vs cystine vs struvite) with high accuracy, but distinguishing subtypes within a family requires crystallographic analysis (PD1).

#### Reading the confusion matrix

A confusion matrix is a table where:
- Each **row** is an actual (true) stone type
- Each **column** is what the model predicted
- The cell at row *i*, column *j* shows how many patients who actually had type *i* were predicted as type *j*

A perfect model has all values on the diagonal (predicted = actual). Off-diagonal values are mistakes.

**"% per row"** means each row is normalized to sum to 100%. For example, row `a` (pure_com) showing 72% on the diagonal means 72% of actual pure_com patients were correctly predicted; the remaining 28% were misclassified as other types (typically mixed_com_cod or pure_cod — the neighboring calcium oxalate subtypes).

Empty cells are zeros — the model never confused those two types. Only values >1% are annotated to keep the figure readable.

### Limitations and Future Directions

#### Feature importance

The feature importance chart shows labs entirely dominating genes. This is expected: lab features are continuous-valued (many distinct splitting points for the decision trees) while gene features are mostly binary (0 or 1 pathogenic variant), giving the Random Forest more discriminating power from labs. In real data, genomic features might carry more weight because lab values are noisier and confounded by treatment effects.

#### The 0-episode patients

The cohort contains 2,241 patients with zero stone episodes and 9,031 with at least one. A natural clinical question is: "Why did some patients form stones while others didn't? Are the 0-episode patients candidates for stones who got lucky?"

In real clinical research, this is one of the most important questions — distinguishing at-risk patients who haven't yet developed disease is the basis of predictive and preventive medicine. You'd look for patients with borderline labs, heterozygous carriers of stone-associated genes, or dietary/environmental risk factors that haven't yet tipped over into stone formation.

**In this synthetic data, the question is not meaningful.** The data generator assigned stone status randomly (80% stones, 20% no stones) *before* generating any lab values or genetic variants. Labs and variants were then generated *conditioned on* the assignment: stone patients received shifted lab values and pathogenic variants; no-stone patients received population-normal labs and only benign background variants. The 0-episode patients aren't lucky survivors of underlying risk — they're a control group with no synthetic risk signals by construction.

A more sophisticated data generator could model partial penetrance (carrying a pathogenic variant but not developing disease), protective factors (high citrate compensating for high calcium), and time-to-event dynamics (risk accumulating over years before first episode). This would make the 0-episode patients genuinely interesting to analyze and would support time-to-event (survival) modeling. This is a potential future enhancement to the `securecomputing-datagen` pipeline.

---

*End of ANALYSIS.md — Next: DIAGRAMS.md*
