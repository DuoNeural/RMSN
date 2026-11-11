#!/usr/bin/env python3
import sys, os, time, math, json, torch
import torch.nn.functional as F
from transformers import AutoTokenizer

sys.path.insert(0, '/workspace')
from rmsn_core import ResonantMetriplecticSheafLM

DEVICE = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

def eval_checkpoint(ckpt_path, label):
    print('=' * 70)
    print(f'Evaluating: {label}')
    print(f'Path: {ckpt_path}')
    print('=' * 70)
    
    if not os.path.exists(ckpt_path):
        print(f'Error: {ckpt_path} not found!')
        return None
        
    raw = torch.load(ckpt_path, map_location='cpu', weights_only=False)
    args = raw.get('args', {})
    dim = args.get('dim', 2048)
    depth = args.get('depth', 16)
    slots = args.get('slots', 64)
    vocab = args.get('vocab', 49152)
    
    print(f'Architecture: D={dim}, L={depth}, M_w={slots}, vocab={vocab}')
    model = ResonantMetriplecticSheafLM(vocab_size=vocab, dim=dim, depth=depth, num_slots=slots).to(DEVICE)
    
    sd = raw.get('model', raw)
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
        
    return {
        'model': label,
        'dim': dim,
        'wiki_loss': mean_wiki_loss,
        'wiki_ppl': wiki_ppl,
        'cot_loss': mean_cot_loss,
        'cot_ppl': cot_ppl
    }

if __name__ == '__main__':
    res = eval_checkpoint('/workspace/rmsn_project/d2048_s1/rmsn_best.pt', 'RMSN-655M (D=2048 seed1)')
    with open('/workspace/eval_d2048_results.json', 'w') as f:
        json.dump(res, f, indent=2)
    print('[DONE] Results saved to /workspace/eval_d2048_results.json')
