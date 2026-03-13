"""AWS Cognito EMAIL_OTP + whitelist tabanli kimlik dogrulama.

Akis:
1. Kullanici email girer
2. allowed_users.json whitelist kontrolu
3. Cognito'da kullanici yoksa olusturulur
4. EMAIL_OTP challenge baslatilir (Cognito otomatik kod gonderir)
5. Kullanici kodu girer → Cognito dogrular → token doner
"""

import json
import os
import secrets
from datetime import datetime
from pathlib import Path

USERS_FILE = Path("config/allowed_users.json")
ALLOWED_DOMAIN = "kocsistem.com.tr"


# ── Whitelist Yonetimi ──────────────────────────────────────────────────────


def load_allowed_users() -> dict:
    """allowed_users.json oku. Dosya yoksa bos yapi dondur."""
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text("utf-8"))
    return {"admin_emails": [], "allowed_users": []}


def save_allowed_users(data: dict) -> None:
    """allowed_users.json yaz."""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    USERS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", "utf-8"
    )


def is_allowed(email: str) -> bool:
    """E-posta whitelist'te mi?"""
    data = load_allowed_users()
    email_lower = email.strip().lower()
    return any(
        u["email"].lower() == email_lower for u in data.get("allowed_users", [])
    )


def is_admin(email: str) -> bool:
    """E-posta admin mi?"""
    data = load_allowed_users()
    email_lower = email.strip().lower()
    return email_lower in [e.lower() for e in data.get("admin_emails", [])]


def validate_email_domain(email: str) -> bool:
    """Sadece izin verilen domain'i kabul et."""
    return email.strip().lower().endswith(f"@{ALLOWED_DOMAIN}")


def add_user(email: str, name: str, role: str = "user") -> bool:
    """Whitelist'e kullanici ekle. Zaten varsa False dondur."""
    data = load_allowed_users()
    email_lower = email.strip().lower()

    if any(u["email"].lower() == email_lower for u in data["allowed_users"]):
        return False

    data["allowed_users"].append(
        {
            "email": email_lower,
            "name": name.strip(),
            "role": role,
            "added_at": datetime.now().strftime("%Y-%m-%d"),
        }
    )

    if role == "admin" and email_lower not in [
        e.lower() for e in data["admin_emails"]
    ]:
        data["admin_emails"].append(email_lower)

    save_allowed_users(data)
    return True


def remove_user(email: str) -> bool:
    """Whitelist'ten kullanici sil. Yoksa False dondur."""
    data = load_allowed_users()
    email_lower = email.strip().lower()

    original_count = len(data["allowed_users"])
    data["allowed_users"] = [
        u for u in data["allowed_users"] if u["email"].lower() != email_lower
    ]
    data["admin_emails"] = [
        e for e in data["admin_emails"] if e.lower() != email_lower
    ]

    if len(data["allowed_users"]) == original_count:
        return False

    save_allowed_users(data)
    return True


def update_user_role(email: str, new_role: str) -> bool:
    """Kullanicinin rolunu degistir."""
    data = load_allowed_users()
    email_lower = email.strip().lower()

    for user in data["allowed_users"]:
        if user["email"].lower() == email_lower:
            user["role"] = new_role
            if new_role == "admin" and email_lower not in [
                e.lower() for e in data["admin_emails"]
            ]:
                data["admin_emails"].append(email_lower)
            elif new_role != "admin":
                data["admin_emails"] = [
                    e for e in data["admin_emails"] if e.lower() != email_lower
                ]
            save_allowed_users(data)
            return True
    return False


# ── Cognito Islemleri ────────────────────────────────────────────────────────


def _get_cognito_client():
    """Boto3 Cognito client olustur."""
    import boto3

    return boto3.client(
        "cognito-idp",
        region_name=os.environ.get("AWS_REGION", "eu-central-1"),
    )


def _cognito_configured() -> bool:
    """Cognito ortam degiskenleri ayarli mi?"""
    return bool(
        os.environ.get("COGNITO_USER_POOL_ID")
        and os.environ.get("COGNITO_CLIENT_ID")
    )


