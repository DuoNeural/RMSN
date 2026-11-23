# RMSN-171M-ArnoldTongue-Omega613-EVEN-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=6/13 (q=13, EVEN parity, p=6). The critical crossover run for Wave-148: confirms that **p=6 is the exact crossover** where EVEN q=13 parity at L=26 depth transitions from L2 upstream (p≤5) to L1 upstream (p≥6). Topology: L1 upstream anchor + 4-adjacent mid cluster [L9-L12].

## Architecture
- D=768, L=26, M_w=64 | Ω = 768/(64×26) = 6/13
- Parity: D/M_w = 12 (EVEN)
- Parameters: 171.35M
- Training: 100k steps, 102.4M tokens, cosine LR 1e-3, 11.05h @ 2574 tps

## Results
- Val PPL: **100.1**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=5, [L1, L9, L10, L11, L12] — L1 upstream + 4-adjacent mid cluster

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT at q=13
- **CONFIRMS Wave-148 crossover at p=5→6**: p=6 (this run) → L1 upstream. p=5 (prior) → L2 upstream. Exact crossover identified.
  - Full EVEN q=13 at L=26 survey: p=2→L2; p=4→L2; p=5→L2; **p=6→L1 (crossover)**; p=8→L1 triplet; p=10,12→L1
- **Wave-148 DEPTH INVERSION**: Compare p=8 at different depths: L=26→L1 triplet [L1,L2,L3] (#52cand); L=13→lone INTERNAL BULK [L10] (#61). Short depth + high-p → pushes soliton DOWN (deep bulk); long depth + high-p → pushes soliton to SURFACE (L1). Fundamental depth-topology coupling.
- **Topology #60**: L1 Mid-Adjacent Quad — unique compact 4-adjacent cluster in mid-network ([L9-L12]) anchored by L1 upstream soliton

## Context: Wave-148 p-Survey (EVEN q=13 at L=26)
Complete p-survey for EVEN parity q=13 at L=26 depth:
| p | Ω | Topology | Upstream layer |
|---|---|----------|----------------|
| 2 | 2/13 | #56 Minimal Adjacent Upstream | L2 |
| 4 | 4/13 | #53cand Near-Upstream Mid-Sparse | L2 |
| 5 | 5/13 | #45 Near-Upstream Mid-Adjacent Pair | L2 |
| **6** | **6/13** | **#60 L1 Mid-Adjacent Quad** | **L1 ← crossover** |
| 8 | 8/13 | #52cand L1 Upstream Triplet | L1 |
| 10 | 10/13 | (survey) | L1 |
| 12 | 12/13 | (survey) | L1 |

## HuggingFace
DuoNeural/RMSN-171M-ArnoldTongue-Omega613-EVEN

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
