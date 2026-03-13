# PresalesAgent — Kurulum Kilavuzu

Bu kilavuz, PresalesAgent'i kendi bilgisayarinizda calistirmak icin gereken TUM adimlari icerir.
Hic bir yazilim bilgisi gerektirmez. Adimlari sirasi ile takip edin.

> **ONEMLI:** Her komutu TEK TEK yazin ve Enter'a basin. Bir sonraki komuta gecmeden once
> mevcut komutun bitmesini bekleyin. Komutlari toplu olarak kopyala-yapistir YAPMAYIN.

---

## BOLUM A: macOS Kurulumu

### Adim 1: Terminal'i Ac

1. Klavyenizde `Cmd + Space` tuslarina basin (Spotlight arama acilir)
2. Acilan arama kutusuna `Terminal` yazin
3. Cikan sonuclardan **Terminal** uygulamasina tiklayin
4. Siyah veya beyaz bir pencere acilacak

Bu pencereye **Terminal** denir. Tum komutlari buraya yazacaksiniz.
Ekraninizda su sekilde bir satir goreceksiniz:

```
kullanici@MacBook ~ %
```

Bu satira **komut satiri** denir. Yanip sonen imleciniz burada bekliyor.
Komutlari bu satira yazip Enter'a basacaksiniz.

---

### Adim 2: Python Kur

Python, uygulamanin calistigi programlama dilidir. Bilgisayarinizda yuklu olmayabilir.

**Once kontrol edin.** Terminal'e su komutu yazin ve Enter'a basin:

```bash
python3 --version
```

**Gorecekleriniz (2 ihtimal):**

**Ihtimal 1 — Python yuklu (GUZEL):**
```
Python 3.11.5
```
veya `Python 3.12.x` gibi bir sayi goruyorsaniz Python zaten yuklu. **Adim 3'e gecin.**

**Ihtimal 2 — Python yuklu DEGIL:**
```
command not found: python3
```
veya buna benzer bir hata goruyorsaniz, Python yuklemeniz gerekiyor.

**Python yuklemek icin:**

Oncelikle Homebrew'u yukleyin (Mac icin paket yoneticisi).
Su komutu Terminal'e yapisitirin ve Enter'a basin:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

> Bu komut sifrenizi sorabilir. Mac giris sifrenizi yazin (yazarken ekranda hicbir sey gozukmez, bu normal).
> Yukleme 2-5 dakika surebilir. "Installation successful" yazisini gorene kadar bekleyin.

Simdi Python'u yukleyin. Terminal'e su komutu yazin ve Enter'a basin:
```bash
brew install python@3.12
```

> Yukleme 1-3 dakika surebilir. Ekranda bircok satir akacak, bu normal.

Yukleme bittikten sonra tekrar kontrol edin:
```bash
python3 --version
```

Artik `Python 3.12.x` goruyor olmalisiniz.

---

### Adim 3: Projeyi GitHub'dan Indir

Simdi projenin dosyalarini bilgisayariniza indireceksiniz.

**3a) Masaustune gidin.** Terminal'e su komutu yazin ve Enter'a basin:
```bash
cd ~/Desktop
```

> Bu komut sizi masaustune goturur. Ekranda yeni bir satir cikar, hata mesaji yoksa basarilidir:
> ```
> kullanici@MacBook Desktop %
> ```
> Dikkat edin: artik satirin sonunda `Desktop` yaziyor. Bu, masaustundesiniz demektir.

**3b) Projeyi indirin.** Su komutu yazin ve Enter'a basin:
```bash
git clone https://github.com/zeyneptunca/PresalesAgent.git
```

> Ekranda su sekilde satirlar goreceksiniz:
> ```
> Cloning into 'PresalesAgent'...
> remote: Enumerating objects: 245, done.
> remote: Counting objects: 100% (245/245), done.
> ...
> ```
> Indirme bittikten sonra masaustunuzde `PresalesAgent` adinda bir klasor olusur.

**Eger "git: command not found" hatasi alirsiniz:**
Su komutu calistirin ve acilan pencerede "Install" butonuna tiklayin:
```bash
xcode-select --install
```
Yukleme bittikten sonra `git clone` komutunu tekrar calistirin.

