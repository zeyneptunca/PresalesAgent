#!/bin/bash
# PresalesAgent — Mac/Linux kurulum scripti
# Kullanim: curl -sSL https://raw.githubusercontent.com/zeyneptunca/PresalesAgent/main/install.sh | bash

set -e

echo ""
echo "================================================"
echo "  PresalesAgent Kurulum"
echo "================================================"
echo ""

# Python kontrolu
if ! command -v python3 &> /dev/null; then
    echo "HATA: Python 3 bulunamadi!"
    echo "  Mac:   brew install python3"
    echo "  Linux: sudo apt install python3 python3-pip"
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PY_VERSION"

# Kurulum dizini
INSTALL_DIR="$HOME/PresalesAgent"
echo "  Kurulum dizini: $INSTALL_DIR"

# Repo klonla veya guncelle
if [ -d "$INSTALL_DIR" ]; then
    echo "  Mevcut kurulum guncelleniyor..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "  Repo klonlaniyor..."
    git clone https://github.com/zeyneptunca/PresalesAgent.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Virtual environment
if [ ! -d ".venv" ]; then
    echo "  Sanal ortam olusturuluyor..."
    python3 -m venv .venv
fi

echo "  Bagimliliklar yukleniyor..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

# Calisma dizinleri
mkdir -p uploads wbs wbs/.raw_responses output projects config

# Baslat scripti
cat > "$INSTALL_DIR/start.sh" << 'STARTEOF'
#!/bin/bash
cd "$(dirname "$0")"

if [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo ""
    echo "  API key gerekli! Asagidakilerden birini calistirin:"
    echo ""
    echo "  Anthropic:"
    echo "    export ANTHROPIC_API_KEY='sk-ant-...'"
    echo "    ./start.sh"
    echo ""
    echo "  OpenAI:"
    echo "    export LLM_PROVIDER=openai"
    echo "    export OPENAI_API_KEY='sk-...'"
    echo "    ./start.sh"
    echo ""
    exit 1
fi

.venv/bin/python -m streamlit run app.py --server.port=8501 --server.headless=true
STARTEOF
chmod +x "$INSTALL_DIR/start.sh"

echo ""
echo "================================================"
echo "  Kurulum tamamlandi!"
echo "================================================"
echo ""
echo "  Baslatmak icin:"
echo "    cd $INSTALL_DIR"
echo "    export ANTHROPIC_API_KEY='sk-ant-...'"
echo "    ./start.sh"
echo ""
echo "  Tarayicida: http://localhost:8501"
echo ""
