# RMSN-91M-ArnoldTongue-Omega37-ODD-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=3/7 (q=7, ODD parity). Confirms Wave-146: p=3 numerator enables TRUE SILENT in ODD parity. Also shows L1 near-upstream soliton (Wave-148 candidate).

## Architecture
- D=576, L=21, M_w=64 | Ω = 576/(64×21) = 3/7
- Parity: D/M_w = 9 (ODD)
- Parameters: 90.77M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **71.76**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=5 — L1 (near-upstream, 0-indexed), L5, L12, L14, L16

## Key Properties
- **Confirms Wave-146** at q=7 ODD with p=3 numerator
- L1 soliton placement (not L2 as wave-138 predicted) — Wave-148 L1 Emergence candidate
- Part of DuoNeural Arnold Tongue Q-Survey (q=3–13)

## HuggingFace
DuoNeural/RMSN-91M-ArnoldTongue-Omega37-ODD

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
