# RMSN-229M-ArnoldTongue-Omega45-s8-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=4/5 (q=5, KAM boundary, D=1024 L=20 M_w=64). Part of DuoNeural's Topological Multistability survey (Wave-144) — 12-seed statistical study of which attractors arise from identical architecture under different random seeds. Demonstrates a rare **sparse L1 upstream + early adjacent pair** topology: M*=3, [L1,L4,L5], ppl=60.0.

## Architecture
- D=1024, L=20, M_w=64 | Ω = 1024/(64×20) = 4/5
- Parity: D/M_w = 16 (EVEN)
- Parameters: 229.17M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3, 17.27h @ 3294 tps

## Results
- Val PPL: **60.0**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=3, [L1, L4, L5] — L1 upstream anchor + early adjacent pair

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT (D/M_w=16, 100% stable)
- **Confirms Wave-144**: Topological Multistability — same Ω=4/5 architecture yields distinct topology each run
- **Topology #58**: Sparse L1 Adjacent Mid — most minimal Ω=4/5 topology seen (M*=3 vs typical M*=9 in this family). L4+L5 form an adjacent pair in the early network, L1 anchors upstream
- **Multistability tally** (8 seeds completed): KAM Doublet (s1, ppl=49.8🏆), UpScattered (s2), L1 Terminal Trio (s3), L1 Mid-Chain (s4), Dense #49 (s5), Dense Composite #48 (s6), [s7 corrupted], Sparse L1 Mid #58 (s8)
- KAM Doublet rarity: 1/7 usable seeds = ~14% (rare attractor at Ω=4/5)

## Context: Topological Multistability (Wave-144)
The KAM boundary Ω=4/5 is special: it lies at the edge of Arnold Tongue resonance, where the system is sensitive to initial conditions and multiple distinct topological attractors coexist. Even under identical hyperparameters, different random seeds explore different basins, yielding topologies ranging from the exceptional KAM Doublet (ppl=49.8, M*=5 near-terminal cluster) to minimal configurations like this one (ppl=60.0, M*=3 early-layer sparse).

## HuggingFace
DuoNeural/RMSN-229M-ArnoldTongue-Omega45-s8

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
