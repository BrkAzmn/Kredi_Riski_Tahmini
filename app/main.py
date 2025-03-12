import streamlit as st
import pandas as pd
import joblib
import numpy as np

# 📌 Eğitilmiş modeli ve ölçekleyiciyi yükleme
try:
    model = joblib.load("models/turkiye_kredi_riski_model.pkl")
    scaler = joblib.load("models/turkiye_scaler.pkl")
except:
    st.error("❌ Model dosyaları yüklenemedi. Lütfen modeli tekrar eğitip kaydedin.")

# 📌 Uygulama başlığı ve açıklama
st.title("🏦 Kredi Riski Tahmin Uygulaması")
st.markdown("""
📢 **Bu uygulama, kredi başvurunuzun banka tarafından onaylanma ihtimalini hesaplamaya yardımcı olur.**  
✅ **Türkiye’deki bankaların kullandığı kriterler dikkate alınarak geliştirilmiştir.**  
💡 **Tahmin edilen sonuçlar sadece bilgi amaçlıdır. Bankaların kredi onay politikaları değişebilir.**  
---
""")

# 📌 Kullanıcıdan giriş al
yas = st.number_input("📌 Yaş", min_value=18, max_value=75, value=30)
gelir = st.number_input("📌 Aylık Gelir (₺)", min_value=10000, max_value=1000000, value=50000, step=5000)
findeks_skoru = st.slider("📌 Findeks Kredi Skoru (0 - 1900)", 0, 1900, 1000)
kredi_miktari = st.number_input("📌 Talep Edilen Kredi Miktarı (₺)", min_value=5000, max_value=2000000, value=100000, step=10000)
borc_gelir_orani = st.slider("📌 Borç/Gelir Oranı (0.1 - 1.5)", 0.1, 1.5, 0.5)
gecikmeler = st.slider("📌 Son 1 Yıldaki Gecikmeli Ödeme Sayısı", 0, 10, 2)

# 📌 Çalışma süresini yaşa göre sınırla
max_calisma_suresi = max(1, yas - 18)

# Eğer max_calisma_suresi = 1 ise slider yerine doğrudan 1 ata
if max_calisma_suresi == 1:
    calisma_suresi = 1
    st.write(f"📌 Çalışma Süresi: **{calisma_suresi} yıl**")
else:
    calisma_suresi = st.slider(f"📌 Çalışma Süresi (Yıl) (Maks: {max_calisma_suresi})", 1, max_calisma_suresi, min(5, max_calisma_suresi))

ev_sahibi = st.radio("📌 Ev Sahibi misiniz?", ["Evet", "Hayır"])
sgk_durumu = st.radio("📌 SGK'lı mısınız?", ["Evet", "Hayır"])

# 📌 Kullanıcıdan gelen yanıtları modele uygun hale getirme
ev_sahibi = 1 if ev_sahibi == "Evet" else 0
sgk_durumu = 1 if sgk_durumu == "Evet" else 0

# 📌 Feature isimleri ekleyelim
feature_names = [
    "Yaş", "Gelir (₺)", "Findeks Skoru", "Kredi Miktarı (₺)",
    "Borç/Gelir Oranı", "Geçmiş Gecikmeli Ödemeler", 
    "Çalışma Süresi (Yıl)", "Ev Sahibi mi?", "SGK'lı mı?"
]

# 📌 Banka Kurallarını Uygulayalım
hata_mesajlari = []

if yas < 25 and kredi_miktari > (gelir * 5 * 12):
    hata_mesajlari.append("⚠️ 25 yaş altındaki kişilere yıllık gelirinin **en fazla 5 katı** kadar kredi verilebilir.")

if sgk_durumu == 0 and kredi_miktari > 250000:
    hata_mesajlari.append("⚠️ SGK kaydınız yoksa **250.000 TL'den fazla kredi alamazsınız.**")

if findeks_skoru < 900 and kredi_miktari > 500000:
    hata_mesajlari.append("⚠️ Findeks skoru 900'ün altındaysa **500.000 TL'den fazla kredi almak zor olabilir.**")

if borc_gelir_orani > 1.2:
    hata_mesajlari.append("⚠️ Borç/Gelir oranınız çok yüksek! Bankalar genellikle borcunuzun gelirinizin en fazla %60-70’i olmasını ister.")

# 📌 Tahmin butonu
if st.button("📌 Kredi Riskini Tahmin Et"):
    try:
        if hata_mesajlari:
            for mesaj in hata_mesajlari:
                st.warning(mesaj)
        else:
            # Kullanıcıdan alınan veriyi modele uygun hale getirme
            yeni_veri = np.array([[yas, gelir, findeks_skoru, kredi_miktari, borc_gelir_orani, gecikmeler, calisma_suresi, ev_sahibi, sgk_durumu]])

            # 📌 StandardScaler için feature isimleri eklendi
            yeni_veri_df = pd.DataFrame(yeni_veri, columns=feature_names)
            yeni_veri_scaled = scaler.transform(yeni_veri_df)

            tahmin = model.predict_proba(yeni_veri_scaled)

            # Kredi riski yüzdeleri
            risk_orani = tahmin[0][1] * 100  # Yüksek risk oranı (% olarak)
            onay_orani = 100 - risk_orani  # Kredi onaylanma oranı

            # 📌 Kullanıcıya uygun bilgilendirme
            if risk_orani > 50:
                st.error(f"⚠️ **Yüksek Kredi Riski!** 🔴\n📉 Tahmini kredi reddedilme oranı: **%{round(risk_orani, 2)}**")
                st.markdown("💡 **Öneriler:**")
                st.markdown("- 📌 **Findeks Kredi Skoru**'nuzu artırmak için düzenli ödeme yapın. 📈")
                st.markdown("- 📌 **Borç/Gelir oranınızı düşürerek riskinizi azaltın.** 🏦")
                st.markdown("- 📌 **Daha uzun çalışma süresi** ve **SGK kaydı** bankalar için olumlu bir etkendir. 🏆")
                st.markdown("- 📌 Kredi kartı ve fatura ödemelerinizi **geciktirmeden yapmaya özen gösterin.**")

            else:
                st.success(f"✅ **Düşük Kredi Riski!** 🟢\n📈 Tahmini kredi onaylanma oranı: **%{round(onay_orani, 2)}**")

    except Exception as e:
        st.error(f"❌ Tahmin yapılırken hata oluştu: {e}")
