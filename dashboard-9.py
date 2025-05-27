
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
today = datetime.now().date()
df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")

# Safe date subtraction
df["Sisa Hari"] = df["Due Date"].apply(lambda x: (x.date() - today).days if pd.notnull(x) else None)

# Tambahkan Unique ID jika belum ada
if "Unique ID" not in df.columns:
    year_suffix = today.strftime("%y")
    df["Unique ID"] = [f"AZM/HDS/{year_suffix}-{str(i+1).zfill(3)}" for i in range(len(df))]

# Inisialisasi session state
if "DataFrame" not in st.session_state:
    st.session_state["DataFrame"] = df
    st.session_state["change_log"] = []

tabs = st.tabs(["📋 Input Baru", "📊 Status & Detail Proyek"])

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
            st.session_state["change_log"].append(f"[{datetime.now()}] Proyek ditambahkan: {item}")
            st.success("✅ Proyek berhasil ditambahkan!")

with tabs[1]:
    df = st.session_state.DataFrame
    df_sorted = df.sort_values(by=["Urgensi", "Sisa Hari"], ascending=[True, True])

    st.subheader("📋 Daftar Proyek (klik untuk lihat detail)")

    # Kolom untuk ditampilkan di dashboard awal
    display_cols = ["Item", "Jumlah", "PIC", "Divisi", "Start", "Due Date", "Sisa Hari", "Unique ID"]
    df_display = df_sorted[display_cols]

    selected_id = st.selectbox(
        "Pilih Proyek berdasarkan Unique ID:",
        options=df_display["Unique ID"],
        format_func=lambda x: df_display[df_display["Unique ID"] == x]["Unique ID"].values[0]
    )

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Detail proyek
    with st.expander("🔍 Detail Proyek Terpilih"):
        detail = df[df["Unique ID"] == selected_id].iloc[0]
        st.markdown(
            f"""
**🆔 ID:** {detail['Unique ID']}  
**📌 Item:** {detail['Item']}  
**📦 Jumlah:** {detail['Jumlah']}  
**👤 PIC:** {detail['PIC']}  
**🏢 Divisi:** {detail['Divisi']}  
**📅 Mulai:** {detail['Start'].strftime('%d %b %Y') if pd.notnull(detail['Start']) else '-'}  
**⏳ Due Date:** {detail['Due Date'].strftime('%d %b %Y') if pd.notnull(detail['Due Date']) else '-'}  
**🗓️ Sisa Hari:** {detail['Sisa Hari']} hari  
**🚦 Urgensi:** {detail['Urgensi']}  
**📍 Status:** {detail['Status']}  
**📝 Catatan:** {detail['Remarks'] if pd.notnull(detail['Remarks']) else '-'}
""")

    st.subheader("🕓 Riwayat Perubahan")
    for log in reversed(st.session_state["change_log"][-10:]):
        st.text(log)

    if st.button("💾 Simpan ke Google Sheets"):
        update_gsheet(worksheet, st.session_state.DataFrame)
        st.success("✅ Data berhasil disimpan ke Google Sheets!")

        
    # ------------------ DETAIL LANJUTAN DAN GRAFIK ---------------------
    st.markdown("---")
    st.subheader("📊 Visualisasi dan Detail Lanjutan")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### 📈 Distribusi Proyek per Divisi")
        div_count = df["Divisi"].value_counts().reset_index()
        div_count.columns = ["Divisi", "Jumlah"]
        st.bar_chart(data=div_count.set_index("Divisi"))

    with col2:
        st.markdown("#### 🎯 Ringkasan Urgensi")
        urgency_count = df["Urgensi"].value_counts().reset_index()
        urgency_count.columns = ["Urgensi", "Jumlah"]
        st.dataframe(urgency_count, use_container_width=True, hide_index=True)

    # Timeline projek berdasarkan Due Date
    st.markdown("#### 🗓️ Timeline Proyek")
    df_timeline = df[["Item", "PIC", "Start", "Due Date"]].dropna()
    df_timeline["Durasi"] = (df_timeline["Due Date"] - df_timeline["Start"]).dt.days

    if not df_timeline.empty:
        import altair as alt
        timeline_chart = alt.Chart(df_timeline).mark_bar().encode(
            x='Start:T',
            x2='Due Date:T',
            y=alt.Y('Item:N', sort="-x"),
            color='PIC:N',
            tooltip=['Item', 'PIC', 'Start', 'Due Date', 'Durasi']
        ).properties(height=400)
        st.altair_chart(timeline_chart, use_container_width=True)
    else:
        st.info("Tidak ada data proyek dengan tanggal lengkap untuk ditampilkan dalam timeline.")


