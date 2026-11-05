#!/usr/bin/env python3
"""
rmsn_train_lm.py -- RMSN Language Model Full Test Run
DuoNeural Lab | Archon | 2026-11-04

Real language modeling on wikitext-103. Trains RMSN-Small:
  D=1024, L=16, M_w=64, vocab=49152 (cosmo2)
  ~260M params. Runs on RTX 4080 Super (p19285).

This is NOT the PoC synthetic benchmark — this is actual text learning.
Target: 5000 steps on real text, tracking perplexity, Lyapunov stability, DHP.
"""

import sys, math, time, json, os, argparse
from pathlib import Path
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, "/workspace/rmsn_project")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def ts():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("[%Y-%m-%dT%H:%M:%SZ]")

# ─────────────────────────────────────────────────────────────
# Data
# ─────────────────────────────────────────────────────────────

def download_wikitext(cache_dir="/workspace/rmsn_data"):
    """Download wikitext-103 raw text directly — no HF datasets needed."""
    import urllib.request, gzip
    Path(cache_dir).mkdir(exist_ok=True)
    out = Path(cache_dir) / "wiki103_train.txt"
    if out.exists() and out.stat().st_size > 1_000_000:
        print(f"{ts()} wikitext cached at {out} ({out.stat().st_size/1e6:.1f}MB)")
        return str(out)
    # pull from HF datasets direct download
    url = "https://huggingface.co/datasets/Salesforce/wikitext/resolve/main/wikitext-103-raw-v1/train-00000-of-00002.parquet"
    fallback = "https://raw.githubusercontent.com/pytorch/examples/main/word_language_model/data/wikitext-2/train.txt"
    print(f"{ts()} Downloading wikitext-103 ...")
    try:
        import io
        import pandas as pd
        resp = urllib.request.urlopen(url, timeout=120)
        df = pd.read_parquet(io.BytesIO(resp.read()))
        text = "\n".join(df["text"].dropna().tolist())
        out.write_text(text, encoding="utf-8")
        print(f"{ts()} Downloaded {out.stat().st_size/1e6:.1f}MB")
    except Exception as e:
        print(f"{ts()} parquet failed ({e}), trying plain text fallback...")
        urllib.request.urlretrieve(fallback, out)
        print(f"{ts()} Downloaded fallback {out.stat().st_size/1e6:.1f}MB")
    return str(out)


def tokenize(text_path: str, tokenizer_name: str, max_tokens: int, cache_dir: str):
    """Tokenize text, cache the tensor."""
    cache_path = Path(cache_dir) / f"tokens_{max_tokens//1000}k.pt"
    if cache_path.exists():
        print(f"{ts()} Loading cached tokens from {cache_path}")
        return torch.load(cache_path)
    print(f"{ts()} Tokenizing with {tokenizer_name} ...")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(tokenizer_name, cache_dir=cache_dir + "/hf")
    text = Path(text_path).read_text(encoding="utf-8", errors="ignore")[:50_000_000]  # 50MB max
    ids = tok.encode(text, add_special_tokens=False)
    ids = torch.tensor(ids[:max_tokens], dtype=torch.long)
    torch.save(ids, cache_path)
    print(f"{ts()} Tokenized: {len(ids):,} tokens → {cache_path}")
    return ids


