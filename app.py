import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from page_config import setup_page

# =========================
# PAGE CONFIGURATION
# =========================
setup_page()

# =========================
# MODEL PARAMETERS
# =========================
SCALE_PATH = "/Users/thinh/VSC Workspace/Py/da prj/input/aft_scale_parameter.csv"
COEFF_PATH = "/Users/thinh/VSC Workspace/Py/da prj/input/aft_coefficient_result.csv"
TRAIN_PATH = "/Users/thinh/VSC Workspace/Py/da prj/input/data_loan_dev_80_stratified.csv"

@st.cache_data
def load_data():
    scale_df = pd.read_csv(SCALE_PATH)
    coeff_df = pd.read_csv(COEFF_PATH)
    df_train = pd.read_csv(TRAIN_PATH)
    return scale_df, coeff_df, df_train

scale_df, coeff_df, df_train = load_data()

kappa     = scale_df.loc[scale_df["Parameter"] == "Shape Parameter", "Value"].values[0]
intercept = scale_df.loc[scale_df["Parameter"] == "Intercept", "Value"].values[0]

retained  = coeff_df[coeff_df["%_p<0.05"] >= 60.0]
beta      = dict(zip(retained["covariate"], retained["Mean_Beta"]))
FEATURES  = list(beta.keys())

# =========================
# FICO BINNING
# =========================
def fico_to_stage(score):
    if score < 580:   return 1
    elif score < 670: return 2
    elif score < 740: return 3
    elif score < 800: return 4
    else:             return 5

# =========================
# SCORE BAND
# =========================
def score_band(s):
    if s < 450:   return ("VERY POOR",  "var(--band-vp-text)", "var(--band-vp-bg)")
    elif s < 550: return ("POOR",       "var(--band-p-text)",  "var(--band-p-bg)")
    elif s < 650: return ("FAIR",       "var(--band-f-text)",  "var(--band-f-bg)")
    elif s < 750: return ("GOOD",       "var(--band-g-text)",  "var(--band-g-bg)")
    else:         return ("EXCELLENT",  "var(--band-e-text)",  "var(--band-e-bg)")

# =========================
# TABS
# =========================
tab1, tab2 = st.tabs(["RISK CALCULATOR", "MODEL COEFFICIENTS"])

# =========================
# TAB 2 — MODEL COEFFICIENTS (Config first)
# =========================
with tab2:
    st.markdown("### PDO METHOD")
    cal1, cal2 = st.columns(2)
    with cal1:
        PDO = st.slider("PDO", 10, 50, 20, help="Points to double odds")
    with cal2:
        TARGET_SCORE = st.slider("Target score", 300, 850, 580)

    Factor = PDO / np.log(2)

    st.divider()
    st.markdown("### AFT LOG-LOGISTIC MODEL COEFFICIENTS")
    st.dataframe(coeff_df, use_container_width=True)
    st.markdown("### SCALE PARAMETERS")
    st.dataframe(scale_df, use_container_width=True)

# =========================
# TAB 1 — RISK CALCULATOR
# =========================
# =========================
# TAB 1 — RISK CALCULATOR
# =========================
if "calculated" not in st.session_state:
    st.session_state.calculated = False

def do_calculate():
    st.session_state.calculated = True

def do_reset():
    st.session_state.calculated = False

