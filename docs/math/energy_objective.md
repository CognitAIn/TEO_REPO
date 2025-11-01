# Energy-Aware Objective

Minimize over time t:  
J = Σ_t [ L(t) + λ·P(t) + β·Var(L)_t ]

Where  
- L: latency  
- P: power  
- Var(L): latency variance (jitter)  
- λ, β: control weights  

Stable update:  
uₜ = clip(K·eₜ, −α·Δₜ₋₁, α·Δₜ₋₁)
