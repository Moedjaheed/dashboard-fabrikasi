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
df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce", dayfirst=True)
df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce", dayfirst=True)
df["Request Date"] = pd.to_datetime(df["Request Date"], errors="coerce", dayfirst=True)
df["Sisa Hari"] = df["Due Date"].apply(lambda x: (x.date() - today).days if pd.notnull(x) else None)

if "DataFrame" not in st.session_state:
    st.session_state["DataFrame"] = df
    st.session_state["change_log"] = []

total_projects = len(df)
active_projects = df[df["Project Status"].isin(["Open", "In Progress"])]
overdue_projects = df[df["Sisa Hari"] < 0]

avg_duration = (df["Due Date"] - df["Start Date"]).dt.days.mean()

st.subheader("📊 Ringkasan Proyek")

col1, col2, col3, col4 = st.columns(4)
col1.metric("📌 Total Proyek", total_projects)
col2.metric("🛠 Aktif Saat Ini", len(active_projects))
col3.metric("⚠️ Overdue", len(overdue_projects))
col4.metric("📉 Rata-rata Durasi", f"{avg_duration:.1f} hari" if not pd.isna(avg_duration) else "-")


tabs = st.tabs(["📊 Status Proyek", "📋 Input Baru", "🔍 Detail Proyek"])

with tabs[1]:
    with st.form("new_entry"):
        st.subheader("➕ Tambah Proyek Baru")
        item = st.text_input("Item")
        quantity = st.text_input("Quantity")
        requested_by = st.text_input("Requested By")
        request_date = st.date_input("Request Date", today)
        pic = st.text_input("PIC")
        division = st.text_input("Division")
        start = st.date_input("Start Date")
        due = st.date_input("Due Date")
        priority = st.selectbox("Priority Level", ["Tinggi", "Sedang", "Rendah"])
        status = st.selectbox("Project Status", ["Open", "In Progress", "Finish"])
        remarks = st.text_area("Remarks")

        submitted = st.form_submit_button("Tambah Proyek")
        if submitted:
            year_suffix = today.strftime("%y")
            new_row = pd.DataFrame([{
                "WO Number": f"AZM/HDS/{year_suffix}-{str(len(st.session_state.DataFrame)+1).zfill(3)}",
                "Item": item,
                "Quantity": quantity,
                "Requested By": requested_by,
                "Request Date": request_date,
                "PIC": pic,
                "Division": division,
                "Start Date": start,
                "Due Date": due,
                "Priority Level": priority,
                "Project Status": status,
                "Remarks": remarks,
                "Sisa Hari": (due - today).days
            }])
            st.session_state.DataFrame = pd.concat([st.session_state.DataFrame, new_row], ignore_index=True)
            st.session_state["change_log"].append(f"[{datetime.now()}] Proyek ditambahkan: {item}")
            st.success("✅ Proyek berhasil ditambahkan!")

with tabs[2]:
    st.subheader("🔍 Detail Proyek")
    df = st.session_state.DataFrame
    selected_id = st.selectbox("Pilih Proyek berdasarkan WO Number:", options=df["WO Number"].tolist())

    detail = df[df["WO Number"] == selected_id].iloc[0]
    st.markdown(f'''
**🆔 ID:** {detail["WO Number"]}  
**📌 Item:** {detail["Item"]}  
**📦 Quantity:** {detail["Quantity"]}  
**👥 Requested By:** {detail["Requested By"]}  
**📅 Request Date:** {detail["Request Date"].strftime("%d %B %Y") if pd.notnull(detail["Request Date"]) else '-'}  
**👤 PIC:** {detail["PIC"]}  
**🏢 Division:** {detail["Division"]}  
**📅 Start:** {detail["Start Date"].strftime("%d %B %Y") if pd.notnull(detail["Start Date"]) else '-'}  
**⏳ Due Date:** {detail["Due Date"].strftime("%d %B %Y") if pd.notnull(detail["Due Date"]) else '-'}  
**🗓️ Sisa Hari:** {detail["Sisa Hari"]} days  
**🚦 Priority:** {detail["Priority Level"]}  
**📍 Status:** {detail["Project Status"]}  
**📝 Notes:** {detail["Remarks"] if pd.notnull(detail["Remarks"]) else '-'}
''')

