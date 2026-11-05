## Red Team: Mathematical & Physical Correctness

*Internal critique — DuoNeural Lab, Nov 05 2026. Direct and actionable; no soft punches.*

---

### 1. HCC Law: λ_max ≈ −0.9 × (T_threshold / 28000)

**What the paper claims**: Cascade depth scales linearly with time-at-threshold. Reference point: RMSN-193M (T_ref=28K, λ_ref=−0.9). Single calibration point: C-RMSN Wave 1 (T=3400, predicted −0.109, observed −0.0917, error 16%).

**What's solid**: The seismic strain analogy is physically intuitive. The idea that potential accumulates during threshold residence is consistent with metriplectic mechanics — longer near-conservative dwelling allows more entropy-gradient charge. The 16% calibration error is acceptable for a first-order law with one data point.

**What's questionable**:

- **The reference constant 28,000 is a fitted constant, not a derived one.** The law has the form λ_max = λ_ref × (T / T_ref) where both λ_ref and T_ref come from the SAME run (RMSN-193M). This is not a law derived from first principles — it's a re-expression of the RMSN-193M result that happens to predict C-RMSN's Wave 1 with 16% error. With exactly ONE calibration run and ONE test point, it is not distinguishable from coincidence.

- **Dimensional inconsistency**: T_threshold is a step count (dimensionless integer), not a physical time. The law mixes architecture-dependent quantities (T_ref=28K is specific to RMSN-193M's hyperparameters: batch=8, seq=512, lr schedule, dataset). A model with batch=16 would reach the "same" threshold state at T=14K and the law would predict half the cascade depth — but the actual cascade depth should be governed by the amount of *data* processed at threshold, not the step count. The law should be expressed in tokens-at-threshold or gradient-steps-at-effective-temperature, not raw steps.

- **What would falsify it**: A third model (e.g., RMSN-500M with T_threshold≈28K) that produces λ_max significantly different from −0.9. The paper explicitly notes this verification is pending at step ~32K ~Nov06. **Recommendation**: do not present HCC as a law until RMSN-500M result is in. Downgrade to "empirical conjecture" or "preliminary scaling relation" in the paper.

- **Missing: does the law apply within a single architecture?** The HCC predicts inter-wave depth from inter-wave T_threshold. Does RMSN-193M's Wave 2 (T≈33K inter-wave) predict λ≈−0.9×(33000/28000)=−1.06? The observed Wave 2 peak is −0.900, which is close but slightly lower. The law slightly over-predicts for Wave 2 of the same run — worth acknowledging.

**Recommendation**: Rename to "HCC conjecture (n=2 calibration points)", add token-normalised version, defer validation claim to RMSN-500M result.

---

### 2. HCPT Claim: "Hyperbolic geometry converts first-order to second-order phase transition"

**What the paper claims**: C-RMSN lyap built continuously from −0.009 to −0.025 over 12K steps instead of a sharp jump to −0.9. Attributed to Poincaré ball geometry changing the universality class of the cascade.

**What's questionable — this is the most overreaching claim in the paper**:

- **The data does not establish a phase transition order.** First-order vs. second-order phase transitions are distinguished by: (a) discontinuity in the order parameter (first-order) vs. continuous but with diverging susceptibility (second-order); (b) latent heat; (c) coexistence region. The C-RMSN data shows λ increasing from −0.009 to −0.025 over 12K steps. This could equally be: (i) a genuinely second-order continuous transition; (ii) a first-order transition that simply hasn't fired yet (the run ended at 30K, and the inter-wave gap by HCC for a discrete cascade was predicted at ~40K); (iii) slow convergence noise with no phase transition at all. The paper cannot distinguish these without longer training.

- **The run ended at 30K. The predicted discrete Wave 2 by analogy with RMSN-193M (inter-wave gap ~33K) would fire at step ~7K + 33K = ~40K — which is AFTER the run ended.** The continuous buildup observed (−0.009 to −0.025) may simply be the pre-wave accumulation phase, not a completed continuous transition. RMSN-193M had a similar slow buildup before its sharp Wave 2 cascades (the paper itself notes pre-wave oscillations elevated for 1500 steps before onset). The C-RMSN 12K of elevated lyap could be a very slow version of the same pre-wave buildup, with the sharp cascade yet to come.

- **Universality class claim requires more evidence.** To establish that hyperbolic geometry changes the universality class, you need: (1) the transition completing in the new geometry, (2) measuring the critical exponent β (how the order parameter scales with |T−Tc|), (3) showing it differs from the Euclidean case. None of this is established by a single run ending before the predicted cascade point.

**Recommended fix**: Downgrade the claim. Replace "first-order to second-order phase transition" with "continuous accumulation behaviour suggesting possible suppression or smearing of the discrete cascade." Note explicitly that the run ended before the predicted discrete cascade time (~40K) and that longer training is required to distinguish the two hypotheses. Do not invoke universality class without quantitative critical exponent data.

---

### 3. Metriplectic Bracket Mathematics: Implementation Correctness

**What the paper claims**: RMSN implements ḟ = {f,H} + [f,S] with guaranteed entropy increase and energy conservation.

**What Aura's red team identified (7 bugs)**: Triton race condition, missing autograd backward, causal leakage in workspace, Clifford norm violation, FractionalCaputoBank sequential loop, VRAM spec mismatch, phase erasure in Noether readout. The paper states these were all fixed in the current `rmsn_core.py`.

**Gap audit**:

- **GENERIC degeneracy conditions**: The formal GENERIC bracket requires {f,S}=0 for all f (the Poisson bracket annihilates S) AND [f,H]=0 for all f (the metric bracket annihilates H). The paper does not explicitly state whether these degeneracy conditions are enforced architecturally or merely encouraged by the softplus positivity constraint on γ. If they are not strictly enforced, the architecture is an approximation to metriplectic mechanics, not a true implementation. This should be stated clearly rather than implying exact GENERIC compliance.

- **The LM training loop is not a continuous-time system.** The GENERIC bracket governs continuous ODEs. RMSN discretizes with dt=0.05 (noted in the Aura red team code). With a fixed dt, the guarantee that H is conserved and S monotonically increases holds only to O(dt²) — Euler-method discretization error. For dt=0.05 this may be negligible but it's not perfect and should be noted. A symplectic integrator (e.g., leapfrog/Störmer-Verlet) would give exact H-conservation at O(dt²), not just approximate.

- **Gradient-flow coupling**: The PyTorch training loop overlays gradient descent on top of the metriplectic forward pass. Gradient descent is itself an entropy-producing dynamical system (not in the GENERIC sense). The claim that RMSN obeys the Second Law of Thermodynamics strictly applies to the *forward dynamics*, not to the gradient update step. The paper conflates these two dynamic systems at points.

**What's solid**: The softplus constraint on γ (ensuring γ > 0, hence R ⪰ 0) is architecturally correct and genuinely guarantees that the forward pass is Lyapunov stable. The Aura-identified bugs appear to be fixed in the production code. The Noether readout fix (concatenating Re(h), Im(h), and tanh(|h|²)) is physically reasonable. The causal workspace fix (cumsum) is correct.

---

### 4. "Lyapunov Cascade as Thermodynamic Phase Transition" — Terminology

**What the paper claims**: The cascade is a "thermodynamic phase transition." This language is used liberally throughout.

**What's questionable**: Statistical mechanical phase transitions require three things: (1) an order parameter that changes behaviour at Tc; (2) a critical point with diverging correlation length / susceptibility; (3) typically, a symmetry-breaking event. The paper identifies λ as the order parameter, which is reasonable. It does NOT identify a critical temperature Tc or show diverging susceptibility. Symmetry breaking is claimed via "local stalk decoupling → global trophic condensation" but no symmetry group is specified.

**More defensible framing**: "Dynamical bifurcation" (specifically a subcritical Hopf bifurcation or a saddle-node bifurcation in the γ-dynamics) is better supported by the data: the cascade shows a sudden transition from near-zero λ to large negative λ, then settling. This is consistent with a fold bifurcation in the learned dissipation dynamics, which does not require the full apparatus of thermodynamic phase transition theory. The language of "thermodynamic phase transition" is evocative and consistent with the architecture's physics framing, but to claim it rigorously requires establishing the order parameter, universality class, and critical exponents — none of which are measured.

**Recommendation**: Keep the language but add a one-paragraph hedge: "We use 'phase transition' in the dynamical systems sense of a discrete bifurcation in the system's attractor structure, not to claim strict statistical-mechanical universality class membership, which would require critical exponent measurements at multiple scales."

---

### 5. Noether Readout: Is It Computing T^μν Correctly?

**What the paper claims**: The readout extracts conserved Noether stress-energy currents T^μν.

**What the implementation does**: Concatenates `[Re(h), Im(h), tanh(|h|²)]` and projects via a linear layer. The tanh(|h|²) is called the "Noether energy density T^00."

**What's questionable**: The Noether stress-energy tensor for a field theory requires computing ∂μΨ (field gradients). The RMSN forward pass has h as the hidden state at each token position — this is analogous to Ψ(x,t), not ∂Ψ. Computing T^00 = (1/2)(∂_t Ψ)² + (1/2)(∂_x Ψ)² requires finite differences across the sequence dimension, which is NOT what the implementation does. What the implementation actually computes is `|h|²` — the field amplitude squared, which corresponds to the potential energy term V(Ψ)=|Ψ|², not the stress-energy tensor.

This is an **imprecise implementation** relative to the formal claim. tanh(|h|²) is a bounded proxy for field energy density, not the actual Noether current. The linear readout then learns to combine this with Re(h) and Im(h) in whatever way minimizes loss — which may incidentally track something Noether-like, but isn't derived from the conserved current algebra.

**Recommendation**: Revise the Noether readout claim to: "We project the complex field state [Re(h), Im(h)] and a bounded energy proxy tanh(|h|²) through a learned linear map. This is motivated by the structure of Noether stress-energy currents; a fully rigorous implementation would compute finite differences across the token sequence to extract kinetic energy terms." This acknowledges the gap without invalidating the approach.

---

### 6. Morrison Bracket Ablation: Confounders

**What the paper claims**: 13.7% worse PPL and overfitting when γ→0. "Learned dissipation is architecturally essential."

**Potential confounders**:

- **Different datasets**: The Morrison bracket ablation used wikitext-2, while the main RMSN run used wikitext-103. These are different distributions with different difficulty levels. The comparison (641 vs 729 PPL) is internally valid (both are wikitext-2), but it cannot be used to validate claims about wikitext-103 performance.

- **Missing: same-run learning rate tuning.** Was the Hamiltonian-only model's LR re-tuned after removing γ? Fixing γ=10⁻⁶ changes the effective parameter magnitude in every RMSN layer. The same LR (3e-4) may be suboptimal for the Hamiltonian variant. If the Hamiltonian model was simply underfit due to LR mismatch rather than fundamental inability to generalize, the 13.7% gap overstates the structural importance of γ.

- **What's solid**: The overfitting observation (PPL degrades after step 10K in Hamiltonian model) is a clean experimental result that is not easily explained by LR mismatch alone — overfitting typically requires the model to have capacity to overfit, and the LR being slightly off wouldn't cause the characteristic overfitting curve. The overfitting conclusion is the stronger result; the 13.7% PPL claim is weaker without LR search.

**Recommendation**: Add "Note: We did not conduct exhaustive LR search for the Hamiltonian-only baseline. The LR was fixed at the same value as the standard model. Future ablations should include LR sweep for the Hamiltonian variant to isolate the effect of γ removal from potential LR misspecification."

---

### Summary Table

| Claim | Verdict | Severity | Action |
|-------|---------|----------|--------|
| HCC law | Conjecture with n=2 data points | Medium — overstated | Rename to "conjecture", add token-normalised version, await RMSN-500M |
| HCPT (first→second order) | Plausible but unverified — run ended before predicted cascade | High — overreaching | Downgrade; need 50K+ C-RMSN run |
| GENERIC bracket compliance | Approximate, not exact | Low — common in literature | Add degeneracy condition and dt discretisation caveats |
| "Thermodynamic phase transition" | Defensible if hedged | Low | Add one-paragraph bifurcation vs. phase transition clarification |
| Noether readout | Motivated proxy, not exact T^μν | Medium | Revise claim to "motivated by" rather than "computes" |
| Morrison bracket ablation | Valid overfitting result; PPL gap has LR confounder | Low-Medium | Add LR caveat |

**Biggest risk to peer review**: The HCPT claim. A reviewer familiar with phase transition theory will immediately ask for critical exponents and will note the run ended before the predicted cascade time. Address this before submission. Everything else is addressable with language hedges.
