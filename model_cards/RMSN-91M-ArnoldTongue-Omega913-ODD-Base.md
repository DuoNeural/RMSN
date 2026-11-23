# RMSN-91M-ArnoldTongue-Omega913-ODD-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=9/13 (q=13, ODD parity). Part of DuoNeural's q=13 Arnold Tongue Q-Survey. Demonstrates **Topology #50: Lone Internal Bulk** — M*=1 single soliton at L8, confirming the High-Numerator Compression Law for ODD parity.

## Architecture
- D=576, L=13, M_w=64 | Ω = 576/(64×13) = 9/13
- Parity: D/M_w = 9 (ODD)
- Parameters: 91.17M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **76.7**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology #50 — Lone Internal Bulk: M*=1, single soliton at L8 (layer 8 of 13)

## Key Properties
- **Confirms Wave-146**: HIGH-q ODD Parity TRUE SILENT at q=13 ODD
- **Discovers Wave-150 candidate**: HIGH NUMERATOR COMPRESSION — q=13 ODD, p≥9 → M*=1 lone internal bulk at L8 (confirmed independently by Ω=11/13 ODD, same position)
- **Topology #50**: Lone Internal Bulk — soliton collapses to single mid-to-terminal position under high p/q ratio ODD
- Part of DuoNeural Arnold Tongue Q-Survey (q=13)

## HuggingFace
DuoNeural/RMSN-91M-ArnoldTongue-Omega913-ODD

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
