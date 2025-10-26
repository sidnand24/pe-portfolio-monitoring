-- PE Portfolio Monitoring Database - Star Schema

-- ============================================
-- CREATE SCHEMA
-- ============================================
CREATE SCHEMA IF NOT EXISTS raw_data;

-- Drop existing tables if they exist (in reverse dependency order)
DROP TABLE IF EXISTS raw_data.fact_comments CASCADE;
DROP TABLE IF EXISTS raw_data.fact_budget CASCADE;
DROP TABLE IF EXISTS raw_data.fact_kpis_monthly CASCADE;
DROP TABLE IF EXISTS raw_data.fact_financials_monthly CASCADE;
DROP TABLE IF EXISTS raw_data.dim_investment CASCADE;
DROP TABLE IF EXISTS raw_data.dim_kpi CASCADE;
DROP TABLE IF EXISTS raw_data.dim_date CASCADE;
DROP TABLE IF EXISTS raw_data.dim_fund CASCADE;
DROP TABLE IF EXISTS raw_data.dim_company CASCADE;

-- ============================================
-- DIMENSION TABLES
-- ============================================

-- Dimension: Company
CREATE TABLE raw_data.dim_company (
    company_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    industry VARCHAR(100),
    subindustry VARCHAR(100),
    hq_city VARCHAR(100),
    hq_country VARCHAR(100),
    website VARCHAR(255),
    founded_year INTEGER,
    employees INTEGER
);

-- Dimension: Fund
CREATE TABLE raw_data.dim_fund (
    fund_id VARCHAR(50) PRIMARY KEY,
    fund_name VARCHAR(255) NOT NULL,
    vintage_year INTEGER
);

-- Dimension: Date
CREATE TABLE raw_data.dim_date (
    date_id INTEGER PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    year_month VARCHAR(7) NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_month_end BOOLEAN NOT NULL,
    is_quarter_end BOOLEAN NOT NULL,
    is_year_end BOOLEAN NOT NULL
);

-- Dimension: KPI
CREATE TABLE raw_data.dim_kpi (
    kpi_id SERIAL PRIMARY KEY,
    kpi_name VARCHAR(255) NOT NULL UNIQUE
);

-- Dimension: Investment (Company-Fund relationships - portfolio composition)
CREATE TABLE raw_data.dim_investment (
    investment_id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    fund_id VARCHAR(50) NOT NULL,
    investment_date DATE,
    ownership_type VARCHAR(50),
    FOREIGN KEY (company_id) REFERENCES raw_data.dim_company(company_id),
    FOREIGN KEY (fund_id) REFERENCES raw_data.dim_fund(fund_id),
    UNIQUE (company_id, fund_id)
);

-- ============================================
-- FACT TABLES
-- ============================================

-- Fact: Monthly Financials (EUR millions)
CREATE TABLE raw_data.fact_financials_monthly (
    financial_id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    date_id INTEGER NOT NULL,
    revenue NUMERIC(15, 2),
    gross_profit NUMERIC(15, 2),
    cogs NUMERIC(15, 2),
    ebitda NUMERIC(15, 2),
    depreciation NUMERIC(15, 2),
    amortization NUMERIC(15, 2),
    ebita NUMERIC(15, 2),
    ebit NUMERIC(15, 2),
    net_income NUMERIC(15, 2),
    cash_from_ops NUMERIC(15, 2),
    capex NUMERIC(15, 2),
    ebitda_margin_pct NUMERIC(5, 2),
    working_capital NUMERIC(15, 2),
    net_debt NUMERIC(15, 2),
    currency VARCHAR(10) DEFAULT 'EUR',
    FOREIGN KEY (company_id) REFERENCES raw_data.dim_company(company_id),
    FOREIGN KEY (date_id) REFERENCES raw_data.dim_date(date_id),
    UNIQUE (company_id, date_id)
);

-- Fact: Monthly KPIs
CREATE TABLE raw_data.fact_kpis_monthly (
    kpi_fact_id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    date_id INTEGER NOT NULL,
    kpi_id INTEGER NOT NULL,
    kpi_value NUMERIC(15, 4),
    FOREIGN KEY (company_id) REFERENCES raw_data.dim_company(company_id),
    FOREIGN KEY (date_id) REFERENCES raw_data.dim_date(date_id),
    FOREIGN KEY (kpi_id) REFERENCES raw_data.dim_kpi(kpi_id),
    UNIQUE (company_id, date_id, kpi_id)
);

-- Fact: Annual Budget
CREATE TABLE raw_data.fact_budget (
    budget_id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    fiscal_year INTEGER NOT NULL,
    currency VARCHAR(10),
    revenue_budget NUMERIC(15, 2),
    cogs_budget NUMERIC(15, 2),
    gross_profit_budget NUMERIC(15, 2),
    ebitda_budget NUMERIC(15, 2),
    depreciation_budget NUMERIC(15, 2),
    amortization_budget NUMERIC(15, 2),
    ebita_budget NUMERIC(15, 2),
    ebit_budget NUMERIC(15, 2),
    net_income_budget NUMERIC(15, 2),
    cash_from_ops_budget NUMERIC(15, 2),
    capex_budget NUMERIC(15, 2),
    working_capital_budget NUMERIC(15, 2),
    net_debt_budget NUMERIC(15, 2),
    FOREIGN KEY (company_id) REFERENCES raw_data.dim_company(company_id),
    UNIQUE (company_id, fiscal_year)
);

-- Fact: Comments
CREATE TABLE raw_data.fact_comments (
    comment_id SERIAL PRIMARY KEY,
    company_id VARCHAR(50) NOT NULL,
    date_id INTEGER NOT NULL,
    author VARCHAR(255) NOT NULL,
    role VARCHAR(100),
    comment_text TEXT,
    FOREIGN KEY (company_id) REFERENCES raw_data.dim_company(company_id),
    FOREIGN KEY (date_id) REFERENCES raw_data.dim_date(date_id)
);

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON SCHEMA raw_data IS 'Raw data schema containing source tables for PE portfolio monitoring';
COMMENT ON TABLE raw_data.dim_company IS 'Company dimension containing portfolio company master data';
COMMENT ON TABLE raw_data.dim_fund IS 'Fund dimension containing PE fund information';
COMMENT ON TABLE raw_data.dim_date IS 'Date dimension for time-based analysis';
COMMENT ON TABLE raw_data.dim_kpi IS 'KPI dimension containing unique KPI names';
COMMENT ON TABLE raw_data.dim_investment IS 'Investment dimension tracking company-fund portfolio composition';
COMMENT ON TABLE raw_data.fact_financials_monthly IS 'Fact table containing monthly financial metrics in EUR millions';
COMMENT ON TABLE raw_data.fact_kpis_monthly IS 'Fact table containing monthly KPI values (varies by company)';
COMMENT ON TABLE raw_data.fact_budget IS 'Fact table containing annual budget data';
COMMENT ON TABLE raw_data.fact_comments IS 'Fact table containing portfolio company comments and notes';