**3c) Proje klasorune girin.** Su komutu yazin ve Enter'a basin:
```bash
cd PresalesAgent
```

> Satir sonu artik soyle gorunmeli:
> ```
> kullanici@MacBook PresalesAgent %
> ```
> `PresalesAgent` yazisini goruyorsaniz dogru klasordesiniz.

---

### Adim 4: Sanal Ortam (Virtual Environment) Olustur

Sanal ortam, projenin ihtiyac duydugu kutuphaneleri sisteminizin geri kalanindan izole tutar.
Boylece baska projelerle karisma olmaz. **Bundan sonraki TUM komutlari `PresalesAgent` klasorunun icinde calistiracaksiniz.**

> Kontrol: Satir sonunda `PresalesAgent %` yaziyor mu?
> Yazmiyorsa `cd ~/Desktop/PresalesAgent` yazin ve Enter'a basin.

**4a) Sanal ortami olusturun.** Su komutu yazin ve Enter'a basin:
```bash
python3 -m venv .venv
```

> Ekranda HICBIR SEY YAZMAYABILIR — bu normal. Komut 10-20 saniye surebilir.
> Islem bittiginde yeni bir bos satir cikar ve imlec tekrar yanip soner.
> Bu, sanal ortamin basariyla olusturuldugu anlamina gelir.

**4b) Sanal ortami aktif edin.** Su komutu yazin ve Enter'a basin:
```bash
source .venv/bin/activate
```

**Gorecekleriniz:**
```
(.venv) kullanici@MacBook PresalesAgent %
```

Satir basinda **(.venv)** yazisini gormeniz SART.
Bu yazi, sanal ortamin aktif oldugunu gosterir.

> **(.venv) yazisini GORMUYORSANIZ:**
> Bir sonraki adima GECMEYIN. Komutu tekrar yazip Enter'a basin.
> Hala gelmiyorsa, 4a adimini tekrar calistirin, sonra 4b'yi tekrar deneyin.

---

### Adim 5: Gerekli Kutuphaneleri Yukle

Bu adimda uygulama icin gereken tum ek yazilimlari (Streamlit, Anthropic, PDF okuyucu vb.) yukleyeceksiniz.

> Kontrol: Satir basinda **(.venv)** yazisi var mi?
> Yoksa once `source .venv/bin/activate` calistirin.

Su komutu yazin ve Enter'a basin:
```bash
pip install -r requirements.txt
```

**Gorecekleriniz:**
Ekranda bircok satir hizla akacak. Bu tamamen normal. Ornek:
```
Collecting streamlit==1.45.1
  Downloading streamlit-1.45.1-py2.py3-none-any.whl (9.9 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 9.9/9.9 MB 12.5 MB/s eta 0:00:00
Collecting anthropic>=0.40.0
  Downloading anthropic-0.52.0-py3-none-any.whl (237 kB)
...
Successfully installed anthropic-0.52.0 streamlit-1.45.1 PyMuPDF-1.25.5 ...
```

> Yukleme **1-3 dakika** surebilir. Sabirin.
> En sonda **"Successfully installed ..."** yazisini gordugunuzde tamamdir.
> Hata alirsiniz "ERROR" yazisi gorursunuz, Zeynep'e haber verin.

---

### Adim 6: API Key Ayarla

PresalesAgent, Claude AI kullanir. Bunun icin bir API anahtari gerekir.
**API anahtarinizi Zeynep'ten isteyin.** `sk-ant-...` ile baslayan uzun bir metin olacak.

> Kontrol: Hala `PresalesAgent` klasorunde misiniz?
> Satir sonunda `PresalesAgent` yazisi var mi? Yoksa `cd ~/Desktop/PresalesAgent` yazin.

Aldiginiz anahtari asagidaki komutta yerine koyun ve Enter'a basin:
```bash
echo 'ANTHROPIC_API_KEY=sk-ant-BURAYA_GERCEK_ANAHTARI_YAPISTIRINIZ' > .env
```

