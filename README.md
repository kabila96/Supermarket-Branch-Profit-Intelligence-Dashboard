# Supermarket Branch Profit Intelligence Dashboard

An interactive Streamlit dashboard built from branch-level supermarket data with spending and profit fields.

## Business focus
This project is designed to show how branch spending patterns relate to profitability across states. It helps answer:
- Which spending categories are most associated with profit?
- Which states appear strongest on average profit and efficiency?
- Which branches are high-profit but inefficient, and which are efficient but under-scaled?
- Where should managers focus budget review first?

## Dataset
The dataset contains 50 supermarket branches with:
- Advertisement Spend
- Promotion Spend
- Administration Spend
- State
- Profit

## Dashboard sections
- Executive Overview
- Spend Drivers
- Efficiency & Ranking
- Data Audit

## Run locally
```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```
