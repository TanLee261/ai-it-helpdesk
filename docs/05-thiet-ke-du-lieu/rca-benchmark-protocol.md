# RCA Benchmark Protocol

## Purpose and limits

This protocol evaluates whether the assistant answers when incident evidence supports a cause and abstains when it does not. The current incident corpus is synthetic and its root-cause labels are assumptions, not expert-verified operational truth. Report results as synthetic-benchmark results only.

## Dataset audit findings

- The current 50 incidents are grouped by category in the source file. The legacy split is not stratified: all 8 legacy test incidents are database incidents, while network and server/API have no test rows.
- Some linked tickets do not describe the assigned service or incident (for example, marketing-campaign and graphics-rendering tickets linked to database/backup scenarios). These cases must be excluded or corrected before treating the labels as valid RCA ground truth.
- The current logs often echo ticket symptoms and generic markers such as an anomaly threshold; these are not automatically cause-specific evidence. Metric signals can support broad symptom classes, but do not automatically prove every detailed root-cause label.
- Run `python3 scripts/audit_incident_links.py` to produce `data/eval/incident_link_audit.csv`. The current audit flags 39/50 low lexical-overlap links for manual review, and all 50 service labels are constant by service. Treat overlap flags as review cues only; semantic mismatches can exist even when overlap is high.
- Detailed counts and examples are recorded in `benchmarks/reports/rca_data_audit_v3.md`. Existing legacy files are preserved; no rows were automatically repaired or removed.
- The audit CSV intentionally omits full ticket text and root-cause labels. Use ticket IDs to inspect source rows; never add the audit artifact to the retrieval/knowledge index.

## Versioned split

Generate a deterministic category-stratified split without rewriting `incidents.jsonl` or the legacy `rca_review.csv`:

```bash
python3 scripts/prepare_rca_benchmark_v2.py
```

The outputs are `data/eval/benchmark_v2_splits.csv` and `data/eval/benchmark_v2_review.csv`. Seed: `20261014`. The test review template starts unreviewed intentionally; labels from a different legacy test membership are not copied over.

Treat `train` as the source for development baselines, `dev` for prompt/rule tuning, and `test` as locked until the protocol and system configuration are frozen. Do not change the split after inspecting test predictions.

## V2 disposition and blind evidence review

V2 has already been used for tuning and its test metrics have been inspected. Keep V2 as an exploratory/dev artifact; do not use its test scores as the final held-out result. A blind evidence-review worksheet for all current incidents can be regenerated with:

```bash
python3 scripts/prepare_evaluation_review.py
```

The output is `data/eval/incident_evidence_review_v3.csv`. It includes linked ticket text, incident symptoms/window, runbook titles, and in-window log/metric samples, but intentionally omits the generated root-cause label and model prediction. Reviewers should assess the evidence first, write their own cause hypothesis and evidence IDs, and only then compare that judgment with the synthetic label in a separate pass. The script preserves populated review fields when rerun.

The review sheet now includes `log_provenance`, `log_evidence_scope`, `metric_provenance`, and `metric_evidence_scope`. All current log and metric records are generated from templates/service profiles. `logs_valid` and `metrics_valid` are review judgments about whether the records are usable for the incident window/service; they do not by themselves establish causality. The generated logs are generic service-health/error signals, and generated metrics are not independent operational measurements. Do not describe either as production-observed evidence or as proof of a detailed root cause.

Do not promote an incident to a gold evaluation case based only on matching IDs, service metadata, or automated lexical-overlap flags. Exclude or replace mismatched cases in a new dataset version; do not silently repair V2 after seeing its scores. For a final result, create a fresh held-out test after review and configuration freeze, with at least 20 independent incidents as a practical minimum for an MVP study. Query paraphrases from one incident are repeated measurements, not independent incident samples; report incident-level counts and scores alongside query-level metrics.

## Sufficiency rubric

Label sufficiency before inspecting model output:

- `sufficient`: ticket context is a real incident for the assigned service; at least one in-window log and one in-window metric belong to that same service/incident; together they support one declared cause class at the intended label granularity; and no plausible competing cause is equally supported.
- `insufficient`: evidence is missing, outside the window, mismatched to service/incident, only generic symptoms, contradictory, or supports multiple plausible causes without distinguishing them.
- `exclude`: ticket is informational/non-incident, service linkage is wrong, or the synthetic ground truth cannot be justified. Excluded rows are not scored and should be repaired in a new dataset version, not silently relabeled.

Record the evidence IDs and a concise rationale for every sufficiency label. This rubric is a human-review protocol; a simple presence check for one log plus one metric is not by itself proof of sufficiency.

## Baselines and leakage controls

Compare at least (1) a pre-registered, deterministic rule baseline that reads only ticket text and in-window operational evidence, (2) nearest historical-ticket retrieval using training incidents only, and (3) the RAG+LLM system. All methods use the exact same test incidents and evidence window. Exclude the current ticket from nearest-neighbor candidates. Never use `root_cause_label`, `label_status`, review annotations, incident IDs, or runbook IDs as prediction features. Freeze rules and retrieval settings using development data before test.

Because current synthetic labels are largely assigned by service and the generated logs are generic, a service-to-label lookup is leakage-prone and is not an acceptable baseline. Baselines should abstain when their predeclared evidence conditions are not met.

The initial exploratory rule baseline currently maps the synthetic metric names/thresholds directly to the same cause classes used by the scenario generator. Its observed 7/7 exact match is therefore a data-generation shortcut/ceiling, not credible evidence that a diagnostic rule generalizes. Keep it as a leakage/simplicity check, but add independently authored decoy scenarios and revise the metric-to-label generation before presenting baseline superiority as a research result.

## Trace fields

For each model run, retain a JSONL trace with: incident/request ID; retrieved evidence IDs and source types; evidence IDs actually placed in the prompt; raw LLM response before parsing/validation; validated response after validator; model and retrieval configuration; timestamps and latency. Keep traces local, redact sensitive data, and never put hidden ground-truth labels into prompts.

The API trace is disabled by default. To enable locally, set `RCA_TRACE_PATH=./data/eval/rca_traces.jsonl` in the environment (or `.env`) and restart the backend. The trace stores raw model output and validated RCA response, so keep this file local and do not commit or share it without checking for sensitive information.

## Reporting

Fill the V2 review CSV, then run:

```bash
python3 benchmarks/evaluate_rca_matrix.py
```

Report the 2x2 matrix and counts, correct-abstention recall on insufficient cases, abstention precision, false-abstention rate and answer coverage on sufficient cases, RCA accuracy among answered sufficient cases, and unsupported-fact rate. Always include numerators/denominators. A model abstention on a sufficient case is a false abstention, not an incorrect predicted cause; do not count it in conditional RCA accuracy.
