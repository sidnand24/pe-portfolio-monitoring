{{
    config(
        materialized='table',
        schema='reporting'
    )
}}

with investments as (
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

companies as (
    select * from {{ source('raw_data', 'dim_company') }}
),

latest_financials as (
    select 
        f.*,
        row_number() over (partition by f.company_id order by f.date desc) as rn
    from {{ ref('stg_financials_enhanced') }} f
),

fund_portfolio as (
    select
        i.fund_id,
        i.fund_name,
        i.vintage_year,
        i.company_id,
        i.investment_date,
        i.ownership_type,
        c.company_name,
        c.legal_name,
        c.industry,
        c.subindustry,
        c.hq_city,
        c.hq_country,
        c.website,
        c.founded_year,
        c.employees,
        f.revenue as latest_revenue,
        f.ebitda as latest_ebitda,
        f.ebitda_margin,
        f.ltm_revenue,
        f.ltm_ebitda,
        f.net_leverage_ratio,
        f.cash_conversion_pct,
        f.revenue_yoy_growth_pct,
        f.ebitda_yoy_growth_pct
    from investments i
    join companies c on i.company_id = c.company_id
    left join latest_financials f on i.company_id = f.company_id and f.rn = 1
)

select * from fund_portfolio
