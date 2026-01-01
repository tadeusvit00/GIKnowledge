import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import nltk
import plotly.express as px
from wordcloud import WordCloud
from collections import Counter
from nltk.corpus import stopwords
from nltk.util import ngrams

# =====================
# INITIALIZATION
# =====================
# Pastikan resource NLTK terunduh (opsional jika dijalankan di server baru)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="Evaluasi GIKnowledge Building 2025",
    layout="wide"
)

# =====================
# HELPER FUNCTIONS
# =====================
def clean_text(text):
    if pd.isna(text):
        return []
    
    # Ambil stopwords bahasa Indonesia
    stop_words = set(stopwords.words('indonesian'))
    
    # Custom Stopwords
    custom_stop = {
        "program", "giknowledge", "building", "kelas", "materi", "mentor", 
        "peserta", "kegiatan", "gik", "nan", "pertanyaan", "relevan", "pilih", "jawaban"
    }
    stop_words.update(custom_stop)
    
    text = str(text).lower()
    text = re.sub(r"[^a-z\s]", " ", text) # Hapus simbol & angka
    
    # Tokenisasi dan filter
    tokens = [t for t in text.split() if t not in stop_words and len(t) > 3]
    return tokens

def extract_bigrams(text, n=5):
    words = clean_text(text)
    bigrams = list(ngrams(words, 2))
    return Counter([" ".join(bg) for bg in bigrams]).most_common(n)

def get_representative_comments(df, col_text, n=3):
    comments = df[col_text].dropna().astype(str)
    return comments.head(n).tolist()

def get_relevant_comments(df, keywords, n=3):
    filtered = df["saran"].dropna().astype(str)
    filtered = filtered[
        filtered.str.lower().apply(lambda x: any(k in x for k in keywords))
    ]
    return filtered.head(n).tolist()

def get_dominant_reason(text, reason_map):
    scores = {}
    text_lower = text.lower()
    for reason, keywords in reason_map.items():
        scores[reason] = sum(text_lower.count(k) for k in keywords)
    scores = {k: v for k, v in scores.items() if v > 0}
    return max(scores, key=scores.get) if scores else None

# =====================
# LOAD DATA
# =====================
@st.cache_data
def load_data():
    # Pastikan file CSV tersedia di path berikut
    df = pd.read_csv("data/data_evaluasi.csv") 
    df.columns = df.columns.str.strip()

    column_mapping = {
        '5.1. Seberapa puas Anda terhadap Anda menilai kemampuan mentor dalam menjelaskan materi?': 'puas_mentor',
        '5.4. Seberapa puas Anda terhadap metode pembelajaran yang digunakan oleh mentor?': 'puas_metode',
        '5.5. Seberapa puas Anda terhadap materi kelas Program GIKnowledge Building 2025?': 'puas_materi',
        '5.7. Apakah materi dan kegiatan yang diberikan sesuai dengan kebutuhan pengembangan Anda?': 'sesuai_kebutuhan',
        '5.8. Apakah Program GIKnowledge Building membantu Anda memahami hal-hal baru yang relevan dengan rencana pekerjaan atau karier Anda?': 'relevan_karier',
        '5.9. Apakah Anda merasa lebih percaya diri setelah mengikuti program ini?': 'percaya_diri',
        '5.10. Sejauh mana program ini memberi dampak positif bagi cara Anda bekerja, berpikir, atau berkolaborasi?': 'dampak_positif',
        '5.11. Bagaimana pendapat Anda tentang jadwal dan durasi setiap sesi?': 'jadwal_durasi',
        '5.12. Seberapa puas Anda terhadap fasilitas kelas GIKnowledge Building 2025?': 'puas_fasilitas',
        '5.14. Seberapa puas Anda terhadap Tim GIK dalam memberikan bimbingan dan dukungan yang cukup selama  penyelenggaraan Program GIKnowledge Building 2025?': 'puas_tim',
        '5.19. Berdasarkan level kepuasanmu terhadap keseluruhan pelaksanaan program sejauh ini, seberapa mungkin Anda memberi rekomendasi ke teman atau mahasiswa lain untuk mengikuti Program GIKnowledge Building?': 'rekomendasi',
        '5.18. Apakah ada topik, metode, atau aktivitas baru yang ingin Anda tambahkan pada pelaksanaan selanjutnya?': 'harapan',
        '5.22. Berikan saran perbaikan untuk pengembangan dan keberlanjutan Program GIKnowledge Building!': 'saran'
    }
    return df.rename(columns=column_mapping)

