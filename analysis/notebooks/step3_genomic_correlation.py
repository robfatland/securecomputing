"""
Step 3: Genomic Correlation (PD2)
==================================
Parse VCF files from PD2, extract pathogenic variants in stone-associated genes,
and quantify genotype-phenotype concordance with stone type assignments.

Outputs:
- variants_df: DataFrame of all pathogenic variants (MRN, gene, chrom, pos)
- Concordance statistics: how well gene variants predict stone type
- Figure: gene variant frequency by stone type (heatmap) with key

Terminology:
- VCF: Variant Call Format (standard genomics file for reporting sequence variations)
- GRCh38: Human genome reference assembly (version 38)
- Pathogenic: a variant that causes or contributes to disease
- Stone-associated genes (10): SLC3A1, SLC7A9, CLCN5, CASR, VDR, AGXT, GRHPR, HOGA1, SLC22A12, APRT
- COM: Calcium Oxalate Monohydrate (whewellite)
- COD: Calcium Oxalate Dihydrate (weddellite)
"""

import os
import re
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.path.expanduser("~/securecomputing-data"))
PD2_DIR = DATA_DIR / "pd2"
PD0_DIR = DATA_DIR / "pd0"

# Known stone-associated genes and their expected stone type correlations
GENE_STONE_MAP = {
    "SLC3A1": "cystine",
    "SLC7A9": "cystine",
    "CLCN5": "com_calcium_phosphate",
    "CASR": "com_calcium_phosphate",
    "VDR": "pure_com",
    "AGXT": "pure_com",
    "GRHPR": "mixed_com_cod",
    "HOGA1": "mixed_com_cod",
    "SLC22A12": "pure_uric_acid",
    "APRT": "pure_uric_acid",
}

# ---------------------------------------------------------------------------
# Parse pathogenic variants from VCF files
# ---------------------------------------------------------------------------
print("Step 3: Parsing PD2 VCF files for pathogenic variants...")

vcf_files = sorted(PD2_DIR.glob("*.vcf"))
print(f"  Found {len(vcf_files):,} VCF files")

records = []
mrn_pattern = re.compile(r"^##patient_mrn=(\S+)")

for vcf_path in vcf_files:
    mrn = None
    with open(vcf_path, "r") as f:
        for line in f:
            # Header lines
            if line.startswith("##"):
                m = mrn_pattern.match(line)
                if m:
                    mrn = m.group(1)
                continue
            # Column header
            if line.startswith("#CHROM"):
                continue
            # Data lines — only keep pathogenic variants
            if "PATHOGENIC" in line:
                parts = line.strip().split("\t")
                chrom = parts[0]
                pos = int(parts[1])
                info = parts[7]
                # Extract gene name
                gene_match = re.search(r"GENE=(\w+)", info)
                gene = gene_match.group(1) if gene_match else "unknown"
                records.append({
                    "mrn": mrn,
                    "chrom": chrom,
                    "pos": pos,
                    "gene": gene,
                })

variants_df = pd.DataFrame(records)
print(f"  Pathogenic variants found: {len(variants_df):,}")
print(f"  Patients with pathogenic variants: {variants_df['mrn'].nunique():,}")
print(f"  Genes represented: {sorted(variants_df['gene'].unique())}")

# ---------------------------------------------------------------------------
# Merge with stone assignments
# ---------------------------------------------------------------------------
print("\n--- Merging with stone type assignments ---")

patient_stones = pd.read_csv(PD0_DIR / "patient_stones.csv")
phi_mapping = pd.read_csv(PD0_DIR / "phi_mapping.csv")

# Get primary stone type per patient (first episode for stone patients)
stone_patients = patient_stones[patient_stones["stone_type"] != "none"]
primary_stones = stone_patients.groupby("mrn")["stone_type"].first().reset_index()
primary_stones.columns = ["mrn", "primary_stone_type"]

# Merge variants with stone types
variants_with_stones = variants_df.merge(primary_stones, on="mrn", how="left")

# Patients without stones should have no pathogenic variants (by design)
no_stone_variants = variants_with_stones[variants_with_stones["primary_stone_type"].isna()]
print(f"  Pathogenic variants in non-stone patients: {len(no_stone_variants)}")

# Keep only stone patients
variants_with_stones = variants_with_stones.dropna(subset=["primary_stone_type"])

