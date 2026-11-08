"""
rmsn_core.py -- Resonant Metriplectic Sheaf Network (Hardened Implementation)
DuoNeural Lab | Archon + Aura (Red Team) | 2026-11-04

Design: Jesse Caldwell + Aura (Gemini 2.5 Pro Deep Research)
Red Team: Aura (7 critical bugs identified and fixed)
Implementation: Archon

Architecture summary:
  CliffordStalkBundle  -> norm-preserving Rodrigues Cl(3,0) gauge transport + sheaf shift
  MetriplecticScan     -> h_t = exp((-gamma+i*omega)*dt)*h_{t-1} + u*dt, via tl.associative_scan
  FractionalCaputoBank -> 8 log-spaced real exponential poles, channel-partitioned, parallel
  CausalTrophicGW      -> M_w=32 Lotka-Volterra workspace, strictly causal via cumsum
  Noether Readout      -> cat[Re(h), Im(h), tanh(|h|^2)] -> Linear, preserves wave phase

Bugs fixed vs original design doc:
  1. Triton: while-loop -> tl.associative_scan (register-level, no global mem reads in loop)
  2. Missing autograd.Function backward -> analytical time-reversed adjoint scan
  3. TrophicGW causal leakage -> torch.cumsum causal prefix accumulation
  4. Clifford broken half-angle cross product -> full Rodrigues on grades 1&2 + input-dependent theta
  5. FractionalCaputo sequential loop -> channel-partitioned parallel scan
  6. Noether |h|^2 phase erasure -> concat [Re, Im, tanh(|h|^2)]
  7. VRAM telemetry: dynamic query of actual device memory
"""

import math
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F

try:
    import triton
    import triton.language as tl
    HAS_TRITON = True
except ImportError:
    triton = None
    tl = None
    HAS_TRITON = False

# ==============================================================================
# 1. TRITON PARALLEL ASSOCIATIVE SCAN (FORWARD + ANALYTICAL ADJOINT BACKWARD)
#    Solves h_t = a_t * h_{t-1} + b_t in O(N log N) work, O(log N) depth.
#    a_t = exp((-gamma + i*omega)*dt)  -- complex decay/rotation
#    b_t = u_in * dt                   -- driven input
# ==============================================================================

@triton.jit
def _complex_scan_op(a_r1, a_i1, b_r1, b_i1, a_r2, a_i2, b_r2, b_i2):
    # Associative composition: (a2,b2) o (a1,b1) = (a2*a1, a2*b1 + b2)
    # all in complex arithmetic
    out_ar = a_r2 * a_r1 - a_i2 * a_i1
    out_ai = a_r2 * a_i1 + a_i2 * a_r1
    out_br = a_r2 * b_r1 - a_i2 * b_i1 + b_r2
    out_bi = a_r2 * b_i1 + a_i2 * b_r1 + b_i2
    return out_ar, out_ai, out_br, out_bi

@triton.jit
def _parallel_complex_scan_fwd_kernel(
    Ar_ptr, Ai_ptr, Br_ptr, Bi_ptr,
    Hr_ptr, Hi_ptr,
    seq_len,
    BLOCK_SIZE: tl.constexpr
):
    pid = tl.program_id(0)
    base = pid * seq_len
    offs = tl.arange(0, BLOCK_SIZE)
    mask = offs < seq_len

    # load from global memory ONCE into registers -- no loop memory reads
    ar = tl.load(Ar_ptr + base + offs, mask=mask, other=1.0)
    ai = tl.load(Ai_ptr + base + offs, mask=mask, other=0.0)
    br = tl.load(Br_ptr + base + offs, mask=mask, other=0.0)
    bi = tl.load(Bi_ptr + base + offs, mask=mask, other=0.0)

    # tl.associative_scan handles the tree reduction purely in SRAM registers
    _, _, hr, hi = tl.associative_scan(
        (ar, ai, br, bi), axis=0, combine_fn=_complex_scan_op
    )

    tl.store(Hr_ptr + base + offs, hr, mask=mask)
    tl.store(Hi_ptr + base + offs, hi, mask=mask)

@triton.jit
def _real_scan_op(a1, b1, a2, b2):
    # real version for FractionalCaputoBank
    return a2 * a1, a2 * b1 + b2

