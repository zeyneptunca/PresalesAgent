"""Login ekrani — koyu lacivert tema, stilize P logosu, Streamlit-native form."""

import streamlit as st

from src.auth import start_login, verify_code, validate_email_domain, ALLOWED_DOMAIN


# ── Login sayfasi CSS ────────────────────────────────────────────────────────

_LOGIN_CSS = """
<style>
/* Tum sayfa koyu lacivert arka plan */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a1628 0%, #0f2044 50%, #0a1628 100%);
    min-height: 100vh;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stMainBlockContainer"] { max-width: 1200px; }

/* Sol kolon — brand metinleri */
.login-title {
    color: #ffffff !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    text-align: center;
    margin-top: 0.8rem !important;
    margin-bottom: 0 !important;
    letter-spacing: 0.02em;
}
.login-subtitle {
    color: rgba(180,200,230,0.8) !important;
    font-size: 1.1rem !important;
    font-weight: 300 !important;
    text-align: center;
    letter-spacing: 0.05em;
}

/* Sag kolon — beyaz kart */
.login-card-wrapper {
    background: #ffffff;
    border-radius: 18px;
    padding: 2.5rem 2rem 2rem 2rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    max-width: 420px;
    margin: 0 auto;
}
.login-card-wrapper h2 {
    color: #1a2744 !important;
    font-size: 1.6rem !important;
    margin-bottom: 0.2rem !important;
}
.login-card-wrapper p,
.login-card-wrapper .subtitle {
    color: #888 !important;
    font-size: 0.9rem !important;
    margin-bottom: 1.5rem !important;
}
.login-card-wrapper p b {
    color: #1a2744 !important;
}

/* Kart icindeki form input'lari */
.login-card-wrapper [data-testid="stTextInput"] input {
    background: #fff !important;
    border: 1.5px solid #ddd !important;
    border-radius: 8px !important;
    padding: 0.7rem 1rem !important;
    font-size: 1rem !important;
    color: #333 !important;
}
.login-card-wrapper [data-testid="stTextInput"] input:focus {
    border-color: #1a3a6b !important;
    box-shadow: 0 0 0 2px rgba(26,58,107,0.15) !important;
}
.login-card-wrapper [data-testid="stTextInput"] label {
    color: #333 !important;
    font-weight: 500 !important;
}

/* Submit buton */
.login-card-wrapper .stFormSubmitButton > button {
    background: linear-gradient(135deg, #1a3a6b 0%, #0f2044 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.7rem 1rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    transition: all 0.2s;
}
.login-card-wrapper .stFormSubmitButton > button:hover {
    background: linear-gradient(135deg, #244d8a 0%, #1a3a6b 100%) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

/* Kart icindeki secondary butonlar */
.login-card-wrapper button[kind="secondary"] {
    color: #1a3a6b !important;
    border-color: #ccc !important;
}

/* KocSistem footer */
.login-footer {
    text-align: center;
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #eee;
}
.login-footer .ks-brand {
    font-weight: 700;
    font-size: 1rem;
}
.login-footer .ks-koc { color: #cc2233; }
.login-footer .ks-sistem { color: #1a3a6b; }
.login-footer .ks-sub {
    font-size: 0.65rem;
    color: #999;
    margin-top: 2px;
}

/* Logo container ortalama */
.logo-container {
    display: flex;
    justify-content: center;
    margin-top: 8vh;
}
</style>
"""

# ── Stilize P Logosu (SVG) ───────────────────────────────────────────────────

_P_LOGO_SVG = """
<div class="logo-container">
<svg width="160" height="180" viewBox="0 0 180 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="pgrad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#c0c8d8;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#8898b0;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="pgrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#cc2233;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#991122;stop-opacity:1" />
    </linearGradient>
    <filter id="pshadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="3" dy="5" stdDeviation="6" flood-color="rgba(0,0,0,0.35)"/>
    </filter>
  </defs>
  <path d="M 40,25 L 70,25 L 70,180 L 40,180 Z" fill="url(#pgrad1)" filter="url(#pshadow)"/>
  <path d="M 65,25 Q 150,25 150,75 Q 150,125 65,125" fill="none" stroke="url(#pgrad1)"
        stroke-width="30" stroke-linecap="round" filter="url(#pshadow)"/>
  <path d="M 55,65 L 55,180" stroke="url(#pgrad2)" stroke-width="12" stroke-linecap="round"/>
  <path d="M 125,50 L 155,35 L 148,55" fill="none" stroke="#c0c8d8" stroke-width="4"
        stroke-linecap="round" stroke-linejoin="round" opacity="0.9"/>
</svg>
</div>
"""


# ── Ana render ───────────────────────────────────────────────────────────────


