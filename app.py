import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis AI - Süper App", page_icon="🛠️", layout="wide")

# --- API ANAHTARI YÖNETİMİ (GLOBAL) ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # Eğer otomatik giriş yoksa sidebar'da sor
    with st.sidebar:
        st.warning("⚠️ API Anahtarı Bulunamadı")
        api_key = st.text_input("Gemini API Anahtarı", type="password")

# --- MODEL FONKSİYONU (GEMINI 2.0 FLASH) ---
def get_gemini_response(prompt, image=None):
    if not api_key:
        return "Lütfen önce API anahtarını girin."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash') # GÜÇLÜ MODEL
    
    try:
        if image:
            response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Hata oluştu: {e}"

# ==========================================
# 1. SAYFA: TEKNİK RESİM ANALİZİ (ESKİ SİSTEM)
# ==========================================
def sayfa_teknik_resim():
    st.title("📐 Teknik Resim Analiz Asistanı")
    st.markdown("Teknik resimlerinizi yükleyin, hataları bulun ve raporlayın.")
    
    # Hafıza
    if "analiz_msgs" not in st.session_state: st.session_state.analiz_msgs = []
    
    col1, col2 = st.columns([1, 1])
    
    uploaded_file = col1.file_uploader("Teknik Resim Yükle", type=["jpg", "png", "pdf", "webp"])
    mod = col2.selectbox("Analiz Modu", ["Genel Kontrol", "İmalatçı", "Kalite Kontrol", "Malzeme", "Maliyet"])
    
    if uploaded_file:
        with col1.expander("Dosyayı Görüntüle", expanded=False):
            if uploaded_file.type != "application/pdf":
                image = Image.open(uploaded_file)
                st.image(image, use_column_width=True)
        
        if col2.button("Analizi Başlat 🚀", type="primary", use_container_width=True):
            if api_key:
                prompt = f"Sen uzman bir mühendissin. Bu resmi '{mod}' modunda analiz et. Detaylı Türkçe rapor yaz."
                
                # Veri hazırlığı
                img_data = Image.open(uploaded_file) if uploaded_file.type != "application/pdf" else {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                
                with st.spinner("Gemini 2.0 inceliyor..."):
                    cevap = get_gemini_response(prompt, img_data)
                    st.session_state.analiz_msgs = [{"role": "assistant", "content": cevap}]
                    st.rerun()

    # Sonuç Ekranı
    if st.session_state.analiz_msgs:
        st.divider()
        for msg in st.session_state.analiz_msgs:
            st.markdown(msg["content"])
            st.download_button("📥 Raporu İndir", msg["content"], "Analiz.txt")

# ==========================================
# 2. SAYFA: FORMÜL & ÖDEV FOTOĞRAFÇISI
# ==========================================
def sayfa_odev_cozucu():
    st.title("📸 Formül ve Problem Çözücü")
    st.info("Defterindeki karmaşık sorunun fotoğrafını çek yükle, Gemini adım adım çözsün.")
    
    uploaded_file = st.file_uploader("Sorunun Fotoğrafını Yükle", type=["jpg", "png", "webp"])
    
    if uploaded_file and api_key:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Soru", width=400)
        
        if st.button("Soruyu Çöz 🧠", type="primary"):
            prompt = """
            Sen uzman bir profesörsün. Bu görseldeki matematik/fizik/mühendislik problemini çöz.
            1. Önce soruyu anladığını belirt.
            2. Hangi formülleri kullanacağını yaz.
            3. Adım adım işlemi yap.
            4. Sonucu net bir şekilde belirt.
            """
            with st.spinner("Profesör düşünüyor..."):
                cevap = get_gemini_response(prompt, image)
                st.success("Çözüm:")
                st.markdown(cevap)

# ==========================================
# 3. SAYFA: MALZEME KIYASLAMA MOTORU
# ==========================================
def sayfa_malzeme_kiyasla():
    st.title("⚖️ Malzeme Kıyaslama Motoru")
    st.markdown("İki farklı malzemeyi teknik özellikleri ve kullanım alanlarına göre kıyaslayın.")
    
    col1, col2 = st.columns(2)
    m1 = col1.text_input("1. Malzeme (Örn: Alüminyum 6061)")
    m2 = col2.text_input("2. Malzeme (Örn: Çelik 1040)")
    
    if m1 and m2 and st.button("Kıyasla ⚔️", type="primary"):
        prompt = f"""
        '{m1}' ile '{m2}' malzemelerini bir makine mühendisi için kıyasla.
        Aşağıdaki başlıkları içeren bir MARKDOWN TABLOSU oluştur:
        - Yoğunluk
        - Akma Mukavemeti (Yield Strength)
        - Korozyon Direnci
        - Tahmini Maliyet
        - Yaygın Kullanım Alanları
        
        Tablonun altına hangisinin hangi durumda seçilmesi gerektiğini yorumla.
        """
        with st.spinner("Veritabanı taranıyor..."):
            cevap = get_gemini_response(prompt)
            st.markdown(cevap)

# ==========================================
# 4. SAYFA: KOD ÇEVİRİCİ (MATLAB <-> PYTHON)
# ==========================================
def sayfa_kod_cevirici():
    st.title("💻 Kod Çevirici & Açıklayıcı")
    st.markdown("MATLAB kodlarını Python'a çevirin veya kodunuzdaki hatayı bulun.")
    
    kod = st.text_area("Kodunuzu buraya yapıştırın:", height=200)
    islem = st.selectbox("Ne yapmak istersiniz?", ["MATLAB -> Python Çevir", "Python -> MATLAB Çevir", "Koddaki Hatayı Bul", "Kodu Açıkla"])
    
    if kod and st.button("Çalıştır ⚡"):
        prompt = f"Sen uzman bir yazılımcısın. Aşağıdaki kod için şu işlemi yap: {islem}.\n\nKOD:\n{kod}\n\nLütfen sadece kodu ve kısa bir açıklamayı ver."
        with st.spinner("Kodlanıyor..."):
            cevap = get_gemini_response(prompt)
            st.code(cevap)

# ==========================================
# 5. SAYFA: MÜLAKAT SİMÜLASYONU
# ==========================================
def sayfa_mulakat_kocu():
    st.title("👔 Mülakat Simülasyonu")
    st.markdown("Yapay zeka İK veya Teknik Müdür olsun, seni mülakata alsın.")
    
    # Mülakat hafızası
    if "mulakat_msgs" not in st.session_state: 
        st.session_state.mulakat_msgs = [{"role": "assistant", "content": "Merhaba! Hangi pozisyon için mülakat yapmak istiyorsun? (Örn: Tasarım Mühendisi, Ar-Ge, Üretim Stajyeri)"}]

    # Mesajları göster
    for msg in st.session_state.mulakat_msgs:
        st.chat_message(msg["role"]).markdown(msg["content"])
    
    # Kullanıcı girişi
    if prompt := st.chat_input("Cevabını yaz..."):
        st.session_state.mulakat_msgs.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        
        # Gemini Cevabı (Bağlamlı)
        gecmis = [m["content"] for m in st.session_state.mulakat_msgs]
        full_prompt = f"""
        Sen sert ama adil bir Mühendislik Müdürüsün. Şu an bir mülakattayız.
        Kullanıcının cevabına göre ona teknik bir soru sor veya cevabını puanla.
        Konuşma Geçmişi: {gecmis}
        """
        
        with st.spinner("Mülakatçı düşünüyor..."):
            cevap = get_gemini_response(full_prompt)
            st.session_state.mulakat_msgs.append({"role": "assistant", "content": cevap})
            st.chat_message("assistant").markdown(cevap)
            st.rerun()

# ==========================================
# ANA MENÜ YÖNETİMİ (SOL TARAF)
# ==========================================
with st.sidebar:
    st.title("Mühendis AI")
    st.write("V5.0 - Super App")
    st.markdown("---")
    
    secim = st.radio(
        "Araç Seçimi:",
        ["📐 Teknik Resim Analizi", "📸 Ödev Çözücü", "⚖️ Malzeme Kıyasla", "💻 Kod Çevirici", "👔 Mülakat Koçu"]
    )
    
    st.markdown("---")
    if st.button("🗑️ Tüm Geçmişi Temizle"):
        st.session_state.clear()
        st.rerun()

# Seçime göre sayfayı getir
if secim == "📐 Teknik Resim Analizi":
    sayfa_teknik_resim()
elif secim == "📸 Ödev Çözücü":
    sayfa_odev_cozucu()
elif secim == "⚖️ Malzeme Kıyasla":
    sayfa_malzeme_kiyasla()
elif secim == "💻 Kod Çevirici":
    sayfa_kod_cevirici()
elif secim == "👔 Mülakat Koçu":
    sayfa_mulakat_kocu()