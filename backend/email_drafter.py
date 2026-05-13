"""Gemini ile tedarikçi/müşteri e-posta taslakları üretir.

Hiçbir gerçek SMTP/WhatsApp bağlantısı yok; yalnızca metin üretiyor.
Demo için: ajanlar/araçlar bunu çağırıp DB'ye taslak yazıyor, UI 'Gönder'
butonuyla taslağı 'gönderildi' olarak işaretliyor.
"""
import os
import re

import google.generativeai as genai

GEMINI_MODEL = "gemini-2.5-flash"


def _slug_email(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "", name.lower())[:18] or "tedarikci"
    return f"{base}@tedarikci.example.com"


def _supplier_for_category(category: str) -> tuple[str, str]:
    """Ürün kategorisine göre sahte ama gerçekçi tedarikçi adı + e-postası üret."""
    mapping = {
        "Bakliyat": ("Anadolu Bakliyat A.Ş.", "satis@anadolubakliyat.example.com"),
        "Baharat":  ("Egem Baharat Ltd.",     "siparis@egembaharat.example.com"),
        "Yağ":      ("Marmara Zeytin Koop.",  "tedarik@marmarazeytin.example.com"),
        "Tatlı":    ("Karadeniz Pekmez San.", "siparis@karadenizpekmez.example.com"),
        "Sebze":    ("Çukurova Tarım Koop.",  "satis@cukurovatarim.example.com"),
        "Meyve":    ("Akdeniz Meyve Birliği",  "tedarik@akdenizmeyve.example.com"),
    }
    for k, v in mapping.items():
        if k.lower() in (category or "").lower():
            return v
    return ("Anadolu Tedarik Ltd.", _slug_email(category or "tedarikci"))


def _gemini_text(prompt: str, max_tokens: int = 400) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("your_"):
        return ""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=max_tokens,
            ),
        )
        resp = model.generate_content(prompt)
        return (resp.text or "").strip()
    except Exception as e:
        print(f"[email_drafter] Gemini hatası: {e}")
        return ""


def draft_supplier_email(product_name: str, category: str, quantity: float, unit: str,
                          current_stock: float, reorder_point: float) -> dict:
    """Tedarikçiye gönderilecek sipariş taslağı üretir."""
    supplier_name, supplier_email = _supplier_for_category(category)
    subject = f"Acil Tedarik Talebi — {product_name} ({quantity:.0f} {unit})"

    fallback_body = (
        f"Sayın {supplier_name} yetkilisi,\n\n"
        f"Anadolu Tarım ve Gıda Kooperatifi olarak {product_name} ürününde stok "
        f"seviyemiz {current_stock:.0f} {unit}'a düştü ve yeniden sipariş noktamız "
        f"olan {reorder_point:.0f} {unit}'ın altına indi.\n\n"
        f"Operasyonlarımızın aksamaması için aşağıdaki tedariki en kısa sürede "
        f"gerçekleştirmenizi rica ederiz:\n\n"
        f"  • Ürün: {product_name}\n"
        f"  • Miktar: {quantity:.0f} {unit}\n"
        f"  • Talep edilen teslim süresi: 7 iş günü\n\n"
        f"Fiyat teklifi ve teslim tarihi konusunda bugün geri dönüş yapabilirseniz "
        f"memnun oluruz.\n\n"
        f"Saygılarımızla,\n"
        f"Anadolu Tarım ve Gıda Kooperatifi\n"
        f"Operasyon Birimi"
    )

    prompt = (
        f"Tedarikçiye gönderilecek profesyonel bir Türkçe sipariş e-postası yaz. "
        f"Sadece e-posta gövdesini döndür — konu, başlık, açıklama yazma.\n\n"
        f"Bilgiler:\n"
        f"- Tedarikçi: {supplier_name}\n"
        f"- Ürün: {product_name} ({category})\n"
        f"- Mevcut stok: {current_stock:.0f} {unit} (yeniden sipariş noktası: {reorder_point:.0f} {unit})\n"
        f"- Talep edilen miktar: {quantity:.0f} {unit}\n"
        f"- Gönderen: Anadolu Tarım ve Gıda Kooperatifi, Operasyon Birimi\n\n"
        f"E-posta kibar, kısa (200 kelime altı), aciliyet vurgusu olan ama profesyonel tonda olsun. "
        f"'Sayın ... yetkilisi,' ile başla, 'Saygılarımızla,' ile bitir."
    )
    body = _gemini_text(prompt, max_tokens=500) or fallback_body

    return {
        "supplier_name": supplier_name,
        "supplier_email": supplier_email,
        "subject": subject,
        "body": body,
    }


def draft_delay_notification(customer_name: str, tracking_number: str, carrier: str,
                              days_overdue: int, order_id: int) -> dict:
    """Kargo gecikmesinde müşteriye gönderilecek bildirim taslağı."""
    subject = f"Kargonuz hakkında bilgilendirme — Sipariş #{order_id}"

    fallback_body = (
        f"Sayın {customer_name},\n\n"
        f"Anadolu Tarım ve Gıda Kooperatifi olarak {order_id} numaralı siparişinizin "
        f"kargosunda ({carrier}, takip no: {tracking_number}) yaşanan {days_overdue} "
        f"günlük gecikme nedeniyle sizi bilgilendirmek isteriz.\n\n"
        f"Kargo firmasıyla irtibata geçtik ve siparişinizin en kısa sürede teslim "
        f"edilmesi için süreci yakından takip ediyoruz. Yaşanan gecikme için "
        f"özür dileriz.\n\n"
        f"Sorularınız için info@anadolutarim.example.com adresinden bize "
        f"ulaşabilirsiniz.\n\n"
        f"Anlayışınız için teşekkür ederiz.\n\n"
        f"Saygılarımızla,\n"
        f"Anadolu Tarım ve Gıda Kooperatifi\n"
        f"Müşteri Hizmetleri"
    )

    prompt = (
        f"Müşteriye kargo gecikmesi konusunda gönderilecek samimi ve özürlü bir Türkçe "
        f"e-posta yaz. Sadece gövdesini döndür.\n\n"
        f"Bilgiler:\n"
        f"- Müşteri: {customer_name}\n"
        f"- Sipariş no: #{order_id}\n"
        f"- Kargo firması: {carrier}, takip no: {tracking_number}\n"
        f"- Gecikme: {days_overdue} gün\n"
        f"- Gönderen: Anadolu Tarım ve Gıda Kooperatifi, Müşteri Hizmetleri\n\n"
        f"E-posta kısa (150 kelime altı), samimi ama profesyonel olsun, gecikme için "
        f"net özür içersin, takip sürecinin devam ettiğini belirtsin. "
        f"'Sayın {customer_name},' ile başla, 'Saygılarımızla,' ile bitir."
    )
    body = _gemini_text(prompt, max_tokens=400) or fallback_body

    return {"subject": subject, "body": body}
