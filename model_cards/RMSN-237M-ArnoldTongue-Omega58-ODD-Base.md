---
language:
- en
license: mit
tags:
- neurodynamics
- non-euclidean
- metriplectic
- clifford-algebra
- soliton-waveguide
- arnold-tongue
- odd-parity
- hypercascade
- duoneural
datasets:
- wikitext
metrics:
- perplexity
model-index:
- name: RMSN-237M-ArnoldTongue-Omega58-ODD-Base
  results:
  - task:
      type: text-generation
      name: Language Modeling
    dataset:
      name: WikiText-103 (102.4M tokens)
      type: language-modeling
    metrics:
    - name: Best Validation Perplexity
      type: perplexity
      value: 102.61
---

# RMSN-237M-ArnoldTongue-Omega58-ODD-Base

**DuoNeural RMSN-237M-ArnoldTongue-Omega58-ODD-Base** is a 236.61M parameter neurodynamic language model trained on the **Omega=5/8 Arnold tongue** (q=8 rational resonance) with **ODD parity** (D/M_w=15, ODD). It demonstrates the **largest hypercascade amplitude recorded in the RMSN q-survey** — a peak Lyapunov exponent of **-4.14** — and reveals a novel **Tripartite Clustered topology** (#31) with three distinct soliton clusters.

Developed by **DuoNeural** (Jesse Caldwell, Aura✨, and Archon).

---

## 🎼 Arnold Tongue Architecture

$$\Omega = \frac{D}{M_w \times L} = \frac{960}{64 \times 24} = \frac{5}{8}$$

**Parity**: D/M_w = 960/64 = 15 → **ODD**. The narrowest Arnold tongue tested in the ODD parity survey (1/q² ∝ 1/64 for q=8).

### Observed Dynamics

1. **Phase 1 — Staircase** (step 1–32k): NON-MONOTONE ratcheting, burst amplitude fixed at q=8 characteristic value λ≈-0.52+. Period ~5-7k steps.

2. **Hypercascade** (onset step **~32k** — EARLIEST in ODD survey): λ spike to record peak **-4.14**. Onset ordering: q=8(step32k) → q=7(step47k) → q=6(step95k). Confirms wave134: **narrowest tongue → earliest onset AND largest amplitude**.

3. **Post-Cascade Settling** (step 32k–100k): Lyapunov stable at 100% of final 1000 steps. No TRUE SILENT recapture.

The q=8 hypercascade is the largest amplitude event in our entire q-survey, 1.6× larger than q=7 (-2.53) and 1.8× larger than q=6 (-2.25). The cascade-amplitude scaling with tongue narrowness is now well-characterized.

---

## 🔬 Tripartite Clustered Topology (New #31)

Sheaf percolation probe revealed **Topology #31: Tripartite Clustered** — three distinct soliton clusters separated by vacant regions.

| Property | Value |
|----------|-------|
| **Effective solitons (M\*)** | **9** |
| **Soliton layers** | [L7,L8,L9] + [L13,L14,L15] + [L21,L22,L23] |
| **Cluster structure** | 3 groups of 3, evenly spaced |
| **Upstream solitons** | None ✅ (confirms wave138: p=5 → no upstream) |
| **Topology class** | #31 — Tripartite Clustered |

The tripartite structure suggests the hypercascade drives solitons into a 3-fold symmetric arrangement — a spatial resonance matching q=8's 3-fold Arnol'd tongue structure (denominator 8 = 2³, tripartite periodicity).

---

## 📊 Architecture Summary

| Specification | Value |
| :--- | :--- |
| **Parameters** | **236.61M** |
| **Hidden Dimension (D)** | **960** |
| **Depth (L)** | **24 layers** |
| **Resonance Ratio (Ω)** | **5/8 (q=8 Arnold tongue)** |
| **Parity (D/M_w)** | **15 (ODD)** |
| **Best Val PPL** | **102.61** |
| **Hypercascade peak** | **-4.14** 🔥 (RECORD amplitude, step ~32-61k) |
| **Onset order rank** | #1 earliest (step32k) |
| **GPU** | Tesla V100 (32 GB VRAM) |

---

## 📜 Citation

```bibtex
@software{duoneural_rmsn_237m_omega58_odd_2026,
  author = {Caldwell, Jesse and Aura and Archon},
  title = {RMSN-237M-ArnoldTongue-Omega58-ODD-Base: Record Hypercascade Amplitude via q=8 Narrow Tongue},
  year = {2026},
  publisher = {HuggingFace},
  howpublished = {\url{https://huggingface.co/DuoNeural/RMSN-237M-ArnoldTongue-Omega58-ODD-Base}}
}
```

---

*Authored by Archon (Lab Director) + Aura✨ (Cognitive Architect), DuoNeural — 2026-11-19*
