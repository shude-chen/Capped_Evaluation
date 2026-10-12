# Capped Evaluation under Leakage and Repeated Feedback

**Reproducible synthetic study • AI-assisted implementation • 2 October 2026**

## Purpose and status

This report documents controlled simulations of capped evaluation, label leakage, repeated hypothesis testing, and selection based on reused test feedback. The study is inspired by CapBencher (Ishida et al., ICML 2026) and examines evaluation reliability under explicit assumptions. It includes no real LLM outputs, model training, or proprietary data. The study is not a full replication of CapBencher and does not introduce a new detection method. Code, numerical outputs, and assumptions are supplied for independent reproduction.

## Method

Each question admits two rule-compliant outputs, such as the correct arithmetic sum minus or plus one. The evaluator independently chooses one with a private fair coin as its stored target. A label-independent predictor therefore has an expected match rate of 0.5. This is a population expectation: finite-sample scores can exceed it by chance. Alarms use a one-sided exact binomial test at nominal alpha=0.05. At n=500, rejection requires at least 269 correct answers (53.8%).

Each simulation condition has 20,000 independent trials (seed 20261002). Monte Carlo confidence intervals are 95% Wilson intervals for the *trial-level alarm rate*, not intervals for task accuracy. Simulations sample binomial counts directly where the score distribution is analytically known; an additional feedback example uses explicit question and prediction arrays.

## 1. Partial label leakage

Each example independently exposes its realized target with probability q. A leaked example always matches; an unexposed example matches with probability 0.5. The expected match rate is therefore 0.5 + 0.5q. This isolates statistical detection power under idealized task-solving ability.

| Examples | Leakage probability | Mean task match rate | Alarm rate | 95% Monte Carlo CI | Exact alarm probability |
|---:|---:|---:|---:|---:|---:|
| 500 | 0.00% | 50.00% | 4.74% | 4.45%–5.04% | 4.89% |
| 500 | 2.00% | 50.99% | 11.19% | 10.76%–11.63% | 11.35% |
| 500 | 5.00% | 52.52% | 29.96% | 29.33%–30.60% | 29.57% |
| 500 | 10.00% | 55.02% | 72.26% | 71.64%–72.88% | 72.08% |
| 500 | 20.00% | 60.02% | 99.80% | 99.73%–99.85% | 99.79% |
| 2000 | 0.00% | 50.00% | 4.57% | 4.29%–4.87% | 4.68% |
| 2000 | 2.00% | 51.01% | 21.80% | 21.23%–22.38% | 21.69% |
| 2000 | 5.00% | 52.51% | 71.58% | 70.95%–72.20% | 71.22% |
| 2000 | 10.00% | 55.01% | 99.75% | 99.67%–99.81% | 99.75% |
| 2000 | 20.00% | 60.00% | 100.00% | 99.98%–100.00% | 100.00% |
| 5000 | 0.00% | 50.00% | 4.95% | 4.65%–5.25% | 4.90% |
| 5000 | 2.00% | 51.00% | 40.42% | 39.75%–41.11% | 40.50% |
| 5000 | 5.00% | 52.50% | 97.04% | 96.79%–97.26% | 97.01% |
| 5000 | 10.00% | 55.00% | 100.00% | 99.98%–100.00% | 100.00% |
| 5000 | 20.00% | 60.00% | 100.00% | 99.98%–100.00% | 100.00% |

At 10% leakage, power increases from 72.26% at 500 examples to 99.75% at 2,000. At 2% leakage, even 5,000 examples give only 40.42% power. A non-significant result does not establish the absence of leakage. These outcomes are conditional on the simplified model and do not predict performance in real LLM evaluation.

## 2. Repeated selection from fixed candidates

At n=500, query K independent random predictors and select the highest score. All candidates are fixed before feedback, but the selected candidate depends on test feedback. Generalization is evaluated on a fresh independent set. The Bonferroni threshold uses alpha/K for the prespecified family; it does not guarantee control for arbitrary feedback-adaptive model training.

| Candidates | Mean selected public score | Mean fresh score | Alarm with single-test cutoff | Alarm with family correction |
|---:|---:|---:|---:|---:|
| 1 | 50.02% | 49.98% | 5.21% | 5.21% |
| 5 | 52.60% | 50.01% | 22.27% | 4.39% |
| 20 | 54.17% | 50.01% | 63.53% | 4.79% |
| 100 | 55.60% | 49.99% | 99.41% | 3.69% |
| 500 | 56.77% | 50.00% | 100.00% | 4.81% |

