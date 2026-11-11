#!/usr/bin/env python3
import sys, os, time, math, json, argparse, torch
import torch.nn.functional as F
from transformers import AutoTokenizer

sys.path.insert(0, '/workspace')
from rmsn_core import ResonantMetriplecticSheafLM

p = argparse.ArgumentParser()
p.add_argument('--ckpt', required=True)
p.add_argument('--name', default='RMSN Evaluation')
p.add_argument('--out', default='/workspace/eval_results.json')
p.add_argument('--dim', type=int, default=1792)
p.add_argument('--depth', type=int, default=16)
p.add_argument('--slots', type=int, default=64)
p.add_argument('--gpu', type=int, default=0)
args = p.parse_args()

DEVICE = torch.device(f'cuda:{args.gpu}' if torch.cuda.is_available() else 'cpu')

def eval_checkpoint(ckpt_path, label, dim, depth, slots, out_file):
    print('=' * 70)
    print(f'Evaluating: {label}')
    print(f'Path: {ckpt_path} | Device: {DEVICE}')
    print('=' * 70)
    
    if not os.path.exists(ckpt_path):
        print(f'Error: {ckpt_path} not found!')
        return None
        
    raw = torch.load(ckpt_path, map_location='cpu', weights_only=False)
    raw_args = raw.get('args', {}) if isinstance(raw, dict) else {}
    m_dim = raw_args.get('dim', dim)
    m_depth = raw_args.get('depth', depth)
    m_slots = raw_args.get('slots', slots)
    vocab = raw_args.get('vocab', 49152)
    
    print(f'Architecture: D={m_dim}, L={m_depth}, M_w={m_slots}, vocab={vocab}')
    model = ResonantMetriplecticSheafLM(vocab_size=vocab, dim=m_dim, depth=m_depth, num_slots=m_slots).to(DEVICE)
    
    sd = raw.get('model_state', raw.get('model', raw))
    clean_sd = {k[6:] if k.startswith('model.') else k: v for k, v in sd.items()}
    model.load_state_dict(clean_sd, strict=False)
    model.eval()
    
    # 1. WikiText-103 Retention
    wiki_path = '/workspace/rmsn_data/tokens_wiki103_full.pt'
    tokens = torch.load(wiki_path, map_location='cpu')
    if isinstance(tokens, dict):
        tokens = tokens.get('train', tokens.get('tokens'))
    val_tokens = tokens[-100000:].long()
    
    seq_len = 256
    batch_size = 2
    wiki_losses = []
    with torch.no_grad():
        for i in range(0, min(len(val_tokens) - seq_len - 1, 50 * batch_size * seq_len), batch_size * seq_len):
            chunks = []
            for b in range(batch_size):
                idx = i + b * seq_len
                if idx + seq_len + 1 < len(val_tokens):
                    chunks.append(val_tokens[idx : idx + seq_len + 1])
            if len(chunks) < batch_size:
                break
            batch = torch.stack(chunks).to(DEVICE)
            x, y = batch[:, :-1], batch[:, 1:]
            logits = model(x)
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
            wiki_losses.append(loss.item())
            
    mean_wiki_loss = sum(wiki_losses) / len(wiki_losses) if wiki_losses else 0.0
    wiki_ppl = math.exp(min(20, mean_wiki_loss))
    print(f'  --> WikiText-103 Test Retention: Loss={mean_wiki_loss:.4f} | PPL={wiki_ppl:.2f}')
    
    # 2. CoT Hard Traces
    cot_path = '/workspace/cdm_reasoning_traces_v4_hard.jsonl'
    cot_losses = []
    if os.path.exists(cot_path):
        tokenizer = AutoTokenizer.from_pretrained('HuggingFaceTB/cosmo2-tokenizer')
        lines = []
        with open(cot_path) as f:
            for i, line in enumerate(f):
                if i >= 80: break
                lines.append(json.loads(line))
        
        c_seq_len = 512
        c_batch_size = 2
        for b_idx in range(0, len(lines), c_batch_size):
            sub = lines[b_idx : b_idx + c_batch_size]
            batch_tokens = []
            for item in sub:
                p = item.get('prompt', '')
                t = item.get('thinking_trace', item.get('completion', ''))
                a = item.get('answer', '')
                text = f'Q: {p}\n\nA: {t}\n\n#### {a}'
                toks = tokenizer.encode(text)[:c_seq_len + 1]
                if len(toks) < c_seq_len + 1:
                    toks = toks + [tokenizer.eos_token_id or 0] * (c_seq_len + 1 - len(toks))
                batch_tokens.append(torch.tensor(toks, dtype=torch.long))
            if len(batch_tokens) == c_batch_size:
                b_tensor = torch.stack(batch_tokens).to(DEVICE)
                x, y = b_tensor[:, :-1], b_tensor[:, 1:]
                with torch.no_grad():
                    logits = model(x)
                    loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
                    cot_losses.append(loss.item())
                    
        mean_cot_loss = sum(cot_losses) / len(cot_losses) if cot_losses else 0.0
        cot_ppl = math.exp(min(20, mean_cot_loss))
        print(f'  --> CoT Hard Reasoning:        Loss={mean_cot_loss:.4f} | PPL={cot_ppl:.2f}')
    else:
        mean_cot_loss, cot_ppl = None, None
        
    res = {
        'model': label,
        'dim': m_dim,
        'wiki_loss': mean_wiki_loss,
        'wiki_ppl': wiki_ppl,
        'cot_loss': mean_cot_loss,
        'cot_ppl': cot_ppl
    }
    with open(out_file, 'w') as f:
        json.dump(res, f, indent=2)
    print(f'[DONE] Results saved to {out_file}')
    return res

if __name__ == '__main__':
    eval_checkpoint(args.ckpt, args.name, args.dim, args.depth, args.slots, args.out)