with tabs[0]:
    st.subheader("📋 Daftar Proyek")
    df_vis = st.session_state.DataFrame.copy()
    df_vis["Start Date"] = pd.to_datetime(df_vis["Start Date"], errors="coerce", dayfirst=True)
    df_vis["Due Date"] = pd.to_datetime(df_vis["Due Date"], errors="coerce", dayfirst=True)

    st.markdown("#### 📋 Auto-scroll Daftar Proyek (Looping & Prioritas Berwarna)")

    df_scroll = df[["WO Number", "Item", "PIC", "Priority Level", "Start Date", "Due Date", "Sisa Hari"]].copy()
    df_scroll = df_scroll.reset_index(drop=True)

    def row_class(priority):
        if priority == "Tinggi":
            return "high-priority"
        elif priority == "Sedang":
            return "medium-priority"
        elif priority == "Rendah":
            return "low-priority"
        return ""

    rows_html = ""
    for _, row in df_scroll.iterrows():
        priority_class = row_class(row["Priority Level"])
        row_html = f"""
        <tr class="{priority_class}">
            <td>{row["WO Number"]}</td>
            <td>{row["Item"]}</td>
            <td>{row["PIC"]}</td>
            <td>{row["Priority Level"]}</td>
            <td>{row["Start Date"].strftime('%d %b %Y') if pd.notnull(row["Start Date"]) else '-'}</td>
            <td>{row["Due Date"].strftime('%d %b %Y') if pd.notnull(row["Due Date"]) else '-'}</td>
            <td>{row["Sisa Hari"]}</td>
        </tr>
        """
        rows_html += row_html
    import streamlit.components.v1 as components

    # Sort dataframe berdasarkan urutan prioritas
    priority_order = {"Tinggi": 0, "Sedang": 1, "Rendah": 2}
    df_scroll = df.copy()
    df_scroll["Priority_Sort"] = df_scroll["Priority Level"].map(priority_order)
    df_scroll = df_scroll.sort_values("Priority_Sort")

    # Konversi tanggal ke string agar ditampilkan rapi
    for col in ["Start Date", "Due Date"]:
        df_scroll[col] = df_scroll[col].dt.strftime("%d %b %Y")

    # HTML + CSS scroll dan warna
    scroll_style = """
    <style>
    .scroll-table-container {
    height: 300px;
    overflow-y: hidden;
    position: relative;
    }
    .scroll-table {
    width: 100%;
    border-collapse: collapse;
    animation: scroll-up 20s linear infinite;
    }
    .scroll-table thead {
    position: sticky;
    top: 0;
    background-color: #1a1a1a;
    z-index: 1;
    }
    .scroll-table th, .scroll-table td {
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid #444;
    font-size: 14px;
    }
    .high-priority { background-color: #ff4d4d; color: white; }
    .medium-priority { background-color: #ffa500; color: black; }
    .low-priority { background-color: #87ceeb; color: black; }

    @keyframes scroll-up {
    0% { transform: translateY(0); }
    100% { transform: translateY(-100%); }
    }
    </style>
    """

    # Bangun HTML tabel
    table_html = """
    <h4>📜 Auto-scroll Daftar Proyek (Header Freeze + Prioritas Berwarna)</h4>
    <div class="scroll-table-container">
    <table class="scroll-table">
    <thead>
        <tr>
        <th>WO Number</th>
        <th>Item</th>
        <th>PIC</th>
        <th>Priority</th>
        <th>Start Date</th>
        <th>Due Date</th>
        <th>Sisa Hari</th>
        </tr>
    </thead>
    <tbody>
    """

    for _, row in df_scroll.iterrows():
        priority_class = {
            "Tinggi": "high-priority",
            "Sedang": "medium-priority",
            "Rendah": "low-priority"
        }.get(row["Priority Level"], "")
        
        table_html += f"""
        <tr class="{priority_class}">
        <td>{row['WO Number']}</td>
        <td>{row['Item']}</td>
        <td>{row['PIC']}</td>
        <td>{row['Priority Level']}</td>
        <td>{row['Start Date']}</td>
        <td>{row['Due Date']}</td>
        <td>{row['Sisa Hari']}</td>
        </tr>
        """

    table_html += """
    </tbody>
    </table>
    </div>
    """

    # Render tabel
    components.html(scroll_style + table_html, height=360, scrolling=False)

    # Gabungkan HTML dan CSS
    full_html = scroll_style + table_html

    components.html(full_html, height=350, scrolling=False)



    df = st.session_state.DataFrame
    df_sorted = df.sort_values(by=["Priority Level", "Sisa Hari"], ascending=[True, True])
    df_sorted["Start Date"] = pd.to_datetime(df_sorted["Start Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
    df_sorted["Due Date"] = pd.to_datetime(df_sorted["Due Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
    df_sorted["Request Date"] = pd.to_datetime(df_sorted["Request Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")

    display_cols = ["WO Number", "Item", "PIC", "Requested By", "Request Date", "Start Date", "Due Date", "Sisa Hari"]
    st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)

    if st.button("💾 Simpan ke Google Sheets"):
        update_gsheet(worksheet, st.session_state.DataFrame)
        st.success("✅ Data berhasil disimpan ke Google Sheets!")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### 📈 Distribusi Proyek per Division")
        div_count = df_vis["Division"].value_counts().reset_index()
        div_count.columns = ["Division", "Jumlah"]
        st.bar_chart(data=div_count.set_index("Division"))

    with col2:
        st.markdown("#### 📈 Distribusi Proyek per PIC")
        pic_count = df_vis["PIC"].value_counts().reset_index()
        pic_count.columns = ["PIC", "Jumlah"]
        st.bar_chart(data=pic_count.set_index("PIC"))

    st.markdown("#### 📊 Ringkasan Status")
    status_count = df_vis["Project Status"].value_counts().reset_index()
    status_count.columns = ["Project Status", "Jumlah"]
    st.bar_chart(data=status_count.set_index("Project Status"))

    st.markdown("#### 🗓️ Timeline Proyek (3 Bulan ke Depan)")
    cutoff_date = today + timedelta(days=90)
    df_timeline = df_vis[(df_vis["Start Date"].notna()) & (df_vis["Due Date"].notna())]
    df_timeline = df_timeline[df_timeline["Start Date"].dt.date <= cutoff_date]

    df_timeline["Durasi"] = (df_timeline["Due Date"] - df_timeline["Start Date"]).dt.days
    df_timeline["Week"] = df_timeline["Start Date"].dt.to_period("W").dt.start_time

    if not df_timeline.empty:
        timeline_chart = alt.Chart(df_timeline).mark_bar().encode(
            x='Week:T',
            x2='Due Date:T',
            y=alt.Y('Item:N', sort='-x'),
            color='PIC:N',
            tooltip=['Item', 'PIC', 'Start Date', 'Due Date', 'Durasi']
        ).properties(height=450)

        st.altair_chart(timeline_chart, use_container_width=True)
    else:
        st.info("Tidak ada proyek yang dimulai dalam 3 bulan ke depan.")

    # Donut Chart: Distribusi Proyek per Status
    status_counts = df["Project Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Jumlah"]

    st.altair_chart(
        alt.Chart(status_counts)
        .mark_arc(innerRadius=50)
        .encode(
            theta="Jumlah:Q",
            color="Status:N",
            tooltip=["Status", "Jumlah"]
        )
        .properties(title="📊 Distribusi Proyek per Status"),
        use_container_width=True
    )

    # Donut Chart: Distribusi Prioritas
    priority_counts = df["Priority Level"].value_counts().reset_index()
    priority_counts.columns = ["Priority", "Jumlah"]

    st.altair_chart(
        alt.Chart(priority_counts)
        .mark_arc(innerRadius=50)
        .encode(
            theta="Jumlah:Q",
            color="Priority:N",
            tooltip=["Priority", "Jumlah"]
        )
        .properties(title="🎯 Distribusi Prioritas Proyek"),
        use_container_width=True
    )

    # Donut Chart: Distribusi per PIC
    pic_counts = df["PIC"].value_counts().reset_index()
    pic_counts.columns = ["PIC", "Jumlah"]

    st.altair_chart(
        alt.Chart(pic_counts)
        .mark_arc(innerRadius=50)
        .encode(
            theta="Jumlah:Q",
            color="PIC:N",
            tooltip=["PIC", "Jumlah"]
        )
        .properties(title="👤 Distribusi Proyek per PIC"),
        use_container_width=True
    )

    st.markdown("#### 📊 Jumlah Proyek per Divisi berdasarkan Status")

    div_status_df = (
        df.groupby(["Division", "Project Status"])
        .size()
        .reset_index(name="Jumlah")
    )

    chart_div_status = alt.Chart(div_status_df).mark_bar().encode(
        x=alt.X("Division:N", title="Division"),
        y=alt.Y("Jumlah:Q"),
        color=alt.Color("Project Status:N"),
        column=alt.Column("Project Status:N", spacing=10),
        tooltip=["Division", "Project Status", "Jumlah"]
    ).properties(height=300)

    st.altair_chart(chart_div_status, use_container_width=True)

    st.markdown("#### 📊 Jumlah Proyek per PIC berdasarkan Prioritas")

    pic_priority_df = (
        df.groupby(["PIC", "Priority Level"])
        .size()
        .reset_index(name="Jumlah")
    )

    chart_pic_priority = alt.Chart(pic_priority_df).mark_bar().encode(
        x=alt.X("PIC:N", title="PIC"),
        y=alt.Y("Jumlah:Q"),
        color=alt.Color("Priority Level:N"),
        column=alt.Column("Priority Level:N", spacing=10),
        tooltip=["PIC", "Priority Level", "Jumlah"]
    ).properties(height=300)

    st.altair_chart(chart_pic_priority, use_container_width=True)

    st.markdown("#### 📈 Tren Proyek Dimulai & Diselesaikan per Minggu")

    df_trend = df.copy()
    df_trend["Start Date"] = pd.to_datetime(df_trend["Start Date"], errors="coerce")
    df_trend["Due Date"] = pd.to_datetime(df_trend["Due Date"], errors="coerce")

    # Buat kolom minggu
    df_trend["Start Week"] = df_trend["Start Date"].dt.to_period("W").dt.start_time
    df_trend["Finish Week"] = df_trend.loc[df_trend["Project Status"] == "Finish", "Due Date"].dt.to_period("W").dt.start_time

    # Hitung jumlah proyek dimulai dan diselesaikan
    start_trend = df_trend.groupby("Start Week").size().reset_index(name="Started Projects")
    finish_trend = df_trend[df_trend["Project Status"] == "Finish"].groupby("Finish Week").size().reset_index(name="Finished Projects")

    # Gabungkan dan rapikan
    trend_df = pd.merge(start_trend, finish_trend, left_on="Start Week", right_on="Finish Week", how="outer")
    trend_df["Week"] = trend_df["Start Week"].combine_first(trend_df["Finish Week"])
    trend_df = trend_df[["Week", "Started Projects", "Finished Projects"]].fillna(0)
    trend_df = trend_df.sort_values("Week")

    # Buat chart
    chart = alt.Chart(trend_df).transform_fold(
        ['Started Projects', 'Finished Projects'],
        as_=['Type', 'Count']
    ).mark_line(point=True).encode(
        x=alt.X('Week:T', title='Week'),
        y=alt.Y('Count:Q', title='Number of Projects'),
        color='Type:N',
        tooltip=['Week:T', 'Type:N', 'Count:Q']
    ).properties(height=400, title="Trend of Projects Started and Finished per Week")

    st.altair_chart(chart, use_container_width=True)

    st.markdown("#### 🏆 Leaderboard PIC Dengan Project Terbanyak")

    if "PIC" in df.columns and df["PIC"].notna().sum() > 0:
        df_valid = df[df["PIC"].notna()].copy()
        df_valid["PIC"] = df_valid["PIC"].astype(str)

        pic_leaderboard = (
            df_valid["PIC"]
            .value_counts()
            .rename_axis("PIC")
            .reset_index(name="Jumlah_Proyek")
        )

        st.write("Data Leaderboard PIC:")
        st.dataframe(pic_leaderboard, hide_index=True)

        # Pastikan nama kolom dan tipe data terdeteksi dengan benar
        chart_leaderboard = alt.Chart(pic_leaderboard).mark_bar().encode(
            x=alt.X("Jumlah_Proyek:Q", title="Jumlah Proyek"),
            y=alt.Y("PIC:N", sort='-x', title="PIC"),
            tooltip=["PIC:N", "Jumlah_Proyek:Q"]
        ).properties(
            height=400,
            title="PIC dengan Jumlah Proyek Terbanyak"
        )

        st.altair_chart(chart_leaderboard, use_container_width=True)

    else:
        st.warning("⚠️ Tidak ada data PIC yang tersedia untuk ditampilkan.")

    st.markdown("#### 🔍 Daftar Proyek dari PIC Terpilih")

    # Dropdown interaktif untuk memilih PIC dari leaderboard
    selected_pic = st.selectbox("Pilih PIC untuk melihat proyeknya:", options=pic_leaderboard["PIC"])

    # Filter data proyek berdasarkan PIC terpilih
    filtered_projects = df[df["PIC"] == selected_pic]

    # Tampilkan dalam bentuk tabel
    st.dataframe(
        filtered_projects[["WO Number", "Item", "Start Date", "Due Date", "Priority Level", "Project Status"]],
        use_container_width=True,
        hide_index=True
    )

    # Tampilkan Leaderboard dan Detail PIC dalam 2 kolom
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### 🏆 Leaderboard PIC Dengan Project Terbanyak")
        st.write("Data Leaderboard PIC:")
        st.dataframe(pic_leaderboard, hide_index=True)

    with col2:
        st.markdown("#### 📊 Visualisasi Leaderboard")
        chart_leaderboard = alt.Chart(pic_leaderboard).mark_bar().encode(
            x=alt.X("Jumlah_Proyek:Q", title="Jumlah Proyek"),
            y=alt.Y("PIC:N", sort='-x', title="PIC"),
            tooltip=["PIC:N", "Jumlah_Proyek:Q"]
        ).properties(
            height=400,
            title="PIC dengan Jumlah Proyek Terbanyak"
        )

        st.altair_chart(chart_leaderboard, use_container_width=True)


    # Ambil datamu, misal 38 baris
    df = st.session_state.DataFrame.sort_values(by="Sisa Hari", ascending=True)
    display_cols = ["WO Number", "Item", "PIC", "Requested By", "Request Date", "Start Date", "Due Date", "Sisa Hari"]
    df_display = df[display_cols].reset_index(drop=True)

    # Convert to HTML Table
    table_html = df_display.to_html(index=False, classes="scroll-table")

    # CSS + JS for auto-scroll
    scroll_style = """
    <style>
    .scroll-container {
        height: 300px;
        overflow: hidden;
        position: relative;
    }
    .scroll-table-wrapper {
        animation: scroll-up 20s linear infinite;
    }
    @keyframes scroll-up {
        0%   { transform: translateY(0); }
        100% { transform: translateY(-100%); }
    }
    .scroll-table {
        width: 100%;
        border-collapse: collapse;
    }
    .scroll-table th, .scroll-table td {
        border: 1px solid #ddd;
        padding: 8px;
    }
    .scroll-table tr:nth-child(even) {
        background-color: #1e1e1e;
    }
    .scroll-table th {
        background-color: #0a58ca;
        color: white;
        position: sticky;
        top: 0;
    }
    </style>
    """

    # Combine and render
    st.markdown("#### 📋 Daftar Proyek Auto-scroll")
    st.markdown(scroll_style, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="scroll-container">
    <div class="scroll-table-wrapper">
        {table_html}
        {table_html} <!-- Duplicate for smooth looping -->
    </div>
    </div>
    """, unsafe_allow_html=True)

