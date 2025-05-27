import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

st.set_page_config(page_title='Dashboard Proyek Fabrikasi', page_icon='🛠️', layout="wide")
st.title('🛠️ Dashboard Skedul Proyek Fabrikasi Hidrolis')
st.info('Unggah file Excel untuk melihat, mengedit, dan menganalisis progres proyek tim fabrikasi.')

uploaded_file = st.file_uploader("📤 Upload file Excel", type=["xlsx"])

if uploaded_file:
    sheet_name = "Skedul (2)"
    df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name)

    df = df_raw.iloc[6:, [1, 2, 3, 4, 6, 7, 8]].copy()
    df.columns = ["Item", "Jumlah", "PIC", "Divisi", "Start", "Due Date", "Remarks"]
    df = df[df["Item"].notna()].reset_index(drop=True)

    today = datetime.now().date()
    df["Due Date"] = pd.to_datetime(df["Due Date"]).dt.date
    df["Sisa Hari"] = (df["Due Date"] - today).apply(lambda x: x.days)
    year_suffix = today.strftime("%y")
    df["Unique ID"] = [f"AZM/HDS/{year_suffix}-{str(i+1).zfill(3)}" for i in range(len(df))]

    if "Urgensi" not in df.columns:
        df["Urgensi"] = ""

    if "Status" not in df.columns:
        df["Status"] = "Open"

    if "DataFrame" not in st.session_state:
        st.session_state["DataFrame"] = df

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
                new_row = pd.DataFrame([{
                    "Item": item,
                    "Jumlah": jumlah,
                    "PIC": pic,
                    "Divisi": divisi,
                    "Start": start,
                    "Due Date": due,
                    "Remarks": remarks,
                    "Sisa Hari": (due - today).days,
                    "Unique ID": f"AZM/HDS/{year_suffix}-{str(len(st.session_state.DataFrame)+1).zfill(3)}",
                    "Urgensi": urgensi,
                    "Status": status
                }])
                st.session_state.DataFrame = pd.concat([st.session_state.DataFrame, new_row], ignore_index=True)
                st.success("✅ Proyek berhasil ditambahkan!")

    with tabs[1]:
        st.subheader("📊 Status Proyek")
        st.markdown("📝 Edit Status, Urgensi, atau Informasi Lainnya:")

        edited_df = st.data_editor(
            st.session_state.DataFrame,
            use_container_width=True,
            num_rows="dynamic",
            height=250,
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Selesai"]),
                "Urgensi": st.column_config.SelectboxColumn("Urgensi", options=["Tinggi", "Sedang", "Rendah"]),
            }
        )

        st.session_state.DataFrame = edited_df

        st.markdown("📈 **Statistik Visual**")
        col1, col2 = st.columns(2)

        with col1:
            status_plot = alt.Chart(edited_df).mark_bar().encode(
                x="Status:N",
                y="count():Q",
                color="Status:N"
            ).properties(title="Distribusi Status Proyek", height=300)
            st.altair_chart(status_plot, use_container_width=True)

        with col2:
            urgensi_plot = alt.Chart(edited_df).mark_arc().encode(
                theta="count():Q",
                color="Urgensi:N"
            ).properties(title="Distribusi Urgensi", height=300)
            st.altair_chart(urgensi_plot, use_container_width=True)

        st.download_button(
            "⬇️ Unduh Data sebagai Excel",
            data=edited_df.to_csv(index=False).encode("utf-8"),
            file_name="rekap_proyek_fabrikasi.csv",
            mime="text/csv"
        )
else:
    st.warning("Mohon unggah file Excel terlebih dahulu untuk mulai menggunakan dashboard.")

