"""
rmsn_thermo_sft.py -- T-RMSN Reasoning SFT (4 Laws of Thermodynamics)
Fine-tunes T-RMSN on DuoNeural/cdm-reasoning-traces-v4
DuoNeural Lab | Jesse, Archon, Aura✨ | Nov 2026
"""

import sys, math, time, json, os, argparse
from pathlib import Path
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, '/workspace')
from rmsn_thermo_core import ThermodynamicResonantMetriplecticSheafLM

def ts():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log(msg):
    print(f"[{ts()}] {msg}", flush=True)

class ReasoningTraceDataset(Dataset):
    def __init__(self, jsonl_path, tokenizer, max_len=512, only_verified=True):
        self.examples = []
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if only_verified and not r.get("verified", True):
                    continue
                text = f"Q: {r['prompt']}\n\nA: {r['thinking_trace']}\n\n#### {r['answer']}"
                tokens = tokenizer.encode(text, return_tensors="pt")[0]
                if len(tokens) > max_len:
                    tokens = tokens[:max_len]
                if len(tokens) > 8:
                    self.examples.append(tokens)
        log(f"Dataset: {len(self.examples)} verified reasoning traces loaded")

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]

def collate_fn(batch):
    max_len = max(len(t) for t in batch)
    padded = torch.full((len(batch), max_len), 0, dtype=torch.long)
    for i, t in enumerate(batch):
        padded[i, :len(t)] = t
    x = padded[:, :-1]
    y = padded[:, 1:]
    return x, y

def main():
    p = argparse.ArgumentParser(description="T-RMSN SFT on reasoning traces")
    p.add_argument("--ckpt",         default="/workspace/rmsn_project/t_rmsn_d1024_d16_100k/ckpt_best.pt")
    p.add_argument("--data",         default="/workspace/rmsn_project/cdm_reasoning_traces_v4_hard.jsonl")
    p.add_argument("--out-dir",      default="/workspace/rmsn_project/t_rmsn_sft_5k")
    p.add_argument("--total-steps",  type=int, default=5000)
    p.add_argument("--warmup",       type=int, default=200)
    p.add_argument("--lr",           type=float, default=2e-5)
    p.add_argument("--batch",        type=int, default=2)
    p.add_argument("--seq-len",      type=int, default=512)
    p.add_argument("--save-every",   type=int, default=2500)
    p.add_argument("--log-every",    type=int, default=50)
    p.add_argument("--grad-clip",    type=float, default=1.0)
    p.add_argument("--only-verified", action="store_true", default=True)
    args = p.parse_args()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    Path(args.out_dir).mkdir(parents=True, exist_ok=True)

    log(f"T-RMSN SFT (4 Laws) — DuoNeural Lab")
    log(f"ckpt={args.ckpt} data={args.data}")

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        "HuggingFaceTB/cosmo2-tokenizer",
        cache_dir="/workspace/hf_cache", local_files_only=True
    )
    log(f"Tokenizer: vocab={len(tokenizer)}")

    ckpt = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    model_state = ckpt.get("model_state", ckpt.get("model", ckpt))
    dim   = ckpt.get("dim", 1024)
    depth = ckpt.get("depth", 16)
    slots = ckpt.get("slots", 64)
    vocab = ckpt.get("vocab", 49152)

    model = ThermodynamicResonantMetriplecticSheafLM(
        vocab_size=vocab, dim=dim, depth=depth, num_slots=slots
    ).to(device)
    clean_sd = {k.replace('module.', ''): v for k, v in model_state.items()}
    model.load_state_dict(clean_sd, strict=False)
    n_params = sum(p.numel() for p in model.parameters())
    log(f"Model: {n_params/1e6:.2f}M params (dim={dim} depth={depth} slots={slots})")

    dataset = ReasoningTraceDataset(args.data, tokenizer, args.seq_len, args.only_verified)
    loader = DataLoader(dataset, batch_size=args.batch, shuffle=True,
                        collate_fn=collate_fn, drop_last=True)
    loader_iter = iter(loader)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    best_loss = float("inf")
    t0 = time.time()
    model.train()

    log(f"T-RMSN SFT STARTED: {len(dataset)} traces | {args.total_steps} steps | lr={args.lr}")

    for step in range(1, args.total_steps + 1):
        if step <= args.warmup:
            lr = args.lr * step / args.warmup
        else:
            progress = (step - args.warmup) / (args.total_steps - args.warmup)
            lr = args.lr * max(0.1, 0.5 * (1 + math.cos(math.pi * progress)))
        for pg in optimizer.param_groups:
            pg["lr"] = lr

        try:
            x, y = next(loader_iter)
        except StopIteration:
            loader_iter = iter(loader)
            x, y = next(loader_iter)

        x, y = x.to(device), y.to(device)

        logits = model(x)
        loss = F.cross_entropy(logits.reshape(-1, vocab), y.reshape(-1), ignore_index=0)

        optimizer.zero_grad()
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
        optimizer.step()

        if step % args.log_every == 0 or step == 1:
            elapsed = time.time() - t0
            tps = step * args.batch * (args.seq_len - 1) / elapsed
            eta = (args.total_steps - step) * elapsed / step / 3600
            log(f"step={step}/{args.total_steps} loss={loss.item():.4f} gnorm={grad_norm:.3f} "
                f"lr={lr:.2e} tps={tps:.0f} ETA={eta:.2f}h")

        if step % args.save_every == 0:
            path = Path(args.out_dir) / f"t_rmsn_sft_step{step:06d}.pt"
            torch.save({
                "model_state": model.state_dict(),
                "step": step,
                "loss": loss.item(),
                "args": {"dim": dim, "depth": depth, "slots": slots, "vocab": vocab},
            }, path)
            log(f"SAVED: {path}")
            if loss.item() < best_loss:
                best_loss = loss.item()
                best_path = Path(args.out_dir) / "t_rmsn_sft_best.pt"
                torch.save({"model_state": model.state_dict(), "step": step,
                            "loss": best_loss, "args": {"dim": dim, "depth": depth,
                            "slots": slots, "vocab": vocab}}, best_path)
                log(f"BEST: {best_path} (loss={best_loss:.4f})")

    log(f"T-RMSN SFT COMPLETE — best_loss={best_loss:.4f}")

if __name__ == "__main__":
    main()
