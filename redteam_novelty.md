# RMSN Novelty & Related Work — Red Team Audit
**Archon | DuoNeural Lab | 2026-11-05**

---

## 1. Port-Hamiltonian / Hamiltonian Neural Networks

**Existing prior art the paper must address:**
- Greydanus et al. (2019) *Hamiltonian Neural Networks* — learns H(q,p) so dynamics obey Hamiltonian mechanics. Purely conservative, no dissipation.
- Cranmer et al. (2020) *Lagrangian Neural Networks* — learns L(q,q̇) under variational principle.
- Zhong et al. (2020) *Symplectic ODE-Net* — symplectic integrator for mechanical systems.
- Desai et al. (2021) *Port-Hamiltonian Neural Networks* — explicitly uses port-Hamiltonian formulation for physical system identification.
- Zhong et al. (2021) *Dissipative SymODEN* — adds dissipation to symplectic networks.

**Is RMSN's Port-Hamiltonian use novel?**

YES, but needs clearer articulation. All prior PH-NN work targets *physical system identification* (robots, pendulums, molecules) — they learn a Hamiltonian from observed trajectories. RMSN uses metriplectic mechanics as a *representational prior* for language modeling, where "energy" and "entropy" are not physical quantities but learned latent-space organization principles. This is a fundamentally different use case. The paper gestures at this distinction in §1 but does not make it explicit.

**Critical gap**: The paper MUST add a paragraph distinguishing RMSN from Desai et al. 2021 (the closest prior PHN work). Key distinction: (1) RMSN uses metriplectic (Morrison bracket), not just Port-Hamiltonian; (2) RMSN is a language model, not a physical system emulator; (3) RMSN's dissipation parameter γ is learned and deepens during training — it is not a fixed physical constant. The *Lyapunov Cascade* is evidence of this: a physical system emulator with fixed γ cannot exhibit it.

**Recommended fix**: Add §2.4 "Relationship to Physical Neural Networks" distinguishing metriplectic from purely Hamiltonian NNs and clarifying the language-modeling context.

---

## 2. State Space Models (SSMs)

**Existing prior art:**
- S4 (Gu et al. 2021), S5, Mamba (Gu & Dao 2023), Mamba-2 — all use linear recurrence h_t = A·h_{t-1} + B·x_t with parallel scan.
- Liquid Neural Networks (Hasani et al. 2021) — ODE-based recurrence with time-varying dynamics.
- LRU (Orvieto et al. 2023) — complex exponential diagonal recurrence.
- Hawk/Griffin (De et al. 2024) — real-valued gated recurrence.

**Is RMSN's parallel scan novel?**

The `parallel_metriplectic_scan` computing h_t = exp((-γ+iω)dt)·h_{t-1} + u_t·dt is structurally a **complex diagonal linear recurrence** — essentially S4/LRU with complex exponential decay where γ and ω are input-dependent (not fixed). This is not novel as a computational primitive.

**What IS novel**: The *physical motivation* and the *γ-deepening phenomenon*. In Mamba/S4, the decay constants A are fixed or learned as static parameters. In RMSN, γ deepens during training as a consequence of the Morrison bracket constraint — this dynamic adaptation of the dissipation rate has no analog in SSMs. The Lyapunov Cascade is evidence of this: SSMs cannot exhibit a cascade because their recurrence parameters do not have a thermodynamic motivation to change their distribution during training.

**Critical gap**: The paper does not cite S4/Mamba at all. Reviewers will immediately ask "how is this different from a complex-valued SSM with Clifford preprocessing?" This needs to be addressed directly. The key answer: RMSN's γ deepening is architecturally driven by the softplus constraint on the Morrison bracket, not learned through gradient descent in the usual sense — it has a thermodynamic forcing term. The cascade is the empirical evidence.

**Recommended fix**: Add SSM comparison to §2 or §6.2. Acknowledge the structural similarity of the recurrence, then distinguish the thermodynamic forcing and the cascade as genuine differentiators.

---

## 3. Global Workspace Theory in ML

**Existing prior art:**
- Goyal et al. (2021) *Recurrent Independent Mechanisms* — modular attention with competition.
- Goyal & Bengio (2022) *Inductive Biases for Deep Learning of Higher-Level Cognition* — reviews GWT-inspired ML.
- Lamarre et al. (2023) *Global Workspace Transformer* — explicit GWT implementation with bottleneck attention.
- Perceiver IO (Jaegle et al. 2021) — latent bottleneck for cross-modal routing (structurally similar to RMSN workspace).

**Is RMSN's Trophic Workspace novel?**

The GWT bottleneck concept is not novel. What is novel:
1. **Lotka-Volterra competition** replacing standard softmax attention — to the best of our knowledge, no prior ML workspace uses ecological niche dynamics for slot competition. This prevents slot collapse (a known problem with standard GWT attention) via a principled mechanism.
2. **Causal prefix accumulation** (cumsum) for workspace updates — necessary for autoregressive causality, but specifically formulated here.
3. **Integration with the metriplectic dynamics** — the workspace slot entropy is monitored as telemetry and feeds into the Lyapunov analysis.

