import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# GLOBAL STYLE (ACCESSIBLE & EYE-CATCHING)
# ==================================================
px.defaults.template = "plotly_dark"
px.defaults.color_continuous_scale = px.colors.sequential.Blues

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="GIKnowledge Building – Participant Analytics",
    layout="wide"
)

# ==================================================
# UI POLISH (CSS)
# ==================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
    }

    h1 {
        font-size: 2.2rem;
        margin-bottom: 0.2rem;
    }

    hr {
        margin-top: 1rem;
        margin-bottom: 1rem;
        border: 0;
        border-top: 1px solid rgba(255,255,255,0.15);
    }

    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 16px;
        border-radius: 14px;
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 1.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==================================================
# LOAD DATA + CLEANING
# ==================================================
@st.cache_data
def load_data():
    df = pd.read_csv("data/data_peserta.csv")
    df.columns = df.columns.str.strip()

    def clean_text(series):
        return series.astype(str).str.strip()

    if 'Asal Instansi' in df.columns:
        df['Asal Instansi'] = clean_text(df['Asal Instansi']).str.lower()

    if 'Jenis Kelamin' in df.columns:
        df['Jenis Kelamin'] = clean_text(df['Jenis Kelamin']).str.title()

    if 'Fakultas/Sekolah Asal' in df.columns:
        df['Fakultas/Sekolah Asal'] = clean_text(df['Fakultas/Sekolah Asal']).str.title()

    if 'Prodi Asal' in df.columns:
        df['Prodi Asal'] = clean_text(df['Prodi Asal']).str.title()

    if 'Semester' in df.columns:
        df['Semester'] = clean_text(df['Semester'])

    def normalize_instansi(name):
        if not isinstance(name, str):
            return name
        n = name.lower()
        if 'gadjah' in n or n.strip() == 'ugm':
            return 'Universitas Gadjah Mada'
        if 'upn' in n:
            return 'UPN Veteran Yogyakarta'
        if 'sunan' in n or 'uin' in n:
            return 'Universitas Islam Negeri Sunan Kalijaga'
        if 'amikom' in n:
            return 'Universitas Amikom Yogyakarta'
        if 'uty' in n or 'teknologi yogyakarta' in n:
            return 'Universitas Teknologi Yogyakarta'
        return name.title()

    if 'Asal Instansi' in df.columns:
        df['Asal Instansi'] = df['Asal Instansi'].apply(normalize_instansi)

    def derive_jenjang(prodi, fakultas=None):
        if not isinstance(prodi, str):
            prodi = ''
        p = prodi.lower()
        if p.startswith('s1') or 'sarjana' in p:
            return 'S1'
        if p.startswith('s2') or 'magister' in p or 'master' in p:
            return 'S2'
        if p.startswith('d4') or 'vokasi' in (fakultas or '').lower():
            return 'Vokasi'
        return 'Lainnya'

    if 'Prodi Asal' in df.columns:
        df['Jenjang'] = df.apply(
            lambda r: derive_jenjang(
                r.get('Prodi Asal', ''),
                r.get('Fakultas/Sekolah Asal', '')
            ),
            axis=1
        )
    else:
        df['Jenjang'] = 'Lainnya'

    if 'Semester' in df.columns:
        df['Tahun Angkatan'] = df['Semester']
    else:
        df['Tahun Angkatan'] = 'N/A'

    return df

df = load_data()

# ==================================================
# RESET FILTER
# ==================================================
def reset_filters():
    st.session_state['instansi_selected'] = 'Semua'
    st.session_state['jenjang_selected'] = 'Semua'
    st.session_state['angkatan_selected'] = 'Semua'

# ==================================================
# SIDEBAR FILTER
# ==================================================
st.sidebar.title("🎛️ Filter Data")
st.sidebar.caption(
    "Gunakan kombinasi filter di bawah untuk mengeksplorasi "
    "profil peserta secara lebih spesifik."
)

if "instansi_selected" not in st.session_state:
    reset_filters()

if st.sidebar.button("🔄 Reset Semua Filter"):
    reset_filters()
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 🔎 Filter Dimensi")

instansi_options = ["Semua"] + sorted(df["Asal Instansi"].dropna().unique())
jenjang_options = ["Semua"] + sorted(df["Jenjang"].dropna().unique())
angkatan_options = ["Semua"] + sorted(df["Tahun Angkatan"].dropna().unique())

instansi_selected = st.sidebar.selectbox("🏫 Asal Universitas", instansi_options, key="instansi_selected")
jenjang_selected = st.sidebar.selectbox("🎓 Jenjang Pendidikan", jenjang_options, key="jenjang_selected")
angkatan_selected = st.sidebar.selectbox("📚 Tahun Angkatan", angkatan_options, key="angkatan_selected")

# ==================================================
# APPLY FILTER
# ==================================================
filtered_df = df.copy()

if instansi_selected != "Semua":
    filtered_df = filtered_df[filtered_df["Asal Instansi"] == instansi_selected]

if jenjang_selected != "Semua":
    filtered_df = filtered_df[filtered_df["Jenjang"] == jenjang_selected]

if angkatan_selected != "Semua":
    filtered_df = filtered_df[filtered_df["Tahun Angkatan"] == angkatan_selected]

# ==================================================
# HEADER
# ==================================================
st.title("📊 GIKnowledge Building – Participant Analytics")
st.caption(
    "Interactive demographic dashboard for monitoring participant distribution "
    "based on education level, cohort, and university."
)
st.divider()

# ==================================================
# KPI SECTION
# ==================================================
total_peserta = filtered_df.shape[0]

