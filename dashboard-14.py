
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from gsheets_utils import load_gsheet, update_gsheet

st.set_page_config(page_title='Dashboard Proyek Fabrikasi', page_icon='🛠️', layout="wide")
st.title('🛠️ Dashboard Skedul Proyek Fabrikasi Hidrolis')
st.info('Terhubung dengan Google Sheets untuk manajemen proyek tim fabrikasi.')

sheet_id = "1JLb5wzQL5yT-8joGw53Wc_rDlzO1TaJeZDWCLtB1DoY"
worksheet_name = "Sheet1"
cred_path = "aldzama-dashboard-hidrolis-415739989ae4.json"

df, worksheet = load_gsheet(sheet_id, worksheet_name, cred_path)

today = datetime.now().date()
df["Start"] = pd.to_datetime(df["Start"], errors="coerce", dayfirst=True)
df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce", dayfirst=True)
df["Sisa Hari"] = df["Due Date"].apply(lambda x: (x.date() - today).days if pd.notnull(x) else None)

if "Unique ID" not in df.columns:
    year_suffix = today.strftime("%y")
    df["Unique ID"] = [f"AZM/HDS/{year_suffix}-{str(i+1).zfill(3)}" for i in range(len(df))]

if "Urgensi" not in df.columns:
    df["Urgensi"] = "Sedang"
if "Tanggal Diminta" not in df.columns:
    df["Tanggal Diminta"] = pd.to_datetime("today").normalize()
if "Diminta Oleh" not in df.columns:
    df["Diminta Oleh"] = "-"

if "DataFrame" not in st.session_state:
    st.session_state["DataFrame"] = df
    st.session_state["change_log"] = []

tabs = st.tabs(["📋 Input Baru", "📊 Status Proyek", "🔍 Detail Proyek", "📈 Visualisasi"])

with tabs[0]:
    with st.form("new_entry"):
        st.subheader("➕ Tambah Proyek Baru")
        item = st.text_input("Item")
        jumlah = st.text_input("Jumlah")
        pic = st.text_input("PIC")
        diminta_oleh = st.text_input("Diminta Oleh")
        divisi = st.text_input("Divisi")
        tanggal_diminta = st.date_input("Tanggal Diminta", today)
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
                "Diminta Oleh": diminta_oleh,
                "Tanggal Diminta": tanggal_diminta,
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
    df_sorted["Start"] = pd.to_datetime(df_sorted["Start"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
    df_sorted["Due Date"] = pd.to_datetime(df_sorted["Due Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
    df_sorted["Tanggal Diminta"] = pd.to_datetime(df_sorted["Tanggal Diminta"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")

    st.subheader("📋 Daftar Proyek")
    display_cols = ["Unique ID", "Item", "PIC", "Diminta Oleh", "Tanggal Diminta", "Start", "Due Date", "Sisa Hari"]
    st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)

    if st.button("💾 Simpan ke Google Sheets"):
        update_gsheet(worksheet, st.session_state.DataFrame)
        st.success("✅ Data berhasil disimpan ke Google Sheets!")

with tabs[2]:
    st.subheader("🔍 Detail Proyek")
    df = st.session_state.DataFrame
    selected_id = st.selectbox("Pilih Proyek berdasarkan Unique ID:", options=df["Unique ID"].tolist())

    detail = df[df["Unique ID"] == selected_id].iloc[0]
    st.markdown(f'''
**🆔 ID:** {detail["Unique ID"]}  
**📌 Item:** {detail["Item"]}  
**📦 Jumlah:** {detail["Jumlah"]}  
**👤 PIC:** {detail["PIC"]}  
**👥 Diminta Oleh:** {detail["Diminta Oleh"]}  
**📅 Tanggal Diminta:** {detail["Tanggal Diminta"].strftime("%d %b %Y") if pd.notnull(detail["Tanggal Diminta"]) else '-'}  
**🏢 Divisi:** {detail["Divisi"]}  
**📅 Mulai:** {detail["Start"].strftime("%d %b %Y") if pd.notnull(detail["Start"]) else '-'}  
**⏳ Due Date:** {detail["Due Date"].strftime("%d %b %Y") if pd.notnull(detail["Due Date"]) else '-'}  
**🗓️ Sisa Hari:** {detail["Sisa Hari"]} hari  
**🚦 Urgensi:** {detail["Urgensi"]}  
**📍 Status:** {detail["Status"]}  
**📝 Catatan:** {detail["Remarks"] if pd.notnull(detail["Remarks"]) else '-'}
''')



with tabs[3]:
    st.subheader("📊 Visualisasi Proyek")
    df_vis = st.session_state.DataFrame.copy()
    df_vis["Start"] = pd.to_datetime(df_vis["Start"], errors="coerce", dayfirst=True)
    df_vis["Due Date"] = pd.to_datetime(df_vis["Due Date"], errors="coerce", dayfirst=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### 📈 Distribusi Proyek per Divisi")
        div_count = df_vis["Divisi"].value_counts().reset_index()
        div_count.columns = ["Divisi", "Jumlah"]
        st.bar_chart(data=div_count.set_index("Divisi"))

    with col2:
        st.markdown("#### 📈 Distribusi Proyek per PIC")
        pic_count = df_vis["PIC"].value_counts().reset_index()
        pic_count.columns = ["PIC", "Jumlah"]
        st.bar_chart(data=pic_count.set_index("PIC"))

    st.markdown("#### 📊 Ringkasan Status")
    status_count = df_vis["Status"].value_counts().reset_index()
    status_count.columns = ["Status", "Jumlah"]
    st.bar_chart(data=status_count.set_index("Status"))

    st.markdown("#### 🗓️ Timeline Proyek (3 Bulan ke Depan)")
    cutoff_date = today + timedelta(days=90)
    df_timeline = df_vis[(df_vis["Start"].notna()) & (df_vis["Due Date"].notna())]
    df_timeline = df_timeline[df_timeline["Start"].dt.date <= cutoff_date]

    df_timeline["Durasi"] = (df_timeline["Due Date"] - df_timeline["Start"]).dt.days
    df_timeline["Week"] = df_timeline["Start"].dt.to_period("W").dt.start_time

    if not df_timeline.empty:
        timeline_chart = alt.Chart(df_timeline).mark_bar().encode(
            x='Week:T',                     # Per minggu
            x2='Due Date:T',
            y=alt.Y('Item:N', sort='-x'),
            color='PIC:N',
            tooltip=['Item', 'PIC', 'Start', 'Due Date', 'Durasi']
        ).properties(height=450)

        st.altair_chart(timeline_chart, use_container_width=True)
    else:
        st.info("Tidak ada proyek yang dimulai dalam 3 bulan ke depan.")

