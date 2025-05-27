import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dashboard Proyek AZM", layout="wide")

st.title("📊 Dashboard Skedul Proyek Tim Fabrikasi Hidrolis")

uploaded_file = st.file_uploader("📤 Upload file Excel", type=["xlsx"])

if uploaded_file:
    sheet_name = "Skedul (2)"
    df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name)

    # Ambil data mulai baris ke-6
    df = df_raw.iloc[6:, [1, 2, 3, 4, 6, 7, 8]].copy()
    df.columns = ["Item", "Jumlah", "PIC", "Divisi", "Start", "Due Date", "Remarks"]
    df = df[df["Item"].notna()].reset_index(drop=True)

    # Hitung Sisa Hari
    today = datetime.now().date()
    df["Due Date"] = pd.to_datetime(df["Due Date"]).dt.date
    df["Sisa Hari"] = (df["Due Date"] - today).apply(lambda x: x.days)

    # Unique ID
    year_suffix = today.strftime("%y")
    df["Unique ID"] = [f"AZM/HDS/{year_suffix}-{str(i+1).zfill(3)}" for i in range(len(df))]

    # Tambahkan kolom Urgensi (default kosong, bisa diedit)
    df["Urgensi"] = ""

    # Tampilkan data
    st.subheader("📋 Tabel Proyek")
    edited_df = st.data_editor(
        df[["Unique ID", "Item", "Jumlah", "PIC", "Divisi", "Start", "Due Date", "Sisa Hari", "Urgensi"]],
        use_container_width=True,
        num_rows="dynamic",
        key="editable_table"
    )

    # Unduh hasil
    st.markdown("---")
    st.subheader("📥 Ekspor Hasil")
    def convert_df_to_excel(dataframe):
        output = pd.ExcelWriter("output.xlsx", engine="xlsxwriter")
        dataframe.to_excel(output, index=False, sheet_name="Rekap")
        output.close()
        return open("output.xlsx", "rb").read()

    st.download_button(
        label="💾 Unduh sebagai Excel",
        data=convert_df_to_excel(edited_df),
        file_name="rekap_proyek.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Silakan unggah file Excel terlebih dahulu.")
