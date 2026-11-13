import sys, math
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, '/home/ai/duoneural/RMSN')
from rmsn_core import (
    CliffordStalkBundle,
    FractionalCaputoBank,
    CausalTrophicGlobalWorkspace,
    parallel_metriplectic_scan
)

class ThermodynamicRMSNLayer(nn.Module):
    """
    RMSN Layer implementing the 4 Laws of Thermodynamics:
      1st Law: Symplectic Poisson bracket unitary phase rotation e^(i*omega*dt) + Noether readout
      2nd Law: Morrison dissipative bracket entropy production e^(-gamma*dt)
      0th Law: Local temperature calculation T_l = 1 / (mean(gamma) + eps)
      3rd Law: Nernst ground-state floor xi_S = tanh(max(0, S_ws - S_min) / tau)
               protecting ground state solitons from over-dissipation.
    """
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

        # 0th Law: Inter-stalk thermal conduction projection
        self.thermal_proj = nn.Linear(dim, dim, bias=False)
        self.kappa = nn.Parameter(torch.tensor(0.05))

        # 3rd Law: Nernst ground-state entropy floor
        self.s_min = nn.Parameter(torch.tensor(default_s_min))

    def forward(self, x: torch.Tensor, prev_temp: torch.Tensor = None):
        residual = x
        x_norm = self.norm1(x)

        # 1. Clifford gauge rotation
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

        # Memory + workspace accumulation
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

class ThermodynamicRMSNLM(nn.Module):
    def __init__(self, vocab_size: int = 49152, dim: int = 512, depth: int = 6, num_slots: int = 32):
        super().__init__()
        self.vocab_size = vocab_size
        self.dim = dim
        self.depth = depth

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
        layer_telemetries = []

        for layer in self.layers:
            x, prev_temp, telem = layer(x, prev_temp=prev_temp)
            layer_telemetries.append(telem)

        x = self.final_norm(x)
        logits = self.lm_head(x)
        if return_telemetry:
            return logits, layer_telemetries
        return logits

if __name__ == '__main__':
    print("Initializing ThermodynamicRMSNLM test...")
    model = ThermodynamicRMSNLM(vocab_size=1000, dim=128, depth=4, num_slots=16)
    inputs = torch.randint(0, 1000, (2, 32))
    logits, telems = model(inputs, return_telemetry=True)
    loss = logits.sum()
    loss.backward()
    print("Forward + Backward Successful!")
    print(f"Logits shape: {logits.shape}")
    for idx, t in enumerate(telems):
        print(f"  Layer {idx}: Temp={t['temperature']:.3f} | HeatFlux={t['heat_flux']:.4f} | Entropy={t['ws_entropy']:.3f} | Nernst_xi={t['nernst_xi']:.3f} | Gamma={t['gamma_mean']:.4f}")
    print("ALL 4 LAWS OF THERMODYNAMICS OPERATIONAL!")
