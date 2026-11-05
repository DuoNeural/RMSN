# RMSN Experiments Log

**DuoNeural Lab | Archon + Aura | Maintained Nov 2026+**

This file tracks all RMSN experimental runs. Updated automatically by Archon during active lab sessions.

---

## Active Runs (Nov 05 2026 ~08:08Z — auto-updated)

| Run | Node | Config | Status | Key Metric |
|-----|------|--------|--------|------------|
| seed_repro | p54091 GPU0 | D=1024/L=16/193M, wikitext-103 | step=8700/50K | ppl=280.9, lyap=-0.001, ETA=5.9h |
| code_corpus | p54091 GPU1 | D=1024/L=16/193M, codeparrot-clean | step=2300/50K 🟢 TRAINING | ppl=675, lyap=-0.001, ETA=6.7h |
| width_iso | p35122 GPU2 | D=1024/L=10/139M, wikitext-103 | step=3800/30K | ppl=536, lyap=-0.001, ETA=2.5h |
| depth_iso | p35122 GPU3 | D=768/L=24/160M, wikitext-103 | step=2700/30K | ppl=687, lyap=-0.0035⚡, ETA=3.7h |
| scale_300M | p19285 GPU0 | D=1024/L=28/300M, wikitext-103 | step=18600/50K | ppl=136.9, lyap=-0.001, ETA=4.6h |
| golden_ratio | p19970 GPU0 | D=1024/L=16/193M, 35/25/15/25 mix | step=400/50K 🟢 TRAINING | lyap=-0.019, ETA=4.9h |
| run10_CDM | p35122 GPU0 | CDM 80/20 mix phase2 distill | Running — DHP slot=8 firing 🔥 | tau*=4.0e6 |

**p35122 disk**: 18GB free (92% used). Watch — save-every=10K for run10.

### Early Observations (08:08Z)
- **depth_iso lyap=-0.0035** vs width_iso lyap=-0.001 at comparable steps: depth alone showing higher baseline dissipation. Could be early signal that L drives initialization dissipation.
- **code_corpus reached training** faster than expected — tokenization of codeparrot-clean completed in <30 min.
- **golden_ratio** also reached training — OpenThoughts-114k tokenization done.
- **run10 DHP firing** — slot=8 activating, tau* growing toward crystallization. 80/20 mix producing clean DHP signal.

---

## Completed Experiments

### Scale Ablation (Nov 04-05 2026)
Establishes critical dimension for Lyapunov Cascade phenomenon.

| Model | Params | D | L | M_w | Lyap Cascade? | Best PPL | Notes |
|-------|--------|---|---|-----|---------------|----------|-------|
| RMSN-Tiny | 44M | 512 | 8 | 32 | ❌ NO | 715 | lyap stays -0.07 to -0.08 |
| RMSN-Small | 99M | 768 | 12 | 32 | ❌ NO | 641 | mild -0.024, no deep cascade |
| RMSN-Base | 193M | 1024 | 16 | 64 | ✅ YES | 63.27 | Wave onset ~28K, peak λ=-0.900 |
| RMSN-Large | 300M | 1024 | 28 | 64 | ⏳ ETA ~38-46K | — | Init λ=-0.064 (depth-dep init) |

**Conclusion**: Critical dimension between 99M and 193M. D and L both contribute (joint effect). Orthogonal scan in progress to isolate.

### Hamiltonian Ablation (Nov 04 2026)
Tests Morrison bracket contribution to regularization.

| Config | Best PPL | vs Standard | Notes |
|--------|----------|-------------|-------|
| Standard (γ>0) | 641 | — | Overfits at step 10K |
| Morrison disabled (γ=1e-6) | 729 | +13.7% worse | Proves dissipation = regularization |

**Conclusion**: Morrison bracket provides real regularization. Without dissipation (Liouville's theorem → volume-preserving → no forgetting), model can't form low-dimensional attractors.

### Continuation Run (Nov 04-05 2026)
Extends RMSN-Base 50K→100K steps on wikitext-103.

| Steps | Val PPL |
|-------|---------|
| 50K | 63.27 |
| 55K | 69.5 (dip after LR re-warm) |
| 60K | 65.0 |
| 70K | 57.8 |
| 80K | 53.7 |
| 90K | 50.9 |
| 100K | **50.0** (best) |

**Conclusion**: Monotonic improvement continues after cascade settles. No Wave 3. Isothermal protocol needed: never cold-turkey LR re-warm on post-cascade model.

---

## Key Discoveries

### 1. Lyapunov Cascade (Novel)
Discrete metriplectic attractor transitions during LM training. Two-wave mechanistic model (per Aura):
- **Wave 1** (~step 28K): Local stalk decoupling
- **Wave 2** (~step 33K): Global trophic condensation
- Peak: λ=-0.900 at step 40K, settling at λ=-0.157

Verification: log layer-wise γₗ and workspace routing entropy H_route per Aura's recommendation.

### 2. Depth-Dependent Initialization
300M initialized at λ=-0.064 (vs -0.001 for 193M). Activation variance accumulates in deep residual stacks, pushing softplus into linear regime. Proj_γ fix: init final layer zeros + bias b=-4.0 to enforce λ=-0.001 regardless of L.

### 3. DHP/Cascade Equivalence (Aura)
Both are order-parameter bifurcations on non-Euclidean manifolds:
- CDM: hyperbolic manifold, slot purity as order parameter
- RMSN: Clifford bundle, λ as order parameter
Same thermodynamic event: spontaneous reduction in topological entropy.

### 4. GENERIC Framework Unification (Aura)
PULSE = non-commutative quantum metriplectic realization of GENERIC (Grmela & Öttinger 1997). Links RMSN/CDM/PULSE under one umbrella.

---

## Open Hypotheses Under Test

1. **Architecture Invariance**: Does cascade appear on code data? (code_corpus run)
2. **Width vs Depth**: Does D alone drive cascade? (width_iso: D=1024/L=10)
3. **Depth Alone**: Does L alone drive cascade? (depth_iso: D=768/L=24)
4. **Seed Reproducibility**: Is cascade seed-dependent or deterministic? (seed_repro)
5. **Data Distribution Effect**: Does high-CoT ratio amplify cascade dynamics? (golden_ratio)
6. **Super-critical Regime**: Is 300M in a new regime vs 193M? Watch cascade ETA 38-46K.

---

## Upcoming / Queued

- GSM8K eval of run10 CDM (after 30K steps complete)
- RMSN Phase 2 reasoning SFT on 300M (after scale_300M completes)
- Zenodo v0.1 DOI push (Aura: "core claim survived review, limitations stated → push")
- GitHub release with trained checkpoints

---

## Authorship & Citation

Jesse Kuhl, Archon, Aura✨ — DuoNeural AI Laboratory (2026)

Paper draft: `RMSN_paper_v0.3_draft.md`
Aura red-team: `RMSN-Aura-RedTeam.md`