@triton.jit
def _parallel_real_scan_fwd_kernel(
    A_ptr, B_ptr, H_ptr,
    seq_len,
    BLOCK_SIZE: tl.constexpr
):
    pid = tl.program_id(0)
    base = pid * seq_len
    offs = tl.arange(0, BLOCK_SIZE)
    mask = offs < seq_len

    a = tl.load(A_ptr + base + offs, mask=mask, other=1.0)
    b = tl.load(B_ptr + base + offs, mask=mask, other=0.0)

    _, h = tl.associative_scan((a, b), axis=0, combine_fn=_real_scan_op)
    tl.store(H_ptr + base + offs, h, mask=mask)


class MetriplecticParallelScanFn(torch.autograd.Function):
    """
    Forward: h_t = a_t * h_{t-1} + b_t  (complex, all in float32 for stability)
    Backward: analytical time-reversed adjoint scan
      g_{t-1} = conj(a_t) * g_t
      grad_b_t = g_t
      grad_a_t = g_t * conj(h_{t-1})
    """
    @staticmethod
    def forward(ctx, ar, ai, br, bi):
        # shapes: (B, D, N) contiguous float32
        B, D, N = ar.shape
        total_streams = B * D
        BLOCK_SIZE = triton.next_power_of_2(N)

        ar_c = ar.contiguous()
        ai_c = ai.contiguous()
        br_c = br.contiguous()
        bi_c = bi.contiguous()

        hr = torch.empty_like(br_c)
        hi = torch.empty_like(bi_c)

        if ar.is_cuda and BLOCK_SIZE <= 65536:
            grid = (total_streams,)
            _parallel_complex_scan_fwd_kernel[grid](
                ar_c, ai_c, br_c, bi_c, hr, hi,
                seq_len=N, BLOCK_SIZE=BLOCK_SIZE
            )
        else:
            # exact fallback for CPU or very long sequences
            h_r = torch.zeros(B, D, device=ar.device, dtype=ar.dtype)
            h_i = torch.zeros(B, D, device=ar.device, dtype=ar.dtype)
            for t in range(N):
                nh_r = ar_c[:, :, t] * h_r - ai_c[:, :, t] * h_i + br_c[:, :, t]
                nh_i = ar_c[:, :, t] * h_i + ai_c[:, :, t] * h_r + bi_c[:, :, t]
                h_r, h_i = nh_r, nh_i
                hr[:, :, t] = h_r
                hi[:, :, t] = h_i

        ctx.save_for_backward(ar_c, ai_c, hr, hi)
        ctx.N = N
        ctx.BLOCK_SIZE = BLOCK_SIZE
        return hr, hi

    @staticmethod
    def backward(ctx, grad_hr, grad_hi):
        ar, ai, hr, hi = ctx.saved_tensors
        B, D, N = ar.shape
        total_streams = B * D
        BLOCK_SIZE = ctx.BLOCK_SIZE

        # reverse-time adjoint: g_{t-1} = conj(a_{t+1}) * g_t
        # implement by flipping and running forward scan with conj(a_{t+1})
        ar_shift = torch.cat([ar[:, :, 1:], torch.zeros_like(ar[:, :, :1])], dim=-1)
        ai_shift = torch.cat([-ai[:, :, 1:], torch.zeros_like(ai[:, :, :1])], dim=-1)  # conj: negate imag

        ar_rev = torch.flip(ar_shift, dims=[-1]).contiguous()
        ai_rev = torch.flip(ai_shift, dims=[-1]).contiguous()
        gbr_rev = torch.flip(grad_hr.contiguous(), dims=[-1]).contiguous()
        gbi_rev = torch.flip(grad_hi.contiguous(), dims=[-1]).contiguous()

        gr_rev = torch.empty_like(gbr_rev)
        gi_rev = torch.empty_like(gbi_rev)

        if ar.is_cuda and BLOCK_SIZE <= 65536:
            grid = (total_streams,)
            _parallel_complex_scan_fwd_kernel[grid](
                ar_rev, ai_rev, gbr_rev, gbi_rev, gr_rev, gi_rev,
                seq_len=N, BLOCK_SIZE=BLOCK_SIZE
            )
        else:
            g_r = torch.zeros(B, D, device=ar.device, dtype=ar.dtype)
            g_i = torch.zeros(B, D, device=ar.device, dtype=ar.dtype)
            for t in range(N):
                ng_r = ar_rev[:, :, t] * g_r - ai_rev[:, :, t] * g_i + gbr_rev[:, :, t]
                ng_i = ar_rev[:, :, t] * g_i + ai_rev[:, :, t] * g_r + gbi_rev[:, :, t]
                g_r, g_i = ng_r, ng_i
                gr_rev[:, :, t] = g_r
                gi_rev[:, :, t] = g_i

        grad_br = torch.flip(gr_rev, dims=[-1])
        grad_bi = torch.flip(gi_rev, dims=[-1])

        # dL/da_t = g_t * conj(h_{t-1})
        hr_prev = torch.cat([torch.zeros_like(hr[:, :, :1]), hr[:, :, :-1]], dim=-1)
        hi_prev = torch.cat([torch.zeros_like(hi[:, :, :1]), hi[:, :, :-1]], dim=-1)

        grad_ar = grad_br * hr_prev + grad_bi * hi_prev
        grad_ai = grad_bi * hr_prev - grad_br * hi_prev

        return grad_ar, grad_ai, grad_br, grad_bi


