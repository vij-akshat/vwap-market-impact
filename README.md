# VWAP Market Impact & Almgren-Chriss Optimal Execution

**Optimal execution from first principles — VWAP benchmarking, market impact decomposition, and the Almgren-Chriss cost-risk frontier**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-ff4b4b)](https://vwap-market-impact-dvvttdr9gkfnmdchdcv6d2.streamlit.app)

**[Open Live App](https://vwap-market-impact-dvvttdr9gkfnmdchdcv6d2.streamlit.app)**

---

## Overview

Large orders cannot be executed in a single market order without significant price impact. Optimal execution theory asks: given a fixed order, what trading trajectory minimizes a combination of expected market impact cost and timing risk?

This project covers the complete answer — from derivation to interactive simulation — across a Jupyter notebook and a Streamlit trading terminal.

**Key deliverables:**

| Component | Contents |
|---|---|
| Notebook | VWAP derivation, market impact theory, full Almgren-Chriss proof, efficient frontier, IS measurement |
| Streamlit app | Interactive execution desk: order ticket, trajectory explorer, cost-risk frontier, post-trade report |
|  | Step-by-step proofs: E-L equation, sinh trajectory, limiting cases, IS decomposition |
|  | How to calibrate sigma, gamma, eta, lambda from real market data |

---

## Theory Summary

### VWAP Schedule

Distribute an order proportional to expected intraday volume:

  n_k = Q * V_k / sum_j V_j

Expected fill equals the market VWAP — a fair-price benchmark, not a cost-minimizing strategy.

### Market Impact

Two additive components:

- **Temporary** (eta * trading_rate): reflects bid-ask spread and immediate liquidity demand; reverts after execution
- **Permanent** (gamma * cumulative_executed): reflects information content; never reverts

### Almgren-Chriss Objective

  min_{x(t)}  eta * integral x_dot^2 dt  +  lambda * sigma^2 * integral x^2 dt

subject to x(0) = Q, x(T) = 0.

### Optimal Trajectory (Euler-Lagrange)

  x*(t) = Q * sinh(kappa*(T-t)) / sinh(kappa*T),   kappa = sqrt(lambda*sigma^2 / eta)

Limiting cases: lambda=0 gives uniform TWAP; lambda->inf gives immediate execution.

### Lambda from Alpha Decay

Match execution urgency to signal half-life h:

  lambda = eta / (h^2 * sigma^2)

### Implementation Shortfall

  IS = VWAP_exec - S_decision

Decomposed into permanent impact, temporary impact, and timing noise for TCA and model calibration.

---

## Repository Structure

    vwap-market-impact/
    ├── app.py                        # Streamlit execution terminal
    ├── vwap-market-impact.ipynb      # Full derivation notebook
    ├── requirements.txt
    ├── LICENSE
    └── docs/
        ├── math_derivations.md       # Full proofs
        └── parameter_guide.md        # Calibration guide

---

## Quick Start

    git clone https://github.com/vij-akshat/vwap-market-impact.git
    cd vwap-market-impact
    pip install -r requirements.txt
    streamlit run app.py

---

## Streamlit App

Five-panel execution desk with a dark terminal aesthetic:

| Tab | Contents |
|---|---|
| Execution Analytics | Trajectory vs TWAP, fill scatter on price path, front-loaded schedule bars, cost breakdown |
| Cost-Risk Frontier | Full efficient frontier, kappa vs lambda, front-loading curve, sample-point table |
| Market Impact | Cost vs number of slices, scenario cards for HFT through value signals |
| VWAP Schedule | U-shaped volume profile, participation schedule, AC vs TWAP comparison |
| Trade Report | Order ticket, pre-trade analytics, post-trade IS attribution, slice-by-slice execution log |

**Sidebar controls:** ticker, side, shares, decision price, horizon, slices, sigma/gamma/eta, signal type (auto-derives lambda from alpha half-life), random seed.

---

## Notebook

 covers:

1. VWAP definition and schedule generation
2. Temporary and permanent impact cost functions
3. Almgren-Chriss problem formulation
4. Euler-Lagrange derivation and closed-form solution
5. Limiting cases (TWAP and immediate execution)
6. Cost-risk efficient frontier
7. Lambda selection from alpha half-life
8. Implementation shortfall measurement
9. Complete simulation workflow
10. Extensions: transient impact, stochastic control, limit orders, multi-asset, reinforcement learning

---

## Extensions Covered

- **Obizhaeva-Wang transient impact**: exponentially decaying price impact
- **Cartea-Jaimungal stochastic control**: HJB-based adaptive policies
- **Guéant-Lehalle limit orders**: optimal posting under adverse selection
- **Multi-asset portfolios**: matrix-valued impact with cross-asset effects
- **Reinforcement learning**: DDQN-based execution policies

---

## References

1. Almgren, R. & Chriss, N. (2000). *Optimal Execution of Portfolio Transactions.* Journal of Risk.
2. Almgren, R. et al. (2005). *Direct Estimation of Equity Market Impact.* Risk.
3. Gatheral, J. (2010). *No-Dynamic-Arbitrage and Market Impact.* Quantitative Finance.
4. Obizhaeva, A. & Wang, J. (2013). *Optimal Trading Strategy and Supply/Demand Dynamics.* Journal of Financial Markets.
5. Cartea, Á., Jaimungal, S. & Penalva, J. (2015). *Algorithmic and High-Frequency Trading.* Cambridge University Press.
6. Guéant, O., Lehalle, C.A. & Fernandez-Tapia, J. (2012). *Dealing with the Inventory Risk.* Mathematics and Financial Economics.
