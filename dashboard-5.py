
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from collections import Counter
from gsheets_utils import load_gsheet, update_gsheet

st.set_page_config(page_title='Dashboard Proyek Fabrikasi', page_icon='🛠️', layout="wide")
st.title('🛠️ Dashboard Skedul Proyek Fabrikasi Hidrolis')
st.info('Terhubung dengan Google Sheets untuk manajemen proyek tim fabrikasi.')

# KONFIGURASI GOOGLE SHEETS
sheet_id = "1JLb5wzQL5yT-8joGw53Wc_rDlzO1TaJeZDWCLtB1DoY"
worksheet_name = "Sheet1"
cred_path = "aldzama-dashboard-hidrolis-415739989ae4.json"

# Load data dari Google Sheet
df, worksheet = load_gsheet(sheet_id, worksheet_name, cred_path)

# Data preprocessing
df["Start"] = pd.to_datetime(df["Start"])
df["Due Date"] = pd.to_datetime(df["Due Date"])
today = datetime.now().date()
df["Sisa Hari"] = (df["Due Date"].dt.date - today).apply(lambda x: x.days)

if "Unique ID" not in df.columns:
    year_suffix = today.strftime("%y")
    df["Unique ID"] = [f"AZM/HDS/{year_suffix}-{str(i+1).zfill(3)}" for i in range(len(df))]

if "DataFrame" not in st.session_state:
    st.session_state["DataFrame"] = df
    st.session_state["change_log"] = []

tabs = st.tabs(["📋 Input Baru", "📊 Status & Analitik"])

with tabs[0]:
    with st.form("new_entry"):
        st.subheader("➕ Tambah Proyek Baru")
        item = st.text_input("Item")
        jumlah = st.text_input("Jumlah")
        pic = st.text_input("PIC")
        divisi = st.text_input("Divisi")
        start = st.date_input("Start Date")
        due = st.date_input("Due Date")
        urgensi = st.selectbox("Urgensi", ["Tinggi", "Sedang", "Rendah"])
        status = st.selectbox("Status", ["Open", "In Progress", "Selesai"])
        remarks = st.text_area("Keterangan")

        submitted = st.form_submit_button("Tambah Proyek")
        if submitted:
            year_suffix = today.strftime("%y")
            new_row = pd.DataFrame([{
                "Unique ID": f"AZM/HDS/{year_suffix}-{str(len(st.session_state.DataFrame)+1).zfill(3)}",
                "Item": item,
                "Jumlah": jumlah,
                "PIC": pic,
                "Divisi": divisi,
                "Start": start,
                "Due Date": due,
                "Sisa Hari": (due - today).days,
                "Urgensi": urgensi,
                "Status": status,
                "Remarks": remarks
            }])
            st.session_state.DataFrame = pd.concat([st.session_state.DataFrame, new_row], ignore_index=True)
            st.session_state.change_log.append(f"[{datetime.now()}] Proyek ditambahkan: {item}")
            st.success("✅ Proyek berhasil ditambahkan!")

with tabs[1]:
    df = st.session_state.DataFrame
    df_sorted = df.sort_values(by=["Urgensi", "Sisa Hari"], ascending=[True, True])

    overdue_df = df_sorted[df_sorted["Sisa Hari"] < 0]
    if not overdue_df.empty:
        st.error(f"⚠️ Terdapat {len(overdue_df)} proyek yang telah melewati deadline!")

    st.markdown("📝 Edit Status, Urgensi, atau Informasi Lainnya:")
    edited_df = st.data_editor(
        df_sorted,
        use_container_width=True,
        num_rows="dynamic",
        height=300,
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Selesai"]),
            "Urgensi": st.column_config.SelectboxColumn("Urgensi", options=["Tinggi", "Sedang", "Rendah"]),
        }
    )
    if not edited_df.equals(st.session_state.DataFrame):
        st.session_state.change_log.append(f"[{datetime.now()}] Data diedit oleh user")
    st.session_state.DataFrame = edited_df

    st.subheader("📈 Ringkasan Proyek")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Jumlah Proyek", len(df))
        overdue = df[df["Sisa Hari"] < 0]
        st.metric("Overdue", len(overdue), delta=None)
    with col2:
        open_projects = df[df["Status"] == "Open"]
        in_progress = df[df["Status"] == "In Progress"]
        done = df[df["Status"] == "Selesai"]
        st.metric("Proyek Aktif", len(open_projects) + len(in_progress))
        st.metric("Selesai", len(done))
    with col3:
        durations = (df["Due Date"] - df["Start"]).dt.days
        st.metric("Rata-rata Durasi Proyek", f"{durations.mean():.1f} hari")

    st.subheader("🏅 Leaderboard PIC")
    leaderboard = df["PIC"].value_counts().head(5).reset_index()
    leaderboard.columns = ["PIC", "Jumlah Proyek"]
    st.dataframe(leaderboard, use_container_width=True, hide_index=True)

    st.subheader("🕓 Riwayat Perubahan")
    for log in reversed(st.session_state.change_log[-10:]):
        st.text(log)

    if st.button("💾 Simpan ke Google Sheets"):
        update_gsheet(worksheet, st.session_state.DataFrame)
        st.success("✅ Data berhasil disimpan ke Google Sheets!")
