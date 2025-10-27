{{
    config(
        materialized='table',
        schema='reporting'
    )
}}

with comments as (
    select * from {{ source('raw_data', 'fact_comments') }}
),

companies as (
    select company_id, company_name from {{ source('raw_data', 'dim_company') }}
),

dates as (
    select date_id, date, year_month from {{ source('raw_data', 'dim_date') }}
),

formatted_comments as (
    select
        c.company_id,
        co.company_name,
        d.date as comment_date,
        d.year_month,
        c.author,
        c.role,
        c.comment_text
    from comments c
    join companies co on c.company_id = co.company_id
    join dates d on c.date_id = d.date_id
)

select * from formatted_comments
order by company_id, comment_date desc