with tab1:
    # ── LAYOUT ───────────────────────────────────────────────────────────
    top_left, top_right = st.columns([1.1, 1.5], gap="large")

    with top_left:
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            T = st.selectbox("Reference Months", options=list(range(36, 66, 6)), index=2)
        
        # Calculate exact odds dynamically based on selected Reference Month T
        bad_mask_train  = (df_train["defaulted"] == 1) & (df_train["time_to_default"] <= T)
        n_bad_train     = bad_mask_train.sum()
        n_good_train    = len(df_train) - n_bad_train
        exact_odds      = n_good_train / n_bad_train if n_bad_train > 0 else 10.0
        Offset          = TARGET_SCORE - Factor * np.log(exact_odds)
        
        with t_col2:
            if st.session_state.calculated:
                st.metric("Base Odds (Good:Bad)", f"{exact_odds:.2f}")
            else:
                st.metric("Base Odds (Good:Bad)", "—")
        
        st.markdown('<div class="section-header">Portfolio Characteristics</div>', unsafe_allow_html=True)

        col_left, col_right = st.columns(2)
        with col_left:
            loan_amount_raw = st.number_input("Loan Amount (USD)", min_value=4000, max_value=120000, value=15000, step=500, disabled=st.session_state.calculated)
            interest_rate = st.number_input("Interest Rate (%)", min_value=5.0, max_value=25.0, value=12.0, step=0.1, disabled=st.session_state.calculated)
            annual_income = st.number_input("Annual Income (USD)", min_value=7000, max_value=690000, value=60000, step=1000, disabled=st.session_state.calculated)

        with col_right:
            term_val = st.selectbox("Loan Term (Months)", options=[36, 60], index=0, disabled=st.session_state.calculated)
            fico_raw = st.number_input("FICO Score", min_value=300, max_value=850, value=680, step=1, disabled=st.session_state.calculated)

        term = 1 if term_val == 60 else 0

        # ── Derived inputs ──
        Log_loan_amount   = np.log(loan_amount_raw)
        Log_annual_income = np.log(annual_income)
        fico_stage        = fico_to_stage(fico_raw)
        monthly_rate      = (interest_rate / 100) / 12
        n_payments        = term_val
        PMT               = loan_amount_raw * monthly_rate / (1 - (1 + monthly_rate) ** (-n_payments)) if monthly_rate > 0 else loan_amount_raw / n_payments
        PTI_rescaling     = (PMT / (annual_income / 12)) * 10

        x_input = {
            "interest_rate":      interest_rate,
            "fico_stage":         fico_stage,
            "term_months_binary": term,
            "Log_loan_amount":    Log_loan_amount,
            "Log_annual_income":  Log_annual_income,
            "PTI_rescaling":      PTI_rescaling,
        }

        if not st.session_state.calculated:
            st.button("Calculate", on_click=do_calculate, type="primary")
        else:
            st.button("Calculate a new portfolio", on_click=do_reset)

    if st.session_state.calculated:
        bot_left, bot_right = st.columns([1.1, 1.5], gap="large")

        with bot_left:
            st.markdown('<div class="section-header" style="margin-top:20px;">Modification</div>', unsafe_allow_html=True)
            mod_loan_amount = st.slider(f"Loan Amount (USD) [Original: {loan_amount_raw}]", 4000, 120000, int(loan_amount_raw), 500, key="mod_loan")
            mod_term_val = st.select_slider(f"Loan Term (Months) [Original: {term_val}]", options=[36, 60], value=int(term_val), key="mod_term_slider")
            mod_interest = st.slider(f"Interest Rate (%) [Original: {interest_rate}]", 5.0, 25.0, float(interest_rate), 0.1, key="mod_int")
            mod_annual_income = st.slider(f"Annual Income (USD) [Original: {annual_income}]", 7000, 690000, int(annual_income), 1000, key="mod_income")
            
            mod_term = 1 if mod_term_val == 60 else 0
            mod_monthly_rate = (mod_interest / 100) / 12
            mod_n_payments   = mod_term_val
            mod_PMT          = mod_loan_amount * mod_monthly_rate / (1 - (1 + mod_monthly_rate) ** (-mod_n_payments)) if mod_monthly_rate > 0 else mod_loan_amount / mod_n_payments
            mod_PTI_rescaling = (mod_PMT / (mod_annual_income / 12)) * 10

            mod_x_input = {
                "interest_rate":      mod_interest,
                "fico_stage":         fico_stage,
                "term_months_binary": mod_term,
                "Log_loan_amount":    np.log(mod_loan_amount),
                "Log_annual_income":  np.log(mod_annual_income),
                "PTI_rescaling":      mod_PTI_rescaling,
            }

        # ── SCORE COMPUTE ──
        def compute_linear(x):
            return intercept + sum(beta[k] * x[k] for k in FEATURES)

        def compute_score(x, factor, offset, t, kap):
            xb = compute_linear(x)
            eta = np.exp(xb)
            S = 1.0 / (1.0 + (t / eta) ** kap)
            S = np.clip(S, 1e-9, 1 - 1e-9)
            log_odds = np.log(S / (1 - S))
            return float(np.clip(offset + factor * log_odds, 300, 850)), eta, S

        score_val, eta, S_val = compute_score(x_input, Factor, Offset, T, kappa)
        score_int = int(round(score_val))
        
        score_wi, eta_wi, S_wi = compute_score(mod_x_input, Factor, Offset, T, kappa)
        score_wi = float(np.clip(score_wi, 300, 850))
        score_wi_int = int(round(score_wi))
        delta_score = score_wi - score_val

        with top_right:
            band_label, band_color, band_bg = score_band(score_int)
            score_color = band_color
            PD_val = 1 - S_val
            eta_months = eta

            mod_band_label, mod_band_color, mod_band_bg = score_band(score_wi_int)
            mod_PD_val = 1 - S_wi
            mod_eta_months = eta_wi
            
            delta_str = f"{delta_score:+.1f} pts"
            delta_color = '#2ecc71' if delta_score >= 0 else '#e74c3c'
            
            st.markdown(f"""
            <div class="score-box" style="border-width: 2px; border-color: {mod_band_color}; padding: 30px 20px; min-height: 285px; display: flex; flex-direction: column; justify-content: center;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex:1;">
                    <div style="text-align:center; flex:1;">
                        <div class="score-label" style="font-size:16px;">Original Score</div>
                        <div class="score-number" style="color:{score_color}; font-size:48px;">{score_int}</div>
                        <div><span class="score-band" style="color:{band_color}; background:{band_bg}; font-size:12px; padding:4px 8px;">{band_label}</span></div>
                        <div style="font-size:14px; margin-top:12px; color:var(--inline-lbl); line-height:1.4;">
                            <div>Default Probability: <span style="font-size:16px; font-weight:bold; color:var(--inline-val);">{PD_val:.1%}</span></div>
                            <div>Median Survival Time: <span style="font-size:16px; font-weight:bold; color:var(--inline-val);">{eta_months:.1f}m</span></div>
                        </div>
                    </div>
                    <div style="font-size:42px; color:var(--inline-arrow); padding:0 20px;">&rarr;</div>
                    <div style="text-align:center; flex:1;">
                        <div class="score-label" style="font-size:16px;">Modified Score</div>
                        <div class="score-number" style="color:{mod_band_color}; font-size:56px;">{score_wi_int}</div>
                        <div><span class="score-band" style="color:{mod_band_color}; background:{mod_band_bg}; font-size:14px; padding:4px 10px;">{mod_band_label}</span></div>
                        <div style="font-size:14px; margin-top:12px; color:var(--inline-lbl); line-height:1.4;">
                            <div>Default Probability: <span style="font-size:16px; font-weight:bold; color:var(--inline-val);">{mod_PD_val:.1%}</span></div>
                            <div>Median Survival Time: <span style="font-size:16px; font-weight:bold; color:var(--inline-val);">{mod_eta_months:.1f}m</span></div>
                        </div>
                    </div>
                </div>
                <div style="text-align:center; margin-top: 25px; font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: {delta_color};">
                    Change: {delta_str}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with bot_right:
            # CONTRIBUTION CHART
            base_lin = compute_linear(mod_x_input)
            contributions = {}
            for f in FEATURES:
                x_zero = {k: (0.0 if k == f else mod_x_input[k]) for k in FEATURES}
                contributions[f] = (beta[f] * mod_x_input[f]) * Factor * kappa  # approx score pts

            FEATURE_LABELS = {
                "interest_rate":      "Interest Rate",
                "fico_stage":         "FICO Stage",
                "term_months_binary": "Loan Term",
                "Log_loan_amount":    "Loan Amount",
                "Log_annual_income":  "Annual Income",
                "PTI_rescaling":      "Payment to Income",
            }

            chart_df = pd.DataFrame({
                "Feature": [FEATURE_LABELS.get(f, f) for f in FEATURES],
                "Points": [contributions[f] for f in FEATURES],
            })
            chart_df["Color"] = chart_df["Points"].apply(lambda v: "Positive" if v >= 0 else "Negative")
            chart_df = chart_df.sort_values("Points")

            chart_df["Start"] = 580
            chart_df["End"] = 580 + chart_df["Points"]

            st.markdown('<div class="section-header" style="margin-top:20px;">Variable Contributions (Points)</div>', unsafe_allow_html=True)

            max_abs = chart_df["Points"].abs().max()
            max_abs = max_abs if pd.notna(max_abs) and max_abs > 0 else 10

            base_bar = (
                alt.Chart(chart_df)
                .mark_bar(cornerRadiusEnd=4)
                .encode(
                    x=alt.X("Start:Q", title="Score Points (580 = Base Score)", axis=alt.Axis(grid=False), scale=alt.Scale(domain=[580-max_abs-10, 580+max_abs+10])),
                    x2=alt.X2("End:Q"),
                    y=alt.Y("Feature:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, labelColor="#888", labelFont="DM Mono", labelLimit=200)),
                    color=alt.Color(
                        "Color:N",
                        scale=alt.Scale(domain=["Positive", "Negative"], range=["#2ecc71", "#e74c3c"]),
                        legend=None
                    ),
                    tooltip=["Feature", alt.Tooltip("Points:Q", format=".2f")]
                )
            )

            text_pos = base_bar.mark_text(
                align='left', baseline='middle', dx=3, color='white'
            ).encode(
                x=alt.X("End:Q"),
                text=alt.Text('Points:Q', format='+.1f')
            ).transform_filter(alt.datum.Points >= 0)

            text_neg = base_bar.mark_text(
                align='right', baseline='middle', dx=-3, color='white'
            ).encode(
                x=alt.X("End:Q"),
                text=alt.Text('Points:Q', format='+.1f')
            ).transform_filter(alt.datum.Points < 0)

            bar = (base_bar + text_pos + text_neg).properties(height=300).configure_view(strokeWidth=0).configure_axis(domainColor="#888", tickColor="#888", labelColor="#888", labelFontSize=14)

            st.altair_chart(bar, use_container_width=True)