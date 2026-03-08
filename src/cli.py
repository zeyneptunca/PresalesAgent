"""PresalesAgent CLI — tek komutla uygulamayi baslatir."""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """presalesagent komutu ile Streamlit uygulamasini baslatir."""

    # app.py'nin konumunu bul (paket icinden)
    package_dir = Path(__file__).resolve().parent.parent
    app_path = package_dir / "app.py"

    if not app_path.exists():
        # pip install ile kurulduysa, src dizininin ust klasorunde arar
        # Alternatif: site-packages icindeki konum
        possible = [
            Path(sys.prefix) / "app.py",
            Path(__file__).resolve().parent.parent / "app.py",
        ]
        for p in possible:
            if p.exists():
                app_path = p
                break
        else:
            print("Hata: app.py bulunamadi.")
            print(f"Aranan konumlar: {[str(p) for p in possible]}")
            sys.exit(1)

    # Calisma dizinini app.py'nin oldugu yere ayarla
    os.chdir(app_path.parent)

    # Gerekli dizinleri olustur
    for d in ["uploads", "wbs", "wbs/.raw_responses", "output", "projects", "config"]:
        Path(d).mkdir(parents=True, exist_ok=True)

    # API key kontrolu
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if not os.environ.get(key_name):
        print(f"\n{'='*50}")
        print(f"  PresalesAgent")
        print(f"{'='*50}")
        print(f"\n  {key_name} ortam degiskeni gerekli!\n")
        print(f"  Mac/Linux:")
        print(f"    export {key_name}='sk-...'")
        print(f"    presalesagent")
        print(f"\n  Windows:")
        print(f"    set {key_name}=sk-...")
        print(f"    presalesagent")
        print(f"\n  OpenAI kullanmak icin:")
        print(f"    export LLM_PROVIDER=openai")
        print(f"    export OPENAI_API_KEY='sk-...'")
        print(f"{'='*50}\n")
        sys.exit(1)

    print(f"\n  PresalesAgent baslatiliyor...")
    print(f"  Provider: {provider}")
    print(f"  Tarayicida acilacak: http://localhost:8501\n")

    # Streamlit'i baslat
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ])


if __name__ == "__main__":
    main()
