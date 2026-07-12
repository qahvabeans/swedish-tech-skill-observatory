import duckdb
import pandas as pd
import pydeck as pdk
import streamlit as st


DB_PATH = "data/warehouse/skill_observatory.duckdb"


@st.cache_data(show_spinner=False)
def load_skill_trends() -> pd.DataFrame:
    con = duckdb.connect(DB_PATH, read_only=True)

    return con.sql(
        """
        select
            publication_month,
            skill,
            mentions,
            ads,
            share_of_ads
        from mart_dashboard_skill_trends
        order by publication_month, skill
        """
    ).df()


@st.cache_data(show_spinner=False)
def load_skill_geography() -> pd.DataFrame:
    con = duckdb.connect(DB_PATH, read_only=True)

    return con.sql(
        """
        select
            publication_month,
            skill,
            municipality,
            municipality_code,
            region,
            region_code,
            longitude,
            latitude,
            mentions,
            ads,
            share_of_ads
        from mart_skill_geography
        where longitude is not null
          and latitude is not null
        order by publication_month, skill, municipality
        """
    ).df()


def growth_table(
    data: pd.DataFrame,
    metric: str,
    top_n: int,
    ascending: bool,
) -> pd.DataFrame:
    first_month = data["publication_month"].min()
    last_month = data["publication_month"].max()

    first = (
        data[data["publication_month"] == first_month][["skill", metric]]
        .rename(columns={metric: "first_value"})
    )
    last = (
        data[data["publication_month"] == last_month][["skill", metric]]
        .rename(columns={metric: "last_value"})
    )

    growth = first.merge(last, on="skill", how="inner")
    growth["change"] = growth["last_value"] - growth["first_value"]

    return (
        growth.sort_values("change", ascending=ascending)
        .head(top_n)
        .reset_index(drop=True)
    )


def format_percent_columns(data: pd.DataFrame) -> pd.io.formats.style.Styler:
    return data.style.format(
        {
            "share_of_ads": "{:.2%}",
            "first_value": "{:.2%}",
            "last_value": "{:.2%}",
            "change": "{:.2%}",
        },
        na_rep="",
    )


def render_geography_map(
    geo_summary: pd.DataFrame,
    metric: str,
) -> None:
    map_data = geo_summary.copy()
    max_metric = map_data[metric].max()

    if max_metric <= 0:
        st.info("No positive values are available for the selected metric.")
        return

    map_data["radius"] = 3_000 + (map_data[metric] / max_metric) * 35_000
    map_data["share_label"] = (map_data["share_of_ads"] * 100).round(2).astype(str)

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[longitude, latitude]",
        get_radius="radius",
        get_fill_color="[208, 61, 32, 145]",
        get_line_color="[112, 27, 14, 220]",
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=62.0,
        longitude=16.0,
        zoom=4.1,
        pitch=0,
    )

    tooltip = {
        "html": (
            "<b>{municipality}</b><br/>"
            "{region}<br/>"
            "Mentions: {mentions}<br/>"
            "Ads: {ads}<br/>"
            "Share of ads: {share_label}%"
        ),
        "style": {
            "backgroundColor": "#111827",
            "color": "#f9fafb",
        },
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=None,
            tooltip=tooltip,
        ),
        use_container_width=True,
    )


