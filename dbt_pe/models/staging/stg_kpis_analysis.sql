{{
    config(
        materialized='table',
        schema='dbt_stg'
    )
}}

with kpis as (
    select * from {{ source('raw_data', 'fact_kpis_monthly') }}
),

kpi_names as (
    select * from {{ source('raw_data', 'dim_kpi') }}
),

companies as (
    select * from {{ source('raw_data', 'dim_company') }}
),

dates as (
    select * from {{ source('raw_data', 'dim_date') }}
),

base_data as (
    select
        k.company_id,
        c.company_name,
        c.industry,
        d.date,
        d.year,
        d.month,
        d.year_month,
        kn.kpi_name,
        k.kpi_value
    from kpis k
    join kpi_names kn on k.kpi_id = kn.kpi_id
    join companies c on k.company_id = c.company_id
    join dates d on k.date_id = d.date_id
),

with_lag as (
    select
        *,
        lag(kpi_value, 1) over (partition by company_id, kpi_name order by date) as prev_month_value,
        lag(kpi_value, 12) over (partition by company_id, kpi_name order by date) as prev_year_value
    from base_data
),

calculations as (
    select
        company_id,
        company_name,
        industry,
        date,
        year,
        month,
        year_month,
        kpi_name,
        kpi_value,
        
        case 
            when prev_month_value is not null then
                round((kpi_value - prev_month_value)::numeric, 2)
            else null
        end as mom_change,
        
        case 
            when prev_month_value > 0 then
                round(((kpi_value - prev_month_value) / prev_month_value * 100)::numeric, 2)
            else null
        end as mom_change_pct,
        
        case 
            when prev_year_value > 0 then
                round(((kpi_value - prev_year_value) / prev_year_value * 100)::numeric, 2)
            else null
        end as yoy_change_pct,
        
        avg(kpi_value) over (
            partition by company_id, kpi_name 
            order by date 
            rows between 2 preceding and current row
        ) as ma_3month
        
    from with_lag
),

with_trends as (
    select
        *,
        case
            when kpi_name = 'Churn Rate (%)' and kpi_value > 2.5 then true
            when kpi_name = 'Churn Rate (%)' and mom_change_pct > 20 then true
            when kpi_name = 'ARPU (€ / month)' and mom_change_pct < -5 then true
            when kpi_name = 'Homes Passed (000s)' and mom_change_pct < 0 then true
            else false
        end as risk_flag
    from calculations
)

select * from with_trends
