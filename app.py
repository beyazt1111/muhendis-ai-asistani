import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io

# --- SAYFA AYARLARI ---
st.set_page_config(
    page_title="Mühendislik Asistanı",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS (ARAYÜZ DÜZENLEMELERİ) ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 4rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        width: 100%;
        overflow-x: auto;
        gap: 5px;
        border-bottom: 2px solid #333;
        padding-bottom: 0px;
        position: sticky;
        top: 3.5rem;
        background-color: #0e1117;
        z-index: 99999;
        padding-top: 10px;
        margin-top: 0px;
        align-items: end;
    }
    div[role="radiogroup"] label > div:first-child { display: none; }
    div[role="radiogroup"] label {
        background-color: #1c1f26;
        border: 1px solid #333;
        border-bottom: none;
        border-radius: 10px 10px 0px 0px;
        padding: 12px 25px;
        margin-right: 0px !important;
        cursor: pointer;
        transition: all 0.2s;
        color: #aaa;
        font-size: 1rem;
        font-weight: 500;
        min-width: 120px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 50px !important;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: #262730 !important;
        border-top: 3px solid #ff4b4b;
        border-left: 1px solid #333;
        border-right: 1px solid #333;
        color: #ffffff !important;
        font-weight: bold;
        border-bottom: 2px solid #262730;
        margin-bottom: -2px;
        z-index: 10;
        height: 55px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        flex-direction: column;
        border-bottom: none;
        position: static;
        height: auto !important;
        padding-top: 0;
        background-color: transparent;
        top: 0;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        height: auto !important;
        border: none;
        border-radius: 5px;
        text-align: left;
        justify-content: flex-start;
        background-color: transparent;
        margin-bottom: 5px;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
        height: auto !important;
        background-color: #262730 !important;
        border-top: none;
        border-left: 4px solid #ff4b4b;
        margin-bottom: 5px;
    }
    .stButton>button { border-radius: 8px; font-weight: 600; border: 1px solid #444; }
    .stTextInput input { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- PDF MOTORU ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Muhendislik Asistani Raporu', 0, 1, 'C')
        self.ln(5)

def create_pdf(text):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    replacements = {'ğ': 'g', 'Ğ': 'G', 'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C', 'â': 'a'}
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
    pass

# --- MODEL FONKSİYONU ---
def get_gemini_response(inputs):
    if not api_key: return "Hata: API Anahtarı Eksik."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        if not isinstance(inputs, list): inputs = [inputs]
        response = model.generate_content(inputs)
        return response.text
    except Exception as e:
        return f"Sistem Hatası: {e}"

# ==================================================
# MODÜL 1: DERS ASİSTANI (PDF EKLENDİ)
# ==================================================
def sayfa_ders_asistani():
    if "dersler" not in st.session_state: st.session_state.dersler = {} 
    if "aktif_ders_sekmesi" not in st.session_state: st.session_state.aktif_ders_sekmesi = "➕ Yeni Ders"

    mevcut_dersler = list(st.session_state.dersler.keys())
    sekme_secenekleri = mevcut_dersler + ["➕ Yeni Ders"]
    try: secili_index = sekme_secenekleri.index(st.session_state.aktif_ders_sekmesi)
    except ValueError: secili_index = len(sekme_secenekleri) - 1

    secilen_sekme = st.radio("nav_ders", sekme_secenekleri, index=secili_index, horizontal=True, label_visibility="collapsed", key="nav_radio")
    if secilen_sekme != st.session_state.aktif_ders_sekmesi:
        st.session_state.aktif_ders_sekmesi = secilen_sekme
        st.rerun()

    st.write("") 

    if st.session_state.aktif_ders_sekmesi == "➕ Yeni Ders":
        st.markdown("### 🆕 Yeni Ders Oluştur")
        st.info("Buradan eklediğiniz ders otomatik olarak çalışma alanına eklenecektir.")
        col1, col2 = st.columns([3, 1])
        yeni_isim = col1.text_input("Ders Adı", placeholder="Örn: Akışkanlar Mekaniği")
        if col2.button("Dersi Ekle ve Git", use_container_width=True):
            if yeni_isim and yeni_isim not in st.session_state.dersler:
                st.session_state.dersler[yeni_isim] = {'sorular': [], 'formuller': []}
                st.session_state.aktif_ders_sekmesi = yeni_isim
                st.rerun()
            elif yeni_isim in st.session_state.dersler: st.warning("Bu ders zaten var.")

    else:
        ders_adi = st.session_state.aktif_ders_sekmesi
        col_sol, col_sag = st.columns([1, 3])
        with col_sol:
            st.markdown(f"### 📂 {ders_adi}")
            ozellik = st.radio("Araçlar", ["Soru Çözücü", "Formül Defteri", "Örnek Sınav"], key=f"rad_{ders_adi}")
            st.markdown("---")
            if st.button(f"Dersi Sil", key=f"del_{ders_adi}"):
                del st.session_state.dersler[ders_adi]
                st.session_state.aktif_ders_sekmesi = "➕ Yeni Ders"
                st.rerun()

        with col_sag:
            if ozellik == "Soru Çözücü":
                st.info("Soruyu yükleyin, Yapay Zeka çözsün.")
                # PDF DESTEĞİ EKLENDİ
                q_file = st.file_uploader("Soru Dosyası (PDF/Resim)", type=["jpg", "png", "pdf"], key=f"up_{ders_adi}")
                
                if q_file:
                    # Görselse Göster, PDF ise ikon göster
                    if q_file.type != "application/pdf":
                        img = Image.open(q_file)
                        st.image(img, width=400)
                        input_data = img
                    else:
                        st.success("📄 PDF Yüklendi")
                        input_data = {"mime_type": "application/pdf", "data": q_file.getvalue()}

                    if st.button("Çöz ve Kaydet", key=f"solve_{ders_adi}", type="primary"):
                        if api_key:
                            with st.spinner("Çözülüyor..."):
                                prompt = f"Ders: {ders_adi}. Adım adım çöz. En alta '---FORMÜLLER---' başlığı ile formülleri listele."
                                res = get_gemini_response([prompt, input_data])
                                parts = res.split("---FORMÜLLER---")
                                st.markdown(parts[0])
                                st.session_state.dersler[ders_adi]['sorular'].append(parts[0])
                                if len(parts) > 1:
                                    st.session_state.dersler[ders_adi]['formuller'].append(parts[1].strip())
                                    st.success("Formüller kaydedildi.")
                        else: st.error("API Anahtarı eksik.")

            elif ozellik == "Formül Defteri":
                st.subheader("Kayıtlı Formüller")
                flist = st.session_state.dersler[ders_adi]['formuller']
                if flist:
                    for f in flist: st.code(f)
                    st.download_button("PDF İndir", create_pdf("\n".join(flist)), "Formuller.pdf")
                else: st.warning("Henüz kayıtlı formül yok.")

            elif ozellik == "Örnek Sınav":
                st.subheader("Deneme Sınavı")
                if st.button("Sınav Hazırla", key=f"ex_{ders_adi}"):
                    hist = str(st.session_state.dersler[ders_adi]['sorular'])[:2500]
                    if not hist: st.warning("Önce soru çözdürmelisiniz.")
                    else:
                        with st.spinner("Hazırlanıyor..."):
                            res = get_gemini_response(f"Ders: {ders_adi}. 4 soru yaz. Cevap verme. {hist}")
                            st.markdown(res)
                            st.download_button("Sınav PDF", create_pdf(res), "Sinav.pdf")

# ==================================================
# MODÜL 2: TEKNİK RESİM ANALİZİ (PDF ZATEN VARDI)
# ==================================================
def sayfa_analiz():
    st.title("Teknik Resim Analizi")
    st.markdown("---")
    if "analiz_msgs" not in st.session_state: st.session_state.analiz_msgs = []
    
    col1, col2 = st.columns([1, 1])
    with col1:
        f = st.file_uploader("Dosya Yükle", type=["jpg", "png", "pdf"])
        if f:
             with st.expander("Önizleme", expanded=False):
                 if f.type != "application/pdf": st.image(Image.open(f))
                 else: st.info("PDF Yüklendi")
    with col2:
        m = st.selectbox("Mod", ["Genel Kontrol", "İmalat (CAM)", "Malzeme Seçimi", "Maliyet Analizi"])
        if f and st.button("Analizi Başlat", type="primary", use_container_width=True):
            c = [f"Bu dosyayı '{m}' modunda analiz et. Profesyonel rapor yaz."]
            if f.type == "application/pdf": c.append({"mime_type": "application/pdf", "data": f.getvalue()})
            else: c.append(Image.open(f))
            with st.spinner("Yapay Zeka dosyayı inceliyor..."):
                resp = get_gemini_response(c)
                st.session_state.analiz_msgs = [{"role": "assistant", "content": resp}]
                st.rerun()

    if st.session_state.analiz_msgs:
        st.divider()
        for msg in st.session_state.analiz_msgs:
            st.markdown(msg["content"])
            if msg == st.session_state.analiz_msgs[0]:
                st.download_button("Raporu PDF İndir", create_pdf(msg["content"]), "Rapor.pdf", "application/pdf")
        if prompt := st.chat_input("Raporla ilgili sormak istediğiniz bir detay var mı?"):
            st.session_state.analiz_msgs.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)
            hist = "\n".join([m["content"] for m in st.session_state.analiz_msgs])
            c = [f"Önceki analiz bağlamında cevap ver: {prompt}\nGeçmiş: {hist}"]
            if f: 
                if f.type == "application/pdf": c.append({"mime_type": "application/pdf", "data": f.getvalue()})
                else: c.append(Image.open(f))
            res = get_gemini_response(c)
            st.session_state.analiz_msgs.append({"role": "assistant", "content": res})
            st.chat_message("assistant").markdown(res)

# ==================================================
# MODÜL 3: STAJ DEFTERİ (SOLA HİZALANDI)
# ==================================================
def sayfa_staj():
    st.title("Staj Defteri Düzenleyici")
    st.markdown("---")
    
    # --- DEĞİŞİKLİK: COLUMNS (2 Sütun) KALDIRILDI, TEK SÜTUN OLDU ---
    d = st.date_input("Faaliyet Tarihi")
    t = st.text_input("Yapılan İş / Konu", placeholder="Örn: CNC Dik İşleme Operasyonu")
    n = st.text_area("Ham Notlar", height=150, placeholder="Örn: Bugün usta ile tezgahın periyodik bakımını yaptık.")
    
    if st.button("Profesyonel Metne Çevir", type="primary"):
        with st.spinner("Yapay Zeka metni düzenliyor..."):
            res = get_gemini_response(f"Staj notu teknik dil, edilgen çatı: {n}")
            st.write(res)
            st.download_button("Sayfayı PDF Olarak İndir", create_pdf(f"{d} - {t}\n\n{res}"), "Staj.pdf")

# ==================================================
# MODÜL 4: MÜLAKAT KOÇU (PDF EKLENDİ)
# ==================================================
def sayfa_mulakat():
    st.title("Mülakat Simülasyonu")
    st.markdown("---")
    if "mlog" not in st.session_state: st.session_state.mlog = []
    c1, c2 = st.columns(2)
    
    s = c1.text_input("Şirket Adı", placeholder="Örn: TUSAŞ")
    sec = c1.text_input("Sektör", placeholder="Örn: Savunma Sanayi")
    p = c2.text_input("Pozisyon", placeholder="Örn: Üretim Mühendisi")
    cv = c2.file_uploader("CV (PDF)", type=["pdf"])
    
    if st.button("Simülasyonu Başlat", type="primary"):
        st.session_state.mlog = [{"role": "assistant", "content": f"Merhaba. Ben {s} ({sec}) firmasından Teknik Müdürüm. {p} pozisyonu için seninle görüşmek istiyorum."}]
        st.rerun()
        
    for m in st.session_state.mlog: st.chat_message(m["role"]).markdown(m["content"])
    
    if usr := st.chat_input("Cevabınızı buraya yazın..."):
        st.session_state.mlog.append({"role": "user", "content": usr})
        st.chat_message("user").write(usr)
        inps = [f"Sen {s} ({sec}) yöneticisisin. Doğal konuş. Geçmiş: {st.session_state.mlog}"]
        if cv: inps += [{"mime_type": "application/pdf", "data": cv.getvalue()}, "CV Ekte"]
        
        with st.spinner("Mülakatçı dinliyor..."):
            res = get_gemini_response(inps)
            st.session_state.mlog.append({"role": "assistant", "content": res})
            st.chat_message("assistant").write(res)
    
    if len(st.session_state.mlog) > 4:
        st.divider()
        if st.button("Görüşmeyi Bitir ve Raporla"):
            with st.spinner("Yapay Zeka performansınızı analiz ediyor..."):
                rpt = get_gemini_response(f"Mülakatı değerlendir. Puanla. Geçmiş: {st.session_state.mlog}")
                st.markdown(rpt)
                st.download_button("Karne PDF", create_pdf(rpt), "Karne.pdf")

# ==================================================
# ANA MENÜ (SOL TARAF)
# ==================================================
with st.sidebar:
    st.header("Mühendislik Asistanı")
    if not api_key: 
        api_key = st.text_input("API Anahtarı", type="password")
        st.caption("Otomatik giriş için secrets.toml kullanın.")
    else:
        st.success("Yapay Zeka Bağlantısı Aktif")
    
    st.markdown("---")
    nav = st.radio("Modüller", ["Ders Çalışma Asistanı", "Teknik Resim Analizi", "Staj Defteri", "Mülakat Koçu"], label_visibility="collapsed")
    st.markdown("---")
    if st.button("Oturumu Temizle"): st.session_state.clear(); st.rerun()

if nav == "Ders Çalışma Asistanı": sayfa_ders_asistani()
elif nav == "Teknik Resim Analizi": sayfa_analiz()
elif nav == "Staj Defteri": sayfa_staj()
elif nav == "Mülakat Koçu": sayfa_mulakat()