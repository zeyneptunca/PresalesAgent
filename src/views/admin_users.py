"""Admin kullanici yonetimi ekrani.

Sadece admin rolundeki kullanicilar erisebilir.
Whitelist'e kullanici ekleme/silme islemleri yapar.
"""

import streamlit as st

from src.auth import (
    load_allowed_users,
    add_user,
    remove_user,
    update_user_role,
    validate_email_domain,
    ALLOWED_DOMAIN,
)


def show_admin_users():
    """Admin kullanici yonetimi sayfasi."""

    auth_user = st.session_state.get("auth_user")
    if not auth_user or not auth_user.get("is_admin"):
        st.error("Bu sayfaya erisim yetkiniz yok.")
        return

    st.title("Kullanici Yonetimi")
    st.caption("Uygulamaya giris yapabilecek kullanicilari yonetin.")

    # ── Mevcut Kullanicilar ──────────────────────────────────────────────

    data = load_allowed_users()
    users = data.get("allowed_users", [])

    st.markdown(f"### Kayitli Kullanicilar ({len(users)})")

    if not users:
        st.info("Henuz kullanici eklenmemis.")
    else:
        for i, user in enumerate(users):
            with st.container():
                cols = st.columns([3, 2, 1.5, 1.5, 1])
                with cols[0]:
                    st.markdown(f"**{user['email']}**")
                with cols[1]:
                    st.markdown(user.get("name", "-"))
                with cols[2]:
                    role = user.get("role", "user")
                    if role == "admin":
                        st.markdown(":orange[Admin]")
                    else:
                        st.markdown("Kullanici")
                with cols[3]:
                    st.caption(user.get("added_at", "-"))
                with cols[4]:
                    # Kendini silemesin
                    is_self = user["email"].lower() == auth_user["email"].lower()
                    if not is_self:
                        if st.button("Sil", key=f"del_{i}", type="secondary"):
                            st.session_state[f"confirm_delete_{i}"] = True

                # Silme onayi
                if st.session_state.get(f"confirm_delete_{i}"):
                    st.warning(
                        f"**{user['email']}** kullanicisini silmek istediginize emin misiniz?"
                    )
                    c1, c2, _ = st.columns([1, 1, 3])
                    with c1:
                        if st.button("Evet, Sil", key=f"yes_del_{i}", type="primary"):
                            remove_user(user["email"])
                            del st.session_state[f"confirm_delete_{i}"]
                            st.toast(f"{user['email']} silindi.")
                            st.rerun()
                    with c2:
                        if st.button("Iptal", key=f"no_del_{i}"):
                            del st.session_state[f"confirm_delete_{i}"]
                            st.rerun()

            if i < len(users) - 1:
                st.divider()

    # ── Yeni Kullanici Ekle ──────────────────────────────────────────────

    st.markdown("---")
    st.markdown("### Yeni Kullanici Ekle")

    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            new_email = st.text_input(
                "E-posta Adresi",
                placeholder=f"isim.soyisim@{ALLOWED_DOMAIN}",
            )
        with col2:
            new_name = st.text_input("Ad Soyad", placeholder="Ahmet Yilmaz")

        new_role = st.selectbox("Rol", ["user", "admin"], format_func=lambda r: "Kullanici" if r == "user" else "Admin")

        submitted = st.form_submit_button(
            "Kullanici Ekle", type="primary", use_container_width=True
        )

    if submitted:
        if not new_email or not new_name:
            st.error("E-posta ve Ad Soyad alanlari zorunludur.")
        elif not validate_email_domain(new_email):
            st.error(f"Sadece @{ALLOWED_DOMAIN} adresleri eklenebilir.")
        else:
            ok = add_user(new_email, new_name, new_role)
            if ok:
                st.toast(f"{new_email} basariyla eklendi!")
                st.rerun()
            else:
                st.warning("Bu e-posta adresi zaten kayitli.")
