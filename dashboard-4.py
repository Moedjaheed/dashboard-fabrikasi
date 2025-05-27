
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from collections import Counter

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

    df = df[["Unique ID", "Item", "Jumlah", "PIC", "Divisi", "Start", "Due Date", "Sisa Hari", "Urgensi", "Status", "Remarks"]]

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
        df["Start"] = pd.to_datetime(df["Start"])
        df["Due Date"] = pd.to_datetime(df["Due Date"])

        st.subheader("📊 Status Proyek")

        # Filter & sorting
        df_sorted = df.sort_values(by=["Urgensi", "Sisa Hari"], ascending=[True, True])

        # Highlight overdue
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

        # Ringkasan
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

        # Leaderboard PIC
        st.subheader("🏅 Leaderboard PIC")
        leaderboard = df["PIC"].value_counts().head(5).reset_index()
        leaderboard.columns = ["PIC", "Jumlah Proyek"]
        st.dataframe(leaderboard, use_container_width=True, hide_index=True)

        # Log Perubahan
        st.subheader("🕓 Riwayat Perubahan")
        for log in reversed(st.session_state.change_log[-10:]):
            st.text(log)

        # Export
        st.download_button(
            "⬇️ Unduh Data sebagai Excel",
            data=edited_df.to_csv(index=False).encode("utf-8"),
            file_name="rekap_proyek_fabrikasi.csv",
            mime="text/csv"
        )

        st.info("🔄 Untuk integrasi dengan Google Sheets atau database, tambahkan kredensial dan autentikasi secara aman.")