#!/usr/bin/env python3
"""A synthetic capped-evaluation pilot, inspired by CapBencher (not a replication).

Run: python run_experiment.py --out results --repeats 20000 --seed 20261002
No LLM/API/GPU or proprietary data are used. See README.md for assumptions.
"""
from pathlib import Path
import argparse
import csv
import json
import platform
import hashlib

import numpy as np
import scipy
from scipy.stats import binom, norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def cutoff(n, alpha):
    """Smallest integer k with P[Bin(n,.5)>=k] <= alpha; n+1 if impossible."""
    return int(binom.isf(alpha, n, .5)) + 1


def wilson(hits, total):
    z = norm.ppf(.975)
    p = hits / total
    d = 1 + z*z / total
    c = (p + z*z / (2*total)) / d
    h = z*np.sqrt(p*(1-p)/total + z*z/(4*total*total)) / d
    return float(c-h), float(c+h)


def rate_record(hits, total):
    lo, hi = wilson(hits, total)
    return {"hits": int(hits), "trials": total, "rate": hits/total,
            "ci95_low": lo, "ci95_high": hi}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def row_level_demo(rng, n, fresh_n):
    """Demonstrate exact-score feedback leakage using n+1 queries.

    Each task has two legitimate outputs, sum-1 and sum+1. Its stored target
    chooses one by a private fair coin. The attack never reads stored targets;
    only the evaluator reads them. A one-coordinate flip reveals that target
    from the +/-1 change in the reported correct-count score.
    """
    a = rng.integers(2, 100, n)
    b = rng.integers(2, 100, n)
    private_bits = rng.integers(0, 2, n, dtype=np.int8)
    base = np.zeros(n, dtype=np.int8)
    def evaluator(prediction):
        return int(np.sum(prediction == private_bits))
    initial_score = evaluator(base)
    inferred = np.empty(n, dtype=np.int8)
    queries = 1
    for j in range(n):
        candidate = base.copy()
        candidate[j] = 1
        delta = evaluator(candidate) - initial_score
        assert delta in (-1, 1)
        inferred[j] = int(delta == 1)
        queries += 1
    assert evaluator(inferred) == n
    # The n+1 observations suffice to infer the final score; evaluating the
    # final solution here is an offline diagnostic, not an extra oracle query.
    examples = [{"id": i, "question": f"Compute {int(a[i])}+{int(b[i])}; return the sum minus 1 or plus 1.",
                 "valid_answers": [int(a[i]+b[i]-1), int(a[i]+b[i]+1)],
                 "private_target_bit": int(private_bits[i]),
                 "feedback_inferred_bit": int(inferred[i])} for i in range(n)]
    fresh_labels = rng.integers(0, 2, fresh_n)
    # Unseen IDs: no stored bits; fallback returns the minus-one alternative.
    fresh_correct = int(np.sum(fresh_labels == 0))
    return examples, {"public_n": n, "feedback_queries": queries,
                      "public_accuracy": 1., "fresh_n": fresh_n,
                      "fresh_correct": fresh_correct,
                      "fresh_accuracy": fresh_correct/fresh_n,
                      "fresh_p_value": float(binom.sf(fresh_correct-1, fresh_n, .5)),
                      "oracle": "exact integer correct count", "fresh_fallback": "minus-one output"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("results"))
    ap.add_argument("--repeats", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=20261002)
    args = ap.parse_args()
    if args.repeats < 100:
        raise ValueError("Use at least 100 repeats.")
    args.out.mkdir(parents=True, exist_ok=True)
    seeds = np.random.SeedSequence(args.seed).spawn(4)
    leak_rng, select_rng, seq_rng, demo_rng = [np.random.default_rng(s) for s in seeds]
    ns = [50, 100, 250, 500, 1000, 2000, 5000]
    qs = [0., .02, .05, .10, .20, 1.]
    alpha = .05

    # Check exact thresholds, including the n+1 "no possible rejection" case.
    for n in ns + [1, 2, 3]:
        for a in [alpha, alpha/500, alpha/len(ns)]:
            k = cutoff(n, a)
            assert binom.sf(k-1, n, .5) <= a + 1e-12
            if k > 0:
                assert binom.sf(k-2, n, .5) > a
    assert cutoff(500, alpha) == 269

    leakage = []
    for n in ns:
        k = cutoff(n, alpha)
        for q in qs:
            # Each example independently leaks its realized target with
            # probability q. Otherwise the score is a fair-coin match.
            # Exact marginal score distribution, not a trained language model.
            p = .5 + .5*q
            counts = leak_rng.binomial(n, p, args.repeats)
            leakage.append({"n": n, "leak_probability": q, "expected_accuracy": p,
                            "cutoff_correct": k, "observed_mean_accuracy": float(np.mean(counts)/n),
                            "exact_alarm_probability": float(binom.sf(k-1, n, p)),
                            **rate_record(np.sum(counts >= k), args.repeats)})
    write_csv(args.out / "leakage.csv", leakage)

    selection = []
    n = 500
    for candidates in [1, 5, 20, 100, 500]:
        # Candidates are independent random bit-vectors fixed before feedback.
        # Conditional on any fair target vector, scores are iid Bin(n,.5).
        # Score-space sampling is distributionally exact for this toy setting.
        maxima = select_rng.binomial(n, .5, (args.repeats, candidates)).max(axis=1)
        fresh = select_rng.binomial(n, .5, args.repeats)
        for method, a in [("naive", alpha), ("bonferroni", alpha/candidates)]:
            k = cutoff(n, a)
            one_tail = float(binom.sf(k-1, n, .5))
            exact = float(-np.expm1(candidates*np.log1p(-one_tail)))
            selection.append({"n": n, "candidates": candidates, "method": method,
                              "cutoff_correct": k, "mean_selected_public_accuracy": float(maxima.mean()/n),
                              "mean_fresh_accuracy": float(fresh.mean()/n),
                              "exact_any_alarm_probability": exact,
                              **rate_record(np.sum(maxima >= k), args.repeats)})
    write_csv(args.out / "selection.csv", selection)

    sequential = []
    for q in [0., .05, .10]:
        cumulative = np.zeros(args.repeats, dtype=int)
        draws = []
        last_n = 0
        for n in ns:
            cumulative += seq_rng.binomial(n-last_n, .5+.5*q, args.repeats)
            draws.append(cumulative.copy())
            last_n = n
        for method, a in [("naive", alpha), ("bonferroni_looks", alpha/len(ns))]:
            first = np.full(args.repeats, -1, dtype=int)
            for n, counts in zip(ns, draws):
                first[(first < 0) & (counts >= cutoff(n, a))] = n
            sequential.append({"leak_probability": q, "method": method, "looks": len(ns),
                               "max_n": ns[-1], **rate_record(np.sum(first >= 0), args.repeats),
                               **{f"detected_by_{n}": float(np.mean((first >= 0) & (first <= n))) for n in ns}})
    write_csv(args.out / "sequential.csv", sequential)

    examples, attack = row_level_demo(demo_rng, 500, 5000)
    (args.out / "feedback_attack.json").write_text(json.dumps(attack, indent=2)+"\n")
    (args.out / "toy_task_examples.json").write_text(json.dumps(examples, indent=2)+"\n")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.3), layout="constrained")
    for q in qs[:-1]:
        rows = [r for r in leakage if r["leak_probability"] == q]
        axs[0].plot(ns, [r["rate"] for r in rows], marker="o", label=f"{q:.0%} leakage")
    axs[0].axhline(alpha, color="gray", ls="--", lw=1)
    axs[0].set(xscale="log", xlabel="Evaluation examples", ylabel="Alarm probability",
               title="A  Partial label leakage", ylim=(-.02, 1.03))
    axs[0].legend(fontsize=8)
    for method, label in [("naive", "Single-test threshold"), ("bonferroni", "Corrected across candidates")]:
        rows = [r for r in selection if r["method"] == method]
        axs[1].plot([r["candidates"] for r in rows], [r["rate"] for r in rows], marker="o", label=label)
    axs[1].axhline(alpha, color="gray", ls="--", lw=1)
    axs[1].set(xscale="log", xlabel="Candidates queried (n = 500)", ylabel="Any alarm probability",
               title="B  Repeated model selection", ylim=(-.02, 1.03))
    axs[1].legend(fontsize=8)
    rows = [r for r in sequential if r["leak_probability"] == 0]
    for r, label in zip(rows, ["Repeated 5% test", "Corrected across 7 looks"]):
        axs[2].plot(ns, [r[f"detected_by_{n}"] for n in ns], marker="o", label=label)
    axs[2].axhline(alpha, color="gray", ls="--", lw=1)
    axs[2].set(xscale="log", xlabel="Cumulative examples (no leakage)", ylabel="False alarm by this point",
               title="C  Repeated inspection", ylim=(-.005, .23))
    axs[2].legend(fontsize=8)
    fig.savefig(args.out / "pilot_results.png", dpi=180)
    fig.savefig(args.out / "pilot_results.svg")
    plt.close(fig)

    metadata = {"seed": args.seed, "repeats_per_condition": args.repeats, "alpha": alpha,
                "cap": .5, "sample_sizes": ns, "python": platform.python_version(),
                "numpy": np.__version__, "scipy": scipy.__version__, "matplotlib": matplotlib.__version__,
                "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    summary = {"metadata": metadata, "leakage": leakage, "selection": selection,
               "sequential": sequential, "feedback_attack": attack}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps({"metadata": metadata,
        "leakage_at_500": [r for r in leakage if r["n"] == 500],
        "selection": selection, "sequential": sequential, "feedback_attack": attack}, indent=2))


if __name__ == "__main__":
    main()