def start_login(email: str) -> dict:
    """Login akisini baslat.

    1. Whitelist kontrolu
    2. Cognito'da kullanici yoksa olustur
    3. EMAIL_OTP challenge baslat

    Returns:
        {"session": "...", "status": "CODE_SENT"} basarili
        {"error": "..."} hata
    """
    email = email.strip().lower()

    # Domain kontrolu
    if not validate_email_domain(email):
        return {"error": f"Sadece @{ALLOWED_DOMAIN} adresleri ile giris yapilabilir."}

    # Whitelist kontrolu
    if not is_allowed(email):
        return {
            "error": "Bu e-posta adresi ile giris izni yok. Yoneticinizle iletisime gecin."
        }

    # Cognito yapilandirilmamissa dev modu
    if not _cognito_configured():
        return _dev_mode_login(email)

    client = _get_cognito_client()
    pool_id = os.environ["COGNITO_USER_POOL_ID"]
    client_id = os.environ["COGNITO_CLIENT_ID"]

    # Cognito'da kullanici var mi?
    try:
        client.admin_get_user(UserPoolId=pool_id, Username=email)
    except client.exceptions.UserNotFoundException:
        _sign_up_user(client, pool_id, client_id, email)
    except Exception as e:
        return {"error": f"Cognito hatasi: {e}"}

    # EMAIL_OTP challenge baslat
    try:
        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PREFERRED_CHALLENGE": "EMAIL_OTP",
            },
        )
        return {"session": response["Session"], "status": "CODE_SENT"}
    except Exception as e:
        return {"error": f"Kod gonderme hatasi: {e}"}


def verify_code(email: str, code: str, session: str) -> dict:
    """OTP kodunu dogrula.

    Returns:
        {"authenticated": True, "email": "...", "is_admin": bool, ...} basarili
        {"error": "..."} hata
    """
    email = email.strip().lower()

    # Dev modu
    if not _cognito_configured():
        return _dev_mode_verify(email, code, session)

    client = _get_cognito_client()
    client_id = os.environ["COGNITO_CLIENT_ID"]

    try:
        response = client.respond_to_auth_challenge(
            ClientId=client_id,
            ChallengeName="EMAIL_OTP",
            Session=session,
            ChallengeResponses={
                "USERNAME": email,
                "EMAIL_OTP_CODE": code,
            },
        )

        if "AuthenticationResult" in response:
            return {
                "authenticated": True,
                "email": email,
                "is_admin": is_admin(email),
                "id_token": response["AuthenticationResult"].get("IdToken"),
                "access_token": response["AuthenticationResult"].get("AccessToken"),
            }
        return {"error": "Dogrulama basarisiz. Kodu kontrol edin."}
    except Exception as e:
        err = str(e)
        if "CodeMismatchException" in err or "NotAuthorizedException" in err:
            return {"error": "Kod hatali. Tekrar deneyin."}
        if "ExpiredCodeException" in err:
            return {"error": "Kodun suresi doldu. Yeni kod gonderin."}
        return {"error": f"Dogrulama hatasi: {e}"}


def _sign_up_user(client, pool_id: str, client_id: str, email: str) -> None:
    """Yeni Cognito kullanicisi olustur (whitelist'te olan kisi icin)."""
    temp_pw = secrets.token_urlsafe(32) + "!A1"  # Cognito password policy uyumu
    client.sign_up(
        ClientId=client_id,
        Username=email,
        Password=temp_pw,
        UserAttributes=[{"Name": "email", "Value": email}],
    )
    # Admin confirm — kullanici hemen aktif, email dogrulama gerekmez
    client.admin_confirm_sign_up(UserPoolId=pool_id, Username=email)


# ── Dev Modu (Cognito olmadan test) ──────────────────────────────────────────


def _dev_mode_login(email: str) -> dict:
    """Cognito yapilandirilmamissa: kodu konsola yaz, session olarak sakla."""
    code = f"{secrets.randbelow(900000) + 100000}"  # 6 haneli
    print(f"\n{'='*50}")
    print(f"  DEV MODE — OTP Kodu: {code}")
    print(f"  Email: {email}")
    print(f"{'='*50}\n")
    return {"session": f"dev_{code}", "status": "CODE_SENT_DEV"}


def _dev_mode_verify(email: str, code: str, session: str) -> dict:
    """Dev modunda kod dogrulama."""
    expected = session.replace("dev_", "")
    if code == expected:
        return {
            "authenticated": True,
            "email": email,
            "is_admin": is_admin(email),
            "id_token": None,
            "access_token": None,
        }
    return {"error": "Kod hatali. (Dev modu — kodu terminal'de gorabilirsiniz)"}
