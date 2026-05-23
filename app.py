"""
VWAP Market Impact & Almgren-Chriss Optimal Execution
Interactive Streamlit App
"""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="VWAP & Optimal Execution",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
C = {
    "primary":   "#2ecc71",
    "secondary": "#3498db",
    "accent":    "#e74c3c",
    "warn":      "#f39c12",
    "neutral":   "#95a5a6",
    "bg":        "#0e1117",
    "surface":   "#1c1c2e",
}

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .metric-box {
        background: #1c1c2e;
        border-left: 4px solid #2ecc71;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 6px 0;
    }
    .metric-label { color: #95a5a6; font-size: 0.78rem; letter-spacing: 0.05em; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 1.45rem; font-weight: 700; }
    .metric-sub   { color: #2ecc71; font-size: 0.82rem; margin-top: 2px; }
    .formula-box {
        background: #161b27;
        border: 1px solid #2ecc71;
        border-radius: 10px;
        padding: 16px 22px;
        margin: 10px 0 18px 0;
        font-family: monospace;
        font-size: 0.95rem;
        color: #e8e8e8;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #3498db;
        border-bottom: 1px solid #1c2d40;
        padding-bottom: 4px;
        margin: 18px 0 10px 0;
    }
    .insight-box {
        background: #12211a;
        border-left: 3px solid #2ecc71;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        color: #b8f0cc;
        font-size: 0.9rem;
        margin: 12px 0;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def metric_card(label, value, sub=""):
    st.markdown(
        f'<div class="metric-box">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def base_layout(title="", height=420, xl="", yl=""):
    return dict(
        template="plotly_dark",
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["bg"],
        height=height,
        title=dict(text=title, font=dict(size=15)),
        xaxis=dict(title=xl, gridcolor="#1e2a38"),
        yaxis=dict(title=yl, gridcolor="#1e2a38"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        margin=dict(l=50, r=20, t=50, b=50),
    )

# ─────────────────────────────────────────────
# MODEL FUNCTIONS
# ─────────────────────────────────────────────
def generate_vwap_schedule(total_shares, volume_profile):
    weights = volume_profile / volume_profile.sum()
    return total_shares * weights

def optimal_trajectory(Q, T, N, sigma, eta, lam):
    tau = T / N
    t = np.arange(N + 1) * tau
    if lam < 1e-12:
        return Q * (1 - t / T), 0.0
    kappa = np.sqrt(lam * sigma**2 / eta)
    traj = Q * np.sinh(kappa * (T - t)) / np.sinh(kappa * T)
    return traj, kappa

def perm_impact_cost(schedule, gamma):
    cost, cum = 0.0, 0.0
    for n in schedule:
        cost += gamma * n * cum
        cum += n
    return cost

def temp_impact_cost(schedule, tau, eta):
    return eta * np.sum(schedule**2 / tau)

def analyze(Q, T, N, sigma, gamma, eta, lam):
    tau = T / N
    traj, kappa = optimal_trajectory(Q, T, N, sigma, eta, lam)
    sched = -np.diff(traj)
    perm = perm_impact_cost(sched, gamma)
    temp = temp_impact_cost(sched, tau, eta)
    var  = sigma**2 * tau * np.sum(traj[1:]**2)
    return dict(
        kappa=kappa, trajectory=traj, schedule=sched,
        perm=perm, temp=temp, expected_cost=perm + temp,
        std_dev=np.sqrt(var), first_pct=sched[0] / Q * 100
    )

def suggest_lambda(halflife, sigma, eta):
    return eta / (halflife**2 * sigma**2)

def simulate(Q, T, N, S0, sigma, gamma, eta, lam, seed=42):
    np.random.seed(seed)
    tau = T / N
    r = analyze(Q, T, N, sigma, gamma, eta, lam)
    sched = r["schedule"]
    prices, path = [], [S0]
    price = S0
    for n in sched:
        price += gamma * n
        price += sigma * np.sqrt(tau) * np.random.randn() * price / 100
        prices.append(price + eta * (n / tau))
        path.append(price)
    prices = np.array(prices)
    vwap = np.sum(prices * sched) / Q
    return dict(
        pre=r, prices=prices, path=np.array(path),
        vwap=vwap, is_per_share=vwap - S0,
        is_total=(vwap - S0) * Q,
        is_bps=(vwap - S0) / S0 * 10000,
    )

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## VWAP & Optimal Execution")
    st.markdown("*Almgren-Chriss Framework*")
    st.divider()

    page = st.radio(
        "**Navigate**",
        ["Overview", "VWAP Schedule", "Market Impact", "Optimal Trajectory", "Execution Simulator"],
        index=0,
    )

    st.divider()
    st.markdown("### Order Parameters")
    Q      = st.number_input("Shares", min_value=1000, max_value=5_000_000, value=100_000, step=1000)
    S0     = st.number_input("Decision Price ($)", min_value=1.0, value=150.0, step=0.5)
    T      = st.slider("Horizon (hours)", 0.5, 8.0, 4.0, 0.5)
    N      = st.select_slider("Slices", [8, 12, 16, 24, 32, 48], value=16)

    st.divider()
    st.markdown("### Market Parameters")
    sigma  = st.slider("Volatility σ (%/hr)", 0.5, 5.0, 1.5, 0.1) / 100
    gamma  = st.slider("Perm. Impact γ (×10⁻⁶)", 1, 50, 5) * 1e-6
    eta    = st.slider("Temp. Impact η (×10⁻⁵)", 1, 20, 8) * 1e-5

    st.divider()
    st.markdown("### Alpha Signal")
    signal = st.selectbox("Signal Type", [
        "HFT / Microstructure (6 min)",
        "Momentum (30 min)",
        "Intraday Alpha (2 hr)",
        "Mean Reversion (8 hr)",
        "Value / Rebalancing",
        "Manual",
    ])
    HL_MAP = {
        "HFT / Microstructure (6 min)": 0.1,
        "Momentum (30 min)": 0.5,
        "Intraday Alpha (2 hr)": 2.0,
        "Mean Reversion (8 hr)": 8.0,
        "Value / Rebalancing": 40.0,
    }
    if signal == "Manual":
        lam = st.slider("Risk Aversion λ", 0.0, 50.0, 1.0, 0.1)
    else:
        lam = suggest_lambda(HL_MAP[signal], sigma, eta)
        st.metric("Derived λ", f"{lam:.4f}")

    st.divider()
    st.markdown("### Resources")
    st.markdown("[Math Derivations](docs/math_derivations.md)")
    st.markdown("[Parameter Guide](docs/parameter_guide.md)")

# ─────────────────────────────────────────────
# Pre-compute
# ─────────────────────────────────────────────
tau = T / N
t_pts = np.linspace(0, T, N + 1)
slice_mids = t_pts[:-1] + tau / 2
res = analyze(Q, T, N, sigma, gamma, eta, lam)

# ═══════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════
if page == "Overview":
    st.markdown("# VWAP Market Impact & Almgren-Chriss Optimal Execution")
    st.markdown("### From VWAP benchmarking to optimal execution trajectories")

    st.markdown("""
    Large orders cannot be filled in one shot without moving the market against you.
    This app implements the complete optimal execution framework, from the VWAP benchmark
    to the Almgren-Chriss mean-variance optimization.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="formula-box">VWAP Schedule<br><br>'
                    'n_k = Q · V_k / Σ V_j<br><br>'
                    'Tracks market volume profile</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="formula-box">Optimal Trajectory<br><br>'
                    'x*(t) = Q · sinh(κ(T−t)) / sinh(κT)<br><br>'
                    'κ = √(λσ²/η)</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="formula-box">Lambda from Signal<br><br>'
                    'λ = η / (h² · σ²)<br><br>'
                    'h = alpha half-life</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### The Core Tradeoff")
    st.markdown("""
    | Force | Effect | Formula |
    |---|---|---|
    | **Temporary impact** | Cost of trading fast | η · (n/τ)² |
    | **Timing risk** | Cost of trading slow | σ² · τ · Σ x_k² |
    | **Optimal balance** | Euler-Lagrange solution | x*(t) = sinh trajectory |

    The risk aversion parameter **λ** controls where you sit on this frontier.
    λ = 0 gives pure TWAP (minimize cost only). λ → ∞ gives immediate execution (minimize risk only).
    """)

    st.divider()
    # Quick metrics for current settings
    st.markdown("### Current Settings Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Expected Cost", f"${res['expected_cost']:,.0f}", f"λ = {lam:.3f}")
    with c2: metric_card("Cost Std Dev", f"±${res['std_dev']:,.0f}", "timing risk")
    with c3: metric_card("Urgency κ", f"{res['kappa']:.3f}", "1/hr")
    with c4: metric_card("First Slice", f"{res['first_pct']:.1f}%", "of total order")

    st.info("Use the sidebar to navigate to each section. All charts update live with your parameters.")

# ═══════════════════════════════════════════
# PAGE: VWAP SCHEDULE
# ═══════════════════════════════════════════
elif page == "VWAP Schedule":
    st.markdown("## VWAP Schedule")
    st.markdown("**Problem**: How do you distribute an order to track the market's VWAP?")
    st.markdown(r"""
    $$n_k = Q \cdot \frac{V_k}{\sum_j V_j}$$

    Executing proportional to expected volume gives an average fill equal to the market VWAP —
    a *fair price* benchmark. VWAP is not an optimization target; it's a reference.
    """)

    # Intraday volume profile
    hours = np.arange(9.5, 16.5, 0.5)
    vol_profile = np.array([1.5, 1.2, 0.9, 0.7, 0.6, 0.5, 0.5, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.8])
    vwap_sched = generate_vwap_schedule(Q, vol_profile)
    uniform_n = Q / len(vol_profile)

    st.markdown('<div class="section-header">Intraday Volume Profile (U-Shaped)</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Volume Profile", "VWAP Schedule", "vs TWAP Comparison"])

    with tab1:
        fig = go.Figure()
        bar_cols = [C["accent"] if h < 10.5 or h > 15.0 else C["secondary"] for h in hours]
        fig.add_trace(go.Bar(x=hours, y=vol_profile, marker_color=bar_cols,
                             name="Relative Volume",
                             hovertemplate="%{x:.1f}h: %{y:.2f}x avg<extra></extra>"))
        fig.add_hline(y=1.0, line=dict(color=C["neutral"], dash="dot", width=1.5),
                      annotation_text="Average", annotation_font_color=C["neutral"])
        fig.update_layout(**base_layout("Intraday Volume Profile", xl="Hour of Day", yl="Relative Volume"))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('<div class="insight-box">U-shaped profile: high volume at open (price discovery) '
                    'and close (rebalancing). Mid-day is thin. VWAP participation front- and back-loads '
                    'your order accordingly.</div>', unsafe_allow_html=True)

    with tab2:
        fig2 = go.Figure()
        sched_cols = [C["accent"] if s > uniform_n * 1.15 else
                      C["primary"] if s < uniform_n * 0.85 else C["secondary"]
                      for s in vwap_sched]
        fig2.add_trace(go.Bar(x=hours, y=vwap_sched, marker_color=sched_cols,
                              name="Shares to Execute",
                              hovertemplate="%{x:.1f}h: %{y:,.0f} shares (%{customdata:.1f}%)<extra></extra>",
                              customdata=vwap_sched / Q * 100))
        fig2.add_hline(y=uniform_n, line=dict(color=C["neutral"], dash="dot", width=1.5),
                       annotation_text="Uniform (TWAP)", annotation_font_color=C["neutral"])
        fig2.update_layout(**base_layout(f"VWAP Schedule — {Q:,} shares",
                                          xl="Hour of Day", yl="Shares per Period"))
        st.plotly_chart(fig2, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("Total Scheduled", f"{vwap_sched.sum():,.0f}", "shares")
        with c2: metric_card("Max Slice", f"{vwap_sched.max():,.0f}", f"{vwap_sched.max()/Q*100:.1f}% of order")
        with c3: metric_card("Min Slice", f"{vwap_sched.min():,.0f}", f"{vwap_sched.min()/Q*100:.1f}% of order")
        with c4: metric_card("Periods", f"{len(vol_profile)}", "30-min intervals")

    with tab3:
        traj_twap = Q * (1 - np.linspace(0, 1, len(vol_profile) + 1))
        vwap_remaining = np.concatenate([[Q], Q - np.cumsum(vwap_sched)])

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=hours.tolist() + [16.5], y=vwap_remaining,
                                   line=dict(color=C["primary"], width=2.5),
                                   name="VWAP Trajectory"))
        fig3.add_trace(go.Scatter(x=hours.tolist() + [16.5], y=traj_twap,
                                   line=dict(color=C["neutral"], width=2, dash="dot"),
                                   name="TWAP (Uniform)"))
        fig3.update_layout(**base_layout("VWAP vs TWAP — Shares Remaining",
                                          xl="Hour of Day", yl="Shares Remaining"))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('<div class="insight-box">VWAP front-loads at open and back-loads at close '
                    '(high-volume periods). TWAP executes at a fixed rate regardless of market activity. '
                    'Neither is optimal — both ignore the cost-risk tradeoff.</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# PAGE: MARKET IMPACT
# ═══════════════════════════════════════════
elif page == "Market Impact":
    st.markdown("## Market Impact")
    st.markdown("**Problem**: When you trade, you move the market against yourself. How does this compound?")

    st.markdown(r"""
    Two additive components:

    $$\tilde{S}(t) = \underbrace{\gamma \cdot X(t)}_{\text{permanent}} + \underbrace{\eta \cdot v(t)}_{\text{temporary}} + \sigma W(t)$$

    - **Permanent** $\gamma$: price shift that *never* reverts — reflects information content of your flow
    - **Temporary** $\eta$: cost of demanding liquidity *now* — reverts after execution
    """)

    tab1, tab2 = st.tabs(["Cost vs Slices", "Impact Decomposition"])

    with tab1:
        st.markdown('<div class="section-header">Tradeoff: More Slices = Less Temp, More Perm</div>',
                    unsafe_allow_html=True)
        n_options = [1, 2, 5, 10, 20, 50, 100]
        perms, temps, totals = [], [], []
        for n in n_options:
            tau_i = T / n
            s_u = np.full(n, Q / n)
            perms.append(perm_impact_cost(s_u, gamma))
            temps.append(temp_impact_cost(s_u, tau_i, eta))
            totals.append(perms[-1] + temps[-1])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=n_options, y=perms, mode="lines+markers",
                                  name="Permanent Impact",
                                  line=dict(color=C["accent"], width=2.5),
                                  marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=n_options, y=temps, mode="lines+markers",
                                  name="Temporary Impact",
                                  line=dict(color=C["secondary"], width=2.5),
                                  marker=dict(size=8, symbol="square")))
        fig.add_trace(go.Scatter(x=n_options, y=totals, mode="lines+markers",
                                  name="Total Cost",
                                  line=dict(color=C["primary"], width=3),
                                  marker=dict(size=9, symbol="triangle-up")))
        fig.add_vline(x=N, line=dict(color=C["warn"], dash="dot", width=2),
                      annotation_text=f"Your N={N}", annotation_font_color=C["warn"])
        fig.update_layout(**base_layout("Impact Cost vs Number of Slices (Uniform Schedule)",
                                         xl="Number of Slices", yl="Cost ($)"),
                           xaxis_type="log")
        st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        idx = min(range(len(n_options)), key=lambda i: abs(n_options[i] - N))
        with c1: metric_card("Permanent Impact", f"${perms[idx]:,.2f}", f"at N={N}")
        with c2: metric_card("Temporary Impact", f"${temps[idx]:,.2f}", f"at N={N}")
        with c3: metric_card("Total Cost", f"${totals[idx]:,.2f}", f"at N={N}")

        st.markdown('<div class="insight-box">Permanent impact is nearly constant — it depends only on '
                    'how much you trade, not how fast. Temporary impact falls as 1/N. '
                    'The optimal N balances these two forces.</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-header">Permanent Impact Compounds Slice by Slice</div>',
                    unsafe_allow_html=True)

        n_demo = 8
        demo_sched = np.full(n_demo, Q / n_demo)
        cum_prior = np.concatenate([[0], np.cumsum(demo_sched[:-1])])
        perm_per_slice = gamma * demo_sched * cum_prior
        temp_per_slice = eta * demo_sched**2 / (T / n_demo)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=list(range(1, n_demo + 1)), y=perm_per_slice,
                               name="Permanent Impact Cost",
                               marker_color=C["accent"]))
        fig2.add_trace(go.Bar(x=list(range(1, n_demo + 1)), y=temp_per_slice,
                               name="Temporary Impact Cost",
                               marker_color=C["secondary"]))
        fig2.update_layout(**base_layout("Per-Slice Impact Cost (8 equal slices)",
                                          xl="Slice Number", yl="Cost ($)"),
                            barmode="stack")
        st.plotly_chart(fig2, use_container_width=True)

        rows = []
        for i in range(n_demo):
            rows.append({
                "Slice": i + 1,
                "Shares": f"{demo_sched[i]:,.0f}",
                "Cumul. Prior": f"{cum_prior[i]:,.0f}",
                "Perm Cost ($)": f"{perm_per_slice[i]:.2f}",
                "Temp Cost ($)": f"{temp_per_slice[i]:.2f}",
                "Total ($)": f"{perm_per_slice[i] + temp_per_slice[i]:.2f}",
            })
        st.dataframe(pd.DataFrame(rows).set_index("Slice"), use_container_width=True)
        st.markdown('<div class="insight-box">Each new slice faces all the permanent impact from prior '
                    'slices. Slice 1 pays zero permanent impact; slice 8 pays the most. '
                    'This is why large orders front-run themselves.</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# PAGE: OPTIMAL TRAJECTORY
# ═══════════════════════════════════════════
elif page == "Optimal Trajectory":
    st.markdown("## Optimal Execution Trajectory")
    st.markdown("**Problem**: Find the trading path that minimizes cost + risk simultaneously.")

    st.markdown(r"""
    $$\min_{x(t)} \quad J[x] = \underbrace{\eta \int_0^T \dot{x}^2 \, dt}_{\text{temporary impact}} + \underbrace{\lambda\sigma^2 \int_0^T x^2 \, dt}_{\text{timing risk}}$$

    The Euler-Lagrange equation gives $\ddot{x} = \kappa^2 x$ with solution:

    $$x^*(t) = Q \cdot \frac{\sinh(\kappa(T-t))}{\sinh(\kappa T)}, \qquad \kappa = \sqrt{\frac{\lambda\sigma^2}{\eta}}$$
    """)

    tab1, tab2, tab3 = st.tabs(["Trajectory Explorer", "Cost-Risk Frontier", "Lambda & Signal"])

    with tab1:
        st.markdown('<div class="section-header">How Lambda Changes the Trajectory</div>',
                    unsafe_allow_html=True)

        fig = go.Figure()
        lambda_vals = [0.0, 0.1, 0.5, 2.0, 10.0]
        colors_traj = [C["neutral"], C["secondary"], C["primary"], C["warn"], C["accent"]]

        for lv, col in zip(lambda_vals, colors_traj):
            traj, kappa_v = optimal_trajectory(Q, T, N, sigma, eta, lv)
            fig.add_trace(go.Scatter(
                x=t_pts, y=traj,
                mode="lines", line=dict(color=col, width=2.5),
                name=f"λ={lv:.1f}  (κ={kappa_v:.2f})",
                hovertemplate=f"λ={lv}<br>t=%{{x:.2f}}h<br>Remaining=%{{y:,.0f}}<extra></extra>",
            ))

        # Highlight current lambda
        fig.add_trace(go.Scatter(
            x=t_pts, y=res["trajectory"],
            mode="lines", line=dict(color="#ffffff", width=3, dash="dot"),
            name=f"Your λ={lam:.3f} (κ={res['kappa']:.3f})",
        ))

        fig.update_layout(**base_layout("Optimal Execution Trajectories",
                                         xl="Time (hours)", yl="Shares Remaining"))
        st.plotly_chart(fig, use_container_width=True)

        # Schedule bars
        fig2 = go.Figure()
        uniform_bar = Q / N
        bar_cols = [C["accent"] if s > uniform_bar * 1.2 else
                    C["primary"] if s < uniform_bar * 0.8 else
                    C["secondary"] for s in res["schedule"]]
        fig2.add_trace(go.Bar(x=slice_mids, y=res["schedule"],
                               marker_color=bar_cols, name="Shares per Slice",
                               hovertemplate="t=%{x:.2f}h<br>%{y:,.0f} shares<extra></extra>"))
        fig2.add_hline(y=uniform_bar, line=dict(color=C["neutral"], dash="dot", width=1.5),
                       annotation_text="Uniform (TWAP)", annotation_font_color=C["neutral"])
        fig2.update_layout(**base_layout("Execution Schedule",
                                          xl="Time (hours)", yl="Shares per Slice", height=300))
        st.plotly_chart(fig2, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("Urgency κ", f"{res['kappa']:.3f}", "higher = more front-loaded")
        with c2: metric_card("First Slice", f"{res['first_pct']:.1f}%", f"vs {100/N:.1f}% uniform")
        with c3: metric_card("Expected Cost", f"${res['expected_cost']:,.0f}", "perm + temp")
        with c4: metric_card("Cost Std Dev", f"±${res['std_dev']:,.0f}", "timing risk")

        st.markdown(
            f'<div class="insight-box">κ = {res["kappa"]:.3f}/hr means the trajectory decays on a '
            f'timescale of {1/res["kappa"]:.1f}h. '
            f'{"Front-loaded: most shares trade early." if res["kappa"] > 0.5 else "Near-uniform: TWAP-like execution."}'
            f'</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-header">Efficient Frontier: Cost vs Risk</div>',
                    unsafe_allow_html=True)

        with st.spinner("Computing frontier..."):
            lam_range = np.concatenate([[0], np.logspace(-3, 2, 100)])
            e_costs = []
            stds = []
            kappas = []
            first_pcts = []
            for lv in lam_range:
                r = analyze(Q, T, N, sigma, gamma, eta, lv)
                e_costs.append(r["expected_cost"])
                stds.append(r["std_dev"])
                kappas.append(r["kappa"])
                first_pcts.append(r["first_pct"])

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=stds, y=e_costs, mode="lines",
            line=dict(color=C["secondary"], width=2.5),
            name="Efficient Frontier",
            hovertemplate="σ(cost)=$%{x:,.0f}<br>E[cost]=$%{y:,.0f}<extra></extra>",
        ))

        # Mark current lambda
        cur_idx = int(np.argmin(np.abs(np.array(lam_range) - lam)))
        fig3.add_trace(go.Scatter(
            x=[stds[cur_idx]], y=[e_costs[cur_idx]],
            mode="markers+text",
            marker=dict(color=C["accent"], size=13, symbol="star"),
            text=["  Your λ"], textposition="middle right",
            textfont=dict(color=C["accent"]),
            name=f"Your λ={lam:.3f}",
        ))

        # Mark key lambdas
        for lv_mark, label in [(0, "λ=0\n(TWAP)"), (1.0, "λ=1"), (10.0, "λ=10")]:
            idx = int(np.argmin(np.abs(np.array(lam_range) - lv_mark)))
            fig3.add_trace(go.Scatter(
                x=[stds[idx]], y=[e_costs[idx]],
                mode="markers+text",
                marker=dict(color=C["neutral"], size=9),
                text=[f"  {label}"], textposition="top center",
                textfont=dict(color=C["neutral"], size=9),
                showlegend=False,
            ))

        fig3.update_layout(**base_layout("Cost-Risk Efficient Frontier",
                                          xl="Cost Std Dev ($)", yl="Expected Cost ($)"))
        st.plotly_chart(fig3, use_container_width=True)

        # Sample table
        rows = []
        sample_lams = [0.0, 0.01, 0.1, 0.5, 1.0, 5.0, 20.0]
        for lv in sample_lams:
            r = analyze(Q, T, N, sigma, gamma, eta, lv)
            rows.append({
                "λ": f"{lv:.2f}", "κ": f"{r['kappa']:.3f}",
                "E[Cost] ($)": f"{r['expected_cost']:,.2f}",
                "Std Dev ($)": f"{r['std_dev']:,.2f}",
                "Perm ($)": f"{r['perm']:,.2f}",
                "Temp ($)": f"{r['temp']:,.2f}",
                "1st Slice %": f"{r['first_pct']:.1f}%",
            })
        st.dataframe(pd.DataFrame(rows).set_index("λ"), use_container_width=True)

    with tab3:
        st.markdown('<div class="section-header">Matching Lambda to Your Alpha Signal</div>',
                    unsafe_allow_html=True)

        st.markdown(r"""
        Set $\kappa \approx 1/h$ where $h$ is the signal half-life. This gives:

        $$\lambda = \frac{\eta}{h^2 \sigma^2}$$

        The execution rate matches the signal's decay — you're aggressive when the edge is fresh,
        patient when it's durable.
        """)

        scenarios = [
            ("HFT / Microstructure", 0.1, "6 minutes"),
            ("Momentum", 0.5, "30 minutes"),
            ("Intraday Alpha", 2.0, "2 hours"),
            ("Mean Reversion", 8.0, "8 hours"),
            ("Value Signal", 40.0, "1 week"),
        ]

        cols = st.columns(len(scenarios))
        palette = [C["accent"], C["warn"], C["primary"], C["secondary"], C["neutral"]]
        for col, (name, hl, desc), color in zip(cols, scenarios, palette):
            lv = suggest_lambda(hl, sigma, eta)
            r = analyze(Q, T, N, sigma, gamma, eta, lv)
            with col:
                metric_card(name, f"λ={lv:.3f}", f"κ={r['kappa']:.2f} · {desc}")

        st.markdown("")
        fig4 = go.Figure()
        halflives = np.logspace(-2, 2, 200)
        lambdas_curve = [suggest_lambda(h, sigma, eta) for h in halflives]
        kappas_curve  = [np.sqrt(l * sigma**2 / eta) if l > 0 else 0 for l in lambdas_curve]

        fig4.add_trace(go.Scatter(x=halflives, y=kappas_curve,
                                   mode="lines", line=dict(color=C["primary"], width=2.5),
                                   name="κ (urgency)"))
        fig4.add_vline(x=HL_MAP.get(signal, 2.0) if signal != "Manual" else 2.0,
                       line=dict(color=C["accent"], dash="dot", width=1.5),
                       annotation_text="Your signal", annotation_font_color=C["accent"])
        fig4.update_layout(**base_layout("Execution Urgency κ vs Signal Half-Life",
                                          xl="Signal Half-Life (hours)", yl="Urgency κ"),
                            xaxis_type="log")
        st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════
# PAGE: EXECUTION SIMULATOR
# ═══════════════════════════════════════════
elif page == "Execution Simulator":
    st.markdown("## Execution Simulator")
    st.markdown("**Full workflow**: pre-trade analysis → simulated execution → post-trade attribution")

    seed = st.number_input("Random Seed", min_value=0, max_value=9999, value=42)
    run = st.button("▶  Run Simulation")

    if run or "sim" not in st.session_state:
        st.session_state["sim"] = simulate(Q, T, N, S0, sigma, gamma, eta, lam, seed=int(seed))

    sim = st.session_state["sim"]
    pre = sim["pre"]

    # KPIs
    st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    is_col = "red" if sim["is_bps"] > 0 else "green"
    ratio = abs(sim["is_total"]) / pre["expected_cost"] if pre["expected_cost"] > 0 else 0

    with c1: metric_card("Exec VWAP",      f"${sim['vwap']:.3f}",           f"Decision: ${S0:.2f}")
    with c2: metric_card("Impl. Shortfall", f"{sim['is_bps']:+.1f} bps",     f"${sim['is_total']:,.0f}")
    with c3: metric_card("Expected Cost",   f"${pre['expected_cost']:,.0f}", f"λ={lam:.3f}")
    with c4: metric_card("IS / E[Cost]",    f"{ratio:.2f}×",                 "calibration ratio")
    with c5: metric_card("Urgency κ",       f"{pre['kappa']:.3f}",           "1/hr")

    tab1, tab2, tab3 = st.tabs(["Price Path & Fills", "Cost Breakdown", "Execution Log"])

    with tab1:
        fig = make_subplots(rows=1, cols=2,
                             subplot_titles=["Execution Trajectory", "Price Path & Fills"])

        # Trajectory
        fig.add_trace(go.Scatter(x=t_pts, y=pre["trajectory"],
                                  fill="tozeroy", fillcolor="rgba(46,204,113,0.08)",
                                  line=dict(color=C["primary"], width=2.5),
                                  name="Optimal Trajectory"), row=1, col=1)
        fig.add_trace(go.Scatter(x=t_pts, y=Q * (1 - t_pts / T),
                                  line=dict(color=C["neutral"], width=1.5, dash="dot"),
                                  name="TWAP"), row=1, col=1)

        # Price path
        fig.add_trace(go.Scatter(x=t_pts, y=sim["path"],
                                  line=dict(color="#e6edf3", width=2),
                                  name="Mid Price",
                                  hovertemplate="t=%{x:.2f}h  $%{y:.3f}<extra></extra>"), row=1, col=2)
        fig.add_trace(go.Scatter(x=slice_mids, y=sim["prices"],
                                  mode="markers",
                                  marker=dict(color=C["accent"], size=7, symbol="diamond"),
                                  name="Fill Prices"), row=1, col=2)

        fig.add_hline(y=S0,           line=dict(color=C["secondary"], dash="dash", width=1.5),
                      row=1, col=2)
        fig.add_hline(y=sim["vwap"],  line=dict(color=C["primary"],   dash="dash", width=1.5),
                      row=1, col=2)

        fig.update_layout(template="plotly_dark", paper_bgcolor=C["bg"], plot_bgcolor=C["bg"],
                           height=420, legend=dict(bgcolor="rgba(0,0,0,0)"),
                           margin=dict(l=50, r=20, t=60, b=50))
        fig.update_xaxes(title_text="Time (hours)", gridcolor="#1e2a38")
        fig.update_yaxes(title_text="Shares Remaining", gridcolor="#1e2a38", row=1, col=1)
        fig.update_yaxes(title_text="Price ($)", gridcolor="#1e2a38", row=1, col=2)
        st.plotly_chart(fig, use_container_width=True)

        if abs(ratio - 1) < 0.25:
            msg = f"IS/E[Cost] = {ratio:.2f}× — within tolerance. Model well-calibrated."
        elif ratio < 0.75:
            msg = f"IS/E[Cost] = {ratio:.2f}× — beat expectations. Lucky timing or overestimated impact."
        else:
            msg = f"IS/E[Cost] = {ratio:.2f}× — exceeded expectations. Review impact parameters."
        st.markdown(f'<div class="insight-box">{msg}</div>', unsafe_allow_html=True)

    with tab2:
        labels = ["Permanent", "Temporary", "Expected Total", "Realized IS"]
        values = [pre["perm"], pre["temp"], pre["expected_cost"], abs(sim["is_total"])]
        colors_bar = [C["accent"], C["secondary"], C["warn"], C["primary"]]

        fig2 = go.Figure(go.Bar(
            x=labels, y=values, marker_color=colors_bar,
            text=[f"${v:,.0f}" for v in values],
            textposition="outside",
        ))
        fig2.update_layout(**base_layout("Cost Attribution", yl="Cost ($)"))
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        rows = []
        cum = 0
        for i, (n, p) in enumerate(zip(pre["schedule"], sim["prices"])):
            cum += n
            rows.append({
                "Slice": i + 1,
                "Time (h)": f"{slice_mids[i]:.2f}",
                "Shares": f"{n:,.0f}",
                "% Done": f"{cum/Q*100:.1f}%",
                "Fill Price": f"${p:.4f}",
                "Slippage (bps)": f"{(p - S0) / S0 * 10000:+.1f}",
            })
        st.dataframe(pd.DataFrame(rows).set_index("Slice"), use_container_width=True)
