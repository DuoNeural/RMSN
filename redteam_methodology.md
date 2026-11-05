## Red Team: Experimental Methodology

*Internal critique — DuoNeural Lab, Nov 05 2026. Actionable, no softening.*

---

### 1. External Baselines: The Biggest Methodology Gap

**What the paper does**: All comparisons are ablations of RMSN against itself (Morrison bracket removed, Clifford grades removed, workspace scale varied, Caputo order varied). No external architecture comparison.

**Why this is a problem**: Reviewers at any top ML venue (NeurIPS/ICLR/ICML) will ask: "RMSN-Small at 193M achieves val_ppl=50.0 on wikitext-103 after 100K steps — how does this compare to a comparably-sized Transformer, Mamba, or S4?" Without this number, the paper cannot make performance claims. §6.2 is careful to say "this is a proof-of-concept run, not an optimized training campaign" — but even a proof-of-concept needs a reference point.

**Minimum bar for submission**: One external comparison — even a rough one — at the same scale. Options in increasing effort:
- Reproduce a public wikitext-103 number for GPT-2 at 117M–345M (numbers are publicly available)
- Run a 1-day wikitext-103 run with a comparably-sized vanilla Transformer or Mamba-130M using the same tokenizer, batch size, and step count
- Cite existing reported numbers from the literature, clearly stating the comparison is not perfectly controlled

The claim RMSN is making is architectural, not performance-based. The paper can still succeed without winning on perplexity if it frames correctly: "We demonstrate the cascade phenomenon in a 193M model; whether this translates to competitive performance requires hyperparameter search and scale that is beyond this initial work."

---

### 2. Single-Run Concerns

**What the paper does**: Every result is a single training run. The ablations are single runs. The cascades are observed once per configuration.

**What this limits**: The cascade could be a random seed artifact. The 13.7% PPL gap in the Morrison bracket ablation could be run-to-run variance. The specific step at which the cascade fires (28K) could vary by thousands of steps.

**What's defensible**: The nature of the cascade (a qualitative change in Lyapunov exponent from near-zero to deep negative) is not a small-delta effect that would disappear under multiple seeds. Even if the step number varies, the phenomenon would still appear. The Morrison bracket ablation's overfitting curve (PPL degrades after step 10K) is similarly qualitative — a slight LR mismatch wouldn't reverse the direction of that curve.

**Recommendation**: Run the RMSN-193M (seed_repro) experiment with 2-3 different random seeds and report the cascade step as a range (e.g., "cascade fires at steps 24K–32K across seeds; PPL improvement is consistent"). This is 3-4 GPU-hours on p35122 and dramatically strengthens the cascade claim. The ablation seeds are less critical — the qualitative effect (presence/absence of cascade, presence/absence of overfitting) is robust.

---

### 3. Ablation Design: What's Missing

**What the paper ablates**: Morrison bracket (γ→0), Clifford algebra grades, global workspace scale (M_w), Caputo fractional order (α).

**What's not ablated**:

- **CliffordStalkBundle vs. standard projection**: Does the Clifford algebra matter *per se*, or is it enough to have any structured projection of the same dimensionality? A flat linear projection baseline (same parameter count as CliffordStalkBundle) would isolate the grade structure contribution.

- **FractionalCaputoBank vs. single exponential**: Does the multi-scale memory matter, or would a single exponential with the same parameter count match? This isolates the fractional calculus contribution.

- **Lyapunov monitoring independence**: The Lyapunov exponent is computed as a monitoring quantity. Is it possible the cascade is a consequence of the monitoring itself (e.g., via backprop through the aggregated γ)? Confirm γ is not in the backward graph for the perplexity loss (or if it is, that this is intentional).

- **LR schedule sensitivity**: The cascade fires at a specific step. Would a different cosine decay schedule (e.g., shorter or longer total budget) shift the cascade proportionally, or is the cascade tied to absolute gradient magnitude? This would validate whether T_threshold ≈ 28K is architecture-specific or LR-schedule-dependent.

- **Dropout/regularization interaction**: Was dropout used? If not, is the learned γ serving as the only regularizer? If yes, is the 13.7% Morrison bracket gap partly an interaction with dropout?

**Priority ablation to add**: CliffordStalkBundle vs. flat projection. This is the most credible attack on the architecture — a reviewer will ask if Clifford algebra is load-bearing or just ornamental. It can be run quickly (same script, replace CliffordStalkBundle with nn.Linear of equivalent dimension).

---

### 4. Dataset Scope

