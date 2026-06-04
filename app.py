import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="Employee Attrition Analyzer",
    page_icon="📊",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #0d0d0d;
        color: #f0f0f0;
    }
    .main { background-color: #0d0d0d; }

    h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #ffffff15;
        border-radius: 16px;
        padding: 24px 28px;
        text-align: center;
        box-shadow: 0 4px 24px #0005;
    }
    .metric-label {
        font-size: 13px;
        color: #888;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .metric-value {
        font-family: 'Syne', sans-serif;
        font-size: 36px;
        font-weight: 800;
        color: #ffffff;
    }
    .metric-value.red { color: #ff4d6d; }
    .metric-value.green { color: #06d6a0; }
    .metric-value.blue { color: #4cc9f0; }

    .insight-box {
        background: #1a1a2e;
        border-left: 4px solid #4cc9f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 8px 0;
        font-size: 15px;
        color: #ddd;
    }
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: 20px;
        font-weight: 700;
        color: #f0f0f0;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #ffffff15;
    }
    .stSelectbox label, .stMultiSelect label { color: #aaa !important; }
    div[data-baseweb="select"] { background: #1a1a2e !important; }
    .stSidebar { background: #111 !important; }
</style>
""", unsafe_allow_html=True)


# ── Load & Prepare Data ───────────────────────────────────────
@st.cache_data
def load_data():
    csv_path = "data/hr_data.csv"
    db_path  = "data/hr_data.db"

    df = pd.read_csv(csv_path)

    # Create SQLite DB
    conn = sqlite3.connect(db_path)
    df.to_sql("employees", conn, if_exists="replace", index=False)

    # SQL Queries → back into Pandas
    attrition_count = pd.read_sql(
        "SELECT Attrition, COUNT(*) as count FROM employees GROUP BY Attrition", conn)

    dept_attrition = pd.read_sql(
        "SELECT Department, Attrition, COUNT(*) as count FROM employees GROUP BY Department, Attrition", conn)

    salary_attrition = pd.read_sql(
        "SELECT Attrition, ROUND(AVG(MonthlyIncome),0) as avg_salary FROM employees GROUP BY Attrition", conn)

    age_attrition = pd.read_sql("""
        SELECT
            CASE WHEN Age < 30 THEN 'Under 30'
                 WHEN Age < 40 THEN '30–40'
                 ELSE '40+' END as age_group,
            Attrition, COUNT(*) as count
        FROM employees
        GROUP BY age_group, Attrition
    """, conn)

    jobrole_attrition = pd.read_sql(
        "SELECT JobRole, Attrition, COUNT(*) as count FROM employees GROUP BY JobRole, Attrition", conn)

    conn.close()
    return df, attrition_count, dept_attrition, salary_attrition, age_attrition, jobrole_attrition


# ── Check if dataset exists ───────────────────────────────────
if not os.path.exists("data/hr_data.csv"):
    st.error("⚠️ Dataset not found! Please place `hr_data.csv` inside a `data/` folder.")
    st.markdown("""
    **Download the dataset:**
    1. Go to [Kaggle IBM HR Dataset](https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset)
    2. Download `WA_Fn-UseC_-HR-Employee-Attrition.csv`
    3. Rename it to `hr_data.csv`
    4. Put it inside a folder called `data/`
    5. Restart the app
    """)
    st.stop()

df, attrition_count, dept_attrition, salary_attrition, age_attrition, jobrole_attrition = load_data()


# ── Sidebar Filters ───────────────────────────────────────────
st.sidebar.markdown("## 🎛️ Filters")
st.sidebar.markdown("---")

dept_options = ["All"] + sorted(df["Department"].unique().tolist())
selected_dept = st.sidebar.selectbox("Department", dept_options)

role_options = ["All"] + sorted(df["JobRole"].unique().tolist())
selected_role = st.sidebar.selectbox("Job Role", role_options)

age_range = st.sidebar.slider("Age Range", int(df["Age"].min()), int(df["Age"].max()), (20, 60))

filtered_df = df.copy()
if selected_dept != "All":
    filtered_df = filtered_df[filtered_df["Department"] == selected_dept]
if selected_role != "All":
    filtered_df = filtered_df[filtered_df["JobRole"] == selected_role]
filtered_df = filtered_df[(filtered_df["Age"] >= age_range[0]) & (filtered_df["Age"] <= age_range[1])]


# ── Header ────────────────────────────────────────────────────
st.markdown("""
<h1 style='font-family:Syne,sans-serif; font-size:40px; font-weight:800; margin-bottom:4px;'>
    📊 Employee Attrition Analyzer
</h1>
<p style='color:#888; font-size:15px; margin-bottom:32px;'>
    IBM HR Analytics · Python · SQL · Streamlit · Plotly
</p>
""", unsafe_allow_html=True)


# ── KPI Cards ─────────────────────────────────────────────────
total      = len(filtered_df)
left       = len(filtered_df[filtered_df["Attrition"] == "Yes"])
rate       = round((left / total) * 100, 1) if total > 0 else 0
avg_salary = int(filtered_df["MonthlyIncome"].mean()) if total > 0 else 0
avg_tenure = round(filtered_df["YearsAtCompany"].mean(), 1) if total > 0 else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Total Employees</div>
        <div class="metric-value blue">{total:,}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Employees Left</div>
        <div class="metric-value red">{left:,}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Attrition Rate</div>
        <div class="metric-value {'red' if rate > 15 else 'green'}">{rate}%</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Avg Monthly Income</div>
        <div class="metric-value green">${avg_salary:,}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Charts Row 1 ──────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Attrition Overview</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    # Attrition by Department
    dept_fig = dept_attrition.copy()
    fig1 = px.bar(
        dept_fig, x="Department", y="count", color="Attrition",
        barmode="group", title="Attrition by Department",
        color_discrete_map={"Yes": "#ff4d6d", "No": "#4cc9f0"},
        template="plotly_dark"
    )
    fig1.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font_color="#ddd", title_font_size=16,
        legend=dict(bgcolor="#1a1a2e")
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Attrition Pie
    fig2 = px.pie(
        attrition_count, values="count", names="Attrition",
        title="Overall Attrition Split",
        color_discrete_map={"Yes": "#ff4d6d", "No": "#4cc9f0"},
        hole=0.5, template="plotly_dark"
    )
    fig2.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font_color="#ddd", title_font_size=16
    )
    st.plotly_chart(fig2, use_container_width=True)


# ── Charts Row 2 ──────────────────────────────────────────────
st.markdown('<div class="section-title">💰 Salary & Age Analysis</div>', unsafe_allow_html=True)
col3, col4 = st.columns(2)

with col3:
    # Salary distribution by attrition
    fig3 = px.box(
        filtered_df, x="Attrition", y="MonthlyIncome",
        color="Attrition", title="Monthly Income vs Attrition",
        color_discrete_map={"Yes": "#ff4d6d", "No": "#4cc9f0"},
        template="plotly_dark"
    )
    fig3.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font_color="#ddd", title_font_size=16
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    # Age group attrition
    fig4 = px.bar(
        age_attrition, x="age_group", y="count", color="Attrition",
        barmode="group", title="Attrition by Age Group",
        color_discrete_map={"Yes": "#ff4d6d", "No": "#4cc9f0"},
        category_orders={"age_group": ["Under 30", "30–40", "40+"]},
        template="plotly_dark"
    )
    fig4.update_layout(
        paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
        font_color="#ddd", title_font_size=16
    )
    st.plotly_chart(fig4, use_container_width=True)


# ── Chart Row 3 ───────────────────────────────────────────────
st.markdown('<div class="section-title">👔 Job Role Breakdown</div>', unsafe_allow_html=True)

fig5 = px.bar(
    jobrole_attrition, x="count", y="JobRole", color="Attrition",
    barmode="group", orientation="h", title="Attrition by Job Role",
    color_discrete_map={"Yes": "#ff4d6d", "No": "#4cc9f0"},
    template="plotly_dark", height=420
)
fig5.update_layout(
    paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e",
    font_color="#ddd", title_font_size=16
)
st.plotly_chart(fig5, use_container_width=True)


# ── Key Insights ──────────────────────────────────────────────
st.markdown('<div class="section-title">🔍 Key Insights</div>', unsafe_allow_html=True)

# Auto-generated insights from data
top_dept = dept_attrition[dept_attrition["Attrition"]=="Yes"].sort_values("count", ascending=False).iloc[0]["Department"]
left_salary  = int(salary_attrition[salary_attrition["Attrition"]=="Yes"]["avg_salary"].values[0])
stayed_salary= int(salary_attrition[salary_attrition["Attrition"]=="No"]["avg_salary"].values[0])
salary_diff  = round(((stayed_salary - left_salary) / left_salary) * 100, 1)

young_left  = age_attrition[(age_attrition["age_group"]=="Under 30") & (age_attrition["Attrition"]=="Yes")]["count"].values[0]
young_total = age_attrition[age_attrition["age_group"]=="Under 30"]["count"].sum()
young_rate  = round((young_left / young_total) * 100, 1)

st.markdown(f"""
<div class="insight-box">💡 <b>{top_dept}</b> has the highest number of employees who left the company.</div>
<div class="insight-box">💡 Employees who left earned on average <b>${left_salary:,}/month</b> — that's <b>{salary_diff}% less</b> than those who stayed (${stayed_salary:,}/month). Lower pay is a strong attrition driver.</div>
<div class="insight-box">💡 <b>{young_rate}%</b> of employees under 30 left the company — the highest attrition rate across all age groups.</div>
""", unsafe_allow_html=True)


# ── Raw Data Table ────────────────────────────────────────────
st.markdown('<div class="section-title">🗂️ Filtered Data Table</div>', unsafe_allow_html=True)
st.markdown(f"Showing **{len(filtered_df):,}** employees based on your filters.")
cols_to_show = ["Age", "Department", "JobRole", "Attrition", "MonthlyIncome", "YearsAtCompany", "JobSatisfaction", "OverTime"]
st.dataframe(
    filtered_df[cols_to_show].sort_values("Attrition", ascending=False).reset_index(drop=True),
    use_container_width=True, height=300
)


# ── Footer ────────────────────────────────────────────────────
st.markdown("""
<br>
<p style='text-align:center; color:#444; font-size:13px;'>
    Built by <b style='color:#4cc9f0'>Ashish</b> · Python · SQL · Streamlit · Plotly · IBM HR Dataset
</p>
""", unsafe_allow_html=True)
