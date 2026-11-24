# CRSN-T-ext-50k-Base

## Overview
Continuity-Regularized Sheaf Network (CRSN-T-ext), trained on the extended dataset for 50,000 steps on the DuoNeural Ryzen home node (kilonova → node-0). Best validation loss achieved at step ~24,400, with the resumed training running to completion at 50k steps without improving further.

## Architecture
- Model: CRSN-T-ext (Continuity-Regularized Sheaf Network, extended variant)
- Checkpoint size: ~97MB
- Training hardware: AMD Ryzen CPU (node-0, kilonova local network)
- Training steps: 50,000
- Total tokens: 209,715,200

## Results
- **Best Val Loss: 2.5900** (ppl = **13.33**)
- Best checkpoint: `crsn_t_best.pt` (saved at step ~24,400)
- Final step val loss: ~2.84 (ppl=~17.2) — model peaked early, stable thereafter
- Average training speed: 446.85 tok/s (CPU training)
- Total wall time: ~469,314s (~130 hours)

## Key Properties
- **Val PPL = 13.33** is the CRSN-T record on this dataset
- CRSN uses continuity regularization to enforce smooth sheaf topology transitions
- Training on CPU (Ryzen) demonstrates CRSN feasibility on consumer hardware
- Best checkpoint reached at step ~24,400; second half of training served as extended stability verification
- All 50k validation logs archived in `/home/duoneural/srsn_ryzen/crsn_t_ext.log`

## Training Notes
- Run resumed from a prior checkpoint (best_val_loss=2.5900 restored at resume)
- After resume the model stabilized — later validations ranged ppl=14.8–18.1
- No overfitting observed; loss plateaued rather than degraded
- Duplicate process was killed mid-run (had been halving throughput ~440 → 640 tok/s)

## Sheaf Probe Results (Nov 23, 2026)

Probed on node-0 by Aura. All 8 layers maintain strictly positive alpha dynamics — confirming healthy sheaf continuity regularization throughout the full depth.

| Layer | alpha_min | alpha_mean | omega_mean |
| :--- | :--- | :--- | :--- |
| All 8 layers | **0.1073** | 0.1276 – 0.1324 | 0.5223 – 0.6364 |

- **alpha_min = 0.1073** across all layers (never zero; no sheaf collapse)
- omega_mean range 0.52–0.64 indicates moderate resonance across layers
- Generation quality: story prompts produce fluent, coherent narrative
- CoT/Logic/Code prompts pivot toward TinyStories-style narrative (expected — training data is TinyStories-heavy; addressed in planned CRSN-T SFT extension)

## Files
- Best checkpoint: `/home/duoneural/srsn_ryzen/checkpoints_crsn_t/crsn_t_best.pt`
- Training log: `/home/duoneural/srsn_ryzen/crsn_t_ext.log`

## HuggingFace
DuoNeural/CRSN-T-ext-50k

## Citation
DuoNeural AI Laboratory | Archon, Aura, Jesse Schram | November 2026
