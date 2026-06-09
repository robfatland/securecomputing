"""
Step 6: Predictive Model
=========================
Build a classifier that predicts stone type from genomics (PD2) + labs (PD3)
alone — without requiring crystallography (PD1). The synthetic data was designed
with strong, clean correlations, so this model should achieve unrealistically
high accuracy, demonstrating the data coherence.

Outputs:
- Classification accuracy and confusion matrix
- Feature importance ranking
- Figure: confusion matrix heatmap + feature importance bar chart with key

Terminology:
- Random Forest: an ensemble of decision trees that votes on the classification
- Confusion matrix: a table showing predicted vs actual class for each sample
- Feature importance: how much each input variable contributes to the prediction
- Cross-validation: training on a subset of data, testing on the rest, repeated
"""

import os
from pathlib import Path
import json
import re

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.path.expanduser("~/securecomputing-data"))
PD0_DIR = DATA_DIR / "pd0"
PD2_DIR = DATA_DIR / "pd2"
PD3_PATH = DATA_DIR / "pd3" / "lab_results.csv"

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Build integrated feature matrix (genomics + labs only, no crystallography)
# ---------------------------------------------------------------------------
print("Step 6: Building predictive model (genomics + labs → stone type)...")

# --- Load stone assignments ---
patient_stones = pd.read_csv(PD0_DIR / "patient_stones.csv")
stone_episodes = patient_stones[patient_stones["stone_type"] != "none"]
primary_stones = stone_episodes.groupby("mrn").agg(
    primary_stone_type=("stone_type", "first")
).reset_index()

# --- PD2: extract pathogenic gene indicators per patient ---
print("  Loading PD2 genomic features...")

STONE_GENES = ["SLC3A1", "SLC7A9", "CLCN5", "CASR", "VDR",
               "AGXT", "GRHPR", "HOGA1", "SLC22A12", "APRT"]

mrn_vcf_pattern = re.compile(r"^##patient_mrn=(\S+)")
pd2_records = []

for vcf_path in sorted(PD2_DIR.glob("*.vcf")):
    mrn = None
    gene_counts = {g: 0 for g in STONE_GENES}
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
                gene_match = re.search(r"GENE=(\w+)", line)
                if gene_match:
                    gene = gene_match.group(1)
                    if gene in gene_counts:
                        gene_counts[gene] += 1
    record = {"mrn": mrn}
    record.update({f"gene_{g}": gene_counts[g] for g in STONE_GENES})
    pd2_records.append(record)

pd2_df = pd.DataFrame(pd2_records)
print(f"    PD2: {len(pd2_df):,} patients, {len(STONE_GENES)} gene features")

# --- PD3: mean stone panel values per patient ---
print("  Loading PD3 lab features...")

labs_df = pd.read_csv(PD3_PATH)
stone_panel = labs_df[labs_df["panel"] == "stone_panel"]

pd3_features = (
    stone_panel.groupby(["mrn", "test_code"])["value"]
    .mean()
    .reset_index()
    .pivot(index="mrn", columns="test_code", values="value")
    .reset_index()
)
pd3_features.columns = ["mrn"] + [f"lab_{c}" for c in pd3_features.columns[1:]]
print(f"    PD3: {len(pd3_features):,} patients, {len(pd3_features.columns)-1} lab features")

# --- Merge ---
print("  Merging features...")
model_df = primary_stones.merge(pd2_df, on="mrn", how="inner")
model_df = model_df.merge(pd3_features, on="mrn", how="inner")

# Drop patients with any missing values
feature_cols = [c for c in model_df.columns if c.startswith("gene_") or c.startswith("lab_")]
model_df = model_df.dropna(subset=feature_cols)

print(f"  Model dataset: {len(model_df):,} patients × {len(feature_cols)} features")
print(f"  Stone types: {model_df['primary_stone_type'].nunique()}")

# ---------------------------------------------------------------------------
# Train and evaluate Random Forest classifier
# ---------------------------------------------------------------------------
print("\n--- Training Random Forest Classifier ---")

