{{
    config(
        materialized='table',
        schema='dbt_stg'
    )
}}

with financials as (
    select * from {{ source('raw_data', 'fact_financials_monthly') }}
),

companies as (
    select * from {{ source('raw_data', 'dim_company') }}
),

dates as (
    select * from {{ source('raw_data', 'dim_date') }}
),

base_data as (
    select
        f.company_id,
        c.company_name,
        c.industry,
        c.employees,
        d.date,
        d.year,
        d.month,
        d.quarter,
        d.year_month,
        f.revenue,
        f.cogs,
        f.gross_profit,
        f.ebitda,
        f.depreciation,
        f.amortization,
        f.ebita,
        f.ebit,
        f.net_income,
        f.cash_from_ops,
        f.capex,
        f.ebitda_margin_pct as ebitda_margin,
        f.working_capital,
        f.net_debt,
        f.currency
    from financials f
    join companies c on f.company_id = c.company_id
    join dates d on f.date_id = d.date_id
),

with_lag as (
    select
        *,
        -- Previous month values for MoM calculations
        lag(revenue, 1) over (partition by company_id order by date) as revenue_prev_month,
        lag(ebitda, 1) over (partition by company_id order by date) as ebitda_prev_month,
        lag(ebitda_margin, 1) over (partition by company_id order by date) as margin_prev_month,
        
        -- Same month last year for YoY calculations
        lag(revenue, 12) over (partition by company_id order by date) as revenue_prev_year,
        lag(ebitda, 12) over (partition by company_id order by date) as ebitda_prev_year
    from base_data
),

with_rolling as (
    select
        *,
        -- LTM (Last Twelve Months) metrics
        sum(revenue) over (
            partition by company_id 
            order by date 
            rows between 11 preceding and current row
        ) as ltm_revenue,
        
        sum(ebitda) over (
            partition by company_id 
            order by date 
            rows between 11 preceding and current row
        ) as ltm_ebitda,
        
        sum(cash_from_ops) over (
            partition by company_id 
            order by date 
            rows between 11 preceding and current row
        ) as ltm_cash_from_ops,
        
        sum(capex) over (
            partition by company_id 
            order by date 
            rows between 11 preceding and current row
        ) as ltm_capex,
        
        -- Count months for LTM validation
        count(*) over (
            partition by company_id 
            order by date 
            rows between 11 preceding and current row
        ) as months_count
    from with_lag
),

with_ytd as (
    select
        *,
        -- YTD (Year to Date) metrics for current fiscal year
        case 
            when year = (select max(year) from base_data) then
                sum(revenue) over (
                    partition by company_id, year 
                    order by date 
                    rows between unbounded preceding and current row
                )
            else null
        end as ytd_revenue,
        
        case 
            when year = (select max(year) from base_data) then
                sum(ebitda) over (
                    partition by company_id, year 
                    order by date 
                    rows between unbounded preceding and current row
                )
            else null
        end as ytd_ebitda,
        
        case 
            when year = (select max(year) from base_data) then
                sum(cash_from_ops) over (
                    partition by company_id, year 
                    order by date 
                    rows between unbounded preceding and current row
                )
            else null
        end as ytd_cash_from_ops,
        
        case 
            when year = (select max(year) from base_data) then
                sum(capex) over (
                    partition by company_id, year 
                    order by date 
                    rows between unbounded preceding and current row
                )
            else null
        end as ytd_capex
    from with_rolling
),

calculations as (
    select
        company_id,
        company_name,
        industry,
        employees,
        date,
        year,
        month,
        quarter,
        year_month,
        
        -- Base metrics
        revenue,
        cogs,
        gross_profit,
        ebitda,
        depreciation,
        amortization,
        ebita,
        ebit,
        net_income,
        cash_from_ops,
        capex,
        ebitda_margin,
        working_capital,
        net_debt,
        currency,
        
        -- Growth rates
        case 
            when revenue_prev_month > 0 then
                round(((revenue - revenue_prev_month) / revenue_prev_month * 100)::numeric, 2)
            else null
        end as revenue_mom_growth_pct,
        
        case 
            when ebitda_prev_month > 0 then
                round(((ebitda - ebitda_prev_month) / ebitda_prev_month * 100)::numeric, 2)
            else null
        end as ebitda_mom_growth_pct,
        
        case 
            when revenue_prev_year > 0 then
                round(((revenue - revenue_prev_year) / revenue_prev_year * 100)::numeric, 2)
            else null
        end as revenue_yoy_growth_pct,
        
        case 
            when ebitda_prev_year > 0 then
                round(((ebitda - ebitda_prev_year) / ebitda_prev_year * 100)::numeric, 2)
            else null
        end as ebitda_yoy_growth_pct,
        
        -- Margin expansion (in basis points)
        case
            when margin_prev_month is not null then
                round(((ebitda_margin - margin_prev_month) * 100)::numeric, 0)
            else null
        end as margin_change_bps,
        
        -- LTM metrics (only if we have 12 months of data)
        case when months_count = 12 then ltm_revenue else null end as ltm_revenue,
        case when months_count = 12 then ltm_ebitda else null end as ltm_ebitda,
        case when months_count = 12 then ltm_cash_from_ops else null end as ltm_cash_from_ops,
        case when months_count = 12 then ltm_capex else null end as ltm_capex,
        
        -- YTD metrics
        ytd_revenue,
        ytd_ebitda,
        ytd_cash_from_ops,
        ytd_capex,
        
        -- PE-specific metrics
        case 
            when ebitda > 0 then
                round((cash_from_ops / ebitda * 100)::numeric, 1)
            else null
        end as cash_conversion_pct,
        
        case 
            when ltm_ebitda > 0 and months_count = 12 then
                round((net_debt / ltm_ebitda)::numeric, 2)
            else null
        end as net_leverage_ratio,
        
        case 
            when revenue > 0 then
                round((capex / revenue * 100)::numeric, 1)
            else null
        end as capex_intensity_pct,
        
        case 
            when employees > 0 then
                round((revenue / employees)::numeric, 2)
            else null
        end as revenue_per_employee,
        
        case 
            when revenue > 0 then
                round((gross_profit / revenue * 100)::numeric, 2)
            else null
        end as gross_margin_pct,
        
        -- Operating Expenses
        gross_profit - ebitda as operating_expenses,
        
        -- OpEx as % of Revenue
        case 
            when revenue > 0 then
                round(((gross_profit - ebitda) / revenue * 100)::numeric, 2)
            else null
        end as opex_pct_of_revenue
        
    from with_ytd
),

final as (
    select
        *,
        -- Risk flags (must be in separate CTE to reference calculated columns)
        case 
            when revenue_mom_growth_pct < -10 then true
            else false
        end as revenue_risk_flag,
        
        case
            when margin_change_bps < -200 then true
            else false
        end as margin_risk_flag,
        
        case
            when net_leverage_ratio > 5.0 then true
            else false
        end as leverage_risk_flag,
        
        case
            when cash_conversion_pct < 70 then true
            else false
        end as liquidity_risk_flag
    from calculations
)

select * from final
