# Parameter Calibration Guide

How to set model parameters from real market data.

---

## sigma — Price Volatility

sigma is the per-hour standard deviation of mid-price returns (not annualized).

**From daily vol:**

  sigma_hourly = sigma_daily / sqrt(6.5)

**From intraday data:**

  sigma_hourly = std(hourly log-returns) * price

**Typical ranges:**
  - Large-cap (AAPL, MSFT): 0.8-1.5% per hour in normal conditions
  - Small-cap / high-beta: 2-4% per hour
  - Earnings / macro event: 5-15% per hour (use realized vol, not historical)

**Regime check**: If current realized vol is 2x historical, double sigma. The Almgren-Chriss variance is quadratic in sigma, so underestimating it by 2x understates timing risk by 4x.

---

## gamma — Permanent Impact Coefficient

gamma is dollars of permanent price change per share executed (regardless of speed).

**Almgren et al. (2005) estimate:**

  gamma ~ 0.1 * sigma / (V * sqrt(T_day))

where V is average daily volume (shares) and T_day is the trading horizon as a fraction of a day.

**Typical ranges:**
  - S&P 500 stocks: 1e-7 to 1e-5 ($/share per share)
  - Illiquid mid-cap: 1e-5 to 1e-4
  - Very illiquid: >1e-4

**Rule of thumb**: Executing 1% of average daily volume in one slice should move the price ~1-2 bps permanently. Use that to back out gamma.

**Calibration from IS data:**
  Regress realized IS against cumulative shares executed. The slope is gamma.

---

## eta — Temporary Impact Coefficient

eta is the dollar cost per (share / time) of trading rate. Units: $/share per (shares/hour).

**From Almgren-Chriss:**

  eta ~ 0.01 * sigma * sqrt(T_day / V)

**Intuition**: eta controls the cost of demanding liquidity now vs. later.
  - Tight spread, deep book (liquid): small eta
  - Wide spread, thin book: large eta

**Typical ranges:**
  - Mega-cap (SPY, AAPL): 5e-6 to 5e-5
  - Large-cap: 1e-5 to 2e-4
  - Mid-cap: 1e-4 to 5e-4

**From trade data**: Run several executions at different rates. Regress slippage on shares/time. The slope is eta.

---

## lambda — Risk Aversion

lambda is derived from your alpha signal half-life h:

  lambda = eta / (h^2 * sigma^2)

**Signal half-life guidelines:**

  | Signal Type          | Half-life       | lambda (typical) | Execution style |
  |----------------------|-----------------|------------------|-----------------|
  | HFT / microstructure | 5-10 minutes    | >10              | Very aggressive |
  | Momentum             | 30-60 minutes   | 1-5              | Aggressive      |
  | Intraday mean rev.   | 1-3 hours       | 0.2-1.0          | Moderate        |
  | Overnight / swing    | 1-2 days        | 0.01-0.1         | Passive         |
  | Value / fundamental  | Weeks-months    | <0.01            | Very passive    |
  | Index rebalancing    | Known date/time | ~0               | Pure TWAP       |

**Manual override**: If you do not have an alpha signal, set lambda = 0 for pure cost minimization (TWAP), or choose lambda to achieve a target kappa directly.

---

## N — Number of Execution Slices

N trades off scheduling granularity vs. market impact of each slice.

**Practical considerations:**
  - More slices = smaller per-slice impact, smoother trajectory
  - Fewer slices = fewer market orders, lower latency overhead
  - For T = 4 hours, N = 16 gives 15-minute slices (standard for institutional algos)
  - For T = 1 hour, N = 12 gives 5-minute slices

**Optimal slice size** rule of thumb: each slice should be <5% of average volume in that period. If n_k / V_k > 0.05, reduce N or extend the horizon T.

---

## Putting It Together — Example

AAPL buy order, momentum signal, 4-hour horizon:

  Price: 85, ADV: 55M shares, daily vol: 1.3%
  Signal half-life: 45 minutes = 0.75 hours

  sigma = 1.3% / sqrt(6.5) = 0.51% per hour = 0.0051

  gamma = 0.1 * 0.0051 / (55e6 * sqrt(4/6.5)) = ~5e-9  (very liquid, expect small perm impact)
  eta   = 0.01 * 0.0051 * sqrt((4/6.5) / 55e6) = ~7e-8

  lambda = eta / (h^2 * sigma^2) = 7e-8 / (0.75^2 * 0.0051^2) = ~4.8
  kappa  = sqrt(4.8 * 0.0051^2 / 7e-8) = ~1.35 per hour

  => Aggressive front-loading: ~40% of order in first hour.

---

## Common Pitfalls

1. **Units mismatch**: Make sure sigma, T, and h are in the same time units (hours throughout, or minutes throughout).
2. **Static vol in volatile regimes**: Use 5-day realized vol near earnings or macro events.
3. **Ignoring ADV check**: If your order is >5-10% of ADV, the linear impact model breaks down. Use nonlinear extensions.
4. **Confusing temporary and permanent**: Temporary impact affects only your fill price. Permanent impact shifts the market permanently — it raises the cost of every subsequent slice.
5. **Misinterpreting lambda=0**: Risk-neutral does not mean zero cost. It means you minimize expected cost only, accepting unlimited variance. You will still pay permanent and temporary impact.
