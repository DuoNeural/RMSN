#!/usr/bin/env python3
"""
Generalized sheaf probe for percolation experiments (D=944, Kramers, etc.)
Archon, DuoNeural Lab | Nov 09 2026
Args: --dim DIM --ckpt CKPT_PATH --gpu GPU_ID --out OUT_JSON --name LABEL
"""
import os, sys, math, json, argparse, torch, torch.nn.functional as F
sys.path.insert(0, '/workspace')
from rmsn_core import RMSNConfig, RMSNForCausalLM
from transformers import AutoTokenizer

p = argparse.ArgumentParser()
p.add_argument('--dim',  type=int, required=True)
p.add_argument('--depth', type=int, default=16)
p.add_argument('--slots', type=int, default=64)
p.add_argument('--ckpt', required=True)
p.add_argument('--gpu',  type=int, default=0)
p.add_argument('--out',  default=None)
p.add_argument('--name', default='unknown')
args = p.parse_args()

device = torch.device(f'cuda:{args.gpu}')
print(f"\n{'='*70}")
print(f"SHEAF PROBE: {args.name} | dim={args.dim} depth={args.depth} slots={args.slots}")
print(f"Checkpoint: {args.ckpt} | Device: {device}")
print(f"{'='*70}\n")

config = RMSNConfig(vocab_size=49152, hidden_dim=args.dim, num_layers=args.depth,
                    num_workspace_slots=args.slots, max_seq_len=512)
model = RMSNForCausalLM(config).to(device)

raw = torch.load(args.ckpt, map_location='cpu', weights_only=False)
stored_lyap = None
if isinstance(raw, dict):
    stored_lyap = raw.get('val_lyap') or raw.get('max_lyapunov') or raw.get('lyap')
    sd = raw.get('model_state', raw.get('model', raw.get('state_dict', raw)))
else:
    sd = raw
clean_sd = {(k[6:] if k.startswith('model.') else k): v for k,v in sd.items()}
model.model.load_state_dict(clean_sd, strict=False)
model.eval()
print(f"Loaded. val_lyap={stored_lyap:.4f}" if stored_lyap else f"Loaded. val_lyap=N/A")
print(f"Params: {sum(p.numel() for p in model.parameters()):,}\n")

tok = AutoTokenizer.from_pretrained('HuggingFaceTB/cosmo2-tokenizer')
prompts = [
    'Let S be the set of primes. Assume S is finite. Let P = p1*p2*...*pn + 1.',
    'The ancient library was carved into the subterranean obsidian cliffs.',
    '((((([[[[[{{{{{ A -> B -> C -> D -> E }}}}}]]]]])))))',
    'Once upon a time, Lily found a small cat near the old oak tree.',
    'The gradient descent algorithm minimizes the loss function iteratively.',
]

captured = []
def make_hook(l):
    def hook(mod, inp, out):
        x = inp[0]
        u = mod.write_proj(x)
        aff = torch.einsum('bnd,md->bnm', u, mod.workspace_slots) / math.sqrt(mod.slot_dim)
        lv = F.softplus(mod.interaction_matrix)
        inh = torch.einsum('bnm,mk->bnk', aff, lv)
        bw = F.softmax(aff - 0.1*inh, dim=-1)
        captured.append((l, bw.detach().cpu()))
    return hook

hooks = [layer.workspace.register_forward_hook(make_hook(i))
         for i, layer in enumerate(model.model.layers)]

# accumulate per-layer PR over all prompts
layer_pr_sum = {}
layer_pr_count = {}

for prompt in prompts:
    tokens = tok.encode(prompt, return_tensors='pt').to(device)
    captured.clear()
    with torch.no_grad():
        _ = model(tokens)
    for l_idx, bw in captured:
        sp = bw.mean(dim=(0,1))
        pr = 1.0 / torch.sum(sp**2).item()
        layer_pr_sum[l_idx] = layer_pr_sum.get(l_idx, 0.0) + pr
        layer_pr_count[l_idx] = layer_pr_count.get(l_idx, 0) + 1

for h in hooks: h.remove()

print(f"{'Layer':>6}  {'PR (avg)':>9}  {'Soliton?':>10}")
print("-"*35)
results = {}
soliton_layers = []
SOLITON_THRESHOLD = 6.0

for l in sorted(layer_pr_sum):
    avg_pr = layer_pr_sum[l] / layer_pr_count[l]
    is_sol = avg_pr < SOLITON_THRESHOLD
    if is_sol:
        soliton_layers.append(l)
    results[l] = {'pr': round(avg_pr, 3), 'soliton': is_sol}
    flag = '  <-- SOLITON' if is_sol else ''
    print(f"  L{l:02d}   {avg_pr:9.3f}  {'YES' if is_sol else 'no':>10}{flag}")

print(f"\nSoliton layers: {soliton_layers}")
if soliton_layers:
    if min(soliton_layers) <= 3:
        stype = 'Upstream'
    elif min(soliton_layers) <= 6:
        stype = 'Near-Upstream'
    elif min(soliton_layers) <= 10:
        stype = 'Internal Bulk'
    elif min(soliton_layers) >= 13:
        stype = 'Terminal Boundary'
    else:
        stype = 'Deep Internal'
    print(f"Soliton type: {stype} (L={min(soliton_layers)})")
else:
    stype = 'None / Multi-Soliton'
    print("No concentrated soliton detected (Multi-Soliton or No Soliton)")

summary = {
    'name': args.name,
    'dim': args.dim,
    'ckpt': args.ckpt,
    'stored_lyap': stored_lyap,
    'soliton_layers': soliton_layers,
    'soliton_type': stype,
    'layer_results': results,
}

if args.out:
    with open(args.out, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved: {args.out}")

print(f"\n{'='*70}")
print(f"RESULT: {args.name} | Soliton: {stype} | layers={soliton_layers}")
print(f"{'='*70}\n")
