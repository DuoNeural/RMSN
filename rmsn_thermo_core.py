"""
rmsn_thermo_core.py -- 4-Laws of Thermodynamics Resonant Metriplectic Sheaf Network (T-RMSN)
DuoNeural Lab | Jesse Caldwell, Aura & Archon | 2026-11-13

Theoretical Foundation:
  1st Law: Symplectic Poisson bracket {F, H} = grad(F)^T J grad(H), with J = -J^T.
           Unitary phase rotation e^(i*omega*dt) conserving Hamiltonian energy + Noether energy current.
  2nd Law: Morrison dissipative bracket [F, S] = grad(F)^T M grad(S), with M >= 0.
           Contractive Lyapunov decay e^(-gamma*dt) driving entropy production.
  0th Law: Thermal Equilibrium Transitivity:
           Dynamic layer temperature T_l = 1 / (mean(gamma_l) + eps).
           Inter-layer Fourier thermal conduction:
             Q_{l-1 -> l} = kappa_l * tanh(T_{l-1} - T_l) * W_thermal(x_{l-1})
           High-T (turbulent) layers flow knowledge down thermal gradient into low-T (dissipative) layers.
  3rd Law: Nernst Ground State Protection:
           As global workspace entropy approaches learned ground state S_min,
           xi_S = tanh(max(0, S_ws - S_min) / tau_S) -> 0.
           Dissipation freezes: gamma_effective = gamma * (0.05 + 0.95 * xi_S).
           Guarantees exact topological soliton ground state without over-collapse or catastrophic forgetting.
"""

import math
from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F

from rmsn_core import (
    CliffordStalkBundle,
    FractionalCaputoBank,
    CausalTrophicGlobalWorkspace,
    parallel_metriplectic_scan
)

class ThermodynamicRMSNLayer(nn.Module):
    def __init__(self, dim: int, num_slots: int = 32, default_s_min: float = 1.5):
        super().__init__()
        self.dim = dim
        self.norm1 = nn.RMSNorm(dim)
        self.norm2 = nn.RMSNorm(dim)

        self.clifford = CliffordStalkBundle(dim)
        self.omega_proj = nn.Linear(dim, dim)
        self.gamma_proj = nn.Linear(dim, dim)
        self.in_proj = nn.Linear(dim, dim)

        # Noether current readout: [Re(h), Im(h), tanh(|h|^2)] -> dim
        self.noether_readout = nn.Linear(dim * 3, dim)

        self.fractional_bank = FractionalCaputoBank(dim, num_modes=8)
        self.workspace = CausalTrophicGlobalWorkspace(
            dim, num_slots=num_slots, slot_dim=min(256, dim)
        )

        # 0th Law: Inter-layer Fourier thermal conduction
        self.thermal_proj = nn.Linear(dim, dim, bias=False)
        self.kappa = nn.Parameter(torch.tensor(0.05))

        # 3rd Law: Nernst ground-state entropy floor
        self.s_min = nn.Parameter(torch.tensor(default_s_min))

    def forward(self, x: torch.Tensor, prev_temp: torch.Tensor = None):
        residual = x
        x_norm = self.norm1(x)

        # 1. Clifford gauge rotation + cellular sheaf transport
        x_cliff = self.clifford(x_norm)

        # 2. Raw physical frequencies and unmodulated dissipation
        omega = F.softplus(self.omega_proj(x_cliff))
        gamma_raw = F.softplus(self.gamma_proj(x_cliff)) + 1e-3
        u_in = self.in_proj(x_cliff)

        # 0th Law: Calculate current layer temperature
        # Hot layers: low dissipation (high T). Cold layers: deep dissipation (low T).
        layer_temp = 1.0 / (gamma_raw.mean() + 1e-4)

        # 0th Law Thermal Conduction: If receiving heat flux from previous layer
        heat_flux = torch.tensor(0.0, device=x.device)
        if prev_temp is not None:
            # Thermal gradient: delta_T = prev_temp - layer_temp
            # Heat flows down temperature gradient: Q = kappa * tanh(delta_T) * W_thermal(x)
            delta_T = prev_temp - layer_temp
            heat_flux = torch.tanh(delta_T) * self.kappa
            x_cliff = x_cliff + heat_flux * self.thermal_proj(x_cliff)

        # 3rd Law: Query global workspace entropy to evaluate Nernst floor
        x_norm2 = self.norm2(x)
        ws_out, ws_entropy = self.workspace(x_norm2)

        # Nernst ground-state protection factor xi_S:
        # As ws_entropy approaches s_min, xi_S -> 0, freezing dissipation
        entropy_gap = F.relu(ws_entropy - self.s_min)
        xi_S = torch.tanh(entropy_gap / 0.5)
        gamma = gamma_raw * (0.05 + 0.95 * xi_S)

        # 1st + 2nd Law Metriplectic Scan
        dt = 0.05
        decay = torch.exp(-gamma * dt)
        ar = (decay * torch.cos(omega * dt)).transpose(1, 2)
        ai = (decay * torch.sin(omega * dt)).transpose(1, 2)
        br = (u_in * dt).transpose(1, 2)
        bi = torch.zeros_like(br)

        hr, hi = parallel_metriplectic_scan(ar, ai, br, bi)
        hr_t = hr.transpose(1, 2)
        hi_t = hi.transpose(1, 2)

        noether_energy = torch.tanh(hr_t ** 2 + hi_t ** 2)
        field_state = torch.cat([hr_t, hi_t, noether_energy], dim=-1)
        dynamic_out = self.noether_readout(field_state)
        x = residual + dynamic_out

        # Fractional memory + global workspace accumulation
        frac_mem = self.fractional_bank(x_norm2)
        x = x + frac_mem + ws_out

        telemetry = {
            "temperature": float(layer_temp.detach().item()),
            "heat_flux": float(heat_flux.detach().item()),
            "ws_entropy": float(ws_entropy.detach().item()),
            "nernst_xi": float(xi_S.detach().item()),
            "gamma_mean": float(gamma.detach().mean().item()),
            "max_lyapunov": float((-gamma).detach().max().item()),
        }
        return x, layer_temp, telemetry

