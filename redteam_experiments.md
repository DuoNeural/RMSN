## Red Team: Experimental Methodology

*Generated Nov 05 2026 — Archon (DuoNeural Lab). Severity: HIGH = likely rejection, MEDIUM = major revision, LOW = minor revision.*

---

### 1. Scale Ablation Sufficiency (§5.4) — **SEVERITY: HIGH**

**Claim**: "The critical dimension for cascade emergence lies between 100M and 193M parameters (D between 768 and 1024). This is not a gradual transition."

**Concerns**:

**1a. Three points, one seed each, different dataset.** The ablation uses wikitext-2 (~2.1M tokens) while the primary result uses wikitext-103 (~103M tokens). At 20K steps × batch 2 × seq 512 = 20.5M tokens, the ablation models are seeing ~10 epochs of wikitext-2, which is approaching dataset repetition and may cause memorization artifacts that suppress or modify cascade dynamics. The primary 193M model at 50K steps sees only ~0.2 epochs of wikitext-103. **This is a significant experimental confound** — the cascade behavior may differ between single-epoch and multi-epoch regimes for reasons unrelated to scale. A reviewer will catch this immediately.

**1b. Insufficient sampling density to claim "sharp transition."** You have three data points separated by 4.4× (44M→100M→193M) and claim a phase transition between the last two. This is consistent with a sharp transition but equally consistent with a gradual transition that your sampling density cannot resolve. To defend "sharp transition" language you need at minimum two intermediate points: ~130M and ~160M. If cascade appears at 160M but not 130M, the transition is confirmed sharp in the D-range claimed. Without these, change the claim to "cascade-capable threshold between 100M and 193M."

**1c. Single seed.** One seed per scale means you cannot distinguish architecture-driven cascade from seed-dependent initialization luck. The cascade is claimed to be "not an artifact" — but without seed ablation this claim cannot hold. Minimum: 3 seeds at 193M.

**Strengthening**: (1) Re-run ablations on wikitext-103 for consistency; (2) Add two intermediate scales (130M, 160M); (3) Run three seeds at the critical Small scale. If resources are limited, the seed ablation at 193M is the most important.

---

### 2. C-RMSN Second-Order Phase Transition Claim (§5.7.3) — **SEVERITY: HIGH**

**Claim**: "Hyperbolic geometry converts first-order to second-order phase transition." "Both discrete-cascade models (A) and (B) are falsified."

**Concerns**:

**2a. The run simply may not have been long enough.** This is the most parsimonious alternative explanation, and you have not ruled it out. RMSN-193M's inter-wave gap is steps ~7K to ~40K = 33K steps. C-RMSN Wave 1 fired at step 6.7K. If the inter-wave compression ratio is even 1.0× (no compression), Wave 2 would fire at step 6.7K + 33K = ~40K. You ran to 30K. The "continuous buildup" from lyap −0.009 to −0.025 (steps 15K–30K) looks identical to the pre-Wave 1 oscillation pattern — it rose from −0.001 to −0.009 over similar timescales before Wave 1. You are calling the pre-wave oscillation a "second-order phase transition" when it may simply be a longer version of the pre-Wave 1 buildup. **The simplest explanation: Wave 2 would have fired at step 35–45K, and you stopped at 30K.**

**2b. "Falsifies" is too strong.** You have one run at one hyperbolic configuration (K=16, c=1.0). A reviewer will correctly note that you cannot "falsify" a model with a single run. Use "not observed within 30K steps" or "inconsistent with discrete cascade up to step 30K." Reserve falsification language for the paper's conclusion.

**2c. Claiming "universality class change" requires statistical mechanics grounding.** The term "universality class" has a precise meaning in statistical physics (determined by symmetry and dimensionality, not by specific parameter choices). Using it here implies you have computed or estimated critical exponents for both the Euclidean and hyperbolic cases. You have not. Either add this analysis or use weaker language: "suggests a qualitative change in the order of the phase transition."

