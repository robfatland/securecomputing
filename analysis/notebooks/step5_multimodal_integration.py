"""
Step 5: Multi-Modal Integration
=================================
Combine all four data types (PD0 EHR, PD1 composition, PD2 genomics, PD3 labs)
into a single unified patient-level DataFrame. Demonstrate that the synthetic
correlations across modalities are internally consistent and recoverable.

Outputs:
- integrated_df: one row per patient with features from all four data sources
- Correlation matrix showing cross-modal feature relationships
- Figure: multi-panel correlation heatmap with key

Terminology:
- Multi-modal: using data from multiple independent measurement types
- Feature: a single measurable property extracted from a data source
- Concordance: agreement between independent measurements of the same underlying truth
"""

import os
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.path.expanduser("~/securecomputing-data"))
PD0_DIR = DATA_DIR / "pd0"
PD1_DIR = DATA_DIR / "pd1"
PD2_DIR = DATA_DIR / "pd2"
PD3_PATH = DATA_DIR / "pd3" / "lab_results.csv"

# ---------------------------------------------------------------------------
# Load base cohort (from Step 1 logic)
# ---------------------------------------------------------------------------
print("Step 5: Building multi-modal integrated patient view...")

person_df = pd.read_csv(PD0_DIR / "person.csv")
phi_mapping = pd.read_csv(PD0_DIR / "phi_mapping.csv")
patient_stones = pd.read_csv(PD0_DIR / "patient_stones.csv")

# Build base cohort
cohort_df = person_df.merge(phi_mapping[["person_id", "mrn"]], on="person_id", how="left")

# Primary stone type
stone_episodes = patient_stones[patient_stones["stone_type"] != "none"]
primary_stones = stone_episodes.groupby("mrn").agg(
    n_episodes=("episode_number", "nunique"),
    primary_stone_type=("stone_type", "first")
).reset_index()

cohort_df = cohort_df.merge(primary_stones, on="mrn", how="left")
cohort_df["has_stones"] = cohort_df["n_episodes"].notna()
cohort_df["n_episodes"] = cohort_df["n_episodes"].fillna(0).astype(int)

print(f"  Base cohort: {len(cohort_df):,} patients")

# ---------------------------------------------------------------------------
# PD1 features: dominant mineral percentage
# ---------------------------------------------------------------------------
print("  Extracting PD1 features (composition)...")

import json
import re

composition_pattern = re.compile(r"^# Composition:\s*(\{.*\})\s*%?")
mrn_cif_pattern = re.compile(r"^# Patient MRN:\s*(\S+)")

# For integration, take the composition from the first episode per patient
pd1_records = []
seen_mrns = set()

for cif_path in sorted(PD1_DIR.glob("*.cif")):
    mrn = None
    composition = None
    with open(cif_path, "r") as f:
        for line in f:
            if not line.startswith("#"):
                break
            m = mrn_cif_pattern.match(line)
            if m:
                mrn = m.group(1)
            m = composition_pattern.match(line)
            if m:
                try:
                    composition = json.loads(m.group(1))
                except json.JSONDecodeError:
                    composition = {}
    if mrn and mrn not in seen_mrns and composition:
        seen_mrns.add(mrn)
        # Extract dominant mineral fraction
        max_mineral = max(composition, key=composition.get) if composition else None
        max_pct = composition.get(max_mineral, 0) if max_mineral else 0
        pd1_records.append({
            "mrn": mrn,
            "dominant_mineral": max_mineral,
            "dominant_pct": max_pct,
            "n_minerals": len(composition),
        })

pd1_df = pd.DataFrame(pd1_records)
print(f"    PD1 features for {len(pd1_df):,} patients")

# ---------------------------------------------------------------------------
# PD2 features: pathogenic variant count and gene list
# ---------------------------------------------------------------------------
print("  Extracting PD2 features (genomics)...")

mrn_vcf_pattern = re.compile(r"^##patient_mrn=(\S+)")
pd2_records = []

for vcf_path in sorted(PD2_DIR.glob("*.vcf")):
    mrn = None
    pathogenic_count = 0
    genes = set()
    with open(vcf_path, "r") as f:
        for line in f:
            if line.startswith("##"):
                m = mrn_vcf_pattern.match(line)
                if m:
                    mrn = m.group(1)
                continue
            if line.startswith("#"):
                continue
            if "PATHOGENIC" in line:
                pathogenic_count += 1
                gene_match = re.search(r"GENE=(\w+)", line)
                if gene_match:
                    genes.add(gene_match.group(1))
    pd2_records.append({
        "mrn": mrn,
        "pathogenic_variant_count": pathogenic_count,
        "pathogenic_gene_count": len(genes),
        "has_pathogenic": pathogenic_count > 0,
    })

pd2_df = pd.DataFrame(pd2_records)
print(f"    PD2 features for {len(pd2_df):,} patients")
print(f"    Patients with pathogenic variants: {pd2_df['has_pathogenic'].sum():,}")