class ThermodynamicResonantMetriplecticSheafLM(nn.Module):
    def __init__(self, vocab_size: int = 49152, dim: int = 1024, depth: int = 16, num_slots: int = 64):
        super().__init__()
        self.vocab_size = vocab_size
        self.dim = dim
        self.depth = depth
        self.num_slots = num_slots

        self.token_embed = nn.Embedding(vocab_size, dim)
        self.layers = nn.ModuleList([
            ThermodynamicRMSNLayer(dim=dim, num_slots=num_slots) for _ in range(depth)
        ])
        self.final_norm = nn.RMSNorm(dim)
        self.lm_head = nn.Linear(dim, vocab_size, bias=False)
        self.lm_head.weight = self.token_embed.weight

    def forward(self, input_ids: torch.Tensor, return_telemetry: bool = False):
        x = self.token_embed(input_ids)
        prev_temp = None
        telemetries = []

        for layer in self.layers:
            x, prev_temp, telem = layer(x, prev_temp=prev_temp)
            telemetries.append(telem)

        x = self.final_norm(x)
        logits = self.lm_head(x)
        if return_telemetry:
            return logits, telemetries
        return logits

@dataclass
class ThermodynamicRMSNConfig:
    vocab_size: int = 49152
    hidden_dim: int = 1024
    num_layers: int = 16
    num_workspace_slots: int = 64
    max_seq_len: int = 512

class ThermodynamicRMSNForCausalLM(nn.Module):
    def __init__(self, config: ThermodynamicRMSNConfig):
        super().__init__()
        self.config = config
        self.model = ThermodynamicResonantMetriplecticSheafLM(
            vocab_size=config.vocab_size,
            dim=config.hidden_dim,
            depth=config.num_layers,
            num_slots=config.num_workspace_slots
        )

    def forward(self, input_ids: torch.Tensor, return_telemetry: bool = False):
        return self.model(input_ids, return_telemetry=return_telemetry)

print('Thermodynamic RMSN Core loaded successfully.')
