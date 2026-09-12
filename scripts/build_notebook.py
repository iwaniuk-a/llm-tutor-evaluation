"""Build the offline, GitHub-facing evaluation notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "01_llm_tutor_evaluation.ipynb"


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(True),
    }


cells = [
    markdown(
        """# LLM-Tutor: Offline Evaluation

This notebook analyzes a committed benchmark of 75 mathematical tasks across 15 categories. It compares result-only and structured-reasoning prompt modes for a local Llama 3 8B configuration and a Groq-hosted Llama 3.3 70B configuration.

The notebook is intentionally offline: it reads saved responses and does not call external model APIs.
"""
    ),
    markdown(
        """## Context and methods

The primary outcome is final-answer accuracy. Secondary outcomes are response-format compliance and mean latency. A response is scored using the deterministic evaluator in `src/llm_tutor/evaluation.py`; structured reasoning is treated as an output protocol, not as proof of faithful internal explanation.

### Key assumptions

- The committed CSV contains one response for each task-model-mode combination.
- The hand-authored expected result is the reference target for scoring.
- Latency values are descriptive of the recorded run environment and should not be generalized to other hardware.
"""
    ),
    code(
        """from pathlib import Path
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

REPO_ROOT = next(
    candidate for candidate in [Path.cwd(), *Path.cwd().parents]
    if (candidate / 'data' / 'math_tasks.json').exists()
)
sys.path.insert(0, str(REPO_ROOT / 'src'))

from llm_tutor.evaluation import evaluate_answer, validate_tasks

sns.set_theme(style='whitegrid', context='notebook')
pd.set_option('display.max_colwidth', 120)
print(f'Repository root: {REPO_ROOT}')
"""
    ),
    markdown("## Data\n\nValidate the task contract before interpreting any benchmark result."),
    code(
        """with open(REPO_ROOT / 'data' / 'math_tasks.json', encoding='utf-8') as handle:
    tasks = json.load(handle)

task_contract = validate_tasks(tasks)
task_frame = pd.DataFrame(tasks)
display(pd.DataFrame([task_contract]))
display(task_frame.groupby('category', as_index=False).size().rename(columns={'size': 'task_count'}))
"""
    ),
    code(
        """raw = pd.read_csv(REPO_ROOT / 'data' / 'tutor_benchmark_raw_results.csv')
summary = pd.read_csv(REPO_ROOT / 'data' / 'tutor_benchmark_summary.csv')
print(f'Raw benchmark rows: {len(raw)}')
display(summary)
assert len(raw) == 75 * 2 * 2
assert raw.groupby(['model', 'variant']).size().eq(75).all()
assert 'audited_score' in raw.columns
"""
    ),
    markdown(
        """## Scoring audit

The recorded `score` column is preserved for provenance. The independently audited `audited_score` column is computed with the tested evaluator. Four numeric responses are mathematically equivalent to their expected answers under the audited rules.
"""
    ),
    markdown("## Results\n\nRecompute the headline accuracy from the saved per-response results and compare it with the committed summary."),
    code(
        """raw['recomputed_score'] = [
    evaluate_answer(answer, expected)
    for answer, expected in zip(raw['raw_answer'], raw['expected'])
]
recomputed = (
    raw.groupby(['model', 'variant'], as_index=False)
       .agg(accuracy=('recomputed_score', 'mean'),
            mean_latency=('latency', 'mean'),
            format_compliance=('format_ok', 'mean'))
)
recomputed['accuracy_pct'] = (recomputed['accuracy'] * 100).round(1)
display(recomputed)
assert set(recomputed['accuracy_pct']) == set(summary['Accuracy %'])
"""
    ),
    code(
        """plot_data = summary.copy()
plot_data['label'] = plot_data['model'] + ' / ' + plot_data['variant']
fig, ax = plt.subplots(figsize=(9, 4.5))
sns.barplot(data=plot_data, x='label', y='Accuracy %', hue='variant', legend=False, palette='viridis', ax=ax)
ax.set_title('Final-answer accuracy by model and prompt mode')
ax.set_xlabel('Configuration')
ax.set_ylabel('Accuracy (%)')
ax.set_ylim(0, 105)
ax.tick_params(axis='x', rotation=20)
for container in ax.containers:
    ax.bar_label(container, fmt='%.1f%%', padding=3)
plt.tight_layout()
display(fig)
plt.close(fig)
"""
    ),
    code(
        """category_accuracy = (
    raw.groupby(['category', 'model', 'variant'], as_index=False)['audited_score']
       .mean()
)
category_accuracy['accuracy_pct'] = category_accuracy['audited_score'] * 100
heatmap_data = category_accuracy.pivot_table(
    index='category', columns=['model', 'variant'], values='accuracy_pct'
)
fig, ax = plt.subplots(figsize=(12, 7))
sns.heatmap(heatmap_data, annot=True, fmt='.0f', vmin=0, vmax=100,
            cmap='RdYlGn', cbar_kws={'label': 'Accuracy (%)'}, ax=ax)
ax.set_title('Accuracy by mathematical category')
ax.set_xlabel('Model and prompt mode')
ax.set_ylabel('Category')
plt.tight_layout()
display(fig)
plt.close(fig)
"""
    ),
    markdown("## Error inspection\n\nThe benchmark preserves raw responses so that aggregate accuracy is not the only evidence available."),
    code(
        """errors = raw.loc[raw['audited_score'].eq(0),
                  ['task_id', 'category', 'model', 'variant', 'expected', 'raw_answer']]
print(f'Audited incorrect responses: {len(errors)} of {len(raw)}')
display(errors.head(10))
"""
    ),
    markdown(
        """## Takeaways

- Structured reasoning improved final-answer accuracy in both configurations on this fixed benchmark.
- The local model received the larger accuracy lift, but structured-mode latency increased substantially.
- The hosted 70B configuration produced the best quality-latency balance in the recorded run.
- The result supports further evaluation; it does not establish generalization, causal prompt superiority, or faithful explainability.

## Next steps

- Add repeated runs and confidence intervals.
- Expand the held-out task set and independently verify intermediate steps.
- Record model versions, hardware, prompt versions, and provider metadata for each run.
"""
    ),
]


notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NOTEBOOK_PATH.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(NOTEBOOK_PATH)
