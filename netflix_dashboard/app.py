import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Netflix Dashboard", layout="wide")
px.defaults.template = "plotly_white"

st.title("🎬 Netflix Movies & TV Shows Dashboard")
st.caption("Interactive analysis of Netflix content trends (filters + visuals).")

@st.cache_data
def load_data():
    df = pd.read_csv("netflix_titles.csv")


    # Clean date
    df["date_added"] = pd.to_datetime(df["date_added"], errors="coerce")
    df = df.dropna(subset=["date_added"]).copy()
    df["year_added"] = df["date_added"].dt.year

    # Clean country/genre
    df["country"] = df["country"].fillna("Unknown")
    df["listed_in"] = df["listed_in"].fillna("Unknown")
    df["rating"] = df["rating"].fillna("Unknown")

    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")

content_type = st.sidebar.multiselect(
    "Content Type",
    options=sorted(df["type"].dropna().unique()),
    default=sorted(df["type"].dropna().unique())
)

min_year = int(df["year_added"].min())
max_year = int(df["year_added"].max())
year_range = st.sidebar.slider(
    "Year Added Range",
    min_value=min_year,
    max_value=max_year,
    value=(max(min_year, 2015), max_year)
)

# Country filter (Top 30 + Unknown for performance/readability)
country_counts = (
    df["country"].str.split(", ")
    .explode()
    .value_counts()
)
top_country_list = list(country_counts.head(30).index)
if "Unknown" not in top_country_list:
    top_country_list.append("Unknown")

country_selected = st.sidebar.multiselect(
    "Country (Top 30)",
    options=top_country_list,
    default=[]  # empty = no country filtering
)

# Apply filters
filtered_df = df[
    (df["type"].isin(content_type)) &
    (df["year_added"].between(year_range[0], year_range[1]))
].copy()

if country_selected:
    tmp = filtered_df.copy()
    tmp["country_exploded"] = tmp["country"].str.split(", ")
    tmp = tmp.explode("country_exploded")
    filtered_df = tmp[tmp["country_exploded"].isin(country_selected)].copy()

# --- KPI Row ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Titles", len(filtered_df))
c2.metric("Movies", int((filtered_df["type"] == "Movie").sum()))
c3.metric("TV Shows", int((filtered_df["type"] == "TV Show").sum()))
c4.metric("Years Covered", f"{filtered_df['year_added'].min()}–{filtered_df['year_added'].max()}")

st.divider()

# --- Layout: 2 columns for charts ---
left, right = st.columns(2)

# Chart 1: Movies vs TV (Donut)
with left:
    type_counts = filtered_df["type"].value_counts().reset_index()
    type_counts.columns = ["type", "count"]
    fig = px.pie(type_counts, names="type", values="count", hole=0.55,
                 title="🍩 Movies vs TV Shows")
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)

# Chart 2: Growth over time
with right:
    growth = filtered_df["year_added"].value_counts().sort_index().reset_index()
    growth.columns = ["year_added", "titles_added"]
    fig2 = px.line(growth, x="year_added", y="titles_added", markers=True,
                   title="📈 Titles Added Over Time")
    st.plotly_chart(fig2, use_container_width=True)

# Chart 3: Top countries
st.subheader("🌍 Geographic & Category Insights")
c5, c6 = st.columns(2)

with c5:
    top_countries = (
        filtered_df["country"].str.split(", ")
        .explode().value_counts()
        .drop(index=["Unknown"], errors="ignore")
        .head(10).reset_index()
    )
    top_countries.columns = ["country", "titles"]
    top_countries = top_countries.sort_values("titles", ascending=True)

    fig3 = px.bar(top_countries, x="titles", y="country", orientation="h",
                  text="titles", title="Top 10 Content-Producing Countries")
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Top genres
with c6:
    top_genres = (
        filtered_df["listed_in"].str.split(", ")
        .explode().value_counts()
        .drop(index=["Unknown"], errors="ignore")
        .head(12).reset_index()
    )
    top_genres.columns = ["genre", "count"]
    top_genres = top_genres.sort_values("count", ascending=True)

    fig4 = px.bar(top_genres, x="count", y="genre", orientation="h",
                  text="count", title="Top Genres (Top 12)")
    fig4.update_traces(textposition="outside")
    st.plotly_chart(fig4, use_container_width=True)

# Chart 5: Ratings distribution
c7, c8 = st.columns(2)

with c7:
    rating_counts = filtered_df["rating"].value_counts().reset_index()
    rating_counts.columns = ["rating", "count"]
    fig5 = px.bar(rating_counts, x="rating", y="count", text="count",
                  title="🔞 Ratings Distribution")
    fig5.update_traces(textposition="outside")
    st.plotly_chart(fig5, use_container_width=True)

# Chart 6: Content type mix over time (stacked area)
with c8:
    year_type = filtered_df.groupby(["year_added", "type"]).size().reset_index(name="titles")
    fig6 = px.area(year_type, x="year_added", y="titles", color="type",
                   title="🎞️ Content Mix Over Time (Movies vs TV Shows)")
    st.plotly_chart(fig6, use_container_width=True)

st.divider()
st.caption("Tip: Use the sidebar filters to explore how trends change by country, year range, and content type.")