def show_login():
    """Login sayfasini goster."""

    # State defaults
    if "login_step" not in st.session_state:
        st.session_state.login_step = "email"
    if "login_email" not in st.session_state:
        st.session_state.login_email = ""
    if "login_session" not in st.session_state:
        st.session_state.login_session = ""
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""

    # CSS enjekte et
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # ── 2 Sutunlu Layout: Sol (brand) | Sag (form karti) ──
    col_left, col_space, col_right = st.columns([1.1, 0.2, 1], gap="large")

    # ────── SOL: Logo + Brand ──────
    with col_left:
        # SVG logo
        st.markdown(_P_LOGO_SVG, unsafe_allow_html=True)

        # Baslik — CSS class ile stillendirilmis
        st.markdown('<p class="login-title">PresalesAgent</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="login-subtitle">Kurumsal Yazilim Efor Tahmini</p>',
            unsafe_allow_html=True,
        )

    # ────── SAG: Beyaz Kart ──────
    with col_right:
        # Bosluk — karti dikeyde ortala
        st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)

        # Kart acilis
        st.markdown('<div class="login-card-wrapper">', unsafe_allow_html=True)

        # Hata mesaji
        if st.session_state.login_error:
            st.error(st.session_state.login_error)
            st.session_state.login_error = ""

        if st.session_state.login_step == "email":
            _show_email_step()
        elif st.session_state.login_step == "code":
            _show_code_step()

        # KocSistem footer
        st.markdown(
            '<div class="login-footer">'
            '<div class="ks-brand">'
            '<span class="ks-koc">Koc</span>'
            '<span class="ks-sistem">Sistem</span>'
            '</div>'
            '<div class="ks-sub">Turkey\'s Leading ICT Company</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Kart kapanis
        st.markdown('</div>', unsafe_allow_html=True)


# ── Form Adimlari ────────────────────────────────────────────────────────────


def _show_email_step():
    """Asama 1: E-posta girisi."""
    st.markdown(
        '<h2>Giris Yap</h2>'
        '<p class="subtitle">Hesabiniza giris yapin</p>',
        unsafe_allow_html=True,
    )

    with st.form("login_email_form"):
        email = st.text_input(
            "E-posta",
            placeholder=f"adiniz@{ALLOWED_DOMAIN}",
            key="login_email_input",
        )
        submitted = st.form_submit_button(
            "Giris Kodu Gonder", type="primary", use_container_width=True
        )

    if submitted and email:
        email = email.strip().lower()

        if not validate_email_domain(email):
            st.session_state.login_error = (
                f"Sadece @{ALLOWED_DOMAIN} adresleri kabul edilir."
            )
            st.rerun()
            return

        with st.spinner("Kod gonderiliyor..."):
            result = start_login(email)

        if "error" in result:
            st.session_state.login_error = result["error"]
            st.rerun()
        else:
            st.session_state.login_email = email
            st.session_state.login_session = result["session"]
            st.session_state.login_step = "code"
            if result.get("status") == "CODE_SENT_DEV":
                st.session_state.login_error = (
                    "Dev modu — Kod terminal'e yazdirildi. "
                    "Cognito yapilandirilinca e-postaya gelecek."
                )
            st.rerun()


def _show_code_step():
    """Asama 2: OTP kod dogrulama."""
    email = st.session_state.login_email

    st.markdown(
        '<h2>Dogrulama</h2>'
        '<p class="subtitle">'
        f'<b>{email}</b> adresine kod gonderildi</p>',
        unsafe_allow_html=True,
    )

    with st.form("login_code_form"):
        code = st.text_input(
            "Dogrulama Kodu",
            max_chars=8,
            placeholder="12345678",
            key="login_code_input",
        )
        submitted = st.form_submit_button(
            "Giris Yap", type="primary", use_container_width=True
        )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Tekrar Gonder", use_container_width=True, key="btn_resend"):
            result = start_login(email)
            if "error" in result:
                st.session_state.login_error = result["error"]
            else:
                st.session_state.login_session = result["session"]
                st.toast("Yeni kod gonderildi!")
            st.rerun()
    with col2:
        if st.button("Farkli E-posta", use_container_width=True, key="btn_diff_email"):
            st.session_state.login_step = "email"
            st.session_state.login_email = ""
            st.session_state.login_session = ""
            st.rerun()

    if submitted and code:
        with st.spinner("Dogrulaniyor..."):
            result = verify_code(
                email, code.strip(), st.session_state.login_session
            )

        if "error" in result:
            st.session_state.login_error = result["error"]
            st.rerun()
        elif result.get("authenticated"):
            st.session_state.auth_user = {
                "email": result["email"],
                "is_admin": result["is_admin"],
            }
            st.session_state.login_step = "email"
            st.session_state.login_email = ""
            st.session_state.login_session = ""
            st.session_state.login_error = ""
            st.rerun()
