# RMSN-229M-ArnoldTongue-Omega45-s9-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=4/5 (q=5, KAM boundary, D=1024 L=20 M_w=64). Part of DuoNeural's Topological Multistability survey (Wave-144) — 12-seed statistical study of which attractors arise from identical architecture under different random seeds. Demonstrates a **sparse mid-scatter + 5-adjacent terminal run** topology: M*=8, [L1,L6,L13,L15,L16,L17,L18,L19], ppl=59.9.

## Architecture
- D=1024, L=20, M_w=64 | Ω = 1024/(64×20) = 4/5
- Parity: D/M_w = 16 (EVEN)
- Parameters: 229.17M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **59.9**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=8, [L1, L6, L13, L15, L16, L17, L18, L19] — L1 upstream + L6 isolated mid + L13 lone near-terminal + [L15-L19] 5-adjacent terminal run

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT (D/M_w=16, 100% stable)
- **Confirms Wave-144**: Topological Multistability — same Ω=4/5 architecture yields distinct topology each run
- **Topology #59**: Sparse-Mid Terminal Run — features a 5-layer contiguous terminal run [L15-L19] with scattered precursors at L1, L6, L13. The longest terminal run seen in the Ω=4/5 family. L14 gap before the terminal cluster creates a distinctive sparse+dense pattern.
- **Multistability tally** (10 seeds): KAM Doublet (s1, 49.8🏆), UpScattered (s2, 67.92), #39 (s3, 59.73), #40 (s4, 58.71), #49 (s5, 60.55), #48 (s6, 57.32), [s7 corrupted/disk], #58 Sparse L1 Mid (s8, 60.0), #59 Sparse-Mid Terminal Run (s9, 59.9), [s10-s18 running]
- KAM Doublet rarity: 1/9 usable seeds = ~11% — rare attractor

## Context: Topological Multistability (Wave-144)
Each run at Ω=4/5 explores a different basin of attraction in the same energy landscape. The 5-adjacent terminal run [L15-L19] in this seed reflects a topology where the network "chose" to pack solitons near the output end. The ppl=59.9 is competitive with other seeds (59-61 range for non-KAM-Doublet seeds), suggesting the energy landscape has many near-equivalent minima at this PPL level, with the KAM Doublet being a rare deep attractor at 49.8.

## HuggingFace
DuoNeural/RMSN-229M-ArnoldTongue-Omega45-s9

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