**What the paper uses**: wikitext-103 for the main results. Wikitext-2 for the Morrison bracket ablation (different dataset — noted in the math red team as a confounder).

**What reviewers will ask**: Does the cascade phenomenon generalize beyond wikitext-103? Is it dependent on the specific token distribution, vocabulary structure, or domain? A secondary evaluation on a different dataset (e.g., Penn Treebank, or any small but different-domain corpus) would significantly strengthen the generalization claim.

**Minimum fix**: Standardise the ablation dataset to wikitext-103. The Morrison bracket ablation on wikitext-2 creates an internal inconsistency — the ablation PPL numbers cannot be compared to the main result PPL numbers, which makes the "13.7% worse" claim imprecise.

---

### 5. Metric Scope: Perplexity Only

**What the paper measures**: Validation perplexity (token-level cross-entropy). Nothing else.

**What's missing**: Downstream task performance. The paper acknowledges the inference bottleneck (§5.4) makes autoregressive GSM8K eval intractable at current implementation speed. This is an honest admission, but it leaves the paper with a methodological gap: perplexity is a proxy for language modeling quality, not for reasoning or task performance.

**Recommended alternatives** (noted in EXPERIMENTS_LOG.md, should appear in the paper's future work):
- Perplexity scoring of fixed answer choices (no generation required)
- Batch logit scoring: compute logP(correct answer | question prefix) using a single forward pass
- These can be added to §6.4 as "Future Work: Downstream Evaluation" with a note that the KV-cache analog for RMSN states is required for practical eval speed

---

### 6. HCC Law: Minimum Validation Bar

**Current status**: n=2 data points (RMSN-193M Wave 1 as reference, C-RMSN Wave 1 as test). Both points come from architecturally different models with different threshold residence times.

**What constitutes a "law" vs. a "conjecture"**: In ML empirical work, a scaling law typically requires 4+ data points spanning at least 2 orders of magnitude. The HCC has 2 points spanning 8× in T_threshold — not enough to establish the exponent is linear (vs. sublinear or superlinear).

**Minimum bar**: The pending RMSN-500M result (T_threshold ≈ 28K → predicted λ_max = −0.9) provides the third point. If confirmed, the law has three points on two architectures. That justifies "empirical scaling relation" but not yet "law." For "law" status: add RMSN-193M Wave 2 (T_inter-wave ≈ 33K → predicted λ_max = −1.06, observed −0.9, error 15%), which is already in the data. That gives 4 points. Present all 4 in a calibration plot.

**Recommended fix**: Add a §5.7.4 "HCC Calibration" subsection with a 4-point calibration table and a log-log plot (even ASCII-formatted). Present RMSN-500M result when it comes in. This converts the "preliminary empirical law" into a properly calibrated empirical relation.

---

### 7. Compute Reporting

**What the paper reports**: Training steps, parameter count, sequence length, batch size, PPL, Lyapunov exponent. GPU-hours and FLOPs are not reported.

**Why this matters**: ML efficiency claims now require compute reporting as a baseline expectation (Bommasani et al. 2021, Patterson et al. 2021). Without it, the paper cannot be compared to other works in terms of compute budget. RMSN may be more or less compute-efficient than Transformers — the paper should report both model FLOPs per step and total training FLOPs.

**What to add**: One line per model in the ablations table: "Total training compute: 6.08×10¹⁸ FLOPs (RMSN-Small, 100K steps, estimated)." Formula: FLOPs ≈ 6·N·D·batch_size·seq_len·steps where N = parameters.

---

### Summary Table

| Issue | Severity | Recommended Fix |
|-------|----------|----------------|
| No external baselines | High | Add one wikitext-103 Transformer/Mamba comparison or cite existing numbers |
| Single-run all results | Medium | Run 3 seeds for RMSN-193M; report cascade step range |
| Morrison ablation on wikitext-2 (not wikitext-103) | Medium | Re-run Morrison ablation on wikitext-103 for internal consistency |
| CliffordStalkBundle vs flat projection not ablated | Medium | Add flat projection ablation to isolate Clifford contribution |
| Perplexity-only metrics | Medium | Add downstream eval plan to §6.4 future work |
| HCC law with n=2 points | Medium | Add RMSN-500M result + 4-point calibration table when available |
| No compute reporting | Low-Medium | Add estimated FLOPs per model in ablations table |
| Dataset scope (wikitext-103 only) | Low | Acknowledge; add secondary dataset to future work |

**Most urgent before submission**: External baseline comparison + Morrison ablation moved to wikitext-103. These are the two issues that would cause a desk rejection at a competitive venue.
