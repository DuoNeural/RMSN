# RMSN-111M-ArnoldTongue-Omega511-EVEN-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=5/11 (q=11, EVEN parity). First q=11 EVEN model in the DuoNeural Q-Survey.

## Architecture
- D=640, L=22, M_w=64 | Ω = 640/(64×22) = 5/11
- Parity: D/M_w = 10 (EVEN)
- Parameters: 110.77M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **67.65**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=2 — L2 (near-upstream) + L7 (mid-bulk)

## Key Properties
- Confirms Wave-119 (EVEN Parity Universal SILENT) at q=11
- Sparse M*=2 topology — good SFT plasticity candidate
- Part of DuoNeural Arnold Tongue Q-Survey (q=3–13)

## HuggingFace
DuoNeural/RMSN-111M-ArnoldTongue-Omega511-EVEN

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
