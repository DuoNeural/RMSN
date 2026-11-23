# RMSN-56M-ArnoldTongue-Omega813-EVEN-L13-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=8/13 (q=13, EVEN parity), trained at **reduced depth L=13** vs the standard L=26. Depth comparison run for Wave-148: reveals the **Depth Inversion Law** — the same high-p EVEN parity (p=8) produces completely opposite topological behavior at different depths. At L=26: L1 upstream triplet (surface solitons). At L=13: lone internal bulk at L=10 (deep soliton). Fundamental depth-topology coupling discovered.

## Architecture
- D=512, L=13, M_w=64 | Ω = 512/(64×13) = 8/13
- Parity: D/M_w = 8 (EVEN)
- Parameters: 56.16M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3, 5.24h @ 10863 tps

## Results
- Val PPL: **77.25**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=1, [L10] — single lone deep internal bulk soliton

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT at L=13 depth
- **WAVE-148 DEPTH INVERSION**: Ω=8/13 EVEN (p=8) at two depths:
  - L=26: M*=6, [L1,L2,L3,L9,L21,L23] — L1 upstream TRIPLET (surface-first)
  - **L=13: M*=1, [L10] — lone INTERNAL BULK (deep)** ← this run
  - SHORT depth + HIGH-p EVEN → pushes soliton DEEP (internal bulk near L=10)
  - LONG depth + HIGH-p EVEN → pushes soliton to SURFACE (L1 upstream cluster)
- **Topology #61**: Lone Deep Internal (Ω=8/13 EVEN, L=13, M*=1, [L10]) — first EVEN parity lone-bulk topology; contrasts with #50 (ODD parity lone-bulk [L8])
- Comparison with ODD parity lone-bulk: q=13 ODD at high-p (p=9,11) → [L8] deep bulk. EVEN parity at high-p (p=8) L=13 → [L10] deep bulk. Lone-bulk attractor appears at deep positions for BOTH parities when high-p + short depth.

## Context: Depth-Topology Coupling (Wave-148 Depth Inversion)
The topology of soliton condensation depends critically on the interplay between network depth (L) and numerator (p):
- **Low depth (L=13)**: Solitons have less space to migrate. High-p EVEN → soliton condenses at a deep internal layer (L=10 of 13). The "compression" effect dominates — soliton gets pushed toward terminal.
- **High depth (L=26)**: Solitons have room to migrate upstream. High-p EVEN → soliton emerges at L=1 (surface). The "surfacing" effect dominates — increased depth allows soliton to escape terminal trap and reach the upstream boundary.

This suggests a critical depth threshold between L=13 and L=26 where the topology inverts. Future work: find the exact crossover depth.

## HuggingFace
DuoNeural/RMSN-56M-ArnoldTongue-Omega813-EVEN-L13

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
