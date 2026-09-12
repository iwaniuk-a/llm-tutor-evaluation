"""Render static, GitHub-friendly figures from the audited benchmark."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

summary = pd.read_csv(ROOT / "data" / "tutor_benchmark_summary.csv")
raw = pd.read_csv(ROOT / "data" / "tutor_benchmark_raw_results.csv")

sns.set_theme(style="whitegrid", context="notebook")
palette = {"direct": "#4C78A8", "cot": "#F58518"}

fig, ax = plt.subplots(figsize=(8.5, 4.6))
sns.barplot(
    data=summary,
    x="model",
    y="Accuracy %",
    hue="variant",
    hue_order=["direct", "cot"],
    palette=palette,
    ax=ax,
)
ax.set_title("Audited final-answer accuracy")
ax.set_xlabel("Model configuration")
ax.set_ylabel("Accuracy (%)")
ax.set_ylim(0, 105)
ax.legend(title="Prompt mode", labels=["Direct", "Structured reasoning"])
for container in ax.containers:
    ax.bar_label(container, fmt="%.1f%%", padding=3)
fig.tight_layout()
fig.savefig(ASSETS / "accuracy_by_configuration.png", dpi=180, bbox_inches="tight")
plt.close(fig)

category = (
    raw.groupby(["category", "model", "variant"], as_index=False)["audited_score"]
       .mean()
)
category["accuracy_pct"] = category["audited_score"] * 100
pivot = category.pivot_table(
    index="category", columns=["model", "variant"], values="accuracy_pct"
)
fig, ax = plt.subplots(figsize=(11, 7))
sns.heatmap(
    pivot,
    annot=True,
    fmt=".0f",
    vmin=0,
    vmax=100,
    cmap="YlGnBu",
    linewidths=0.4,
    linecolor="white",
    cbar_kws={"label": "Accuracy (%)"},
    ax=ax,
)
ax.set_title("Audited accuracy by mathematical category")
ax.set_xlabel("Model and prompt mode")
ax.set_ylabel("Category")
fig.tight_layout()
fig.savefig(ASSETS / "accuracy_by_category.png", dpi=180, bbox_inches="tight")
plt.close(fig)

print("Wrote accuracy_by_configuration.png and accuracy_by_category.png")
