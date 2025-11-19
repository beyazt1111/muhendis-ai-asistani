import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Analiz Asistanı", page_icon="📊", layout="wide")

col1, col2 = st.columns([1, 5])
with col1:
    st.write("🤖")
with col2:
    st.title("Analiz Asistanı V3.7 (Sohbet Modu)")
    st.write("Teknik resim analizi, raporlama ve **interaktif soru-cevap**.")

st.divider()

# --- API ANAHTARI ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    st.sidebar.success("✅ API Anahtarı Tanımlı")
else:
    with st.sidebar:
        st.warning("⚠️ Otomatik giriş yapılamadı.")
        api_key = st.text_input("Gemini API Anahtarı", type="password")

# --- HAFIZA (SESSION STATE) AYARLARI ---
# Eğer hafızada geçmiş yoksa, boş bir liste oluştur
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

# --- YAN MENÜ ---
with st.sidebar:
    st.header("🎛️ Kontrol Paneli")
    st.divider()
    mod = st.selectbox(
        "Analiz Modu:",
        ["Genel Kontrol", "İmalatçı (CNC/Torna)", "Kalite Kontrol (GD&T)", "🧪 Malzeme Danışmanı", "💰 Maliyet Tahmini"]
    )
    
    # Sohbeti Temizle Butonu
    if st.button("🗑️ Yeni Analiz / Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- ANA EKRAN ---
col_resim, col_analiz = st.columns([1, 1])

uploaded_file = None

with col_resim:
    st.subheader("📂 Dosya Yükleme")
    uploaded_file = st.file_uploader("Dosya Yükle", type=["jpg", "jpeg", "png", "pdf", "webp"])
    
    if uploaded_file:
        # Yeni dosya yüklendiyse hafızayı temizle
        if st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.messages = []
            st.session_state.last_uploaded_file = uploaded_file.name
        
        # Dosyayı göster
        if uploaded_file.type in ["image/jpeg", "image/png", "image/webp"]:
            image = Image.open(uploaded_file)
            st.image(image, caption='Yüklenen Tasarım', use_column_width=True)
        elif uploaded_file.type == "application/pdf":
            st.warning("📄 PDF Dosyası Yüklendi.")

with col_analiz:
    st.subheader("📝 Analiz ve Sohbet")
    
    # --- 1. ANALİZİ BAŞLATMA KISMI ---
    if uploaded_file and api_key and len(st.session_state.messages) == 0:
        st.info("Analizi başlatmak için butona basın. Sonrasında sohbet açılacaktır.")
        
        if st.button("Analizi Başlat 🚀", type="primary", use_container_width=True):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            # Prompt Hazırlığı
            base_prompt = "Sen uzman bir Makine Mühendisisin. Bu dosyayı incele. "
            ozel_istek = ""
            if mod == "Genel Kontrol": ozel_istek = "Eksik ölçüleri ve hataları listele."
            elif mod == "İmalatçı (CNC/Torna)": ozel_istek = "CNC operatörü gözüyle bak. İşleme zorlukları neler?"
            elif mod == "Kalite Kontrol (GD&T)": ozel_istek = "Toleranslara odaklan."
            elif mod == "🧪 Malzeme Danışmanı": ozel_istek = "Malzeme önerisi yap."
            elif mod == "💰 Maliyet Tahmini": ozel_istek = "Maliyet analizi yap."

            full_prompt = base_prompt + ozel_istek + " Cevabı Türkçe ve maddeler halinde ver."

            with st.spinner('Mühendis AI inceliyor...'):
                try:
                    # Veri Hazırlığı
                    input_data = None
                    if uploaded_file.type == "application/pdf":
                        input_data = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                    else:
                        input_data = Image.open(uploaded_file)

                    # Gemini'ye Sor
                    response = model.generate_content([full_prompt, input_data])
                    
                    # Cevabı Hafızaya Kaydet (Sohbetin ilk mesajı olarak)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    st.rerun() # Sayfayı yenile ki sohbet ekranı gelsin
                    
                except Exception as e:
                    st.error(f"Hata: {e}")

    # --- 2. SOHBET VE RAPOR GÖSTERİMİ ---
    if len(st.session_state.messages) > 0:
        
        # Eski mesajları (Rapor dahil) ekrana yazdır
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Eğer bu mesaj ilk raporsa, altına indirme butonu koy
                if message == st.session_state.messages[0]:
                    st.download_button(
                        label="📥 Raporu İndir (TXT)",
                        data=message["content"],
                        file_name="Analiz_Raporu.txt",
                        mime="text/plain"
                    )

        # --- 3. KULLANICI SORU SORMA KISMI ---
        st.divider()
        st.caption("💬 **Anlamadığın bir yer mi var? Aşağıya yaz, Mühendis AI cevaplasın.**")
        
        if prompt := st.chat_input("Örn: 'Neden çelik seçtin?' veya 'H7 toleransı nedir?'"):
            # 1. Kullanıcının mesajını ekle ve göster
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 2. Yapay Zekadan Cevap Al
            with st.chat_message("assistant"):
                with st.spinner("Düşünüyor..."):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        # Resmi tekrar okuyoruz (Hafızada tutmak için)
                        input_data = None
                        if uploaded_file.type == "application/pdf":
                            input_data = {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                        else:
                            input_data = Image.open(uploaded_file)
                        
                        # Sohbet geçmişini modele veriyoruz ki bağlamı kopmasın
                        chat_history = [full_prompt, input_data] # İlk prompt ve resim
                        
                        # Geçmiş konuşmaları da ekleyelim (Basitleştirilmiş history)
                        for msg in st.session_state.messages:
                            chat_history.append(msg["content"])
                        
                        # Yeni soruyu ekle
                        chat_history.append(prompt)

                        # Cevap üret (Stream = False yaptık ki hata riskini azaltalım)
                        response = model.generate_content(chat_history)
                        
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                        
                    except Exception as e:
                        st.error(f"Hata oluştu: {e}")