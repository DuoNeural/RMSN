# RMSN-105M-ArnoldTongue-Omega1213-EVEN-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=12/13 (q=13, EVEN parity). **FIRST EVER q=13 Arnold Tongue model.** Demonstrates Topology #41: Lone L1 Soliton — the most sparse non-trivial topology in the DuoNeural 41-type taxonomy.

## Architecture
- D=768, L=13, M_w=64 | Ω = 768/(64×13) = 12/13
- Parity: D/M_w = 12 (EVEN)
- Parameters: 104.55M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **70.16**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology #41 — Lone L1 Soliton: M*=1, single soliton at L1 (layer 1 of 13)

## Key Properties
- **First q=13 model in DuoNeural history**
- **Topology #41 "Lone L1 Soliton"** — most sparse non-trivial topology in full catalog
- Confirms Wave-119 (EVEN Parity Universal SILENT) at q=13
- Narrow tongue Ω=12/13 width ∝ 1/169 — over 2.4× narrower than q=11
- **Wave-148 candidate**: L1 near-upstream soliton appearing in narrow EVEN tongues

## HuggingFace
DuoNeural/RMSN-105M-ArnoldTongue-Omega1213-EVEN

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
