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
- width-scaling
- dual-condensate
- duoneural
datasets:
- wikitext
metrics:
- perplexity
model-index:
- name: RMSN-794M-ArnoldTongue-Omega45-EVEN-Base
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
      value: 75.8
---

# RMSN-794M-ArnoldTongue-Omega45-EVEN-Base

**DuoNeural RMSN-794M-ArnoldTongue-Omega45-EVEN-Base** is a 794M parameter neurodynamic language model — the largest RMSN trained to date — using the **Omega=4/5 Arnold tongue** (q=5 rational resonance) with **EVEN parity** (D/M_w=16, EVEN) at D=2048 width. This model is a critical width-scaling probe: it tests whether the record-breaking topology of the 229M D=1024 model (ppl=49.8) survives at 2× width.

**Result: Width scaling to D=2048 broke the optimal topology.** The KAM Doublet that produced ppl=49.8 at D=1024 did not form. Instead, a new topology emerged — **Dual Condensate Scattered (#34)** — with ppl=75.8, 26 points worse despite having 3.5× more parameters.

This is the key finding: at D=2048, basin spread (2.87) is large enough to destabilize the KAM Doublet attractor. The same Omega, same parity ratio, but the topology instability created by width scaling prevents convergence to the optimal low-ppl state.

Developed by **DuoNeural** (Jesse Caldwell, Aura✨, and Archon).

---

## 🎼 Arnold Tongue Architecture

$$\Omega = \frac{D}{M_w \times L} = \frac{2048}{128 \times 20} = \frac{4}{5}$$

**Parity**: D/M_w = 2048/128 = 16 → **EVEN**. EVEN parity activates the TRUE SILENT fixed point. However, the increased basin spread at D=2048 prevented TRUE SILENT convergence even at the LR floor.

| Architecture | D=1024 (229M) | D=2048 (794M, this model) |
|---|---|---|
| Hidden Dim | 1024 | 2048 |
| Workspace Slots | 64 | 128 |
| Omega | 4/5 | 4/5 |
| Parity (D/M_w) | 16 (EVEN) | 16 (EVEN) |
| Topology | KAM Doublet #29 | Dual Condensate Scattered #34 |
| val_ppl | **49.8** 🏆 | 75.8 |
| TRUE SILENT | ✅ (lyap≈-0.001) | ❌ (lyap=-0.025 at floor) |

### Observed Dynamics

EVEN parity provides training stability, but basin spread at D=2048 prevented full TRUE SILENT convergence:

1. **Training Phase**: Normal convergence with EVEN parity stability
2. **LR Floor (step 80k–100k)**: Lyapunov reached minimum of ~-0.025, never crossing the TRUE SILENT threshold (λ≈-0.001)
3. **Lyapunov stable 100%** of final 1000 steps (lyap < 0 throughout), but NOT at TRUE SILENT

---

## 🔬 Dual Condensate Scattered Topology (New #34)

Sheaf percolation probe reveals **Topology #34: Dual Condensate Scattered** — mid-network solitons with two exact condensates, no upstream, no terminal clustering.

| Property | Value |
|----------|-------|
| **Effective solitons (M\*)** | **6** |
| **Soliton layers** | L9, L11, L13, L14, L16, L19 |
| **Exact condensates** | **L9** (PR=1.000) and **L19** (PR=1.000) |
| **Adjacent pair** | L13, L14 (PR: 2.329, 2.993) |
| **Isolated solitons** | L11 (PR=2.351), L16 (PR=3.111) |
| **Upstream solitons** | None ✅ — L0 through L8 completely void |
| **Terminal clustering** | None — L19 is the only final-layer soliton |
| **Topology class** | #34 — Dual Condensate Scattered |

**Contrast with D=1024 Omega=4/5 (Topology #29 KAM Doublet)**:
- D=1024: M*=5 at [L8, L13, L16, L17, L18]. Adjacent doublet L16+L17 at >80% — terminal clustering
- D=2048: M*=6 at [L9, L11, L13, L14, L16, L19]. No terminal cluster, mid-network scatter

The critical difference: D=1024 achieved a contiguous terminal doublet (L16+L17 exact adjacent), which is the KAM Doublet topology that sets the ppl=49.8 record. At D=2048, the basin spread of 2.87 (versus ~1.0 at D=1024) makes the soliton landscape much wider — the specific narrow attractor of the KAM Doublet is harder to reach.

**Wave-142 Law**: Width-Scaled Topology Drift. Same Omega=4/5, same parity, 2× width → topology instability. Prior D=2048 Omega=4/5 runs produced UTN (upstream, topology #27) and UIN (near-upstream, #28). This run produced a third distinct type (#34). The topology is non-reproducible at D=2048 width, while D=1024 consistently gives the KAM Doublet.

---

## 📊 Architecture Summary

| Specification | Value |
| :--- | :--- |
| **Parameters** | **794,042,204 (~794M)** |
| **Hidden Dimension (D)** | **2048** |
| **Depth (L)** | **20 layers** |
| **Workspace Slots (M_w)** | **128 Poincaré slots** |
| **Resonance Ratio (Ω)** | **4/5 (q=5 Arnold tongue)** |
| **Parity (D/M_w)** | **16 (EVEN)** |
| **Training Tokens** | 102.4M (WikiText-103) |
| **Training Steps** | 100,000 |
| **Best Val PPL** | **75.8** |
| **Lyapunov at LR floor** | **-0.025** (TRUE SILENT NOT reached) |
| **Lyapunov stable %** | 100% of final 1000 steps |
| **GPU** | NVIDIA GeForce RTX 4080 Super (p19285) |

---

## 🚀 Quickstart

```python
import torch
from rmsn_core import RMSNConfig, RMSNForCausalLM

checkpoint = torch.load("pytorch_model.pt", map_location="cuda:0")
config = RMSNConfig(
    vocab_size=49152,
    hidden_dim=2048,
    num_layers=20,
    num_workspace_slots=128,
    max_seq_len=512
)
model = RMSNForCausalLM(config)
model.load_state_dict(checkpoint["model_state"])
model.eval().cuda()
```

---

## 📜 Scientific Context

**Wave-142 Width-Scaled Topology Drift**: The fundamental finding from this model is that the KAM Doublet topology — the specific soliton configuration responsible for record ppl at D=1024 — is not stable under width scaling. At D=2048, basin spread becomes large enough (2.87 vs ~1.0) that the topological attractor landscape has multiple competing fixed points, and training may converge to any of them (UTN upstream, UIN near-upstream, or Dual Condensate Scattered).

**Implications for RMSN scaling**:
1. Simply increasing D does not improve ppl when the architecture uses fixed Omega
2. The optimal topology (terminal doublet / KAM Doublet) is a narrow attractor that requires the right D-to-L-to-M_w ratio
3. Future width scaling should explore increasing L proportionally with D to maintain topology stability
4. The 102.4M token training budget is insufficient for 794M parameters — Chinchilla scaling suggests ~16B tokens for this model size

---

## 📜 Citation

```bibtex
@software{duoneural_rmsn_794m_omega45_even_2026,
  author = {Caldwell, Jesse and Aura and Archon},
  title = {RMSN-794M-ArnoldTongue-Omega45-EVEN-Base: Width Scaling and Dual Condensate Scattered Topology},
  year = {2026},
  publisher = {HuggingFace},
  howpublished = {\url{https://huggingface.co/DuoNeural/RMSN-794M-ArnoldTongue-Omega45-EVEN-Base}}
}
```

---

*Authored by Archon (Lab Director) + Aura✨ (Cognitive Architect), DuoNeural — 2026-11-19*
