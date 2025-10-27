{{
    config(
        materialized='table',
        schema='dbt_stg'
    )
}}

with budget as (
    select * from {{ source('raw_data', 'fact_budget') }}
),

companies as (
    select * from {{ source('raw_data', 'dim_company') }}
),

dates as (
    select * from {{ source('raw_data', 'dim_date') }}
    where year in (2023, 2024)
),

budget_monthly as (
    select
        b.company_id,
        c.company_name,
        d.date,
        d.year,
        d.month,
        d.year_month,
        b.fiscal_year,
        b.currency,
        round((b.revenue_budget / 12)::numeric, 2) as revenue_budget_monthly,
        round((b.cogs_budget / 12)::numeric, 2) as cogs_budget_monthly,
        round((b.gross_profit_budget / 12)::numeric, 2) as gross_profit_budget_monthly,
        round((b.ebitda_budget / 12)::numeric, 2) as ebitda_budget_monthly,
        round((b.depreciation_budget / 12)::numeric, 2) as depreciation_budget_monthly,
        round((b.amortization_budget / 12)::numeric, 2) as amortization_budget_monthly,
        round((b.ebita_budget / 12)::numeric, 2) as ebita_budget_monthly,
        round((b.ebit_budget / 12)::numeric, 2) as ebit_budget_monthly,
        round((b.net_income_budget / 12)::numeric, 2) as net_income_budget_monthly,
        round((b.cash_from_ops_budget / 12)::numeric, 2) as cash_from_ops_budget_monthly,
        round((b.capex_budget / 12)::numeric, 2) as capex_budget_monthly,
        round((b.working_capital_budget / 12)::numeric, 2) as working_capital_budget_monthly,
        round((b.net_debt_budget / 12)::numeric, 2) as net_debt_budget_monthly,
        b.revenue_budget as revenue_budget_annual,
        b.ebitda_budget as ebitda_budget_annual
    from budget b
    join companies c on b.company_id = c.company_id
    cross join dates d
    where d.year = b.fiscal_year
),

with_ytd_budget as (
    select
        *,
        sum(revenue_budget_monthly) over (
            partition by company_id, year 
            order by date 
            rows between unbounded preceding and current row
        ) as ytd_revenue_budget,
        
        sum(ebitda_budget_monthly) over (
            partition by company_id, year 
            order by date 
            rows between unbounded preceding and current row
        ) as ytd_ebitda_budget,
        
        sum(cash_from_ops_budget_monthly) over (
            partition by company_id, year 
            order by date 
            rows between unbounded preceding and current row
        ) as ytd_cash_from_ops_budget,
        
        sum(capex_budget_monthly) over (
            partition by company_id, year 
            order by date 
            rows between unbounded preceding and current row
        ) as ytd_capex_budget
    from budget_monthly
)

select * from with_ytd_budget
