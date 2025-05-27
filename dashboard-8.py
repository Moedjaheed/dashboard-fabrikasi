
import streamlit as st
import pandas as pd
from datetime import datetime
from gsheets_utils import load_gsheet, update_gsheet

st.set_page_config(page_title='Dashboard Proyek Fabrikasi', page_icon='🛠️', layout="wide")
st.title('🛠️ Dashboard Skedul Proyek Fabrikasi Hidrolis')
st.info('Terhubung dengan Google Sheets untuk manajemen proyek tim fabrikasi.')

# KONFIGURASI GOOGLE SHEETS
sheet_id = "1JLb5wzQL5yT-8joGw53Wc_rDlzO1TaJeZDWCLtB1DoY"
worksheet_name = "Sheet1"
cred_path = "aldzama-dashboard-hidrolis-415739989ae4.json"

df, worksheet = load_gsheet(sheet_id, worksheet_name, cred_path)

today = datetime.now().date()
df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
df["Sisa Hari"] = df["Due Date"].apply(lambda x: (x.date() - today).days if pd.notnull(x) else None)

# Tambahkan kolom jika belum ada
if "Unique ID" not in df.columns:
    year_suffix = today.strftime("%y")
    df["Unique ID"] = [f"AZM/HDS/{year_suffix}-{str(i+1).zfill(3)}" for i in range(len(df))]

if "Urgensi" not in df.columns:
    df["Urgensi"] = "Sedang"

if "DataFrame" not in st.session_state:
    st.session_state["DataFrame"] = df
    st.session_state["change_log"] = []

st.subheader("📋 Tabel Proyek")
display_cols = ["Item", "Jumlah", "PIC", "Divisi", "Start", "Due Date", "Sisa Hari", "Unique ID"]
df_display = df[display_cols].copy()

# Gabung Urgensi untuk sorting
df_display["Urgensi"] = df["Urgensi"]
df_display = df_display.sort_values(by=["Urgensi", "Sisa Hari"], ascending=[True, True])

selected_index = st.data_editor(
    df_display[display_cols],
    use_container_width=True,
    hide_index=True,
    height=400,
    disabled=True,
    key="main_table"
)

# Tampilkan detail jika ada klik baris
if isinstance(selected_index, dict) and "edited_rows" in selected_index and selected_index["edited_rows"]:
    idx = list(selected_index["edited_rows"].keys())[0]
    selected_id = df_display.iloc[idx]["Unique ID"]
    detail = df[df["Unique ID"] == selected_id].iloc[0]

    st.markdown("### 🔍 Detail Proyek Terpilih")
    st.markdown(f'''
**🆔 ID:** {detail["Unique ID"]}  
**📌 Item:** {detail["Item"]}  
**📦 Jumlah:** {detail["Jumlah"]}  
**👤 PIC:** {detail["PIC"]}  
**🏢 Divisi:** {detail["Divisi"]}  
**📅 Mulai:** {detail["Start"].strftime('%d %b %Y') if pd.notnull(detail["Start"]) else '-'}  
**⏳ Due Date:** {detail["Due Date"].strftime('%d %b %Y') if pd.notnull(detail["Due Date"]) else '-'}  
**🗓️ Sisa Hari:** {detail["Sisa Hari"]} hari  
**🚦 Urgensi:** {detail["Urgensi"]}  
**📍 Status:** {detail["Status"]}  
**📝 Catatan:** {detail["Remarks"] if pd.notnull(detail["Remarks"]) else '-'}
''')

if st.button("💾 Simpan ke Google Sheets"):
    update_gsheet(worksheet, st.session_state["DataFrame"])
    st.success("✅ Data berhasil disimpan ke Google Sheets!")
