# RMSN-87M-ArnoldTongue-Omega413-EVEN-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=4/13 (q=13, EVEN parity). Part of DuoNeural's q=13 Arnold Tongue Q-Survey. Demonstrates low-numerator EVEN topology behavior: L2 near-upstream soliton consistent with Wave-148 depth constraint (L=26→L2 for low-p EVEN).

## Architecture
- D=512, L=26, M_w=64 | Ω = 512/(64×26) = 4/13
- Parity: D/M_w = 8 (EVEN)
- Parameters: 87.15M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **71.31**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=4, [L2, L9, L11, L22] — L2 upstream, mid-scattered pair, terminal

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT at q=13
- **Confirms Wave-148 depth constraint**: L=26 + low-p (p=4) → L2 upstream soliton ✓
- **Wave-148 p-dependence**: p=4 and p=5 both give L2 upstream at L=26; p=8 breaks to L1 triplet. Crossover between p=5 and p=8 (p=6 Ω=6/13 running)
- Topology #53: Near-Upstream Mid-Sparse Terminal (L2 upstream + mid pair + terminal)
- Part of DuoNeural Arnold Tongue Q-Survey (q=13 EVEN complete set)

## HuggingFace
DuoNeural/RMSN-87M-ArnoldTongue-Omega413-EVEN

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
