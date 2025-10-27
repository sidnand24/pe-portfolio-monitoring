{{
    config(
        materialized='table',
        schema='reporting'
    )
}}

with financials as (
    select * from {{ ref('stg_financials_enhanced') }}
),

budget as (
    select * from {{ ref('stg_budget_monthly_spread') }}
),

variance_calcs as (
    select
        f.company_id,
        f.company_name,
        f.industry,
        f.date,
        f.year,
        f.month,
        f.year_month,
        
        f.revenue as actual_revenue,
        b.revenue_budget_monthly as budget_revenue,
        round((f.revenue - b.revenue_budget_monthly)::numeric, 2) as variance_revenue,
        case 
            when b.revenue_budget_monthly != 0 then
                round(((f.revenue - b.revenue_budget_monthly) / b.revenue_budget_monthly * 100)::numeric, 1)
            else null
        end as variance_revenue_pct,
        
        f.ebitda as actual_ebitda,
        b.ebitda_budget_monthly as budget_ebitda,
        round((f.ebitda - b.ebitda_budget_monthly)::numeric, 2) as variance_ebitda,
        case 
            when b.ebitda_budget_monthly != 0 then
                round(((f.ebitda - b.ebitda_budget_monthly) / b.ebitda_budget_monthly * 100)::numeric, 1)
            else null
        end as variance_ebitda_pct,
        
        f.ebitda_margin as actual_ebitda_margin,
        case 
            when b.revenue_budget_monthly > 0 then
                round((b.ebitda_budget_monthly / b.revenue_budget_monthly * 100)::numeric, 2)
            else null
        end as budget_ebitda_margin,
        
        f.cash_from_ops as actual_cash_from_ops,
        b.cash_from_ops_budget_monthly as budget_cash_from_ops,
        round((f.cash_from_ops - b.cash_from_ops_budget_monthly)::numeric, 2) as variance_cash_from_ops,
        
        f.capex as actual_capex,
        b.capex_budget_monthly as budget_capex,
        round((f.capex - b.capex_budget_monthly)::numeric, 2) as variance_capex,
        
        f.ytd_revenue as ytd_actual_revenue,
        b.ytd_revenue_budget as ytd_budget_revenue,
        round((f.ytd_revenue - b.ytd_revenue_budget)::numeric, 2) as ytd_variance_revenue,
        case 
            when b.ytd_revenue_budget != 0 then
                round(((f.ytd_revenue - b.ytd_revenue_budget) / b.ytd_revenue_budget * 100)::numeric, 1)
            else null
        end as ytd_variance_revenue_pct,
        
        f.ytd_ebitda as ytd_actual_ebitda,
        b.ytd_ebitda_budget as ytd_budget_ebitda,
        round((f.ytd_ebitda - b.ytd_ebitda_budget)::numeric, 2) as ytd_variance_ebitda,
        case 
            when b.ytd_ebitda_budget != 0 then
                round(((f.ytd_ebitda - b.ytd_ebitda_budget) / b.ytd_ebitda_budget * 100)::numeric, 1)
            else null
        end as ytd_variance_ebitda_pct,
        
        case
            when f.ytd_revenue is not null and b.ytd_revenue_budget != 0 then
                case 
                    when ((f.ytd_revenue - b.ytd_revenue_budget) / b.ytd_revenue_budget * 100) < -15 then true
                    else false
                end
            else false
        end as budget_risk_flag
        
    from financials f
    left join budget b 
        on f.company_id = b.company_id 
        and f.date = b.date
)

select * from variance_calcs
