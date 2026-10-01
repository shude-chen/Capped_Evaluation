# Capped Evaluation under Leakage and Repeated Feedback

**Synthetic pilot • AI-assisted implementation • 2 October 2026 • Shude Chen application preparation**

## Purpose and status

This preparatory exercise explores how a known population performance cap supports leakage detection, and how repeated testing changes alarm probabilities. It contains no real LLM outputs, no model training and no proprietary data. It is inspired by CapBencher; it is neither a full replication nor an original research contribution. The applicant should rerun the code and be able to explain each assumption before including it in an application.

## Method

Each question admits two rule-compliant outputs, such as the correct arithmetic sum minus or plus one. The evaluator independently chooses one by a fair coin as the stored target. A label-independent predictor therefore has expected match rate 0.5. This is a population cap: finite-sample scores can exceed it by chance. Alarms use a one-sided exact binomial test at nominal alpha=0.05. At n=500, rejection requires at least 269 correct answers (53.8%).

Each simulation condition has 20,000 independent trials. Seed: 20261002. Monte Carlo confidence intervals are 95% Wilson intervals for the trial-level alarm rate, not confidence intervals for the task accuracy. Simulations sample binomial counts directly where the score distribution is analytically known; an additional attack uses explicit question and prediction arrays.

## 1. Partial label leakage

Each example independently exposes its realized target with probability q. A leaked example always matches; an unexposed example matches with probability 0.5. Thus the expected match rate is 0.5+0.5q. This isolates statistical power under ideal task-solving ability.

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

At 10% leakage, power increases from 72.26% at 500 examples to 99.75% at 2,000. At 2% leakage, even 5,000 examples give only 40.42% power. A non-significant alarm therefore does not establish absence of leakage. These numbers are conditional on this toy model, not forecasts of LLM detection performance.

## 2. Repeated selection from fixed candidates

At n=500, query K independent random predictors and choose the one with the highest score. Candidates are fixed before feedback, but the selected identity is feedback-dependent. A fresh independent test set evaluates generalization. The Bonferroni threshold uses alpha/K, accounting for search across a prespecified family; it is not a guarantee for arbitrary feedback-adaptive training.

| Candidates | Mean selected public score | Mean fresh score | Alarm with single-test cutoff | Alarm with family correction |
|---:|---:|---:|---:|---:|
| 1 | 50.02% | 49.98% | 5.21% | 5.21% |
| 5 | 52.60% | 50.01% | 22.27% | 4.39% |
| 20 | 54.17% | 50.01% | 63.53% | 4.79% |
| 100 | 55.60% | 49.99% | 99.41% | 3.69% |
| 500 | 56.77% | 50.00% | 100.00% | 4.81% |

The public score rises to 55.60% after selecting among 100 candidates while fresh performance stays near 50%. This is selection overfitting without direct label access. The elevated alarm rate should not be called proof of intentional cheating, or automatically a detector false positive: the selected predictor has already used test feedback. Family correction asks whether any candidate was unusually good relative to the prespecified search process.

## 3. Repeated inspection of a fixed predictor

The fixed predictor is tested on nested prefixes of 50, 100, 250, 500, 1,000, 2,000 and 5,000 examples. Predictions and the schedule are independent of the hidden targets. Compare a 5% threshold at every look with alpha/7 at each look. Bonferroni provides at-most-5% family error here despite dependence among nested looks, and can be conservative.

| Leakage probability | Test policy | Any alarm by 5,000 examples | 95% Monte Carlo CI |
|---:|---|---:|---:|
| 0.00% | naive | 18.70% | 18.17%–19.25% |
| 0.00% | bonferroni_looks | 3.06% | 2.83%–3.31% |
| 5.00% | naive | 98.02% | 97.82%–98.21% |
| 5.00% | bonferroni_looks | 87.32% | 86.85%–87.77% |
| 10.00% | naive | 100.00% | 99.98%–100.00% |
| 10.00% | bonferroni_looks | 100.00% | 99.98%–100.00% |

Under no leakage, repeated nominal 5% testing alarms in 18.71% of trials; correction reduces this to 3.06%. At 5% leakage, detection falls from 98.02% to 87.32%. Thus controlling repeated-look errors has a power cost. These guarantees require the fixed-predictor assumptions above.

## 4. Explicit adaptive feedback demonstration

On 500 explicit tasks, a baseline all-zero prediction receives an exact integer correct-count score. Flip one coordinate relative to that baseline per subsequent query. A +1 or -1 difference reveals that coordinate’s private target. Exactly 501 observations reconstruct all 500 target bits without reading the label array in the attack. The final score is computed offline for audit; it does not require an additional observation to infer it.

The reused-set match rate is 100%. For 5,000 new task IDs, a fixed default response gives 2513 matches (50.26%); its one-sided binomial p-value is 0.3618. This one demonstration illustrates an information channel, not an estimated attack success rate over diverse realistic systems.

The example assumes exact scores, unlimited queries and coordinate-level prediction control. It does not demonstrate real coding-agent behavior or an attack on an external service. Score rounding, noise, budget limits and correlated model outputs are not studied.

## Verification and reproducibility

A second complete run with the same seed reproduced all numerical JSON and CSV outputs byte-for-byte.

Threshold minimality is checked for all configured n and alpha values. Monte Carlo rates are compared against exact binomial and maximum-score distributions; the largest discrepancy is 3.23 Monte Carlo standard errors (verification tolerance: 5). The feedback routine asserts exact reconstruction. Environment and a source checksum are recorded in summary.json. Run the command in README.md to reproduce the results.

## Interpretation for the doctoral application

The strongest use is as a small reproducible reading exercise showing understanding of finite-sample uncertainty, selection bias and repeated testing. It does not validate the enterprise knowledge-write-back proposal and should be a separate supplementary note. CapBencher already studies leaderboard hacking, so neither leaderboard reuse nor the basic detection principle is claimed as a new research gap. Establishing novelty would require broader literature review and a materially different problem or method.

## Limitations and next experiments

- No natural-language understanding, LLM sampling, trained models or calibration errors are modeled.
- Hidden random targets are independent and the cap is exactly known; real designs may violate these assumptions.
- Leakage is independent per example and perfectly exploited; weaker memorization or imperfect task solving can reduce detection power.
- Candidate scores are independent; real candidate models often have correlated errors.
- Bonferroni is an elementary baseline, not a new or optimized detector. Family control for fixed candidates must not be generalized to adaptively changed models on reused labels.
- A capped score exceeding the threshold signals an assumption violation or feedback use in this setting; it does not identify intent or prove a particular contamination mechanism.
- No enterprise-memory propagation or partial-human-feedback results have been obtained.

## Reference

T. Ishida, T. Lodkaew, and I. Yamane. *CapBencher: Give Your LLM Benchmark a Built-in Alarm for Test-Set Overfitting*. ICML 2026, arXiv:2505.18102v7. https://arxiv.org/html/2505.18102v7. Section 2.1 motivates randomized answers and the one-sided binomial test; Section 3 also examines leaderboard hacking.
