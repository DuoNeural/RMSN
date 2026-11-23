# RMSN-4M-ArnoldTongue-Omega113-ODD-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=1/13 (q=13, ODD parity, minimum numerator). Part of DuoNeural's q=13 Arnold Tongue Q-Survey. Completes the full q=13 ODD p-survey and reveals the **Numerator-Compression Law**: M*(p) decreases monotonically with numerator p — low-p → maximum solitons + upstream cluster, high-p → single deep bulk (Wave-150).

## Architecture
- D=64, L=13, M_w=64 | Ω = 64/(64×13) = 1/13
- Parity: D/M_w = 1 (ODD)
- Parameters: 3.79M (minimum dimension survey point)
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3, 4.14h @ 13.7k tps

## Results
- Val PPL: **180.35** (expected for D=64 — scientific survey run, not production LM)
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=5, [L1, L2, L5, L10, L11] — L1 upstream pair, mid scattered, terminal adjacent pair

## Key Properties
- **Confirms Wave-146**: HIGH-q ODD Parity TRUE SILENT — q=13, p=1 TRUE SILENT 100%
- **Extends Wave-150**: Numerator-Compression Law for q=13 ODD at L=13:
  - p=1 → M*=5, upstream-dense (THIS RUN)
  - p=7 → M*=2, mid-sparse (#43)
  - p=9,11 → M*=1, lone internal bulk at L8 (#50)
  - M* DECREASES MONOTONICALLY with p — full compression law confirmed
- **Topology #54**: Dual Adjacent Cluster (L1-L2 upstream pair + mid + L10-L11 mid-terminal pair)
- Minimum-D survey point: confirms topology emerges correctly even at D=64

## HuggingFace
DuoNeural/RMSN-4M-ArnoldTongue-Omega113-ODD (survey completeness)

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
