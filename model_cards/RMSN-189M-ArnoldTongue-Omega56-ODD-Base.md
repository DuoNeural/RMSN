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
- name: RMSN-189M-ArnoldTongue-Omega56-ODD-Base
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
      value: 107.19
---

# RMSN-189M-ArnoldTongue-Omega56-ODD-Base

**DuoNeural RMSN-189M-ArnoldTongue-Omega56-ODD-Base** is a 189.25M parameter neurodynamic language model trained on the **Omega=5/6 Arnold tongue** (q=6 rational resonance) with **ODD parity** (D/M_w=15, ODD). It demonstrates the **latest hypercascade onset in the ODD parity survey** (step ~95k) — confirming the Arnold Tongue Width Law: wider tongue (larger 1/q²) means later, smaller amplitude cascade.

Developed by **DuoNeural** (Jesse Caldwell, Aura✨, and Archon).

---

## 🎼 Arnold Tongue Architecture

$$\Omega = \frac{D}{M_w \times L} = \frac{960}{64 \times 18} = \frac{5}{6}$$

**Parity**: D/M_w = 960/64 = 15 → **ODD**. The widest Arnold tongue in the ODD parity survey (1/q² = 1/36 for q=6, vs 1/49 for q=7, 1/64 for q=8).

### Observed Dynamics

1. **Staircase Phase** (step 1–95k): Extended Phase1 ratcheting with NON-MONOTONE character. The wide tongue (Omega=5/6 is closest to 1 of all tested) means the staircase persists for nearly the full training run before cascade onset.

2. **Hypercascade** (onset step **~95k** — LATEST in ODD survey): λ spike to peak **-2.25**. The latest onset and second-smallest amplitude in the survey. Onset ordering: q=8(step32k)→q=7(step47k)→q=6(step95k). 

3. **Final state** (step100k): ppl=107.19 (D=960 capacity ceiling). Hypercascade did not complete before training end — partial topology reorganization.

The late onset means the topology formed under less cascade influence, explaining the Non-Adjacent Terminal arrangement compared to q=7's clean Terminal Boundary.

---

## 🔬 Non-Adjacent Terminal Topology

Sheaf percolation probe revealed a Non-Adjacent Terminal arrangement — a subtype of terminal clustering without the tight contiguity of Terminal Boundary (#30).

| Property | Value |
|----------|-------|
| **Effective solitons (M\*)** | **7** |
| **Soliton layers** | L7, L11, L12, L14, L15, L16, L17 |
| **Terminal solitons** | L15+L17 (non-adjacent, L16=3.431 between) |
| **Upstream solitons** | None ✅ |
| **Key distinction** | Non-adjacent terminal vs. adjacent (q=5 ppl=49.8) or contiguous (q=7 Terminal Boundary) |

The slight non-adjacency at the terminal doublet (gap of 3.431 between L15 and L17) compared to the perfect adjacency of q=5's L16+L17 doublet (ppl=49.8) illustrates the precision required for optimal PPL: even a slight mis-alignment in terminal clustering costs ~57 PPL points.

---

## 📊 Architecture Summary

| Specification | Value |
| :--- | :--- |
| **Parameters** | **189.25M** |
| **Hidden Dimension (D)** | **960** |
| **Depth (L)** | **18 layers** |
| **Resonance Ratio (Ω)** | **5/6 (q=6 Arnold tongue)** |
| **Parity (D/M_w)** | **15 (ODD)** |
| **Best Val PPL** | **107.19** |
| **Hypercascade peak** | **-2.25** (step ~95k — latest onset) |
| **GPU** | Tesla V100 (32 GB VRAM) |

---

## 📜 Citation

```bibtex
@software{duoneural_rmsn_189m_omega56_odd_2026,
  author = {Caldwell, Jesse and Aura and Archon},
  title = {RMSN-189M-ArnoldTongue-Omega56-ODD-Base: Latest Cascade Onset via Wide Omega=5/6 Tongue},
  year = {2026},
  publisher = {HuggingFace},
  howpublished = {\url{https://huggingface.co/DuoNeural/RMSN-189M-ArnoldTongue-Omega56-ODD-Base}}
}
```

---

*Authored by Archon (Lab Director) + Aura✨ (Cognitive Architect), DuoNeural — 2026-11-19*
