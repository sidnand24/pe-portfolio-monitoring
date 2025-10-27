import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.append('..')
from db_connection import get_fund_list, get_fund_portfolio

st.title("📊 Fund Overview")

# Set dark mode permanently
st._config.set_option('theme.base', 'dark')

with st.sidebar:
    st.header("Filters")
    
    funds_df = get_fund_list()
    
    if funds_df is not None and not funds_df.empty:
        fund_options = {f"{row['fund_name']} ({row['vintage_year']})": row['fund_id'] 
                       for _, row in funds_df.iterrows()}
        
        selected_fund_label = st.selectbox(
            "Select Fund",
            options=list(fund_options.keys()),
            index=0
        )
        
        selected_fund_id = fund_options[selected_fund_label]
        selected_fund_data = funds_df[funds_df['fund_id'] == selected_fund_id].iloc[0]
    else:
        st.error("No funds available")
        st.stop()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        label="Fund Name",
        value=selected_fund_data['fund_name']
    )

with col2:
    st.metric(
        label="Vintage Year",
        value=int(selected_fund_data['vintage_year'])
    )

st.divider()

st.subheader("Portfolio Companies")

portfolio_df = get_fund_portfolio(selected_fund_id)

if portfolio_df is not None and not portfolio_df.empty:
    
    display_cols = [
        'company_name',
        'industry',
        'investment_date',
        'ownership_type',
        'employees',
        'latest_revenue',
        'latest_ebitda',
        'ebitda_margin',
        'ltm_revenue',
        'ltm_ebitda',
        'net_leverage_ratio',
        'cash_conversion_pct',
        'revenue_yoy_growth_pct',
        'ebitda_yoy_growth_pct'
    ]
    
    display_df = portfolio_df[display_cols].copy()
    
    display_df.columns = [
        'Company',
        'Industry',
        'Investment Date',
        'Ownership',
        'Employees',
        'Revenue (€M)',
        'EBITDA (€M)',
        'EBITDA Margin %',
        'LTM Revenue (€M)',
        'LTM EBITDA (€M)',
        'Net Leverage Ratio',
        'Cash Conv. %',
        'Rev Growth YoY %',
        'EBITDA Growth YoY %'
    ]
    
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        column_config={
            "Investment Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Revenue (€M)": st.column_config.NumberColumn(format="%.2f"),
            "EBITDA (€M)": st.column_config.NumberColumn(format="%.2f"),
            "EBITDA Margin %": st.column_config.NumberColumn(format="%.1f"),
            "LTM Revenue (€M)": st.column_config.NumberColumn(format="%.2f"),
            "LTM EBITDA (€M)": st.column_config.NumberColumn(format="%.2f"),
            "Net Leverage": st.column_config.NumberColumn(format="%.2f"),
            "Cash Conv. %": st.column_config.NumberColumn(format="%.1f"),
            "Rev Growth YoY %": st.column_config.NumberColumn(format="%.1f"),
            "EBITDA Growth YoY %": st.column_config.NumberColumn(format="%.1f"),
        }
    )
    
    with st.expander("📋 Company Details"):
        selected_company = st.selectbox(
            "Select company for details",
            options=portfolio_df['company_name'].tolist()
        )
        
        company_details = portfolio_df[portfolio_df['company_name'] == selected_company].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Legal Name:**", company_details['legal_name'])
            st.write("**Industry:**", company_details['industry'])
            st.write("**Sub-industry:**", company_details['subindustry'])
        
        with col2:
            st.write("**HQ Location:**", f"{company_details['hq_city']}, {company_details['hq_country']}")
            st.write("**Founded:**", int(company_details['founded_year']) if pd.notna(company_details['founded_year']) else "N/A")
            st.write("**Employees:**", int(company_details['employees']) if pd.notna(company_details['employees']) else "N/A")
        
        with col3:
            st.write("**Website:**", company_details['website'] if pd.notna(company_details['website']) else "N/A")
            st.write("**Investment Date:**", company_details['investment_date'])
            st.write("**Ownership:**", company_details['ownership_type'])
    
    st.divider()
    
    st.subheader("Fund-Level Summary")
    
    total_companies = len(portfolio_df)
    total_revenue = portfolio_df['latest_revenue'].sum()
    total_ebitda = portfolio_df['latest_ebitda'].sum()
    avg_margin = portfolio_df['ebitda_margin'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Companies", total_companies)
    
    with col2:
        st.metric("Total Revenue", f"€{total_revenue:.1f}M")
    
    with col3:
        st.metric("Total EBITDA", f"€{total_ebitda:.1f}M")
    
    with col4:
        st.metric("Avg EBITDA Margin", f"{avg_margin:.1f}%")
    
else:
    st.warning("No portfolio data available for this fund")
