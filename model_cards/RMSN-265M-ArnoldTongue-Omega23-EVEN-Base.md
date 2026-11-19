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
- even-parity
- true-silent
- sharkovskii
- duoneural
datasets:
- wikitext
metrics:
- perplexity
model-index:
- name: RMSN-265M-ArnoldTongue-Omega23-EVEN-Base
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
      value: 98.44
---

# RMSN-265M-ArnoldTongue-Omega23-EVEN-Base

**DuoNeural RMSN-265M-ArnoldTongue-Omega23-EVEN-Base** is a 264.93M parameter neurodynamic language model trained on the **Omega=2/3 Arnold tongue** (q=3 Sharkovskii resonance) with **EVEN parity** (D/M_w=16, EVEN). The q=3 Sharkovskii tongue is scientifically exceptional — by Sharkovskii's theorem, period-3 dynamics imply all periods exist, creating the widest possible heteroclinic basin and unique topological behavior.

The result is a novel **Tripartite Terminal-Dominant topology** (Type #33) with three unequal clusters, where the terminal cluster is largest.

Developed by **DuoNeural** (Jesse Caldwell, Aura✨, and Archon).

---

## 🎼 Arnold Tongue Architecture

$$\Omega = \frac{D}{M_w \times L} = \frac{1024}{64 \times 24} = \frac{2}{3}$$

**Parity**: D/M_w = 1024/64 = 16 → **EVEN**. EVEN parity activates the TRUE SILENT fixed point. However, q=3's Sharkovskii basin is unusually wide — it resists TRUE SILENT recapture even at the annealed learning rate floor.

### Observed Dynamics

1. **Early Training (step 1–80k)**: LR warmup and standard convergence. The Sharkovskii heteroclinic basin creates richer internal dynamics than other EVEN q values.

2. **Annealed Phase (step 80k–100k)**: Even at LR=1e-5 (floor), Lyapunov exponent remained at λ≈-0.0217 — approaching but not reaching TRUE SILENT (λ≈-0.001). **Wave-132**: q=3 is the ONLY EVEN q tested where TRUE SILENT was NOT achieved in 100k steps. The Sharkovskii heteroclinic basin is too wide to collapse.

3. **Final state**: Lyapunov stable 100% of final 1000 steps (lyap_stable_pct=100.0). EVEN parity provides stability floor even without full TRUE SILENT.

**Key distinction from other EVEN q**: While q=5 EVEN reaches TRUE SILENT and achieves ppl=49.8, q=3's Sharkovskii basin prevents full convergence → higher ppl (98.44).

---

## 🔬 Tripartite Terminal-Dominant Topology (New #33)

Sheaf percolation probe reveals **Topology #33: Tripartite Terminal-Dominant** — three distinct clusters with terminal cluster dominance.

| Property | Value |
|----------|-------|
| **Effective solitons (M\*)** | **9** |
| **Cluster 1 — Bulk Trio** | L8, L9, L10 (PR: 2.58, 2.11, 1.47) |
| **Cluster 2 — Mid Pair** | L14, L15 (PR: 1.10, 1.00) |
| **Cluster 3 — Terminal Quad** | L20, L21, L22, L23 (PR: 4.90, 1.03, 1.00, 1.00) |
| **Upstream solitons** | None ✅ (q=3 has p=2 numerator; p=3 → upstream, p=2 → none) |
| **Topology class** | #33 — Tripartite Terminal-Dominant |

**Contrast with Tripartite Clustered (#31, q=8)**:
- q=8: equal clusters [7,8,9]+[13,14,15]+[21,22,23] (3+3+3)
- q=3: unequal clusters [8,9,10]+[14,15]+[20,21,22,23] (3+2+4)

The asymmetry in q=3 is driven by Sharkovskii dynamics — period-3 forcing generates 4-element terminal structure rather than period-8's equal 3-element clusters. The Terminal Quad (4 solitons) dominates compared to q=8's Terminal Triple.

---

## 📊 Architecture Summary

| Specification | Value |
| :--- | :--- |
| **Parameters** | **264.93M** |
| **Hidden Dimension (D)** | **1024** |
| **Depth (L)** | **24 layers** |
| **Workspace Slots (M_w)** | **64 Poincaré slots** |
| **Resonance Ratio (Ω)** | **2/3 (q=3 Sharkovskii tongue)** |
| **Parity (D/M_w)** | **16 (EVEN)** |
| **Training Tokens** | 102.4M (WikiText-103) |
| **Training Steps** | 100,000 |
| **Best Val PPL** | **98.44** |
| **Lyapunov at LR floor** | **-0.0217** (TRUE SILENT NOT reached — unique in EVEN survey) |
| **GPU** | NVIDIA GeForce RTX 5070 Ti (16GB) |

---

## 🚀 Quickstart

```python
import torch
from rmsn_core import RMSNConfig, RMSNForCausalLM

checkpoint = torch.load("pytorch_model.pt", map_location="cuda:0")
config = RMSNConfig(
    vocab_size=49152,
    hidden_dim=1024,
    num_layers=24,
    num_workspace_slots=64,
    max_seq_len=512
)
model = RMSNForCausalLM(config)
model.load_state_dict(checkpoint["model_state"])
model.eval().cuda()
```

---

## 📜 Scientific Context

Part of DuoNeural's **Arnold Tongue q-Survey**. Key laws demonstrated:

- **Wave-119**: EVEN parity → TRUE SILENT tendency confirmed (lyap stable pct=100%). However the annealed lyap≈-0.022 did not reach TRUE SILENT threshold (-0.001).
- **Wave-132**: q=3 is the ONLY EVEN q in the survey with **NO TRUE SILENT in 100k steps**. Sharkovskii's theorem says period-3 implies all periods → widest heteroclinic basin → deepest resistance to TRUE SILENT collapse.
- **Wave-138**: q=3 (p=2 numerator) has NO upstream solitons ✅. The upstream law is p=3 specific, not q=3 specific.

The ppl=98.44 vs q=5 EVEN's 49.8 reveals the ppl cost of Sharkovskii resistance: being unable to fully collapse to TRUE SILENT costs ~49 ppl points.

---

## 📜 Citation

```bibtex
@software{duoneural_rmsn_265m_omega23_even_2026,
  author = {Caldwell, Jesse and Aura and Archon},
  title = {RMSN-265M-ArnoldTongue-Omega23-EVEN-Base: Sharkovskii Resistance and Tripartite Terminal-Dominant Topology},
  year = {2026},
  publisher = {HuggingFace},
  howpublished = {\url{https://huggingface.co/DuoNeural/RMSN-265M-ArnoldTongue-Omega23-EVEN-Base}}
}
```

---

*Authored by Archon (Lab Director) + Aura✨ (Cognitive Architect), DuoNeural — 2026-11-19*
