import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- SAYFA AYARLARI (Geniş Düzen) ---
st.set_page_config(page_title="Analiz Asistanı", page_icon="📊", layout="wide")

# Başlık
st.title("Analiz Asistanı V4.1 (Pro Arayüz)")
st.markdown("---")

# --- API ANAHTARI ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        st.warning("⚠️ Otomatik giriş yapılamadı.")
        api_key = st.text_input("Gemini API Anahtarı", type="password")

# --- HAFIZA (SESSION STATE) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# --- YAN MENÜ (Temizleme) ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    if st.button("🗑️ Temizle ve Başa Dön", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_uploaded_file = None
        st.rerun()

# ==========================================
# 1. BÖLÜM: GİRİŞ VE AYARLAR (ÜST KISIM)
# ==========================================

# Ekranı ikiye bölüyoruz: Resim ve Ayarlar
col_resim, col_ayar = st.columns([1, 1])

uploaded_file = None
mod = "Genel Kontrol"
analiz_tetiklendi = False

with col_resim:
    st.subheader("1. Dosya Yükle")
    uploaded_file = st.file_uploader("Teknik Resim Seçin", type=["jpg", "jpeg", "png", "pdf", "webp"])
    
    if uploaded_file:
        # Dosya değişirse hafızayı temizle
        if st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.messages = []
            st.session_state.last_uploaded_file = uploaded_file.name

        # --- DEĞİŞİKLİK BURADA: expanded=False YAPTIK ---
        with st.expander("🖼️ Yüklenen Dosyayı Görüntüle (Tıkla)", expanded=False):
            if uploaded_file.type in ["image/jpeg", "image/png", "image/webp"]:
                image = Image.open(uploaded_file)
                st.image(image, use_column_width=True)
            elif uploaded_file.type == "application/pdf":
                st.success("📄 PDF dosyası hazır.")

with col_ayar:
    st.subheader("2. Analiz Ayarları")
    
    if uploaded_file:
        mod = st.selectbox(
            "Hangi gözle bakılsın?",
            [
                "Genel Kontrol", 
                "İmalatçı (CNC/Torna)", 
                "Kalite Kontrol (GD&T)", 
                "🧪 Malzeme Danışmanı", 
                "💰 Maliyet Tahmini"
            ]
        )
        
        st.info(f"Seçilen Mod: **{mod}**")
        
        # Analiz Butonu
        if len(st.session_state.messages) == 0:
            if st.button("Analizi Başlat 🚀", type="primary", use_container_width=True):
                analiz_tetiklendi = True
    else:
        st.warning("👈 Lütfen sol taraftan dosya yükleyerek başlayın.")

# ==========================================
# 2. BÖLÜM: İŞLEM VE SONUÇLAR (TAM EKRAN)
# ==========================================

if uploaded_file and api_key:
    
    # --- ANALİZ İŞLEMİ ---
    if analiz_tetiklendi:
        genai.configure(api_key=api_key)
        
        # --- MODEL: GEMINI 2.0 FLASH ---
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        base_prompt = "Sen uzman bir Makine Mühendisisin. Bu dosyayı incele. "
        ozel_istek = ""
        if mod == "Genel Kontrol": ozel_istek = "Eksik ölçüleri ve hataları listele."
        elif mod == "İmalatçı (CNC/Torna)": ozel_istek = "CNC operatörü gözüyle bak. İşleme zorlukları neler?"
        elif mod == "Kalite Kontrol (GD&T)": ozel_istek = "Toleranslara odaklan."
        elif mod == "🧪 Malzeme Danışmanı": ozel_istek = "Malzeme önerisi yap."
        elif mod == "💰 Maliyet Tahmini": ozel_istek = "Maliyet analizi yap."

        full_prompt = base_prompt + ozel_istek + " Cevabı Türkçe, detaylı ve maddeler halinde ver."

        with st.spinner('Gemini 2.0 raporu hazırlıyor...'):
            try:
                input_data = None
                if uploaded_file.type == "application/pdf":
                    input_data = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                else:
                    input_data = Image.open(uploaded_file)

                response = model.generate_content([full_prompt, input_data])
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.rerun()
                
            except Exception as e:
                st.error(f"Hata: {e}")

    # --- SONUÇ EKRANI ---
    if len(st.session_state.messages) > 0:
        st.divider()
        st.header("📝 Analiz Raporu ve Sohbet")
        
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                if i == 0:
                    st.download_button(
                        label="📥 Raporu İndir (TXT)",
                        data=message["content"],
                        file_name="Analiz_Raporu.txt",
                        mime="text/plain"
                    )

        if prompt := st.chat_input("Raporda anlamadığınız bir yer var mı? Sorun cevaplayayım..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Gemini 2.0 düşünüyor..."):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-2.0-flash')
                        
                        input_data = None
                        if uploaded_file.type == "application/pdf":
                            input_data = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                        else:
                            input_data = Image.open(uploaded_file)
                        
                        chat_history = [full_prompt, input_data]
                        for msg in st.session_state.messages:
                            chat_history.append(msg["content"])
                        chat_history.append(prompt)

                        response = model.generate_content(chat_history)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        
                    except Exception as e:
                        st.error(f"Hata: {e}")