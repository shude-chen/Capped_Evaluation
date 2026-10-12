# Capped Evaluation under Leakage and Repeated Feedback

A reproducible **synthetic study** of statistical reliability in AI evaluation, inspired by [CapBencher (Ishida et al., ICML 2026)](https://arxiv.org/abs/2505.18102).

The experiments examine partial label leakage, repeated hypothesis testing, and feedback-driven model selection. A simplified evaluation task with a known 50% expected matching cap allows exact binomial tests and Monte Carlo simulations of detection sensitivity, repeated testing, and test-set selection overfitting.

**[View the study, results, and reproduction instructions](capped-evaluation-pilot/)**

## Project files

- [Overview and quick start](capped-evaluation-pilot/README.md)
- [English report and results](capped-evaluation-pilot/report.md)
- [Methods and statistical assumptions](capped-evaluation-pilot/METHODS.md)
- [Python source code](capped-evaluation-pilot/run_experiment.py)

## Scope and transparency

The experiments use synthetic data, not real LLM inference, model training, or multi-agent workflows. This is a preliminary, reproduction-oriented investigation rather than an original detection method or a full replication of CapBencher. The randomized-answer construction and core statistical tests are attributed to the cited work.

Implementation and execution were assisted by AI. The full code, assumptions, results, and limitations are documented so readers can inspect and reproduce the experiments.
