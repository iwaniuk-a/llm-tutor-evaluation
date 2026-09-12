# LLM-Tutor Technical Report

## Executive summary

LLM-Tutor evaluates whether a structured response prompt improves the correctness and usability of LLM-generated solutions to elementary and intermediate mathematics problems. 
The benchmark contains 75 hand-authored tasks across 15 categories, with five tasks per category. 
Two models are evaluated in two modes: a result-only prompt and a structured-reasoning prompt that requests analysis, reasoning, self-evaluation, and a delimited final answer.

The hosted Llama 3.3 70B configuration achieved 97.3% accuracy in structured mode versus 77.3% in direct mode, a 20.0 percentage-point difference. The local Llama 3 8B configuration improved from 38.7% to 72.0%, a 33.3 percentage-point difference. Structured responses were slower: mean latency increased from 0.25 s to 0.83 s for the hosted model and from 2.83 s to 35.69 s for the local model.

These are benchmark-specific observations, not general claims about model reasoning. The project measures the quality of a requested answer format and final-answer correctness; it does not establish that the displayed reasoning is a faithful causal explanation of the model's internal computation.

## Research question

Does requesting a structured, self-checking response improve final-answer correctness, and what latency cost does that impose for local and hosted model configurations?

## Experimental design

### Dataset

The dataset contains 75 tasks and 15 categories, with five tasks per category. Each record contains:

- a unique task ID;
- a category;
- the question text;
- the expected result; and
- reference solution steps for human inspection.

### Configurations

| Dimension | Values |
| --- | --- |
| Model | Llama 3 8B via Ollama; Llama 3.3 70B via Groq |
| Prompt mode | Direct result-only; structured reasoning |
| Primary outcome | Final-answer accuracy |
| Secondary outcomes | Format compliance and mean latency |
| Evaluation unit | One model-mode response per task |

The same task set is used for every configuration. Results are saved per response before aggregation so errors and latency can be audited.

## Evaluation method

The evaluator extracts the first result enclosed in `[[...]]`. It then applies, in order:

1. exact normalized comparison;
2. alternative-answer handling for answers separated by `or`;
3. multi-component handling for answers joined by `and`;
4. symbolic equivalence when SymPy can parse both expressions; and
5. approximate numeric equivalence with an absolute tolerance of 0.03.

Format compliance is separate from correctness. Direct responses must contain the delimited result. Structured responses must also contain the `ANALYSIS`, `REASONING`, and `SELF-EVALUATION` sections.

## Results

| Model | Mode | Accuracy | Lift vs direct | Mean latency | Compliance |
| --- | --- | ---: | ---: | ---: | ---: |
| Llama 3.3 70B via Groq | Direct | 77.3% | - | 0.25 s | 100.0% |
| Llama 3.3 70B via Groq | Structured reasoning | 97.3% | +20.0 p.p. | 0.83 s | 100.0% |
| Llama 3 8B via Ollama | Direct | 38.7% | - | 2.83 s | 98.7% |
| Llama 3 8B via Ollama | Structured reasoning | 72.0% | +33.3 p.p. | 35.69 s | 100.0% |

The hosted model gives the best quality-latency balance in this run. The local model shows a larger accuracy improvement from structured prompting, but its structured-mode latency is substantially higher.

### Scoring audit

The raw CSV preserves the recorded `score` column and an independently audited `audited_score` column. The audited evaluator counts four mathematically equivalent numeric responses as correct, including `7.0710678118654755` versus `5√2` and `0.0769` versus `1/13`. The headline results above use `audited_score`.

## Interpretation

The experiment is consistent with the hypothesis that requiring intermediate written steps can improve final-answer accuracy on this task set. The effect is especially visible for the smaller local model. However, the prompt also asks the model to produce more tokens and to follow additional formatting instructions. The result therefore reflects a combined change in reasoning budget, output length, and response contract.

The project should use the term “structured reasoning” rather than presenting the output as definitive explainability. A generated explanation can be incomplete, post hoc, or internally inconsistent even when its final answer is correct. A stronger explainability study would require independent verification of intermediate claims, faithfulness tests, and a larger, held-out evaluation set.

## Limitations and reproducibility

- The dataset is hand-authored and small; five tasks per category cannot support precise category-level generalization claims.
- The answer evaluator is deterministic but not a formal proof checker. It can accept mathematically equivalent strings that are outside the intended domain unless the task author has constrained the answer format.
- Provider latency includes network and serving conditions for Groq and local hardware conditions for Ollama. These measurements are not portable across machines.
- The benchmark is not a paired statistical significance study across multiple random seeds or repeated model generations.
- Model and provider versions, hardware, prompt wording, and temperature should be recorded for every future run.
- API credentials must be supplied through environment variables and must never appear in notebook cells or committed files.

## Conclusion

LLM-Tutor is a compact project for demonstrating evaluation engineering: it defines a benchmark, preserves per-response evidence, separates correctness from format compliance, and exposes the accuracy-latency trade-off between local and hosted inference. It is suitable for a GitHub portfolio and as a secondary project on a quantitative-finance CV.
