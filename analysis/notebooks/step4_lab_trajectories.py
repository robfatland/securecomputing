"""
Step 4: Lab Value Trajectories (PD3)
======================================
Analyze longitudinal lab results, focusing on the stone panel tests that
differentiate stone types. Show that lab patterns correlate with stone type
(by design — the synthetic data was generated with these correlations built in).

Outputs:
- Summary statistics for stone panel labs by stone type
- Figure: box plots of key stone panel values by stone type (with key)

Terminology:
- Stone panel: a set of lab tests used to evaluate kidney stone risk
  - Urine Calcium 24hr: elevated in calcium stone formers (hypercalciuria)
  - Urine Oxalate 24hr: elevated in oxalate stone formers (hyperoxaluria)
  - Urine Citrate 24hr: LOW citrate = risk factor (hypocitraturia inhibits crystallization)
  - Urine pH: low pH → uric acid stones; high pH → calcium phosphate/struvite
  - Uric Acid (serum): elevated in uric acid stone formers (hyperuricemia)
  - Urine Cystine 24hr: elevated only in cystinuria patients
  - Phosphorus: may be elevated in calcium phosphate stones
  - PTH (parathyroid hormone): elevated in primary hyperparathyroidism → calcium stones
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
PD3_PATH = DATA_DIR / "pd3" / "lab_results.csv"
PD0_DIR = DATA_DIR / "pd0"

# Key stone panel tests to visualize (most discriminating for stone type)
KEY_TESTS = ["urine_calcium", "urine_oxalate", "urine_citrate", "urine_ph",
             "uric_acid", "urine_cystine"]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
print("Step 4: Analyzing PD3 lab value trajectories...")

print("  Loading lab results (this may take a moment)...")
labs_df = pd.read_csv(PD3_PATH)
print(f"  Lab results: {len(labs_df):,} rows")
print(f"  Panels: {sorted(labs_df['panel'].unique())}")
print(f"  Patients: {labs_df['person_id'].nunique():,}")
print(f"  Visits per patient: {labs_df.groupby('person_id')['visit_date'].nunique().describe()[['mean','min','max']].to_dict()}")

# Load stone assignments
patient_stones = pd.read_csv(PD0_DIR / "patient_stones.csv")
stone_patients = patient_stones[patient_stones["stone_type"] != "none"]
primary_stones = stone_patients.groupby("mrn")["stone_type"].first().reset_index()
primary_stones.columns = ["mrn", "primary_stone_type"]

# ---------------------------------------------------------------------------
# Filter to stone panel and merge with stone type
# ---------------------------------------------------------------------------
stone_labs = labs_df[labs_df["panel"] == "stone_panel"].copy()
print(f"\n  Stone panel rows: {len(stone_labs):,}")

stone_labs = stone_labs.merge(primary_stones, on="mrn", how="left")
# Keep only patients with a known stone type
stone_labs = stone_labs.dropna(subset=["primary_stone_type"])
print(f"  Stone panel rows (stone patients only): {len(stone_labs):,}")

# ---------------------------------------------------------------------------
# Summary statistics by stone type and test
# ---------------------------------------------------------------------------
print("\n--- Mean Stone Panel Values by Stone Type ---")

summary = (
    stone_labs[stone_labs["test_code"].isin(KEY_TESTS)]
    .groupby(["primary_stone_type", "test_code"])["value"]
    .agg(["mean", "std", "count"])
    .round(1)
)

# Print a condensed view
for test in KEY_TESTS:
    print(f"\n  {test}:")
    test_data = summary.xs(test, level="test_code") if test in summary.index.get_level_values("test_code") else None
    if test_data is not None:
        for stype in test_data.index:
            row = test_data.loc[stype]
            print(f"    {stype}: mean={row['mean']:.1f}, std={row['std']:.1f}, n={int(row['count'])}")

# ---------------------------------------------------------------------------
# Figure: Box plots of key labs by stone type
# ---------------------------------------------------------------------------
print("\n  Generating lab trajectory figure...")

# Get stone type ordering and letter labels
type_counts = primary_stones["primary_stone_type"].value_counts()
stone_types_sorted = type_counts.index.tolist()
letters = [chr(ord('a') + i) for i in range(len(stone_types_sorted))]
stone_type_key = dict(zip(letters, stone_types_sorted))

# Map stone types to letters for plotting
stone_labs["type_letter"] = stone_labs["primary_stone_type"].map(
    {v: k for k, v in stone_type_key.items()}
)

# Build key text
key_lines = ["Stone Type Key",
            "  COM = calcium oxalate monohydrate (whewellite); COD = calcium oxalate dihydrate (weddellite)"]
for letter, stype in stone_type_key.items():
    n = type_counts.get(stype, 0)
    key_lines.append(f"  {letter} = {stype} (n={n})")
key_text = "\n".join(key_lines)

# Create figure: 2x3 grid of box plots + key row
fig = plt.figure(figsize=(14, 10))

# 6 panels for key tests
for idx, test_code in enumerate(KEY_TESTS):
    ax = fig.add_subplot(3, 3, idx + 1)
    test_data = stone_labs[stone_labs["test_code"] == test_code]

    # Build data for box plot
    box_data = []
    box_labels = []
    for letter in letters:
        stype = stone_type_key[letter]
        values = test_data[test_data["primary_stone_type"] == stype]["value"].dropna()
        if len(values) > 0:
            box_data.append(values.values)
            box_labels.append(letter)
        else:
            box_data.append([])
            box_labels.append(letter)

    bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True,
                    medianprops=dict(color="black", linewidth=1.5),
                    flierprops=dict(marker='.', markersize=2, alpha=0.3))

    # Color boxes
    colors = plt.cm.tab10(np.linspace(0, 1, len(box_labels)))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    # Get unit from data
    units = test_data["unit"].dropna()
    unit_row = units.iloc[0] if len(units) > 0 else ""
    # Special case: pH title and label
    if test_code == "urine_ph":
        ax.set_title("Urine pH", fontsize=10)
        ax.set_ylabel("pH", fontsize=8)
    else:
        ax.set_title(test_code.replace("_", " ").title(), fontsize=10)
        ax.set_ylabel(unit_row, fontsize=8)
    ax.set_xlabel("Stone Type", fontsize=8)
    ax.tick_params(axis='x', labelsize=8)

# Key panel (bottom row, spanning columns)
ax_key = fig.add_subplot(3, 1, 3)
ax_key.axis("off")
ax_key.text(0.0, 0.95, key_text, transform=ax_key.transAxes,
            fontsize=8, fontfamily="monospace", verticalalignment="top")

plt.tight_layout()
plt.savefig("step4_lab_trajectories.png", dpi=150, bbox_inches="tight")
plt.show()

# ---------------------------------------------------------------------------
# Second figure: Uric Acid detail chart with key
# ---------------------------------------------------------------------------
print("  Generating uric acid detail figure...")

fig2 = plt.figure(figsize=(10, 6))

ax_ua = fig2.add_subplot(2, 1, 1)
test_data = stone_labs[stone_labs["test_code"] == "uric_acid"]

box_data = []
box_labels = []
for letter in letters:
    stype = stone_type_key[letter]
    values = test_data[test_data["primary_stone_type"] == stype]["value"].dropna()
    box_data.append(values.values if len(values) > 0 else [])
    box_labels.append(letter)

bp = ax_ua.boxplot(box_data, labels=box_labels, patch_artist=True,
                   medianprops=dict(color="black", linewidth=1.5),
                   flierprops=dict(marker='.', markersize=2, alpha=0.3))

colors = plt.cm.tab10(np.linspace(0, 1, len(box_labels)))
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

ax_ua.set_title("Serum Uric Acid by Stone Type", fontsize=11)
ax_ua.set_ylabel("mg/dL", fontsize=9)
ax_ua.set_xlabel("Stone Type", fontsize=9)

# Key panel
ax_key2 = fig2.add_subplot(2, 1, 2)
ax_key2.axis("off")
ax_key2.text(0.0, 0.95, key_text, transform=ax_key2.transAxes,
             fontsize=8, fontfamily="monospace", verticalalignment="top")

plt.tight_layout()
plt.savefig("step4_uric_acid_detail.png", dpi=150, bbox_inches="tight")
plt.show()

print("\n[Step 4 complete] Figures saved to step4_lab_trajectories.png and step4_uric_acid_detail.png")
