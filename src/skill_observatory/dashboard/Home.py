import duckdb
import streamlit as st

st.set_page_config(
    page_title="Swedish Tech Skill Observatory",
    layout="wide",
)

con = duckdb.connect(
    "data/warehouse/skill_observatory.duckdb"
)

st.title("Swedish Tech Skill Observatory")

top_skills = con.sql("""
    select
        skill,
        sum(mentions) as mentions
    from monthly_skill_counts
    group by skill
    order by mentions desc
    limit 20
""").df()

st.subheader("Top Skills")

st.dataframe(
    top_skills,
    use_container_width=True,
)

trend_df = con.sql("""
    select
        month,
        skill,
        mentions
    from monthly_skill_counts
    order by month
""").df()

st.subheader("Skill Trends")

st.line_chart(
    trend_df,
    x="month",
    y="mentions",
    color="skill",
)

selected_skill = st.selectbox(
    "Skill",
    sorted(top_skills["skill"].unique())
)

skill_df = con.sql(f"""
    select
        month,
        mentions
    from monthly_skill_counts
    where skill = '{selected_skill}'
    order by month
""").df()

st.line_chart(
    skill_df,
    x="month",
    y="mentions",
)