#!/usr/bin/env python3
"""
generate.py -- Production Autoregressive Text Generation for RMSN
DuoNeural AI Laboratory | Jesse Caldwell, Archon, Aura✨ | Nov 2026

Usage:
  python generate.py --checkpoint /path/to/checkpoint.pt --prompt "Once upon a time"
  python generate.py --checkpoint /workspace/rmsn_project/scale_300m/step50000.pt --prompt "The second law of thermodynamics"
"""

import sys
import os
import argparse
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer

from rmsn_core import ResonantMetriplecticSheafLM, RMSNConfig, RMSNForCausalLM


def parse_args():
    parser = argparse.ArgumentParser(description="RMSN Text Generation Engine")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to .pt model checkpoint")
    parser.add_argument("--prompt", type=str, default="The fundamental law of thermodynamics states", help="Input text prompt")
    parser.add_argument("--max_new_tokens", type=int, default=64, help="Tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    parser.add_argument("--top_k", type=int, default=40, help="Top-k sampling threshold")
    parser.add_argument("--top_p", type=float, default=0.9, help="Nucleus sampling threshold")
    parser.add_argument("--tokenizer", type=str, default="HuggingFaceTB/cosmo2-tokenizer", help="HuggingFace tokenizer ID")
    parser.add_argument("--dim", type=int, default=1024, help="Model hidden dimension (if not in ckpt)")
    parser.add_argument("--depth", type=int, default=16, help="Model layer depth (if not in ckpt)")
    parser.add_argument("--slots", type=int, default=64, help="Workspace slots")
    parser.add_argument("--vocab_size", type=int, default=49152, help="Vocabulary size")
    parser.add_argument("--device", type=str, default=None, help="Device (cuda / cpu)")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"[RMSN-Inference] Target device: {device}")
    print(f"[RMSN-Inference] Loading tokenizer: {args.tokenizer}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    except Exception as e:
        print(f"[RMSN-Inference] Warning: could not load {args.tokenizer}: {e}")
        print("[RMSN-Inference] Falling back to gpt2 tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained("gpt2")

    vocab_size = getattr(tokenizer, "vocab_size", args.vocab_size)
    dim = args.dim
    depth = args.depth
    slots = args.slots

    # Load checkpoint if provided
    state_dict = None
    if args.checkpoint and os.path.exists(args.checkpoint):
        print(f"[RMSN-Inference] Loading checkpoint: {args.checkpoint}")
        raw = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
        if isinstance(raw, dict):
            if "model" in raw:
                state_dict = raw["model"]
            elif "state_dict" in raw:
                state_dict = raw["state_dict"]
            else:
                state_dict = raw
        else:
            state_dict = raw

        # Infer config from checkpoint shapes
        if "token_embed.weight" in state_dict:
            vocab_size, dim = state_dict["token_embed.weight"].shape
        elif "model.token_embed.weight" in state_dict:
            vocab_size, dim = state_dict["model.token_embed.weight"].shape

        layer_keys = [k for k in state_dict.keys() if "layers." in k]
        if layer_keys:
            layer_indices = [int(k.split("layers.")[1].split(".")[0]) for k in layer_keys]
            depth = max(layer_indices) + 1

        print(f"[RMSN-Inference] Inferred config from checkpoint: dim={dim}, depth={depth}, vocab={vocab_size}")

    # Build model
    config = RMSNConfig(
        vocab_size=vocab_size,
        hidden_dim=dim,
        num_layers=depth,
        num_workspace_slots=slots,
    )
    model = RMSNForCausalLM(config).to(device)

    if state_dict is not None:
        # Strip model prefix if saved under wrapper
        clean_sd = {}
        for k, v in state_dict.items():
            if k.startswith("model."):
                clean_sd[k[6:]] = v
            else:
                clean_sd[k] = v
        try:
            model.model.load_state_dict(clean_sd, strict=False)
            print("[RMSN-Inference] Checkpoint state loaded successfully!")
        except Exception as e:
            print(f"[RMSN-Inference] Note during load: {e}")

    model.eval()

    # Encode prompt
    input_ids = tokenizer.encode(args.prompt, return_tensors="pt").to(device)
    print(f"\n[RMSN-Inference] Prompt: \"{args.prompt}\" ({input_ids.shape[1]} tokens)")
    print(f"[RMSN-Inference] Generating {args.max_new_tokens} tokens (T={args.temperature}, top_k={args.top_k}, top_p={args.top_p})...\n")

    # Generate
    with torch.no_grad():
        out_ids = model.generate(
            input_ids=input_ids,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated_text = tokenizer.decode(out_ids[0].tolist(), skip_special_tokens=True)
    print("=" * 60)
    print(generated_text)
    print("=" * 60)
    print("\n[RMSN-Inference] Generation complete.")


if __name__ == "__main__":
    main()