> **ORNEK:** Zeynep size `sk-ant-api03-abc123xyz` diye bir anahtar verdiyse, komut soyle olur:
> ```bash
> echo 'ANTHROPIC_API_KEY=sk-ant-api03-abc123xyz' > .env
> ```

> Ekranda hicbir sey yazmayacak — bu normal. Dosya sessizce olusturulur.

---

### Adim 7: Uygulamayi Calistir

> Kontrol: Satir basinda **(.venv)** yazisi var mi?
> Yoksa once `source .venv/bin/activate` calistirin.

Su komutu yazin ve Enter'a basin:
```bash
streamlit run app.py
```

**Gorecekleriniz:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.5:8501
```

Tarayiciniz (Chrome, Safari vb.) otomatik olarak acilacak ve uygulama gorunecek.
Eger otomatik acilmazsa, tarayicinizi acin ve adres cubuguna `http://localhost:8501` yazin.

**Uygulamayi kapatmak icin:** Terminal'e donun ve `Ctrl + C` tuslarina basin.

---

### Adim 8: Sonraki Kullanimlarda (Bilgisayari kapatip actiginda)

Bilgisayarinizi her kapatip actiginizda, uygulamayi tekrar baslatmak icin bu **3 komutu sirayla** yazin.
Her komutu yazin, Enter'a basin, sonraki komuta gecin.

**Komut 1 — Proje klasorune git:**
```bash
cd ~/Desktop/PresalesAgent
```
> Satir sonunda `PresalesAgent` yazisini goreceksiniz.

**Komut 2 — Sanal ortami aktif et:**
```bash
source .venv/bin/activate
```
> Satir basinda `(.venv)` yazisini goreceksiniz.

**Komut 3 — Uygulamayi baslat:**
```bash
streamlit run app.py
```
> Tarayici otomatik acilacak.

**Uygulamayi kapatmak icin:** Terminal'de `Ctrl + C` basin.

---

## BOLUM B: Windows Kurulumu

### Adim 1: Python Kur

Python, uygulamanin calistigi programlama dilidir.

1. Tarayicinizi acin (Chrome, Edge vb.)
2. Adres cubuguna su adresi yazip Enter'a basin: **https://www.python.org/downloads/**
3. Sayfadaki buyuk sari **"Download Python 3.12.x"** butonuna tiklayin
4. Indirilen `.exe` dosyasini calistirin (genelde sol altta veya indirilenler klasorunde)
5. **KRITIK ADIM:** Kurulum ekraninda en altta **"Add python.exe to PATH"** yazisi var.
   Yanindaki kutucugu **MUTLAKA ISARETLEYIN** (tik atin).
   Bu isaretlenmezse komutlar calismaz.
6. **"Install Now"** butonuna tiklayin
7. Kurulum bitmesini bekleyin (1-2 dakika). "Setup was successful" yazisini gorun ve kapatin.

---

### Adim 2: Git Kur

Git, projeyi GitHub'dan indirmek icin gereken bir aractir.

1. Tarayicinizda su adrese gidin: **https://git-scm.com/download/win**
2. Sayfa acilinca indirme otomatik baslar. Baslamazsa "Click here to download" linkine tiklayin.
3. Indirilen `.exe` dosyasini calistirin
4. Acilan kurucu pencerelerinde hicbir seyi degistirmeyin. Sadece **Next → Next → Next → Install** tiklayin.
5. Kurulum bitince **Finish** tiklayin.

---

### Adim 3: Komut Satirini Ac

1. Klavyenizde `Windows tusu + R` tuslarina ayni anda basin
2. Acilan kucuk pencereye `cmd` yazin ve Enter'a basin (veya Tamam'a tiklayin)
3. Siyah bir pencere acilacak. Bu pencereye **Komut Satiri (Command Prompt)** denir.

Ekranin sol ustunde su sekilde bir yazi goreceksiniz:
```
C:\Users\Ahmet>
```
(Ahmet yerine sizin Windows kullanici adiniz yazar)

Bu satira **komut satiri** denir. Tum komutlari buraya yazacaksiniz.

**Once Python'un yuklengini kontrol edin.** Su komutu yazin ve Enter'a basin:
```cmd
python --version
```

