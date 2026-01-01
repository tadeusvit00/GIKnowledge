import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Dashboard Pendaftar GIKnowledge Building",
    layout="wide"
)

# ==================================================
# GLOBAL VISUAL STYLE
# ==================================================
px.defaults.template = "plotly_dark"
px.defaults.color_continuous_scale = px.colors.sequential.Blues

# ==================================================
# UI POLISH (CSS ONLY – NO LOGIC CHANGE)
# ==================================================
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
    }

    h1 {
        font-size: 2.1rem;
        margin-bottom: 0.3rem;
    }

    h2, h3 {
        margin-top: 0.6rem;
    }

    hr {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.12);
        margin: 1.2rem 0;
    }

    /* KPI cards */
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        padding: 16px;
        border-radius: 14px;
    }

    div[data-testid="metric-container"] label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.75);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            rgba(20,20,20,0.95),
            rgba(10,10,10,0.95)
        );
    }

    section[data-testid="stSidebar"] h1 {
        font-size: 1.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==================================================
# LOAD DATA
# ==================================================
@st.cache_data
def load_data():
    df = pd.read_csv("data/data_pendaftar.csv")
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

df = load_data()

# ==================================================
# DATA CLEANING (LOGIC UNCHANGED)
# ==================================================
def clean_text(series):
    return series.astype(str).str.strip().str.lower()

df['Asal Instansi'] = clean_text(df['Asal Instansi'])
df['Jenjang pendidikan asal'] = clean_text(df['Jenjang pendidikan asal'])
df['Jenis kelamin'] = clean_text(df['Jenis kelamin'])

semester_col = (
    'Semester kuliah bagi mahasiswa aktif ketika mengikuti Program '
    'GIKnowledge Building (di semester ganjil tahun ajaran 2025/2026)?'
)
df[semester_col] = clean_text(df[semester_col])

def normalize_instansi(name):
    if "gadjah" in name or "ugm" in name:
        return "Universitas Gadjah Mada"
    if "upn" in name:
        return "UPN Veteran Yogyakarta"
    if "sunan kalijaga" in name or "uin" in name:
        return "Universitas Islam Negeri Sunan Kalijaga"
    if "amikom" in name:
        return "Universitas Amikom Yogyakarta"
    if "uty" in name or "teknologi yogyakarta" in name:
        return "Universitas Teknologi Yogyakarta"
    return name.title()

df['Asal Instansi'] = df['Asal Instansi'].apply(normalize_instansi)

# ==================================================
# SIDEBAR FILTER
# ==================================================
st.sidebar.title("🎛️ Filter Data")
st.sidebar.caption("Gunakan filter untuk mengeksplorasi data pendaftar")

if st.sidebar.button("🔄 Reset All Filter"):
    min_date = df['Timestamp'].dt.date.min()
    max_date = df['Timestamp'].dt.date.max()
    st.session_state['date_range'] = (min_date, max_date)
    st.session_state['instansi_selected'] = "Semua"
    st.session_state['jenjang_selected'] = "Semua"
    st.session_state['gender_selected'] = "Semua"
    st.session_state['semester_selected'] = "Semua"
    st.rerun()

st.sidebar.divider()

min_date = df['Timestamp'].dt.date.min()
max_date = df['Timestamp'].dt.date.max()

if "date_range" not in st.session_state:
    st.session_state["date_range"] = (min_date, max_date)

date_range = st.sidebar.date_input(
    "📅 Rentang Tanggal",
    min_value=min_date,
    max_value=max_date,
    key="date_range"
)

# ==================================================
# DATE RANGE VALIDATION (ERROR HANDLING)
# ==================================================
if (
    not isinstance(date_range, (list, tuple)) or
    len(date_range) != 2 or
    date_range[0] is None or
    date_range[1] is None
):
    st.sidebar.warning("⚠️ Pilih rentang tanggal yang valid.")
    date_start, date_end = min_date, max_date
else:
    date_start, date_end = date_range

# Handle inverted range
if date_start > date_end:
    st.sidebar.warning("⚠️ Tanggal awal lebih besar dari tanggal akhir. Rentang direset.")
    date_start, date_end = min_date, max_date

instansi_list = ["Semua"] + sorted(df['Asal Instansi'].unique())
jenjang_list = ["Semua"] + sorted(df['Jenjang pendidikan asal'].unique())
gender_list = ["Semua"] + sorted(df['Jenis kelamin'].unique())
semester_list = ["Semua"] + sorted(df[semester_col].unique())

instansi_selected = st.sidebar.selectbox("🏫 Asal Instansi", instansi_list, key="instansi_selected")
jenjang_selected = st.sidebar.selectbox("🎓 Jenjang Pendidikan", jenjang_list, key="jenjang_selected")
gender_selected = st.sidebar.selectbox("👥 Jenis Kelamin", gender_list, key="gender_selected")
semester_selected = st.sidebar.selectbox("📚 Semester / Angkatan", semester_list, key="semester_selected")

# ==================================================
# APPLY FILTER (UNCHANGED)
# ==================================================
filtered_df = df.copy()

filtered_df = filtered_df[
    (filtered_df['Timestamp'].dt.date >= date_start) &
    (filtered_df['Timestamp'].dt.date <= date_end)
]

if instansi_selected != "Semua":
    filtered_df = filtered_df[filtered_df['Asal Instansi'] == instansi_selected]

if jenjang_selected != "Semua":
    filtered_df = filtered_df[filtered_df['Jenjang pendidikan asal'] == jenjang_selected]

if gender_selected != "Semua":
    filtered_df = filtered_df[filtered_df['Jenis kelamin'] == gender_selected]

if semester_selected != "Semua":
    filtered_df = filtered_df[filtered_df[semester_col] == semester_selected]

# ==================================================
# HEADER
# ==================================================
st.title("📊 Dashboard Pendaftar GIKnowledge Building")
st.caption(
    "Interactive analytics dashboard untuk memantau demografi "
    "dan tren pendaftaran program GIKnowledge Building."
)
st.divider()

# ==================================================
# KPI
# ==================================================
total_pendaftar = filtered_df.shape[0]

if total_pendaftar > 0:
    instansi_terbanyak = filtered_df['Asal Instansi'].value_counts().idxmax()
    hari_terpadat = filtered_df['Timestamp'].dt.date.value_counts().idxmax()
else:
    instansi_terbanyak = "-"
    hari_terpadat = "-"

k1, k2, k3 = st.columns(3)
k1.metric("👥 Total Pendaftar", f"{total_pendaftar}")
k2.metric("🏫 Instansi Terbanyak", instansi_terbanyak)
k3.metric("📅 Hari Terpadat", str(hari_terpadat))

st.divider()

# ==================================================
# ROW 1 – GENDER & JENJANG
# ==================================================
col1, col2 = st.columns(2)

gender_count = filtered_df['Jenis kelamin'].value_counts().reset_index()
gender_count.columns = ['Jenis Kelamin', 'Jumlah']

with col1:
    if gender_count.empty:
        st.info("ℹ️ Tidak ada data jenis kelamin pada filter ini.")
    else:
        fig_gender = px.pie(
            gender_count,
            names='Jenis Kelamin',
            values='Jumlah',
            hole=0.45,
            title='Distribusi Jenis Kelamin',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_gender.update_traces(
            textinfo='percent+label',
            hovertemplate='%{label}: %{value} orang (%{percent})'
        )

        st.plotly_chart(fig_gender, use_container_width=True)

# Hitung jumlah dan persentase
jenjang_count = filtered_df['Jenjang pendidikan asal'].value_counts().reset_index()
jenjang_count.columns = ['Jenjang Pendidikan', 'Jumlah']

# Tambahkan kolom persentase manual
total_pendaftar = jenjang_count['Jumlah'].sum()
jenjang_count['Persentase'] = (jenjang_count['Jumlah'] / total_pendaftar * 100).round(1)
with col2:
    if jenjang_count.empty:
        st.info("ℹ️ Tidak ada data jenjang pendidikan pada filter ini.")
    else:
        fig_jenjang = px.bar(
            jenjang_count,
            x='Jenjang Pendidikan',
            y='Jumlah',
            # Tambahkan kolom Persentase ke custom_data agar bisa dipanggil di hovertemplate
            custom_data=['Persentase'],
            title='Distribusi Jenjang Pendidikan',
            color='Jumlah'
        )
        
        fig_jenjang.update_traces(
            textposition='none',
            # %{y} adalah jumlah orang, %{customdata[0]} adalah persentase yang kita hitung tadi
            hovertemplate='Jenjang: %{x}<br>Jumlah: %{y} orang<br>Persentase: %{customdata[0]}%'
        )
        
        fig_jenjang.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_jenjang, use_container_width=True)


st.divider()

# ==================================================
# ROW 2 – INSTANSI & SEMESTER
# ==================================================
col1, col2 = st.columns(2)

# --- BAGIAN INSTANSI ---
instansi_count = (
    filtered_df['Asal Instansi']
    .value_counts()
    .sort_values(ascending=True)
    .reset_index()
)
instansi_count.columns = ['Asal Instansi', 'Jumlah']

# Hitung Persentase Instansi
total_instansi = instansi_count['Jumlah'].sum()
instansi_count['Persentase'] = (instansi_count['Jumlah'] / total_instansi * 100).round(1)

with col1:
    if instansi_count.empty:
        st.info("ℹ️ Tidak ada data instansi pada filter ini.")
    else:
        fig_instansi = px.bar(
            instansi_count,
            x='Jumlah',
            y='Asal Instansi',
            orientation='h',
            custom_data=['Persentase'], # Tambahkan data persen
            title='Distribusi Asal Instansi',
            color='Jumlah'
        )
        fig_instansi.update_traces(
            hovertemplate='Instansi: %{y}<br>Jumlah: %{x} orang<br>Persentase: %{customdata[0]}%'
        )
        fig_instansi.update_layout(
            height=max(450, len(instansi_count) * 26),
            yaxis_title="",
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_instansi, use_container_width=True)


# --- BAGIAN SEMESTER ---
semester_count = (
    filtered_df[semester_col]
    .value_counts()
    .sort_index()
    .reset_index()
)
semester_count.columns = ['Semester', 'Jumlah']

# Hitung Persentase Semester
total_semester = semester_count['Jumlah'].sum()
semester_count['Persentase'] = (semester_count['Jumlah'] / total_semester * 100).round(1)

with col2:
    if semester_count.empty:
        st.info("ℹ️ Tidak ada data semester/angkatan pada filter ini.")
    else:
        fig_semester = px.bar(
            semester_count,
            x='Semester',
            y='Jumlah',
            custom_data=['Persentase'], # Tambahkan data persen
            title='Distribusi Semester / Tahun Angkatan',
            color='Jumlah'
        )
        fig_semester.update_traces(
            textposition='none',
            hovertemplate='Semester: %{x}<br>Jumlah: %{y} orang<br>Persentase: %{customdata[0]}%'
        )
        fig_semester.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_semester, use_container_width=True)