**Critical gap**: The paper should cite Goyal et al. 2021 and the Global Workspace Transformer explicitly and explain the Lotka-Volterra niche partitioning as the key differentiator.

---

## 4. Lyapunov Cascade Novelty

**Closest related phenomena:**
- **Grokking** (Power et al. 2022) — sharp late generalization transition after apparent convergence. Structurally similar in timing (late-training phase transition) but different mechanism: grokking is a loss-landscape phenomenon without any thermodynamic interpretation.
- **Phase transitions in LLMs** (Wei et al. 2022, emergent capabilities) — capability jumps at scale thresholds. Different axis (parameter count vs. training steps), no Lyapunov connection.
- **Loss spikes / catapults** (Lewkowycz et al. 2020, Damian et al. 2022) — oscillations at the edge of stability. Caused by LR too large; RMSN's cascade is not a spike (lyap returns to stable baseline, not NaN/divergence).
- **Neural collapse** (Papyan et al. 2020) — terminal phase of training when representations collapse to simplex ETF. Different phenomenon (representation geometry, not dissipation dynamics).

**Is the Lyapunov Cascade genuinely novel?**

YES, with one important caveat. The cascade is distinguishable from all prior phenomena because:
1. It is defined in terms of the **Lyapunov exponent** (a system-theoretic stability measure), not loss, accuracy, or representation geometry.
2. It is **architecturally caused** — it cannot occur in architectures without explicit metriplectic structure (confirmed by Morrison bracket ablation).
3. It is **beneficial** — directly correlated with PPL improvement, not a training pathology.
4. It has a **mechanistic explanation** rooted in thermodynamics (attractor basin transitions in the metriplectic bracket).

**Caveat**: The paper should explicitly address why this is NOT grokking. The timing is different (grokking occurs on tiny datasets with weight decay; cascade occurs on full wikitext-103 without weight decay), the mechanism is different (Lyapunov dynamics vs. norm-based regularization theories of grokking), and the measurement is different. Add a "Relationship to Grokking" paragraph in §6.1 or §4.

---

## 5. Missing Related Work — Reviewer Flags

The following will be flagged by reviewers at ICLR/NeurIPS. Add citations and brief distinguishing statements:

| Prior Work | Why Reviewers Will Flag It | How RMSN Differs |
|-----------|---------------------------|-----------------|
| Bodnar et al. (2022) *Neural Sheaf Diffusion* | Sheaf neural networks on graphs | RMSN uses cellular sheaves for causal sequence transport, not graph diffusion; RMSN's sheaf structure is temporal/causal, theirs is spatial/symmetric |
| Chami et al. (2019) *Hyperbolic GCN* | Hyperbolic neural networks | C-RMSN variant uses Poincaré ball; cite for C-RMSN section only |
| Brandstetter et al. (2021) *Geometric and Physical Quantities Improve E(3)NNs* | Clifford algebra in ML | RMSN uses Cl(3,0) stalks for feature representation, not E(3) equivariance; different purpose |
| Rusch et al. (2022) *Oscillatory SSMs* | Complex exponential recurrence | Very close to RMSN's scan component; cite and distinguish via thermodynamic motivation |
| Hasani et al. (2022) *Liquid S4* | Combining liquid dynamics with SSMs | Structural overlap; distinguish via Morrison bracket forcing |
| Momennejad et al. (2017) *Successor representations* | Memory as predictive coding | Fractional Caputo memory serves a similar functional role |
| Vertes & Bhatt (2022) *Neurally plausible mechanisms for GWT* | GWT in neural modeling | Cite alongside Goyal et al. for the workspace section |

**Additional note**: The paper cites only 11 references total. For a venue-ready preprint, this is severely under-cited. A realistic target for submission to NeurIPS/ICLR is 30–50 references. The missing SSM, Clifford, sheaf, and GWT literature alone accounts for 10–15 missing citations.

---

## 6. Structural Novelty Assessment

**Strongest novelty claims (defend vigorously):**
1. Metriplectic mechanics as a language modeling architecture prior (not physical system emulation)
2. Lyapunov Cascade as an empirically observed, mechanistically explained training phenomenon
3. Morrison bracket ablation proving dissipation drives generalization
4. HCPT (Hyperbolic Continuous Phase Transition) — first-order vs second-order cascade depending on workspace geometry (C-RMSN §5.7.3)
5. Unified dissipation draining law across architectures

**Weaker novelty claims (need hedging or stronger evidence):**
1. "24 scientific disciplines unified" — this is motivation, not a formal unification theorem; the claim is correct but overstated if presented as a theorem
2. RMSN unifies SRSN/PULSE/CDM "as special cases" — the unification is conceptual (all use Port-Hamiltonian-inspired dynamics) rather than mathematical (formal reduction proofs not provided); should say "conceptual unification" or provide the reduction proofs
3. Scale ablation with only 3 points (Pico/Nano/Small) — 3 data points establishes correlation between scale and cascade, but the "critical dimension between 100M and 193M" claim needs at least one more point (e.g., 150M at D=896) for a credible phase transition claim
4. val_ppl=50.0 comparison to other architectures — §6.2 is careful about this but abstract/intro should clarify this is not an optimized competition run

---

*Red team complete. See `section_24disciplines.md` for the disciplines expansion.*