if total_peserta > 0:
    instansi_counts = filtered_df["Asal Instansi"].value_counts()
    jenjang_counts = filtered_df["Jenjang"].value_counts()
    instansi_terbanyak = instansi_counts.idxmax()
    jenjang_terbanyak = jenjang_counts.idxmax()
    instansi_pct = (instansi_counts.max() / total_peserta) * 100
else:
    instansi_terbanyak = "-"
    jenjang_terbanyak = "-"
    instansi_pct = 0

k1, k2, k3 = st.columns(3)
k1.metric("👥 Total Peserta", total_peserta)
k2.metric("🏫 Instansi Dominan", instansi_terbanyak, f"{instansi_pct:.1f}%")
k3.metric("🎓 Jenjang Dominan", jenjang_terbanyak)

st.divider()

# ==================================================
# ROW 1 – JENJANG & ANGKATAN
# ==================================================
col1, col2 = st.columns(2)

# --- BAGIAN JENJANG ---
jenjang_count = filtered_df["Jenjang"].value_counts().reset_index()
jenjang_count.columns = ["Jenjang", "Jumlah"]

# Hitung persentase untuk Jenjang
total_j = jenjang_count["Jumlah"].sum()
jenjang_count["Persentase"] = (jenjang_count["Jumlah"] / total_j * 100).round(1)

with col1:
    if jenjang_count.empty:
        st.info("📭 Tidak ada data jenjang pendidikan untuk filter yang dipilih.")
    else:
        fig_jenjang = px.pie(
            jenjang_count,
            names="Jenjang",
            values="Jumlah",
            hole=0.45,
            custom_data=["Persentase"], # Tambahkan data persen
            title="Proporsi Jenjang Pendidikan",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        # Menampilkan persentase langsung di label dan hover yang lebih rapi
        fig_jenjang.update_traces(
            textinfo="percent+label",
            hovertemplate="Jenjang: %{label}<br>Jumlah: %{value} orang<br>Proporsi: %{customdata[0]}%"
        )
        fig_jenjang.add_annotation(
            text=f"Total<br>{total_peserta}",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False
        )
        st.plotly_chart(fig_jenjang, use_container_width=True)

# --- BAGIAN ANGKATAN ---
angkatan_count = filtered_df["Tahun Angkatan"].value_counts().reset_index()
angkatan_count.columns = ["Tahun Angkatan", "Jumlah"]

# Hitung persentase untuk Angkatan
total_a = angkatan_count["Jumlah"].sum()
angkatan_count["Persentase"] = (angkatan_count["Jumlah"] / total_a * 100).round(1)

with col2:
    if angkatan_count.empty:
        st.info("📭 Tidak ada data tahun angkatan untuk filter yang dipilih.")
    else:
        fig_angkatan = px.bar(
            angkatan_count.sort_values("Tahun Angkatan"),
            x="Tahun Angkatan",
            y="Jumlah",
            custom_data=["Persentase"], # Tambahkan data persen
            title="Distribusi Tahun Angkatan",
            color="Jumlah"
        )
        fig_angkatan.update_traces(
            hovertemplate="Angkatan: %{x}<br>Jumlah: %{y} orang<br>Persentase: %{customdata[0]}%"
        )
        fig_angkatan.update_layout(
            yaxis_title="Jumlah Peserta",
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_angkatan, use_container_width=True)

st.divider()

# ==================================================
# ROW 2 – ASAL INSTANSI
# ==================================================
instansi_count = (
    filtered_df["Asal Instansi"]
    .value_counts()
    .sort_values(ascending=True)
    .reset_index()
)
instansi_count.columns = ["Asal Instansi", "Jumlah"]

# Hitung persentase untuk Instansi
total_i = instansi_count["Jumlah"].sum()
instansi_count["Persentase"] = (instansi_count["Jumlah"] / total_i * 100).round(1)

if instansi_count.empty:
    st.info("📭 Tidak ada data asal universitas untuk filter yang dipilih.")
else:
    fig_instansi = px.bar(
        instansi_count,
        x="Jumlah",
        y="Asal Instansi",
        orientation="h",
        custom_data=["Persentase"], # Tambahkan data persen
        title="Distribusi Asal Universitas",
        color="Jumlah"
    )

    fig_instansi.update_traces(
        # Untuk bar horizontal, %{y} adalah label instansi dan %{x} adalah jumlahnya
        hovertemplate="Instansi: %{y}<br>Jumlah: %{x} orang<br>Persentase: %{customdata[0]}%"
    )

    fig_instansi.update_layout(
        height=max(450, len(instansi_count) * 26),
        margin=dict(l=180, r=30, t=60, b=40),
        yaxis_title="",
        coloraxis_showscale=False
    )

    st.plotly_chart(fig_instansi, use_container_width=True)

st.divider()

# ==================================================
# INSIGHT SECTION
# ==================================================
st.subheader("🧠 Key Insights (Auto-Generated)")
st.caption("Insight diperbarui otomatis berdasarkan filter yang dipilih.")

if total_peserta == 0:
    st.warning("Tidak ada data pada filter yang dipilih.")
elif instansi_pct > 50:
    st.info("Satu universitas mendominasi lebih dari setengah total peserta.")
else:
    st.success("Distribusi peserta relatif beragam antar universitas.")

st.write(
    f"""
    - Total peserta: **{total_peserta} orang**
    - Instansi terbanyak: **{instansi_terbanyak}**
    - Jenjang dominan: **{jenjang_terbanyak}**
    """
)

# ==================================================
# FOOTER
# ==================================================
st.caption(
    "📌 GIKnowledge Building Participant Dashboard | "
    "Interactive Data Analyst Intern Assessment"
)