**What would constitute rigorous proof**: (1) Run C-RMSN to 60K steps — if no discrete cascade fires, the claim is substantially stronger; (2) Try K=32 and K=8 to show the effect is robust to Voronoi granularity; (3) Compare the lyap autocorrelation length in the "continuous buildup" region vs. the pre-wave oscillation region — if autocorrelation is qualitatively different, that distinguishes continuous PT from pre-wave buildup.

---

### 3. Morrison Bracket Ablation (§5.5) — **SEVERITY: MEDIUM**

**Claim**: "13.7% worse perplexity and early overfitting proves the cascade is not an artifact." "The Morrison bracket provides active regularization."

**Concerns**:

**3a. Ablation is at sub-critical scale (Nano, 99.3M), which does not cascade.** The ablation proves that γ matters for generalization in the sub-critical regime but does not directly address whether γ is essential to the cascade at the critical 193M scale. A reviewer will note: "you ablated dissipation in a model that doesn't cascade anyway — how does this inform us about the cascade mechanism?" Run the Morrison ablation at RMSN-Small (193M) to close this gap.

**3b. Alternative explanation: initialization confound.** When γ is fixed to 10⁻⁶, the γ weight initialization is effectively frozen. If the standard model's weight decay and optimizer dynamics interact with γ's gradient flow to provide implicit regularization, fixing γ=10⁻⁶ may disrupt this interaction for reasons unrelated to dissipation theory. Specifically: does the Hamiltonian-only model have the same effective learning rate on `omega_proj` and `in_proj` as the standard model? If γ absorbs some gradient energy in the standard case, its absence may effectively increase the learning rate on other components, explaining overfitting via standard sharpness rather than thermodynamic mechanism.

**3c. Absolute PPL values are weak.** Both models achieve PPL > 600 on wikitext-2. This is well above the range where model quality comparisons are meaningful. A 13.7% gap in the 600–730 range could reflect initialization sensitivity, dataset overfitting, or optimizer interactions more than architectural properties.

**Strengthening**: Run the Morrison bracket ablation at 193M on wikitext-103. If the cascade disappears when γ=10⁻⁶ at critical scale, that is a much stronger claim.

---

### 4. HCC Law (§5.7.2) — **SEVERITY: MEDIUM**

**Claim**: "Hyperbolic Compressed Cascade (HCC) — preliminary empirical law: λ_max ≈ λ_ref × (T_threshold / T_ref)"

**Concerns**:

**4a. One independent data point with 16% error is not a law.** The HCC equation uses RMSN-193M (T_ref=28K, λ_ref=−0.9) as the reference — meaning RMSN-193M is *built into the formula*, not an independent validation point. The only truly new data point used to test the formula is C-RMSN Wave 1. A 16% prediction error on a single novel data point is weak evidence for a quantitative law. The word "law" should be replaced with "preliminary scaling hypothesis" or "empirical conjecture" — or add "Law" in scare quotes with explicit acknowledgment of single-point calibration.

**4b. No derivation of the linear form.** The formula assumes linear proportionality between threshold residence time and cascade depth. There is no theoretical argument for why the relationship should be linear rather than power-law, logarithmic, or threshold-triggered. The physical analogy (seismic strain) would suggest a relationship more like elastic strain energy ∝ T², not T. Present the formula as a first-order linear approximation rather than a derivation.

**4c. Validation path exists but hasn't been used.** You have multiple models with known T_threshold and known λ_max: width_iso (D=1024/L=10), golden_ratio, and scale_300M. These can serve as independent HCC data points RIGHT NOW. Including even two additional validation points would substantially strengthen the claim.

**Strengthening**: Extract T_threshold and λ_max for width_iso and scale_300M from EXPERIMENTS_LOG.md and add them as validation data points. Even if the law holds only roughly (< 25% error across all data points), that's worth reporting.

---

### 5. Comparison to Baselines (§6.2) — **SEVERITY: MEDIUM**

**Claim**: RMSN-Small achieves val_ppl=50.0 on wikitext-103 (100K steps, 409.6M tokens).

**Concerns**:

**5a. No actual comparison table.** Section 6.2 has narrative comparison but no table showing RMSN-Small vs. comparably-sized recurrent architectures (RWKV-v4 ~170M, Mamba ~130M, Hyena ~153M, RetNet ~1.3B/smallest) on wikitext-103 with equivalent or comparable token budgets. This is the first thing a reviewer will request.