class SlideWindowDataset(Dataset):
    """Sliding window over a flat token tensor."""
    def __init__(self, tokens: torch.Tensor, seq_len: int, stride: int):
        self.tokens = tokens
        self.seq_len = seq_len
        self.stride = stride
        self.n = max(0, (len(tokens) - seq_len - 1) // stride)

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        s = i * self.stride
        x = self.tokens[s : s + self.seq_len]
        y = self.tokens[s + 1 : s + self.seq_len + 1]
        return x, y


# ─────────────────────────────────────────────────────────────
# LR schedule
# ─────────────────────────────────────────────────────────────

def cosine_lr(step, warmup, total, lr_max, lr_min=1e-5):
    if step < warmup:
        return lr_max * step / warmup
    t = (step - warmup) / (total - warmup)
    return lr_min + 0.5 * (lr_max - lr_min) * (1 + math.cos(math.pi * t))


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dim",       type=int, default=1024)
    p.add_argument("--depth",     type=int, default=16)
    p.add_argument("--slots",     type=int, default=64)
    p.add_argument("--vocab",     type=int, default=49152)
    p.add_argument("--seq-len",   type=int, default=512)
    p.add_argument("--batch",     type=int, default=4)
    p.add_argument("--total-steps", type=int, default=5000)
    p.add_argument("--warmup",    type=int, default=200)
    p.add_argument("--lr",        type=float, default=3e-4)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--save-every", type=int, default=500)
    p.add_argument("--log-every",  type=int, default=50)
    p.add_argument("--out-dir",   default="/workspace/rmsn_project/lm_run")
    p.add_argument("--data-dir",  default="/workspace/rmsn_data")
    p.add_argument("--tokenizer", default="HuggingFaceTB/cosmo2-tokenizer")
    p.add_argument("--resume",    default=None)
    p.add_argument("--max-tokens", type=int, default=20_000_000)
    args = p.parse_args()

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    Path(args.data_dir).mkdir(parents=True, exist_ok=True)

    LOG = Path(args.out_dir) / "train.log"

    def log(msg):
        line = f"{ts()} {msg}"
        print(line, flush=True)
        with open(LOG, "a") as f:
            f.write(line + "\n")

    log("=" * 70)
    log("RMSN Language Model Training — DuoNeural Lab")
    log(f"D={args.dim} L={args.depth} M_w={args.slots} vocab={args.vocab}")
    log(f"B={args.batch} N={args.seq_len} steps={args.total_steps}")
    log(f"Device: {DEVICE}")
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        log(f"GPU: {props.name} | VRAM: {props.total_memory/1024**3:.1f}GB")
    log("=" * 70)

    # ── data ──────────────────────────────────────────────────────
    log("Preparing dataset...")
    text_path = download_wikitext(args.data_dir)
    tokens = tokenize(text_path, args.tokenizer, args.max_tokens, args.data_dir)
    n_tokens = len(tokens)
    log(f"Dataset: {n_tokens:,} tokens")

    split = int(0.95 * n_tokens)
    train_tokens = tokens[:split]
    val_tokens   = tokens[split:]

    stride = args.seq_len // 2  # 50% overlap
    train_ds = SlideWindowDataset(train_tokens, args.seq_len, stride)
    val_ds   = SlideWindowDataset(val_tokens,   args.seq_len, stride)
    log(f"Train examples: {len(train_ds):,} | Val examples: {len(val_ds):,}")

    train_dl = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                          num_workers=2, pin_memory=True)
    val_dl   = DataLoader(val_ds,   batch_size=args.batch, shuffle=False,
                          num_workers=1, pin_memory=True)
    train_iter = iter(train_dl)

    # ── model ─────────────────────────────────────────────────────
    from rmsn_core import ResonantMetriplecticSheafLM

    model = ResonantMetriplecticSheafLM(
        vocab_size=args.vocab,
        dim=args.dim,
        depth=args.depth,
        num_slots=args.slots,
    ).to(DEVICE)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"Model params: {n_params/1e6:.2f}M")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01,
                             betas=(0.9, 0.95))

    start_step = 0
    best_val_loss = float("inf")

    if args.resume and Path(args.resume).exists():
        log(f"Resuming from {args.resume}")
        ckpt = torch.load(args.resume, map_location=DEVICE)
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["opt"])
        start_step = ckpt.get("step", 0)
        best_val_loss = ckpt.get("best_val_loss", float("inf"))
        log(f"Resumed at step {start_step}, best_val={best_val_loss:.4f}")

    # ── training loop ─────────────────────────────────────────────
    log("Starting training...")
    model.train()
    t_start = time.time()
    tokens_seen = 0
    step_losses = []
    lyapunov_hist = []

    for step in range(start_step + 1, args.total_steps + 1):
        # lr
        lr = cosine_lr(step, args.warmup, args.total_steps, args.lr)
        for g in opt.param_groups:
            g["lr"] = lr

        # batch
        try:
            x, y = next(train_iter)
        except StopIteration:
            train_iter = iter(train_dl)
            x, y = next(train_iter)
        x, y = x.to(DEVICE), y.to(DEVICE)

        # forward / backward
        t0 = time.time()
        opt.zero_grad()
        logits, telemetry = model(x, return_telemetry=True)
        loss = F.cross_entropy(logits.reshape(-1, args.vocab), y.reshape(-1))
        loss.backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
        opt.step()
        dt = time.time() - t0

        tokens_seen += args.batch * args.seq_len
        tps = (args.batch * args.seq_len) / dt
        step_losses.append(loss.item())
        lyapunov_hist.append(telemetry.get("max_lyapunov", 0.0))

        if step % args.log_every == 0 or step == 1:
            avg_loss = sum(step_losses[-args.log_every:]) / min(len(step_losses), args.log_every)
            ppl = math.exp(min(avg_loss, 20))
            lyap = telemetry.get("max_lyapunov", 0.0)
            ws_e = telemetry.get("ws_entropy", 0.0)
            elapsed = time.time() - t_start
            eta_steps = args.total_steps - step
            eta_s = eta_steps * (elapsed / max(step - start_step, 1))
            log(
                f"step={step}/{args.total_steps} loss={avg_loss:.4f} ppl={ppl:.1f} "
                f"lyap={lyap:.4f} ws_ent={ws_e:.4f} "
                f"tps={tps:.0f} lr={lr:.2e} gnorm={grad_norm:.3f} "
                f"ETA={eta_s/3600:.1f}h"
            )

        # validation + checkpoint
        if step % args.save_every == 0 or step == args.total_steps:
            model.eval()
            val_losses = []
            val_lyaps = []
            with torch.no_grad():
                for vx, vy in val_dl:
                    vx, vy = vx.to(DEVICE), vy.to(DEVICE)
                    vlogits, vtel = model(vx, return_telemetry=True)
                    vl = F.cross_entropy(vlogits.reshape(-1, args.vocab), vy.reshape(-1))
                    val_losses.append(vl.item())
                    val_lyaps.append(vtel.get("max_lyapunov", 0.0))
                    if len(val_losses) >= 100:
                        break
            val_loss = sum(val_losses) / len(val_losses)
            val_ppl  = math.exp(min(val_loss, 20))
            val_lyap = sum(val_lyaps) / len(val_lyaps)
            log(f"[VAL] step={step} val_loss={val_loss:.4f} val_ppl={val_ppl:.1f} "
                f"val_lyap={val_lyap:.4f} {'✓ STABLE' if val_lyap < 0 else '⚠ UNSTABLE'}")

            ckpt = {
                "step": step,
                "model": model.state_dict(),
                "opt": opt.state_dict(),
                "val_loss": val_loss,
                "best_val_loss": best_val_loss,
                "args": vars(args),
            }
            ckpt_path = Path(args.out_dir) / f"rmsn_lm_step{step:06d}.pt"
            torch.save(ckpt, ckpt_path)
            log(f"Saved checkpoint: {ckpt_path}")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_path = Path(args.out_dir) / "rmsn_lm_best.pt"
                torch.save(ckpt, best_path)
                log(f"New best: val_loss={val_loss:.4f}")

            model.train()

    # ── final summary ─────────────────────────────────────────────
    total_time = time.time() - t_start
    avg_tps = tokens_seen / total_time
    final_loss = step_losses[-1] if step_losses else float("nan")
    lyap_stable = sum(1 for l in lyapunov_hist[-100:] if l < 0) / min(len(lyapunov_hist), 100)

    summary = {
        "total_steps": args.total_steps,
        "tokens_seen": tokens_seen,
        "total_time_s": round(total_time),
        "avg_tps": round(avg_tps),
        "final_train_loss": round(final_loss, 4),
        "best_val_loss": round(best_val_loss, 4),
        "lyapunov_stable_pct": round(lyap_stable * 100, 1),
        "params_M": round(n_params / 1e6, 2),
    }
    out_json = Path(args.out_dir) / "summary.json"
    out_json.write_text(json.dumps(summary, indent=2))

    log("=" * 70)
    log("TRAINING COMPLETE")
    log(f"Steps:          {args.total_steps}")
    log(f"Tokens seen:    {tokens_seen:,}")
    log(f"Total time:     {total_time/3600:.2f}h")
    log(f"Avg tok/sec:    {avg_tps:.0f}")
    log(f"Best val loss:  {best_val_loss:.4f} (ppl={math.exp(min(best_val_loss,20)):.1f})")
    log(f"Lyapunov stable {lyap_stable*100:.1f}% of last 100 steps")
    log("=" * 70)
    log(f"Summary saved to {out_json}")


if __name__ == "__main__":
    main()
