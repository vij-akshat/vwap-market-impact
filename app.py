"""
VWAP Market Impact & Almgren-Chriss Execution Dashboard
Interactive trading terminal for optimal execution analysis.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Tuple, Dict
import time

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Optimal Execution Desk",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Styling
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Dark terminal aesthetic */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0a0e17;
    color: #c9d1d9;
}

/* Header banner */
.header-banner {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border: 1px solid #21262d;
    border-left: 4px solid #00d4aa;
    padding: 20px 28px;
    border-radius: 6px;
    margin-bottom: 24px;
}
.header-banner h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    color: #00d4aa;
    margin: 0 0 4px 0;
    letter-spacing: 0.04em;
}
.header-banner p {
    color: #6e7681;
    font-size: 0.85rem;
    margin: 0;
    font-family: 'IBM Plex Mono', monospace;
}

/* Metric cards */
.metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 16px 20px;
    text-align: center;
}
.metric-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}
.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem;
    font-weight: 600;
    color: #e6edf3;
}
.metric-value.green { color: #3fb950; }
.metric-value.red   { color: #f85149; }
.metric-value.blue  { color: #58a6ff; }
.metric-value.gold  { color: #d29922; }

/* Section headers */
.section-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 8px 0;
    border-bottom: 1px solid #21262d;
    margin-bottom: 16px;
}

/* Trade button */
.stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: #ffffff;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: 0.9rem;
    letter-spacing: 0.05em;
    border: none;
    border-radius: 6px;
    padding: 12px 28px;
    cursor: pointer;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2ea043, #3fb950);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(63, 185, 80, 0.3);
}

/* Tag pills */
.tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
}
.tag-aggressive { background: #3d1f1f; color: #f85149; border: 1px solid #f85149; }
.tag-moderate   { background: #1f2d1f; color: #3fb950; border: 1px solid #3fb950; }
.tag-passive    { background: #1f2533; color: #58a6ff; border: 1px solid #58a6ff; }

/* Assessment box */
.assessment-box {
    background: #161b22;
    border-radius: 6px;
    padding: 16px 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    margin-top: 16px;
}
.assessment-box.good  { border-left: 4px solid #3fb950; }
.assessment-box.great { border-left: 4px solid #00d4aa; }
.assessment-box.poor  { border-left: 4px solid #f85149; }

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #21262d;
}

/* Slider / Input styling */
[data-testid="stSlider"] label,
[data-testid="stNumberInput"] label,
[data-testid="stSelectbox"] label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0d1117;
    border-bottom: 1px solid #21262d;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #6e7681;
    letter-spacing: 0.05em;
    padding: 10px 20px;
}
.stTabs [aria-selected="true"] {
    color: #00d4aa;
    border-bottom: 2px solid #00d4aa;
    background-color: transparent;
}

/* Blinking cursor for "live" feel */
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.cursor { animation: blink 1s infinite; }

/* Plotly charts */
.js-plotly-plot { border-radius: 6px; }

/* Info banner */
.info-row {
    display: flex;
    gap: 12px;
    margin-bottom: 8px;
}
.info-pill {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 20px;
    padding: 4px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #8b949e;
}
.info-pill span { color: #e6edf3; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Core model functions (from notebook)
# ─────────────────────────────────────────────

def calculate_vwap(prices: np.ndarray, volumes: np.ndarray) -> float:
    return np.sum(prices * volumes) / np.sum(volumes)

def generate_vwap_schedule(total_shares: float, volume_profile: np.ndarray) -> np.ndarray:
    weights = volume_profile / np.sum(volume_profile)
    return total_shares * weights

def temporary_impact_cost(schedule: np.ndarray, tau: float, eta: float) -> float:
    return eta * np.sum(schedule ** 2 / tau)

def permanent_impact_cost(schedule: np.ndarray, gamma: float) -> float:
    cost, cumulative_prior = 0.0, 0.0
    for n_k in schedule:
        cost += gamma * n_k * cumulative_prior
        cumulative_prior += n_k
    return cost

def optimal_trajectory(Q, T, N, sigma, eta, lambda_risk) -> Tuple[np.ndarray, float]:
    tau = T / N
    t_points = np.arange(N + 1) * tau
    if lambda_risk < 1e-12:
        kappa = 0.0
        trajectory = Q * (T - t_points) / T
    else:
        kappa = np.sqrt(lambda_risk * sigma ** 2 / eta)
        trajectory = Q * np.sinh(kappa * (T - t_points)) / np.sinh(kappa * T)
    return trajectory, kappa

def trajectory_to_schedule(trajectory: np.ndarray) -> np.ndarray:
    return -np.diff(trajectory)

def analyze_execution(Q, T, N, sigma, gamma, eta, lambda_risk) -> Dict:
    tau = T / N
    trajectory, kappa = optimal_trajectory(Q, T, N, sigma, eta, lambda_risk)
    schedule = trajectory_to_schedule(trajectory)
    perm_cost = permanent_impact_cost(schedule, gamma)
    temp_cost = temporary_impact_cost(schedule, tau, eta)
    expected_cost = perm_cost + temp_cost
    variance = sigma ** 2 * tau * np.sum(trajectory[1:] ** 2)
    std_dev = np.sqrt(variance)
    return {
        'lambda': lambda_risk, 'kappa': kappa,
        'trajectory': trajectory, 'schedule': schedule,
        'perm_cost': perm_cost, 'temp_cost': temp_cost,
        'expected_cost': expected_cost,
        'variance': variance, 'std_dev': std_dev,
        'objective': expected_cost + lambda_risk * variance,
        'first_slice_pct': schedule[0] / Q * 100
    }

def suggest_lambda(alpha_halflife, sigma, eta):
    target_kappa = 1.0 / alpha_halflife
    return (target_kappa ** 2) * eta / (sigma ** 2)

def run_execution_simulation(Q, T, N, decision_price, sigma, gamma, eta, lambda_risk, seed=None):
    if seed is not None:
        np.random.seed(seed)
    tau = T / N
    pre_trade = analyze_execution(Q, T, N, sigma, gamma, eta, lambda_risk)
    schedule = pre_trade['schedule']
    execution_prices, price_path = [], [decision_price]
    current_price = decision_price
    for shares in schedule:
        current_price += gamma * shares
        current_price += sigma * np.sqrt(tau) * np.random.randn() * current_price / 100
        fill_price = current_price + eta * (shares / tau)
        execution_prices.append(fill_price)
        price_path.append(current_price)
    execution_prices = np.array(execution_prices)
    total_shares = np.sum(schedule)
    vwap_exec = np.sum(execution_prices * schedule) / total_shares
    is_per_share = vwap_exec - decision_price
    is_total = is_per_share * total_shares
    is_bps = (is_per_share / decision_price) * 10000
    return {
        'pre_trade': pre_trade,
        'execution_prices': execution_prices,
        'price_path': np.array(price_path),
        'vwap': vwap_exec,
        'is_per_share': is_per_share,
        'is_total': is_total,
        'is_bps': is_bps,
        'schedule': schedule,
    }

# ─────────────────────────────────────────────
# Plotly theme
# ─────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor='#0d1117',
    plot_bgcolor='#161b22',
    font=dict(family='IBM Plex Mono', color='#8b949e', size=11),
    xaxis=dict(gridcolor='#21262d', zerolinecolor='#21262d'),
    yaxis=dict(gridcolor='#21262d', zerolinecolor='#21262d'),
    margin=dict(l=50, r=20, t=40, b=50),
)

# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="header-banner">
  <h1>⬛ OPTIMAL EXECUTION DESK <span class="cursor">|</span></h1>
  <p>Almgren-Chriss Framework · VWAP Benchmark · Market Impact Analysis · Implementation Shortfall</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Sidebar — Order & Market Parameters
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-header">🗂 ORDER TICKET</div>', unsafe_allow_html=True)

    ticker = st.text_input("TICKER", value="AAPL", max_chars=8).upper()
    side = st.selectbox("SIDE", ["BUY", "SELL"])
    total_shares = st.number_input("SHARES", min_value=1000, max_value=10_000_000,
                                    value=100_000, step=1000)
    decision_price = st.number_input("DECISION PRICE ($)", min_value=1.0,
                                      value=150.00, step=0.01, format="%.2f")
    T = st.slider("HORIZON (hours)", min_value=0.5, max_value=8.0, value=4.0, step=0.5)
    N = st.select_slider("EXECUTION SLICES", options=[8, 12, 16, 24, 32, 48], value=16)

    st.markdown('<div class="section-header">📡 MARKET PARAMETERS</div>', unsafe_allow_html=True)

    sigma = st.slider("VOLATILITY σ (% / hr)", min_value=0.5, max_value=5.0,
                       value=1.5, step=0.1) / 100
    gamma = st.slider("PERM. IMPACT γ (×10⁻⁶)", min_value=1, max_value=50, value=5) * 1e-6
    eta = st.slider("TEMP. IMPACT η (×10⁻⁵)", min_value=1, max_value=20, value=8) * 1e-5

    st.markdown('<div class="section-header">⚡ ALPHA SIGNAL</div>', unsafe_allow_html=True)

    signal_type = st.selectbox("SIGNAL TYPE", [
        "HFT / Microstructure",
        "Momentum (30 min)",
        "Intraday Alpha (2 hr)",
        "Mean Reversion (8 hr)",
        "Value / Rebalancing",
        "Manual Override",
    ])

    HALFLIFE_MAP = {
        "HFT / Microstructure": 0.1,
        "Momentum (30 min)": 0.5,
        "Intraday Alpha (2 hr)": 2.0,
        "Mean Reversion (8 hr)": 8.0,
        "Value / Rebalancing": 40.0,
        "Manual Override": None,
    }

    if signal_type == "Manual Override":
        lambda_risk = st.slider("RISK AVERSION λ", min_value=0.0, max_value=50.0,
                                 value=1.0, step=0.1)
        alpha_halflife = None
    else:
        alpha_halflife = HALFLIFE_MAP[signal_type]
        lambda_risk = suggest_lambda(alpha_halflife, sigma, eta)
        st.metric("Derived λ", f"{lambda_risk:.4f}")

    st.markdown('<div class="section-header">🎲 SIMULATION</div>', unsafe_allow_html=True)
    sim_seed = st.number_input("RANDOM SEED", min_value=0, max_value=9999, value=42)
    run_sim = st.button("▶  EXECUTE ORDER")

# ─────────────────────────────────────────────
# Compute pre-trade + simulation
# ─────────────────────────────────────────────
pre_trade = analyze_execution(total_shares, T, N, sigma, gamma, eta, lambda_risk)

if run_sim or 'sim_result' not in st.session_state:
    sim = run_execution_simulation(
        total_shares, T, N, decision_price,
        sigma, gamma, eta, lambda_risk, seed=int(sim_seed)
    )
    st.session_state['sim_result'] = sim
    st.session_state['sim_run'] = True

sim = st.session_state['sim_result']

# ─────────────────────────────────────────────
# Top KPI bar
# ─────────────────────────────────────────────
kappa = pre_trade['kappa']
is_bps = sim['is_bps']
is_color = "red" if (side == "BUY" and is_bps > 0) or (side == "SELL" and is_bps < 0) else "green"

if kappa > 2:     urgency_tag, urgency_class = "AGGRESSIVE", "tag-aggressive"
elif kappa > 0.5: urgency_tag, urgency_class = "MODERATE",  "tag-moderate"
else:             urgency_tag, urgency_class = "PASSIVE",   "tag-passive"

col1, col2, col3, col4, col5 = st.columns(5)
metrics = [
    (col1, "EXEC VWAP",     f"${sim['vwap']:.3f}",                    "blue"),
    (col2, "IMPL. SHORTFALL", f"{is_bps:+.1f} bps",                  is_color),
    (col3, "EXP. COST",     f"${pre_trade['expected_cost']:,.0f}",    "gold"),
    (col4, "COST STD DEV",  f"±${pre_trade['std_dev']:,.0f}",         ""),
    (col5, "URGENCY κ",     f"{kappa:.3f}",                           ""),
]
for col, label, val, cls in metrics:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {cls}">{val}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈  EXECUTION ANALYTICS",
    "🌐  COST-RISK FRONTIER",
    "📊  MARKET IMPACT",
    "📅  VWAP SCHEDULE",
    "📋  TRADE REPORT",
])

# ═══════════════════════════════════════════════
# TAB 1: Execution Analytics
# ═══════════════════════════════════════════════
with tab1:
    t_points = np.linspace(0, T, N + 1)
    tau = T / N
    slice_midpoints = t_points[:-1] + tau / 2

    # Row 1: Trajectory + Price path
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("EXECUTION TRAJECTORY", "PRICE PATH & FILLS"),
        horizontal_spacing=0.08
    )

    traj = pre_trade['trajectory']
    sched = pre_trade['schedule']

    # Trajectory
    fig.add_trace(go.Scatter(
        x=t_points, y=traj,
        fill='tozeroy',
        fillcolor='rgba(0, 212, 170, 0.08)',
        line=dict(color='#00d4aa', width=2.5),
        name='Remaining Position',
        hovertemplate='t=%{x:.2f}h<br>Remaining=%{y:,.0f} shares<extra></extra>',
    ), row=1, col=1)

    # Uniform for reference
    uniform_traj = total_shares * (1 - t_points / T)
    fig.add_trace(go.Scatter(
        x=t_points, y=uniform_traj,
        line=dict(color='#6e7681', width=1.5, dash='dot'),
        name='Uniform TWAP',
        hovertemplate='Uniform: %{y:,.0f}<extra></extra>',
    ), row=1, col=1)

    fig.update_xaxes(title_text="Time (hours)", row=1, col=1)
    fig.update_yaxes(title_text="Shares Remaining", row=1, col=1)

    # Price path
    fig.add_trace(go.Scatter(
        x=t_points, y=sim['price_path'],
        line=dict(color='#e6edf3', width=2),
        name='Mid Price',
        hovertemplate='t=%{x:.2f}h<br>Price=$%{y:.3f}<extra></extra>',
    ), row=1, col=2)

    fig.add_hline(y=decision_price, line=dict(color='#58a6ff', width=1.5, dash='dash'),
                  row=1, col=2)
    fig.add_hline(y=sim['vwap'], line=dict(color='#3fb950', width=1.5, dash='dash'),
                  row=1, col=2)

    fig.add_trace(go.Scatter(
        x=slice_midpoints, y=sim['execution_prices'],
        mode='markers',
        marker=dict(color='#f85149', size=7, symbol='diamond',
                    line=dict(color='#ff7b72', width=1)),
        name='Fill Prices',
        hovertemplate='Fill #%{pointNumber}<br>$%{y:.4f}<extra></extra>',
    ), row=1, col=2)

    fig.update_xaxes(title_text="Time (hours)", row=1, col=2)
    fig.update_yaxes(title_text="Price ($)", row=1, col=2)

    fig.update_layout(**PLOT_LAYOUT, height=380, showlegend=True,
                      legend=dict(bgcolor='#0d1117', bordercolor='#21262d', borderwidth=1,
                                  font=dict(size=10)))
    fig.update_annotations(font=dict(color='#8b949e', size=11))
    st.plotly_chart(fig, use_container_width=True)

    # Row 2: Schedule bars + Cost breakdown
    col_a, col_b = st.columns(2)

    with col_a:
        fig2 = go.Figure()
        uniform_shares = total_shares / N
        bar_colors = ['#f85149' if s > uniform_shares * 1.15 else
                      '#3fb950' if s < uniform_shares * 0.85 else
                      '#00d4aa' for s in sched]
        fig2.add_trace(go.Bar(
            x=slice_midpoints,
            y=sched,
            marker_color=bar_colors,
            marker_line_width=0,
            name='Scheduled Shares',
            hovertemplate='Slice %{x:.2f}h<br>%{y:,.0f} shares<br>(%{customdata:.1f}%)<extra></extra>',
            customdata=sched / total_shares * 100,
        ))
        fig2.add_hline(y=uniform_shares, line=dict(color='#6e7681', dash='dot', width=1.5),
                       annotation_text='TWAP baseline', annotation_font_color='#6e7681',
                       annotation_font_size=10)
        fig2.update_layout(**PLOT_LAYOUT, height=300,
                           title=dict(text='EXECUTION SCHEDULE', font=dict(color='#8b949e', size=11)),
                           xaxis_title='Time (hours)', yaxis_title='Shares per Slice',
                           showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        labels = ['Permanent Impact', 'Temporary Impact', 'Total Expected', 'Realized IS']
        values = [pre_trade['perm_cost'], pre_trade['temp_cost'],
                  pre_trade['expected_cost'], abs(sim['is_total'])]
        bar_colors_cost = ['#f85149', '#d29922', '#8957e5', '#3fb950']
        fig3 = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=bar_colors_cost,
            marker_line_width=0,
            text=[f'${v:,.0f}' for v in values],
            textposition='outside',
            textfont=dict(color='#e6edf3', size=11, family='IBM Plex Mono'),
            hovertemplate='%{x}<br>$%{y:,.2f}<extra></extra>',
        ))
        fig3.update_layout(**PLOT_LAYOUT, height=300,
                           title=dict(text='COST BREAKDOWN', font=dict(color='#8b949e', size=11)),
                           yaxis_title='Cost ($)', showlegend=False,
                           xaxis_tickfont=dict(size=10))
        st.plotly_chart(fig3, use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 2: Cost-Risk Frontier
# ═══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">ALMGREN-CHRISS EFFICIENT FRONTIER</div>', unsafe_allow_html=True)

    with st.spinner("Computing frontier..."):
        lambda_range = np.concatenate([[0], np.logspace(-3, 2, 120)])
        frontier_results = [analyze_execution(total_shares, T, N, sigma, gamma, eta, lam)
                            for lam in lambda_range]

    e_costs = np.array([r['expected_cost'] for r in frontier_results])
    std_devs = np.array([r['std_dev'] for r in frontier_results])
    kappas   = np.array([r['kappa'] for r in frontier_results])
    lambdas  = np.array([r['lambda'] for r in frontier_results])
    first_sl = np.array([r['first_slice_pct'] for r in frontier_results])

    col_f1, col_f2 = st.columns([3, 2])

    with col_f1:
        fig_f = go.Figure()
        fig_f.add_trace(go.Scatter(
            x=std_devs, y=e_costs,
            mode='lines',
            line=dict(color='#00d4aa', width=2),
            name='Efficient Frontier',
            hovertemplate='σ(cost)=$%{x:,.0f}<br>E[cost]=$%{y:,.0f}<extra></extra>',
        ))

        # Highlight current λ
        cur_idx = np.argmin(np.abs(lambdas - lambda_risk))
        fig_f.add_trace(go.Scatter(
            x=[std_devs[cur_idx]], y=[e_costs[cur_idx]],
            mode='markers+text',
            marker=dict(color='#f85149', size=12, symbol='star'),
            text=['◀ YOUR λ'],
            textposition='middle right',
            textfont=dict(color='#f85149', size=11, family='IBM Plex Mono'),
            name='Current Setting',
        ))

        # Label key lambdas
        for lam_mark, label in [(0, 'λ=0 (TWAP)'), (1.0, 'λ=1'), (10.0, 'λ=10')]:
            idx = np.argmin(np.abs(lambdas - lam_mark))
            fig_f.add_trace(go.Scatter(
                x=[std_devs[idx]], y=[e_costs[idx]],
                mode='markers+text',
                marker=dict(color='#58a6ff', size=8, symbol='circle'),
                text=[label],
                textposition='top center',
                textfont=dict(color='#58a6ff', size=9, family='IBM Plex Mono'),
                showlegend=False,
            ))

        fig_f.update_layout(**PLOT_LAYOUT, height=400,
                            title=dict(text='COST-RISK EFFICIENT FRONTIER',
                                       font=dict(color='#8b949e', size=11)),
                            xaxis_title='Cost Std Dev ($)',
                            yaxis_title='Expected Cost ($)',
                            legend=dict(bgcolor='#0d1117', bordercolor='#21262d'))
        st.plotly_chart(fig_f, use_container_width=True)

    with col_f2:
        # Kappa vs Lambda
        fig_kl = go.Figure()
        fig_kl.add_trace(go.Scatter(
            x=lambdas[1:], y=kappas[1:],
            mode='lines', line=dict(color='#d29922', width=2),
            name='κ(λ)',
        ))
        fig_kl.add_vline(x=lambda_risk, line=dict(color='#f85149', dash='dot', width=1.5),
                         annotation_text=f'λ={lambda_risk:.3f}',
                         annotation_font_color='#f85149', annotation_font_size=9)
        fig_kl.update_layout(**PLOT_LAYOUT, height=190,
                             title=dict(text='URGENCY κ vs λ', font=dict(color='#8b949e', size=10)),
                             xaxis_title='λ', yaxis_title='κ',
                             xaxis_type='log', showlegend=False,
                             margin=dict(l=50, r=20, t=40, b=40))
        st.plotly_chart(fig_kl, use_container_width=True)

        # Front-loading
        fig_fl = go.Figure()
        fig_fl.add_trace(go.Scatter(
            x=lambdas[1:], y=first_sl[1:],
            mode='lines', line=dict(color='#3fb950', width=2),
            name='1st Slice %',
        ))
        fig_fl.add_hline(y=100 / N, line=dict(color='#6e7681', dash='dot', width=1),
                         annotation_text='Uniform', annotation_font_color='#6e7681',
                         annotation_font_size=9)
        fig_fl.update_layout(**PLOT_LAYOUT, height=190,
                             title=dict(text='FRONT-LOADING vs λ', font=dict(color='#8b949e', size=10)),
                             xaxis_title='λ', yaxis_title='1st Slice (%)',
                             xaxis_type='log', showlegend=False,
                             margin=dict(l=50, r=20, t=40, b=40))
        st.plotly_chart(fig_fl, use_container_width=True)

    # Summary table
    st.markdown('<div class="section-header">FRONTIER SAMPLE POINTS</div>', unsafe_allow_html=True)
    sample_lams = [0.0, 0.01, 0.1, 0.5, 1.0, 5.0, 20.0]
    rows = []
    for lam in sample_lams:
        r = analyze_execution(total_shares, T, N, sigma, gamma, eta, lam)
        rows.append({
            'λ': f"{lam:.2f}", 'κ': f"{r['kappa']:.3f}",
            'E[Cost] ($)': f"{r['expected_cost']:,.2f}",
            'Std Dev ($)': f"{r['std_dev']:,.2f}",
            'Perm ($)': f"{r['perm_cost']:,.2f}",
            'Temp ($)': f"{r['temp_cost']:,.2f}",
            '1st Slice %': f"{r['first_slice_pct']:.1f}%",
        })
    df_table = pd.DataFrame(rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════════════
# TAB 3: Market Impact
# ═══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">MARKET IMPACT DECOMPOSITION</div>', unsafe_allow_html=True)

    n_slices_options = [1, 2, 5, 10, 20, 50, 100]
    c_perms, c_temps, c_totals = [], [], []
    for n in n_slices_options:
        tau_i = T / n
        sched_u = np.full(n, total_shares / n)
        c_perms.append(permanent_impact_cost(sched_u, gamma))
        c_temps.append(temporary_impact_cost(sched_u, tau_i, eta))
        c_totals.append(c_perms[-1] + c_temps[-1])

    fig_mi = go.Figure()
    fig_mi.add_trace(go.Scatter(x=n_slices_options, y=c_perms, mode='lines+markers',
                                name='Permanent Impact',
                                line=dict(color='#f85149', width=2),
                                marker=dict(size=8)))
    fig_mi.add_trace(go.Scatter(x=n_slices_options, y=c_temps, mode='lines+markers',
                                name='Temporary Impact',
                                line=dict(color='#58a6ff', width=2),
                                marker=dict(size=8, symbol='square')))
    fig_mi.add_trace(go.Scatter(x=n_slices_options, y=c_totals, mode='lines+markers',
                                name='Total Cost',
                                line=dict(color='#00d4aa', width=2.5),
                                marker=dict(size=9, symbol='triangle-up')))
    fig_mi.add_vline(x=N, line=dict(color='#f85149', dash='dot', width=1.5),
                     annotation_text=f'Your N={N}', annotation_font_color='#f85149',
                     annotation_font_size=10)

    fig_mi.update_layout(**PLOT_LAYOUT, height=380,
                         title=dict(text='IMPACT COST vs NUMBER OF SLICES (UNIFORM SCHEDULE)',
                                    font=dict(color='#8b949e', size=11)),
                         xaxis_title='Number of Slices', yaxis_title='Cost ($)',
                         xaxis_type='log',
                         legend=dict(bgcolor='#0d1117', bordercolor='#21262d'))
    st.plotly_chart(fig_mi, use_container_width=True)

    # λ comparison across strategies
    st.markdown('<div class="section-header">SCENARIO COMPARISON</div>', unsafe_allow_html=True)
    scenarios = [
        ("HFT Signal", 0.1, "#f85149"),
        ("Momentum", 0.5, "#d29922"),
        ("Intraday Alpha", 2.0, "#00d4aa"),
        ("Mean Reversion", 8.0, "#3fb950"),
        ("Value Signal", 40.0, "#58a6ff"),
    ]
    sc_cols = st.columns(len(scenarios))
    for col, (name, hl, color) in zip(sc_cols, scenarios):
        lam = suggest_lambda(hl, sigma, eta)
        r = analyze_execution(total_shares, T, N, sigma, gamma, eta, lam)
        kap = r['kappa']
        if kap > 2:   style, tag = "tag-aggressive", "AGGRESSIVE"
        elif kap > 0.5: style, tag = "tag-moderate",   "MODERATE"
        else:           style, tag = "tag-passive",    "PASSIVE"
        with col:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 3px solid {color};">
                <div class="metric-label">{name}</div>
                <div class="metric-value" style="font-size:1.1rem; color:{color};">λ={lam:.3f}</div>
                <div style="margin-top:6px; font-family:'IBM Plex Mono'; font-size:0.72rem; color:#6e7681;">
                    κ={kap:.2f} · ${r['expected_cost']:,.0f}
                </div>
                <div style="margin-top:8px;"><span class="tag {style}">{tag}</span></div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════
# TAB 4: VWAP Schedule
# ═══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">INTRADAY VOLUME PROFILE & VWAP SCHEDULE</div>',
                unsafe_allow_html=True)

    hours = np.arange(9.5, 16.5, 0.5)
    vol_profile = np.array([1.5, 1.2, 0.9, 0.7, 0.6, 0.5, 0.5, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.8])
    vwap_sched = generate_vwap_schedule(total_shares, vol_profile)

    fig_v = make_subplots(rows=1, cols=2,
                          subplot_titles=("INTRADAY VOLUME PROFILE", "VWAP PARTICIPATION SCHEDULE"))

    fig_v.add_trace(go.Bar(x=hours, y=vol_profile, width=0.35,
                           marker_color='#58a6ff', marker_opacity=0.8,
                           name='Relative Volume',
                           hovertemplate='%{x:.1f}h: %{y:.2f}x<extra></extra>'), row=1, col=1)
    fig_v.add_hline(y=1.0, line=dict(color='#6e7681', dash='dot', width=1),
                    row=1, col=1, annotation_text='Average',
                    annotation_font_color='#6e7681', annotation_font_size=9)

    bar_cols_vwap = ['#f85149' if h < 10.5 or h > 15.0 else '#3fb950' for h in hours]
    fig_v.add_trace(go.Bar(x=hours, y=vwap_sched, width=0.35,
                           marker_color=bar_cols_vwap, marker_opacity=0.85,
                           name='VWAP Shares',
                           hovertemplate='%{x:.1f}h: %{y:,.0f} shares<extra></extra>'), row=1, col=2)
    fig_v.add_hline(y=total_shares / len(vol_profile),
                    line=dict(color='#6e7681', dash='dot', width=1),
                    row=1, col=2, annotation_text='Uniform',
                    annotation_font_color='#6e7681', annotation_font_size=9)

    fig_v.update_layout(**PLOT_LAYOUT, height=370, showlegend=False)
    fig_v.update_xaxes(title_text='Hour of Day', tickvals=hours[::2],
                        ticktext=[f'{h:.1f}' for h in hours[::2]])
    fig_v.update_yaxes(title_text='Relative Volume', row=1, col=1)
    fig_v.update_yaxes(title_text='Shares', row=1, col=2)
    st.plotly_chart(fig_v, use_container_width=True)

    # Comparison: AC vs VWAP
    st.markdown('<div class="section-header">ALMGREN-CHRISS vs VWAP COMPARISON</div>',
                unsafe_allow_html=True)

    t_pts_vwap = np.linspace(0, T, len(vol_profile) + 1)
    vwap_traj = np.concatenate([[total_shares],
                                 total_shares - np.cumsum(vwap_sched[:len(vol_profile)])])
    if len(vwap_traj) > N + 1:
        vwap_traj = vwap_traj[:N + 1]

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Scatter(
        x=t_points, y=pre_trade['trajectory'],
        line=dict(color='#00d4aa', width=2.5), name='Almgren-Chriss (Optimal)',
    ))
    fig_cmp.add_trace(go.Scatter(
        x=t_points, y=pre_trade['trajectory'] * 0 + total_shares * (1 - t_points / T),
        line=dict(color='#6e7681', width=1.5, dash='dot'), name='TWAP (Uniform)',
    ))
    fig_cmp.update_layout(**PLOT_LAYOUT, height=320,
                          title=dict(text='TRAJECTORY COMPARISON',
                                     font=dict(color='#8b949e', size=11)),
                          xaxis_title='Time (hours)', yaxis_title='Shares Remaining',
                          legend=dict(bgcolor='#0d1117', bordercolor='#21262d'))
    st.plotly_chart(fig_cmp, use_container_width=True)

# ═══════════════════════════════════════════════
# TAB 5: Trade Report
# ═══════════════════════════════════════════════
with tab5:
    ratio = abs(sim['is_total']) / pre_trade['expected_cost'] if pre_trade['expected_cost'] > 0 else 0
    if abs(ratio - 1) < 0.25:
        assess_class, assess_icon, assess_text = "good", "✓", "WITHIN TOLERANCE — Actual cost within 25% of expected. Impact model well-calibrated."
    elif ratio < 0.75:
        assess_class, assess_icon, assess_text = "great", "★", "BEAT EXPECTATIONS — Execution significantly outperformed pre-trade estimates."
    else:
        assess_class, assess_icon, assess_text = "poor", "⚠", "EXCEEDED EXPECTATIONS — Realized cost exceeded model predictions. Review impact parameters."

    st.markdown(f"""
    <div class="assessment-box {assess_class}">
        <strong style="color:#e6edf3;">{assess_icon} POST-TRADE ASSESSMENT</strong><br>
        <span style="color:#8b949e;">{assess_text}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown('<div class="section-header">ORDER DETAILS</div>', unsafe_allow_html=True)
        order_df = pd.DataFrame([
            ("Ticker", ticker),
            ("Side", side),
            ("Shares", f"{total_shares:,}"),
            ("Horizon", f"{T} hours"),
            ("Slices", str(N)),
            ("Slice Size (avg)", f"{total_shares/N:,.0f} shares"),
            ("Decision Price", f"${decision_price:.2f}"),
        ], columns=["Field", "Value"])
        st.dataframe(order_df, use_container_width=True, hide_index=True)

    with r2:
        st.markdown('<div class="section-header">PRE-TRADE ANALYTICS</div>', unsafe_allow_html=True)
        pretrade_df = pd.DataFrame([
            ("Signal Type", signal_type),
            ("Risk Aversion λ", f"{lambda_risk:.4f}"),
            ("Urgency κ", f"{kappa:.4f}"),
            ("Execution Style", urgency_tag),
            ("Exp. Cost", f"${pre_trade['expected_cost']:,.2f}"),
            ("  Permanent", f"${pre_trade['perm_cost']:,.2f}"),
            ("  Temporary", f"${pre_trade['temp_cost']:,.2f}"),
            ("Cost Std Dev", f"±${pre_trade['std_dev']:,.2f}"),
            ("First Slice %", f"{pre_trade['first_slice_pct']:.1f}%"),
        ], columns=["Field", "Value"])
        st.dataframe(pretrade_df, use_container_width=True, hide_index=True)

    with r3:
        st.markdown('<div class="section-header">POST-TRADE ANALYTICS</div>', unsafe_allow_html=True)
        is_sign = "+" if sim['is_bps'] > 0 else ""
        postrade_df = pd.DataFrame([
            ("Exec VWAP", f"${sim['vwap']:.4f}"),
            ("Decision Price", f"${decision_price:.4f}"),
            ("IS per Share", f"${sim['is_per_share']:.4f}"),
            ("IS Total", f"${sim['is_total']:,.2f}"),
            ("IS (bps)", f"{is_sign}{sim['is_bps']:.1f} bps"),
            ("IS / E[Cost]", f"{ratio:.2f}x"),
            ("Assessment", assess_text[:30] + "..."),
        ], columns=["Field", "Value"])
        st.dataframe(postrade_df, use_container_width=True, hide_index=True)

    # Full schedule table
    st.markdown('<br><div class="section-header">SLICE-BY-SLICE EXECUTION LOG</div>', unsafe_allow_html=True)
    log_rows = []
    cumulative = 0
    for i, (shares_i, fill_i) in enumerate(zip(sim['schedule'], sim['execution_prices'])):
        cumulative += shares_i
        slippage = fill_i - decision_price
        log_rows.append({
            "Slice": i + 1,
            "Time (h)": f"{slice_midpoints[i]:.2f}",
            "Shares": f"{shares_i:,.0f}",
            "Cumulative": f"{cumulative:,.0f}",
            "% Done": f"{cumulative/total_shares*100:.1f}%",
            "Fill Price": f"${fill_i:.4f}",
            "Slippage (bps)": f"{slippage/decision_price*10000:+.1f}",
        })
    log_df = pd.DataFrame(log_rows)
    st.dataframe(log_df, use_container_width=True, hide_index=True, height=350)

# ─────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#21262d; margin-top:40px;">
<div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#6e7681; text-align:center; padding:12px 0;">
    Almgren-Chriss Optimal Execution · VWAP Market Impact Model ·
    Built with Python & Streamlit
</div>
""", unsafe_allow_html=True)
