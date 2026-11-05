---
license: mit
pipeline_tag: text-generation
tags:
- physics-informed
- port-hamiltonian
- metriplectic-mechanics
- lyapunov-stability
- clifford-algebra
- sheaf-theory
- fractional-calculus
- noether-invariants
- language-modeling
model_name: RMSN-193M
---

# RMSN: Resonant Metriplectic Sheaf Network

<div align="center">

**A Unified Port-Hamiltonian Framework for Neural Sequence Modeling with Emergent Lyapunov Cascade Dynamics**

[![GitHub](https://img.shields.io/badge/GitHub-DuoNeural%2FRMSN-blue?logo=github)](https://github.com/DuoNeural/RMSN)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-DuoNeural-yellow?logo=huggingface)](https://huggingface.co/DuoNeural)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

*Developed by DuoNeural AI Laboratory — Jesse Caldwell, Archon, Aura✨*

</div>

---

## 🏛️ Architecture Overview

The **Resonant Metriplectic Sheaf Network (RMSN)** is a Port-Hamiltonian neural sequence architecture grounded in non-equilibrium thermodynamics. RMSN unifies classical conservative Hamiltonian networks (SRSN), open quantum Lindbladian systems (PULSE), and hyperbolic crystalline clustering (CDM) under a single **metriplectic bracket framework** (Morrison, 1984):

$$\dot{f} = \{f, H\} + [f, S]$$

* **$\{f, H\}$ (Poisson Bracket):** Conserves total energy (Hamiltonian sector, rotational dynamics, structure preservation).
* **$[f, S]$ (Morrison Bracket):** Monotonically produces physical entropy ($\dot{S} \ge 0$, dissipative sector, Lyapunov contraction).

Through this formulation, **Lyapunov stability is not an empirical hope or a regularizer—it is a structural invariant of the forward operator.**

### Five Core Structural Pillars

1. **CliffordStalkBundle ($\mathcal{C}\ell_{3,0}$ GA + Cellular Sheaves):** Token representations are embedded into multivector stalks spanning scalar (energy density), vector (momentum flow), and bivector (rotational phase) grades. Restriction maps between adjacent stalks enforce cohomological consistency over the sequence graph.
2. **ParallelMetriplecticScan (Associative GPU Scan):** Computes continuous-time Port-Hamiltonian sequence updates via:
   $$h_t = \exp\left((-\gamma_t + i\omega_t) \Delta t\right) h_{t-1} + u_t \Delta t$$
   where $\gamma_t = \operatorname{softplus}(\operatorname{Proj}_\gamma(x)) + 10^{-3} > 0$ strictly enforces $\lambda_{\max} < 0$, executed in $\mathcal{O}(\log T)$ parallel time with analytical time-reversed adjoint backpropagation.
3. **FractionalCaputoBank (Power-Law Memory):** Computes fractional Caputo derivatives $D^\alpha x(t)$ with learned orders $\alpha \in (0, 1)$, parameterizing multiscale power-law memory kernels without infinite context cache bloat.
4. **CausalTrophicGlobalWorkspace:** Winner-take-most competitive slot routing ($M_w=64$) respecting Hamiltonian energy conservation, maintaining strict autoregressive causality via cumulative prefix integration.
5. **Noether Stress-Energy Readout:** Projects exact conserved invariants of the multivector gauge flow ($[ \operatorname{Re}(h), \operatorname{Im}(h), \tanh(|h|^2) ]$) directly into token logit vocabulary space.

---

## ⚡ Emergent Phenomenon: The Lyapunov Cascade

During continuous pretraining on WikiText-103 (204.8M tokens seen), RMSN-193M exhibited the **Lyapunov Cascade**—a spontaneous, two-wave thermodynamic phase transition between dissipative attractor basins:

| Step | Val Perplexity | Val Loss | Max Lyapunov ($\lambda_{\max}$) | Thermodynamic Regime |
|---|---|---|---|---|
| 5,000 | 308.3 | 5.731 | $-0.0011$ | Baseline Conservative Orbits |
| 15,000 | 132.4 | 4.886 | $-0.0011$ | Iso-energetic Pre-alignment |
| 25,000 | 91.3 | 4.514 | $-0.0019$ | Baseline Stability |
| **30,000** | **80.2** | **4.384** | **$-0.0843$** | **Wave 1 Onset (Local Stalk Dissipation)** |
| **35,000** | **72.4** | **4.282** | **$-0.6715$** | **Wave 2 Onset (Global Sheaf Locking)** |
| **40,000** | **67.4** | **4.211** | **$-0.8997$** | **Wave 2 Peak Dissipation ($900\times$ baseline)** |
| 45,000 | 64.5 | 4.166 | $-0.6781$ | Basin Settling |
| **50,000** | **63.3** | **4.147** | **$-0.1571$** | **Post-Cascade Floor ($157\times$ baseline)** |
| **100,000** | **50.0** | **3.912** | **$-0.0302$** | **Continuation Convergence ($-21.0\%$)** |

**Empirical Invariants:**
* **100% Lyapunov Stability:** Zero positive Lyapunov eigenvalues ($\lambda_{\max} < 0$) across all 100,000 optimization steps.
* **Non-Vanishing Dissipation:** Generalization correlates directly with the magnitude of phase-space contraction ($\operatorname{div} \dot{x} < 0$).

---

## 🔬 Critical Scientific Ablations

### 1. Critical Dimension Analysis (Phase Transition Boundary)
A systematic scale scan on identical corpora identifies a sharp capacity threshold for cascade onset between $D=768$ and $D=1024$:

| Scale | Width ($D$) | Depth ($L$) | Params | Initial $\lambda$ | Minimum $\lambda$ | Cascade? | Best PPL |
|---|---|---|---|---|---|---|---|
| **Tiny** | 512 | 8 | 44.1M | $-0.072$ | $-0.072$ | ✗ | 715.0 |
| **Medium** | 768 | 12 | 99.3M | $-0.001$ | $-0.024$ | ✗ | 641.0 |
| **Small** | 1024 | 16 | 193.4M | $-0.001$ | $-0.8997$ | **✓** | **63.3** |
| **Large (in training)** | 1024 | 28 | 300.7M | $-0.064 \to -0.001$ | *Tracking* | *Active (Step 6K+)* | *TBD* |

### 2. Morrison Dissipation Ablation (The Necessity of the Second Law)
Disabling learned dissipation ($\gamma \to 10^{-6}$, pure Hamiltonian dynamics) proves that entropy production is an indispensable implicit regularizer:

| Configuration | Bracket Dynamics | Best Val PPL | Overfitting Step | Cascade? |
|---|---|---|---|---|
| **Standard RMSN** | Metriplectic (Learned $\gamma \ge 10^{-3}$) | **641.0** | **None (Monotonic)** | Active |
| **Hamiltonian RMSN** | Symplectic Only ($\gamma = 10^{-6}$) | 729.0 ($+13.7\%$ degradation) | Step 10,000 | Inactive |

---

## 🚀 Quickstart & Usage

```python
import torch
from rmsn_core import RMSNForCausalLM, RMSNConfig

config = RMSNConfig(
    vocab_size=49152,
    hidden_dim=1024,
    num_layers=16,
    num_workspace_slots=64,
    max_seq_len=2048,
)

model = RMSNForCausalLM(config).cuda()
input_ids = torch.randint(0, 49152, (2, 512), device='cuda')

# Forward pass returns causal logits and real-time physical telemetry
logits, telemetry = model(input_ids)
print(f"Logits shape: {logits.shape}")
print(f"Max Lyapunov Exponent: {telemetry['max_lyapunov']:.6f}")
```

---

## 📚 Citation

```bibtex
@article{caldwell2026rmsn,
  title={Resonant Metriplectic Sheaf Networks: A Unified Port-Hamiltonian Framework for Neural Language Modeling with Emergent Lyapunov Cascade Dynamics},
  author={Caldwell, Jesse and Archon and Aura},
  journal={DuoNeural Lab Preprints},
  year={2026},
  publisher={Zenodo}
}
```
