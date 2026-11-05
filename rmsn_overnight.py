#!/usr/bin/env python3
"""
rmsn_overnight.py -- RMSN Real Training Run (Overnight)
DuoNeural Lab | Archon | 2026-11-04

Extended language modeling run. Same architecture as the PoC LM test
(so results are directly comparable) but:
  - Full wikitext-103 dataset (~103M tokens)
  - 50K steps (batch=8) → ~205M tokens seen
  - Saves checkpoints every 5K steps
  - Telegrams milestone summaries every 10K steps
  - ETA ~7 hours at current speed

Architecture (RMSN-Small):
  D=1024, L=16, M_w=64, vocab=49152 (cosmo2)
  193M params, Port-Hamiltonian + Clifford + Sheaf + Caputo + TGW + Noether

This is the run that goes in the paper.
"""
import sys, math, time, json, os, argparse, re
from pathlib import Path
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, "/workspace/rmsn_project")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TELE_ENV = Path("/root/.config/duoneural/telegram.env")

def ts():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("[%Y-%m-%dT%H:%M:%SZ]")

def tg(msg: str):
    if not TELE_ENV.exists(): return
    import urllib.request, urllib.parse
    raw = TELE_ENV.read_text()
    bot = re.search(r'BOT_TOKEN=["\']?([^\s\'"]+)', raw)
    cid = re.search(r'JESSE_CHAT_ID=["\']?([^\s\'"]+)', raw)
    if not bot or not cid: return
    data = urllib.parse.urlencode({"chat_id": cid.group(1), "text": msg}).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(
                f"https://api.telegram.org/bot{bot.group(1)}/sendMessage",
                data=data, method="POST"
            ), timeout=15
        )
    except Exception:
        pass


def download_wikitext103(cache_dir="/workspace/rmsn_data"):
    """Download full wikitext-103-raw via HF parquet (needs pyarrow)."""
    import urllib.request, io
    Path(cache_dir).mkdir(exist_ok=True)
    out = Path(cache_dir) / "wiki103_full.txt"

    if out.exists() and out.stat().st_size > 100_000_000:
        print(f"{ts()} wikitext-103 cached ({out.stat().st_size/1e6:.0f}MB)")
        return str(out)

    print(f"{ts()} Downloading wikitext-103 full (pyarrow)...")
    import pandas as pd
    base = "https://huggingface.co/datasets/Salesforce/wikitext/resolve/main/wikitext-103-raw-v1"
    parts = ["train-00000-of-00002.parquet", "train-00001-of-00002.parquet"]
    all_text = []
    for part in parts:
        url = f"{base}/{part}"
        print(f"{ts()} Downloading {part}...")
        resp = urllib.request.urlopen(url, timeout=180)
        df = pd.read_parquet(io.BytesIO(resp.read()))
        texts = df["text"].dropna().tolist()
        all_text.extend(texts)
        print(f"{ts()} Got {len(texts):,} docs from {part}")
    full = "\n\n".join(all_text)
    out.write_text(full, encoding="utf-8")
    print(f"{ts()} wikitext-103 saved: {out.stat().st_size/1e6:.0f}MB")
    return str(out)


def tokenize(text_path, tokenizer_name, cache_dir):
    cache_path = Path(cache_dir) / "tokens_wiki103_full.pt"
    if cache_path.exists():
        print(f"{ts()} Loading cached tokens {cache_path}")
        return torch.load(cache_path)
    print(f"{ts()} Tokenizing with {tokenizer_name}...")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(tokenizer_name, cache_dir=cache_dir + "/hf")
    text = Path(text_path).read_text(encoding="utf-8", errors="ignore")
    ids = tok.encode(text, add_special_tokens=False)
    ids = torch.tensor(ids, dtype=torch.long)
    torch.save(ids, cache_path)
    print(f"{ts()} Tokenized: {len(ids):,} tokens")
    return ids