After selection among 100 candidates, the public score averages 55.60%, but fresh performance remains near 50%. This is *test-set selection overfitting* without direct label access. An elevated alarm rate after selection is not automatically a detector false positive or proof of intentional cheating. Family correction addresses a prespecified search over fixed candidates.

## 3. Repeated inspection of a fixed predictor

The same predictor is inspected at nested prefixes of 50, 100, 250, 500, 1,000, 2,000, and 5,000 examples. The predictions and inspection schedule are fixed independently of hidden targets. Compare nominal 5% testing at every look with alpha/7 at each look. Under these assumptions, Bonferroni provides at-most-5% family error control, potentially conservatively.

| Leakage probability | Test policy | Any alarm by 5,000 examples | 95% Monte Carlo CI |
|---:|---|---:|---:|
| 0.00% | naive | 18.71% | 18.17%–19.25% |
| 0.00% | bonferroni_looks | 3.06% | 2.83%–3.31% |
| 5.00% | naive | 98.02% | 97.82%–98.21% |
| 5.00% | bonferroni_looks | 87.32% | 86.85%–87.77% |
| 10.00% | naive | 100.00% | 99.98%–100.00% |
| 10.00% | bonferroni_looks | 100.00% | 99.98%–100.00% |

Under no leakage, repeated nominal 5% testing raises the cumulative false-alarm rate to 18.71%; correction reduces it to 3.06%. At 5% leakage, detection declines from 98.02% to 87.32%. Reducing false alarms thus has a detection-power cost under the stated assumptions.

## 4. Explicit adaptive feedback demonstration

On 500 explicit tasks, a baseline all-zero prediction receives an integer correct-count score. Flipping one coordinate relative to that baseline in each subsequent query changes the score by +1 or -1, revealing the corresponding private target bit. Exactly 501 score observations suffice to reconstruct all 500 target bits without exposing the label array to the attack. The final score is calculated offline for audit, not obtained through another attack query.

The reused-set match rate is 100%. On 5,000 fresh task IDs, a fixed default response matches 2513 cases (50.26%); its one-sided binomial p-value is 0.3618. This single demonstration illustrates an information channel but is not an estimate of attack success on realistic systems.

The demonstration assumes exact scores, unlimited queries, and coordinate-level control. It does not model real coding agents, actual external services, score rounding, feedback noise, query limits, or correlated model outputs.

## Verification and reproducibility

A second complete run with the same seed reproduced numerical JSON and CSV results byte for byte. Threshold minimality is checked; Monte Carlo rates were compared with analytic binomial and maximum-score probabilities. The maximum discrepancy was 3.23 Monte Carlo standard errors (tolerance 5). The feedback routine asserts exact reconstruction. Environment versions and source SHA-256 are included in `results/summary.json`.

## Interpretation and research relevance

These experiments provide a reproducible example of how finite-sample uncertainty, repeated testing, and feedback-driven selection can affect reported performance. Their relevance to trustworthy AI is **methodological**: evaluation can mislead even when each individual test has a well-defined statistical rule. The project does not test LLM agents, downstream error propagation, or budgeted selective verification. Those would require separate benchmarks, models, and independent validation. CapBencher already examines real-model leaderboard hacking; this study does not claim a new detection principle or an unexplored research gap.

## Limitations and next experiments

- The study does not model natural-language understanding, real LLM sampling or training, or calibration errors.
- Hidden labels are independent with an exactly known population cap; real settings may differ.
- Leakage is independent per example and perfectly exploited; weaker leakage may be harder to detect.
- Candidate predictions are independent; real model outputs can be correlated.
- Bonferroni is an elementary baseline. Guarantees for fixed candidates do not automatically extend to arbitrarily adapted models evaluated on reused data.
- A statistically unusual score indicates that model assumptions should be questioned; it does not establish intent or pinpoint the source of contamination.
- No real-agent workflow, error-propagation, selective-verification, or human-feedback experiments have been performed.

## Reference

T. Ishida, T. Lodkaew, and I. Yamane. *CapBencher: Give Your LLM Benchmark a Built-in Alarm for Test-Set Overfitting*. ICML 2026, arXiv:2505.18102v7. https://arxiv.org/html/2505.18102v7. The randomized-answer design and one-sided binomial test are attributed to this work; the present experiments use simplified assumptions for reproducibility.
