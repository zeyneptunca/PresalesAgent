# PresalesAgent — Kurulum Kilavuzu

Bu kilavuz, PresalesAgent'i kendi bilgisayarinizda calistirmak icin gereken TUM adimlari icerir.
Hic bir yazilim bilgisi gerektirmez. Adimlari sirasi ile takip edin.

---

## BOLUM A: macOS Kurulumu

### Adim 1: Terminal'i Ac

1. `Cmd + Space` tusuna basin (Spotlight acar)
2. `Terminal` yazin ve Enter'a basin
3. Siyah/beyaz bir pencere acilacak — tum komutlari buraya yazacaksiniz

### Adim 2: Python Kur

macOS'ta Python genellikle yuklu degildir. Kontrol edin:

```bash
python3 --version
```

Ekranda `Python 3.11.x` veya `Python 3.12.x` gibi bir sey goruyorsaniz → Adim 3'e gecin.

Gormuyorsaniz veya hata aliyorsaniz:

```bash
# Homebrew yukle (Mac icin paket yoneticisi)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python yukle
brew install python@3.12
```

Kurulum bittikten sonra tekrar kontrol edin:
```bash
python3 --version
```

### Adim 3: Projeyi GitHub'dan Indir

```bash
cd ~/Desktop
git clone https://github.com/zeyneptunca/PresalesAgent.git
cd PresalesAgent
```

> **git yuklenmemisse:** `xcode-select --install` komutunu calistirin, acilan pencerede "Install" deyin. Bittikten sonra `git clone` komutunu tekrar calistirin.

### Adim 4: Sanal Ortam (Virtual Environment) Olustur

Sanal ortam, projenin ihtiyac duydugu kutuphaneleri sisteminizin geri kalanindan izole tutar.
Boylece baska projelerle karisma olmaz.

**4a) Sanal ortami olusturun:**
```bash
python3 -m venv .venv
```
Bu komut, `PresalesAgent` klasorunun icine `.venv` adinda gizli bir klasor olusturur.
Biraz bekleyin, 10-20 saniye surebilir.

**4b) Sanal ortami aktif edin:**
```bash
source .venv/bin/activate
```
Basarili olursa satir basinda `(.venv)` yazisi gorursunuz. Ornek:
```
(.venv) kullanici@MacBook PresalesAgent %
```

> **(.venv) yazisini gormuyorsaniz**, bir sonraki adima gecmeyin. Komutu tekrar calistirin.

### Adim 5: Gerekli Kutuphaneleri (Streamlit, Anthropic vb.) Yukle

```bash
pip install -r requirements.txt
```

Bu komut, uygulamanin ihtiyac duydugu tum kutuphaneleri otomatik olarak yukler:
- **streamlit** — web arayuzu
- **anthropic** — Claude AI baglantisi
- **PyMuPDF** — PDF okuma
- **openpyxl** — Excel dosyasi olusturma
- ve diger bagimlliklar...

Yukleme 1-3 dakika surebilir. Ekranda bircok satir akacak, bu normal.
`Successfully installed ...` yazisini gordugunuzde tamamdir.

### Adim 6: API Key Ayarla

PresalesAgent, Claude AI kullanir. Bunun icin bir API anahtari gerekir.

**API anahtarinizi Zeynep'ten isteyin.** Aldiginizda:

```bash
echo 'ANTHROPIC_API_KEY=sk-ant-BURAYA_ANAHTARI_YAPISTIRINIZ' > .env
```

> `sk-ant-BURAYA_ANAHTARI_YAPISTIRINIZ` kismini gercek anahtarla degistirin.

### Adim 7: Uygulamayi Calistir

```bash
streamlit run app.py
```

Tarayicinizda otomatik olarak acilacak: **http://localhost:8501**

> Eger sanal ortam aktif degilse (satir basinda `(.venv)` yoksa), once `source .venv/bin/activate` calistirin.

### Adim 8: Sonraki Kullanimlarda

Bilgisayarinizi kapatip actiktan sonra, her seferinde bu 3 komutu sirayla yazin:
```bash
cd ~/Desktop/PresalesAgent
source .venv/bin/activate
streamlit run app.py
```

Uygulamayi kapatmak icin: Terminal'de `Ctrl + C` basin.

---

## BOLUM B: Windows Kurulumu

### Adim 1: Python Kur

1. Tarayicinizda su adrese gidin: **https://www.python.org/downloads/**
2. **"Download Python 3.12.x"** butonuna tiklayin
3. Indirilen `.exe` dosyasini calistirin
4. **ONEMLI:** Kurulum ekraninda **"Add Python to PATH"** kutucugunu MUTLAKA isaretleyin ✅
5. "Install Now" tiklayin ve bitmesini bekleyin

### Adim 2: Git Kur

1. Tarayicinizda su adrese gidin: **https://git-scm.com/download/win**
2. Otomatik indirme baslar. Indirilen `.exe`'yi calistirin
3. Tum ayarlari varsayilan (default) birakin, Next-Next-Install

