import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendis AI - Pro", page_icon="⚙️", layout="wide")

col1, col2 = st.columns([1, 5])
with col1:
    st.write("🤖")
with col2:
    st.title("Mühendislik Tasarım Asistanı V3.3")
    st.write("Teknik resim (PDF/JPG/PNG/WebP) analizi, malzeme seçimi ve maliyet tahmini.")

st.divider()

# --- API ANAHTARI YÖNETİMİ ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API Anahtarı Tanımlı")
else:
    with st.sidebar:
        st.warning("⚠️ Otomatik giriş yapılamadı.")
        api_key = st.text_input("Gemini API Anahtarı", type="password")

# --- YAN MENÜ ---
with st.sidebar:
    st.header("🎛️ Kontrol Paneli")
    st.divider()
    
    mod = st.selectbox(
        "Analiz Modu:",
        [
            "Genel Kontrol", 
            "İmalatçı (CNC/Torna)", 
            "Kalite Kontrol (GD&T)", 
            "🧪 Malzeme Danışmanı",
            "💰 Maliyet Tahmini"
        ]
    )
    st.info(f"Mod: **{mod}**")

# --- ANA EKRAN ---
col_resim, col_analiz = st.columns([1, 1])

with col_resim:
    st.subheader("📂 Dosya Yükleme")
    
    # GÜNCELLEME 1: Listeye "webp" ekledik
    uploaded_file = st.file_uploader(
        "Dosya Yükle", 
        type=["jpg", "jpeg", "png", "pdf", "webp"]
    )
    
    if uploaded_file:
        # GÜNCELLEME 2: WebP dosya türünü (MIME type) tanıttık
        if uploaded_file.type in ["image/jpeg", "image/png", "image/webp"]:
            image = Image.open(uploaded_file)
            st.image(image, caption='Yüklenen Tasarım', use_column_width=True)
            
        elif uploaded_file.type == "application/pdf":
            st.warning("📄 PDF Dosyası Yüklendi.")

with col_analiz:
    st.subheader("📝 Yapay Zeka Raporu")
    
    if uploaded_file and api_key:
        if st.button("Analizi Başlat 🚀", type="primary"):
            genai.configure(api_key=api_key)
            # Senin güçlü modelin
            model = genai.GenerativeModel('gemini-2.0-flash') 
            
            base_prompt = "Sen uzman bir Makine Mühendisisin. Bu dosyayı incele. "
            
            if mod == "Genel Kontrol":
                ozel_istek = "Eksik ölçüleri, antet bilgilerini ve genel görünüş hatalarını listele."
            elif mod == "İmalatçı (CNC/Torna)":
                ozel_istek = "Bir CNC operatörü gibi düşün. Hangi tezgah gerekir? İşlenmesi zor detaylar neler?"
            elif mod == "Kalite Kontrol (GD&T)":
                ozel_istek = "Sadece toleranslara odaklan. H7/g6 gibi geçme toleransları var mı?"
            elif mod == "🧪 Malzeme Danışmanı":
                ozel_istek = "Bu parça ne kadar yük taşır? Hangi malzeme uygundur ve neden?"
            elif mod == "💰 Maliyet Tahmini":
                ozel_istek = "Maliyet analizi yap. Tasarımı ucuzlatmak için ne değişmeli?"

            full_prompt = base_prompt + ozel_istek + " Cevabı Türkçe ve maddeler halinde ver."

            with st.spinner('Analiz yapılıyor...'):
                try:
                    input_data = None
                    
                    # PDF İşlemi
                    if uploaded_file.type == "application/pdf":
                        input_data = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                    
                    # Resim İşlemi (WebP dahil hepsi buraya girer)
                    else:
                        input_data = Image.open(uploaded_file)

                    response = model.generate_content([full_prompt, input_data])
                    st.success("Analiz Tamamlandı!")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Hata: {e}")

    elif not api_key:
        st.error("Lütfen API anahtarını girin.")
    elif not uploaded_file:
        st.info("Dosya bekleniyor...")