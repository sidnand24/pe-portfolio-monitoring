import streamlit as st

st.set_page_config(
    page_title="PE Portfolio Monitoring",
    page_icon=":material/finance:",
    layout="wide",
    initial_sidebar_state="expanded"
)

page_fund_overview = st.Page(
    "views/fund_overview.py",
    title="Fund Overview",
    icon=":material/account_balance:",
    default=True,
)

page_company_deepdive = st.Page(
    "views/company_deepdive.py",
    title="Company Deep Dive",
    icon=":material/analytics:",
)

pg = st.navigation(pages=[page_fund_overview, page_company_deepdive])

pg.run()
