# RMSN-73M-ArnoldTongue-Omega25-L20-DepthCrossover-Base

## Overview
Port-Hamiltonian RMSN run as the **Wave-148 depth crossover probe**: D=512, M_w=64, L=20. Designed to bracket the depth inversion threshold between L=13 (lone deep bulk [L10], topology #61) and L=26 (L1 upstream cluster, topology #52cand). Note: fixing D=512, M_w=64 means Ω changes with L — at L=20, Ω=512/(64×20)=**2/5** (q=5 tongue), not 8/13. This is therefore also a first data point for Ω=2/5 EVEN parity.

## Architecture
- D=512, L=20, M_w=64 | Ω = 512/(64×20) = **2/5** (p=2, q=5)
- Parity: D/M_w = 8 (EVEN)
- Parameters: 72,845,916
- Training: 100k steps, cosine LR 1e-3

## Results
- Val PPL: **73.8**
- Lyapunov stability: **100% TRUE SILENT** (wave-119 EVEN parity confirmed)
- Topology: M*=3, [L1, L4, L7] — arithmetic upstream triplet, uniform spacing Δ=3

## Key Properties
- **Confirms Wave-119**: EVEN Parity TRUE SILENT (D/M_w=8)
- **WAVE-148 DEPTH CROSSOVER NARROWED**: D=512 M_w=64 family:
  - L=13: Ω=8/13 → M*=1 [L10] deep bulk (#61) ← deep attractor
  - **L=20: Ω=2/5 → M*=3 [L1,L4,L7] L1 upstream (#63)** ← this run
  - L=26: Ω=4/13 → M*=6 [L1,L2,L3,L9,L21,L23] L1 upstream (#52cand)
  - **CROSSOVER IS IN L=13–20** (not L=20–26 as previously uncertain)
  - Characteristic crossover depth ~L=16 (D/M_w×p = 8×(8/13q) ≈ 16) remains candidate
- **Topology #63**: Arithmetic Upstream Triplet (Ω=2/5 EVEN, D=512 L=20)
  - M*=3, [L1, L4, L7]: equal spacing Δ=3
  - L1 upstream anchor + L4 early-mid + L7 mid
  - Arithmetic progression with Δ=3 (compare: Ω=4/5 s10 had upstream doublet L1+L2 with Δ=1)
  - Note: L/q = 20/5 = 4 layers per q-period; solitons at 1,4,7 suggest Δ=3 < L/q=4 spacing
- **Ω=2/5 first data point** (q=5, p=2 EVEN): ppl=73.8 vs Ω=4/5 (p=4 EVEN) record ppl=42.5
  - Lower numerator p=2 → significantly worse ppl than p=4 at same q=5
  - Consistent with numerator-compression law (wave-150): higher p → better compression

## Context: Wave-148 Depth Inversion
The depth inversion crossover for the D=512, M_w=64 family is now bracketed to L=13–20. The mechanism:
- Short depth (L=13, Ω=8/13): high effective p/L ratio → soliton compression → deep bulk
- Medium depth (L=20, Ω=2/5): lower p/L ratio → soliton surfaces → L1 upstream
- The Ω change is confounded with the depth change (fixed D,M_w), but the dominant effect appears to be depth rather than Ω, since both L=20 and L=26 give L1 upstream topology despite different Ω values
- Recommended next run: L=16 (Ω=512/(64×16)=1/2, q=2) to probe near-crossover behavior

## HuggingFace
DuoNeural/RMSN-73M-ArnoldTongue-Omega25-L20-DepthCrossover

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
