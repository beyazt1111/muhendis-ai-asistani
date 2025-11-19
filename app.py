import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mühendislik Asistanı", page_icon="📐", layout="wide")

# --- PDF OLUŞTURMA FONKSİYONU ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Muhendislik Asistani - Otomatik Rapor', 0, 1, 'C')
        self.ln(10)

def create_pdf(text):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Türkçe karakter sorunu için basit çözüm (Standart fontlarda TR karakterleri bozulabilir)
    # Bu fonksiyon karakterleri en yakın Latin karşılığına çevirir.
    replacements = {
        'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I',
        'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    clean_text = text
    for src, target in replacements.items():
        clean_text = clean_text.replace(src, target)
        
    pdf.multi_cell(0, 10, clean_text)
    return pdf.output(dest="S").encode("latin-1", "ignore")

# --- API ANAHTARI ---
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    with st.sidebar:
        st.warning("API Anahtarı Girilmedi")
        api_key = st.text_input("Gemini API Key", type="password")

# --- MODEL FONKSİYONU ---
def get_gemini_response(prompt, image=None):
    if not api_key: return "Lütfen API anahtarını girin."
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash') # Güçlü Model
    try:
        if image:
            response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Hata: {e}"

# ==========================================
# MODÜL 1: TEKNİK RESİM ANALİZİ
# ==========================================
def sayfa_analiz():
    st.header("Teknik Resim ve Tasarım Analizi")
    st.markdown("---")
    
    # Session State (Hafıza)
    if "analiz_sonuc" not in st.session_state: st.session_state.analiz_sonuc = None
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("Görsel Yükleme")
        uploaded_file = st.file_uploader("Dosya Seçin (PDF/Resim)", type=["jpg", "png", "pdf", "webp"])
        
        if uploaded_file:
            with st.expander("Dosya Önizleme", expanded=False):
                if uploaded_file.type != "application/pdf":
                    image = Image.open(uploaded_file)
                    st.image(image, use_column_width=True)
                else:
                    st.info("PDF dosyası yüklendi.")

    with col_right:
        st.subheader("Analiz Parametreleri")
        if uploaded_file:
            mod = st.selectbox(
                "Analiz Türü",
                ["Genel Hata Kontrolü", "İmalat Uygunluğu (CAM)", "Tolerans Analizi (GD&T)", "Malzeme Önerisi", "Maliyet Tahmini"]
            )
            
            if st.button("Analizi Başlat", type="primary", use_container_width=True):
                prompt = f"Sen tecrübeli bir mühendissin. Bu dosyayı '{mod}' kapsamında incele. Profesyonel teknik dille, maddeler halinde Türkçe rapor yaz."
                
                # Veri Hazırlığı
                img_data = Image.open(uploaded_file) if uploaded_file.type != "application/pdf" else {"mime_type": "application/pdf", "data": uploaded_file.getvalue()}
                
                with st.spinner("Gemini 2.0 analiz ediyor..."):
                    cevap = get_gemini_response(prompt, img_data)
                    st.session_state.analiz_sonuc = cevap
        else:
            st.info("Lütfen işlem yapmak için sol taraftan dosya yükleyin.")

    # SONUÇ EKRANI (TAM GENİŞLİK)
    if st.session_state.analiz_sonuc:
        st.markdown("---")
        st.subheader("Analiz Raporu")
        st.markdown(st.session_state.analiz_sonuc)
        
        # PDF İNDİRME
        pdf_data = create_pdf(st.session_state.analiz_sonuc)
        st.download_button(
            label="📄 Raporu PDF Olarak İndir",
            data=pdf_data,
            file_name="Teknik_Analiz_Raporu.pdf",
            mime="application/pdf"
        )

# ==========================================
# MODÜL 2: STAJ DEFTERİ OLUŞTURUCU (YENİ)
# ==========================================
def sayfa_staj():
    st.header("Staj Defteri Asistanı")
    st.markdown("Kısa notlarınızı girin, teknik bir dille yazılmış staj defteri sayfasına dönüştürelim.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    tarih = col1.date_input("Tarih")
    konu = col2.text_input("Yapılan İşin Başlığı (Örn: CNC Operasyonu)")
    
    notlar = st.text_area("Kısa Notlarınız (Örn: Bugün usta safety düğmesini gösterdi, parça bağladık, yüzey sildik.)", height=150)
    
    if st.button("Sayfayı Oluştur", type="primary"):
        if not notlar:
            st.error("Lütfen notlarınızı girin.")
        else:
            prompt = f"""
            Aşağıdaki kısa staj notlarını, bir makine mühendisliği öğrencisinin staj defterine yazacağı şekilde,
            edilgen çatı kullanarak (yapıldı, edildi), teknik terimlerle ve detaylıca yeniden yaz.
            Tarih: {tarih}
            Konu: {konu}
            Notlar: {notlar}
            
            Çıktı sadece metin olsun, giriş/çıkış konuşması yapma.
            """
            
            with st.spinner("Mühendislik diline çevriliyor..."):
                cevap = get_gemini_response(prompt)
                
                st.success("Oluşturulan Metin:")
                st.write(cevap)
                
                # PDF Hazırlığı (Başlık + İçerik)
                pdf_text = f"Tarih: {tarih}\nKonu: {konu}\n\n{cevap}"
                pdf_data = create_pdf(pdf_text)
                
                st.download_button(
                    label="📄 Staj Sayfasını PDF İndir",
                    data=pdf_data,
                    file_name=f"Staj_Defteri_{tarih}.pdf",
                    mime="application/pdf"
                )

# ==========================================
# MODÜL 3: MÜLAKAT SİMÜLASYONU
# ==========================================
def sayfa_mulakat():
    st.header("Teknik Mülakat Simülasyonu")
    st.markdown("---")

    if "history" not in st.session_state:
        st.session_state.history = []

    # Sohbet Geçmişi
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Kullanıcı Girişi
    if prompt := st.chat_input("Cevabınızı yazın..."):
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Bağlam (Context) oluştur
            gecmis_metin = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.history])
            system_prompt = f"""
            Sen kıdemli bir Mühendislik Yöneticisisin. Adayla teknik mülakat yapıyorsun.
            Sadece teknik sorular sor (Mukavemet, Malzeme, Üretim vb.).
            Kullanıcının cevabını yorumla ve yeni zorlayıcı bir soru sor.
            Konuşma Geçmişi:
            {gecmis_metin}
            """
            
            cevap = get_gemini_response(system_prompt)
            st.markdown(cevap)
            st.session_state.history.append({"role": "assistant", "content": cevap})

# ==========================================
# ANA MENÜ (SIDEBAR)
# ==========================================
with st.sidebar:
    st.title("Mühendislik Asistanı")
    st.markdown("Versiyon 5.0 Pro")
    st.markdown("---")
    
    secim = st.radio(
        "Araçlar",
        ["Teknik Resim Analizi", "Staj Defteri Oluşturucu", "Mülakat Hazırlık"],
        label_visibility="collapsed" # Başlığı gizle, daha sade olsun
    )
    
    st.markdown("---")
    if st.button("Sıfırla", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Sayfa Yönlendirme
if secim == "Teknik Resim Analizi":
    sayfa_analiz()
elif secim == "Staj Defteri Oluşturucu":
    sayfa_staj()
elif secim == "Mülakat Hazırlık":
    sayfa_mulakat()