X = model_df[feature_cols].values
le = LabelEncoder()
y = le.fit_transform(model_df["primary_stone_type"].values)
class_names = le.classes_

# Cross-validated accuracy
cv_scores = cross_val_score(
    RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE),
    X, y, cv=5, scoring="accuracy"
)
print(f"  5-fold CV accuracy: {cv_scores.mean()*100:.1f}% ± {cv_scores.std()*100:.1f}%")

# Full predictions for confusion matrix
y_pred = cross_val_predict(
    RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE),
    X, y, cv=5
)

overall_accuracy = accuracy_score(y, y_pred)
print(f"  Overall accuracy: {overall_accuracy*100:.1f}%")

# Per-class report
print("\n--- Classification Report ---")
print(classification_report(y, y_pred, target_names=class_names))

# Feature importance (train on full dataset for importance ranking)
rf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_STATE)
rf.fit(X, y)
importances = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)

print("\n--- Top 10 Features ---")
for feat, imp in importances.head(10).items():
    print(f"  {feat}: {imp:.3f}")

# ---------------------------------------------------------------------------
# Figure: confusion matrix + feature importance
# ---------------------------------------------------------------------------
print("\n  Generating model evaluation figure...")

# Letter labels for stone types
letters = [chr(ord('a') + i) for i in range(len(class_names))]
stone_type_key = dict(zip(letters, class_names))

# Build key text
key_lines = [f"Overall accuracy: {overall_accuracy*100:.1f}% (5-fold cross-validation)"]
key_lines.append("")
key_lines.append("Stone Type Key")
key_lines.append("  COM = calcium oxalate monohydrate (whewellite); COD = calcium oxalate dihydrate (weddellite)")
for letter, stype in stone_type_key.items():
    n = (model_df["primary_stone_type"] == stype).sum()
    key_lines.append(f"  {letter} = {stype} (n={n})")
key_text = "\n".join(key_lines)

fig = plt.figure(figsize=(14, 9))

# Panel 1: Confusion matrix
ax1 = fig.add_subplot(2, 2, 1)
cm = confusion_matrix(y, y_pred)
cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100

im = ax1.imshow(cm_pct, cmap="Blues", vmin=0, vmax=100)
ax1.set_xticks(range(len(letters)))
ax1.set_xticklabels(letters, fontsize=9)
ax1.set_yticks(range(len(letters)))
ax1.set_yticklabels(letters, fontsize=9)
ax1.set_xlabel("Predicted")
ax1.set_ylabel("Actual")
ax1.set_title("Confusion Matrix (% per row)")

for i in range(len(cm)):
    for j in range(len(cm)):
        val = cm_pct[i, j]
        if val > 1:
            color = "white" if val > 60 else "black"
            ax1.text(j, i, f"{val:.0f}", ha="center", va="center",
                     fontsize=7, color=color)

plt.colorbar(im, ax=ax1, label="%", shrink=0.8)

# Panel 2: Feature importance (top 15)
ax2 = fig.add_subplot(2, 2, 2)
top_n = 15
top_features = importances.head(top_n)
ax2.barh(range(top_n), top_features.values, color="#2980b9")
ax2.set_yticks(range(top_n))
ax2.set_yticklabels(top_features.index, fontsize=8)
ax2.set_xlabel("Importance")
ax2.set_title(f"Top {top_n} Feature Importances")
ax2.invert_yaxis()

# Bottom: key
ax_key = fig.add_subplot(2, 1, 2)
ax_key.axis("off")
ax_key.text(0.0, 0.95, key_text, transform=ax_key.transAxes,
            fontsize=8, fontfamily="monospace", verticalalignment="top")

plt.tight_layout()
plt.savefig("step6_predictive_model.png", dpi=150, bbox_inches="tight")
plt.show()

print("\n[Step 6 complete] Model evaluation figure saved to step6_predictive_model.png")
