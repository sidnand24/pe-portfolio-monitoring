"""
PE Portfolio Monitoring - ETL Script
Loads data from Excel into PostgreSQL star schema
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'my_local_db'),
    'user': os.getenv('POSTGRES_USER', 'my_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'my_password'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

EXCEL_FILE = './portfolio_monitoring_case_data (1).xlsx'

def get_db_connection():
    """Establish database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def generate_date_dimension(start_year=2023, end_year=2024):
    """Generate date dimension for monthly periods"""
    dates = []
    
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Use first day of month as the representative date
            date = datetime(year, month, 1)
            date_id = int(date.strftime('%Y%m%d'))
            
            # Calculate quarter
            quarter = (month - 1) // 3 + 1
            
            # Check if month end
            if month == 12:
                next_month = datetime(year + 1, 1, 1)
            else:
                next_month = datetime(year, month + 1, 1)
            is_month_end = (next_month - timedelta(days=1)).day == date.day
            
            # Check if quarter end
            is_quarter_end = month in [3, 6, 9, 12]
            
            # Check if year end
            is_year_end = month == 12
            
            dates.append({
                'date_id': date_id,
                'date': date,
                'year': year,
                'month': month,
                'quarter': quarter,
                'year_month': date.strftime('%Y-%m'),
                'month_name': date.strftime('%B'),
                'day_of_week': date.weekday(),
                'is_month_end': is_month_end,
                'is_quarter_end': is_quarter_end,
                'is_year_end': is_year_end
            })
    
    return pd.DataFrame(dates)

def year_month_to_date_id(year_month_str):
    """Convert YYYY-MM string to date_id (YYYYMMDD format)"""
    if pd.isna(year_month_str):
        return None
    try:
        date = datetime.strptime(str(year_month_str), '%Y-%m')
        return int(date.strftime('%Y%m%d'))
    except:
        return None

