"""UI tema ve custom CSS bilesenleri."""

import streamlit as st


def inject_custom_css():
    """Uygulamaya custom CSS enjekte eder. app.py basinda bir kez cagrilir."""
    st.markdown("""
    <style>
    /* === GENEL LAYOUT === */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px;
    }

    /* === METRIC KARTLAR === */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f0f4f8, #ffffff);
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }

    /* === BUTONLAR === */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        padding: 0.4rem 1rem !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 102, 204, 0.2);
    }
    .stButton > button[kind="primary"] {
        background-color: #0066CC !important;
        border-color: #0066CC !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #0052a3 !important;
    }

    /* === EXPANDER === */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        background-color: #f8f9fb !important;
        border-radius: 8px !important;
    }

    /* === CONTAINER BORDER (kart stili) === */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
    }

    /* === DATAFRAME === */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 600;
    }

    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background-color: #f8f9fb;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
    }

    /* === DIVIDER === */
    hr {
        margin: 1rem 0 !important;
        border-color: #e2e8f0 !important;
    }

    /* === STEP INDICATOR === */
    .step-container {
        display: flex;
        justify-content: center;
        align-items: flex-start;
        gap: 0;
        margin: 0.5rem auto 1.5rem auto;
        max-width: 700px;
    }
    .step-item {
        text-align: center;
        position: relative;
        flex: 1;
        min-width: 80px;
    }
    .step-item:not(:last-child)::after {
        content: '';
        position: absolute;
        top: 17px;
        left: 55%;
        width: 90%;
        height: 3px;
        background: #dee2e6;
        z-index: 0;
    }
    .step-item.step-completed:not(:last-child)::after {
        background: #28a745;
    }
    .step-item.step-active:not(:last-child)::after {
        background: linear-gradient(90deg, #0066CC 50%, #dee2e6 50%);
    }
    .step-circle {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.9rem;
        position: relative;
        z-index: 1;
        transition: all 0.3s ease;
    }
    .step-completed .step-circle {
        background: #28a745;
        color: white;
        box-shadow: 0 2px 6px rgba(40, 167, 69, 0.3);
    }
    .step-active .step-circle {
        background: #0066CC;
        color: white;
        box-shadow: 0 2px 8px rgba(0, 102, 204, 0.4);
        animation: pulse-step 2s ease-in-out infinite;
    }
    .step-pending .step-circle {
        background: #dee2e6;
        color: #6c757d;
    }
    .step-label {
        margin-top: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        color: #6c757d;
        line-height: 1.2;
    }
    .step-active .step-label {
        color: #0066CC;
        font-weight: 700;
    }
    .step-completed .step-label {
        color: #28a745;
    }
    @keyframes pulse-step {
        0%, 100% { box-shadow: 0 2px 8px rgba(0, 102, 204, 0.4); }
        50% { box-shadow: 0 2px 16px rgba(0, 102, 204, 0.6); }
    }

    /* === SIDEBAR NAV === */
    .nav-item {
        padding: 0.6rem 1rem;
        border-radius: 8px;
        margin-bottom: 4px;
        font-size: 0.88rem;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: background 0.15s ease;
    }
    .nav-item.active {
        background: #e8f0fe;
        color: #0066CC;
        font-weight: 700;
    }
    .nav-item.completed {
        color: #28a745;
    }
    .nav-item.pending {
        color: #9ca3af;
    }
    .nav-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }
    .nav-dot.active { background: #0066CC; }
    .nav-dot.completed { background: #28a745; }
    .nav-dot.pending { background: #d1d5db; }

    /* === CHAT === */
    [data-testid="stChatMessage"] {
        border-radius: 12px !important;
        margin-bottom: 0.5rem !important;
    }

    /* === FORM === */
    [data-testid="stForm"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        background: #fafbfc !important;
    }

    /* === TIMELINE (History Tab) === */
    .timeline-item {
        position: relative;
        padding: 0.8rem 0 0.8rem 2rem;
        border-left: 2px solid #e2e8f0;
        margin-left: 0.5rem;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -5px;
        top: 1.1rem;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #0066CC;
    }
    .timeline-item.timeline-calc::before {
        background: #28a745;
        width: 10px;
        height: 10px;
        left: -6px;
    }
    .timeline-item.timeline-wbs::before {
        background: #6366f1;
    }
    .timeline-item.timeline-scope::before {
        background: #f59e0b;
    }

    /* === PROJECT CARD HOVER === */
    .project-card-container [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: box-shadow 0.2s ease;
    }

    /* === VERSION BADGE === */
    .version-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background: #e8f0fe;
        color: #0066CC;
    }
    .version-badge.active {
        background: #28a745;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