### Adim 3: Komut Satirini Ac

1. `Windows tusu + R` basin
2. `cmd` yazin ve Enter'a basin
3. Siyah bir pencere acilir

Python'un yuklenigini kontrol edin:
```cmd
python --version
```
`Python 3.12.x` gibi bir cikti gormalisiniz.

### Adim 4: Projeyi Indir

```cmd
cd %USERPROFILE%\Desktop
git clone https://github.com/zeyneptunca/PresalesAgent.git
cd PresalesAgent
```

### Adim 5: Sanal Ortam (Virtual Environment) Olustur

Sanal ortam, projenin ihtiyac duydugu kutuphaneleri sisteminizin geri kalanindan izole tutar.

**5a) Sanal ortami olusturun:**
```cmd
python -m venv .venv
```
Bu komut, `PresalesAgent` klasorunun icine `.venv` adinda bir klasor olusturur.
Biraz bekleyin, 10-30 saniye surebilir.

**5b) Sanal ortami aktif edin:**
```cmd
.venv\Scripts\activate
```
Basarili olursa satir basinda `(.venv)` yazisi gorursunuz. Ornek:
```
(.venv) C:\Users\Ahmet\Desktop\PresalesAgent>
```

> **(.venv) yazisini gormuyorsaniz**, bir sonraki adima gecmeyin. Komutu tekrar calistirin.

### Adim 6: Gerekli Kutuphaneleri (Streamlit, Anthropic vb.) Yukle

```cmd
pip install -r requirements.txt
```

Bu komut, uygulamanin ihtiyac duydugu tum kutuphaneleri otomatik olarak yukler:
- **streamlit** — web arayuzu
- **anthropic** — Claude AI baglantisi
- **PyMuPDF** — PDF okuma
- **openpyxl** — Excel dosyasi olusturma
- ve diger bagimlliklar...

Yukleme 1-3 dakika surebilir. Ekranda bircok satir akacak, bu normal.
`Successfully installed ...` yazisini gordugunuzde tamamdir.

### Adim 7: API Key Ayarla

**API anahtarinizi Zeynep'ten isteyin.** Aldiginizda:

Not Defteri'ni acin ve icine su tek satiri yazin (anahtari degistirin):
```
ANTHROPIC_API_KEY=sk-ant-BURAYA_ANAHTARI_YAPISTIRINIZ
```
"Farkli Kaydet" ile **PresalesAgent** klasorune `.env` adinda kaydedin.
(Dosya turu: "Tum Dosyalar" secin, yoksa `.env.txt` olarak kaydeder)

### Adim 8: Uygulamayi Calistir

```cmd
streamlit run app.py
```

Tarayicinizda otomatik olarak acilacak: **http://localhost:8501**

> Eger sanal ortam aktif degilse (satir basinda `(.venv)` yoksa), once `.venv\Scripts\activate` calistirin.

### Adim 9: Sonraki Kullanimlarda

Bilgisayarinizi kapatip actiktan sonra, her seferinde bu 3 komutu sirayla yazin:
```cmd
cd %USERPROFILE%\Desktop\PresalesAgent
.venv\Scripts\activate
streamlit run app.py
```

Uygulamayi kapatmak icin: Komut satirinda `Ctrl + C` basin.

---

## SSS (Sik Sorulan Sorular)

**S: "pip: command not found" hatasi aliyorum**
C: Python kurulumunda "Add to PATH" secenegini isaremediniz. Python'u kaldirip tekrar kurun, bu sefer kutucugu isaretleyin.

**S: "streamlit: command not found" hatasi aliyorum**
C: Sanal ortami aktif etmediniz. `source .venv/bin/activate` (Mac) veya `.venv\Scripts\activate` (Windows) komutunu calistirin.

**S: "ANTHROPIC_API_KEY not set" hatasi aliyorum**
C: `.env` dosyasini olusturmadiniz veya yanlis yere koydunuz. `.env` dosyasi `PresalesAgent` klasorunun icinde olmali.

**S: Uygulama acildi ama hicbir proje yok**
C: Normal. Yeni proje olusturmak icin "Yeni Proje" butonuna tiklayin ve bir PDF yukleyin.

**S: Tarayici otomatik acilmadi**
C: Tarayicinizda su adresi elle yazin: http://localhost:8501

**S: Guncellemeleri nasil alirim?**
C: Terminal/Komut satirinda:
```bash
cd ~/Desktop/PresalesAgent   # Mac
cd %USERPROFILE%\Desktop\PresalesAgent   # Windows

git pull origin main
```

---

## Gereksinimler Ozeti

| Gereksinim | Aciklama |
|---|---|
| Python | 3.11 veya ustu |
| Git | Projeyi indirmek icin |
| API Key | Anthropic API anahtari (Zeynep'ten isteyin) |
| Tarayici | Chrome, Firefox, Safari, Edge — herhangi biri |
| Internet | API cagrilari icin gerekli |
| Disk Alani | ~100 MB |
| RAM | 4 GB yeterli |
