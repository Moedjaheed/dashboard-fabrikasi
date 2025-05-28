import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from gsheets_utils import load_gsheet, update_gsheet
import streamlit.components.v1 as components

st.set_page_config(page_title='Dashboard Fabrication Project', page_icon='🛠️', layout="wide")
st.title('🛠️ Fabrication Hydraulic Project Schedule Dashboard')
st.info('Terhubung dengan Google Sheets untuk manajemen proyek tim fabrikasi.')

sheet_id = "1JLb5wzQL5yT-8joGw53Wc_rDlzO1TaJeZDWCLtB1DoY"
worksheet_name = "Sheet1"
df, worksheet = load_gsheet(sheet_id, worksheet_name)

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
        st.subheader("📋 Daftar Proyek Prioritas")
        df_vis = st.session_state.DataFrame.copy()
        df_vis["Start Date"] = pd.to_datetime(df_vis["Start Date"], errors="coerce", dayfirst=True)
        df_vis["Due Date"] = pd.to_datetime(df_vis["Due Date"], errors="coerce", dayfirst=True)
        

        # Siapkan data
        priority_order = {"Tinggi": 0, "Sedang": 1, "Rendah": 2}
        df_scroll = df[["WO Number", "Item", "PIC", "Priority Level", "Start Date", "Due Date", "Sisa Hari"]].copy()
        df_scroll["Priority_Sort"] = df_scroll["Priority Level"].map(priority_order)
        df_scroll = df_scroll.sort_values("Priority_Sort").reset_index(drop=True)
        df_scroll["Start Date"] = df_scroll["Start Date"].dt.strftime("%d %b %Y")
        df_scroll["Due Date"] = df_scroll["Due Date"].dt.strftime("%d %b %Y")

        # CSS & HTML
        scroll_style = """
        <style>
        .scroll-container {
            width: 100%;
            border: 1px solid #444;
            border-radius: 5px;
            overflow-x: auto;
            overflow-y: hidden;
            font-family: sans-serif;
        }

        .scroll-table {
            width: 100%;
            min-width: 700px; /* Allow horizontal scroll on mobile */
            border-collapse: collapse;
            table-layout: fixed;
        }

        .scroll-table thead {
            position: sticky;
            top: 0;
            background-color: #1a1a1a;
            z-index: 2;
        }

        .scroll-table th, .scroll-table td {
            padding: 10px;
            font-size: 13px;
            text-align: left;
            border: 1px solid #333;
        }

        .scroll-table th {
            background-color: white;
            color: black;
        }

        .scroll-body {
            height: 360px;
            overflow: hidden;
            position: relative;
        }

        .scroll-inner {
            display: inline-block;
            animation: scroll-up 100s linear infinite;
        }

        .high-priority { background-color: #ff4d4d; color: black; }
        .medium-priority { background-color: #ffd966; color: black; }
        .low-priority { background-color: #87ceeb; color: black; }

        /* Responsive: Reduce font and enable scroll on small screen */
        @media screen and (max-width: 768px) {
            .scroll-table th, .scroll-table td {
                font-size: 11px;
                padding: 6px;
            }
            .scroll-table {
                min-width: 100%;
            }
        }
        @keyframes scroll-up {
            0% { transform: translateY(0); }
            100% { transform: translateY(-50%); }
        }
        </style>
        """


        # Baris isi tabel
        rows_html = ""
        for _, row in df_scroll.iterrows():
            prio_class = {
                "Tinggi": "high-priority",
                "Sedang": "medium-priority",
                "Rendah": "low-priority"
            }.get(row["Priority Level"], "")

            rows_html += f"""
            <tr>
                <td>{row['WO Number']}</td>
                <td>{row['Item']}</td>
                <td>{row['PIC']}</td>
                <td class="{prio_class}">{row['Priority Level']}</td>
                <td>{row['Start Date']}</td>
                <td>{row['Due Date']}</td>
                <td>{row['Sisa Hari']}</td>
            </tr>
            """

        # Tabel HTML split: header tetap, isi scroll
        table_html = f"""
        <div class="scroll-container">
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
        </table>
        <div class="scroll-body">
            <div class="scroll-inner">
            <table class="scroll-table">
                <tbody>
                {rows_html}
                {rows_html}    <!-- Duplicate to loop -->
                </tbody>
            </table>
            </div>
        </div>
        </div>
        """

        scroll_script = """
        <script>
        let scrollContainer = document.querySelector(".scroll-body");
        let isPaused = false;
        let scrollSpeed = 0.5;
        let idleTimer = null;

        function startAutoScroll() {{
            function step() {{
                if (!isPaused) {{
                    scrollContainer.scrollTop += scrollSpeed;
                    if (scrollContainer.scrollTop >= scrollContainer.scrollHeight - scrollContainer.clientHeight) {{
                        scrollContainer.scrollTop = 0;
                    }}
                }}
                requestAnimationFrame(step);
            }}
            requestAnimationFrame(step);
        }}

        function resetIdleTimer() {{
            isPaused = true;
            clearTimeout(idleTimer);
            idleTimer = setTimeout(() => {{
                isPaused = false;
            }}, 2000);
        }}

        scrollContainer.addEventListener('scroll', resetIdleTimer);
        scrollContainer.addEventListener('wheel', resetIdleTimer);
        scrollContainer.addEventListener('touchmove', resetIdleTimer);
        scrollContainer.addEventListener('mouseenter', resetIdleTimer);
        scrollContainer.addEventListener('mouseleave', resetIdleTimer);

        startAutoScroll();
        </script>
        """


        # Render ke Streamlit
        components.html(scroll_style + table_html + scroll_script, height=360, scrolling=False)



        # df = st.session_state.DataFrame
        # df_sorted = df.sort_values(by=["Priority Level", "Sisa Hari"], ascending=[True, True])
        # df_sorted["Start Date"] = pd.to_datetime(df_sorted["Start Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
        # df_sorted["Due Date"] = pd.to_datetime(df_sorted["Due Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
        # df_sorted["Request Date"] = pd.to_datetime(df_sorted["Request Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")

        # display_cols = ["WO Number", "Item", "PIC", "Requested By", "Request Date", "Start Date", "Due Date", "Sisa Hari"]
        # st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)

        # if st.button("💾 Simpan ke Google Sheets"):
        #     update_gsheet(worksheet, st.session_state.DataFrame)
        #     st.success("✅ Data berhasil disimpan ke Google Sheets!")



        # Grup visualisasi dalam tiga kolom bar dan satu kolom donut
        st.subheader("📈 Visualisasi Data")

        col1, col2, col3 = st.columns(3)
        with col1:
            div_count = df_vis["Division"].value_counts().reset_index()
            div_count.columns = ["Division", "Jumlah"]

            chart_div = alt.Chart(div_count).mark_bar().encode(
                x=alt.X("Jumlah:Q", title="Jumlah Proyek"),
                y=alt.Y("Division:N", sort='-x', title="Divisi"),
                tooltip=["Division", "Jumlah"]
            ).properties(title="📈 Jumlah Proyek per Divisi", height=250)

            st.altair_chart(chart_div, use_container_width=True)

        with col2:
            pic_count = df_vis["PIC"].value_counts().reset_index()
            pic_count.columns = ["PIC", "Jumlah"]

            chart_pic = alt.Chart(pic_count).mark_bar().encode(
                x=alt.X("Jumlah:Q", title="Jumlah Proyek"),
                y=alt.Y("PIC:N", sort='-x', title="PIC"),
                tooltip=["PIC", "Jumlah"]
            ).properties(title="📈 Jumlah Proyek per PIC", height=250)

            st.altair_chart(chart_pic, use_container_width=True)

        with col3:
            status_count = df_vis["Project Status"].value_counts().reset_index()
            status_count.columns = ["Status", "Jumlah"]

            chart_status = alt.Chart(status_count).mark_bar().encode(
                x=alt.X("Jumlah:Q", title="Jumlah Proyek"),
                y=alt.Y("Status:N", sort='-x', title="Status"),
                tooltip=["Status", "Jumlah"]
            ).properties(title="📊 Jumlah per Status", height=250)

            st.altair_chart(chart_status, use_container_width=True)

        # Donut Chart di bawah
        col4, col5, col6 = st.columns(3)
        with col4:
            donut1 = alt.Chart(status_count).mark_arc(innerRadius=50).encode(
                theta="Jumlah:Q",
                color="Status:N",
                tooltip=["Status", "Jumlah"]
            ).properties(title="📊 Distribusi Status")

            priority_counts = df["Priority Level"].value_counts().reset_index()
            priority_counts.columns = ["Prioritas", "Jumlah"]
            st.altair_chart(donut1, use_container_width=True)
        
        with col5 :
            donut2 = alt.Chart(priority_counts).mark_arc(innerRadius=50).encode(
                theta="Jumlah:Q",
                color="Prioritas:N",
                tooltip=["Prioritas", "Jumlah"]
            ).properties(title="🎯 Distribusi Prioritas")
            st.altair_chart(donut2, use_container_width=True)

        with col6:
            donut3 = alt.Chart(pic_count).mark_arc(innerRadius=50).encode(
                theta="Jumlah:Q",
                color="PIC:N",
                tooltip=["PIC", "Jumlah"]
            ).properties(title="👤 Distribusi per PIC")
            st.altair_chart(donut3, use_container_width=True)




        st.markdown("#### 🗓️ Timeline Proyek")

        # Filter opsional
        with st.expander("🔎 Filter Timeline"):
            selected_pic = st.multiselect("Filter berdasarkan PIC:", options=df["PIC"].dropna().unique().tolist())
            selected_priority = st.multiselect("Filter berdasarkan Prioritas:", options=df["Priority Level"].dropna().unique().tolist())

        # Ambil semua proyek yang punya tanggal mulai dan akhir
        df_timeline = df_vis[(df_vis["Start Date"].notna()) & (df_vis["Due Date"].notna())]

        # Terapkan filter jika dipilih
        if selected_pic:
            df_timeline = df_timeline[df_timeline["PIC"].isin(selected_pic)]

        if selected_priority:
            df_timeline = df_timeline[df_timeline["Priority Level"].isin(selected_priority)]

        # Tambahan kolom durasi dan minggu
        df_timeline["Durasi"] = (df_timeline["Due Date"] - df_timeline["Start Date"]).dt.days
        df_timeline["Week"] = df_timeline["Start Date"].dt.to_period("W").dt.start_time

        # Tampilkan jika ada data
        if not df_timeline.empty:
            # Garis vertikal penanda hari ini
            today_line = alt.Chart(pd.DataFrame({'x': [pd.to_datetime(today)]})).mark_rule(color='red').encode(x='x:T')

            # Timeline chart dengan grid horizontal
            timeline_chart = alt.Chart(df_timeline).mark_bar().encode(
                x=alt.X('Start Date:T', title='Tanggal Mulai', axis=alt.Axis(format='%d %b', grid=True)),
                x2='Due Date:T',
                y=alt.Y('Item:N', title='Item Proyek', sort='-x'),
                color=alt.Color('PIC:N', title='PIC'),
                tooltip=['Item', 'PIC', 'Priority Level', 'Start Date', 'Due Date', 'Durasi']
            ).properties(
                height=900,
                title="Timeline Proyek (Tanpa Batasan Waktu)"
            )

            # Gabungkan chart + penanda hari ini
            combined_chart = (timeline_chart + today_line).interactive()

            st.altair_chart(combined_chart, use_container_width=True)
        else:
            st.info("Tidak ada proyek yang memenuhi syarat untuk ditampilkan.")

                        

        # 📊 Visualisasi Proyek per Divisi dan PIC berdasarkan Status & Prioritas
        st.subheader("📊 Distribusi Proyek berdasarkan Kategori")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 📌 Jumlah Proyek per Divisi berdasarkan Status")
            div_status_df = (
                df.groupby(["Division", "Project Status"])
                .size()
                .reset_index(name="Jumlah")
            )

            chart_div_status = alt.Chart(div_status_df).mark_bar().encode(
                x=alt.X("Division:N", title="Divisi"),
                y=alt.Y("Jumlah:Q", title="Jumlah Proyek"),
                color=alt.Color("Project Status:N", title="Status"),
                tooltip=["Division", "Project Status", "Jumlah"]
            ).properties(
                height=400,
                title="Per Divisi per Status"
            )

            st.altair_chart(chart_div_status, use_container_width=True)

        with col2:
            st.markdown("##### 👤 Jumlah Proyek per PIC berdasarkan Prioritas")
            pic_priority_df = (
                df.groupby(["PIC", "Priority Level"])
                .size()
                .reset_index(name="Jumlah")
            )

            chart_pic_priority = alt.Chart(pic_priority_df).mark_bar().encode(
                x=alt.X("PIC:N", title="PIC", sort='-y'),
                y=alt.Y("Jumlah:Q", title="Jumlah Proyek"),
                color=alt.Color("Priority Level:N", title="Prioritas"),
                tooltip=["PIC", "Priority Level", "Jumlah"]
            ).properties(
                height=400,
                title="Per PIC per Prioritas"
            )

            st.altair_chart(chart_pic_priority, use_container_width=True)




        # 📈 Tren Proyek Dimulai dan Diselesaikan
        st.markdown("### 📈 Tren Mingguan Proyek")

        # Siapkan data tren mingguan
        df_trend = df.copy()
        df_trend["Start Date"] = pd.to_datetime(df_trend["Start Date"], errors="coerce")
        df_trend["Due Date"] = pd.to_datetime(df_trend["Due Date"], errors="coerce")

        # Tambahkan kolom minggu
        df_trend["Start Week"] = df_trend["Start Date"].dt.to_period("W").dt.start_time
        df_trend["Finish Week"] = df_trend.loc[df_trend["Project Status"] == "Finish", "Due Date"].dt.to_period("W").dt.start_time

        # Hitung jumlah proyek mulai dan selesai per minggu
        start_trend = df_trend.groupby("Start Week").size().reset_index(name="Started Projects")
        finish_trend = df_trend[df_trend["Project Status"] == "Finish"].groupby("Finish Week").size().reset_index(name="Finished Projects")

        # Gabungkan dan rapikan data tren
        trend_df = pd.merge(start_trend, finish_trend, left_on="Start Week", right_on="Finish Week", how="outer")
        trend_df["Week"] = trend_df["Start Week"].combine_first(trend_df["Finish Week"])
        trend_df = trend_df[["Week", "Started Projects", "Finished Projects"]].fillna(0)
        trend_df = trend_df.sort_values("Week")

        # Visualisasi tren mingguan
        chart_trend = alt.Chart(trend_df).transform_fold(
            ['Started Projects', 'Finished Projects'],
            as_=['Tipe', 'Jumlah']
        ).mark_line(point=True).encode(
            x=alt.X('Week:T', title='Minggu'),
            y=alt.Y('Jumlah:Q', title='Jumlah Proyek'),
            color=alt.Color('Tipe:N', title='Tipe Proyek'),
            tooltip=['Week:T', 'Tipe:N', 'Jumlah:Q']
        ).properties(height=350, title="Tren Proyek Dimulai dan Diselesaikan per Minggu")

        st.altair_chart(chart_trend, use_container_width=True)




        st.markdown("#### 🏆 Leaderboard PIC Dengan Jumlah Proyek Terbanyak")

        if "PIC" in df.columns and df["PIC"].notna().sum() > 0:
            df_valid = df[df["PIC"].notna()].copy()
            df_valid["PIC"] = df_valid["PIC"].astype(str)

            pic_leaderboard = (
                df_valid["PIC"]
                .value_counts()
                .rename_axis("PIC")
                .reset_index(name="Jumlah_Proyek")
            )

            with st.expander("🔎 Filter Leaderboard PIC"):
                min_projects = st.slider(
                    "Tampilkan hanya PIC dengan minimal proyek:",
                    min_value=1,
                    max_value=int(pic_leaderboard["Jumlah_Proyek"].max()),
                    value=1
                )

            # Terapkan filter
            pic_leaderboard_filtered = pic_leaderboard[
                pic_leaderboard["Jumlah_Proyek"] >= min_projects
            ].copy()

            # Tambahkan titik tengah untuk teks
            pic_leaderboard_filtered["Midpoint"] = pic_leaderboard_filtered["Jumlah_Proyek"] / 2

            # Visualisasi dalam satu kolom
            st.markdown("##### 📊 Visualisasi Leaderboard")

            base_chart = alt.Chart(pic_leaderboard_filtered).encode(
                y=alt.Y("PIC:N", sort='-x', title="PIC")
            )

            bars = base_chart.mark_bar().encode(
                x=alt.X("Jumlah_Proyek:Q", title="Jumlah Proyek"),
                tooltip=["PIC:N", "Jumlah_Proyek:Q"]
            )

            labels = alt.Chart(pic_leaderboard_filtered).mark_text(
                align='center',
                baseline='middle',
                color='white'
            ).encode(
                x=alt.X("Midpoint:Q"),
                y=alt.Y("PIC:N"),
                text=alt.Text("Jumlah_Proyek:Q")
            )

            st.altair_chart(
                (bars + labels).properties(
                    height=400,
                    title="PIC dengan Jumlah Proyek Terbanyak"
                ),
                use_container_width=True
            )

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