**Gorecekleriniz (2 ihtimal):**

**Ihtimal 1 — Python yuklu (GUZEL):**
```
Python 3.12.4
```
Bu yaziyi goruyorsaniz Python dogru yuklenmis. **Adim 4'e gecin.**

**Ihtimal 2 — Hata:**
```
'python' is not recognized as an internal or external command
```
Bu hatay goruyorsaniz: Python kurulumunda "Add to PATH" kutucugunu isaretlemediniz.
Python'u Windows ayarlarindan kaldirin ve **Adim 1'i bastan** tekrarlayin.
Bu sefer kutucugu isaretlemeyi unutmayin.

---

### Adim 4: Projeyi Indir

Simdi projenin dosyalarini bilgisayariniza indireceksiniz.

**4a) Masaustune gidin.** Su komutu yazin ve Enter'a basin:
```cmd
cd %USERPROFILE%\Desktop
```

> Ekranda su sekilde gorunecek:
> ```
> C:\Users\Ahmet\Desktop>
> ```
> `Desktop` yazisini goruyorsaniz masaustundesiniz.

**4b) Projeyi indirin.** Su komutu yazin ve Enter'a basin:
```cmd
git clone https://github.com/zeyneptunca/PresalesAgent.git
```

> Ekranda su sekilde satirlar goreceksiniz:
> ```
> Cloning into 'PresalesAgent'...
> remote: Enumerating objects: 245, done.
> remote: Counting objects: 100% (245/245), done.
> ...
> ```
> Indirme bittikten sonra masaustunuzde `PresalesAgent` adinda bir klasor olusur.

**Eger "git is not recognized" hatasi alirsiniz:**
Git kurulumunu (Adim 2) tekrarlayin. Kurulumdan sonra komut satirini KAPATIN ve TEKRAR ACIN.

**4c) Proje klasorune girin.** Su komutu yazin ve Enter'a basin:
```cmd
cd PresalesAgent
```

> Ekranda su sekilde gorunmeli:
> ```
> C:\Users\Ahmet\Desktop\PresalesAgent>
> ```
> `PresalesAgent` yazisini goruyorsaniz dogru yerdesiniz.

---

### Adim 5: Sanal Ortam (Virtual Environment) Olustur

Sanal ortam, projenin ihtiyac duydugu kutuphaneleri sisteminizin geri kalanindan izole tutar.
**Bundan sonraki TUM komutlari `PresalesAgent` klasorunun icinde calistiracaksiniz.**

> Kontrol: Satir sonunda `PresalesAgent>` yaziyor mu?
> Yazmiyorsa `cd %USERPROFILE%\Desktop\PresalesAgent` yazin ve Enter'a basin.

**5a) Sanal ortami olusturun.** Su komutu yazin ve Enter'a basin:
```cmd
python -m venv .venv
```

> Ekranda HICBIR SEY YAZMAYABILIR — bu normal. Komut 10-30 saniye surebilir.
> Islem bittiginde yeni bir bos satir cikar ve imlec tekrar yanip soner:
> ```
> C:\Users\Ahmet\Desktop\PresalesAgent>
> ```
> Bu, sanal ortamin basariyla olusturuldugu anlamina gelir.

**5b) Sanal ortami aktif edin.** Su komutu yazin ve Enter'a basin:
```cmd
.venv\Scripts\activate
```

**Gorecekleriniz:**
```
(.venv) C:\Users\Ahmet\Desktop\PresalesAgent>
```

Satir basinda **(.venv)** yazisini gormeniz SART.

> **(.venv) yazisini GORMUYORSANIZ:**
> Bir sonraki adima GECMEYIN. Komutu tekrar yazip Enter'a basin.
> Hala gelmiyorsa, 5a adimini tekrar calistirin, sonra 5b'yi tekrar deneyin.

---

### Adim 6: Gerekli Kutuphaneleri Yukle

Bu adimda uygulama icin gereken tum ek yazilimlari yukleyeceksiniz.

> Kontrol: Satir basinda **(.venv)** yazisi var mi?
> Yoksa once `.venv\Scripts\activate` calistirin.

