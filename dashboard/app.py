
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Supermarket Branch Profit Intelligence Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "50_supermarket_branches.csv"
REPORT_PATH = Path(__file__).resolve().parents[1] / "outputs" / "Supermarket_Branch_Executive_Report.pdf"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df.columns = [c.strip() for c in df.columns]
    df["Total Spend"] = df["Advertisement Spend"] + df["Promotion Spend"] + df["Administration Spend"]
    df["Marketing Spend"] = df["Advertisement Spend"] + df["Promotion Spend"]
    df["Profit Margin Proxy"] = df["Profit"] / df["Total Spend"]
    df["Ad Efficiency"] = df["Profit"] / df["Advertisement Spend"].replace(0, np.nan)
    df["Promotion Efficiency"] = df["Profit"] / df["Promotion Spend"].replace(0, np.nan)
    df["Admin Efficiency"] = df["Profit"] / df["Administration Spend"].replace(0, np.nan)
    return df

def add_styles():
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(180deg, #f7f9fc 0%, #eef2f6 100%);}
    .hero-card {
        background: linear-gradient(135deg, #1f3c88 0%, #3b82f6 100%);
        color: white; padding: 1.2rem 1.4rem; border-radius: 18px;
        box-shadow: 0 8px 24px rgba(31,60,136,0.18); margin-bottom: 1rem;
    }
    .insight-box {
        background: white; border: 1px solid #d7e2eb; border-radius: 16px;
        padding: 1rem 1.1rem; margin-bottom: .8rem;
        box-shadow: 0 6px 16px rgba(0,0,0,0.05);
    }
    .section-title {font-size: 1.05rem; font-weight: 700; color: #243b53; margin-bottom: .35rem;}
    .small-note {color: #627d98; font-size: .88rem;}
    </style>
    """, unsafe_allow_html=True)

def human_money(v):
    return f"${v:,.0f}"

def apply_filters(df):
    st.sidebar.markdown("## Filters")
    states = st.sidebar.multiselect("State", sorted(df["State"].unique()), default=sorted(df["State"].unique()))
    min_profit, max_profit = float(df["Profit"].min()), float(df["Profit"].max())
    profit_range = st.sidebar.slider("Profit Range", min_value=min_profit, max_value=max_profit, value=(min_profit, max_profit))
    min_total, max_total = float(df["Total Spend"].min()), float(df["Total Spend"].max())
    spend_range = st.sidebar.slider("Total Spend Range", min_value=min_total, max_value=max_total, value=(min_total, max_total))

    out = df[
        df["State"].isin(states) &
        df["Profit"].between(profit_range[0], profit_range[1]) &
        df["Total Spend"].between(spend_range[0], spend_range[1])
    ].copy()
    return out

def executive_overview(df):
    total_profit = df["Profit"].sum()
    avg_profit = df["Profit"].mean()
    total_spend = df["Total Spend"].sum()
    avg_margin = df["Profit Margin Proxy"].mean()
    best_state = df.groupby("State")["Profit"].mean().sort_values(ascending=False)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Profit", human_money(total_profit))
    c2.metric("Average Branch Profit", human_money(avg_profit))
    c3.metric("Total Spend", human_money(total_spend))
    c4.metric("Avg Profit / Spend", f"{avg_margin:.2f}")
    c5.metric("Best Avg Profit State", best_state.index[0] if len(best_state) else "n/a")

    col1, col2 = st.columns((1.2,1))
    with col1:
        state_summary = df.groupby("State", as_index=False).agg(
            Branches=("Profit","size"),
            Total_Profit=("Profit","sum"),
            Avg_Profit=("Profit","mean"),
            Avg_Total_Spend=("Total Spend","mean")
        ).sort_values("Avg_Profit", ascending=False)
        fig = px.bar(state_summary, x="State", y="Avg_Profit", color="State", text_auto=".2s",
                     title="Average Profit by State")
        fig.update_layout(height=400, showlegend=False, xaxis_title="", yaxis_title="Average Profit")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(df, x="Total Spend", y="Profit", color="State", size="Marketing Spend",
                          hover_data=["Advertisement Spend","Promotion Spend","Administration Spend"],
                          title="Total Spend vs Profit")
        fig2.update_layout(height=400, xaxis_title="Total Spend", yaxis_title="Profit")
        st.plotly_chart(fig2, use_container_width=True)

    top_branch = df.sort_values("Profit", ascending=False).iloc[0]
    st.markdown(f"""
    <div class="insight-box">
      <div class="section-title">Executive read-out</div>
      <div class="small-note">
      This view covers <b>{len(df)}</b> branches with a combined profit of <b>{human_money(total_profit)}</b>.
      The strongest branch-level profit observed is <b>{human_money(top_branch["Profit"])}</b>, and <b>{best_state.index[0]}</b>
      currently leads on average profitability. The main strategic question is not just where spend is highest, but where spend converts into profit most efficiently.
      </div>
    </div>
    """, unsafe_allow_html=True)

def spend_analysis(df):
    st.markdown("### Spend Drivers of Profit")
    col1, col2 = st.columns(2)

    with col1:
        corr = df[["Advertisement Spend","Promotion Spend","Administration Spend","Profit"]].corr(numeric_only=True)
        corr_long = corr.reset_index().melt(id_vars="index", var_name="Variable", value_name="Correlation")
        fig = px.imshow(corr, text_auto=".2f", aspect="auto", title="Correlation Heatmap")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        spend_long = df.melt(
            id_vars=["State","Profit"],
            value_vars=["Advertisement Spend","Promotion Spend","Administration Spend"],
            var_name="Spend Type", value_name="Spend"
        )
        summary = spend_long.groupby("Spend Type", as_index=False).agg(
            Average_Spend=("Spend","mean"),
            Median_Spend=("Spend","median")
        )
        fig2 = px.bar(summary, x="Spend Type", y="Average_Spend", color="Spend Type",
                      title="Average Spend by Cost Category", text_auto=".2s")
        fig2.update_layout(height=420, showlegend=False, xaxis_title="", yaxis_title="Average Spend")
        st.plotly_chart(fig2, use_container_width=True)

    ad_line = px.scatter(df, x="Advertisement Spend", y="Profit", color="State", trendline="ols",
                         title="Advertisement Spend vs Profit")
    ad_line.update_layout(height=400)
    st.plotly_chart(ad_line, use_container_width=True)

    promo_line = px.scatter(df, x="Promotion Spend", y="Profit", color="State", trendline="ols",
                            title="Promotion Spend vs Profit")
    promo_line.update_layout(height=400)
    st.plotly_chart(promo_line, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
      <div class="section-title">How to read this section</div>
      <div class="small-note">
      These visuals test whether higher spending is associated with higher profit and whether some cost categories appear more commercially productive than others.
      Strong correlation does not prove causation, but it helps identify where deeper budget optimisation analysis should start.
      </div>
    </div>
    """, unsafe_allow_html=True)

def efficiency_and_ranking(df):
    st.markdown("### Branch Efficiency & Opportunity Ranking")
    summary = df.copy()
    summary["Profit Rank"] = summary["Profit"].rank(ascending=False, method="dense")
    summary["Efficiency Rank"] = summary["Profit Margin Proxy"].rank(ascending=False, method="dense")
    summary["Opportunity Segment"] = np.where(
        (summary["Profit"] >= summary["Profit"].median()) & (summary["Profit Margin Proxy"] >= summary["Profit Margin Proxy"].median()),
        "High Profit / High Efficiency",
        np.where(
            (summary["Profit"] < summary["Profit"].median()) & (summary["Profit Margin Proxy"] >= summary["Profit Margin Proxy"].median()),
            "Low Profit / High Efficiency",
            np.where(
                (summary["Profit"] >= summary["Profit"].median()) & (summary["Profit Margin Proxy"] < summary["Profit Margin Proxy"].median()),
                "High Profit / Low Efficiency",
                "Low Profit / Low Efficiency"
            )
        )
    )

    col1, col2 = st.columns((1.3,1))
    with col1:
        fig = px.scatter(summary, x="Total Spend", y="Profit", color="Opportunity Segment", size="Marketing Spend",
                         hover_data=["State","Advertisement Spend","Promotion Spend","Administration Spend","Profit Margin Proxy"],
                         title="Branch Opportunity Matrix")
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        state_eff = summary.groupby("State", as_index=False).agg(
            Avg_Profit=("Profit","mean"),
            Avg_Efficiency=("Profit Margin Proxy","mean"),
            Branches=("Profit","size")
        ).sort_values("Avg_Efficiency", ascending=False)
        fig2 = px.bar(state_eff, x="State", y="Avg_Efficiency", color="State",
                      title="Average Profit-to-Spend Efficiency by State", text_auto=".2f")
        fig2.update_layout(height=430, showlegend=False, xaxis_title="", yaxis_title="Profit / Total Spend")
        st.plotly_chart(fig2, use_container_width=True)

    ranked = summary[["State","Advertisement Spend","Promotion Spend","Administration Spend","Total Spend","Profit","Profit Margin Proxy","Opportunity Segment"]].sort_values(["Profit","Profit Margin Proxy"], ascending=False)
    st.dataframe(ranked, use_container_width=True)

def recommendations(df):
    st.markdown("### Recommendations & Download")
    by_state = df.groupby("State").agg(Avg_Profit=("Profit","mean"), Avg_Eff=("Profit Margin Proxy","mean")).sort_values("Avg_Profit", ascending=False)
    best_state = by_state.index[0] if len(by_state) else "n/a"

    highest_eff = df.sort_values("Profit Margin Proxy", ascending=False).iloc[0]
    highest_profit = df.sort_values("Profit", ascending=False).iloc[0]

    st.markdown(f"""
    <div class="insight-box">
      <div class="section-title">Recommendation snapshot</div>
      <div class="small-note">
      1. Benchmark planning assumptions against <b>{best_state}</b>, which currently leads on average profit in the filtered view.<br>
      2. Review branches similar to the top-efficiency case, where profit is being generated with stronger spend conversion rather than simply larger budgets.<br>
      3. Investigate low-efficiency high-spend branches first, because that is where budget reallocation is most likely to unlock profit gains.
      </div>
    </div>
    """, unsafe_allow_html=True)

    csv = df.sort_values("Profit", ascending=False).to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered branch analysis CSV", data=csv, file_name="filtered_branch_analysis.csv", mime="text/csv", use_container_width=True)


def executive_report_download(df):
    st.markdown("### Executive PDF Report")
    col1, col2 = st.columns((1.2, 1))
    with col1:
        state_rank = df.groupby("State")["Profit"].mean().sort_values(ascending=False)
        best_state = state_rank.index[0] if len(state_rank) else "n/a"
        st.markdown(f"""
        <div class="insight-box">
          <div class="section-title">Board-ready executive brief</div>
          <div class="small-note">
          Download a concise PDF report summarising the strongest state, branch efficiency patterns, key profit drivers,
          and practical recommendations for budget review and performance benchmarking.
          <br><br>
          Current filtered view highlight: <b>{best_state}</b> leads on average branch profit.
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if REPORT_PATH.exists():
            with open(REPORT_PATH, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "Download Executive PDF Report",
                data=pdf_bytes,
                file_name="Supermarket_Branch_Executive_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.caption("Includes executive summary, state performance snapshot, interpretation, and recommendations.")
        else:
            st.warning("Executive PDF report not found in the outputs folder.")


def data_audit(df):
    st.markdown("### Data Audit")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Missing Values", int(df.isna().sum().sum()))
    c3.metric("Duplicate Rows", int(df.duplicated().sum()))
    c4.metric("States", df["State"].nunique())

    audit = pd.DataFrame({
        "Field": df.columns,
        "Missing": df.isna().sum().values,
        "Type": [str(t) for t in df.dtypes.values]
    })
    st.dataframe(audit, use_container_width=True)

    describe = df[["Advertisement Spend","Promotion Spend","Administration Spend","Total Spend","Profit","Profit Margin Proxy"]].describe().T
    st.dataframe(describe, use_container_width=True)

def main():
    add_styles()
    df = load_data()
    df = apply_filters(df)

    st.markdown("""
    <div class="hero-card">
        <h2 style="margin:0;">Supermarket Branch Profit Intelligence Dashboard</h2>
        <p style="margin:0.35rem 0 0 0;">
        A decision-focused branch performance dashboard designed to uncover profit drivers, spending efficiency, and growth opportunities across supermarket locations.
        Created by : Powell A. Ndlovu GIS and Data Analyst
        </p>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No data available for the current filters.")
        st.stop()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Executive Overview", "Spend Drivers", "Efficiency & Ranking", "Data Audit", "Executive Report"
    ])

    with tab1:
        executive_overview(df)
    with tab2:
        spend_analysis(df)
    with tab3:
        efficiency_and_ranking(df)
        recommendations(df)
    with tab4:
        data_audit(df)
    with tab5:
        executive_report_download(df)

if __name__ == "__main__":
    main()
