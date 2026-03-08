@echo off
REM PresalesAgent — Windows kurulum scripti
REM Kullanim: Bu dosyayi indirip cift tikla

echo.
echo ================================================
echo   PresalesAgent Kurulum
echo ================================================
echo.

REM Python kontrolu
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi!
    echo   https://www.python.org/downloads/ adresinden indirin
    echo   Kurulumda "Add Python to PATH" secenegini isaretleyin
    pause
    exit /b 1
)

REM Kurulum dizini
set INSTALL_DIR=%USERPROFILE%\PresalesAgent
echo   Kurulum dizini: %INSTALL_DIR%

REM Repo klonla veya guncelle
if exist "%INSTALL_DIR%" (
    echo   Mevcut kurulum guncelleniyor...
    cd /d "%INSTALL_DIR%"
    git pull origin main
) else (
    echo   Repo klonlaniyor...
    git clone https://github.com/zeyneptunca/PresalesAgent.git "%INSTALL_DIR%"
    cd /d "%INSTALL_DIR%"
)

REM Virtual environment
if not exist ".venv" (
    echo   Sanal ortam olusturuluyor...
    python -m venv .venv
)

echo   Bagimliliklar yukleniyor...
.venv\Scripts\pip install --quiet --upgrade pip
.venv\Scripts\pip install --quiet -r requirements.txt

REM Calisma dizinleri
if not exist uploads mkdir uploads
if not exist wbs mkdir wbs
if not exist "wbs\.raw_responses" mkdir "wbs\.raw_responses"
if not exist output mkdir output
if not exist projects mkdir projects
if not exist config mkdir config

REM Baslat scripti
(
echo @echo off
echo cd /d "%%~dp0"
echo if "%%ANTHROPIC_API_KEY%%"=="" if "%%OPENAI_API_KEY%%"=="" ^(
echo     echo.
echo     echo   API key gerekli! Asagidaki komutlari calistirin:
echo     echo.
echo     echo   Anthropic:
echo     echo     set ANTHROPIC_API_KEY=sk-ant-...
echo     echo     start.bat
echo     echo.
echo     echo   OpenAI:
echo     echo     set LLM_PROVIDER=openai
echo     echo     set OPENAI_API_KEY=sk-...
echo     echo     start.bat
echo     echo.
echo     pause
echo     exit /b 1
echo ^)
echo .venv\Scripts\python -m streamlit run app.py --server.port=8501 --server.headless=true
) > "%INSTALL_DIR%\start.bat"

echo.
echo ================================================
echo   Kurulum tamamlandi!
echo ================================================
echo.
echo   Baslatmak icin:
echo     cd %INSTALL_DIR%
echo     set ANTHROPIC_API_KEY=sk-ant-...
echo     start.bat
echo.
echo   Tarayicida: http://localhost:8501
echo.
pause
