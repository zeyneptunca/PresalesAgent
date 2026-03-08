"""Merkezi LLM client — Anthropic ve OpenAI provider destegi.

Provider secimi: LLM_PROVIDER env var (anthropic | openai, default: anthropic)
API key: Provider'a gore ANTHROPIC_API_KEY veya OPENAI_API_KEY
"""

import os

# ── Model mapping ────────────────────────────────────────────────────────────

MODEL_MAP = {
    "anthropic": {
        "heavy": "claude-opus-4-6",
        "light": "claude-sonnet-4-6",
    },
    "openai": {
        "heavy": "gpt-4.1",
        "light": "gpt-4o",
    },
}

PROVIDER_KEY_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def get_provider() -> str:
    """Aktif provider'i dondur."""
    return os.environ.get("LLM_PROVIDER", "anthropic").lower()


def get_model_name(tier: str = "heavy") -> str:
    """Tier'a gore model adini dondur."""
    provider = get_provider()
    return MODEL_MAP[provider][tier]


def get_api_key_name() -> str:
    """Aktif provider icin gerekli env var adini dondur."""
    return PROVIDER_KEY_MAP[get_provider()]


def check_api_key() -> tuple[bool, str]:
    """API key kontrolu. (ok, mesaj) tuple dondurur."""
    provider = get_provider()
    key_name = PROVIDER_KEY_MAP.get(provider)
    if not key_name:
        return False, f"Bilinmeyen provider: {provider}. 'anthropic' veya 'openai' olmali."
    key = os.environ.get(key_name)
    if not key:
        return False, (
            f"Provider: {provider}\n"
            f"{key_name} ortam degiskeni ayarlanmamis!\n\n"
            f"export LLM_PROVIDER='{provider}'\n"
            f"export {key_name}='sk-...'"
        )
    return True, f"Provider: {provider} ({get_model_name('heavy')} / {get_model_name('light')})"


# ── API call ─────────────────────────────────────────────────────────────────

def call_llm(
    system: str,
    messages: list[dict],
    tier: str = "heavy",
    max_tokens: int = 16000,
    timeout: int = 600,
) -> str:
    """Tek bir LLM cagirisi. Provider'a gore Anthropic veya OpenAI kullanir.

    Args:
        system: System prompt metni
        messages: [{"role": "user"/"assistant", "content": "..."}]
        tier: "heavy" (opus/gpt-4.1) veya "light" (sonnet/gpt-4o)
        max_tokens: Maksimum cikti token sayisi
        timeout: API timeout (saniye)

    Returns:
        AI yaniti (str)
    """
    provider = get_provider()
    model = MODEL_MAP[provider][tier]

    if provider == "anthropic":
        return _call_anthropic(system, messages, model, max_tokens, timeout)
    elif provider == "openai":
        return _call_openai(system, messages, model, max_tokens, timeout)
    else:
        raise ValueError(f"Bilinmeyen LLM provider: {provider}")


def _call_anthropic(system: str, messages: list[dict], model: str,
                    max_tokens: int, timeout: int) -> str:
    """Anthropic API cagrisi."""
    import anthropic

    client = anthropic.Anthropic(timeout=timeout)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def _call_openai(system: str, messages: list[dict], model: str,
                 max_tokens: int, timeout: int) -> str:
    """OpenAI API cagrisi."""
    from openai import OpenAI

    client = OpenAI(timeout=timeout)

    # OpenAI: system prompt messages dizisinin basina eklenir
    oai_messages = [{"role": "system", "content": system}]
    oai_messages.extend(messages)

    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=oai_messages,
    )
    return response.choices[0].message.content
