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

    /* === SIDEBAR BASE === */
    [data-testid="stSidebar"] {
        background-color: #f8f9fb;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.8rem !important;
    }

    /* Sidebar butonlari — daha kompakt, daha ince */
    [data-testid="stSidebar"] .stButton > button {
        font-size: 0.82rem !important;
        padding: 0.3rem 0.7rem !important;
        font-weight: 500 !important;
        border-color: #e2e8f0 !important;
        color: #475569 !important;
        background: transparent !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #eef2ff !important;
        border-color: #c7d2fe !important;
        color: #0066CC !important;
        transform: none;
        box-shadow: none;
    }
    /* Sidebar primary buton (Yeni Proje) override */
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #0066CC !important;
        border-color: #0066CC !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 0.55rem 1rem !important;
        justify-content: center !important;
        text-align: center !important;
        letter-spacing: 0.3px;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background-color: #0052a3 !important;
        color: white !important;
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(0, 102, 204, 0.25);
    }
    /* Sidebar secondary buton (genel) */
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
        color: #475569 !important;
        border-color: #e2e8f0 !important;
        font-size: 0.82rem !important;
        padding: 0.3rem 0.7rem !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
        background: #eef2ff !important;
        border-color: #c7d2fe !important;
    }

    /* === SIDEBAR BRAND === */
    .sb-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0.4rem 0.2rem 0.2rem 0.2rem;
    }
    .sb-brand-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background: linear-gradient(135deg, #0066CC, #4f46e5);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1.1rem;
        flex-shrink: 0;
    }
    .sb-brand-text { flex: 1; }
    .sb-brand-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #1e293b;
        letter-spacing: -0.3px;
        line-height: 1.2;
    }
    .sb-brand-sub {
        font-size: 0.68rem;
        color: #94a3b8;
        margin-top: 1px;
    }

    /* === SIDEBAR SPACERS === */
    .sb-spacer-sm { height: 0.3rem; }
    .sb-spacer-md { height: 0.6rem; }
    .sb-spacer-lg { height: 1rem; }

    /* === SIDEBAR SECTION HEADER === */
    .sb-section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 0.2rem 0.5rem 0.2rem;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 0.5rem;
    }
    .sb-section-header span {
        font-size: 0.65rem;
        font-weight: 700;
        color: #94a3b8;
        letter-spacing: 1.5px;
    }
    .sb-section-badge {
        font-size: 0.62rem !important;
        font-weight: 700 !important;
        color: #94a3b8 !important;
        background: #e2e8f0;
        border-radius: 10px;
        padding: 1px 7px;
        letter-spacing: 0 !important;
    }

    /* === SIDEBAR EMPTY STATE === */
    .sb-empty {
        font-size: 0.78rem;
        color: #94a3b8;
        padding: 0.8rem 0.5rem;
        text-align: center;
        font-style: italic;
    }

    /* === SIDEBAR AKTIF PROJE (disabled button) === */
    [data-testid="stSidebar"] .stButton > button:disabled {
        background: #eef2ff !important;
        border: 1px solid #c7d2fe !important;
        color: #0066CC !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        cursor: default !important;
    }
    .sb-active-status {
        font-size: 0.58rem;
        font-weight: 400;
        color: #6366f1;
        padding-left: calc(12% + 0.7rem);
        margin-top: -0.6rem;
        line-height: 1;
    }
    .sb-dot-active {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: block;
        background: #0066CC;
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.2);
    }

    /* Sidebar columns dikey ortalama */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }

    /* === SIDEBAR PROJE DOT === */
    .sb-dot-col {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .sb-project-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        display: block;
    }
    .sb-dot-done { background: #16a34a; }
    .sb-dot-progress { background: #f59e0b; }
    .sb-dot-new { background: #d1d5db; }

    /* === SIDEBAR WIZARD STEPS === */
    .sb-wizard-steps {
        padding: 0.3rem 0 0.2rem 1rem;
        margin: 0;
        border-left: 2px solid #c7d2fe;
        margin-left: 1rem;
    }
    .sb-step {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
        margin: 1px 0;
    }
    .sb-step-active {
        background: #dbeafe;
    }
    .sb-step-pending {
        opacity: 0.45;
    }
    .sb-step-done .sb-step-num {
        background: #16a34a;
        color: white;
    }
    .sb-step-done .sb-step-label {
        color: #16a34a;
    }
    .sb-step-num {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.62rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .sb-step-active .sb-step-num {
        background: #0066CC;
        color: white;
    }
    .sb-step-pending .sb-step-num {
        background: #cbd5e1;
        color: #64748b;
    }
    .sb-step-label {
        font-size: 0.76rem;
        font-weight: 600;
    }
    .sb-step-active .sb-step-label {
        color: #1e40af;
    }
    .sb-step-pending .sb-step-label {
        color: #94a3b8;
    }

    /* === SIDEBAR SETTINGS === */
    .sb-settings, .sb-settings-active {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0.45rem 0.7rem;
        border-radius: 8px;
        font-size: 0.82rem;
        margin-top: 0.3rem;
    }
    .sb-settings-active {
        background: #eef2ff;
        color: #0066CC;
        font-weight: 700;
        border: 1px solid #c7d2fe;
    }
    .sb-settings-icon {
        font-size: 1rem;
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