df = load_data()

# =====================
# SIDEBAR
# =====================
st.sidebar.title("🧭 Navigasi Dashboard")
st.sidebar.caption("Evaluasi Program GIKnowledge Building 2025")

page = st.sidebar.radio(
    "Pilih Halaman Analisis",
    [
        "🏠 Overview",
        "📊 Analisis Kuantitatif",
        "📝 Analisis Kualitatif",
        "🔄 Analisis Bauran"
    ]
)

st.sidebar.divider()
st.sidebar.info(
    "Gunakan menu di atas untuk menjelajahi "
    "hasil evaluasi program secara komprehensif."
)

# =====================
# 🏠 PAGE: OVERVIEW
# =====================
if page == "🏠 Overview":
    st.title("📈 Optimalisasi Data & Evaluasi Program")
    st.subheader("GIKnowledge Building 2025")
    st.caption("Ringkasan performa program berdasarkan survei peserta")

    st.divider()

    # ===== METRIC SUMMARY =====
    col1, col2, col3 = st.columns(3)

    # 1. Menghitung jumlah responden yang memberikan jawaban valid (bukan NaN)
    df_valid = df.dropna(subset=["rekomendasi"])
    total_responden_valid = len(df_valid)

    # 2. Logic Akumulasi: (Sangat Direkomendasikan + Direkomendasikan) / Total Valid
    if total_responden_valid > 0:
        # Menghitung jumlah masing-masing kategori
        sangat_direkom = (df_valid["rekomendasi"] == "Sangat direkomendasikan").sum()
        direkomendasikan = (df_valid["rekomendasi"] == "Direkomendasikan").sum()
        
        # Menghitung persentase akumulatif agar sinkron dengan penjumlahan di grafik loyalitas
        rekom_pct = round((sangat_direkom + direkomendasikan) / total_responden_valid * 100, 1)
    else:
        rekom_pct = 0.0

    # --- TAMPILAN METRIC ---
    col1.metric(
        label="👥 Total Responden",
        value=total_responden_valid
    )

    col2.metric(
        label="⭐ Tingkat Rekomendasi",
        value=f"{rekom_pct}%",
        help="Akumulasi persentase responden 'Sangat Direkomendasikan' dan 'Direkomendasikan'"
    )

    col3.metric(
        label="⏱️ Durasi Program",
        value="± 2 Bulan"
    )

    st.divider()

    # ===== DESKRIPSI DASHBOARD =====
    st.markdown(
        """
        Dashboard ini menyajikan hasil **evaluasi menyeluruh Program
        GIKnowledge Building 2025** dengan pendekatan **mixed methods**, yaitu:

        - 📊 **Analisis Kuantitatif** untuk mengukur tingkat kepuasan peserta  
        - 📝 **Analisis Kualitatif** untuk mengidentifikasi aspirasi dan masukan  
        - 🔄 **Analisis Bauran** untuk menghubungkan persepsi numerik dan narasi peserta  

        Insight yang dihasilkan diharapkan dapat menjadi **dasar pengambilan
        keputusan strategis** dalam peningkatan kualitas dan keberlanjutan program.
        """
    )

