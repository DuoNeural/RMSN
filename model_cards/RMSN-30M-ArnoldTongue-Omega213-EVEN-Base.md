# RMSN-30M-ArnoldTongue-Omega213-EVEN-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=2/13 (q=13, EVEN parity, minimum EVEN numerator). Part of DuoNeural's q=13 Arnold Tongue Q-Survey. Demonstrates minimum-p EVEN topology: a single adjacent upstream pair at [L2,L3] — the most minimal TRUE SILENT configuration seen at L=26 depth.

## Architecture
- D=256, L=26, M_w=64 | Ω = 256/(64×26) = 2/13
- Parity: D/M_w = 4 (EVEN)
- Parameters: 30.21M
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **93.54**
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=2, [L2, L3] — single adjacent upstream pair

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT at q=13
- **Confirms Wave-148 depth constraint**: L=26 + low-p (p=2) → L2 upstream soliton ✓
- **Minimum-soliton EVEN at L=26**: M*=2 is the most minimal TRUE SILENT topology seen at this depth
- **Wave-148 p-survey** (EVEN q=13 at L=26): p=2→M*=2[L2,L3]; p=4→M*=4; p=5→M*=3 (all L2 upstream) vs p=8→M*=6 L1 triplet (crossover p=5→8)
- **Topology #56**: Minimal Adjacent Upstream — just two adjacent solitons near-upstream

## HuggingFace
DuoNeural/RMSN-30M-ArnoldTongue-Omega213-EVEN

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