def load_dimension_companies(conn, df_companies):
    """Load company dimension"""
    print("Loading dim_company...")
    
    cursor = conn.cursor()
    
    # Prepare data
    companies_data = []
    for _, row in df_companies.iterrows():
        companies_data.append((
            row['CompanyID'],
            row['CompanyName'],
            row.get('LegalName'),
            row.get('Industry'),
            row.get('Subindustry'),
            row.get('HQ_City'),
            row.get('HQ_Country'),
            row.get('Website'),
            int(row['FoundedYear']) if pd.notna(row.get('FoundedYear')) else None,
            int(row['Employees']) if pd.notna(row.get('Employees')) else None
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.dim_company (company_id, company_name, legal_name, industry, 
                                 subindustry, hq_city, hq_country, website, 
                                 founded_year, employees)
        VALUES %s
        ON CONFLICT (company_id) DO NOTHING
    """
    execute_values(cursor, insert_query, companies_data)
    conn.commit()
    print(f"Loaded {len(companies_data)} companies")

def load_dimension_funds(conn, df_funds):
    """Load fund dimension"""
    print("Loading dim_fund...")
    
    cursor = conn.cursor()
    
    # Prepare data
    funds_data = []
    for _, row in df_funds.iterrows():
        funds_data.append((
            row['FundID'],
            row['FundName'],
            int(row['VintageYear']) if pd.notna(row.get('VintageYear')) else None
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.dim_fund (fund_id, fund_name, vintage_year)
        VALUES %s
        ON CONFLICT (fund_id) DO NOTHING
    """
    execute_values(cursor, insert_query, funds_data)
    conn.commit()
    print(f"Loaded {len(funds_data)} funds")

def load_dimension_date(conn, df_date):
    """Load date dimension"""
    print("Loading dim_date...")
    
    cursor = conn.cursor()
    
    # Prepare data
    date_data = []
    for _, row in df_date.iterrows():
        date_data.append((
            row['date_id'],
            row['date'],
            row['year'],
            row['month'],
            row['quarter'],
            row['year_month'],
            row['month_name'],
            row['day_of_week'],
            row['is_month_end'],
            row['is_quarter_end'],
            row['is_year_end']
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.dim_date (date_id, date, year, month, quarter, year_month,
                              month_name, day_of_week, is_month_end, 
                              is_quarter_end, is_year_end)
        VALUES %s
        ON CONFLICT (date_id) DO NOTHING
    """
    execute_values(cursor, insert_query, date_data)
    conn.commit()
    print(f"Loaded {len(date_data)} date records")

def load_dimension_kpis(conn, df_kpis):
    """Load KPI dimension from unique KPI names"""
    print("Loading dim_kpi...")
    
    cursor = conn.cursor()
    
    # Get unique KPI names
    unique_kpis = df_kpis['KPI_Name'].dropna().unique()
    
    # Insert data
    for kpi_name in unique_kpis:
        cursor.execute("""
            INSERT INTO raw_data.dim_kpi (kpi_name)
            VALUES (%s)
            ON CONFLICT (kpi_name) DO NOTHING
        """, (kpi_name,))
    
    conn.commit()
    print(f"Loaded {len(unique_kpis)} unique KPIs")

def load_dimension_investments(conn, df_investments):
    """Load investment dimension (company-fund relationships)"""
    print("Loading dim_investment...")
    
    cursor = conn.cursor()
    
    # Prepare data
    investments_data = []
    for _, row in df_investments.iterrows():
        # Convert investment date to actual date (not date_id)
        try:
            inv_date = pd.to_datetime(row['InvestmentDate']).date()
        except:
            inv_date = None
        
        investments_data.append((
            row['CompanyID'],
            row['FundID'],
            inv_date,
            row.get('OwnershipType')
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.dim_investment (company_id, fund_id, investment_date, ownership_type)
        VALUES %s
        ON CONFLICT (company_id, fund_id) DO NOTHING
    """
    execute_values(cursor, insert_query, investments_data)
    conn.commit()
    print(f"Loaded {len(investments_data)} investments")

def load_fact_financials(conn, df_financials):
    """Load financial facts"""
    print("Loading fact_financials_monthly...")
    
    cursor = conn.cursor()
    
    # Prepare data
    financials_data = []
    for _, row in df_financials.iterrows():
        date_id = year_month_to_date_id(row.get('YearMonth'))
        if date_id is None:
            continue
        
        financials_data.append((
            row['CompanyID'],
            date_id,
            float(row['Revenue']) if pd.notna(row.get('Revenue')) else None,
            float(row['COGS']) if pd.notna(row.get('COGS')) else None,
            float(row['GrossProfit']) if pd.notna(row.get('GrossProfit')) else None,
            float(row['EBITDA']) if pd.notna(row.get('EBITDA')) else None,
            float(row['Depreciation']) if pd.notna(row.get('Depreciation')) else None,
            float(row['Amortization']) if pd.notna(row.get('Amortization')) else None,
            float(row['EBITA']) if pd.notna(row.get('EBITA')) else None,
            float(row['EBIT']) if pd.notna(row.get('EBIT')) else None,
            float(row['NetIncome']) if pd.notna(row.get('NetIncome')) else None,
            float(row['CashFromOps']) if pd.notna(row.get('CashFromOps')) else None,
            float(row['Capex']) if pd.notna(row.get('Capex')) else None,
            float(row['EBITDA_Margin_%']) if pd.notna(row.get('EBITDA_Margin_%')) else None,
            float(row['WorkingCapital']) if pd.notna(row.get('WorkingCapital')) else None,
            float(row['NetDebt']) if pd.notna(row.get('NetDebt')) else None,
            'EUR'
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.fact_financials_monthly 
        (company_id, date_id, revenue, cogs, gross_profit, ebitda, depreciation,
         amortization, ebita, ebit, net_income, cash_from_ops, capex, 
         ebitda_margin_pct, working_capital, net_debt, currency)
        VALUES %s
        ON CONFLICT (company_id, date_id) DO NOTHING
    """
    execute_values(cursor, insert_query, financials_data)
    conn.commit()
    print(f"Loaded {len(financials_data)} financial records")

def load_fact_kpis(conn, df_kpis):
    """Load KPI facts"""
    print("Loading fact_kpis_monthly...")
    
    cursor = conn.cursor()
    
    # First, get KPI ID mapping
    cursor.execute("SELECT kpi_id, kpi_name FROM raw_data.dim_kpi")
    kpi_mapping = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Prepare data
    kpis_data = []
    for _, row in df_kpis.iterrows():
        date_id = year_month_to_date_id(row.get('YearMonth'))
        kpi_name = row.get('KPI_Name')
        
        if date_id is None or kpi_name is None or kpi_name not in kpi_mapping:
            continue
        
        kpis_data.append((
            row['CompanyID'],
            date_id,
            kpi_mapping[kpi_name],
            float(row['KPI_Value']) if pd.notna(row.get('KPI_Value')) else None
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.fact_kpis_monthly (company_id, date_id, kpi_id, kpi_value)
        VALUES %s
        ON CONFLICT (company_id, date_id, kpi_id) DO NOTHING
    """
    execute_values(cursor, insert_query, kpis_data)
    conn.commit()
    print(f"Loaded {len(kpis_data)} KPI records")

def load_fact_budget(conn, df_budget):
    """Load budget facts"""
    print("Loading fact_budget...")
    
    cursor = conn.cursor()
    
    # Prepare data
    budget_data = []
    for _, row in df_budget.iterrows():
        budget_data.append((
            row['CompanyID'],
            int(row['FiscalYear']) if pd.notna(row.get('FiscalYear')) else None,
            row.get('Currency'),
            float(row['Revenue_Budget']) if pd.notna(row.get('Revenue_Budget')) else None,
            float(row['COGS_Budget']) if pd.notna(row.get('COGS_Budget')) else None,
            float(row['GrossProfit_Budget']) if pd.notna(row.get('GrossProfit_Budget')) else None,
            float(row['EBITDA_Budget']) if pd.notna(row.get('EBITDA_Budget')) else None,
            float(row['Depreciation_Budget']) if pd.notna(row.get('Depreciation_Budget')) else None,
            float(row['Amortization_Budget']) if pd.notna(row.get('Amortization_Budget')) else None,
            float(row['EBITA_Budget']) if pd.notna(row.get('EBITA_Budget')) else None,
            float(row['EBIT_Budget']) if pd.notna(row.get('EBIT_Budget')) else None,
            float(row['NetIncome_Budget']) if pd.notna(row.get('NetIncome_Budget')) else None,
            float(row['CashFromOps_Budget']) if pd.notna(row.get('CashFromOps_Budget')) else None,
            float(row['Capex_Budget']) if pd.notna(row.get('Capex_Budget')) else None,
            float(row['WorkingCapital_Budget']) if pd.notna(row.get('WorkingCapital_Budget')) else None,
            float(row['NetDebt_Budget']) if pd.notna(row.get('NetDebt_Budget')) else None
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.fact_budget 
        (company_id, fiscal_year, currency, revenue_budget, cogs_budget,
         gross_profit_budget, ebitda_budget, depreciation_budget, 
         amortization_budget, ebita_budget, ebit_budget, net_income_budget,
         cash_from_ops_budget, capex_budget, working_capital_budget, net_debt_budget)
        VALUES %s
        ON CONFLICT (company_id, fiscal_year) DO NOTHING
    """
    execute_values(cursor, insert_query, budget_data)
    conn.commit()
    print(f"Loaded {len(budget_data)} budget records")

def load_fact_comments(conn, df_comments):
    """Load comment facts"""
    print("Loading fact_comments...")
    
    cursor = conn.cursor()
    
    # Prepare data
    comments_data = []
    for _, row in df_comments.iterrows():
        try:
            comment_date = pd.to_datetime(row['CommentDate'])
            # Use first day of month
            date_id = int(datetime(comment_date.year, comment_date.month, 1).strftime('%Y%m%d'))
        except:
            continue
        
        comments_data.append((
            row['CompanyID'],
            date_id,
            row['Author'],
            row.get('Role'),
            row.get('Comment')
        ))
    
    # Insert data
    insert_query = """
        INSERT INTO raw_data.fact_comments (company_id, date_id, author, role, comment_text)
        VALUES %s
    """
    execute_values(cursor, insert_query, comments_data)
    conn.commit()
    print(f"Loaded {len(comments_data)} comments")

def main():
    """Main ETL process"""
    print("=" * 60)
    print("PE Portfolio Monitoring - ETL Process")
    print("=" * 60)
    
    # Load Excel data
    print("\n1. Reading Excel file...")
    try:
        dfs = pd.read_excel(EXCEL_FILE, sheet_name=None)
        df_companies = dfs['Companies']
        df_funds = dfs['Funds']
        df_investments = dfs['Investments']
        df_financials = dfs['Financials_Monthly']
        df_kpis = dfs['KPIs_Monthly']
        df_budget = dfs['Annual_Budget']
        df_comments = dfs['Comments']
        print("Excel file loaded successfully")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)
    
    # Connect to database
    print("\n2. Connecting to PostgreSQL...")
    conn = get_db_connection()
    print("Connected to database")
    
    try:
        # Generate date dimension
        print("\n3. Generating date dimension...")
        df_date = generate_date_dimension(2023, 2025)
        print(f"Generated {len(df_date)} date records")
        
        # Load dimensions
        print("\n4. Loading dimension tables...")
        load_dimension_companies(conn, df_companies)
        load_dimension_funds(conn, df_funds)
        load_dimension_date(conn, df_date)
        load_dimension_kpis(conn, df_kpis)
        load_dimension_investments(conn, df_investments)
        
        # Load facts
        print("\n5. Loading fact tables...")
        load_fact_financials(conn, df_financials)
        load_fact_kpis(conn, df_kpis)
        load_fact_budget(conn, df_budget)
        load_fact_comments(conn, df_comments)
        
        print("\n" + "=" * 60)
        print("ETL Process Completed Successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during ETL process: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
