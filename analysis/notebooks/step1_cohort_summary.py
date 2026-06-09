"""
Step 1: Data Loading and Cohort Summary
========================================
Load PD0 (OMOP tables), verify dataset linkage via MRN, and produce
a cohort summary: demographics, stone prevalence, episode counts.

Outputs:
- cohort_df: master DataFrame (one row per patient) with demographics + stone status
- Printed summary statistics
- Figure: cohort demographics overview
"""

import os
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.path.expanduser("~/securecomputing-data"))
PD0_DIR = DATA_DIR / "pd0"

# ---------------------------------------------------------------------------
# Load OMOP person table and PHI mapping
# ---------------------------------------------------------------------------
print("Loading PD0 (OMOP) data...")

person_df = pd.read_csv(PD0_DIR / "person.csv")
phi_mapping = pd.read_csv(PD0_DIR / "phi_mapping.csv")
patient_stones = pd.read_csv(PD0_DIR / "patient_stones.csv")

print(f"  person.csv: {len(person_df):,} patients")
print(f"  phi_mapping.csv: {len(phi_mapping):,} patients")
print(f"  patient_stones.csv: {len(patient_stones):,} rows (patient-episode level)")

# ---------------------------------------------------------------------------
# Build master cohort DataFrame
# ---------------------------------------------------------------------------
# Merge person with PHI mapping to get MRN linkage
cohort_df = person_df.merge(
    phi_mapping[["person_id", "mrn"]],
    on="person_id",
    how="left"
)

# Summarize stone status per patient (exclude "none" entries)
stone_episodes = patient_stones[patient_stones["stone_type"] != "none"]
stone_summary = (
    stone_episodes.groupby("person_id")
    .agg(
        n_episodes=("episode_number", "nunique"),
        primary_stone_type=("stone_type", "first")
    )
    .reset_index()
)

cohort_df = cohort_df.merge(stone_summary, on="person_id", how="left")
cohort_df["has_stones"] = cohort_df["n_episodes"].notna()
cohort_df["n_episodes"] = cohort_df["n_episodes"].fillna(0).astype(int)

print(f"\nCohort built: {len(cohort_df):,} patients")
print(f"  With stones: {cohort_df['has_stones'].sum():,} ({cohort_df['has_stones'].mean()*100:.1f}%)")
print(f"  Without stones: {(~cohort_df['has_stones']).sum():,} ({(~cohort_df['has_stones']).mean()*100:.1f}%)")

# ---------------------------------------------------------------------------
# Verify cross-dataset linkage
# ---------------------------------------------------------------------------
print("\n--- Cross-Dataset Linkage Verification ---")

# Check PD1 (CIF files exist for stone patients)
pd1_dir = DATA_DIR / "pd1"
if pd1_dir.exists():
    pd1_files = list(pd1_dir.glob("*.cif"))
    print(f"  PD1 (CIF files): {len(pd1_files):,} files")
else:
    print("  PD1: directory not found")

# Check PD2 (VCF files - one per patient)
pd2_dir = DATA_DIR / "pd2"
if pd2_dir.exists():
    pd2_files = list(pd2_dir.glob("*.vcf"))
    print(f"  PD2 (VCF files): {len(pd2_files):,} files")
else:
    print("  PD2: directory not found")

# Check PD3 (lab results CSV)
pd3_path = DATA_DIR / "pd3" / "lab_results.csv"
if pd3_path.exists():
    pd3_row_count = sum(1 for _ in open(pd3_path)) - 1  # subtract header
    print(f"  PD3 (lab results): {pd3_row_count:,} rows")
else:
    print("  PD3: file not found")

# ---------------------------------------------------------------------------
# Demographics summary
# ---------------------------------------------------------------------------
print("\n--- Demographics ---")
if "year_of_birth" in cohort_df.columns:
    cohort_df["age_approx"] = 2026 - cohort_df["year_of_birth"]
    print(f"  Age (approx): mean={cohort_df['age_approx'].mean():.1f}, "
          f"std={cohort_df['age_approx'].std():.1f}, "
          f"range=[{cohort_df['age_approx'].min()}, {cohort_df['age_approx'].max()}]")

if "gender_source_value" in cohort_df.columns:
    gender_counts = cohort_df["gender_source_value"].value_counts()
    print(f"  Gender: {dict(gender_counts)}")

# ---------------------------------------------------------------------------
# Stone type distribution
# ---------------------------------------------------------------------------
print("\n--- Stone Type Distribution ---")
stone_patients = cohort_df[cohort_df["has_stones"]]
if "primary_stone_type" in stone_patients.columns:
    type_dist = stone_patients["primary_stone_type"].value_counts()
    for stype, count in type_dist.items():
        print(f"  {stype}: {count} ({count/len(stone_patients)*100:.1f}%)")

# ---------------------------------------------------------------------------
# Episode count distribution
# ---------------------------------------------------------------------------
print("\n--- Episode Count Distribution ---")
episode_dist = cohort_df["n_episodes"].value_counts().sort_index()
for n_ep, count in episode_dist.items():
    print(f"  {int(n_ep)} episodes: {count} patients ({count/len(cohort_df)*100:.1f}%)")

# ---------------------------------------------------------------------------
# Summary figure with embedded key
# ---------------------------------------------------------------------------

# Build the key text first (needed for layout)
type_dist_sorted = type_dist.sort_values(ascending=False)
letters = [chr(ord('a') + i) for i in range(len(type_dist_sorted))]
stone_type_key = dict(zip(letters, type_dist_sorted.index))

key_lines = ["Stone Type Key",
            "  COM = calcium oxalate monohydrate (whewellite); COD = calcium oxalate dihydrate (weddellite)"]
for letter, stype in stone_type_key.items():
    count = type_dist_sorted[stype]
    key_lines.append(f"  {letter} = {stype} (n={count})")
key_text = "\n".join(key_lines)

fig = plt.figure(figsize=(14, 6.5))

# Top row: three chart panels
ax1 = fig.add_subplot(2, 3, 1)
ax2 = fig.add_subplot(2, 3, 2)
ax3 = fig.add_subplot(2, 3, 3)

# Panel 1: Stone vs no-stone
stone_counts = cohort_df["has_stones"].value_counts()
ax1.bar(["Stones", "No Stones"], [stone_counts.get(True, 0), stone_counts.get(False, 0)],
        color=["#d35400", "#2c3e50"])
ax1.set_title("Stone Prevalence")
ax1.set_ylabel("Patients")

# Panel 2: Stone type distribution with letter labels
ax2.bar(letters, type_dist_sorted.values, color="#2980b9")
ax2.set_title("Stone Type Distribution")
ax2.set_ylabel("Patients")
ax2.set_xlabel("Type (see key below)")

# Panel 3: Episode count
episode_dist.plot.bar(ax=ax3, color="#27ae60")
ax3.set_title("Episodes per Patient")
ax3.set_ylabel("Patients")
ax3.set_xlabel("Number of episodes")

# Bottom row: key text spanning full width
ax_key = fig.add_subplot(2, 1, 2)
ax_key.axis("off")
ax_key.text(0.0, 0.95, key_text, transform=ax_key.transAxes,
            fontsize=8, fontfamily="monospace", verticalalignment="top")

plt.tight_layout()
plt.savefig("step1_cohort_summary.png", dpi=150, bbox_inches="tight")
plt.show()

print("\n[Step 1 complete] Cohort summary saved to step1_cohort_summary.png")
