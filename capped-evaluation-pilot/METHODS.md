# Capped Evaluation: Synthetic Pilot — Methods

This document describes the statistical assumptions, experiment design, and reproduction procedure used in the synthetic study. The evaluation construction is inspired by [CapBencher (Ishida et al., ICML 2026)](https://arxiv.org/html/2505.18102v7). Implementation and execution were assisted by AI; the simulations are not real LLM or multi-agent experiments and do not establish a new detection method or a full replication of the paper.

## Run

```bash
python -m pip install -r requirements.txt
python run_experiment.py --out results --repeats 20000 --seed 20261002
```

Python 3.11+ is recommended; execution is CPU-only and requires no API keys, GPU, model weights, or company data. Tested environment versions are recorded in `results/summary.json`. All simulation conditions use 20,000 Monte Carlo trials, except for one deterministic, explicit-score feedback reconstruction demonstration.

## Task construction

For example, given 12+8, the instruction allows 19 or 21 (the sum minus or plus one). The evaluator independently and privately selects one of these two valid options by fair coin. Without access to the private random choice, the *expected* match rate is 50%. The cap is on population expectation, not on every finite-sample score. The experiment uses an exact one-sided binomial test to decide whether a score significantly exceeds this expectation.

The study compares a clean predictor, partial private-label exposure, selection based on repeatedly observed scores, and nested repeated checks of a fixed predictor. The final feedback example is deliberately idealized. These mechanisms are statistical abstractions, not simulations of LLM semantic reasoning or training.

## Statistical design

1. **Single evaluation and leakage:** n = 50, 100, 250, 500, 1000, 2000, 5000; q = 0, .02, .05, .10, .20, 1. With q=0, matching counts follow Bin(n, .5); with independent label exposure probability q, they follow Bin(n, .5 + .5q). The exposure fraction varies by realization.
2. **Repeated selection from fixed candidates:** At n=500, K = 1, 5, 20, 100, 500 independent random candidate prediction vectors are fixed prior to feedback. Select the candidate with maximum evaluation score. Compare a standard alpha threshold against Bonferroni alpha/K, then measure performance on a fresh independent set. Direct binomial-count sampling is distributionally exact for this simplified independent-candidate setting, but is not a model of correlated trained predictors.
3. **Repeated inspection:** One fixed predictor is evaluated on nested prefixes at the seven sample sizes above. Compare a nominal alpha=.05 test at each look against alpha/7. Under the fixed-predictor and predetermined-look assumptions, the family-wise false-alarm rate is controlled conservatively by the correction. No guarantee is made for arbitrary feedback-adaptive predictors on the same test labels.
4. **Explicit adaptive score feedback:** On 500 task instances, obtain a baseline exact integer correct-count score. Flip each predicted bit in one separate query relative to the baseline; its +1/-1 change reveals the corresponding hidden bit. With 501 feedback observations the demonstration reconstructs all hidden bits, without giving the simulated attacker direct access to them. A final score is computed offline for audit, not obtained with another attack query. The example assumes exact scores, unlimited querying, and fine-grained output control, which do not characterize most real services.

The exact rejection cutoff is the smallest integer k such that P[Bin(n, .5) >= k] <= alpha. At n=500 and alpha=.05, k=269 (53.8%). For K independent fixed candidates, the probability of at least one nominal alarm is 1-(1-p)^K, where p is the single-candidate tail probability.

## Interpretation of alarms

After candidates are selected using evaluation feedback, a higher score on the reused set indicates **test-set selection overfitting**; it does not by itself show direct training-data leakage or intentional wrongdoing. An alarm after selection is also not automatically a false positive under the fixed-predictor null, because the selected predictor depends on the test feedback. Multiple-testing corrections account for the specific prespecified search family in this study, not arbitrary model development processes.

## Artifacts

- `run_experiment.py`: experiment generation and plotting source.
- `report.md`: English report with results, uncertainty intervals, and interpretation.
- `results/*.csv`: simulated outcomes, trial counts, rates, and 95% Wilson intervals.
- `results/summary.json`: environment, seed, parameters, and source checksum.
- `results/feedback_attack.json`: explicit feedback reconstruction summary.
- `results/toy_task_examples.json`: 500 audit examples and hidden targets; these are disclosed offline only, not passed to the attack function.
- `results/pilot_results.png` and `.svg`: experiment figures.

## Scope and limitations

The experiment isolates evaluation behavior under idealized assumptions. It does not test real LLM inference or multi-agent workflow dependencies, propagation of incorrect intermediate outputs, selective verification, or real human-review processes. Therefore the results are not evidence of end-to-end agent reliability. Extending this work to complex AI systems requires a new experimental design and independent held-out evaluation.

## Source

T. Ishida, T. Lodkaew, I. Yamane. *CapBencher: Give Your LLM Benchmark a Built-in Alarm for Test-Set Overfitting*. ICML 2026, [arXiv:2505.18102v7](https://arxiv.org/html/2505.18102v7). The randomized answer idea and elementary statistical testing are attributed to the original work, which also examines real-model leaderboard feedback effects.
