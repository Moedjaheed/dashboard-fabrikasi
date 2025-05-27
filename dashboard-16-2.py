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

tabs = st.tabs(["📋 Input Baru", "📊 Status Proyek", "🔍 Detail Proyek", "📈 Visualisasi"])

with tabs[0]:
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

with tabs[1]:
    df = st.session_state.DataFrame
    df_sorted = df.sort_values(by=["Priority Level", "Sisa Hari"], ascending=[True, True])
    df_sorted["Start Date"] = pd.to_datetime(df_sorted["Start Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
    df_sorted["Due Date"] = pd.to_datetime(df_sorted["Due Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")
    df_sorted["Request Date"] = pd.to_datetime(df_sorted["Request Date"], errors="coerce").apply(lambda x: x.strftime("%d %B %Y") if pd.notnull(x) else "")

    st.subheader("📋 Daftar Proyek")
    display_cols = ["WO Number", "Item", "PIC", "Requested By", "Request Date", "Start Date", "Due Date", "Sisa Hari"]
    st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)

    if st.button("💾 Simpan ke Google Sheets"):
        update_gsheet(worksheet, st.session_state.DataFrame)
        st.success("✅ Data berhasil disimpan ke Google Sheets!")

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

with tabs[3]:
    st.subheader("📊 Visualisasi Proyek")
    df_vis = st.session_state.DataFrame.copy()
    df_vis["Start Date"] = pd.to_datetime(df_vis["Start Date"], errors="coerce", dayfirst=True)
    df_vis["Due Date"] = pd.to_datetime(df_vis["Due Date"], errors="coerce", dayfirst=True)

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
