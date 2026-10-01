# Capped Evaluation: Synthetic Pilot

Prepared for Shude Chen's exploration of Takashi Ishida's work. This is an
AI-assisted implementation and execution of a preparatory exercise. It is not
an original research contribution, an LLM experiment, or a full CapBencher
replication. The applicant should rerun and understand it before presenting it.

## Run

```bash
python -m pip install -r requirements.txt
python run_experiment.py --out results --repeats 20000 --seed 20261002
```

CPU only; no API key, model weights, GPU or company data. Python 3.11+ recommended.
Tested versions are recorded in results/summary.json. All conditions use 20,000
Monte Carlo trials, except the explicit coordinate-feedback attack, which is one
deterministic reconstruction demonstration on a randomly generated task set.

## 这个实验做了什么

题目例如：计算 12+8，允许输出正确和的减一值或加一值，即19或21。
评价方事先用独立公平硬币选择一个作为该题的匹配标签。两个答案都遵守
题目规则，但只有一个会匹配隐藏标签。因此，不能接触隐藏随机位的预测器
在每道题上的期望匹配率为50%。50%是期望上限，不是有限样本的硬上限。

正常情况用单侧精确二项检验判断是否显著高于50%。泄漏情况则让每道题
以概率q获得该题的隐藏标签，其余题仍猜测。该设定的期望匹配率是
0.5+0.5q。它只考察统计检测能力，没有语言理解困难。

比较三类情况：正常预测、部分标签泄漏、反复使用评价分数选模型。
另外检查同一预测器在7个累计样本量处反复接受检验，以及一个精确分数
反馈下的标签重构案例。所有CSV都同时给出实测比例和95% Wilson区间；
单次检验和固定候选选择还有精确理论概率可作核对。

## Statistical design

1. **Single evaluation and leakage:** n = 50, 100, 250, 500, 1000, 2000, 5000;
   q = 0, .02, .05, .10, .20, 1. For q=0 scores follow Bin(n,.5); for q>0
   scores follow Bin(n,.5+.5q). Row leakage is independently sampled, so q is
   a probability, not an exactly fixed fraction in each realization.
2. **Repeated model selection:** n=500; K=1,5,20,100,500 independent random
   candidate predictions committed before receiving scores. Choose the maximum
   score. Compare a single-test cutoff to a Bonferroni alpha/K cutoff. The
   score-space simulation is exact for these independent random bit-vectors,
   not a simulation of trained or correlated models. A fresh independent test
   set tests whether the selected score gain generalizes.
3. **Repeated inspection:** the same fixed predictor is evaluated on nested
   prefixes at the seven n values above. Compare alpha=.05 at every look to
   alpha/7. Family error control is valid here because the predictor and look
   schedule are fixed independently of labels; it does not cover arbitrary
   feedback-adaptive predictors evaluated on reused data.
4. **Adaptive score feedback:** on 500 explicit tasks, obtain a base score and
   flip one predicted bit per query relative to that base. With exact integer
   correct-count feedback, every +/-1 score difference identifies a private
   target bit. 501 observations reconstruct all 500 bits. Offline evaluation
   of the final vector is an audit, not another attack query. On new IDs use
   the default minus-one answer. This assumes unusually informative feedback,
   unrestricted queries and per-example prediction control. It is not a claim
   about real LLMs or real evaluation servers.

The count cutoff is the smallest integer k with
P[Bin(n,.5) >= k] <= alpha. For n=500 and alpha=.05, k=269 (53.8%).
For fixed candidates the exact probability of any alarm is
1-(1-P[Bin(n,.5)>=k])**K.

Important terminology: the selected predictor depends on test feedback.
Its elevated reused-test score is **test-set selection overfitting**, not
evidence of direct training-data leakage or intentional deception. An alarm
after selecting many candidates is not automatically a detector's false
positive. The corrected threshold accounts for searching across a prespecified
candidate family. Only the q=0 fixed-predictor repeated-inspection experiment
unambiguously measures repeated-look false positives under the stated null.

## Files

- `run_experiment.py`: all simulation, exact calibration and plotting code.
- `report.md`: English methods, numerical results, limitations and discussion.
- `results/*.csv`: condition-level counts, rates and uncertainty intervals.
- `results/summary.json`: full results, environment, seed and source checksum.
- `results/feedback_attack.json`: explicit attack result.
- `results/toy_task_examples.json`: all 500 demo questions and private labels,
  exposed for offline audit only. The attack function does not read them.
- `results/pilot_results.png` and `.svg`: figure for reading or export.

## Relation to application materials

This can accompany a discussion of capped evaluation and repeated testing.
It does not yet test enterprise knowledge write-back, long-horizon error
propagation, partial human supervision, or the proposed doctoral project.
Do not describe it as evidence that the enterprise workflow proposal works.
An extension would require a separate evolving-memory experiment.

## Source

T. Ishida, T. Lodkaew, I. Yamane. *CapBencher: Give Your LLM Benchmark a
Built-in Alarm for Test-Set Overfitting*. ICML 2026, arXiv:2505.18102v7.
https://arxiv.org/html/2505.18102v7

The capped-answer construction and one-sided binomial test are drawn from that
paper. The current pilot uses elementary multiple-testing controls and simple
feedback examples to build understanding. It makes no novelty claim and does
not establish a gap in the literature. The paper itself studies leaderboard
hacking with real model merging, so that subject is not an untouched problem.