def render_dashboard() -> None:
    st.title("Swedish Tech Skill Observatory")
    st.caption(
        "Historical demand for technology skills in Swedish job ads, modeled with "
        "DuckDB and dbt."
    )

    trends = load_skill_trends()
    geography = load_skill_geography()

    if trends.empty:
        st.warning("No skill trends are available. Run regex extraction and dbt first.")
        st.stop()

    trends["publication_month"] = pd.to_datetime(trends["publication_month"])
    if not geography.empty:
        geography["publication_month"] = pd.to_datetime(geography["publication_month"])

    available_months = sorted(trends["publication_month"].dt.date.unique())
    skill_totals = (
        trends.groupby("skill", as_index=False)["mentions"]
        .sum()
        .sort_values("mentions", ascending=False)
    )

    default_skills = skill_totals["skill"].head(5).tolist()

    with st.sidebar:
        st.header("Filters")
        metric_label = st.radio(
            "Metric",
            options=["Share of ads", "Mentions"],
            horizontal=True,
        )
        metric = "share_of_ads" if metric_label == "Share of ads" else "mentions"

        selected_range = st.date_input(
            "Date range",
            value=(available_months[0], available_months[-1]),
            min_value=available_months[0],
            max_value=available_months[-1],
        )

        selected_skills = st.multiselect(
            "Skills",
            options=skill_totals["skill"].tolist(),
            default=default_skills,
        )

        top_n = st.slider(
            "Top N",
            min_value=5,
            max_value=30,
            value=10,
            step=5,
        )

    if len(selected_range) != 2:
        st.info("Select a start and end month.")
        st.stop()

    start_date, end_date = selected_range
    filtered = trends[
        (trends["publication_month"].dt.date >= start_date)
        & (trends["publication_month"].dt.date <= end_date)
    ].copy()

    if filtered.empty:
        st.warning("No rows match the selected date range.")
        st.stop()

    selected = filtered[filtered["skill"].isin(selected_skills)].copy()

    latest_month = filtered["publication_month"].max()
    latest_rows = filtered[filtered["publication_month"] == latest_month]
    latest_ads = int(latest_rows["ads"].max())
    top_latest = latest_rows.nlargest(1, metric).iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Skills", f"{filtered['skill'].nunique():,}")
    col2.metric("Months", f"{filtered['publication_month'].nunique():,}")
    col3.metric("Ads latest month", f"{latest_ads:,}")
    col4.metric("Top latest skill", str(top_latest["skill"]))

    tab_trends, tab_top, tab_growth, tab_geography, tab_table = st.tabs(
        [
            "Trends",
            "Top N",
            "Growth",
            "Geography",
            "Table",
        ]
    )

    with tab_trends:
        if selected.empty:
            st.info("Select at least one skill.")
        else:
            chart_data = selected.pivot_table(
                index="publication_month",
                columns="skill",
                values=metric,
                aggfunc="sum",
            ).sort_index()

            st.line_chart(chart_data)

    with tab_top:
        filtered_months = sorted(filtered["publication_month"].dt.date.unique())
        selected_month = st.select_slider(
            "Month",
            options=filtered_months,
            value=latest_month.date(),
        )
        top_rows = (
            filtered[filtered["publication_month"].dt.date == selected_month]
            .nlargest(top_n, metric)
            .loc[:, ["skill", "mentions", "share_of_ads"]]
            .reset_index(drop=True)
        )

        st.bar_chart(top_rows.set_index("skill")[[metric]])
        st.dataframe(format_percent_columns(top_rows), use_container_width=True)

    with tab_growth:
        col_up, col_down = st.columns(2)

        growing = growth_table(
            data=filtered,
            metric=metric,
            top_n=top_n,
            ascending=False,
        )
        declining = growth_table(
            data=filtered,
            metric=metric,
            top_n=top_n,
            ascending=True,
        )

        with col_up:
            st.subheader("Fastest growing")
            st.dataframe(format_percent_columns(growing), use_container_width=True)

        with col_down:
            st.subheader("Fastest declining")
            st.dataframe(format_percent_columns(declining), use_container_width=True)

    with tab_geography:
        if geography.empty:
            st.info("No geographic skill data is available.")
        else:
            geo = geography[
                (geography["publication_month"].dt.date >= start_date)
                & (geography["publication_month"].dt.date <= end_date)
                & (geography["skill"].isin(selected_skills))
            ].copy()

            if geo.empty:
                st.info("Select at least one skill with geographic data.")
            else:
                geo_summary = (
                    geo.groupby(
                        [
                            "municipality",
                            "municipality_code",
                            "region",
                            "longitude",
                            "latitude",
                        ],
                        as_index=False,
                    )
                    .agg(
                        mentions=("mentions", "sum"),
                        ads=("ads", "max"),
                        share_of_ads=("share_of_ads", "mean"),
                    )
                    .sort_values(metric, ascending=False)
                )

                render_geography_map(geo_summary=geo_summary, metric=metric)
                st.dataframe(
                    format_percent_columns(
                        geo_summary[
                            [
                                "municipality",
                                "region",
                                "mentions",
                                "ads",
                                "share_of_ads",
                            ]
                        ].head(top_n)
                    ),
                    use_container_width=True,
                )

    with tab_table:
        st.dataframe(
            format_percent_columns(
                filtered.sort_values(
                    ["publication_month", metric],
                    ascending=[False, False],
                )
            ),
            use_container_width=True,
        )
