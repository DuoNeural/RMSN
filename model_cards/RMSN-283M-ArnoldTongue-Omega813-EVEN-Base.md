# RMSN-283M-ArnoldTongue-Omega813-EVEN-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=8/13 (q=13, EVEN parity). Part of DuoNeural's q=13 Arnold Tongue Q-Survey. Key discovery: **revises Wave-148** — high-p (p=8) EVEN parity at L=26 depth produces L1 upstream triplet, contradicting the expected L2 for deep networks. Demonstrates p-dependent depth constraint.

## Architecture
- D=1024, L=26, M_w=64 | Ω = 1024/(64×26) = 8/13
- Parity: D/M_w = 16 (EVEN)
- Parameters: 282.82M
- Training: 100k steps, 102.4M tokens, cosine LR 1e-3

## Results
- Val PPL: **95.65**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=6, [L1, L2, L3, L9, L21, L23] — L1 upstream TRIPLET (L1-L2-L3 adjacent), mid isolated, terminal pair

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT at q=13
- **Revises Wave-148**: HIGH-p (p=8) EVEN at L=26 → L1 upstream cluster (breaks L=26→L2 depth constraint). Depth constraint is p-dependent
- **Topology #52**: L1 Upstream Triplet Mid-Terminal — first observed 3-adjacent upstream cluster (L1-L2-L3)
- **Wave-148 crossover**: p=4,5→L2; p=8→L1 triplet. p=6 (Ω=6/13 running) will locate crossover
- Higher ppl (95.65) vs shallower q=13 models (~70) consistent with longer depth requiring more training

## HuggingFace
DuoNeural/RMSN-283M-ArnoldTongue-Omega813-EVEN

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