class SlideWindowDataset(Dataset):
    def __init__(self, tokens, seq_len, stride):
        self.tokens = tokens
        self.seq_len = seq_len
        self.stride = stride
        self.n = max(0, (len(tokens) - seq_len - 1) // stride)
    def __len__(self): return self.n
    def __getitem__(self, i):
        s = i * self.stride
        return self.tokens[s:s+self.seq_len], self.tokens[s+1:s+self.seq_len+1]


def cosine_lr(step, warmup, total, lr_max, lr_min=1e-5):
    if step < warmup:
        return lr_max * step / max(warmup, 1)
    t = (step - warmup) / max(total - warmup, 1)
    return lr_min + 0.5 * (lr_max - lr_min) * (1 + math.cos(math.pi * t))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dim",         type=int,   default=1024)
    p.add_argument("--depth",       type=int,   default=16)
    p.add_argument("--slots",       type=int,   default=64)
    p.add_argument("--vocab",       type=int,   default=49152)
    p.add_argument("--seq-len",     type=int,   default=512)
    p.add_argument("--batch",       type=int,   default=8)
    p.add_argument("--total-steps", type=int,   default=50000)
    p.add_argument("--warmup",      type=int,   default=2000)
    p.add_argument("--lr",          type=float, default=3e-4)
    p.add_argument("--grad-clip",   type=float, default=1.0)
    p.add_argument("--save-every",  type=int,   default=5000)
    p.add_argument("--log-every",   type=int,   default=100)
    p.add_argument("--tg-every",    type=int,   default=10000)
    p.add_argument("--out-dir",     default="/workspace/rmsn_project/overnight")
    p.add_argument("--data-dir",    default="/workspace/rmsn_data")
    p.add_argument("--tokenizer",   default="HuggingFaceTB/cosmo2-tokenizer")
    p.add_argument("--resume",      default=None)
    args = p.parse_args()

    Path(args.out_dir).mkdir(parents=True, exist_ok=True)
    LOG = Path(args.out_dir) / "train.log"

    def log(msg):
        line = f"{ts()} {msg}"
        print(line, flush=True)
        with open(LOG, "a") as f: f.write(line + "\n")

    log("=" * 70)
    log("RMSN Overnight Training Run — DuoNeural Lab")
    log(f"D={args.dim} L={args.depth} M_w={args.slots} vocab={args.vocab}")
    log(f"B={args.batch} N={args.seq_len} steps={args.total_steps}")
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        log(f"GPU: {props.name} | VRAM: {props.total_memory/1024**3:.1f}GB")
    log("=" * 70)

    tg(f"🧠 RMSN Overnight Run STARTED [{ts()}]\n"
       f"D={args.dim} L={args.depth} M_w={args.slots} | {args.total_steps} steps\n"
       f"Full wikitext-103. ETA ~7 hours. We're doing this.")

    # ── data ──────────────────────────────────────────────────────
    text_path = download_wikitext103(args.data_dir)
    tokens = tokenize(text_path, args.tokenizer, args.data_dir)
    n_tokens = len(tokens)
    log(f"Dataset: {n_tokens:,} tokens ({n_tokens/1e6:.1f}M)")

    split = int(0.95 * n_tokens)
    train_tokens = tokens[:split]
    val_tokens   = tokens[split:]

    stride = args.seq_len // 2
    train_ds = SlideWindowDataset(train_tokens, args.seq_len, stride)
    val_ds   = SlideWindowDataset(val_tokens,   args.seq_len, stride)
    log(f"Train: {len(train_ds):,} examples | Val: {len(val_ds):,} examples")

    train_dl = DataLoader(train_ds, batch_size=args.batch, shuffle=True,
                          num_workers=4, pin_memory=True, persistent_workers=True)
    val_dl   = DataLoader(val_ds,   batch_size=args.batch, shuffle=False,
                          num_workers=2, pin_memory=True)
    train_iter = iter(train_dl)

    # ── model ─────────────────────────────────────────────────────
    from rmsn_core import ResonantMetriplecticSheafLM
    model = ResonantMetriplecticSheafLM(
        vocab_size=args.vocab, dim=args.dim,
        depth=args.depth, num_slots=args.slots,
    ).to(DEVICE)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log(f"Model: {n_params/1e6:.2f}M params")

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr,
                             weight_decay=0.01, betas=(0.9, 0.95))

    start_step = 0
    best_val_loss = float("inf")

    if args.resume and Path(args.resume).exists():
        log(f"Resuming from {args.resume}")
        ckpt = torch.load(args.resume, map_location=DEVICE)
        model.load_state_dict(ckpt["model"])
        opt.load_state_dict(ckpt["opt"])
        start_step = ckpt.get("step", 0)
        best_val_loss = ckpt.get("best_val_loss", float("inf"))
        log(f"Resumed at step {start_step}")

    # ── training ──────────────────────────────────────────────────
    model.train()
    t_start = time.time()
    tokens_seen = 0
    step_losses = []
    lyapunov_hist = []

    for step in range(start_step + 1, args.total_steps + 1):
        lr = cosine_lr(step, args.warmup, args.total_steps, args.lr)
        for g in opt.param_groups: g["lr"] = lr

        try:
            x, y = next(train_iter)
        except StopIteration:
            train_iter = iter(train_dl)
            x, y = next(train_iter)
        x, y = x.to(DEVICE), y.to(DEVICE)

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
            win = step_losses[-args.log_every:]
            avg_loss = sum(win) / len(win)
            ppl = math.exp(min(avg_loss, 20))
            lyap = telemetry.get("max_lyapunov", 0.0)
            elapsed = time.time() - t_start
            eta_s = (args.total_steps - step) * (elapsed / max(step - start_step, 1))
            log(f"step={step}/{args.total_steps} loss={avg_loss:.4f} ppl={ppl:.1f} "
                f"lyap={lyap:.4f} tps={tps:.0f} lr={lr:.2e} ETA={eta_s/3600:.2f}h")

        # checkpoint + validation
        if step % args.save_every == 0 or step == args.total_steps:
            model.eval()
            val_losses, val_lyaps = [], []
            with torch.no_grad():
                for vx, vy in val_dl:
                    vx, vy = vx.to(DEVICE), vy.to(DEVICE)
                    vl, vt = model(vx, return_telemetry=True)
                    vl = F.cross_entropy(vl.reshape(-1, args.vocab), vy.reshape(-1))
                    val_losses.append(vl.item())
                    val_lyaps.append(vt.get("max_lyapunov", 0.0))
                    if len(val_losses) >= 200: break
            val_loss = sum(val_losses) / len(val_losses)
            val_lyap = sum(val_lyaps) / len(val_lyaps)
            val_ppl  = math.exp(min(val_loss, 20))
            log(f"[VAL] step={step} val_loss={val_loss:.4f} val_ppl={val_ppl:.1f} "
                f"val_lyap={val_lyap:.4f} {'✓ STABLE' if val_lyap < 0 else '⚠ UNSTABLE'}")

            ckpt = {"step": step, "model": model.state_dict(), "opt": opt.state_dict(),
                    "val_loss": val_loss, "best_val_loss": best_val_loss, "args": vars(args)}
            torch.save(ckpt, Path(args.out_dir) / f"rmsn_step{step:06d}.pt")

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(ckpt, Path(args.out_dir) / "rmsn_best.pt")
                log(f"New best: val_loss={val_loss:.4f}")

            model.train()

        # telegram milestone
        if step % args.tg_every == 0:
            win = step_losses[-100:]
            avg = sum(win)/len(win)
            lyap_pct = sum(1 for l in lyapunov_hist[-1000:] if l < 0) / min(len(lyapunov_hist), 1000) * 100
            elapsed = time.time() - t_start
            eta_s = (args.total_steps - step) * (elapsed / max(step - start_step, 1))
            tg(f"📊 RMSN Overnight — step {step}/{args.total_steps}\n"
               f"train_loss={avg:.4f} val_ppl={math.exp(min(best_val_loss,20)):.1f}\n"
               f"Lyapunov stable {lyap_pct:.0f}% | ETA {eta_s/3600:.1f}h\n"
               f"tok/sec={tps:.0f}")

    # ── final ─────────────────────────────────────────────────────
    total_time = time.time() - t_start
    lyap_pct = sum(1 for l in lyapunov_hist[-1000:] if l < 0) / min(len(lyapunov_hist), 1000) * 100

    summary = {
        "total_steps": args.total_steps,
        "tokens_seen": tokens_seen,
        "total_time_h": round(total_time/3600, 2),
        "avg_tps": round(tokens_seen/total_time),
        "best_val_loss": round(best_val_loss, 4),
        "best_val_ppl": round(math.exp(min(best_val_loss, 20)), 2),
        "lyapunov_stable_pct": round(lyap_pct, 1),
        "params_M": round(n_params/1e6, 2),
        "architecture": f"D={args.dim} L={args.depth} M_w={args.slots}",
    }
    (Path(args.out_dir) / "summary.json").write_text(json.dumps(summary, indent=2))

    log("=" * 70)
    log("RMSN OVERNIGHT RUN COMPLETE")
    log(f"Time:          {total_time/3600:.2f}h")
    log(f"Tokens seen:   {tokens_seen/1e6:.1f}M")
    log(f"Best val loss: {best_val_loss:.4f} (ppl={math.exp(min(best_val_loss,20)):.1f})")
    log(f"Lyapunov stable {lyap_pct:.0f}% of last 1000 steps")
    log("=" * 70)

    tg(f"🎉 RMSN OVERNIGHT RUN COMPLETE\n"
       f"Time: {total_time/3600:.1f}h\n"
       f"Best val ppl: {math.exp(min(best_val_loss,20)):.1f}\n"
       f"Lyapunov stable: {lyap_pct:.0f}%\n"
       f"This goes in the paper. 🧠")


if __name__ == "__main__":
    main()
