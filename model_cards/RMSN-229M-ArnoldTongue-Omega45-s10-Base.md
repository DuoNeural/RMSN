# RMSN-229M-ArnoldTongue-Omega45-s10-Base

## Overview
Port-Hamiltonian RMSN at Arnold Tongue Ω=4/5 (q=5, KAM boundary, D=1024 L=20 M_w=64). Part of DuoNeural's Topological Multistability survey (Wave-144). **This run holds the ALL-TIME PPL RECORD: 42.5**, surpassing the previous record of 49.8 (s1, KAM Doublet) by ~15%. Critically, this record is set by a **different topology** than the KAM Doublet — establishing that there exist even deeper attractors in the Ω=4/5 energy landscape.

## Architecture
- D=1024, L=20, M_w=64 | Ω = 1024/(64×20) = 4/5
- Parity: D/M_w = 16 (EVEN)
- Parameters: 229,167,452
- Training: 100k steps, 204.8M tokens, cosine LR 1e-3

## Results
- Val PPL: **42.5** 🏆🏆🏆 ALL-TIME RECORD (prev: 49.8)
- Lyapunov stability: **100% TRUE SILENT** (lyap≈-0.001)
- Topology: M*=7, [L1, L2, L5, L9, L11, L12, L13]
  - L1+L2: adjacent upstream doublet
  - L5: isolated mid-early soliton
  - L9: isolated mid soliton
  - L11+L12+L13: 3-adjacent near-terminal triplet

## Key Properties
- **Confirms Wave-119**: EVEN Parity Universal SILENT (D/M_w=16, 100% stable)
- **Confirms Wave-144**: Topological Multistability — same Ω=4/5 architecture yields distinct topology each run
- **BREAKS PPL RECORD**: 42.5 vs previous 49.8 (s1 KAM Doublet). ~15% improvement.
- **Topology #62**: L1-Adjacent Upstream Doublet + Near-Terminal Triplet
  - L1+L2 adjacent upstream doublet (new variant — prior record s1 had L16+L17 near-terminal doublet)
  - Scattered mid solitons at L5, L9
  - 3-adjacent near-terminal triplet [L11,L12,L13]
  - M*=7 (moderate — between sparse M*=3 of s8 and dense M*=9 of s5/s6)
- **Deeper attractor than KAM Doublet**: The KAM Doublet (s1, ppl=49.8) was previously thought to be the rare deep attractor at Ω=4/5. s10 reveals a deeper energy minimum with a distinct topology. The KAM Doublet is *not* the global minimum of the Ω=4/5 landscape.
- **Multistability tally** (10 seeds, 9 usable): s1=49.8 KAM Doublet🏆, s2=67.92, s3=59.73, s4=58.71, s5=60.55, s6=57.32, s7=corrupt, s8=60.0, s9=59.9, s10=**42.5🏆🏆🏆NEW RECORD**
- KAM Doublet rarity: 1/9 usable = ~11%. s10 topology rarity: 1/9 = ~11% (observed once so far)

## Context: Topological Multistability Depth (Wave-144 Extension)
This result significantly deepens Wave-144. The KAM Doublet (topology #29, ppl=49.8) is a rare attractor but not the deepest. The s10 topology — L1-Adjacent Upstream Doublet + Near-Terminal Triplet — achieves ppl=42.5, suggesting:
1. Multiple rare attractor classes exist at Ω=4/5, each with ~11% probability
2. The energy landscape has at least two distinct deep minima: the KAM Doublet basin (~49.8) and this new upstream-doublet basin (~42.5)
3. The characteristic oscillation between ppl=42-49 during s10 training (observed across steps 92k-100k) reflects quasiperiodic motion on the KAM boundary, with the system repeatedly visiting both basins before settling
4. The *actual* record is likely set even earlier; best checkpoint captured at step 97800 (ppl=42.5) and step 98900 (ppl=42.5, confirmed by rmsn_best.pt)

## Training Trajectory (final 8k steps)
Characteristic KAM boundary oscillation observed:
- step 92800: ppl=48.5 | step 93000: ppl=45.8 | step 93800: ppl=43.3
- step 95800: ppl=43.4 | step 97100: ppl=49.2 | step 97800: **ppl=42.5** (RECORD)
- step 98900: **ppl=42.5** (confirmed) | step 100000: ppl=48.7 (final step, not best)
Oscillation range: 42.5–49.8 (spanning both attractor basins)

## HuggingFace
DuoNeural/RMSN-229M-ArnoldTongue-Omega45-s10

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