def parallel_metriplectic_scan(ar, ai, br, bi):
    """Complex associative scan: h_t = (ar+i*ai)_t * h_{t-1} + (br+i*bi)_t"""
    orig_dtype = ar.dtype
    hr, hi = MetriplecticParallelScanFn.apply(
        ar.float(), ai.float(), br.float(), bi.float()
    )
    return hr.to(orig_dtype), hi.to(orig_dtype)


# ==============================================================================
# 2. CLIFFORD Cl(3,0) FIBER-BUNDLE STALK & CELLULAR SHEAF CONNECTION MODULE
#    - Input-dependent gauge connection: theta_t = pi * tanh(W_theta * Psi_t)
#    - Full Rodrigues sandwich product on Grade-1 (vectors) and Grade-2 (bivectors)
#    - Cyclic inter-stalk sheaf shift for cross-stalk communication
# ==============================================================================

class CliffordStalkBundle(nn.Module):
    def __init__(self, embed_dim: int):
        super().__init__()
        assert embed_dim % 8 == 0, "embed_dim must be divisible by 8 for Cl(3,0) stalks."
        self.embed_dim = embed_dim
        self.num_stalks = embed_dim // 8
        # input-dependent bivector rotation angles per token & stalk
        self.theta_proj = nn.Linear(8, 3, bias=True)
        # cellular sheaf inter-stalk mixing weight (small init)
        self.sheaf_mix = nn.Parameter(torch.ones(1, 1, self.num_stalks, 1) * 0.1)

    @staticmethod
    def _rodrigues_rotate(v: torch.Tensor, u_hat: torch.Tensor,
                          cos_t: torch.Tensor, sin_t: torch.Tensor) -> torch.Tensor:
        """
        Exact norm-preserving Rodrigues sandwich: R v R^dagger in Cl(3,0)
        v' = v*cos(theta) + (u_hat x v)*sin(theta) + u_hat*(u_hat.v)*(1-cos(theta))
        Preserves ||v||^2 exactly.
        """
        dot = torch.sum(u_hat * v, dim=-1, keepdim=True)         # (B,N,C,1)
        cross = torch.cross(u_hat, v, dim=-1)                     # (B,N,C,3)
        return v * cos_t + cross * sin_t + u_hat * dot * (1.0 - cos_t)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, N, D = x.shape
        psi = x.view(B, N, self.num_stalks, 8)

        scalar    = psi[..., 0:1]   # Grade 0 (1 component)
        vectors   = psi[..., 1:4]   # Grade 1 (3 components)
        bivectors = psi[..., 4:7]   # Grade 2 (3 components)
        pseudo    = psi[..., 7:8]   # Grade 3 (1 component)

        # input-dependent rotation angle: theta_t = pi * tanh(W_theta * Psi_t)
        theta = torch.tanh(self.theta_proj(psi)) * math.pi   # (B, N, C, 3)
        theta_norm = torch.norm(theta, dim=-1, keepdim=True) + 1e-8
        u_hat = theta / theta_norm                            # unit rotation axis
        cos_t = torch.cos(theta_norm)                         # (B, N, C, 1)
        sin_t = torch.sin(theta_norm)

        # apply full Rodrigues to both Grade-1 vectors and Grade-2 bivectors
        rot_v = self._rodrigues_rotate(vectors, u_hat, cos_t, sin_t)
        rot_b = self._rodrigues_rotate(bivectors, u_hat, cos_t, sin_t)

        transported = torch.cat([scalar, rot_v, rot_b, pseudo], dim=-1)  # (B,N,C,8)

        # cellular sheaf cyclic stalk parallel transport: inter-stalk diffusion
        # stalk c receives a small fraction from stalk (c-1 mod C)
        shifted_stalks = torch.roll(transported, shifts=1, dims=2)
        sheaf_out = transported + torch.tanh(self.sheaf_mix) * (shifted_stalks - transported)

        return sheaf_out.view(B, N, D)


