import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="Mühendislik Asistanı",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PDF OLUŞTURMA MOTORU ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Muhendislik Asistani - Rapor Ciktisi', 0, 1, 'C')
        self.ln(5)

def create_pdf(text):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Türkçe karakter uyumluluğu (Latin-1 dönüşümü)
    replacements = {
        'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I',
        'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C',
        'â': 'a', 'î': 'i'
    }
    clean_text = text
    for src, target in replacements.items():
        clean_text = clean_text.replace(src, target)
        
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest="S").encode("latin-1", "ignore")

# --- API ANAHTARI YÖNETİMİ ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    pass # Sidebar'da sorulacak

# --- GEMINI 2.0 FLASH ENTEGRASYONU ---
def get_gemini_response(inputs):
    """
    Merkezi model fonksiyonu.
    Model: gemini-2.0-flash
    """
    if not api_key:
        return "Hata: API Anahtarı bulunamadı."
    
    try:
        genai.configure(api_key=api_key)
        # KESİNLİKLE GEMINI 2.0 KULLANILIYOR
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        if not isinstance(inputs, list):
            inputs = [inputs]
            
        response = model.generate_content(inputs)
        return response.text
    except Exception as e:
        return f"Sistem Hatası: {e}"

# ==========================================
# MODÜL 1: TEKNİK RESİM VE DOKÜMAN ANALİZİ
# ==========================================
def sayfa_analiz():
    st.title("Teknik Resim Analizi")
    st.markdown("Teknik dokümanlarınızı yükleyin, analiz türünü seçin ve detaylı mühendislik raporu alın.")
    st.markdown("---")

    # Hafıza Yönetimi
    if "analiz_msgs" not in st.session_state: st.session_state.analiz_msgs = []
    if "last_file" not in st.session_state: st.session_state.last_file = None
    
    # --- ÜST BÖLÜM: DOSYA VE AYARLAR ---
    col_resim, col_ayar = st.columns([1, 1])
    
    uploaded_file = None
    analiz_tetiklendi = False
    mod = "Genel Kontrol"

    with col_resim:
        st.subheader("1. Dosya Seçimi")
        uploaded_file = st.file_uploader("Dosya Yükle (PDF, JPG, PNG)", type=["jpg", "png", "pdf", "webp"])
        
        if uploaded_file:
            # Dosya değişirse hafızayı temizle
            if st.session_state.last_file != uploaded_file.name:
                st.session_state.analiz_msgs = []
                st.session_state.last_file = uploaded_file.name
            
            # Önizleme (Varsayılan olarak kapalı)
            with st.expander("Dosya Önizleme", expanded=False):
                if uploaded_file.type != "application/pdf":
                    image = Image.open(uploaded_file)
                    st.image(image, use_column_width=True)
                else:
                    st.info("PDF dosyası işleme hazır.")

    with col_ayar:
        st.subheader("2. Analiz Parametreleri")
        if uploaded_file:
            mod = st.selectbox(
                "Analiz Kapsamı",
                ["Genel Hata Kontrolü", "İmalat Uygunluğu (CAM)", "Kalite Kontrol (GD&T)", "Malzeme Seçimi", "Maliyet Analizi"]
            )
            
            if len(st.session_state.analiz_msgs) == 0:
                if st.button("Analizi Başlat", type="primary", use_container_width=True):
                    analiz_tetiklendi = True
        else:
            st.info("İşlem yapmak için lütfen dosya yükleyin.")

    # --- ANALİZ İŞLEMİ (GEMINI 2.0) ---
    if analiz_tetiklendi and uploaded_file and api_key:
        prompt = f"""
        Sen tecrübeli bir Baş Mühendissin. Yüklenen teknik dokümanı '{mod}' kapsamında detaylıca incele.
        Raporunu profesyonel, teknik bir dille ve maddeler halinde Türkçe olarak yaz.
        Duygusal ifadelerden kaçın, sadece teknik verilere ve gözlemlere odaklan.
        """
        
        # İçerik Hazırlığı
        input_content = [prompt]
        if uploaded_file.type == "application/pdf":
            input_content.append({"mime_type": "application/pdf", "data": uploaded_file.getvalue()})
        else:
            input_content.append(Image.open(uploaded_file))
            
        with st.spinner("Doküman analiz ediliyor..."):
            cevap = get_gemini_response(input_content)
            st.session_state.analiz_msgs.append({"role": "assistant", "content": cevap})
            st.rerun()

    # --- ALT BÖLÜM: RAPOR VE SOHBET (TAM EKRAN) ---
    if len(st.session_state.analiz_msgs) > 0:
        st.divider()
        st.subheader("Analiz Sonuçları ve Soru-Cevap")
        
        for i, msg in enumerate(st.session_state.analiz_msgs):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # İlk mesaj (Rapor) ise İndirme Butonu
                if i == 0:
                    pdf_bytes = create_pdf(msg["content"])
                    st.download_button("Raporu PDF Olarak Kaydet", pdf_bytes, "Analiz_Raporu.pdf", "application/pdf")

        # Sohbet Girişi
        if prompt := st.chat_input("Raporla ilgili teknik sorunuzu buraya yazın..."):
            st.session_state.analiz_msgs.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Yanıt oluşturuluyor..."):
                    # Bağlam
                    context_prompt = f"Önceki analiz bağlamı: {mod}. Kullanıcı sorusu: {prompt}"
                    
                    # Görsel + Geçmiş + Yeni Soru
                    input_content = [context_prompt]
                    if uploaded_file:
                        if uploaded_file.type == "application/pdf":
                            input_content.append({"mime_type": "application/pdf", "data": uploaded_file.getvalue()})
                        else:
                            input_content.append(Image.open(uploaded_file))
                    
                    history_text = "\n".join([m["content"] for m in st.session_state.analiz_msgs])
                    input_content.append(f"Geçmiş Konuşma:\n{history_text}")

                    cevap = get_gemini_response(input_content)
                    st.markdown(cevap)
                    st.session_state.analiz_msgs.append({"role": "assistant", "content": cevap})