st.divider()

# ==================================================
# TREND
# ==================================================
trend = (
    filtered_df
    .groupby(filtered_df['Timestamp'].dt.date)
    .size()
    .reset_index(name='Jumlah')
)

if trend.empty:
    st.info("ℹ️ Tidak ada data tren pada rentang tanggal ini.")
else:
    # Hitung total untuk mendapatkan persentase harian
    total_pendaftar_trend = trend['Jumlah'].sum()
    trend['Persentase'] = (trend['Jumlah'] / total_pendaftar_trend * 100).round(1)

    fig_trend = px.line(
        trend,
        x='Timestamp',
        y='Jumlah',
        custom_data=['Persentase'], # Masukkan data persentase
        title='Tren Waktu Pendaftaran'
    )
    
    fig_trend.update_traces(
        mode='lines+markers',
        # Menampilkan tanggal, jumlah orang, dan persentase kontribusi hari tersebut
        hovertemplate='Tanggal: %{x}<br>Jumlah: %{y} orang<br>Kontribusi: %{customdata[0]}%'
    )
    
    fig_trend.update_layout(
        hovermode='x unified' # Opsional: memudahkan melihat data pada titik yang sejajar
    )
    
    st.plotly_chart(fig_trend, use_container_width=True)

# ==================================================
# INSIGHT
# ==================================================
semester_count = filtered_df[semester_col].value_counts()

if not semester_count.empty:
    semester_terbanyak = semester_count.idxmax()
    jumlah_semester_terbanyak = semester_count.max()
    persentase_semester = (jumlah_semester_terbanyak / total_pendaftar) * 100
else:
    semester_terbanyak = "-"
    jumlah_semester_terbanyak = 0
    persentase_semester = 0

st.subheader("📌 Insight Singkat")
st.caption("Insight diperbarui otomatis berdasarkan filter aktif.")

st.write(
    f"""
    - Total peserta yang dianalisis: **{total_pendaftar} orang**
    - Instansi terbanyak: **{instansi_terbanyak.title()}**
    - Hari pendaftaran terpadat: **{hari_terpadat}**
    - Semester dominan: **{semester_terbanyak}**
      (**{jumlah_semester_terbanyak} peserta / {persentase_semester:.1f}%**)
    """
)