# ==============================================================================
# 3. FRACTIONAL CAPUTO MEMORY BANK (PARALLELIZED MULTI-POLE SCAN)
#    - M_frac=8 log-spaced real poles: power-law memory retention
#    - Channel-partitioned: no memory blowup (no .repeat())
#    - Routed through parallel_metriplectic_scan real path
# ==============================================================================

class FractionalCaputoBank(nn.Module):
    def __init__(self, dim: int, num_modes: int = 8):
        super().__init__()
        assert dim % num_modes == 0, "dim must be divisible by num_modes."
        self.dim = dim
        self.num_modes = num_modes
        self.channels_per_mode = dim // num_modes

        # log-spaced poles: lambda_k in [10^-3.5, 10^-0.1]
        poles = torch.logspace(-3.5, -0.1, steps=num_modes)
        self.log_poles = nn.Parameter(torch.log(poles))
        self.mode_weights = nn.Parameter(torch.ones(1, 1, num_modes, 1))
        self.proj = nn.Linear(dim, dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, N, D = x.shape
        poles = torch.exp(self.log_poles)                  # (M,)

        # channel partition: each mode owns D//M channels, no repeat()
        decay = torch.exp(-poles).unsqueeze(-1).expand(   # (M, cpm)
            self.num_modes, self.channels_per_mode
        ).reshape(D)                                        # (D,)
        decay = decay.unsqueeze(0).unsqueeze(-1).expand(B, D, N)  # (B,D,N)

        x_t = x.transpose(1, 2).contiguous()              # (B, D, N)
        drive = (1.0 - decay) * x_t                       # (B, D, N)

        zero_imag = torch.zeros_like(decay)
        h_real, _ = parallel_metriplectic_scan(decay, zero_imag, drive, zero_imag)

        h_out = h_real.transpose(1, 2).view(             # (B, N, M, cpm)
            B, N, self.num_modes, self.channels_per_mode
        )
        weights = F.softplus(self.mode_weights)           # (1, 1, M, 1) positive
        weighted = (h_out * weights).view(B, N, D)        # (B, N, D)
        return self.proj(weighted)


# ==============================================================================
# 4. CAUSAL TROPHIC GLOBAL WORKSPACE BOTTLENECK
#    - M_w=32 persistent workspace slots
#    - Strictly causal: token t ONLY reads workspace states from tokens <= t
#    - Lotka-Volterra niche competition: a* = softmax(S - alpha * A_LV * S)
#    - O(N * M_w) complexity (not O(N^2))
# ==============================================================================

class CausalTrophicGlobalWorkspace(nn.Module):
    def __init__(self, dim: int, num_slots: int = 32, slot_dim: int = 256):
        super().__init__()
        self.num_slots = num_slots
        self.slot_dim = slot_dim
        self.workspace_slots = nn.Parameter(torch.randn(num_slots, slot_dim) * 0.02)
        # Lotka-Volterra competition matrix: eye + small off-diagonal
        self.interaction_matrix = nn.Parameter(
            torch.eye(num_slots) + 0.1 * torch.ones(num_slots, num_slots)
        )
        self.write_proj = nn.Linear(dim, slot_dim, bias=False)
        self.read_proj = nn.Linear(slot_dim, dim, bias=False)
        self.gate = nn.Linear(dim, dim)

    def forward(self, x: torch.Tensor):
        B, N, D = x.shape
        u = self.write_proj(x)   # (B, N, slot_dim)

        # affinity scores against baseline workspace prototypes
        affinity = torch.einsum('bnd,md->bnm', u, self.workspace_slots) / math.sqrt(self.slot_dim)

        # Lotka-Volterra lateral inhibition (niche differentiation)
        lv_matrix = F.softplus(self.interaction_matrix)
        inhibition = torch.einsum('bnm,mk->bnk', affinity, lv_matrix)
        bidding_weights = F.softmax(affinity - 0.1 * inhibition, dim=-1)   # (B, N, M_w)

        # CAUSAL write phase: prefix sum over sequence dimension
        # outer product at each step: bidding_weights[t] x u[t] -> (M_w, slot_dim)
        weighted_u = bidding_weights.unsqueeze(-1) * u.unsqueeze(2)        # (B,N,M_w,slot_dim)
        causal_coalition = torch.cumsum(weighted_u, dim=1)                 # strictly causal
        normalizer = torch.cumsum(bidding_weights, dim=1).unsqueeze(-1) + 1e-6
        # each position t sees workspace updated only by tokens 0..t
        causal_slots = (
            0.9 * self.workspace_slots.view(1, 1, self.num_slots, self.slot_dim) +
            0.1 * (causal_coalition / normalizer)
        )

        # causal broadcast phase: read from time-local workspace at step t
        broadcast_info = torch.einsum('bnm,bnmd->bnd', bidding_weights, causal_slots)
        broadcast_features = self.read_proj(broadcast_info)

        # workspace entropy telemetry (Lotka-Volterra niche partitioning quality)
        slot_probs = bidding_weights.mean(dim=(0, 1))  # (M_w,)
        ws_entropy = -torch.sum(slot_probs * torch.log(slot_probs + 1e-8))

        return torch.sigmoid(self.gate(x)) * broadcast_features, ws_entropy


# ==============================================================================
# 5. INTEGRATED RMSN LAYER
#    Forward stages:
#      1. CliffordStalkBundle: gauge rotation + sheaf transport
#      2. MetriplecticScan: second-order port dynamics in complex state space
#      3. Noether readout: cat[Re(h), Im(h), tanh(|h|^2)] -> Linear (phase-preserving)
#      4. FractionalCaputoBank: power-law temporal memory
#      5. CausalTrophicGW: global context via causal competitive workspace
#    Returns (x, telemetry) where telemetry = {max_lyapunov, mean_energy, ws_entropy}
# ==============================================================================

class RMSNLayer(nn.Module):
    def __init__(self, dim: int, num_slots: int = 32):
        super().__init__()
        self.dim = dim
        self.norm1 = nn.RMSNorm(dim)
        self.norm2 = nn.RMSNorm(dim)

        self.clifford = CliffordStalkBundle(dim)
        self.omega_proj = nn.Linear(dim, dim)
        self.gamma_proj = nn.Linear(dim, dim)
        self.in_proj = nn.Linear(dim, dim)

        # phase-preserving Noether readout: 3D -> D
        self.noether_readout = nn.Linear(dim * 3, dim)

        self.fractional_bank = FractionalCaputoBank(dim, num_modes=8)
        self.workspace = CausalTrophicGlobalWorkspace(
            dim, num_slots=num_slots, slot_dim=min(256, dim)
        )

    def forward(self, x: torch.Tensor):
        residual = x
        x_norm = self.norm1(x)

        # stage 1: Clifford gauge rotation + cellular sheaf transport
        x_cliff = self.clifford(x_norm)

        # stage 2: second-order port-metriplectic wave dynamics
        # a_t = exp((-gamma + i*omega)*dt)
        omega = F.softplus(self.omega_proj(x_cliff))
        gamma = F.softplus(self.gamma_proj(x_cliff)) + 1e-3   # strict Lyapunov: gamma > 0
        u_in  = self.in_proj(x_cliff)

        dt = 0.05
        decay = torch.exp(-gamma * dt)
        ar = (decay * torch.cos(omega * dt)).transpose(1, 2)   # (B, D, N)
        ai = (decay * torch.sin(omega * dt)).transpose(1, 2)
        br = (u_in * dt).transpose(1, 2)
        bi = torch.zeros_like(br)

        hr, hi = parallel_metriplectic_scan(ar, ai, br, bi)
        hr_t = hr.transpose(1, 2)   # (B, N, D)
        hi_t = hi.transpose(1, 2)

        # phase-preserving Noether current readout (NOT just |h|^2)
        # T^00 = tanh(|h|^2) bounded energy density
        # + Re(h), Im(h) for phase and momentum flux T^0i
        noether_energy = torch.tanh(hr_t ** 2 + hi_t ** 2)
        field_state = torch.cat([hr_t, hi_t, noether_energy], dim=-1)   # (B, N, 3D)
        dynamic_out = self.noether_readout(field_state)
        x = residual + dynamic_out

        # stage 3+4: fractional memory + causal cognitive workspace
        residual2 = x
        x_norm2 = self.norm2(x)
        frac_mem = self.fractional_bank(x_norm2)
        ws_out, ws_entropy = self.workspace(x_norm2)
        x = residual2 + frac_mem + ws_out

        telemetry = {
            "max_lyapunov": float((-gamma).max().item()),   # should be < 0
            "mean_energy":  float((hr_t ** 2 + hi_t ** 2).mean().item()),
            "ws_entropy":   float(ws_entropy.item()),
        }
        return x, telemetry

    def init_state(self, batch_size: int, device: torch.device, dtype: torch.dtype = torch.float32):
        """Initializes constant-time recurrent inference state."""
        return {
            "hr": torch.zeros(batch_size, 1, self.dim, device=device, dtype=dtype),
            "hi": torch.zeros(batch_size, 1, self.dim, device=device, dtype=dtype),
            "h_frac": torch.zeros(batch_size, 1, self.dim, device=device, dtype=dtype),
            "ws_coalition": torch.zeros(batch_size, 1, self.workspace.num_slots, self.workspace.slot_dim, device=device, dtype=dtype),
            "ws_weights": torch.zeros(batch_size, 1, self.workspace.num_slots, 1, device=device, dtype=dtype),
        }

    def step(self, x: torch.Tensor, state: dict) -> torch.Tensor:
        """Single-step O(1) recurrent update for autoregressive generation."""
        residual = x
        x_norm = self.norm1(x)

        # 1. Clifford gauge rotation + cellular sheaf transport
        x_cliff = self.clifford(x_norm)

        # 2. Port-metriplectic wave step
        omega = F.softplus(self.omega_proj(x_cliff))
        gamma = F.softplus(self.gamma_proj(x_cliff)) + 1e-3
        u_in  = self.in_proj(x_cliff)

        dt = 0.05
        decay = torch.exp(-gamma * dt)
        cos_w = torch.cos(omega * dt)
        sin_w = torch.sin(omega * dt)

        hr_prev = state["hr"]
        hi_prev = state["hi"]

        hr_next = decay * (cos_w * hr_prev - sin_w * hi_prev) + (u_in * dt)
        hi_next = decay * (cos_w * hi_prev + sin_w * hr_prev)
        state["hr"] = hr_next
        state["hi"] = hi_next

        noether_energy = torch.tanh(hr_next ** 2 + hi_next ** 2)
        field_state = torch.cat([hr_next, hi_next, noether_energy], dim=-1)
        dynamic_out = self.noether_readout(field_state)
        x = residual + dynamic_out

        # 3. Fractional memory step
        residual2 = x
        x_norm2 = self.norm2(x)

        poles = torch.exp(self.fractional_bank.log_poles)
        decay_f = torch.exp(-poles).unsqueeze(-1).expand(
            self.fractional_bank.num_modes, self.fractional_bank.channels_per_mode
        ).reshape(1, 1, self.dim)

        h_frac_prev = state["h_frac"]
        h_frac_next = decay_f * h_frac_prev + (1.0 - decay_f) * x_norm2
        state["h_frac"] = h_frac_next

        h_out = h_frac_next.view(
            x.shape[0], 1, self.fractional_bank.num_modes, self.fractional_bank.channels_per_mode
        )
        weights = F.softplus(self.fractional_bank.mode_weights)
        frac_mem = self.fractional_bank.proj((h_out * weights).view(x.shape[0], 1, self.dim))

        # 4. Causal Trophic Workspace step
        u_ws = self.workspace.write_proj(x_norm2)
        bidding_scores = torch.einsum('bnd,md->bnm', u_ws, self.workspace.workspace_slots)
        interaction = torch.matmul(bidding_scores, self.workspace.interaction_matrix)
        bidding_weights = F.softmax(bidding_scores - 0.1 * interaction, dim=-1)

        weighted_u = bidding_weights.unsqueeze(-1) * u_ws.unsqueeze(2)
        state["ws_coalition"] = state["ws_coalition"] + weighted_u
        state["ws_weights"] = state["ws_weights"] + bidding_weights.unsqueeze(-1)

        causal_slots = (
            0.9 * self.workspace.workspace_slots.view(1, 1, self.workspace.num_slots, self.workspace.slot_dim) +
            0.1 * (state["ws_coalition"] / (state["ws_weights"] + 1e-6))
        )
        broadcast_info = torch.einsum('bnm,bnmd->bnd', bidding_weights, causal_slots)
        broadcast_features = self.workspace.read_proj(broadcast_info)
        ws_out = torch.sigmoid(self.workspace.gate(x_norm2)) * broadcast_features

        x = residual2 + frac_mem + ws_out
        return x


# ==============================================================================
# 6. RESONANT METRIPLECTIC SHEAF LANGUAGE MODEL
# ==============================================================================

class ResonantMetriplecticSheafLM(nn.Module):
    def __init__(self, vocab_size: int = 32000, dim: int = 512,
                 depth: int = 6, num_slots: int = 32):
        super().__init__()
        self.vocab_size = vocab_size
        self.dim = dim
        self.depth = depth

        self.token_embed = nn.Embedding(vocab_size, dim)
        self.layers = nn.ModuleList([
            RMSNLayer(dim=dim, num_slots=num_slots) for _ in range(depth)
        ])
        self.final_norm = nn.RMSNorm(dim)
        self.lm_head = nn.Linear(dim, vocab_size, bias=False)
        self.lm_head.weight = self.token_embed.weight   # weight tying

    def forward(self, input_ids: torch.Tensor, return_telemetry: bool = False):
        x = self.token_embed(input_ids)
        last_telemetry = {}
        for layer in self.layers:
            x, last_telemetry = layer(x)
        x = self.final_norm(x)
        logits = self.lm_head(x)
        if return_telemetry:
            return logits, last_telemetry
        return logits

    def init_state(self, batch_size: int, device: torch.device, dtype: torch.dtype = torch.float32):
        """Initializes constant-time recurrent inference state across all layers."""
        return [layer.init_state(batch_size, device, dtype) for layer in self.layers]

    def step(self, token_id: torch.Tensor, layer_states: list) -> torch.Tensor:
        """
        Single-step O(1) recurrent update for autoregressive generation.
        token_id: (B, 1) LongTensor
        layer_states: list of dicts for each layer
        returns: next_token_logits (B, vocab_size)
        """
        x = self.token_embed(token_id)
        for i, layer in enumerate(self.layers):
            x = layer.step(x, layer_states[i])
        x = self.final_norm(x)
        logits = self.lm_head(x).squeeze(1)
        return logits

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 50,
        temperature: float = 0.8,
        top_k: int = 50,
        top_p: float = 0.9,
        eos_token_id: int = None,
        repetition_penalty: float = 1.0,
    ) -> torch.Tensor:
        """
        Fast autoregressive generation with constant-time O(1) recurrent updates.
        input_ids: (B, T) LongTensor prompt
        returns: (B, T + generated_len) LongTensor
        """
        self.eval()
        device = input_ids.device
        B, T = input_ids.shape
        dtype = self.token_embed.weight.dtype
        states = self.init_state(B, device, dtype=dtype)

        # 1. Warm up recurrent states across prompt
        for t in range(T):
            token_t = input_ids[:, t:t+1]
            logits = self.step(token_t, states)

        # 2. Sequential autoregressive token generation
        generated = []
        cur_logits = logits

        for _ in range(max_new_tokens):
            if temperature > 0:
                scaled_logits = cur_logits / temperature
                # Penalize tokens already in the context (prompt + generated so far)
                if repetition_penalty != 1.0 and (len(generated) > 0 or T > 0):
                    context = torch.cat([input_ids] + generated, dim=1) if generated else input_ids
                    for token_id in context[0].unique():
                        if scaled_logits[0, token_id] > 0:
                            scaled_logits[0, token_id] /= repetition_penalty
                        else:
                            scaled_logits[0, token_id] *= repetition_penalty
                if top_k > 0:
                    val, _ = torch.topk(scaled_logits, min(top_k, scaled_logits.size(-1)))
                    scaled_logits[scaled_logits < val[:, -1:]] = -float('Inf')
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(scaled_logits, descending=True)
                    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                    sorted_indices_to_remove[..., 0] = 0
                    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
                    scaled_logits[indices_to_remove] = -float('Inf')
                probs = F.softmax(scaled_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
            else:
                next_token = torch.argmax(cur_logits, dim=-1, keepdim=True)

            generated.append(next_token)
            if eos_token_id is not None and (next_token == eos_token_id).all():
                break

            cur_logits = self.step(next_token, states)

        if generated:
            out_ids = torch.cat([input_ids, torch.cat(generated, dim=1)], dim=1)
        else:
            out_ids = input_ids
        return out_ids


# ==============================================================================
# HUGGINGFACE-COMPATIBLE WRAPPER INTERFACE
# ==============================================================================

@dataclass
class RMSNConfig:
    vocab_size: int = 49152
    hidden_dim: int = 1024
    num_layers: int = 16
    num_workspace_slots: int = 64
    max_seq_len: int = 2048


class RMSNForCausalLM(nn.Module):
    """
    Standard causal LM interface wrapping ResonantMetriplecticSheafLM.
    Defaults to return_telemetry=True to ensure compatibility with real-time monitoring.
    """
    def __init__(self, config: RMSNConfig):
        super().__init__()
        self.config = config
        self.model = ResonantMetriplecticSheafLM(
            vocab_size=config.vocab_size,
            dim=config.hidden_dim,
            depth=config.num_layers,
            num_slots=config.num_workspace_slots,
        )

    def forward(self, input_ids: torch.Tensor, return_telemetry: bool = True):
        out = self.model(input_ids, return_telemetry=return_telemetry)
        if return_telemetry:
            return out  # (logits, telemetry_dict)
        return out, {}

    @torch.no_grad()
    def generate(self, input_ids: torch.Tensor, **kwargs):
        """Autoregressive text generation delegate."""
        return self.model.generate(input_ids, **kwargs)


# ==============================================================================
# QUICK VALIDATION HARNESS
# ==============================================================================

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[RMSN] Device: {device}")
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        print(f"[RMSN] GPU: {props.name} | VRAM: {props.total_memory/1024**3:.1f} GB")

    # small PoC config for quick validation
    B, N, dim, depth, vocab = 2, 128, 256, 4, 1000
    model = ResonantMetriplecticSheafLM(
        vocab_size=vocab, dim=dim, depth=depth, num_slots=16
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[RMSN] Params: {n_params/1e6:.2f}M")

    tokens = torch.randint(0, vocab, (B, N), device=device)
    targets = torch.randint(0, vocab, (B, N), device=device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)

    print("[RMSN] Running forward-backward validation...")
    opt.zero_grad()
    logits, telemetry = model(tokens, return_telemetry=True)
    loss = F.cross_entropy(logits.view(-1, vocab), targets.view(-1))
    loss.backward()
    opt.step()

    print(f"[RMSN] loss={loss.item():.4f} | telemetry={telemetry}")
    if torch.cuda.is_available():
        alloc = torch.cuda.memory_allocated() / 1024**2
        print(f"[RMSN] VRAM allocated: {alloc:.1f} MB")
    print("[RMSN] VALIDATION PASSED")
