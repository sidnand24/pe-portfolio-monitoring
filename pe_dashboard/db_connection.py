import pandas as pd
import streamlit as st
from typing import Optional
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

@st.cache_resource
def get_db_engine():
    """Create and cache SQLAlchemy engine"""
    try:
        connection_string = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
            f"{os.getenv('POSTGRES_PORT', '5432')}/"
            f"{os.getenv('POSTGRES_DB', 'portfolio_monitoring')}"
        )
        engine = create_engine(connection_string, pool_pre_ping=True)
        return engine
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

@st.cache_data(ttl=300)
def query_data(query: str) -> Optional[pd.DataFrame]:
    """Execute query and return DataFrame"""
    engine = get_db_engine()
    if engine is None:
        return None
    
    try:
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return None

def get_fund_list():
    """Get list of all funds"""
    query = """
        SELECT DISTINCT fund_id, fund_name, vintage_year
        FROM reporting.mart_fund_overview
        ORDER BY fund_name
    """
    return query_data(query)

def get_company_list(fund_id: Optional[str] = None):
    """Get list of companies, optionally filtered by fund"""
    if fund_id:
        query = f"""
            SELECT DISTINCT company_id, company_name
            FROM reporting.mart_fund_overview
            WHERE fund_id = '{fund_id}'
            ORDER BY company_name
        """
    else:
        query = """
            SELECT DISTINCT company_id, company_name
            FROM reporting.mart_company_performance
            ORDER BY company_name
        """
    return query_data(query)

def get_fund_portfolio(fund_id: str):
    """Get all portfolio companies for a fund"""
    query = f"""
        SELECT *
        FROM reporting.mart_fund_overview
        WHERE fund_id = '{fund_id}'
        ORDER BY company_name
    """
    return query_data(query)

def get_company_financials(company_id: str):
    """Get financial metrics for a company"""
    query = f"""
        SELECT *
        FROM reporting.mart_company_performance
        WHERE company_id = '{company_id}'
        ORDER BY date
    """
    return query_data(query)

def get_company_budget_variance(company_id: str):
    """Get budget variance analysis for a company"""
    query = f"""
        SELECT *
        FROM reporting.mart_budget_variance
        WHERE company_id = '{company_id}'
        ORDER BY date
    """
    return query_data(query)

def get_company_kpis(company_id: str):
    """Get KPI data for a company"""
    query = f"""
        SELECT *
        FROM dbt_stg.stg_kpis_analysis
        WHERE company_id = '{company_id}'
        ORDER BY date
    """
    return query_data(query)

def get_company_comments(company_id: str):
    """Get comments for a company"""
    query = f"""
        SELECT *
        FROM reporting.mart_comments
        WHERE company_id = '{company_id}'
        ORDER BY comment_date DESC
    """
    return query_data(query)
