import fitz


def read_pdf(filepath: str) -> tuple[str, int, int]:
    """PDF dosyasini okur ve metin cikarir.

    Returns:
        (metin, sayfa_sayisi, kelime_sayisi)
    """
    try:
        doc = fitz.open(filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"Dosya bulunamadi: {filepath}")
    except Exception as e:
        raise ValueError(f"PDF acilamadi: {e}")

    pages = []
    for i, page in enumerate(doc, 1):
        text = page.get_text()
        pages.append(f"--- Sayfa {i} ---\n{text}")

    full_text = "\n".join(pages)
    page_count = doc.page_count
    word_count = len(full_text.split())
    doc.close()

    if word_count < 50:
        print("  Uyari: PDF'den cok az metin cikartildi. Taranmis/gorsel PDF olabilir.")

    return full_text, page_count, word_count
