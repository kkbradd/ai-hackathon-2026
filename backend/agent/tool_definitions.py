TOOL_DEFINITIONS = [
    {
        "name": "get_order_status",
        "description": "Belirli bir sipariş ID'sine göre siparişin tam detaylarını getirir: müşteri adı, durum, ürünler, toplam tutar ve kargo bilgisi.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "Sorgulanacak siparişin ID numarası.",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_pending_orders",
        "description": "Bekleyen ve işlemdeki siparişleri listeler. Hangi siparişlerin henüz karşılanmadığını görmek için kullanılır.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Kaç sipariş listeleneceği. Varsayılan 10.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_order_history",
        "description": "Bir müşterinin e-posta adresine göre geçmiş siparişlerini listeler.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_email": {
                    "type": "string",
                    "description": "Sorgulanacak müşterinin e-posta adresi.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Kaç sipariş gösterileceği. Varsayılan 5.",
                },
            },
            "required": ["customer_email"],
        },
    },
    {
        "name": "get_shipment_status",
        "description": "Belirli bir sipariş için kargo durumunu getirir: taşıyıcı, takip numarası, mevcut durum, tahmini teslimat ve gecikme bilgisi.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "Kargo durumu sorgulanacak siparişin ID'si.",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_shipment_timeline",
        "description": "Belirli bir sipariş için kargonun tüm hareket geçmişini (zaman çizelgesini) getirir. Her adımda konum, durum ve zaman bilgisi içerir.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "Kargo zaman çizelgesi sorgulanacak siparişin ID'si.",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_delayed_shipments",
        "description": "Tahmini teslimat tarihi geçmiş ancak henüz teslim edilmemiş (gecikmiş) tüm kargoları listeler.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_recent_messages",
        "description": "Son müşteri mesajlarını listeler. Okunmamış mesaj sayısını ve mesaj içeriklerini gösterir.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Kaç mesaj gösterileceği. Varsayılan 5.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "summarize_daily_operations",
        "description": "Günlük operasyon özetini getirir: bekleyen sipariş sayısı, aktif kargolar, gecikmiş teslimatlar, okunmamış mesajlar ve bugün teslim edilenler.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_inventory_status",
        "description": "Kooperatifin tüm ürünlerinin stok durumunu getirir. Hangi ürünlerin minimum eşiğin altına düştüğünü, kritik stok seviyelerini ve yenileme noktalarını gösterir. filter='low_stock' ile sadece uyarı seviyesindeki ürünleri listeler.",
        "parameters": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "enum": ["all", "low_stock"],
                    "description": "'low_stock' ise sadece stok eşiğinin altındaki ürünleri getirir. Varsayılan 'all'.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_operational_alerts",
        "description": "Operasyonel uyarıları listeler: gecikmiş kargolar, düşük stok, taşıyıcı sorunları, müşteri şikayetleri ve anomaliler. Önem derecesine ve çözüm durumuna göre filtre uygulanabilir.",
        "parameters": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "description": "Filtrelenecek önem derecesi: 'critical', 'warning' veya 'info'.",
                },
                "resolved": {
                    "type": "string",
                    "enum": ["false", "true"],
                    "description": "'true' ise çözülmüş uyarıları getirir. Varsayılan 'false' (aktif uyarılar).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_demand_trends",
        "description": "Son N günde kooperatif ürünlerinin talep trendlerini analiz eder. Hangi ürünlerin çok sipariş edildiğini, günlük ortalama talep miktarlarını gösterir.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Kaç günlük sipariş verisi analiz edilsin. Varsayılan 7.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_daily_summary_rich",
        "description": "Kapsamlı günlük operasyon raporu: bekleyen siparişler, gecikmiş kargolar, kritik stok uyarıları, en çok talep gören ürünler ve tüm operasyonel uyarılar tek bir yanıtta birleştirilir. Günlük brifing için idealdir.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "resolve_operational_alert",
        "description": "Belirtilen operasyonel uyarıyı (alert) çözüldü (resolved) olarak işaretler.",
        "parameters": {
            "type": "object",
            "properties": {
                "alert_id": {
                    "type": "integer",
                    "description": "Çözüldü olarak işaretlenecek uyarının ID'si."
                }
            },
            "required": ["alert_id"]
        }
    },
    {
        "name": "update_shipment_status",
        "description": "Belirtilen kargonun durumunu günceller ve yeni bir hareket kaydı ekler.",
        "parameters": {
            "type": "object",
            "properties": {
                "shipment_id": {
                    "type": "integer",
                    "description": "Durumu güncellenecek kargonun ID'si."
                },
                "new_status": {
                    "type": "string",
                    "description": "Yeni kargo durumu ('preparing', 'in_transit', 'at_facility', 'out_for_delivery', 'delivered', 'failed', 'returned')."
                },
                "location": {
                    "type": "string",
                    "description": "Kargonun şu anki konumu."
                },
                "description": {
                    "type": "string",
                    "description": "Hareketle ilgili ek açıklama."
                }
            },
            "required": ["shipment_id", "new_status", "location"]
        }
    },
    {
        "name": "draft_supplier_order",
        "description": "Stok seviyesi düşen bir ürün için tedarikçiye verilmek üzere bir sipariş taslağı uyarısı oluşturur.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "Sipariş taslağı oluşturulacak ürünün ID'si."
                },
                "quantity": {
                    "type": "number",
                    "description": "Tedarikçiden sipariş edilecek miktar."
                }
            },
            "required": ["product_id", "quantity"]
        }
    },
    {
        "name": "update_order_status",
        "description": "Belirtilen siparişin durumunu günceller.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "Durumu güncellenecek siparişin ID'si."
                },
                "new_status": {
                    "type": "string",
                    "description": "Yeni sipariş durumu ('pending', 'processing', 'shipped', 'delivered', 'cancelled')."
                }
            },
            "required": ["order_id", "new_status"]
        }
    },
    {
        "name": "execute_sql",
        "description": (
            "Veritabanına doğrudan bir SELECT sorgusu çalıştırır ve sonuçları döndürür. "
            "Mevcut araçların karşılamadığı özel veya karmaşık analizler için kullan. "
            "Yalnızca SELECT ifadelerine izin verilir; veri değiştiren sorgular reddedilir. "
            "Tablolar: orders, order_items, products, customers, shipments, shipment_updates, "
            "customer_messages, inventory, inventory_movements, operational_alerts, users."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Çalıştırılacak SQL SELECT sorgusu. Parametre bağlama kullanma; değerleri doğrudan yaz."
                },
                "limit": {
                    "type": "integer",
                    "description": "Maksimum döndürülecek satır sayısı. Varsayılan 20, en fazla 100."
                }
            },
            "required": ["query"]
        }
    }
]