Su komutu yazin ve Enter'a basin:
```cmd
pip install -r requirements.txt
```

**Gorecekleriniz:**
Ekranda bircok satir hizla akacak. Bu tamamen normal. Ornek:
```
Collecting streamlit==1.45.1
  Downloading streamlit-1.45.1-py2.py3-none-any.whl (9.9 MB)
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 9.9/9.9 MB 12.5 MB/s eta 0:00:00
Collecting anthropic>=0.40.0
...
Successfully installed anthropic-0.52.0 streamlit-1.45.1 PyMuPDF-1.25.5 ...
```

> Yukleme **1-3 dakika** surebilir. Sabirin.
> En sonda **"Successfully installed ..."** yazisini gordugunuzde tamamdir.
> "ERROR" yazisi gorurseniz Zeynep'e haber verin.

---

### Adim 7: API Key Ayarla

PresalesAgent, Claude AI kullanir. Bunun icin bir API anahtari gerekir.
**API anahtarinizi Zeynep'ten isteyin.** `sk-ant-...` ile baslayan uzun bir metin olacak.

**Not Defteri (Notepad) ile .env dosyasi olusturun:**

1. Windows arama cubuguna `Notepad` yazin ve acin (veya Baslat menusunden Not Defteri'ni bulun)
2. Bos sayfaya su tek satiri yazin (anahtari degistirin):
```
ANTHROPIC_API_KEY=sk-ant-BURAYA_GERCEK_ANAHTARI_YAPISTIRINIZ
```
> **ORNEK:** Zeynep size `sk-ant-api03-abc123xyz` diye bir anahtar verdiyse:
> ```
> ANTHROPIC_API_KEY=sk-ant-api03-abc123xyz
> ```

3. `Dosya` menusunden **"Farkli Kaydet..."** secin
4. Kayit yerini **Masaustu > PresalesAgent** klasoru olarak secin
5. **"Dosya turu"** kismindan **"Tum Dosyalar (*.*)"** secin (bu cok onemli!)
6. **"Dosya adi"** kismine `.env` yazin (basta nokta var, uzanti yok)
7. **Kaydet** butonuna tiklayin

> **DIKKAT:** Dosya turu "Tum Dosyalar" secilmezse Windows dosyayi `.env.txt` olarak kaydeder
> ve uygulama bulamaz. Dosya turu secimini MUTLAKA yapin.

---

### Adim 8: Uygulamayi Calistir

> Kontrol: Komut satirinda satir basinda **(.venv)** yazisi var mi?
> Yoksa once `.venv\Scripts\activate` calistirin.

Su komutu yazin ve Enter'a basin:
```cmd
streamlit run app.py
```

**Gorecekleriniz:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.5:8501
```

Tarayiciniz (Chrome, Edge vb.) otomatik olarak acilacak ve uygulama gorunecek.
Eger otomatik acilmazsa, tarayicinizi acin ve adres cubuguna `http://localhost:8501` yazin.

**Uygulamayi kapatmak icin:** Komut satiri penceresine donun ve `Ctrl + C` tuslarina basin.

---

### Adim 9: Sonraki Kullanimlarda (Bilgisayari kapatip actiginda)

Bilgisayarinizi her kapatip actiginizda, uygulamayi tekrar baslatmak icin bu **3 komutu sirayla** yazin.
Her komutu yazin, Enter'a basin, sonraki komuta gecin.

**Komut 1 — Proje klasorune git:**
```cmd
cd %USERPROFILE%\Desktop\PresalesAgent
```
> Satir sonunda `PresalesAgent>` yazisini goreceksiniz.

**Komut 2 — Sanal ortami aktif et:**
```cmd
.venv\Scripts\activate
```
> Satir basinda `(.venv)` yazisini goreceksiniz.

**Komut 3 — Uygulamayi baslat:**
```cmd
streamlit run app.py
```
> Tarayici otomatik acilacak.

**Uygulamayi kapatmak icin:** Komut satirinda `Ctrl + C` basin.

---

## Guncellemeleri Alma

Zeynep uygulamaya yeni ozellikler eklediginde, su komutlarla guncelleyebilirsiniz.
Her komutu tek tek yazin ve Enter'a basin.

### Mac:

**Komut 1 — Proje klasorune git:**
```bash
cd ~/Desktop/PresalesAgent
```

**Komut 2 — Sanal ortami aktif et:**
```bash
source .venv/bin/activate
```
> Satir basinda `(.venv)` yazisini gormeniz gerekiyor.

**Komut 3 — Son kodu cek:**
```bash
git pull
```
> Ekranda degisen dosyalar listelenecek. "Already up to date." yazarsa zaten guncelsiniz.

**Komut 4 — Yeni kutuphaneleri yukle:**
```bash
pip install -r requirements.txt
```
> Bu komut her seferinde calistirilmali. Yeni kutuphane yoksa birsey olmaz, varsa otomatik yuklenir.

**Komut 5 — Uygulamayi baslat:**
```bash
streamlit run app.py
```

### Windows:

**Komut 1 — Proje klasorune git:**
```cmd
cd %USERPROFILE%\Desktop\PresalesAgent
```

**Komut 2 — Sanal ortami aktif et:**
```cmd
.venv\Scripts\activate
```
> Satir basinda `(.venv)` yazisini gormeniz gerekiyor.

**Komut 3 — Son kodu cek:**
```cmd
git pull
```
> Ekranda degisen dosyalar listelenecek. "Already up to date." yazarsa zaten guncelsiniz.

**Komut 4 — Yeni kutuphaneleri yukle:**
```cmd
pip install -r requirements.txt
```
> Bu komut her seferinde calistirilmali. Yeni kutuphane yoksa birsey olmaz, varsa otomatik yuklenir.

**Komut 5 — Uygulamayi baslat:**
```cmd
streamlit run app.py
```

---

## SSS (Sik Sorulan Sorular)

**S: "pip: command not found" hatasi aliyorum**
C: Python kurulumunda "Add to PATH" secenegini isaretlemediniz.
Python'u kaldirip tekrar kurun, bu sefer kutucugu isaretleyin.

**S: "streamlit: command not found" hatasi aliyorum**
C: Sanal ortami aktif etmediniz.
Mac: `source .venv/bin/activate` calistirin.
Windows: `.venv\Scripts\activate` calistirin.
Satir basinda `(.venv)` yazisi gorunmeli.

**S: "ANTHROPIC_API_KEY not set" hatasi aliyorum**
C: `.env` dosyasi olusturulmus mu kontrol edin.
Bu dosya `PresalesAgent` klasorunun icinde olmali.
Mac'te `cat .env` komutuyla icini gorebilirsiniz.
Windows'ta `type .env` komutuyla icini gorebilirsiniz.
Icinde `ANTHROPIC_API_KEY=sk-ant-...` yazisi olmali.

**S: Uygulama acildi ama hicbir proje yok**
C: Normal. Yeni proje olusturmak icin "Yeni Proje" butonuna tiklayin ve bir PDF yukleyin.

**S: Tarayici otomatik acilmadi**
C: Tarayicinizi acin ve adres cubuguna `http://localhost:8501` yazin.

**S: "git: command not found" veya "git is not recognized" hatasi**
C: Git yuklenmemis. Mac'te `xcode-select --install` calistirin.
Windows'ta Adim 2'yi tekrarlayin, sonra komut satirini kapatip tekrar acin.

**S: Komut satirinda `PresalesAgent` yazisini goremiyorum**
C: Yanlis klasordesiniz. Su komutu yazin:
Mac: `cd ~/Desktop/PresalesAgent`
Windows: `cd %USERPROFILE%\Desktop\PresalesAgent`

**S: "python3: command not found" hatasi (Mac)**
C: Python yuklenmemis. Adim 2'deki Homebrew + Python yukleme komutlarini calistirin.

**S: "python is not recognized" hatasi (Windows)**
C: Python kurulumunda "Add python.exe to PATH" isaretlenmemis.
Python'u Windows ayarlarindan kaldirin ve tekrar kurun, bu sefer kutucugu isaretleyin.

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