**5b. Tokenizer mismatch may inflate apparent gains.** RMSN uses cosmo2 tokenizer (vocab=49,152). Most published baselines use GPT-2 BPE (vocab=50,257) or similar. cosmo2 may have more efficient encoding for English prose (fewer tokens per word), which would make per-token PPL appear better than per-character BPE comparisons. Either report bits-per-character (BPC) for fair comparison or explicitly note tokenizer differences.

**5c. 409.6M tokens is on the low end.** A 193M-parameter model at Chinchilla-optimal would need ~3.9B tokens. 409.6M is ~10% of Chinchilla optimal, which means the model is severely undertrained relative to its capacity. The comparison should acknowledge this: "our 193M model at 409.6M tokens is roughly equivalent in training budget to a ~19M-parameter model at Chinchilla-optimal." This context prevents the ppl=50 from being interpreted as a ceiling.

---

### 6. Missing Ablations (Reviewer Priority) — **SEVERITY: MEDIUM**

Listed in order of likely reviewer demand:

**6a. Clifford Cl(3,0) vs. standard MLP (HIGHEST PRIORITY).** The paper claims Clifford grade-stratified stalks are essential to the architecture's "geometric integrity." A reviewer will immediately ask: does the cascade also occur if you replace the Clifford stalk bundle with an equivalently-parameterized MLP or LayerNorm+FFN block? If yes, Clifford geometry is not essential to cascade emergence. If no, that's a major positive result that dramatically strengthens §3.2 and §5.4.

**6b. Fractional Caputo vs. standard recurrence.** Replace FractionalCaputoBank with 8 standard GRU cells (equivalent parameter count). Does the cascade still occur? Does ppl change meaningfully? This is the second-most-requested ablation given the theoretical prominence of power-law memory in the paper.

**6c. Global workspace: Lotka-Volterra vs. standard attention.** The ecological competition dynamics are theoretically motivated but computationally costly. Replace with M_w-head cross-attention (causal) at equivalent parameter count. Does cascade occur? Does routing entropy differ? This would isolate whether the ecological dynamics are adding value beyond providing M_w workspace slots.

**6d. Number of Voronoi/workspace slots K.** C-RMSN uses K=16; main RMSN-Small uses M_w=32-64. No ablation on this hyperparameter exists. Slot count affects the inter-wave gap (via centroid migration time), and understanding this is important for the continuous vs. discrete cascade claim.

---

### Summary Prioritization

| Issue | Severity | Effort to Fix | Recommendation |
|-------|----------|---------------|----------------|
| Ablation dataset mismatch (wikitext-2 vs. 103) | HIGH | High (re-runs needed) | Reframe or re-run |
| Single-seed cascade reproducibility | HIGH | Medium (3× 193M runs) | Must do before NeurIPS |
| C-RMSN run truncated at 30K — claim too strong | HIGH | Low (reframe language) | Fix language now; extend run if possible |
| HCC "law" single data point | MEDIUM | Low (use existing data) | Extract validation points from existing logs |
| Morrison ablation at sub-critical scale | MEDIUM | Medium (193M ablation run) | Add to future work or run |
| No baseline comparison table | MEDIUM | Low (literature lookup) | Add table §6.2 |
| Missing Clifford vs. MLP ablation | MEDIUM | Medium | Highest-value missing ablation |
| "Universality class" language | MEDIUM | Low (edit) | Soften claim immediately |

**Immediate text fixes (zero compute cost)**: Change "falsifies" → "is inconsistent with within 30K steps"; change "law" → "preliminary hypothesis"; add "Note: ablations trained on wikitext-2 to reduce compute; full wikitext-103 ablations are future work"; add baseline PPL table in §6.2.

**Most impactful compute investments**: (1) Extend C-RMSN to 60K steps — either confirms HCPT or reveals Wave 2; (2) Three seeds at RMSN-193M — confirms cascade reproducibility; (3) Clifford vs. MLP ablation at Nano scale — isolates geometric necessity.