# ---------------------------------------------------------------------------
# Gene-to-stone-type concordance
# ---------------------------------------------------------------------------
print("\n--- Gene-Stone Type Concordance ---")

concordant = 0
discordant = 0
for _, row in variants_with_stones.iterrows():
    expected_type = GENE_STONE_MAP.get(row["gene"])
    if expected_type and expected_type == row["primary_stone_type"]:
        concordant += 1
    elif expected_type:
        discordant += 1

total_checked = concordant + discordant
if total_checked > 0:
    concordance_rate = concordant / total_checked * 100
    print(f"  Concordant (gene predicts correct stone type): {concordant:,} ({concordance_rate:.1f}%)")
    print(f"  Discordant: {discordant:,} ({100 - concordance_rate:.1f}%)")
    print(f"  Total pathogenic variants checked: {total_checked:,}")
else:
    concordance_rate = 0
    print("  No variants with known gene-stone mappings found")

# ---------------------------------------------------------------------------
# Gene frequency by stone type (for heatmap)
# ---------------------------------------------------------------------------
print("\n--- Gene Variant Frequency by Stone Type ---")

# Count variants per (gene, stone_type) pair
gene_stone_counts = (
    variants_with_stones.groupby(["primary_stone_type", "gene"])
    .size()
    .reset_index(name="count")
)

# Pivot to matrix
pivot = gene_stone_counts.pivot_table(
    index="primary_stone_type", columns="gene", values="count", fill_value=0
)

# Normalize per stone type (proportion of patients with that gene variant)
stone_type_patient_counts = primary_stones["primary_stone_type"].value_counts()
pivot_normalized = pivot.copy()
for stype in pivot_normalized.index:
    if stype in stone_type_patient_counts.index:
        pivot_normalized.loc[stype] = pivot_normalized.loc[stype] / stone_type_patient_counts[stype] * 100

# ---------------------------------------------------------------------------
# Figure: Heatmap with key
# ---------------------------------------------------------------------------
print("  Generating heatmap figure...")

# Letter labels for stone types
stone_types_sorted = [st for st in stone_type_patient_counts.index if st in pivot_normalized.index]
letters = [chr(ord('a') + i) for i in range(len(stone_types_sorted))]
stone_type_key = dict(zip(letters, stone_types_sorted))

# Reindex pivot to match sorted order
pivot_plot = pivot_normalized.reindex(stone_types_sorted)

# Build key text
key_lines = ["Stone Type Key",
            "  COM = calcium oxalate monohydrate (whewellite); COD = calcium oxalate dihydrate (weddellite)"]
for letter, stype in stone_type_key.items():
    n = stone_type_patient_counts.get(stype, 0)
    key_lines.append(f"  {letter} = {stype} (n={n})")
key_lines.append("")
key_lines.append(f"Concordance rate: {concordance_rate:.1f}% "
                 f"({concordant:,} concordant / {total_checked:,} total pathogenic variants)")
key_text = "\n".join(key_lines)

fig = plt.figure(figsize=(12, 8))

# Top: heatmap
ax = fig.add_subplot(2, 1, 1)
im = ax.imshow(pivot_plot.values, aspect="auto", cmap="YlOrRd")

ax.set_xticks(range(len(pivot_plot.columns)))
ax.set_xticklabels(pivot_plot.columns, rotation=45, ha="right", fontsize=9)
ax.set_yticks(range(len(letters)))
ax.set_yticklabels(letters, fontsize=10)
ax.set_xlabel("Gene")
ax.set_ylabel("Stone Type")
ax.set_title("Pathogenic Variant Frequency by Stone Type (% of patients)")

# Add text annotations
for i in range(len(pivot_plot.index)):
    for j in range(len(pivot_plot.columns)):
        val = pivot_plot.iloc[i, j]
        if val > 0:
            color = "white" if val > pivot_plot.values.max() * 0.6 else "black"
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                    fontsize=8, color=color)

plt.colorbar(im, ax=ax, label="% of patients with variant")

# Bottom: key
ax_key = fig.add_subplot(2, 1, 2)
ax_key.axis("off")
ax_key.text(0.0, 0.95, key_text, transform=ax_key.transAxes,
            fontsize=8, fontfamily="monospace", verticalalignment="top")

plt.tight_layout()
plt.savefig("step3_genomic_correlation.png", dpi=150, bbox_inches="tight")
plt.show()

print("\n[Step 3 complete] Heatmap saved to step3_genomic_correlation.png")
