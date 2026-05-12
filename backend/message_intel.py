"""Rule-based classification for customer messages — no LLM."""

from typing import Optional, Tuple

SUBJECT_HINTS = (
    # Teslimat
    ("teslimat gecikmesi", "teslimat_gecikmesi", "yüksek"),
    ("teslimat gecik",     "teslimat_gecikmesi", "yüksek"),
    # Ürün/hasar
    ("ürün kalitesi",      "urun_hasari",        "yüksek"),
    ("ürün kalitesi sorunu","urun_hasari",        "yüksek"),
    ("yanlış ürün",        "yanlis_urun",        "orta"),
    ("yanlış ürün teslimatı","yanlis_urun",       "orta"),
    # Paket hasarı
    ("hasar görmüş paket", "paket_hasari",       "orta"),
    ("hasar görmüş",       "paket_hasari",       "orta"),
    ("paket hasarı",       "paket_hasari",       "orta"),
    # Sipariş
    ("acil stok talebi",   "siparis_talebi",     "yüksek"),
    ("acil sipariş bildirimi","siparis_talebi",   "yüksek"),
    ("acil sipariş",       "siparis_talebi",     "yüksek"),
    ("acil stok",          "siparis_talebi",     "yüksek"),
    ("toplu sipariş",      "siparis_talebi",     "orta"),
    # Fatura
    ("fatura düzeltme",    "fatura_duzeltme",    "düşük"),
    ("fatura düzeltme talebi","fatura_duzeltme", "düşük"),
    ("fatura sorunu",      "fatura_duzeltme",    "düşük"),
    # Stok
    ("stok bilgisi",       "stok_bilgisi",       "düşük"),
    ("stok bilgisi talebi","stok_bilgisi",       "düşük"),
)


def classify_customer_message(subject: Optional[str]) -> Tuple[str, str]:
    """Return (category, urgency) from subject keywords."""
    s = (subject or "").strip().lower()
    for key, cat, urg in SUBJECT_HINTS:
        if key.lower() in s or s == key.lower():
            return cat, urg
    if "gecik" in s or "gelmedi" in s:
        return "teslimat_gecikmesi", "yüksek"
    if "iade" in s or "bozuk" in s:
        return "urun_hasari", "yüksek"
    return "genel_destek", "orta"


def brief_summary(customer_name: str, category: str, subject: Optional[str]) -> str:
    sub = subject or "Konu bildirildi"
    cat_label = {
        "teslimat_gecikmesi": "Teslimat gecikmesi",
        "urun_hasari": "Ürün / paket sorunu",
        "yanlis_urun": "Yanlış ürün",
        "paket_hasari": "Paket hasarı",
        "siparis_talebi": "Sipariş veya kapasite talebi",
        "fatura_duzeltme": "Operasyon/finans bildirimi",
        "stok_bilgisi": "Envanter sorusu",
        "genel_destek": "Genel bildirim",
    }.get(category, "İletişim")
    return f"{customer_name} · {cat_label}: {sub[:80]}{'…' if sub and len(sub) > 80 else ''}"
