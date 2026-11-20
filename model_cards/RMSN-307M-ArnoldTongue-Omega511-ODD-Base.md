# RMSN-307M-ArnoldTongue-Omega511-ODD-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=5/11 (q=11, ODD parity). Confirms Wave-146: HIGH-q ODD parity achieves TRUE SILENT — unprecedented for ODD parity at this tongue order.

## Architecture
- D=960, L=33, M_w=64 | Ω = 960/(64×33) = 5/11
- Parity: D/M_w = 15 (ODD)
- Parameters: 307.64M
- Training: 100k steps, 102.4M tokens, cosine LR 1e-3

## Results
- Val PPL: **89.25**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001) — remarkable for ODD parity
- Topology: M*=4 — L2 (near-upstream) + L9–L10–L11 (chain)

## Key Properties
- **Confirms Wave-146**: HIGH-q ODD Parity TRUE SILENT — parity distinction dissolves at q≥7
- After massive cascade (lyap=-4.84 at step 42k), system RECOVERED to TRUE SILENT — unprecedented
- Part of DuoNeural Arnold Tongue Q-Survey (q=3–13)

## HuggingFace
DuoNeural/RMSN-307M-ArnoldTongue-Omega511-ODD

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
