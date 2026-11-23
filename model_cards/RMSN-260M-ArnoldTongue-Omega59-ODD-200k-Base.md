# RMSN-260M-ArnoldTongue-Omega59-ODD-200k-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=5/9 (q=9, ODD parity), trained for 200k steps on 409.6M tokens. Achieves **ppl=50.04** — the closest any ODD-parity model has come to the sub-50 barrier (record held by KAM Doublet Ω=4/5 at 49.8). Demonstrates topology evolution under extended training consistent with Wave-141 (Near-Silent Limit Cycle with Inward Spiral).

## Architecture
- D=960, L=27, M_w=64 | Ω = 960/(64×27) = 5/9
- Parity: D/M_w = 15 (ODD)
- Parameters: 260.29M
- Training: 200k steps, 409.6M tokens, cosine LR 1e-3

## Results
- Val PPL: **50.04** 🔥
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=7, [L1, L6, L20, L21, L23, L24, L26] — L1 upstream with dense terminal clustering

## Key Properties
- **Sub-50 near-miss**: 0.04 from the sub-50 all-time barrier (record: 49.8 at Ω=4/5 KAM Doublet)
- **Extended-training topology shift**: 100k run shows L3 upstream (#35); 200k run shows L1 upstream — consistent with Wave-141 inward spiral mechanism where additional training drives solitons toward lower-index attractors
- **ODD parity record for q=9**: best ever ODD parity PPL at 200k training budget
- 300k run ongoing to attempt sub-50 breakthrough

## HuggingFace
DuoNeural/RMSN-260M-ArnoldTongue-Omega59-ODD-200k

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
