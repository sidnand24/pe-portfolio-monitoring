{{
    config(
        materialized='table',
        schema='reporting'
    )
}}

with financials as (
    select * from {{ ref('stg_financials_enhanced') }}
),

investments as (
    select 
        inv.company_id,
        f.fund_id,
        f.fund_name,
        f.vintage_year,
        inv.investment_date,
        inv.ownership_type
    from {{ source('raw_data', 'dim_investment') }} inv
    join {{ source('raw_data', 'dim_fund') }} f on inv.fund_id = f.fund_id
),

latest_metrics as (
    select
        company_id,
        max(date) as latest_date
    from financials
    group by company_id
),

performance as (
    select
        f.company_id,
        f.company_name,
        f.industry,
        f.employees,
        i.fund_id,
        i.fund_name,
        i.vintage_year,
        i.ownership_type,
        f.date,
        f.year,
        f.month,
        f.year_month,
        f.revenue,
        f.gross_profit,
        f.gross_margin_pct,
        f.operating_expenses,
        f.opex_pct_of_revenue,
        f.ebitda,
        f.ebitda_margin,
        f.net_income,
        f.cash_from_ops,
        f.capex,
        f.working_capital,
        f.net_debt,
        f.revenue_mom_growth_pct,
        f.ebitda_mom_growth_pct,
        f.revenue_yoy_growth_pct,
        f.ebitda_yoy_growth_pct,
        f.margin_change_bps,
        f.ltm_revenue,
        f.ltm_ebitda,
        f.ytd_revenue,
        f.ytd_ebitda,
        f.cash_conversion_pct,
        f.net_leverage_ratio,
        f.capex_intensity_pct,
        f.revenue_per_employee,
        f.revenue_risk_flag,
        f.margin_risk_flag,
        f.leverage_risk_flag,
        f.liquidity_risk_flag,
        case 
            when lm.latest_date = f.date then true 
            else false 
        end as is_latest_period
    from financials f
    join investments i on f.company_id = i.company_id
    left join latest_metrics lm on f.company_id = lm.company_id
)

select * from performance
