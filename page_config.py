import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="Loan Score Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
    :root {
        --box-bg: #f8f9fa;
        --box-border: #e9ecef;
        --box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
        --text-color: #333333;
        --label-color: #888888;
        --meta-border: #eaeaea;
        --meta-val: #0055cc;
        --header-color: #888888;
        --header-border: #eaeaea;
        --whatif-bg: #fcfcfc;
        
        --inline-val: #111111;
        --inline-lbl: #555555;
        --inline-arrow: #555555;
        
        --band-vp-text: #c0392b;
        --band-vp-bg: #fdedec;
        --band-p-text: #d35400;
        --band-p-bg: #fdf2e9;
        --band-f-text: #8e44ad;
        --band-f-bg: #f5eef8;
        --band-g-text: #27ae60;
        --band-g-bg: #eafaf1;
        --band-e-text: #0055cc;
        --band-e-bg: #ebf5fb;
    }

    /* Dark mode override removed to prevent system dark mode from clashing with Streamlit light mode */

    html, body, [class*="css"] {
        font-family: 'DM Mono', monospace;
    }

    .score-box {
        background: var(--box-bg);
        border: 1px solid var(--box-border);
        border-radius: 12px;
        padding: 28px 20px 20px;
        text-align: center;
        margin-bottom: 16px;
        box-shadow: var(--box-shadow);
        color: var(--text-color);
    }

    .score-number {
        font-family: 'Syne', sans-serif;
        font-size: 88px;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -4px;
        margin: 0;
    }
    .score-label {
        font-size: 11px;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: var(--label-color);
        margin-bottom: 4px;
    }
    .score-band {
        display: inline-block;
        margin-top: 10px;
        padding: 4px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 500;
        letter-spacing: 1px;
    }
    .meta-row {
        display: flex;
        justify-content: space-around;
        margin-top: 14px;
        padding-top: 14px;
        border-top: 1px solid var(--meta-border);
    }
    .meta-item { text-align: center; }
    .meta-val { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 700; color: var(--meta-val); }
    .meta-lbl { font-size: 10px; color: var(--label-color); letter-spacing: 2px; text-transform: uppercase; }

    .section-header {
        font-size: 16px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--header-color);
        margin: 20px 0 10px;
        padding-bottom: 6px;
        border-bottom: 1px solid var(--header-border);
    }
    .whatif-box {
        background: var(--whatif-bg);
        border: 1px solid var(--box-border);
        border-radius: 10px;
        padding: 16px;
        margin-top: 12px;
    }
    </style>
    """, unsafe_allow_html=True)