# =====================
# 📊 PAGE: ANALISIS KUANTITATIF
# =====================
elif page == "📊 Analisis Kuantitatif":
    st.title("📊 Analisis Kuantitatif Program GIKnowledge Building 2025")
    st.caption(
        "Analisis berbasis 11 indikator utama untuk mengukur kualitas pengajaran, "
        "relevansi materi, dampak program, operasional, dan loyalitas peserta."
    )

    # =====================
    # KLASIFIKASI PERTANYAAN
    # =====================
    classifications = {
        "A. Kualitas Pengajaran (Mentor & Metode)": {
            "Kemampuan Mentor": "puas_mentor",
            "Metode Pembelajaran": "puas_metode"
        },
        "B. Materi & Relevansi Karier": {
            "Kualitas Materi Kelas": "puas_materi",
            "Kesesuaian dengan Kebutuhan": "sesuai_kebutuhan",
            "Relevansi terhadap Karier": "relevan_karier"
        },
        "C. Dampak & Kepercayaan Diri": {
            "Peningkatan Kepercayaan Diri": "percaya_diri",
            "Dampak Positif terhadap Pola Pikir/Cara Kerja": "dampak_positif"
        },
        "D. Operasional & Fasilitas": {
            "Kesesuaian Jadwal dan Durasi": "jadwal_durasi",
            "Fasilitas Kelas": "puas_fasilitas",
            "Dukungan Tim GIK": "puas_tim"
        },
        "E. Loyalitas Peserta": {
            "Tingkat Rekomendasi Program": "rekomendasi"
        }
    }

    # =====================
    # URUTAN JAWABAN
    # =====================
    sort_order = [
        "Sangat puas", "Puas", "Netral", "Tidak puas", "Sangat tidak puas",
        "Sangat berdampak", "Berdampak",
        "Cukup/ideal", "Terlalu singkat", "Terlalu panjang",
        "Sangat direkomendasikan", "Direkomendasikan", "Tidak direkomendasikan",
        "Ya", "Tidak"
    ]

    # =====================
    # LOOP PER KLASIFIKASI
    # =====================
    for class_name, questions in classifications.items():
        st.markdown(f"## {class_name}")
        st.markdown("Distribusi jawaban responden berdasarkan indikator berikut:")

        cols = st.columns(len(questions))

        for i, (label, col_name) in enumerate(questions.items()):
            with cols[i]:
                st.markdown(f"### {label}")

                if col_name not in df.columns:
                    st.error(f"Kolom `{col_name}` tidak ditemukan.")
                    continue

                data = df[col_name].dropna()
                if data.empty:
                    st.warning("Tidak ada data responden.")
                    continue

                freq = df[col_name].dropna().value_counts()

                if freq.empty:
                    st.warning("Tidak ada data.")
                    continue

                freq_df = freq.reset_index()
                freq_df.columns = ["Jawaban", "Jumlah"]

                freq_df["Persentase"] = round(
                    freq_df["Jumlah"] / freq_df["Jumlah"].sum() * 100, 1
                )


                # Urutkan kategori
                existing_order = [o for o in sort_order if o in freq_df["Jawaban"].values]
                if existing_order:
                    freq_df["Jawaban"] = pd.Categorical(
                        freq_df["Jawaban"],
                        categories=existing_order,
                        ordered=True
                    )
                    freq_df = freq_df.sort_values("Jawaban")

                # Mayoritas
                dominant = freq.idxmax()
                pct = round((freq.max() / freq.sum()) * 100, 1)

                # =====================
                # MINI KPI
                # =====================
                st.metric(
                    label="Jawaban Dominan",
                    value=dominant
                )

                is_yes_no = set(freq_df["Jawaban"]).issubset({"Ya", "Tidak"})

                # =====================
                # VISUALISASI
                # =====================
                if is_yes_no:
                    # PIE CHART (tetap tampil persen)
                    fig = px.pie(
                        freq_df,
                        names="Jawaban",
                        values="Jumlah",
                        hole=0.55,
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig.update_traces(
                        hovertemplate=
                        "<b>%{label}</b><br>"
                        "Jumlah responden: %{value}<br>"
                        "Persentase: %{percent}<extra></extra>"
                    )
                else:
                    # BAR CHART (tanpa angka)
                    fig = px.bar(
                        freq_df,
                        y="Jawaban",
                        x="Jumlah",
                        orientation="h",
                        color="Jumlah",
                        color_continuous_scale="Blues"
                    )
                    fig.update_traces(
                        hovertemplate=
                        "<b>%{x}</b><br>"
                        "Jumlah responden: %{y}<br>"
                        "Persentase: %{customdata[0]}%<extra></extra>",
                        customdata=freq_df[["Persentase"]]
                    )
                    fig.update_layout(coloraxis_showscale=False)

                fig.update_layout(
                    height=360,
                    margin=dict(l=10, r=10, t=40, b=10),
                    xaxis_title="",
                    yaxis_title=""
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key=f"chart_{class_name}_{col_name}"
                )

                # =====================
                # NARASI TEMUAN
                # =====================
                st.success(
                    f"**Temuan:** Mayoritas responden ({pct}%) memilih **'{dominant}'**, "
                    f"yang menunjukkan persepsi paling dominan pada indikator ini."
                )

        st.divider()

# =====================
# 📝 PAGE: ANALISIS KUALITATIF
# =====================
elif page == "📝 Analisis Kualitatif":
    st.title("📝 Analisis Kualitatif Aspirasi Peserta")
    st.markdown(
        """
        <div style='padding: 15px; border-radius: 10px; border-left: 5px solid #007BFF; margin-bottom: 20px;'>
            Mengidentifikasi tema utama dari <b>saran dan harapan</b> peserta menggunakan teknik 
            <i>Natural Language Processing (NLP)</i> sederhana berbasis frekuensi kata.
        </div>
        """, 
        unsafe_allow_html=True
    )

    # =====================
    # PREPARASI DATA TEKS
    # =====================
    text_data = pd.concat([df["saran"], df["harapan"]]).dropna()
    all_tokens = []
    for t in text_data:
        all_tokens.extend(clean_text(t))

    freq = Counter(all_tokens)
    most_common = freq.most_common(15)

    # =====================
    # SECTION: KATA KUNCI & WORD CLOUD
    # =====================
    with st.container(border=True):
        st.subheader("🔍 Eksplorasi Kata Kunci & Frekuensi")
        col1, col2 = st.columns([1.2, 1.8])

        with col1:
            st.markdown("##### 📈 Top 15 Kata Kunci")
            if most_common:
                freq_df = pd.DataFrame(most_common, columns=["Kata", "Jumlah"])
                st.dataframe(
                    freq_df,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
            else:
                st.warning("Data teks tidak tersedia.")

        with col2:
            st.markdown("##### ☁️ Word Cloud Aspirasi")
            if all_tokens:
                # Menambahkan sedikit estetika pada wordcloud
                wc = WordCloud(
                    width=1000,
                    height=600,
                    background_color="white",
                    colormap="viridis", # Mengganti ke viridis agar lebih modern
                    max_words=100
                ).generate(" ".join(all_tokens))

                fig, ax = plt.subplots(figsize=(12, 7))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                plt.tight_layout(pad=0)
                st.pyplot(fig)
            else:
                st.info("Word cloud tidak dapat ditampilkan.")

    st.markdown("<br>", unsafe_allow_html=True)

    # =====================
    # SECTION: IDENTIFIKASI TEMA
    # =====================
    st.subheader("📊 Pemetaan Tema Strategis")
    st.markdown("Aspirasi peserta dikelompokkan ke dalam kategori berikut berdasarkan kemunculan kata kunci:")

    THEME_MAP = {
        "Kemitraan & Karier": [
            "mitra", "perusahaan", "industri", "magang",
            "kerja", "lapangan", "kunjungan", "umkm"
        ],
        "Metode Pembelajaran": [
            "praktik", "diskusi", "interaktif", "tugas",
            "langsung", "praktek", "seru", "materi"
        ],
        "Manajemen & Fasilitas": [
            "jadwal", "waktu", "durasi", "sesi",
            "bentrok", "malam", "pagi", "link", "zoom", "fasilitas"
        ]
    }

    # Hitung data tema
    theme_results = []
    for theme, keywords in THEME_MAP.items():
        matched_words = [k for k in keywords if k in freq]
        theme_results.append({
            "Tema": theme,
            "Kata": matched_words,
            "Skor": sum(freq[k] for k in matched_words)
        })

    theme_df = pd.DataFrame(theme_results)
    t_cols = st.columns(3)

    for i, row in theme_df.iterrows():
        with t_cols[i]:
            with st.container(border=True):
                # Desain header mini untuk tema
                st.markdown(f"<p style='font-size: 14px; font-weight: bold; color: #666;'>TEMA {i+1}</p>", unsafe_allow_html=True)
                st.markdown(f"#### {row['Tema']}")
                
                # Menampilkan skor kemunculan untuk menambah bobot kuantitatif
                st.metric(label="Volume Aspirasi", value=row["Skor"])

                if row["Kata"]:
                    st.markdown("**Kata Kunci Dominan:**")
                    # Chip-style display sederhana
                    st.caption(", ".join(row["Kata"]))
                else:
                    st.caption("Tidak ada kata kunci terdeteksi.")

    st.markdown("<br>", unsafe_allow_html=True)

    # =====================
    # INSIGHT UTAMA
    # =====================
    if not theme_df.empty:
        # Mengurutkan berdasarkan skor tertinggi untuk insight dinamis
        top_theme = theme_df.sort_values(by="Skor", ascending=False).iloc[0]
        
        st.success(
            f"🎯 **Insight Utama:** Berdasarkan volume kata kunci, aspirasi peserta paling dominan berfokus pada tema "
            f"**{top_theme['Tema'].upper()}**. Hal ini menunjukkan area tersebut merupakan prioritas utama "
            f"bagi peserta untuk pengembangan program di masa depan."
        )

    st.divider()

# =====================
# 🔄 PAGE: ANALISIS BAURAN
# =====================
elif page == "🔄 Analisis Bauran":
    st.title("🔄 Analisis Bauran (Mixed Methods)")
    st.markdown(
        """
        <div style='padding: 15px; border-radius: 10px; border-left: 5px solid #007BFF; margin-bottom: 20px;'>
            Analisis ini mengintegrasikan <b>skor kepuasan (kuantitatif)</b> dan <b>komentar peserta (kualitatif)</b> 
            untuk membedah alasan mendalam di balik angka kepuasan yang muncul.
        </div>
        """, 
        unsafe_allow_html=True
    )

    # --- LOGIKA PERHITUNGAN (Tetap Sama) ---
    score_map = {"Sangat puas": 5, "Puas": 4, "Netral": 3, "Tidak puas": 2, "Sangat tidak puas": 1}
    score_cols = ["puas_mentor", "puas_metode", "puas_materi", "puas_fasilitas", "puas_tim"]

    for col in score_cols:
        df[col + "_score"] = df[col].map(score_map)
    
    df["avg_kepuasan"] = df[[c + "_score" for c in score_cols]].mean(axis=1, skipna=True)

    high_sat = df[df["avg_kepuasan"] >= 4.2]
    low_sat  = df[df["avg_kepuasan"] < 4.2]

    REASON_MAP = {
        "Akses perusahaan mitra & peluang magang": ["perusahaan", "mitra", "magang"],
        "Pengalaman kunjungan industri yang aplikatif": ["kunjungan", "industri", "lapangan"],
        "Pembelajaran praktis & relevan": ["praktik", "langsung", "digital"],
        "Kendala jadwal dan durasi kegiatan": ["jadwal", "waktu", "durasi"],
        "Keterbatasan pendampingan lanjutan": ["mentor", "evaluasi", "pendamping"]
    }

    # --- LAYOUTING CARDS ---
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("<h3 style='color: #28a745;'>😊 Kepuasan Tinggi</h3>", unsafe_allow_html=True)
            st.metric(
                "Rata-rata Skor Kepuasan",
                round(high_sat["avg_kepuasan"].mean(), 2) if not high_sat.empty else 0
            )

            st.markdown("---")
            st.markdown("**Alasan Program Disukai Peserta:**")

            text_high = " ".join(
                high_sat[["saran", "harapan"]]
                .fillna("")
                .astype(str)
                .agg(" ".join, axis=1)
            ).lower()

            found_reason = False

            for reason, keywords in list(REASON_MAP.items())[:3]:
                if any(k in text_high for k in keywords):
                    found_reason = True

                    # Narasi alasan
                    st.success(
                        f"**{reason}** menjadi faktor utama yang mendorong "
                        "tingginya kepuasan peserta terhadap program."
                    )

                    # Bukti komentar
                    with st.expander("📌 Bukti Komentar Peserta"):
                        comments = get_relevant_comments(high_sat, keywords)
                        if comments:
                            for c in comments[:5]:
                                st.markdown(f"- *{c}*")
                        else:
                            st.caption("Tidak ada komentar spesifik yang terdeteksi.")

            if not found_reason:
                st.caption(
                    "Komentar peserta menunjukkan kepuasan umum terhadap program, "
                    "namun tidak terdapat alasan dominan yang muncul secara konsisten."
                )


    with col2:
        with st.container(border=True):
            st.markdown("<h3 style='color: #dc3545;'>😐 Kepuasan Lebih Rendah</h3>", unsafe_allow_html=True)
            st.metric(
                "Rata-rata Skor Kepuasan",
                round(low_sat["avg_kepuasan"].mean(), 2) if not low_sat.empty else 0
            )

            st.markdown("---")
            st.markdown("**Kendala Utama yang Dirasakan Peserta:**")

            text_low = " ".join(
                low_sat[["saran", "harapan"]]
                .fillna("")
                .astype(str)
                .agg(" ".join, axis=1)
            ).lower()

            found_issue = False

            for reason, keywords in list(REASON_MAP.items())[3:]:
                if any(k in text_low for k in keywords):
                    found_issue = True

                    # Narasi kendala
                    st.warning(
                        f"**{reason}** menjadi faktor utama yang menurunkan "
                        "tingkat kepuasan sebagian peserta."
                    )

                    # Bukti komentar
                    with st.expander("📌 Bukti Komentar Peserta"):
                        comments = get_relevant_comments(low_sat, keywords)
                        if comments:
                            for c in comments[:5]:
                                st.markdown(f"- *{c}*")
                        else:
                            st.caption("Tidak ada komentar spesifik yang terdeteksi.")

            if not found_issue:
                st.caption(
                    "Sebagian peserta menunjukkan tingkat kepuasan yang lebih rendah, "
                    "namun tidak terdapat kendala dominan yang muncul secara konsisten "
                    "dalam komentar mereka."
                )

    # --- SECTION: KESIMPULAN ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("📌 Kesimpulan Strategis Bauran")
        
        dominant_high = get_dominant_reason(text_high, dict(list(REASON_MAP.items())[:3]))
        dominant_low = get_dominant_reason(text_low, dict(list(REASON_MAP.items())[3:]))

        if dominant_high and dominant_low:
            # Gunakan st.info untuk highlight teks kesimpulan
            st.info(f"""
            Hasil analisis menunjukkan pola yang jelas:
            1. **Faktor Pendorong (Promoter):** Peserta dengan tingkat kepuasan tinggi (Skor: {round(high_sat['avg_kepuasan'].mean(),2)}) 
               sangat dipengaruhi oleh **{dominant_high.lower()}**.
            2. **Faktor Penghambat (Detractor):** Peserta dengan kepuasan lebih rendah (Skor: {round(low_sat['avg_kepuasan'].mean(),2)}) 
               merasa terganggu oleh **{dominant_low.lower()}**.
            """)
        else:
            st.write("Data bauran menunjukkan pola persepsi yang berbeda antara aspek manfaat program dan kendala teknis implementasi.")

    st.divider()