# ==========================================
# MODÜL 2: STAJ DEFTERİ DÜZENLEYİCİ
# ==========================================
def sayfa_staj():
    st.title("Staj Defteri Düzenleyici")
    st.markdown("Ham notlarınızı kurumsal ve teknik bir dile çevirerek staj defteri formatına getirir.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    tarih = col1.date_input("Faaliyet Tarihi")
    konu = col2.text_input("Yapılan İş / Konu", placeholder="Örn: CNC Dik İşleme Operasyonu")
    
    notlar = st.text_area("Günlük Notlarınız", height=200, placeholder="Örn: Usta ile tezgahı açtık. Referans noktalarına gönderdik. G54 kodunu anlattı. Parçayı bağlarken komparatör saati kullandık.")
    
    if st.button("Metni Oluştur", type="primary"):
        if not api_key:
            st.error("API Anahtarı eksik.")
        elif not notlar:
            st.warning("Lütfen notlarınızı girin.")
        else:
            prompt = f"""
            Aşağıdaki staj notlarını, bir mühendislik öğrencisinin resmi staj defterine yazacağı formatta yeniden düzenle.
            
            Kurallar:
            1. Edilgen çatı kullan (Yapıldı, incelendi, gözlemlendi).
            2. Teknik terimler kullan (Örn: 'Vidaladık' yerine 'Tork anahtarı ile sıkıldı').
            3. Giriş ve sonuç cümleleri ekleme, sadece içeriği yaz.
            
            Tarih: {tarih}
            Konu: {konu}
            Ham Notlar: {notlar}
            """
            
            with st.spinner("Metin düzenleniyor..."):
                cevap = get_gemini_response(prompt)
                
                st.success("Düzenlenmiş Metin:")
                st.write(cevap)
                
                # PDF Çıktısı
                pdf_text = f"Tarih: {tarih}\nKonu: {konu}\n\n{cevap}"
                pdf_data = create_pdf(pdf_text)
                
                st.download_button(
                    label="Sayfayı PDF Olarak İndir",
                    data=pdf_data,
                    file_name=f"Staj_Defteri_{tarih}.pdf",
                    mime="application/pdf"
                )

# ==========================================
# MODÜL 3: MÜLAKAT SİMÜLASYONU (PRO)
# ==========================================
def sayfa_mulakat():
    st.title("Teknik Mülakat Simülasyonu")
    st.markdown("Hedef şirket ve pozisyon detaylarını girerek yapay zeka ile teknik mülakat provası yapın.")
    st.markdown("---")

    if "mulakat_msgs" not in st.session_state: st.session_state.mulakat_msgs = []
    if "mulakat_cv" not in st.session_state: st.session_state.mulakat_cv = None

    # Parametreler
    col1, col2 = st.columns(2)
    with col1:
        sirket = st.text_input("Hedef Şirket", placeholder="Örn: Bilinmeyen Makine A.Ş.")
        sektor = st.text_input("Şirketin Faaliyet Alanı", placeholder="Örn: Hidrolik Pompa Üretimi, Savunma Sanayi vb.")
        pozisyon = st.text_input("Başvurulan Pozisyon", placeholder="Örn: Üretim Mühendisi")
        
    with col2:
        cv_file = st.file_uploader("CV Yükle (Opsiyonel / PDF)", type=["pdf"])

    # Başlat Butonu
    if st.button("Simülasyonu Başlat", type="primary"):
        if not sirket or not sektor or not pozisyon:
            st.warning("Lütfen şirket ve pozisyon bilgilerini eksiksiz girin.")
        else:
            st.session_state.mulakat_msgs = []
            st.session_state.mulakat_cv = cv_file if cv_file else None
            
            ilk_mesaj = f"Merhaba. Ben {sirket} firmasından ({sektor} alanında faaliyet gösteriyoruz) Teknik Müdürüm. {pozisyon} pozisyonu için görüşmemize hoş geldin. Bize kısaca kendinden ve teknik geçmişinden bahseder misin?"
            st.session_state.mulakat_msgs.append({"role": "assistant", "content": ilk_mesaj})
            st.rerun()

    # Sohbet Akışı
    if st.session_state.mulakat_msgs:
        st.divider()
        
        for msg in st.session_state.mulakat_msgs:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if prompt := st.chat_input("Cevabınız..."):
            st.session_state.mulakat_msgs.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Yanıt bekleniyor..."):
                    
                    gecmis = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.mulakat_msgs])
                    
                    # System Prompt (Sektör Bilgisi Dahil)
                    system_prompt = f"""
                    Sen {sirket} şirketinde ({sektor} sektörü) çalışan profesyonel bir Teknik Yöneticisin.
                    Pozisyon: {pozisyon}.
                    
                    GÖREVLERİN:
                    1. Adayın cevabını teknik açıdan değerlendir.
                    2. Sektör ({sektor}) ile ilgili spesifik teknik sorular sor.
                    3. CV varsa, oradaki projelerden detay iste.
                    4. STAR (Situation-Task-Action-Result) tekniğine uygun cevaplar bekle.
                    5. Kısa ve net konuş.
                    
                    Konuşma Geçmişi:
                    {gecmis}
                    """
                    
                    inputs = [system_prompt]
                    if st.session_state.mulakat_cv:
                        inputs.append({"mime_type": "application/pdf", "data": st.session_state.mulakat_cv.getvalue()})
                        inputs.append("Adayın CV dokümanı ektedir.")
                    
                    cevap = get_gemini_response(inputs)
                    st.markdown(cevap)
                    st.session_state.mulakat_msgs.append({"role": "assistant", "content": cevap})

        # Değerlendirme Butonu
        if len(st.session_state.mulakat_msgs) > 4:
            st.divider()
            if st.button("Görüşmeyi Sonlandır ve Raporla"):
                degerlendirme_prompt = f"""
                Mülakat tamamlandı. Adayın performansını değerlendir.
                Şirket: {sirket} ({sektor})
                
                Lütfen aşağıdaki formatta bir karne oluştur:
                1. GENEL PUAN (10 üzerinden)
                2. GÜÇLÜ YÖNLER
                3. GELİŞİME AÇIK YÖNLER
                4. TEKNİK TAVSİYELER (Bu sektöre özel)
                
                Konuşma Geçmişi: {st.session_state.mulakat_msgs}
                """
                with st.spinner("Performans raporu hazırlanıyor..."):
                    karne = get_gemini_response(degerlendirme_prompt)
                    st.success("Mülakat Sonuç Raporu")
                    st.markdown(karne)
                    
                    pdf_bytes = create_pdf(karne)
                    st.download_button("Karneyi PDF Olarak İndir", pdf_bytes, "Mulakat_Sonucu.pdf", "application/pdf")

# ==========================================
# ANA MENÜ (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("Mühendislik Asistanı")
    st.caption("v5.0 Pro | Gemini 2.0 Flash")
    st.markdown("---")
    
    if not api_key:
        api_key = st.text_input("API Anahtarı", type="password")
        st.caption("Otomatik giriş için secrets.toml kullanın.")
    else:
        st.success("Sistem Bağlı")
    
    st.markdown("---")
    
    secim = st.radio(
        "Modüller",
        ["Teknik Resim Analizi", "Staj Defteri Düzenleyici", "Mülakat Simülasyonu"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("Oturumu Temizle", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Sayfa Yönlendirme
if secim == "Teknik Resim Analizi":
    sayfa_analiz()
elif secim == "Staj Defteri Düzenleyici":
    sayfa_staj()
elif secim == "Mülakat Simülasyonu":
    sayfa_mulakat()