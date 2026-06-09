"""
Step 2: Stone Composition Profiling (PD1)
==========================================
Parse CIF files from PD1, extract mineral phase compositions from headers,
cross-reference with patient_stones.csv, and produce composition summary.

Outputs:
- composition_df: DataFrame with one row per specimen (MRN, episode, minerals, percentages)
- Printed summary of mineral prevalence
- Figure: mean composition by stone type category (stacked bar)

Terminology:
- CIF: Crystallographic Information File (standard format for crystallography data)
- PXRD: Powder X-Ray Diffraction (identifies crystalline phases by diffraction angles)
- FTIR: Fourier Transform Infrared Spectroscopy (identifies molecular bonds by IR absorption)
- COM: Calcium Oxalate Monohydrate (mineral name: whewellite) — most common stone mineral
- COD: Calcium Oxalate Dihydrate (mineral name: weddellite) — often mixed with COM
"""

import os
import json
import re
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.path.expanduser("~/securecomputing-data"))
PD1_DIR = DATA_DIR / "pd1"

# ---------------------------------------------------------------------------
# Parse composition from CIF file headers
# ---------------------------------------------------------------------------
print("Step 2: Parsing PD1 CIF files for composition data...")

composition_pattern = re.compile(r"^# Composition:\s*(\{.*\})\s*%?")
mrn_pattern = re.compile(r"^# Patient MRN:\s*(\S+)")
episode_pattern = re.compile(r"^# Episode:\s*(\d+)")
stone_type_pattern = re.compile(r"^# Stone type:\s*(\S+)")

records = []
cif_files = sorted(PD1_DIR.glob("*.cif"))
print(f"  Found {len(cif_files):,} CIF files")

for cif_path in cif_files:
    mrn = None
    episode = None
    stone_type = None
    composition = None

    with open(cif_path, "r") as f:
        for line in f:
            if not line.startswith("#"):
                break  # past the header
            m = mrn_pattern.match(line)
            if m:
                mrn = m.group(1)
                continue
            m = episode_pattern.match(line)
            if m:
                episode = int(m.group(1))
                continue
            m = stone_type_pattern.match(line)
            if m:
                stone_type = m.group(1)
                continue
            m = composition_pattern.match(line)
            if m:
                try:
                    composition = json.loads(m.group(1))
                except json.JSONDecodeError:
                    composition = {}
                continue

    if mrn and composition:
        record = {
            "mrn": mrn,
            "episode": episode,
            "stone_type": stone_type,
            "filename": cif_path.name,
        }
        record.update(composition)
        records.append(record)

composition_df = pd.DataFrame(records)

# Fill NaN minerals with 0 for aggregation
mineral_cols = [c for c in composition_df.columns
                if c not in ("mrn", "episode", "stone_type", "filename")]
composition_df[mineral_cols] = composition_df[mineral_cols].fillna(0)

print(f"  Parsed {len(composition_df):,} specimens successfully")
print(f"  Minerals detected: {sorted(mineral_cols)}")

# ---------------------------------------------------------------------------
# Composition summary by stone type
# ---------------------------------------------------------------------------
print("\n--- Mean Composition by Stone Type (%) ---")

type_means = composition_df.groupby("stone_type")[mineral_cols].mean()

# Sort by most common stone type
type_counts = composition_df["stone_type"].value_counts()
type_means = type_means.loc[type_counts.index]

for stype in type_means.index:
    minerals = type_means.loc[stype]
    nonzero = minerals[minerals > 0].sort_values(ascending=False)
    parts = [f"{m}={v:.1f}%" for m, v in nonzero.items()]
    print(f"  {stype} (n={type_counts[stype]}): {', '.join(parts)}")

# ---------------------------------------------------------------------------
# Cross-reference with patient_stones.csv
# ---------------------------------------------------------------------------
print("\n--- Cross-Reference Verification ---")
patient_stones = pd.read_csv(DATA_DIR / "pd0" / "patient_stones.csv")
stone_episodes = patient_stones[patient_stones["stone_type"] != "none"]
print(f"  patient_stones.csv episodes (non-none): {len(stone_episodes):,}")
print(f"  CIF files parsed: {len(composition_df):,}")
if len(stone_episodes) == len(composition_df):
    print("  ✓ Counts match — one CIF per stone episode")
else:
    diff = len(stone_episodes) - len(composition_df)
    print(f"  Δ = {diff} (stone episodes without CIF files or parsing failures)")

# ---------------------------------------------------------------------------
# Figure: Stacked bar chart of mean composition by stone type (with key)
# ---------------------------------------------------------------------------
print("\n  Generating composition figure...")

# Use letters for x-axis labels (same convention as Step 1)
letters = [chr(ord('a') + i) for i in range(len(type_means))]
stone_type_key = dict(zip(letters, type_means.index))

# Select minerals that contribute >1% in at least one type
significant_minerals = [m for m in mineral_cols
                        if type_means[m].max() > 1.0]
# Sort by overall prevalence
mineral_totals = type_means[significant_minerals].sum().sort_values(ascending=False)
significant_minerals = mineral_totals.index.tolist()

# Color palette
colors = plt.cm.Set3(np.linspace(0, 1, len(significant_minerals)))

# Build key text
key_lines = ["Stone Type Key",
            "  COM = calcium oxalate monohydrate (whewellite); COD = calcium oxalate dihydrate (weddellite)",
            "  Note: mineral phases (chart legend) and stone type categories (below) are distinct.",
            "  A stone type may contain multiple mineral phases (e.g., struvite stones contain hydroxyapatite)."]
for letter, stype in stone_type_key.items():
    count = type_counts[stype]
    key_lines.append(f"  {letter} = {stype} (n={count})")
key_text = "\n".join(key_lines)

# Figure with chart on top, key on bottom
fig = plt.figure(figsize=(10, 7))

ax = fig.add_subplot(2, 1, 1)

bottom = np.zeros(len(type_means))
for i, mineral in enumerate(significant_minerals):
    values = type_means[mineral].values
    ax.bar(letters, values, bottom=bottom, label=mineral,
           color=colors[i], edgecolor="white", linewidth=0.5)
    bottom += values

ax.set_xlabel("Stone Type (see key below)")
ax.set_ylabel("Mean Composition (%)")
ax.set_title("Mean Mineral Composition by Stone Type Category")
ax.legend(loc="upper right", fontsize=8, ncol=2)
ax.set_ylim(0, 105)

# Bottom: key text
ax_key = fig.add_subplot(2, 1, 2)
ax_key.axis("off")
ax_key.text(0.0, 0.95, key_text, transform=ax_key.transAxes,
            fontsize=8, fontfamily="monospace", verticalalignment="top")

plt.tight_layout()
plt.savefig("step2_stone_composition.png", dpi=150, bbox_inches="tight")
plt.show()

print("\n[Step 2 complete] Composition figure saved to step2_stone_composition.png")
