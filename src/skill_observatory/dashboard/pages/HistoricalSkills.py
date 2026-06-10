import duckdb
import pandas as pd
import streamlit as st

st.title("Historical Skill Trends")

con = duckdb.connect(
    "data/warehouse/skill_observatory.duckdb",
    read_only=True,
)

skills = con.sql(
    """
    select
        skill,
        sum(mentions) as mentions
    from monthly_skill_counts
    group by 1
    order by mentions desc
    """
).df()

selected_skill = st.selectbox(
    "Skill",
    options=skills["skill"].tolist(),
    index=0,
    key="selected_skill",
)

trend = con.sql(
    f"""
    select
        publication_month,
        mentions
    from monthly_skill_counts
    where skill = '{selected_skill}'
    order by publication_month
    """
).df()

st.subheader(selected_skill)

st.line_chart(
    trend.set_index("publication_month")
)

st.write(
    f"{len(skills):,} skills loaded"
)

st.dataframe(
    skills.head(20)
)