# RMSN-91M-ArnoldTongue-Omega1113-ODD-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=11/13 (q=13, ODD parity). Part of DuoNeural's q=13 Arnold Tongue Q-Survey. Independently confirms **Topology #50: Lone Internal Bulk** at the same position (L8) as Ω=9/13 ODD, validating the High-Numerator Compression Law.

## Architecture
- D=704, L=13, M_w=64 | Ω = 704/(64×13) = 11/13
- Parity: D/M_w = 11 (ODD)
- Parameters: 91.17M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **71.85**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology #50 — Lone Internal Bulk: M*=1, single soliton at L8 (layer 8 of 13)

## Key Properties
- **Confirms Wave-146**: HIGH-q ODD Parity TRUE SILENT at q=13 ODD
- **Confirms Wave-150 candidate**: q=13 ODD p=11 → SAME topology as p=9 (both M*=1 [L8]). Two independent confirmations of Lone Internal Bulk at L8 for high-p ODD
- **Topology #50 second instance**: Identical soliton position despite D=704 vs D=576 — position is determined by p/q ratio, not raw D
- Part of DuoNeural Arnold Tongue Q-Survey (q=13)

## HuggingFace
DuoNeural/RMSN-91M-ArnoldTongue-Omega1113-ODD

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
