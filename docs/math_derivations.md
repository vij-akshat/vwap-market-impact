# Mathematical Derivations

Full proofs for all models implemented in *VWAP Market Impact & Almgren-Chriss Optimal Execution*.

---

## 1. VWAP Schedule

### Setup

Let Q be total shares to execute. The intraday volume profile gives expected volume V_k in each of N periods. Participation weights: w_k = V_k / sum_j V_j.

The VWAP participation schedule sets n_k = Q * w_k. This achieves expected fill equal to the market VWAP since VWAP_exec = sum_k P_k * n_k / Q = sum_k P_k * w_k = market VWAP.

---

## 2. Market Impact Model

### Temporary Impact

Depends on instantaneous trading rate v(t) = -x_dot(t), reverts after execution:

  Delta_S_temp(t) = eta * v(t)

Total temporary cost over schedule {n_k} with period tau = T/N:

  C_temp = (eta/tau) * sum_k n_k^2

### Permanent Impact

Accumulates from all prior execution, never reverts:

  Delta_S_perm(t) = gamma * X(t),  X(t) = integral_0^t v(s) ds

Each slice n_k pays permanent impact from all prior slices:

  C_perm = gamma * sum_k n_k * X_{k-1}  ~  gamma * Q^2 / 2

Permanent impact is approximately strategy-independent, which is why it drops out of the Almgren-Chriss optimization.

---

## 3. Almgren-Chriss Optimal Trajectory

### Problem

  min_{x(t)}  eta * integral_0^T x_dot^2 dt  +  lambda * sigma^2 * integral_0^T x^2 dt

subject to x(0) = Q, x(T) = 0.

lambda >= 0 is the risk aversion coefficient.

### Euler-Lagrange Equation

Lagrangian: L(x, x_dot) = eta * x_dot^2 + lambda * sigma^2 * x^2

Euler-Lagrange: dL/dx - d/dt(dL/dx_dot) = 0

  2*lambda*sigma^2*x - 2*eta*x_ddot = 0
  => x_ddot = kappa^2 * x,  kappa = sqrt(lambda * sigma^2 / eta)

### Solution

General solution: x(t) = C*cosh(kappa*t) + D*sinh(kappa*t)

Boundary conditions:
  x(0) = Q  =>  C = Q
  x(T) = 0  =>  D = -Q * coth(kappa*T)

Applying sinh(A-B) identity:

  x*(t) = Q * sinh(kappa*(T-t)) / sinh(kappa*T)

Optimal trading rate:

  v*(t) = Q * kappa * cosh(kappa*(T-t)) / sinh(kappa*T)

Front-loaded for kappa > 0.

### Limiting Cases

Risk-neutral (kappa -> 0): L-Hopital gives x*(t) = Q*(1 - t/T), uniform TWAP.

Infinitely risk-averse (kappa -> inf): x*(t) -> 0 for t > 0, immediate execution.

---

## 4. Timing Risk (Variance)

  Var[Cost] = sigma^2 * tau * sum_k x_k^2

Each period k contributes sigma^2*tau variance; exposure is x_k shares remaining.

---

## 5. Lambda from Alpha Decay

Signal half-life h implies target kappa = 1/h.

Inverting kappa = sqrt(lambda*sigma^2/eta):

  lambda = eta / (h^2 * sigma^2)

Comparative statics:
  - Faster decay (h down) => larger lambda => more front-loading
  - Higher vol (sigma up) => smaller lambda => execute more slowly
  - Larger temp impact (eta up) => larger lambda => execute faster

---

## 6. Implementation Shortfall

  IS = VWAP_exec - S_decision

Expected IS (buy order):

  E[IS] = (C_perm + C_temp) / Q = gamma*Q/2 + (eta / (tau*Q)) * sum_k n_k^2

Std[IS] = sqrt(Var[Cost]) / Q

Calibration: compare IS_realized / E[IS_model].
  ~1   => well-calibrated
  <<1  => overestimated impact (reduce gamma, eta)
  >>1  => underestimated impact (increase gamma, eta)