# ---------------------------------------------------------------------------
# PD3 features: mean stone panel values per patient
# ---------------------------------------------------------------------------
print("  Extracting PD3 features (mean lab values)...")

labs_df = pd.read_csv(PD3_PATH)
stone_panel = labs_df[labs_df["panel"] == "stone_panel"]

# Pivot: mean value per patient per test
pd3_features = (
    stone_panel.groupby(["mrn", "test_code"])["value"]
    .mean()
    .reset_index()
    .pivot(index="mrn", columns="test_code", values="value")
    .reset_index()
)

# Prefix columns to identify source
pd3_features.columns = ["mrn"] + [f"lab_{c}" for c in pd3_features.columns[1:]]
print(f"    PD3 features for {len(pd3_features):,} patients")

# ---------------------------------------------------------------------------
# Merge all modalities into integrated DataFrame
# ---------------------------------------------------------------------------
print("\n  Merging all modalities...")

integrated_df = cohort_df[["mrn", "person_id", "has_stones", "n_episodes", "primary_stone_type"]].copy()
integrated_df = integrated_df.merge(pd1_df, on="mrn", how="left")
integrated_df = integrated_df.merge(pd2_df, on="mrn", how="left")
integrated_df = integrated_df.merge(pd3_features, on="mrn", how="left")

print(f"  Integrated DataFrame: {len(integrated_df):,} patients × {len(integrated_df.columns)} features")
print(f"  Columns: {list(integrated_df.columns)}")

# ---------------------------------------------------------------------------
# Completeness check
# ---------------------------------------------------------------------------
print("\n--- Data Completeness ---")
print(f"  Patients with PD1 data (composition): {integrated_df['dominant_mineral'].notna().sum():,}")
print(f"  Patients with PD2 data (genomics): {integrated_df['pathogenic_variant_count'].notna().sum():,}")
print(f"  Patients with PD3 data (labs): {integrated_df['lab_urine_calcium'].notna().sum():,}")

stone_only = integrated_df[integrated_df["has_stones"]]
complete = stone_only.dropna(subset=["dominant_mineral", "pathogenic_variant_count", "lab_urine_calcium"])
print(f"  Stone patients with ALL modalities: {len(complete):,} / {len(stone_only):,} "
      f"({len(complete)/len(stone_only)*100:.1f}%)")

# ---------------------------------------------------------------------------
# Correlation matrix (numeric features, stone patients only)
# ---------------------------------------------------------------------------
print("\n  Computing cross-modal correlation matrix...")

numeric_cols = [c for c in integrated_df.columns
                if c.startswith("lab_") or c in ("n_episodes", "dominant_pct",
                                                  "pathogenic_variant_count", "n_minerals")]

corr_df = stone_only[numeric_cols].corr()

# ---------------------------------------------------------------------------
# Figure: correlation heatmap
# ---------------------------------------------------------------------------
print("  Generating correlation heatmap...")

fig = plt.figure(figsize=(12, 10))

ax = fig.add_subplot(4, 1, (1, 3))

im = ax.imshow(corr_df.values, aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1)

ax.set_xticks(range(len(corr_df.columns)))
ax.set_xticklabels(corr_df.columns, rotation=45, ha="right", fontsize=8)
ax.set_yticks(range(len(corr_df.columns)))
ax.set_yticklabels(corr_df.columns, fontsize=8)
ax.set_title("Cross-Modal Feature Correlation (Stone Patients)", fontsize=11)

plt.colorbar(im, ax=ax, label="Pearson correlation", shrink=0.8)

# Annotate strong correlations
for i in range(len(corr_df)):
    for j in range(len(corr_df)):
        val = corr_df.iloc[i, j]
        if abs(val) > 0.3 and i != j:
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=6,
                    color="white" if abs(val) > 0.6 else "black")

# Key panel
key_text = (
    "Feature sources:\n"
    "  lab_*          = PD3 mean stone panel values (per patient, across all visits)\n"
    "  dominant_pct   = PD1 dominant mineral percentage (from first CIF file)\n"
    "  n_minerals     = PD1 number of mineral phases detected\n"
    "  pathogenic_variant_count = PD2 total pathogenic variants\n"
    "  n_episodes     = PD0 number of stone episodes\n"
    "\n"
    f"  Stone patients with complete data across all modalities: "
    f"{len(complete):,} / {len(stone_only):,} ({len(complete)/len(stone_only)*100:.1f}%)"
)

ax_key = fig.add_subplot(4, 1, 4)
ax_key.axis("off")
ax_key.text(0.0, 0.95, key_text, transform=ax_key.transAxes,
            fontsize=8, fontfamily="monospace", verticalalignment="top")

plt.tight_layout()
plt.savefig("step5_multimodal_integration.png", dpi=150, bbox_inches="tight")
plt.show()

print("\n[Step 5 complete] Correlation heatmap saved to step5_multimodal_integration.png")
print(f"  integrated_df available: {len(integrated_df):,} patients × {len(integrated_df.columns)} features")
