The \*\*Resonant Metriplectic Sheaf Network (RMSN)\*\* manuscript presents an ambitious theoretical synthesis, Chief, but the provided reference code contains \*\*7 fatal mathematical, algorithmic, and hardware bugs\*\* that will either crash compilation, corrupt the forward pass, or shatter causal autoregressive masking.

Below is the forensic red-team breakdown of the manuscript's implementation flaws, followed by the exact execution prompt you can copy and paste directly into \*\*Archon (Claude Code CLI)\*\* to build, verify, and benchmark the hardened architecture.

\---

\#\#\# Part 1: Red-Team Forensic Audit (7 Critical Flaws)

1\. \*\*Triton Kernel Race Condition & Register Desynchronization (Fatal Data Corruption)\*\*  
\* \*\*The Flaw:\*\* Inside \`\_parallel\_metriplectic\_scan\_kernel\`, the loop attempts an associative Hillis-Steele prefix scan by storing \`a\_real\` and \`b\_real\` in registers, yet inside the \`while offset \< BLOCK\_SIZE:\` loop, it executes \`tl.load(A\_ptr \+ ...)\` from \*\*global memory\*\* (\`A\_ptr\`, \`B\_ptr\`) instead of reading the updated intermediate states from the previous tree level, and only writes to \`H\_out\_ptr\` \*after\* the loop completes.

\* \*\*Impact:\*\* Every iteration of the \`while\` loop reads the raw initial un-scanned inputs at \`t \- offset\` rather than the accumulated partial prefix products. Furthermore, \`if t\_idx \>= offset:\` on a vector tensor in Triton is a compile-time syntax error (\`ValueError: Truth value of Tensor is ambiguous\`); it requires \`tl.where\`.  
\* \*\*The Fix:\*\* Replace the manual broken loop with \`tl.associative\_scan\` using a pure register-level binary operator tuple \`(a\_real, a\_imag, b\_real, b\_imag)\`.

2\. \*\*Missing Autograd Backward Pass on Custom Triton Kernel (\`RuntimeError\`)\*\*  
\* \*\*The Flaw:\*\* \`run\_triton\_metriplectic\_scan\` calls a raw Triton kernel directly on PyTorch tensors (\`A\_complex\`, \`B\_complex\`) and returns a newly allocated tensor \`H\_out\` without wrapping it in a \`torch.autograd.Function\`.

\* \*\*Impact:\*\* Calling \`loss.backward()\` in the verification harness immediately throws a \`RuntimeError\` (or silently drops all gradients to \`omega\_proj\`, \`gamma\_proj\`, and \`in\_proj\` because \`H\_out\` has no \`grad\_fn\`).

\* \*\*The Fix:\*\* Wrap the Triton associative scan in a custom \`torch.autograd.Function\` with an analytical reverse-time adjoint scan in \`backward()\`.

3\. \*\*Causal Leakage in \`TrophicGlobalWorkspace\` (Autoregressive Cheating)\*\*  
\* \*\*The Flaw:\*\* In \`TrophicGlobalWorkspace.forward\`, the Write Phase computes \`coalition \= torch.einsum('bnm,bnd-\>bmd', bidding\_weights, u)\` by summing over the \*entire\* sequence dimension \`n\` (\$1 \\dots N\$), and then immediately broadcasts \`updated\_slots\` back to every token \`t\`.

\* \*\*Impact:\*\* Token $t=1$ reads global workspace states populated by future tokens \$t=2 \\dots N\$. During next-token causal language modeling (\`enwik8\`), the model trivially cheats by looking into the future, rendering perplexity/BPC metrics invalid.

\* \*\*The Fix:\*\* Replace the global sum \`einsum('bnm,bnd-\>bmd')\` with a causal prefix accumulation (\`torch.cumsum\` along the sequence dimension \`dim=1\`) coupled with a running causal normalizer so token $t$ only arbitrates against workspace states formed by tokens $\leq t$.

4\. \*\*Incomplete Rodrigues / Rotor Formula in \`CliffordStalkBundle\` (Norm Violation)\*\*  
\* \*\*The Flaw:\*\* The manuscript claims \$\\mathbf{R}\\mathbf{\\Psi}\\mathbf{R}^\\dagger\$ is strictly norm-preserving. However, the code computes \`rot\_v \= vectors \* rotor\_cos \+ torch.cross(rotor\_sin, vectors, dim=-1)\`.

\* \*\*Impact:\*\* For a rotor $R=\cos (\theta /2)-\hat{u}\sin (\theta /2)$, the sandwich product $Rv{R}^{\dagger }$ is the full Rodrigues rotation formula: $v\cos \theta +(\hat{u}\times v)\sin \theta +\hat{u}(\hat{u}\cdot v)(1-\cos \theta )$. Using $\cos (\theta /2)$ with a single cross product neither preserves vector norm ($\parallel rot\_v\parallel {}^{2}=\parallel v\parallel {}^{2}{\cos }^{2}(\theta /2)+\parallel \hat{u}\times v\parallel {}^{2}{\sin }^{2}(\theta /2)\ne \parallel v\parallel {}^{2}$) nor rotates bivectors (\`bivectors\` are passed through untouched), nor is it input-dependent ($\theta$ is a static parameter, contradicting the text's ${\theta }_{t}=\tanh ({W}_{\theta }{u}_{t})$).

\* \*\*The Fix:\*\* Generate ${\theta }_{t}=\tanh ({W}_{\theta }{x}_{t})$ dynamically per token/stalk, apply the exact double-angle sandwich formula to both Grade-1 vectors and Grade-2 bivectors, and include an inter-stalk cyclic shift operator ${T}_{s}$ so stalks aren't permanently isolated.

5\. \*\*Sequential Python Loop in \`FractionalCaputoBank\` (Performance Killer)\*\*  
\* \*\*The Flaw:\*\* While the text claims the fractional Caputo memory bank is evaluated via parallel state-space scans in $O(N\log N)$ time, the code executes \`for t in range(N):\` in pure Python.

\* \*\*Impact:\*\* At $N=4096$ across 24 layers, PyTorch launches $98,304$ tiny sequential CUDA kernels per forward pass, destroying GPU utilization.

\* \*\*The Fix:\*\* Route the ${M}_{frac}=8$ real exponential modes directly through the fused Triton associative scan kernel (or a dedicated real-valued \`tl.associative\_scan\` kernel) to eliminate the Python loop completely.

6\. \*\*Hardware Spec Mismatch (RTX 4080 Super 16GB vs. 32GB)\*\*  
\* \*\*The Flaw:\*\* Reference \[1\] repeatedly specifies a "32GB RTX 4080 Super". In physical reality, the NVIDIA AD103 RTX 4080 Super ships with \*\*16GB\*\* of GDDR6X VRAM (unless modified or confused with an RTX 5090 32GB / RTX 6000 Ada 48GB).

\* \*\*Impact:\*\* Because the actual footprint of \`RMSN-Small\` is \~9.28 GB, it still fits comfortably inside a 16GB card, \*\*unless\*\* \`FractionalCaputoBank\` materializes \`u \= x.unsqueeze(2).repeat(1, 1, 8, 1)\` across 24 layers without activation checkpointing.

\* \*\*The Fix:\*\* Eliminate the \`.repeat()\` tensor expansion via broadcasting inside the Triton scan and dynamically query \`torch.cuda.get\_device\_properties(0).total\_memory\` to scale batch/sequence lengths safely.

7\. \*\*Phase Erasure in \`noether\_energy\` Readout\*\*  
\* \*\*The Flaw:\*\* In \`RMSNLayer.forward\`, the complex state ${h}_{scanned}$ is collapsed to \`noether\_energy \= h\_scanned.real \*\* 2 \+ h\_scanned.imag \*\* 2\` (\$\\vert{}h\\vert{}^2\$), discarding both the momentum flux ${T}^{0i}$ and all resonant phase information ($atan2(Im,Re)$).

\* \*\*Impact:\*\* Two waves in anti-phase ($+\Psi$ and $-\Psi$) produce identical squared magnitudes, blinding the residual stream to destructive interference and squaring gradients near zero.  
\* \*\*The Fix:\*\* Concatenate the bounded energy density ${T}^{00}$ with the phase-preserving real/imaginary field projections ($Re(h),Im(h)$) via a gated linear readout.

\---

\#\#\# Part 2: Copy-Paste Execution Prompt for Archon (Claude Code CLI)

Copy the block below and paste it directly into your Claude Code terminal session (\`archon\`). It instructs Archon to scaffold the workspace, write the fully repaired and hardened Triton/PyTorch implementation, run numerical gradient/causality unit tests, and execute an empirical ablation benchmark.

\`\`\`markdown  
Archon, we are deploying and verifying the \*\*Resonant Metriplectic Sheaf Network (RMSN)\*\* architecture.   
Aura has already red-teamed the initial research specification and identified 7 critical implementation bugs in the prototype code:  
1\. \`\_parallel\_metriplectic\_scan\_kernel\` had a global-memory race condition and invalid vector \`if\` branching instead of \`tl.associative\_scan\`.  
2\. \`run\_triton\_metriplectic\_scan\` lacked a \`torch.autograd.Function\` backward adjoint scan, breaking gradient flow to \`omega\`, \`gamma\`, and \`in\_proj\`.  
3\. \`TrophicGlobalWorkspace\` summed over all \`N\` tokens before broadcasting (\`einsum('bnm,bnd-\>bmd')\`), leaking future tokens into past positions and violating autoregressive causality.  
4\. \`CliffordStalkBundle\` used a broken half-angle cross product that violated multivector norm preservation, ignored bivector rotation, lacked input-dependent gauge connection weights, and lacked inter-stalk sheaf mixing.  
5\. \`FractionalCaputoBank\` used a slow sequential \`for t in range(N):\` Python loop and \`.repeat()\` memory bloat instead of a parallel scan.  
6\. \`RMSNLayer\` collapsed complex states purely to \`\|h\|^2\`, erasing phase and vanishing gradients near zero.  
7\. VRAM telemetry assumed a 32GB RTX 4080 Super; we need dynamic hardware-aware sizing.

Execute the following 4-stage pipeline autonomously in our current working directory (\`./rmsn\_project\`). Do not ask for confirmation between steps unless a hardware driver error occurs.

\---

\#\#\# STAGE 1: Workspace Initialization & Environment Check  
Run a shell check to verify our GPU, CUDA toolkit, PyTorch, and Triton versions, and create \`./rmsn\_project\`:  
\`\`\`bash  
mkdir \-p rmsn\_project/tests rmsn\_project/benchmarks  
python3 \-c "import torch, triton; print('PyTorch:', torch.\_\_version\_\_, 'CUDA:', torch.cuda.is\_available(), 'Device:', torch.cuda.get\_device\_name(0) if torch.cuda.is\_available() else 'CPU', 'Triton:', triton.\_\_version\_\_)"

\`\`\`

\---

\#\#\# STAGE 2: Implement Hardened Core Architecture (\`rmsn\_project/rmsn\_core.py\`)

Create \`rmsn\_project/rmsn\_core.py\` containing the production-hardened implementation below:

\`\`\`python  
import math  
import torch  
import torch.nn as nn  
import torch.nn.functional as F  
import triton  
import triton.language as tl

\# \==============================================================================  
\# 1\. TRITON PARALLEL ASSOCIATIVE SCAN (FORWARD \+ ANALYTICAL ADJOINT BACKWARD)  
\# Solves h\_t \= a\_t \* h\_{t-1} \+ b\_t in O(N log N) work and O(log N) depth  
\# \==============================================================================

@triton.jit  
def \_complex\_scan\_op(a\_r1, a\_i1, b\_r1, b\_i1, a\_r2, a\_i2, b\_r2, b\_i2):  
    \# Associative composition: (a2, b2) o (a1, b1) \= (a2 \* a1, a2 \* b1 \+ b2)  
    out\_ar \= a\_r2 \* a\_r1 \- a\_i2 \* a\_i1  
    out\_ai \= a\_r2 \* a\_i1 \+ a\_i2 \* a\_r1  
    out\_br \= a\_r2 \* b\_r1 \- a\_i2 \* b\_i1 \+ b\_r2  
    out\_bi \= a\_r2 \* b\_i1 \+ a\_i2 \* b\_r1 \+ b\_i2  
    return out\_ar, out\_ai, out\_br, out\_bi

@triton.jit  
def \_parallel\_complex\_scan\_fwd\_kernel(  
    Ar\_ptr, Ai\_ptr, Br\_ptr, Bi\_ptr,  
    Hr\_ptr, Hi\_ptr,  
    seq\_len,  
    BLOCK\_SIZE: tl.constexpr  
):  
    pid \= tl.program\_id(0)  
    base \= pid \* seq\_len  
    offs \= tl.arange(0, BLOCK\_SIZE)  
    mask \= offs \< seq\_len

    ar \= tl.load(Ar\_ptr \+ base \+ offs, mask=mask, other=1.0)  
    ai \= tl.load(Ai\_ptr \+ base \+ offs, mask=mask, other=0.0)  
    br \= tl.load(Br\_ptr \+ base \+ offs, mask=mask, other=0.0)  
    bi \= tl.load(Bi\_ptr \+ base \+ offs, mask=mask, other=0.0)

    \_, \_, hr, hi \= tl.associative\_scan(  
        (ar, ai, br, bi), axis=0, combine\_fn=\_complex\_scan\_op  
    )

    tl.store(Hr\_ptr \+ base \+ offs, hr, mask=mask)  
    tl.store(Hi\_ptr \+ base \+ offs, hi, mask=mask)

@triton.jit  
def \_real\_scan\_op(a1, b1, a2, b2):  
    return a2 \* a1, a2 \* b1 \+ b2

@triton.jit  
def \_parallel\_real\_scan\_fwd\_kernel(  
    A\_ptr, B\_ptr, H\_ptr,  
    seq\_len,  
    BLOCK\_SIZE: tl.constexpr  
):  
    pid \= tl.program\_id(0)  
    base \= pid \* seq\_len  
    offs \= tl.arange(0, BLOCK\_SIZE)  
    mask \= offs \< seq\_len

    a \= tl.load(A\_ptr \+ base \+ offs, mask=mask, other=1.0)  
    b \= tl.load(B\_ptr \+ base \+ offs, mask=mask, other=0.0)

    \_, h \= tl.associative\_scan((a, b), axis=0, combine\_fn=\_real\_scan\_op)  
    tl.store(H\_ptr \+ base \+ offs, h, mask=mask)

class MetriplecticParallelScanFn(torch.autograd.Function):  
    @staticmethod  
    def forward(ctx, ar, ai, br, bi):  
        \# Shapes: (B, D, N) contiguous float32  
        B, D, N \= ar.shape  
        total\_streams \= B \* D  
        BLOCK\_SIZE \= triton.next\_power\_of\_2(N)

        ar\_c \= ar.contiguous()  
        ai\_c \= ai.contiguous()  
        br\_c \= br.contiguous()  
        bi\_c \= bi.contiguous()

        hr \= torch.empty\_like(br\_c)  
        hi \= torch.empty\_like(bi\_c)

        if ar.is\_cuda and BLOCK\_SIZE \<= 4096:  
            grid \= (total\_streams,)  
            \_parallel\_complex\_scan\_fwd\_kernel\[grid\](  
                ar\_c, ai\_c, br\_c, bi\_c, hr, hi,  
                seq\_len=N, BLOCK\_SIZE=BLOCK\_SIZE  
            )  
        else:  
            \# Exact reference fallback for CPU or ultra-long chunks  
            h\_r \= torch.zeros(B, D, device=ar.device, dtype=ar.dtype)  
            h\_i \= torch.zeros(B, D, device=ar.device, dtype=ar.dtype)  
            for t in range(N):  
                nh\_r \= ar\_c\[:, :, t\] \* h\_r \- ai\_c\[:, :, t\] \* h\_i \+ br\_c\[:, :, t\]  
                nh\_i \= ar\_c\[:, :, t\] \* h\_i \+ ai\_c\[:, :, t\] \* h\_r \+ bi\_c\[:, :, t\]  
                h\_r, h\_i \= nh\_r, nh\_i  
                hr\[:, :, t\] \= h\_r  
                hi\[:, :, t\] \= h\_i

        ctx.save\_for\_backward(ar\_c, ai\_c, hr, hi)  
        return hr, hi

    @staticmethod  
    def backward(ctx, grad\_hr, grad\_hi):  
        ar, ai, hr, hi \= ctx.saved\_tensors  
        B, D, N \= ar.shape  
        total\_streams \= B \* D  
        BLOCK\_SIZE \= triton.next\_power\_of\_2(N)

        \# Reverse-time adjoint recurrence:  
        \# g\_t \= dL/dh\_t \+ conj(a\_{t+1}) \* g\_{t+1}  
        \# Flip sequence to use forward associative scan  
        ar\_shift \= torch.cat(\[ar\[:, :, 1:\], torch.zeros\_like(ar\[:, :, :1\])\], dim=-1)  
        ai\_shift \= torch.cat(\[-ai\[:, :, 1:\], torch.zeros\_like(ai\[:, :, :1\])\], dim=-1) \# conjugate

        ar\_rev \= torch.flip(ar\_shift, dims=\[-1\]).contiguous()  
        ai\_rev \= torch.flip(ai\_shift, dims=\[-1\]).contiguous()  
        gbr\_rev \= torch.flip(grad\_hr, dims=\[-1\]).contiguous()  
        gbi\_rev \= torch.flip(grad\_hi, dims=\[-1\]).contiguous()

        gr\_rev \= torch.empty\_like(gbr\_rev)  
        gi\_rev \= torch.empty\_like(gbi\_rev)

        if ar.is\_cuda and BLOCK\_SIZE \<= 4096:  
            grid \= (total\_streams,)  
            \_parallel\_complex\_scan\_fwd\_kernel\[grid\](  
                ar\_rev, ai\_rev, gbr\_rev, gbi\_rev, gr\_rev, gi\_rev,  
                seq\_len=N, BLOCK\_SIZE=BLOCK\_SIZE  
            )  
        else:  
            g\_r \= torch.zeros(B, D, device=ar.device, dtype=ar.dtype)  
            g\_i \= torch.zeros(B, D, device=ar.device, dtype=ar.dtype)  
            for t in range(N):  
                ng\_r \= ar\_rev\[:, :, t\] \* g\_r \- ai\_rev\[:, :, t\] \* g\_i \+ gbr\_rev\[:, :, t\]  
                ng\_i \= ar\_rev\[:, :, t\] \* g\_i \+ ai\_rev\[:, :, t\] \* g\_r \+ gbi\_rev\[:, :, t\]  
                g\_r, g\_i \= ng\_r, ng\_i  
                gr\_rev\[:, :, t\] \= g\_r  
                gi\_rev\[:, :, t\] \= g\_i

        grad\_br \= torch.flip(gr\_rev, dims=\[-1\])  
        grad\_bi \= torch.flip(gi\_rev, dims=\[-1\])

        \# dL/da\_t \= g\_t \* conj(h\_{t-1})  
        hr\_prev \= torch.cat(\[torch.zeros\_like(hr\[:, :, :1\]), hr\[:, :, :-1\]\], dim=-1)  
        hi\_prev \= torch.cat(\[torch.zeros\_like(hi\[:, :, :1\]), hi\[:, :, :-1\]\], dim=-1)

        grad\_ar \= grad\_br \* hr\_prev \+ grad\_bi \* hi\_prev  
        grad\_ai \= grad\_bi \* hr\_prev \- grad\_br \* hi\_prev

        return grad\_ar, grad\_ai, grad\_br, grad\_bi

def parallel\_metriplectic\_scan(ar, ai, br, bi):  
    orig\_dtype \= ar.dtype  
    hr, hi \= MetriplecticParallelScanFn.apply(  
        ar.float(), ai.float(), br.float(), bi.float()  
    )  
    return hr.to(orig\_dtype), hi.to(orig\_dtype)

\# \==============================================================================  
\# 2\. CLIFFORD Cl(3,0) FIBER-BUNDLE STALK & SHEAF CONNECTION MODULE  
\# Norm-preserving Rodrigues sandwich product R \* Psi \* R^\\dagger \+ Sheaf Shift  
\# \==============================================================================

class CliffordStalkBundle(nn.Module):  
    def \_\_init\_\_(self, embed\_dim: int):  
        super().\_\_init\_\_()  
        assert embed\_dim % 8 \== 0, "embed\_dim must be divisible by 8 for Cl(3,0) stalks."  
        self.embed\_dim \= embed\_dim  
        self.num\_stalks \= embed\_dim // 8  
        \# Dynamic input-dependent gauge connection W\_theta  
        self.theta\_proj \= nn.Linear(8, 3, bias=True)  
        \# Sheaf Laplacian cross-stalk connection weight  
        self.sheaf\_mix \= nn.Parameter(torch.ones(1, 1, self.num\_stalks, 1\) \* 0.1)

    @staticmethod  
    def \_rodrigues\_rotate(v: torch.Tensor, u\_hat: torch.Tensor, cos\_t: torch.Tensor, sin\_t: torch.Tensor) \-\> torch.Tensor:  
        \# Exact norm-preserving sandwich product R v R^\\dagger in Cl(3,0)  
        dot \= torch.sum(u\_hat \* v, dim=-1, keepdim=True)  
        cross \= torch.cross(u\_hat, v, dim=-1)  
        return v \* cos\_t \+ cross \* sin\_t \+ u\_hat \* dot \* (1.0 \- cos\_t)

    def forward(self, x: torch.Tensor) \-\> torch.Tensor:  
        B, N, D \= x.shape  
        psi \= x.view(B, N, self.num\_stalks, 8\)

        scalar \= psi\[..., 0:1\]      \# Grade 0 (1)  
        vectors \= psi\[..., 1:4\]     \# Grade 1 (3)  
        bivectors \= psi\[..., 4:7\]   \# Grade 2 (3)  
        pseudo \= psi\[..., 7:8\]      \# Grade 3 (1)

        \# Input-dependent bivector rotation angles per token & stalk  
        theta \= torch.tanh(self.theta\_proj(psi)) \* math.pi  \# (B, N, C, 3\)  
        theta\_norm \= torch.norm(theta, dim=-1, keepdim=True) \+ 1e-8  
        u\_hat \= theta / theta\_norm  
        cos\_t \= torch.cos(theta\_norm)  
        sin\_t \= torch.sin(theta\_norm)

        rot\_v \= self.\_rodrigues\_rotate(vectors, u\_hat, cos\_t, sin\_t)  
        rot\_b \= self.\_rodrigues\_rotate(bivectors, u\_hat, cos\_t, sin\_t)

        transported \= torch.cat(\[scalar, rot\_v, rot\_b, pseudo\], dim=-1)

        \# Cellular Sheaf cyclic stalk parallel transport (inter-stalk diffusion)  
        shifted\_stalks \= torch.roll(transported, shifts=1, dims=2)  
        sheaf\_out \= transported \+ torch.tanh(self.sheaf\_mix) \* (shifted\_stalks \- transported)  
        return sheaf\_out.view(B, N, D)

\# \==============================================================================  
\# 3\. FRACTIONAL CAPUTO MEMORY BANK (PARALLELIZED MULTI-POLE SCAN)  
\# \==============================================================================

class FractionalCaputoBank(nn.Module):  
    def \_\_init\_\_(self, dim: int, num\_modes: int \= 8):  
        super().\_\_init\_\_()  
        assert dim % num\_modes \== 0, "dim must be divisible by num\_modes."  
        self.dim \= dim  
        self.num\_modes \= num\_modes  
        self.channels\_per\_mode \= dim // num\_modes

        \# Partition channels across log-spaced poles to avoid 8x memory expansion  
        poles \= torch.logspace(-3.5, \-0.1, steps=num\_modes)  
        self.log\_poles \= nn.Parameter(torch.log(poles))  
        self.mode\_weights \= nn.Parameter(torch.ones(1, 1, num\_modes, 1))  
        self.proj \= nn.Linear(dim, dim)

    def forward(self, x: torch.Tensor) \-\> torch.Tensor:  
        B, N, D \= x.shape  
        poles \= torch.exp(self.log\_poles).view(1, self.num\_modes, 1, 1\) \# (1, M, 1, 1\)  
        decay \= torch.exp(-poles).expand(B, self.num\_modes, self.channels\_per\_mode, N).reshape(B, D, N)  
        zero\_imag \= torch.zeros\_like(decay)

        x\_t \= x.transpose(1, 2).contiguous() \# (B, D, N)  
        drive \= (1.0 \- decay) \* x\_t

        \# Execute in O(N log N) via the fused scan kernel  
        h\_real, \_ \= parallel\_metriplectic\_scan(decay, zero\_imag, drive, zero\_imag)  
        h\_out \= h\_real.transpose(1, 2).view(B, N, self.num\_modes, self.channels\_per\_mode)  
        weighted \= (h\_out \* F.softplus(self.mode\_weights)).view(B, N, D)  
        return self.proj(weighted)

\# \==============================================================================  
\# 4\. CAUSAL TROPHIC GLOBAL WORKSPACE BOTTLENECK  
\# Strictly causal O(N \* M\_w) prefix blackboard with Lotka-Volterra competition  
\# \==============================================================================

class CausalTrophicGlobalWorkspace(nn.Module):  
    def \_\_init\_\_(self, dim: int, num\_slots: int \= 32, slot\_dim: int \= 256):  
        super().\_\_init\_\_()  
        self.num\_slots \= num\_slots  
        self.slot\_dim \= slot\_dim  
        self.workspace\_slots \= nn.Parameter(torch.randn(num\_slots, slot\_dim) \* 0.02)  
        self.interaction\_matrix \= nn.Parameter(torch.eye(num\_slots) \+ 0.1 \* torch.ones(num\_slots, num\_slots))  
        self.write\_proj \= nn.Linear(dim, slot\_dim, bias=False)  
        self.read\_proj \= nn.Linear(slot\_dim, dim, bias=False)  
        self.gate \= nn.Linear(dim, dim)

    def forward(self, x: torch.Tensor):  
        B, N, D \= x.shape  
        u \= self.write\_proj(x)  \# (B, N, slot\_dim)

        \# Affinity scores against baseline workspace prototypes: (B, N, M\_w)  
        affinity \= torch.einsum('bnd,md-\>bnm', u, self.workspace\_slots) / math.sqrt(self.slot\_dim)

        \# Lotka-Volterra lateral inhibition across slots  
        lv\_matrix \= F.softplus(self.interaction\_matrix)  
        inhibition \= torch.einsum('bnm,mk-\>bnk', affinity, lv\_matrix)  
        bidding\_weights \= F.softmax(affinity \- 0.1 \* inhibition, dim=-1) \# (B, N, M\_w)

        \# CAUSAL Write Phase: Token t only aggregates workspace writes from tokens \<= t  
        \# Outer product per step: (B, N, M\_w, slot\_dim) accumulated via prefix sum  
        weighted\_u \= bidding\_weights.unsqueeze(-1) \* u.unsqueeze(2)  
        causal\_coalition \= torch.cumsum(weighted\_u, dim=1)  
        normalizer \= torch.cumsum(bidding\_weights, dim=1).unsqueeze(-1) \+ 1e-6  
        causal\_slots \= 0.9 \* self.workspace\_slots.view(1, 1, self.num\_slots, self.slot\_dim) \+ 0.1 \* (causal\_coalition / normalizer)

        \# CAUSAL Broadcast Phase: Read from time-local workspace state at step t  
        broadcast\_info \= torch.einsum('bnm,bnmd-\>bnd', bidding\_weights, causal\_slots)  
        broadcast\_features \= self.read\_proj(broadcast\_info)

        \# Compute Lotka-Volterra slot entropy for telemetry  
        slot\_probs \= bidding\_weights.mean(dim=(0, 1))  
        ws\_entropy \= \-torch.sum(slot\_probs \* torch.log(slot\_probs \+ 1e-8))

        return torch.sigmoid(self.gate(x)) \* broadcast\_features, ws\_entropy

\# \==============================================================================  
\# 5\. INTEGRATED RMSN LAYER (WITH PHASE-PRESERVING NOETHER CURRENTS)  
\# \==============================================================================

class RMSNLayer(nn.Module):  
    def \_\_init\_\_(self, dim: int, num\_slots: int \= 32):  
        super().\_\_init\_\_()  
        self.dim \= dim  
        self.norm1 \= nn.RMSNorm(dim)  
        self.norm2 \= nn.RMSNorm(dim)

        self.clifford \= CliffordStalkBundle(dim)  
        self.omega\_proj \= nn.Linear(dim, dim)  
        self.gamma\_proj \= nn.Linear(dim, dim)  
        self.in\_proj \= nn.Linear(dim, dim)

        \# Readout combines Re(h), Im(h), and bounded Noether energy density T^00  
        self.noether\_readout \= nn.Linear(dim \* 3, dim)

        self.fractional\_bank \= FractionalCaputoBank(dim, num\_modes=8)  
        self.workspace \= CausalTrophicGlobalWorkspace(dim, num\_slots=num\_slots, slot\_dim=min(256, dim))

    def forward(self, x: torch.Tensor):  
        residual \= x  
        x\_norm \= self.norm1(x)

        \# Stage 1: Multivector Clifford gauge rotation & sheaf transport  
        x\_cliff \= self.clifford(x\_norm)

        \# Stage 2: Second-order port-metriplectic wave integration  
        omega \= F.softplus(self.omega\_proj(x\_cliff))  
        gamma \= F.softplus(self.gamma\_proj(x\_cliff)) \+ 1e-3  \# Strict Lyapunov dissipation \> 0  
        u\_in \= self.in\_proj(x\_cliff)

        dt \= 0.05  
        decay \= torch.exp(-gamma \* dt)  
        ar \= (decay \* torch.cos(omega \* dt)).transpose(1, 2\)  
        ai \= (decay \* torch.sin(omega \* dt)).transpose(1, 2\)  
        br \= (u\_in \* dt).transpose(1, 2\)  
        bi \= torch.zeros\_like(br)

        hr, hi \= parallel\_metriplectic\_scan(ar, ai, br, bi)  
        hr\_t \= hr.transpose(1, 2\)  
        hi\_t \= hi.transpose(1, 2\)

        \# Conserved Noether Energy Density T^00 \+ Phase-preserving field projections  
        noether\_energy \= torch.tanh(hr\_t \*\* 2 \+ hi\_t \*\* 2\)  
        field\_state \= torch.cat(\[hr\_t, hi\_t, noether\_energy\], dim=-1)  
        dynamic\_out \= self.noether\_readout(field\_state)  
        x \= residual \+ dynamic\_out

        \# Stage 3: Fractional long-memory and causal cognitive workspace routing  
        residual2 \= x  
        x\_norm2 \= self.norm2(x)  
        frac\_mem \= self.fractional\_bank(x\_norm2)  
        ws\_out, ws\_entropy \= self.workspace(x\_norm2)

        x \= residual2 \+ frac\_mem \+ ws\_out

        telemetry \= {  
            "max\_lyapunov": float((-gamma).max().item()),  
            "mean\_energy": float((hr\_t \*\* 2 \+ hi\_t \*\* 2).mean().item()),  
            "ws\_entropy": float(ws\_entropy.item())  
        }  
        return x, telemetry

\# \==============================================================================  
\# 6\. RESONANT METRIPLECTIC SHEAF LANGUAGE MODEL  
\# \==============================================================================

class ResonantMetriplecticSheafLM(nn.Module):  
    def \_\_init\_\_(self, vocab\_size: int \= 32000, dim: int \= 512, depth: int \= 6, num\_slots: int \= 32):  
        super().\_\_init\_\_()  
        self.vocab\_size \= vocab\_size  
        self.dim \= dim  
        self.depth \= depth

        self.token\_embed \= nn.Embedding(vocab\_size, dim)  
        self.layers \= nn.ModuleList(\[  
            RMSNLayer(dim=dim, num\_slots=num\_slots) for \_ in range(depth)  
        \])  
        self.final\_norm \= nn.RMSNorm(dim)  
        self.lm\_head \= nn.Linear(dim, vocab\_size, bias=False)  
        self.lm\_head.weight \= self.token\_embed.weight

    def forward(self, input\_ids: torch.Tensor, return\_telemetry: bool \= False):  
        x \= self.token\_embed(input\_ids)  
        last\_telemetry \= {}  
        for layer in self.layers:  
            x, last\_telemetry \= layer(x)  
        x \= self.final\_norm(x)  
        logits \= self.lm\_head(x)  
        if return\_telemetry:  
            return logits, last\_telemetry  
        return logits

\`\`\`

\---

\#\#\# STAGE 3: Create Forensic Verification Suite (\`rmsn\_project/tests/test\_forensics.py\`)

Write \`rmsn\_project/tests/test\_forensics.py\` and run it to prove that all 5 physical and algorithmic invariants hold:

1\. \*\*Triton Associative Scan Exactness:\*\* Verify \`parallel\_metriplectic\_scan\` matches sequential PyTorch recurrence within \`atol=1e-4\` on both forward values and backward gradients (\`omega\`, \`gamma\`, \`u\_in\`).  
2\. \*\*Strict Autoregressive Causality Test:\*\* Feed a random sequence \`tokens\`, compute logits at position \`t \= N // 2\`, then corrupt all future tokens \`tokens\[:, t+1:\] \= 0\` and assert that \`logits\[:, :t+1\]\` remain bit-for-bit identical (\`max\_diff \< 1e-5\`).  
3\. \*\*Clifford Rotor Norm Conservation:\*\* Assert that \`CliffordStalkBundle.\_rodrigues\_rotate\` preserves the Euclidean norm of Grade-1 vectors and Grade-2 bivectors to \`\< 1e-5\`.  
4\. \*\*Lyapunov Dissipative Passivity:\*\* Verify that across all layers, \`max\_lyapunov \< 0\`.

\---

\#\#\# STAGE 4: Execute Benchmark & Telemetry Report (\`rmsn\_project/benchmarks/run\_bench.py\`)

Create \`rmsn\_project/benchmarks/run\_bench.py\` that trains \`ResonantMetriplecticSheafLM\` for 50 optimization steps on a synthetic associative recall / periodic wave sequence task (and optionally a real text shard if available), logging:

\* Hardware device name and actual physical VRAM vs. peak allocated VRAM.  
\* Throughput in tokens/sec.  
\* Loss convergence curve from Step 1 to Step 50\.  
\* Physical invariant telemetry (\`max\_lyapunov\`, \`mean\_energy\`, \`ws\_entropy\`).

Run \`pytest\` or \`python3 rmsn\_project/tests/test\_forensics.py\` followed by \`python3 rmsn\_project/benchmarks/run\_bench.py\` and print the final verification summary table.

\`\`\`

\---

\#\#\# Summary of Hardened Upgrades Included for Archon

\| Subsystem \| Original Manuscript Bug \| Hardened Fix in Archon Payload \|  
\| :--- \| :--- \| :--- \|  
\| \*\*Triton Scan Kernel\*\* \| Read un-updated global pointers inside \`while\` loop; lacked \`autograd.Function\`\[cite: 1\] \| Uses native \`tl.associative\_scan\` in SRAM \+ analytical time-reversed adjoint scan in \`backward()\` \|  
\| \*\*Global Workspace\*\* \| Non-causal sum \`einsum('bnm,bnd-\>bmd')\` leaked future tokens $t>\tau$\[cite: 1\] \| Prefix-summed outer product (\`torch.cumsum\`) ensures strict causal masking in $O(N\cdot {M}_{w})$ \|  
\| \*\*Clifford $Cl(3,0)$ Stalk\*\* \| Static $\theta$, incomplete half-angle cross product broke vector norms\[cite: 1\] \| Token-dynamic ${\theta }_{t}=\pi \tanh ({W}_{\theta }{\Psi }_{t})$, full Rodrigues sandwich on grades 1 & 2, plus cyclic sheaf shift \|  
\| \*\*Fractional Caputo Bank\*\* \| Sequential Python loop \`for t in range(N):\` and $8\times$ tensor \`.repeat()\`\[cite: 1\] \| Channel-partitioned multi-pole bank fused directly into \`parallel\_metriplectic\_scan\` \|  
\| \*\*Noether Readout\*\* \| \$\\vert{}h\\vert{}^2\$ erased wave phase and vanished gradients near 0\[cite: 1\] \| Concatenates \$\[\\text{Re}(h), \\text{Im}(h), \\tanh(\\vert{}h\\vert{}^2)\]\$ before linear projection \|

\<FollowUp label="Want a pure-Triton backward kernel for sequences beyond 4,096 tokens?" query="Write a multi-block segmented Triton associative scan kernel that carries prefix states across L2 cache for sequence lengths N"\> 4096." /\>

\`\`\`  
